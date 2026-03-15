'use client';

import React, { useEffect, useState } from 'react';
import { generateNmckDoc, GenerateDocRequest, getSmartPrice, SearchNmckResponse, submitManualNmck } from '@/lib/api';
import { useSearchSettings } from '@/context/SearchSettingsContext';

interface SmartPriceAdvisorProps {
  cteId?: string | number;
  cteName?: string;
  currentPrice?: number;
  marketAverage?: number; // Kept as fallback
  minPortalPrice?: number; // Kept as fallback
  compact?: boolean;
  noData?: boolean;
  onPriceChange?: (price: number, justification: string) => void;
}

export const SmartPriceAdvisor: React.FC<SmartPriceAdvisorProps> = ({
  cteId,
  cteName,
  currentPrice = 398.00,
  marketAverage = 415.00,
  minPortalPrice = 385.00,
  compact = false,
  noData = false,
  onPriceChange,
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Date Filters - Default to 1 year ago
  const [dateFrom, setDateFrom] = useState<string>(() => {
    const d = new Date();
    d.setFullYear(d.getFullYear() - 1);
    return d.toISOString().split('T')[0];
  });
  const [dateTo, setDateTo] = useState<string>(() => {
    return new Date().toISOString().split('T')[0];
  });
  
  // Applied Date Filters (trigger the fetch)
  const [appliedDateFrom, setAppliedDateFrom] = useState<string>(dateFrom);
  const [appliedDateTo, setAppliedDateTo] = useState<string>(dateTo);

  const [smartData, setSmartData] = useState<SearchNmckResponse | null>(null);
  const [isLoadingSmartPrice, setIsLoadingSmartPrice] = useState(!!cteId && !compact);
  const [isError, setIsError] = useState(false);
  const [errorDetail, setErrorDetail] = useState<string | null>(null);

  const [isAddingData, setIsAddingData] = useState(false);
  const [manualSuppliers, setManualSuppliers] = useState<{ inn: string; price: string }[]>([{ inn: '', price: '' }]);
  const [manualDate, setManualDate] = useState(new Date().toISOString().split('T')[0]);
  const [isSaving, setIsSaving] = useState(false);
  const [manualResult, setManualResult] = useState<SearchNmckResponse | null>(null);
  
  const [selectedContractIds, setSelectedContractIds] = useState<Set<number>>(new Set());
  const [showContractList, setShowContractList] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const { cteSearchN, scoreThreshold } = useSearchSettings();

  useEffect(() => {
    if (smartData?.contracts) {
      setSelectedContractIds(new Set(smartData.contracts.map(c => c.contract_id)));
    }
  }, [smartData]);

  useEffect(() => {
    if (cteId && !noData && !compact) {
      setIsLoadingSmartPrice(true);
      setIsError(false);
      setErrorDetail(null);
      setIsAddingData(false);
      
      getSmartPrice(cteId, appliedDateFrom, appliedDateTo, cteSearchN, scoreThreshold).then(data => {
        setSmartData(data);
        setIsError(false);
        setIsLoadingSmartPrice(false);
      }).catch(err => {
        console.error('Smart price fetch error:', err);
        setSmartData(null);
        setIsError(true);
        
        // Extract detail from 422 error if possible
        if (err.status === 422 && typeof err.detail === 'string') {
          setErrorDetail(err.detail);
        } else if (err.status === 422 && Array.isArray(err.detail)) {
          // FastAPI validation error detail
          setErrorDetail(err.detail.map((d: any) => d.msg).join('. '));
        }
        
        setIsLoadingSmartPrice(false);
      });
    }
  }, [cteId, noData, appliedDateFrom, appliedDateTo, cteSearchN, scoreThreshold, compact]);

  // Derived values depending on API or fallbacks
  const actualMarketMedian = smartData ? parseFloat(smartData.median_price) : (isError ? 0 : marketAverage);
  const actualMarketAverage = smartData ? parseFloat(smartData.mean_price) : (isError ? 0 : marketAverage);
  const actualMinPrice = smartData ? parseFloat(smartData.price_min) : (isError ? 0 : minPortalPrice);

  const handleGeneratePDF = async () => {
    if (!cteId) return;
    
    setIsGenerating(true);
    try {
      const request: GenerateDocRequest = {
        cte_id: typeof cteId === 'string' ? parseInt(cteId) : cteId,
        customer: "Организация-Заказчик",
        subject: cteName ? `Обоснование расчетной НМЦК по СТЕ: ${cteName}` : undefined,
        quantity: 1,
        unit: "шт",
        date_from: appliedDateFrom,
        date_to: appliedDateTo,
        top_n: cteSearchN,
        score_threshold: scoreThreshold,
      };

      // If we have manual results or selected contracts, provide sources to the backend
      if (smartData && (manualResult || selectedContractIds.size < smartData.contracts.length)) {
        const selectedContracts = smartData.contracts.filter(c => selectedContractIds.has(c.contract_id));
        request.sources = selectedContracts.map(c => {
          const item = c.items.find(i => String(i.cte_id) === String(cteId)) || c.items[0];
          return {
            name: item?.cte_position_name || c.purchase_name || "Контракт",
            supplier: c.supplier_inn || "Не указан",
            price: parseFloat(item?.unit_price || '0'),
            date: c.signed_at || "Не указана"
          };
        });
        request.nmck = actualMarketMedian;
      }
      
      await generateNmckDoc(request, `Обоснование_цены_${cteId}.docx`);
    } catch (error) {
      console.error('Failed to generate document:', error);
      alert('Ошибка при генерации документа. Попробуйте позже.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRecalculate = async () => {
    if (!cteId || !smartData) return;
    
    const selectedContracts = smartData.contracts.filter(c => selectedContractIds.has(c.contract_id));
    if (selectedContracts.length === 0) {
      alert('Выберите хотя бы один контракт для расчета');
      return;
    }

    setIsRecalculating(true);
    try {
      const request = {
        cte_id: typeof cteId === 'string' ? parseInt(cteId, 10) : (cteId as number),
        contracts: selectedContracts.map(c => {
          // Find the item with the correct cteId or fallback to the first item
          const item = c.items.find(i => String(i.cte_id) === String(cteId)) || c.items[0];
          const price = parseFloat(item?.unit_price || '0');
          // Trim signed_at to YYYY-MM-DD if it exists
          const date = c.signed_at ? c.signed_at.substring(0, 10) : null;
          
          return {
            unit_price: price > 0 ? price : 0.01, // Fallback to a small positive value if 0
            signed_at: date,
            supplier_inn: c.supplier_inn || null
          };
        })
      };
      
      const result = await submitManualNmck(request);
      
      // Merge results while keeping original contracts to maintain UI state
      setSmartData(prev => prev ? {
        ...prev,
        ...result,
        contracts: prev.contracts, // Keep original rich contracts
        total_contracts: prev.total_contracts // Keep original total
      } : null);

      setManualResult(result);
    } catch (error) {
      console.error('Failed to recalculate NMCK:', error);
      alert('Ошибка при перерасчете НМЦК');
    } finally {
      setIsRecalculating(false);
    }
  };

  const savings = actualMarketMedian > 0 ? ((actualMarketMedian - currentPrice) / actualMarketMedian) * 100 : 0;
  const isGoodPrice = currentPrice <= (actualMarketMedian || currentPrice);

  if (compact) {
    return (
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] font-bold text-portal-blue italic flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          {noData ? 'Ручное обоснование НМЦК' : (isError ? 'Нет данных для умного расчета' : 'Нажмите, чтобы рассчитать умную НМЦК')}
        </span>
      </div>
    );
  }

  if (isLoadingSmartPrice) {
    return (
      <div className="bg-[#fcfdfd] border border-border-portal rounded-lg p-8 shadow-sm flex flex-col justify-center items-center min-h-[250px] w-full">
         <div className="animate-spin h-8 w-8 border-4 border-portal-blue border-t-transparent rounded-full mb-4" />
         <span className="text-portal-blue font-bold text-base tracking-wide uppercase">Системный анализ рынка...</span>
         <span className="text-text-muted text-sm mt-2">Пожалуйста, подождите. Производится сбор котировок.</span>
      </div>
    );
  }

  if (isError && !isAddingData) {
    return (
      <div className="bg-[#fcfdfd] border-t-4 border-t-portal-red border-l border-r border-b border-border-portal rounded-b-lg p-8 shadow-md w-full animate-in fade-in duration-500">
        <div className="flex items-center gap-3 mb-6 border-b border-border-portal pb-4">
          <svg className="w-6 h-6 text-portal-red" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
          <h3 className="text-portal-red font-black text-xl tracking-tight">Недостаточно данных для анализа</h3>
        </div>
        <div className="p-4 bg-red-50 rounded font-serif border border-red-100">
          <p className="text-sm text-portal-red leading-relaxed">
            {errorDetail || 'Системе не удалось найти достаточное количество исполненных контрактов за выбранный период для формирования достоверной НМЦК.'}
            {' '}Вы можете расширить период поиска или вручную добавить известные вам цены предложений.
          </p>
        </div>
        <div className="mt-6 flex flex-wrap gap-3">
          <button 
            onClick={() => setIsAddingData(true)}
            className="bg-portal-blue text-white px-6 py-2 rounded text-sm font-bold tracking-wide hover:bg-portal-blue-hover transition-colors shadow-sm"
          >
            Добавить данные о поставщиках
          </button>
          <button 
            onClick={() => {
              const d = new Date();
              d.setFullYear(d.getFullYear() - 2); // try 2 years
              setDateFrom(d.toISOString().split('T')[0]);
              setAppliedDateFrom(d.toISOString().split('T')[0]);
            }}
            className="text-portal-blue hover:bg-blue-50 px-6 py-2 rounded text-sm font-bold transition-colors border border-portal-blue"
          >
            Расширить период (2 года)
          </button>
        </div>
      </div>
    );
  }

  if (isAddingData) {
    return (
      <div className="bg-[#fcfdfd] border-t-4 border-t-portal-blue border-l border-r border-b border-border-portal rounded-b-lg p-8 shadow-md w-full animate-in fade-in duration-500">
        <div className="flex items-center gap-3 mb-6 border-b border-border-portal pb-4">
          <svg className="w-6 h-6 text-portal-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
          <h3 className="text-portal-blue font-black text-xl tracking-tight">Добавление данных о закупке</h3>
          <span className="bg-bg-active-light text-portal-blue px-3 py-1 rounded bg-[#e8f0fe] border border-portal-blue text-[11px] font-bold uppercase ml-auto">Новая запись</span>
        </div>
        
        <div className="space-y-6">
          <div className="p-4 bg-[#f8fbff] rounded font-serif border border-[#dae8f5]">
            <p className="text-sm text-[#333] leading-relaxed">
              Укажите информацию о ценовых предложениях от поставщиков для СТЕ: <strong>{cteName}</strong>. 
              Эти данные будут использованы для обоснования НМЦК методом сопоставимых рыночных цен.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2 md:col-span-2">
              <label className="text-xs font-bold uppercase text-[#555] tracking-wide">Наименование СТЕ</label>
              <input 
                disabled
                type="text" 
                value={cteName}
                className="w-full bg-gray-50 border-2 border-border-portal rounded px-4 py-3 text-sm text-text-muted"
              />
            </div>
            
            <div className="md:col-span-2 space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <span className="text-xs font-bold uppercase text-[#555] tracking-wide">ИНН поставщика</span>
                <span className="text-xs font-bold uppercase text-[#555] tracking-wide">Цена за единицу (₽)</span>
              </div>
              {manualSuppliers.map((row, idx) => {
                const trimmed = row.inn.trim();
                const isDuplicate = trimmed !== '' && manualSuppliers.some((r, i) => i !== idx && r.inn.trim() === trimmed);
                return (
                <div key={idx} className="grid grid-cols-2 gap-4 items-start">
                  <div className="space-y-1">
                    <input
                      type="text"
                      placeholder="7701234567"
                      value={row.inn}
                      onChange={(e) => {
                        const updated = [...manualSuppliers];
                        updated[idx] = { ...updated[idx], inn: e.target.value };
                        setManualSuppliers(updated);
                      }}
                      className={`w-full bg-white border-2 rounded focus:ring-0 px-4 py-3 text-sm font-bold ${isDuplicate ? 'border-portal-red focus:border-portal-red' : 'border-border-portal focus:border-portal-blue'}`}
                    />
                    {isDuplicate && (
                      <p className="text-xs text-portal-red font-semibold">ИНН уже указан выше</p>
                    )}
                  </div>
                  <div className="relative flex items-center gap-2">
                    <div className="relative flex-1">
                      <input
                        type="text"
                        placeholder="0.00"
                        value={row.price}
                        onChange={(e) => {
                          const updated = [...manualSuppliers];
                          updated[idx] = { ...updated[idx], price: e.target.value };
                          setManualSuppliers(updated);
                        }}
                        className="w-full bg-white border-2 border-border-portal rounded focus:border-portal-blue focus:ring-0 px-4 py-3 text-lg font-black font-mono pr-8"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted font-bold">₽</span>
                    </div>
                    {manualSuppliers.length > 1 && (
                      <button
                        type="button"
                        onClick={() => setManualSuppliers(manualSuppliers.filter((_, i) => i !== idx))}
                        className="text-portal-red hover:text-red-700 font-bold text-xl leading-none w-7 h-7 flex items-center justify-center shrink-0"
                        title="Удалить"
                      >
                        ×
                      </button>
                    )}
                  </div>
                </div>
                );
              })}
              {manualSuppliers.length < 4 && (
                <button
                  type="button"
                  onClick={() => setManualSuppliers([...manualSuppliers, { inn: '', price: '' }])}
                  className="flex items-center gap-1 text-portal-blue hover:text-portal-blue-hover text-sm font-bold mt-1"
                >
                  <span className="text-lg leading-none">+</span>
                  <span>Добавить поставщика</span>
                </button>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold uppercase text-[#555] tracking-wide">Дата предложения</label>
              <input 
                type="date" 
                value={manualDate}
                onChange={(e) => setManualDate(e.target.value)}
                className="w-full bg-white border-2 border-border-portal rounded focus:border-portal-blue focus:ring-0 px-4 py-3 text-sm font-mono"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-border-portal">
            <button
              disabled={isSaving}
              onClick={async () => {
                const filledInns = manualSuppliers.map(r => r.inn.trim()).filter(v => v !== '');
                const hasDuplicates = filledInns.length !== new Set(filledInns).size;
                if (hasDuplicates) {
                  alert('Удалите дублирующиеся ИНН поставщиков');
                  return;
                }
                const validRows = manualSuppliers.filter(r => parseFloat(r.price) > 0);
                if (validRows.length === 0) {
                  alert('Укажите корректную цену за единицу хотя бы для одного поставщика');
                  return;
                }
                setIsSaving(true);
                try {
                  const result = await submitManualNmck({
                    cte_id: typeof cteId === 'string' ? parseInt(cteId, 10) : (cteId as number),
                    contracts: validRows.map(r => ({
                      unit_price: parseFloat(r.price),
                      signed_at: manualDate || null,
                      supplier_inn: r.inn.trim() || null,
                    })),
                  });
                  setManualResult(result);
                  setIsAddingData(false);
                  setSmartData(result as unknown as SearchNmckResponse);
                  setIsError(false);
                } catch (err) {
                  console.error('submitManualNmck error:', err);
                  alert('Ошибка при сохранении. Проверьте введённые данные.');
                } finally {
                  setIsSaving(false);
                }
              }}
              className="bg-portal-blue text-white px-8 py-3 rounded text-sm font-bold tracking-wide hover:bg-portal-blue-hover transition-colors shadow-sm disabled:opacity-50"
            >
              {isSaving ? 'Сохранение...' : 'Сохранить предложение'}
            </button>
            <button
              onClick={() => { setIsAddingData(false); setManualSuppliers([{ inn: '', price: '' }]); }}
              className="text-[#666] hover:text-[#333] hover:bg-gray-100 px-6 py-3 rounded text-sm font-bold transition-colors"
            >
              Отмена
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (noData) {
    return (
      <div className="bg-[#fcfdfd] border-t-4 border-t-portal-blue border-l border-r border-b border-border-portal rounded-b-lg p-8 shadow-md w-full animate-in fade-in duration-500">
        <div className="flex items-center gap-3 mb-6 border-b border-border-portal pb-4">
          <svg className="w-6 h-6 text-portal-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
          <h3 className="text-portal-blue font-black text-xl tracking-tight">Отсутствие данных</h3>
        </div>
        <div className="space-y-6">
          <div className="p-4 bg-orange-50 rounded font-serif border border-orange-200">
            <p className="text-sm text-orange-800 leading-relaxed">
              Система не обнаружила релевантных контрактов для автоматического расчета НМЦК по данной позиции СТЕ.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border-t-4 border-t-portal-green border-l border-r border-b border-border-portal rounded-b-lg shadow-xl relative animate-in fade-in slide-in-from-bottom-4 duration-500 w-full mt-4 flex flex-col max-h-[90vh]">
      <div className="overflow-y-auto p-8 pr-12">
        <div className="flex justify-between items-center mb-8 pb-4 border-b border-border-portal">
          <div className="flex items-center gap-4">
            <div className="bg-portal-green/10 p-3 rounded-xl">
              <svg className="w-8 h-8 text-portal-green" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            </div>
            <div>
              <h3 className="text-[#1a1a1a] font-black text-2xl tracking-tight">Анализ рыночной стоимости</h3>
              {isGoodPrice ? (
                <div className="flex items-center gap-2 mt-1">
                  <span className="bg-bg-success-light text-portal-green px-2 py-0.5 border border-portal-green/30 rounded text-[10px] font-black uppercase tracking-wider">
                    В рамках рынка
                  </span>
                  <span className="text-[10px] text-text-muted font-bold">Оценка системы: Оптимально</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 mt-1">
                  <span className="bg-bg-error-light text-portal-red px-2 py-0.5 border border-portal-red/30 rounded text-[10px] font-black uppercase tracking-wider">
                    Выше рынка
                  </span>
                  <span className="text-[10px] text-text-muted font-bold">Требуется обоснование</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          {/* Left Column: Analysis & Stats */}
          <div className="lg:col-span-2 space-y-8">
            <div className="font-serif text-[#222]">
              <p className="text-[16px] leading-relaxed">
                В соответствии с алгоритмами анализа портала, на основании изучения {smartData?.sample_size_total ? <strong className="font-bold underline decoration-portal-blue/30">{smartData.sample_size_total} предложений</strong> : `сопоставимых котировочных сессий`}, 
                текущая стоимость единицы СТЕ в размере <strong>{currentPrice.toFixed(2)} ₽</strong> признана {isGoodPrice ? <span className="text-portal-green font-bold">соответствующей рыночной медиане</span> : <span className="text-portal-red font-bold">превышающей рыночную медиану (НМЦК)</span>}.
              </p>
              {smartData?.warnings && smartData.warnings.length > 0 && (
                <div className="mt-4 p-4 bg-red-50 border-l-4 border-portal-red text-portal-red text-sm font-sans flex gap-3 items-start">
                  <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                  <div>
                    <strong className="block mb-1">Рекомендация по закупке:</strong>
                    {smartData.warnings.join('. ')}
                  </div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-0 bg-white rounded-xl border border-border-portal shadow-sm overflow-hidden divide-y md:divide-y-0 md:divide-x divide-border-portal/50">
              <div className="flex flex-col p-6 bg-gray-50/30">
                <span className="text-text-muted text-[11px] font-black uppercase tracking-widest mb-2">Расчетная НМЦК</span>
                <span className="font-mono text-3xl font-black text-[#111]">{actualMarketMedian.toFixed(2)} ₽</span>
                <span className="text-[10px] text-text-light font-bold mt-2">Медианное значение</span>
              </div>
              <div className="flex flex-col p-6">
                <span className="text-text-muted text-[11px] font-black uppercase tracking-widest mb-2">Средняя цена</span>
                <span className="font-mono text-3xl font-black text-[#111]">{actualMarketAverage.toFixed(2)} ₽</span>
                <span className="text-[10px] text-text-light font-bold mt-2">Арифметическое среднее</span>
              </div>
              <div className={`flex flex-col p-6 ${savings > 0 ? 'bg-bg-success-light/30' : 'bg-bg-error-light/30'}`}>
                <span className="text-text-muted text-[11px] font-black uppercase tracking-widest mb-2">Отклонение</span>
                <span className={`font-mono text-2xl font-black flex items-center gap-2 ${savings > 0 ? 'text-portal-green' : 'text-portal-red'}`}>
                  {savings <= 0 && <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>}
                  {savings > 0 ? `-${savings.toFixed(1)}%` : `+${Math.abs(savings).toFixed(1)}%`}
                </span>
                <span className={`text-[10px] font-bold mt-2 ${savings > 0 ? 'text-portal-green' : 'text-portal-red'}`}>
                  {savings > 0 ? 'Ниже медианы' : 'Требует снижения'}
                </span>
              </div>
            </div>

            <div>
              <button 
                type="button"
                onClick={() => setShowContractList(!showContractList)}
                className="flex items-center gap-3 text-xs font-bold text-portal-blue hover:text-portal-blue-hover uppercase tracking-[0.1em] group"
              >
                <div className="bg-portal-blue/10 p-1.5 rounded transition-colors group-hover:bg-portal-blue/20">
                  <svg className={`w-4 h-4 transition-transform duration-300 ${showContractList ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 9l-7 7-7-7"></path>
                  </svg>
                </div>
                База релевантных контрактов ({smartData?.contracts.length || 0})
              </button>
              
              {showContractList && smartData?.contracts && (
                <div className="mt-4 border border-border-portal rounded-xl overflow-hidden bg-white shadow-lg animate-in slide-in-from-top-4 duration-300">
                  <div className="max-h-80 overflow-y-auto">
                    <table className="w-full text-left text-[11px]">
                      <thead className="bg-[#f8fbfd] border-b border-border-portal sticky top-0 z-10 shadow-sm">
                        <tr>
                          <th className="px-5 py-4 w-10">
                            <input 
                              type="checkbox" 
                              checked={selectedContractIds.size === (smartData?.contracts.length || 0)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedContractIds(new Set(smartData.contracts.map(c => c.contract_id)));
                                } else {
                                  setSelectedContractIds(new Set());
                                }
                              }}
                              className="rounded border-border-portal text-portal-blue focus:ring-portal-blue"
                            />
                          </th>
                          <th className="px-5 py-4 font-black text-text-muted uppercase tracking-wider">Исполнение</th>
                          <th className="px-5 py-4 font-black text-text-muted uppercase tracking-wider">Регион</th>
                          <th className="px-5 py-4 font-black text-text-muted uppercase tracking-wider">Наименование позиции</th>
                          <th className="px-5 py-4 font-black text-text-muted uppercase tracking-wider">Цена</th>
                          <th className="px-5 py-4 font-black text-text-muted uppercase tracking-wider">Поставщик</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-portal/30">
                        {smartData.contracts.map((contract) => {
                          const item = contract.items.find(i => String(i.cte_id) === String(cteId)) || contract.items[0];
                          const price = parseFloat(item?.unit_price || '0');
                          const isSelected = selectedContractIds.has(contract.contract_id);
                          return (
                            <tr key={contract.contract_id} className={`transition-all ${!isSelected ? 'opacity-40 grayscale-[0.5] bg-gray-50/50' : 'hover:bg-bg-active-light/20'}`}>
                              <td className="px-5 py-4">
                                <input 
                                  type="checkbox" 
                                  checked={isSelected}
                                  onChange={() => {
                                    const newSet = new Set(selectedContractIds);
                                    if (newSet.has(contract.contract_id)) {
                                      newSet.delete(contract.contract_id);
                                    } else {
                                      newSet.add(contract.contract_id);
                                    }
                                    setSelectedContractIds(newSet);
                                  }}
                                  className="rounded border-border-portal text-portal-blue focus:ring-portal-blue"
                                />
                              </td>
                              <td className="px-5 py-4 font-mono font-bold text-text-main">
                                {contract.signed_at ? new Date(contract.signed_at).toLocaleDateString('ru-RU') : '—'}
                              </td>
                              <td className="px-5 py-4 text-text-muted">
                                {contract.buyer_region || '—'}
                              </td>
                              <td className="px-5 py-4 text-text-main font-medium leading-relaxed max-w-[200px] truncate" title={item?.cte_position_name || contract.purchase_name}>
                                {item?.cte_position_name || contract.purchase_name}
                              </td>
                              <td className="px-5 py-4 font-black text-portal-blue whitespace-nowrap">
                                {price.toLocaleString('ru-RU')} ₽
                              </td>
                              <td className="px-5 py-4 text-text-muted font-bold">
                                {contract.supplier_inn || '—'}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <div className="bg-[#f8fbfd] border-t border-border-portal p-4 flex justify-between items-center bg-gradient-to-r from-[#f8fbfd] to-[#ebf5ff]">
                    <span className="text-[10px] text-text-muted font-black uppercase tracking-widest flex items-center gap-2">
                       <span className="w-2 h-2 rounded-full bg-portal-blue animate-pulse" />
                       Выбрано {selectedContractIds.size} из {smartData.contracts.length} источников
                    </span>
                    <button 
                      type="button"
                      onClick={handleRecalculate}
                      disabled={isRecalculating || selectedContractIds.size === 0}
                      className="bg-portal-blue text-white px-6 py-2.5 rounded shadow-md hover:shadow-lg active:scale-95 transition-all text-[11px] font-bold uppercase tracking-widest disabled:opacity-50 disabled:grayscale"
                    >
                      {isRecalculating ? 'Пересчет...' : 'Обновить расчет'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Controls & Actions */}
          <div className="space-y-8 h-fit lg:sticky lg:top-0">
            <div className="bg-bg-page border border-border-portal rounded-xl p-6 shadow-inner space-y-6">
              <div className="space-y-4">
                <h4 className="text-[11px] font-black text-text-muted uppercase tracking-widest border-b border-border-portal/50 pb-2">Фильтр по датам</h4>
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-text-light uppercase tracking-tight">С даты</label>
                    <input 
                      type="date" 
                      value={dateFrom}
                      onChange={(e) => setDateFrom(e.target.value)}
                      className="w-full text-sm border border-border-portal rounded bg-white px-3 py-2.5 text-text-main font-mono focus:ring-2 focus:ring-portal-blue/20 focus:border-portal-blue outline-none transition-all"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-text-light uppercase tracking-tight">По дату</label>
                    <input 
                      type="date" 
                      value={dateTo}
                      onChange={(e) => setDateTo(e.target.value)}
                      className="w-full text-sm border border-border-portal rounded bg-white px-3 py-2.5 text-text-main font-mono focus:ring-2 focus:ring-portal-blue/20 focus:border-portal-blue outline-none transition-all"
                    />
                  </div>
                </div>
                <div className="flex gap-2 pt-2">
                  <button 
                    onClick={() => {
                      setAppliedDateFrom(dateFrom);
                      setAppliedDateTo(dateTo);
                    }}
                    className="flex-1 bg-portal-blue text-white py-2.5 rounded text-[11px] font-black uppercase tracking-widest hover:bg-portal-blue-hover transition-all shadow-sm active:scale-95"
                  >
                    Обновить
                  </button>
                  <button 
                    onClick={() => { 
                      const d = new Date();
                      d.setFullYear(d.getFullYear() - 1);
                      const resetFrom = d.toISOString().split('T')[0];
                      const resetTo = new Date().toISOString().split('T')[0];
                      setDateFrom(resetFrom); 
                      setDateTo(resetTo); 
                      setAppliedDateFrom(resetFrom);
                      setAppliedDateTo(resetTo);
                    }}
                    className="aspect-square bg-white border border-border-portal text-text-muted p-2.5 rounded hover:bg-white hover:text-portal-red transition-all shadow-sm active:scale-95"
                    title="Сбросить"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                  </button>
                </div>
              </div>

              <div className="pt-4 border-t border-border-portal/50 space-y-4">
                <h4 className="text-[11px] font-black text-text-muted uppercase tracking-widest">Документы</h4>
                <button 
                  disabled={isGenerating}
                  onClick={handleGeneratePDF}
                  className={`w-full flex items-center justify-center gap-3 py-4 rounded-xl font-black text-xs uppercase tracking-widest transition-all shadow-md active:scale-95 border-2 ${isGenerating ? 'bg-gray-100 text-text-muted cursor-not-allowed border-gray-200' : 'bg-white border-portal-blue text-portal-blue hover:bg-portal-blue hover:text-white'}`}
                >
                  {isGenerating ? (
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  ) : (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                  )}
                  {isGenerating ? 'Формирование...' : 'Скачать отчет'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

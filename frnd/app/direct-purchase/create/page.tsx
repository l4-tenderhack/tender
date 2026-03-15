'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useRouter } from 'next/navigation';

export default function CreateDirectPurchase() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [isAiFilling, setIsAiFilling] = useState(false);
  const [deliveryStages, setDeliveryStages] = useState([
    { id: 1, name: 'Поставка продукции согласно спецификации (Ноутбук, Калькуляторы)', days: 5, price: 89776.00 }
  ]);

  const handleAiFill = () => {
    setIsAiFilling(true);
    setTimeout(() => {
      setDeliveryStages([
        { id: 1, name: 'Услуга по доставке офисного оборудования (согласно СТЕ)', days: 5, price: 398.00 },
        { id: 2, name: 'Погрузочно-разгрузочные работы и подъем на этаж', days: 1, price: 0 }
      ]);
      setIsAiFilling(false);
    }, 1500);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      <div className="flex items-center gap-3 text-sm text-text-muted font-bold">
        <span>Каталог</span>
        <span>/</span>
        <span>Корзина</span>
        <span>/</span>
        <span className="text-portal-blue">Создание прямой закупки</span>
      </div>

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-portal-blue">Новая закупка: Офисная техника и канцтовары</h1>
        <Badge variant="active">Черновик</Badge>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <StepIndicator active={step === 1} done={step > 1} label="Параметры" number={1} />
        <StepIndicator active={step === 2} done={step > 2} label="Этапы поставки" number={2} />
        <StepIndicator active={step === 3} done={step > 3} label="Документы" number={3} />
      </div>

      <Card>
        {step === 1 && (
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b pb-2 mb-4">
              <h3 className="font-bold text-lg">Основные сведения</h3>
              <div className="flex gap-2">
                <div className="bg-bg-success-light px-3 py-1 rounded border border-border-green flex items-center gap-2">
                  <span className="text-xs font-bold text-portal-green-dark uppercase">Системное обоснование цены: СООТВЕТСТВУЕТ</span>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <InputGroup label="Основание для заключения" value="Пункт 4 части 1 статьи 93 (44-ФЗ)" />
              <InputGroup label="Планируемая дата заключения" value="20.03.2026" />
              <InputGroup label="Источник финансирования" value="Бюджет города Москвы" />
              <InputGroup label="Классификатор ОКПД2" value="28.23.23 (Ноутбуки), 28.23.12 (Калькуляторы)" />
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-text-muted tracking-tight">Цена контракта (НМЦК)</label>
                <div className="flex gap-2">
                  <div className="flex-1 bg-bg-page border border-border-portal rounded-portal-sm px-3 py-2 text-sm font-bold text-text-main">
                    89 776.00 ₽
                  </div>
                </div>
              </div>
              <InputGroup label="Место поставки" value="г. Москва, ул. Вознесенская, д. 4" />
            </div>
            <div className="pt-6 flex justify-end">
              <Button onClick={() => setStep(2)}>Далее: Этапы поставки</Button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b pb-2 mb-4">
              <div className="space-y-1">
                <h3 className="font-bold text-lg">Спецификация услуги доставки</h3>
                <p className="text-xs text-text-muted italic">Система формирует перечень услуг на основе НМЦК и региона поставки</p>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleAiFill}
                  disabled={isAiFilling}
                >
                  {isAiFilling ? 'Автозаполнение...' : 'Заполнить по шаблону'}
                </Button>
                <Button variant="outline" size="sm">+ Добавить вручную</Button>
              </div>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-bg-page">
                <tr>
                  <th className="text-left p-2 font-bold text-text-muted">№</th>
                  <th className="text-left p-2 font-bold text-text-muted">Наименование этапа</th>
                  <th className="text-left p-2 font-bold text-text-muted">Срок (дней)</th>
                  <th className="text-left p-2 font-bold text-text-muted">Стоимость (₽)</th>
                  <th className="text-right p-2 font-bold text-text-muted">Действия</th>
                </tr>
              </thead>
              <tbody>
                {deliveryStages.map((stage, idx) => (
                  <tr key={stage.id} className="border-b animate-in fade-in slide-in-from-left duration-500" style={{ animationDelay: `${idx * 100}ms` }}>
                    <td className="p-2 font-bold">{idx + 1}</td>
                    <td className="p-2">{stage.name}</td>
                    <td className="p-2">{stage.days}</td>
                    <td className="p-2 font-bold">{stage.price.toLocaleString('ru-RU')}</td>
                    <td className="p-2 text-right">
                      <button className="text-portal-red font-bold hover:underline">Удалить</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="pt-6 flex justify-between">
              <Button variant="ghost" onClick={() => setStep(1)}>Назад</Button>
              <Button onClick={() => setStep(3)}>Далее: Документы</Button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <h3 className="font-bold text-lg border-b pb-2 mb-4">Прикрепленные документы</h3>
            <div className="grid grid-cols-2 gap-4">
                <FileRow name="Спецификация_объекта_закупки.pdf" size="1.2 MB" />
                <FileRow name="Обоснование_НМЦК_AI_Report.pdf" size="0.4 MB" isGenerated />
            </div>
            <div className="border-2 border-dashed border-border-portal rounded-portal-md p-10 flex flex-col items-center gap-3 text-text-muted">
              <p className="font-bold">Перетащите файлы сюда или выберите на компьютере</p>
              <Button variant="outline" size="sm">Выбрать файлы</Button>
            </div>
            <div className="pt-6 flex justify-between">
              <Button variant="ghost" onClick={() => setStep(2)}>Назад</Button>
              <Button variant="secondary" onClick={() => router.push('/direct-purchase/123')}>Опубликовать и направить поставщику</Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

const StepIndicator = ({ number, label, active, done }: { number: number; label: string; active: boolean; done: boolean }) => (
  <div className={`p-3 border-b-4 flex items-center gap-3 transition-colors ${active ? 'border-portal-blue bg-bg-active-light' : done ? 'border-portal-green' : 'border-border-portal'}`}>
    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${active ? 'bg-portal-blue text-white' : done ? 'bg-portal-green text-white' : 'bg-bg-page text-text-muted'}`}>
      {done ? '✓' : number}
    </div>
    <span className={`text-xs font-bold uppercase tracking-wider ${active ? 'text-portal-blue' : done ? 'text-portal-green' : 'text-text-muted'}`}>{label}</span>
  </div>
);

const InputGroup = ({ label, value }: { label: string; value: string }) => (
  <div className="space-y-1">
    <label className="text-[10px] uppercase font-bold text-text-muted tracking-tight">{label}</label>
    <div className="w-full bg-bg-page border border-border-portal rounded-portal-sm px-3 py-2 text-sm font-bold text-text-main">
      {value}
    </div>
  </div>
);

const FileRow = ({ name, size, isGenerated = false }: { name: string, size: string, isGenerated?: boolean }) => (
    <div className="flex items-center justify-between p-3 border border-border-portal rounded-portal-sm bg-bg-page">
        <div className="flex items-center gap-3">
            <div>
                <p className="text-xs font-bold text-text-main underline cursor-pointer">{name}</p>
                <p className="text-[10px] text-text-muted">{size} {isGenerated && <span className="text-portal-green ml-1">(Сформировано системой)</span>}</p>
            </div>
        </div>
        <button className="text-text-muted hover:text-portal-red">✕</button>
    </div>
);

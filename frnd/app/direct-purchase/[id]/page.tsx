'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useParams, useRouter } from 'next/navigation';

export default function TenderHub() {
  const { id } = useParams();
  const router = useRouter();
  const [status, setStatus] = useState<'NEW' | 'CONFIRMED' | 'CONTRACT_DRAFT' | 'SIGNING' | 'ACTIVE'>('NEW');
  const [isSigning, setIsSigning] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleSign = () => {
    setIsSigning(true);
    let p = 0;
    const interval = setInterval(() => {
      p += 10;
      setProgress(p);
      if (p >= 100) {
        clearInterval(interval);
        setStatus('ACTIVE');
        setIsSigning(false);
      }
    }, 300);
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'NEW': return <Badge variant="active">Новая</Badge>;
      case 'CONFIRMED': return <Badge variant="success">Подтверждена поставщиком</Badge>;
      case 'SIGNING': return <Badge variant="active">На подписании</Badge>;
      case 'ACTIVE': return <Badge variant="success">Контракт заключен</Badge>;
      default: return <Badge>Черновик</Badge>;
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs text-text-muted font-bold uppercase tracking-wider">
            <span>Закупка № {id}</span>
            <span>•</span>
            <span>Прямая закупка</span>
          </div>
          <h1 className="text-2xl font-bold text-portal-blue">Поставка офисного оборудования (Калькуляторы)</h1>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" size="sm">Скачать архив</Button>
          <Button variant="outline" size="sm">Печать</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <Card className="relative overflow-hidden">
            <div className="flex justify-between items-start mb-6">
              <h3 className="font-bold text-lg">Статус исполнения</h3>
              {getStatusBadge()}
            </div>
            
            <div className="relative pt-8 pb-4">
              <div className="absolute top-1/2 left-0 w-full h-1 bg-border-portal -translate-y-1/2" />
              <div className="relative flex justify-between">
                <StatusNode active={true} done={true} label="Создана" />
                <StatusNode active={status === 'NEW'} done={['CONFIRMED', 'SIGNING', 'ACTIVE'].includes(status)} label="Направлена" />
                <StatusNode active={status === 'CONFIRMED'} done={['SIGNING', 'ACTIVE'].includes(status)} label="Подтверждена" />
                <StatusNode active={status === 'SIGNING'} done={status === 'ACTIVE'} label="Контракт" />
                <StatusNode active={status === 'ACTIVE'} done={false} label="Исполнение" />
              </div>
            </div>
          </Card>

          <Card className="space-y-4">
            <h3 className="font-bold text-lg border-b pb-2">Объекты закупки</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-bg-page text-text-muted text-[10px] uppercase font-bold">
                    <th className="text-left p-3">Наименование</th>
                    <th className="text-center p-3">Кол-во</th>
                    <th className="text-right p-3">Цена</th>
                    <th className="text-right p-3">Сумма</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  <tr>
                    <td className="p-3 font-bold">Калькулятор настольный 12-разрядный Citizen</td>
                    <td className="p-3 text-center">12 шт.</td>
                    <td className="p-3 text-right">398,00 ₽</td>
                    <td className="p-3 text-right font-bold text-portal-blue">4 776,00 ₽</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="space-y-4">
            <h3 className="font-bold text-sm uppercase text-text-muted">Поставщик</h3>
            <div>
              <p className="font-bold text-text-main">ООО «ОфисМаг-Поволжье»</p>
              <p className="text-[10px] text-text-muted">ИНН: 7712345678</p>
            </div>
            <Button variant="ghost" fullWidth size="sm" className="border">Чат с поставщиком</Button>
          </Card>

          <Card className="space-y-4 border-portal-blue/30 shadow-md">
            <h3 className="font-bold text-sm uppercase text-portal-blue">Действия</h3>
            
            {status === 'NEW' && (
              <div className="space-y-3">
                <p className="text-xs text-text-muted italic">Ожидание подтверждения оферты поставщиком...</p>
                <Button fullWidth variant="secondary" onClick={() => setStatus('CONFIRMED')}>
                    Симулировать ответ поставщика
                </Button>
              </div>
            )}

            {status === 'CONFIRMED' && (
              <div className="space-y-3">
                <p className="text-xs font-bold text-portal-green-dark">Поставщик подтвердил готовность.</p>
                <Button fullWidth variant="primary" onClick={() => setStatus('SIGNING')}>
                   Сформировать проект контракта
                </Button>
              </div>
            )}

            {status === 'SIGNING' && (
              <div className="space-y-4">
                <div className="p-3 bg-bg-active-light rounded border border-border-blue">
                    <p className="text-xs font-bold text-portal-blue">Документы готовы к подписанию ЭП</p>
                </div>
                {isSigning ? (
                    <div className="space-y-2">
                         <div className="w-full h-2 bg-border-portal rounded-full overflow-hidden">
                            <div className="h-full bg-portal-blue transition-all duration-300" style={{ width: `${progress}%` }} />
                         </div>
                         <p className="text-[10px] text-center font-bold animate-pulse text-portal-blue uppercase">Генерация цифровой подписи...</p>
                    </div>
                ) : (
                    <Button fullWidth variant="primary" onClick={handleSign}>
                        Подписать контракт (ЭП)
                    </Button>
                )}
              </div>
            )}

            {status === 'ACTIVE' && (
               <div className="p-3 bg-bg-success-light rounded border border-border-green space-y-2">
                 <p className="text-xs font-bold text-portal-green-dark">Контракт № {id}-2026 активен</p>
                 <Button variant="ghost" fullWidth size="sm" className="text-portal-green-dark">Скачать контракт</Button>
               </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

const StatusNode = ({ label, active, done }: { label: string; active: boolean; done: boolean }) => (
  <div className="flex flex-col items-center gap-2 relative z-10 w-20">
    <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${
      done ? 'bg-portal-green border-portal-green text-white' : 
      active ? 'bg-white border-portal-blue text-portal-blue shadow-lg scale-110' : 
      'bg-white border-border-portal text-text-muted'
    }`}>
    </div>
    <span className={`text-[10px] font-bold uppercase tracking-tight text-center ${active ? 'text-portal-blue' : done ? 'text-portal-green' : 'text-text-muted'}`}>
      {label}
    </span>
  </div>
);

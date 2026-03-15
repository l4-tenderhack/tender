'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Timer } from '@/components/ui/Timer';
import { BiddingPanel } from '@/components/BiddingPanel';
import { SmartPriceAdvisor } from '@/components/SmartPriceAdvisor';
import Link from 'next/link';

export default function QuotationSessionPage({ params }: { params: { id: string } }) {
  const [isPeretorgka, setIsPeretorgka] = useState(false);
  
  const initialData = {
    id: params.id || 'KS-2026-0842',
    name: 'Поставка калькуляторов настольных для нужд ГБУ "Мои Документы"',
    nmcc: 4980.00,
    marketAvg: 415.00, // per unit
    unitPrice: 398.00, // starting unit price
    quantity: 12,
    status: isPeretorgka ? 'ПЕРЕТОРЖКА' : 'АКТИВНА',
  };

  const handleBidPlaced = (amount: number) => {
    // Simulate "Peretorgka" trigger if timer is low (demonstration purposes)
    setIsPeretorgka(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
             <h1 className="text-2xl font-bold text-portal-blue">Котировочная сессия {initialData.id}</h1>
             <Badge variant={isPeretorgka ? 'active' : 'active'} className={isPeretorgka ? 'bg-portal-red' : ''}>
               {initialData.status}
             </Badge>
          </div>
          <p className="text-text-muted text-sm max-w-2xl">{initialData.name}</p>
        </div>
        <div className="text-right space-y-2">
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest">До завершения</p>
          <Timer initialSeconds={isPeretorgka ? 300 : 3600 * 3} onExpire={() => alert('Торги завершены')} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-0 border-none overflow-hidden h-full">
            <div className="bg-portal-blue/5 p-4 border-b border-portal-blue/10 flex justify-between items-center">
              <h3 className="font-bold text-portal-blue">Спецификация объекта закупки</h3>
              <span className="text-xs font-medium text-portal-blue italic">ОКПД2: 28.23.12.110</span>
            </div>
            <div className="p-6">
               <table className="w-full text-sm">
                 <thead>
                   <tr className="border-b text-text-muted font-bold uppercase text-[10px]">
                     <th className="p-2 text-left">Наименование</th>
                     <th className="p-2 text-center">Кол-во</th>
                     <th className="p-2 text-center">Ед. изм.</th>
                     <th className="p-2 text-right">Нач. цена</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y">
                   <tr>
                     <td className="p-4 font-medium">Калькулятор настольный Citizen SDC-888XBK</td>
                     <td className="p-4 text-center">12</td>
                     <td className="p-4 text-center">шт.</td>
                     <td className="p-4 text-right font-bold">{initialData.unitPrice.toLocaleString('ru-RU')} ₽</td>
                   </tr>
                 </tbody>
               </table>
            </div>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
             <Card>
               <h4 className="text-[10px] font-bold text-text-muted uppercase mb-3">Параметры сессии</h4>
               <div className="space-y-3">
                 <div className="flex justify-between text-sm">
                   <span className="text-text-muted">Тип процедуры</span>
                   <span className="font-bold">Котировочная сессия</span>
                 </div>
                 <div className="flex justify-between text-sm">
                   <span className="text-text-muted">Регион поставки</span>
                   <span className="font-bold text-portal-blue">г. Москва</span>
                 </div>
                 <div className="flex justify-between text-sm">
                   <span className="text-text-muted">Срок поставки</span>
                   <span className="font-bold">5 рабочих дней</span>
                 </div>
               </div>
             </Card>
             <SmartPriceAdvisor 
               currentPrice={initialData.unitPrice} 
               marketAverage={initialData.marketAvg}
             />
          </div>
        </div>

        <div className="space-y-6">
          <BiddingPanel initialPrice={initialData.nmcc} onPlaceBid={handleBidPlaced} />
          
          <Card className="bg-bg-page border-portal-blue/20">
            <h4 className="text-[10px] font-bold text-text-muted uppercase mb-3">Сопровождение</h4>
            <p className="text-xs leading-relaxed text-text-main">
              Согласно 44-ФЗ, победитель определяется по наименьшей цене предложения. 
              В случае ставки за последние 5 минут, сессия автоматически продлевается.
            </p>
            <div className="mt-4 flex flex-col gap-2">
               <Button variant="outline" size="sm" fullWidth>Регламент КС (PDF)</Button>
               <Button variant="outline" size="sm" fullWidth>Проект контракта</Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

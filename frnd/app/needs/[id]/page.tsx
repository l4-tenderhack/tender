'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

interface Proposal {
  id: string;
  supplier: string;
  price: number;
  score: number;
  match: string;
  status: 'optimal' | 'warning' | 'normal';
}

export default function NeedDetailPage({ params }: { params: { id: string } }) {
  const needId = params.id || 'ZPP-2026-0042';

  const proposals: Proposal[] = [    { 
      id: '1', 
      supplier: 'ООО "МебельПлюс"', 
      price: 135000, 
      score: 98, 
      match: 'Полное соответствие ТЗ',
      status: 'optimal'
    },
    { 
      id: '2', 
      supplier: 'СтильОфис', 
      price: 132000, 
      score: 85, 
      match: 'Аналог по материалам (ЛДСП вместо шпона)',
      status: 'warning'
    },
    { 
      id: '3', 
      supplier: 'Мебельная фабрика "Заря"', 
      price: 148000, 
      score: 92, 
      match: 'Полное соответствие ТЗ',
      status: 'normal'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold text-portal-blue">Закупка по потребностям {needId}</h1>
            <Badge variant="active">ПРИЕМ ПРЕДЛОЖЕНИЙ</Badge>
          </div>
          <p className="text-sm text-text-muted">Поставка офисной мебели для учебного центра</p>
        </div>
        <div className="text-right">
           <p className="text-[10px] font-bold text-text-muted uppercase">Бюджет</p>
           <p className="text-xl font-black text-portal-blue">150 000.00 ₽</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="space-y-4">
            <h3 className="font-bold border-b pb-2">Поступившие предложения (3)</h3>
            <div className="divide-y">
              {proposals.map((p) => (
                <div key={p.id} className="py-4 flex justify-between items-start">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2">
                       <span className="font-bold text-sm">{p.supplier}</span>
                       <Badge variant={p.status === 'optimal' ? 'active' : 'default'} 
                              className={p.status === 'optimal' ? 'bg-portal-green text-white border-none' : ''}>
                         {p.score}% соответствие
                       </Badge>
                    </div>
                    <p className="text-xs text-text-muted">{p.match}</p>
                    {p.status === 'warning' && (
                      <div className="bg-portal-red/5 text-portal-red text-[10px] font-bold p-2 rounded border border-portal-red/20 inline-block">
                        ⚠️ ТРЕБУЕТСЯ ПРОВЕРКА ХАРАКТЕРИСТИК
                      </div>
                    )}
                  </div>
                  <div className="text-right space-y-2">
                    <p className="font-black text-lg">{p.price.toLocaleString('ru-RU')} ₽</p>
                    <Button size="sm">Выбрать победителя</Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="bg-portal-blue/5 border-portal-blue/20">
            <h3 className="text-xs font-bold text-portal-blue uppercase mb-4">Системное ранжирование (AI)</h3>
            <div className="space-y-4">
               <div className="p-3 bg-white rounded border border-portal-blue/10">
                 <p className="text-[10px] font-bold text-text-muted uppercase mb-1">Рекомендация системы</p>
                 <p className="text-xs font-bold text-portal-blue">ООО "МебельПлюс"</p>
                 <p className="text-[11px] text-text-main mt-1 italic">
                   "Наилучшее сочетание цены и соответствия техническому заданию."
                 </p>
               </div>
               <div className="space-y-2">
                 <p className="text-[10px] font-bold text-text-muted uppercase">Анализ рисков</p>
                 <ul className="text-[11px] space-y-1">
                   <li className="flex gap-2">✅ Поставщик имеет 15+ контрактов</li>
                   <li className="flex gap-2 text-portal-red">❌ Предложение #2 имеет критические отклонения</li>
                   <li className="flex gap-2">✅ Цена в рамках рыночного коридора</li>
                 </ul>
               </div>
            </div>
          </Card>

          <Card>
            <h3 className="text-[10px] font-bold text-text-muted uppercase mb-3">Информация</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                 <span className="text-text-muted">Дата публикации</span>
                 <span className="font-medium">13.03.2026</span>
              </div>
              <div className="flex justify-between">
                 <span className="text-text-muted">Окончание приема</span>
                 <span className="font-medium">15.03.2026</span>
              </div>
              <div className="flex justify-between">
                 <span className="text-text-muted">Код ОКПД2</span>
                 <span className="font-medium">31.01.12.110</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

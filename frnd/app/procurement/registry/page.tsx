'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useRouter } from 'next/navigation';

const procurements = [
  { id: 'DP-001', type: 'Прямая закупка', title: 'Калькулятор настольный (12 ед.)', date: '13.03.2026', status: 'active', amount: '4,776.00 ₽', href: '/direct-purchase/1' },
  { id: 'CS-570824', type: 'Котировочная сессия', title: 'Бумага SvetoCopy A4', date: '12.03.2026', status: 'success', amount: '32,550.00 ₽', href: '/quotation-session/CS-570824' },
  { id: 'ZPP-0042', type: 'Закупка по потребностям', title: 'Офисная мебель', date: '11.03.2026', status: 'active', amount: '150,000.00 ₽', href: '/needs/ZPP-0042' },
];

export default function ProcurementRegistry() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-portal-blue">Реестр закупок</h1>
        <Button variant="primary">+ Новая закупка</Button>
      </div>

      <Card noPadding>
        <table className="w-full text-sm">
          <thead className="bg-bg-page border-b">
            <tr>
              <th className="text-left p-4 font-bold text-text-muted uppercase tracking-tight text-[10px]">Тип / Номер</th>
              <th className="text-left p-4 font-bold text-text-muted uppercase tracking-tight text-[10px]">Наименование закупки</th>
              <th className="text-left p-4 font-bold text-text-muted uppercase tracking-tight text-[10px]">Дата создания</th>
              <th className="text-left p-4 font-bold text-text-muted uppercase tracking-tight text-[10px]">Сумма</th>
              <th className="text-left p-4 font-bold text-text-muted uppercase tracking-tight text-[10px]">Статус</th>
              <th className="text-right p-4 font-bold text-text-muted uppercase tracking-tight text-[10px]">Действия</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-portal">
            {procurements.map((item) => (
              <tr 
                key={item.id} 
                onClick={() => router.push(item.href)}
                className="hover:bg-bg-page transition-colors cursor-pointer border-b last:border-0"
              >
                <td className="p-4">
                  <p className="font-bold text-portal-blue">{item.id}</p>
                  <p className="text-[10px] text-text-muted uppercase">{item.type}</p>
                </td>
                <td className="p-4 font-bold text-text-main">{item.title}</td>
                <td className="p-4 text-text-muted">{item.date}</td>
                <td className="p-4 font-bold">{item.amount}</td>
                <td className="p-4">
                  <Badge variant={item.status as any}>
                    {item.status === 'active' ? 'Новая' : item.status === 'success' ? 'Завершена' : 'Отклонена'}
                  </Badge>
                </td>
                <td className="p-4 text-right">
                  <Button variant="ghost" size="sm">Просмотр</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useRouter } from 'next/navigation';

export default function CreateNeedPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handlePublish = () => {
    setLoading(true);
    setTimeout(() => {
      router.push('/needs/ZPP-2026-0042');
    }, 1500);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-portal-blue">Опубликовать потребность</h1>
        <Badge variant="default">ЗПП</Badge>
      </div>

      <Card className="space-y-6">
        <div className="space-y-4">
          <h3 className="font-bold border-b pb-2">Основные сведения</h3>
          <div className="grid grid-cols-1 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-text-muted uppercase">Предмет закупки (Наименование)</label>
              <input 
                type="text" 
                placeholder="Например: Поставка офисной мебели для учебного центра"
                className="w-full bg-white border border-border-portal rounded-portal-sm px-3 py-2 text-sm font-bold"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
               <div className="space-y-1">
                  <label className="text-[10px] font-bold text-text-muted uppercase">Код ОКПД2</label>
                  <input 
                    type="text" 
                    placeholder="31.01.12.110"
                    className="w-full bg-white border border-border-portal rounded-portal-sm px-3 py-2 text-sm"
                  />
               </div>
               <div className="space-y-1">
                  <label className="text-[10px] font-bold text-text-muted uppercase">Планируемый бюджет (₽)</label>
                  <input 
                    type="number" 
                    placeholder="150 000"
                    className="w-full bg-white border border-border-portal rounded-portal-sm px-3 py-2 text-sm font-bold"
                  />
               </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="font-bold border-b pb-2">Техническое задание</h3>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-text-muted uppercase">Подробное описание требований</label>
            <textarea 
              placeholder="Опишите характеристики товара, требования к качеству и условия поставки..."
              className="w-full bg-white border border-border-portal rounded-portal-sm px-3 py-2 text-sm min-h-[150px]"
            />
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="font-bold border-b pb-2">Условия поставки</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-text-muted uppercase">Место поставки</label>
              <input type="text" value="г. Москва, ул. Вознесенская, д. 4" className="w-full bg-bg-page border border-border-portal rounded-portal-sm px-3 py-2 text-sm" readOnly />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-text-muted uppercase">Срок поставки (дней)</label>
              <input type="number" defaultValue="10" className="w-full bg-white border border-border-portal rounded-portal-sm px-3 py-2 text-sm" />
            </div>
          </div>
        </div>

        <div className="pt-6 flex justify-end gap-3 border-t">
          <Button variant="outline" onClick={() => router.back()}>Отмена</Button>
          <Button onClick={handlePublish} loading={loading}>Опубликовать потребность</Button>
        </div>
      </Card>

      <div className="bg-portal-blue/5 p-4 rounded-portal-md border border-portal-blue/20">
        <h4 className="text-[10px] font-bold text-portal-blue uppercase mb-2">Совет системы</h4>
        <p className="text-xs text-text-main leading-relaxed">
          Для закупок по потребностям (ЗПП) рекомендуется максимально подробно описывать технические характеристики. 
          Это позволит нашей системе точнее ранжировать предложения поставщиков и выявлять несоответствия.
        </p>
      </div>
    </div>
  );
}

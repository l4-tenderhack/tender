'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useRouter } from 'next/navigation';

export default function CreateDirectPurchase() {
  const router = useRouter();
  const [step, setStep] = useState(1);

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
        <h1 className="text-2xl font-bold text-portal-blue">Закупка: Калькулятор настольный</h1>
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
            <h3 className="font-bold text-lg border-b pb-2 mb-4">Основные сведения</h3>
            <div className="grid grid-cols-2 gap-6">
              <InputGroup label="Основание для заключения" value="Пункт 4 части 1 статьи 93 (44-ФЗ)" />
              <InputGroup label="Планируемая дата заключения" value="20.03.2026" />
              <InputGroup label="Источник финансирования" value="Бюджет города Москвы" />
              <InputGroup label="Регион поставки" value="г. Москва" />
            </div>
            <div className="pt-6 flex justify-end">
              <Button onClick={() => setStep(2)}>Далее: Этапы поставки</Button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b pb-2 mb-4">
              <h3 className="font-bold text-lg">График и этапы поставки</h3>
              <Button variant="outline" size="sm">+ Добавить этап</Button>
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
                <tr className="border-b">
                  <td className="p-2 font-bold">1</td>
                  <td className="p-2">Поставка продукции по адресу заказчика</td>
                  <td className="p-2">5</td>
                  <td className="p-2 font-bold">398,00</td>
                  <td className="p-2 text-right">
                    <button className="text-portal-red font-bold">Удалить</button>
                  </td>
                </tr>
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
            <div className="border-2 border-dashed border-border-portal rounded-portal-md p-10 flex flex-col items-center gap-3 text-text-muted">
              <span className="text-4xl">📄</span>
              <p className="font-bold">Перетащите файлы сюда или выберите на компьютере</p>
              <p className="text-xs">Максимальный размер файла 50МБ (doc, pdf, jpg)</p>
              <Button variant="outline" size="sm">Выбрать файлы</Button>
            </div>
            <div className="pt-6 flex justify-between">
              <Button variant="ghost" onClick={() => setStep(2)}>Назад</Button>
              <Button variant="secondary" onClick={() => router.push('/procurement/registry')}>Опубликовать и направить поставщику</Button>
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
    <input 
      disabled 
      value={value} 
      className="w-full bg-bg-page border border-border-portal rounded-portal-sm px-3 py-2 text-sm font-bold text-text-main" 
    />
  </div>
);

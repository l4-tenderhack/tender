'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';

interface CartItem {
  id: string;
  name: string;
  price: number;
  marketPrice: number;
  quantity: number;
  supplier: string;
  customPrice?: boolean;
  justification?: string;
}

const initialCart: CartItem[] = [
  {
    id: '1',
    name: 'Калькулятор настольный 12-разрядный Citizen SDC-888XBK',
    price: 398.00,
    marketPrice: 415.00,
    quantity: 12,
    supplier: 'ОфисМаг-Поволжье'
  },
  {
    id: '2',
    name: 'Ноутбук Aquarius Cmp NS483 (Спец. конфигурация)',
    price: 85000.00,
    marketPrice: 0,
    quantity: 1,
    supplier: 'Аквариус-Торг',
    customPrice: true,
    justification: 'Цена согласована по спец. проекту, рыночные аналоги отсутствуют.'
  }
];

export default function CartPage() {
  const [cart, setCart] = React.useState<CartItem[]>(initialCart);
  const [confirmDeleteId, setConfirmDeleteId] = React.useState<string | null>(null);

  const updateQuantity = (id: string, delta: number) => {
    setCart(prev => prev.map(item =>
      item.id === id ? { ...item, quantity: Math.max(1, item.quantity + delta) } : item
    ));
  };

  const deleteItem = (id: string) => {
    setCart(prev => prev.filter(item => item.id !== id));
    setConfirmDeleteId(null);
  };

  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const totalMarket = cart.reduce((sum, item) => sum + item.marketPrice * item.quantity, 0);
  const savings = totalMarket - total;
  const savingsPercent = totalMarket > 0 ? (savings / totalMarket) * 100 : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-portal-blue">Моя корзина</h1>

      {cart.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 gap-6 bg-bg-page rounded-portal-sm border border-dashed border-border-portal">
          <svg className="w-16 h-16 text-border-portal" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13l-1.5 6h13M7 13L5.4 5M10 21a1 1 0 100-2 1 1 0 000 2zm7 0a1 1 0 100-2 1 1 0 000 2z" />
          </svg>
          <div className="text-center">
            <p className="text-lg font-bold text-text-main">Корзина пуста</p>
            <p className="text-sm text-text-muted mt-1">Добавьте товары из каталога СТЕ</p>
          </div>
          <Link href="/catalog">
            <Button variant="primary">Перейти в каталог</Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            {cart.map((item) => (
              <Card key={item.id} className="flex gap-4">
                <div className="w-20 h-20 bg-bg-page rounded flex items-center justify-center text-portal-blue shrink-0">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 2v20h16V2H4zm13 14H7v-1h10v1zm0-3H7v-1h10v1zm0-3H7V9h10v1zm-3-4H7V6h7v1z"/></svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start gap-2">
                    <h3 className="font-bold text-sm text-text-main">{item.name}</h3>
                    {confirmDeleteId === item.id ? (
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs text-text-muted font-bold">Удалить?</span>
                        <button
                          onClick={() => deleteItem(item.id)}
                          className="text-xs font-bold text-white bg-portal-red px-2 py-0.5 rounded hover:bg-red-700 transition-colors"
                        >
                          Да
                        </button>
                        <button
                          onClick={() => setConfirmDeleteId(null)}
                          className="text-xs font-bold text-text-muted hover:text-text-main transition-colors"
                        >
                          Нет
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmDeleteId(item.id)}
                        className="text-text-muted hover:text-portal-red transition-colors text-xs font-bold shrink-0"
                      >
                        Удалить
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-[10px] text-text-muted uppercase font-bold">{item.supplier}</p>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center border border-border-portal rounded overflow-hidden">
                        <button
                          onClick={() => updateQuantity(item.id, -1)}
                          className="px-2 py-1 bg-bg-page hover:bg-border-portal transition-colors text-sm font-bold"
                        >
                          −
                        </button>
                        <span className="w-10 text-center text-sm font-bold border-x border-border-portal py-1">
                          {item.quantity}
                        </span>
                        <button
                          onClick={() => updateQuantity(item.id, 1)}
                          className="px-2 py-1 bg-bg-page hover:bg-border-portal transition-colors text-sm font-bold"
                        >
                          +
                        </button>
                      </div>
                      <span className="text-sm font-bold">{item.price.toLocaleString('ru-RU')} ₽ / шт.</span>
                    </div>
                    <span className="font-bold text-portal-blue">{(item.price * item.quantity).toLocaleString('ru-RU')} ₽</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <div className="space-y-4">
            <Card className="space-y-4 sticky top-20">
              <h3 className="font-bold text-lg border-b pb-2">Итого</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-text-muted">Товаров ({cart.length})</span>
                  <span className="font-bold">{total.toLocaleString('ru-RU')} ₽</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-text-muted">Доставка</span>
                  <span className="text-portal-green font-bold">Бесплатно</span>
                </div>
              </div>

              {savingsPercent > 0 && (
                <div className="bg-bg-success-light p-3 rounded-portal-sm border border-border-green space-y-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-portal-green-dark uppercase tracking-tight">Системная оценка: Оптимально</span>
                  </div>
                  <p className="text-[11px] text-portal-green-dark leading-tight">
                    Общая экономия относительно рыночных предложений:
                    <span className="font-bold"> {savings.toLocaleString('ru-RU')} ₽ ({savingsPercent.toFixed(1)}%)</span>
                  </p>
                </div>
              )}

              <div className="pt-2 border-t space-y-4">
                <div className="flex justify-between items-end">
                  <span className="text-base font-bold text-portal-blue uppercase">К оплате</span>
                  <span className="text-2xl font-black text-portal-blue">{total.toLocaleString('ru-RU')} ₽</span>
                </div>
                <Link href="/direct-purchase/create" className="block">
                  <Button fullWidth variant="primary">Создать прямую закупку</Button>
                </Link>
                <Link href="/quotation-session/KS-2026-0842" className="block">
                  <Button fullWidth variant="outline">Начать котировочную сессию</Button>
                </Link>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

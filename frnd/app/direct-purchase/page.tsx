'use client';

import React from 'react';
import { SmartPriceAdvisor } from '@/components/SmartPriceAdvisor';

export default function SmartDirectPurchasePage() {
  return (
    <div className="min-h-screen bg-bg-page font-sans text-sm">
      {/* Header Mockup */}
      <header className="bg-white border-b-2 border-portal-red px-10 py-2.5 flex justify-between items-center shadow-md">
        <div className="font-extrabold text-xl text-[#000000]">
          ПОРТАЛ <span className="text-portal-red">ПОСТАВЩИКОВ</span>
        </div>
        <div className="flex items-center gap-5 text-[#111111] font-bold">
          <span>Личный кабинет Заказчика</span>
          <div className="w-8 h-8 bg-gray-500 rounded-full"></div>
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto my-10 px-5">
        <nav className="text-[#111111] font-black mb-2.5 flex gap-2 text-xs uppercase tracking-tight">
          <span>Электронный магазин</span> <span className="text-[#999999] font-normal">/</span> <span>Корзина</span> <span className="text-[#999999] font-normal">/</span> <span className="text-portal-blue font-black underline">Создание закупки</span>
        </nav>
        <h1 className="text-portal-blue text-2xl font-black mb-8">Новая прямая закупка</h1>

        {/* Product Card */}
        <section className="bg-white border-2 border-[#cccccc] rounded-portal-sm p-6 mb-8 shadow-md">
          <h2 className="font-black text-xl mb-6 border-l-8 border-portal-red pl-4 text-[#000000]">Состав закупки</h2>
          <div className="flex gap-8">
            <div className="w-32 h-28 bg-[#f5f5f5] border-2 border-[#dddddd] rounded flex items-center justify-center text-[#000000] shrink-0 font-black text-xs uppercase">
              ФОТО ТОВАРА
            </div>
            <div className="flex-1">
              <span className="bg-[#000000] px-3 py-1 rounded text-[11px] uppercase text-white font-black tracking-widest">СТЕ 1204405</span>
              <h3 className="text-portal-blue text-2xl font-black mt-3">Бумага офисная SvetoCopy A4, 80г/м2, 500л.</h3>
              <div className="text-[#000000] mt-2 font-bold text-base">Поставщик: ООО "Офис-Трейд" (ИНН 7701234567)</div>
              <div className="text-3xl font-black mt-4 text-[#000000]">390.00 ₽ <span className="text-base font-bold text-[#111111]">/ пачка</span></div>
            </div>
          </div>
        </section>

        {/* Smart AI Widget */}
        <SmartPriceAdvisor 
          currentPrice={390} 
          marketAverage={415} 
          minPortalPrice={385} 
        />

        {/* Parameters Section */}
        <section className="bg-white border-2 border-border-portal rounded-portal-sm p-5 mt-6 shadow-md">
          <h2 className="font-black text-lg mb-5 border-l-4 border-portal-red pl-3 text-[#111111]">Параметры поставки</h2>
          <div className="grid grid-cols-2 gap-8">
            <div>
              <label className="block mb-2 font-black text-[#111111] uppercase text-xs tracking-wide">Регион поставки</label>
              <select className="w-full p-2.5 border-2 border-border-portal bg-white font-bold text-[#111111] focus:border-portal-blue outline-none">
                <option>Москва</option>
              </select>
            </div>
            <div>
              <label className="block mb-2 font-black text-[#111111] uppercase text-xs tracking-wide">Срок поставки (рабочих дней)</label>
              <input type="number" defaultValue={3} className="w-full p-2.5 border-2 border-border-portal font-bold text-[#111111] focus:border-portal-blue outline-none" />
            </div>
          </div>
        </section>

        {/* Buttons */}
        <div className="flex gap-4 mt-8">
          <button className="bg-portal-red hover:bg-portal-red-hover text-white px-6 py-3 rounded font-bold transition-colors">
            Отправить на подписание
          </button>
          <button className="bg-transparent border border-portal-red text-portal-red px-6 py-3 rounded font-bold hover:bg-portal-red/5 transition-colors">
            Сохранить черновик
          </button>
          <button className="text-gray-500 underline py-3 hover:text-gray-700">
            Отмена
          </button>
        </div>
      </main>
    </div>
  );
}

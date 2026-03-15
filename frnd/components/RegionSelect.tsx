'use client';

import React, { useEffect, useRef, useState } from 'react';

// Полный список регионов — замените или расширьте по необходимости
const ALL_REGIONS: string[] = [
  'Алтайский край',
  'Амурская',
  'Архангельская область',
  'Астраханская область',
  'Байконур',
  'Белгородская область',
  'Брянская область',
  'Владимирская область',
  'Волгоградская область',
  'Вологодская область',
  'Воронежская область',
  'Еврейская автономная область',
  'Забайкальский край',
  'Ивановская область',
  'Иркутская область',
  'Кабардино-Балкарская Республика',
  'Калининградская область',
  'Калужская область',
  'Камчатский край',
  'Карачаево-Черкесская Республика',
  'Кемеровская область - Кузбасс',
  'Кировская область',
  'Костромская область',
  'Краснодарский',
  'Красноярский край',
  'Курганская область',
  'Курская область',
  'Ленинградская область',
  'Липецкая область',
  'Магаданская область',
  'Москва',
  'Московская область',
  'Мурманская область',
  'Ненецкий автономный округ',
  'Нижегородская область',
  'Новгородская область',
  'Новосибирская область',
  'Омская область',
  'Оренбургская область',
  'Орловская область',
  'Пензенская область',
  'Пермский край',
  'Приморский край',
  'Псковская область',
  'Республика Адыгея',
  'Республика Алтай',
  'Республика Башкортостан',
  'Республика Бурятия',
  'Республика Дагестан',
  'Республика Ингушетия',
  'Республика Калмыкия',
  'Республика Карелия',
  'Республика Коми',
  'Республика Крым',
  'Республика Марий Эл',
  'Республика Мордовия',
  'Республика Саха (Якутия)',
  'Республика Северная Осетия - Алания',
  'Республика Татарстан',
  'Республика Тыва',
  'Республика Хакасия',
  'Ростовская область',
  'Рязанская область',
  'Самарская область',
  'Санкт-Петербург',
  'Саратовская область',
  'Сахалинская область',
  'Свердловская область',
  'Севастополь',
  'Смоленская область',
  'Ставропольский край',
  'Тамбовская область',
  'Тверская область',
  'Томская область',
  'Тульская область',
  'Тюменская область',
  'Удмуртская Республика',
  'Ульяновская область',
  'Хабаровский край',
  'Ханты-Мансийский автономный округ - Югра',
  'Челябинская область',
  'Чеченская Республика',
  'Чувашская Республика - Чувашия',
  'Чукотский автономный округ',
  'Ямало-Ненецкий автономный округ',
  'Ярославская область',
  'Херсонская область',
  'Сургут',
  'Омск',
  'Луганская Народная Республика',
  'Донецкая Народная Республика',
  'Запорожская область',
  'Иваново',
];

interface RegionSelectProps {
  selected: string[];
  onChange: (regions: string[]) => void;
  placeholder?: string;
}

export const RegionSelect: React.FC<RegionSelectProps> = ({
  selected,
  onChange,
  placeholder = 'Регион заказчика...',
}) => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filtered = ALL_REGIONS.filter(r =>
    r.toLowerCase().includes(search.toLowerCase())
  );

  const toggle = (region: string) => {
    if (selected.includes(region)) {
      onChange(selected.filter(r => r !== region));
    } else {
      onChange([...selected, region]);
    }
  };

  const label =
    selected.length === 0
      ? placeholder
      : selected.length === 1
      ? selected[0]
      : `${selected[0]} +${selected.length - 1}`;

  return (
    <div ref={containerRef} className="relative flex-1">
      {/* Trigger */}
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between border border-border-portal rounded-portal-sm px-4 py-2 text-xs bg-white text-left hover:border-portal-blue focus:outline-none focus:ring-1 focus:ring-portal-blue transition-colors"
      >
        <span className={selected.length === 0 ? 'text-gray-400' : 'text-[#222] font-medium'}>
          {label}
        </span>
        <svg
          className={`w-3.5 h-3.5 text-[#999] ml-2 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute z-50 mt-1 w-full min-w-[260px] bg-white border border-border-portal rounded-portal-sm shadow-lg">
          {/* Поиск */}
          <div className="p-2 border-b border-border-portal">
            <input
              autoFocus
              type="text"
              placeholder="Поиск региона..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full border border-border-portal rounded px-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-portal-blue"
            />
          </div>

          {/* Сброс */}
          {selected.length > 0 && (
            <div className="px-3 py-1.5 border-b border-border-portal flex justify-between items-center">
              <span className="text-[10px] text-[#666]">Выбрано: {selected.length}</span>
              <button
                type="button"
                onClick={() => onChange([])}
                className="text-[10px] text-portal-blue hover:underline font-bold"
              >
                Сбросить
              </button>
            </div>
          )}

          {/* Список */}
          <ul className="max-h-56 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <li className="px-4 py-2 text-xs text-[#999]">Ничего не найдено</li>
            ) : (
              filtered.map(region => (
                <li key={region}>
                  <label className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#f4f7f9] cursor-pointer text-xs">
                    <input
                      type="checkbox"
                      checked={selected.includes(region)}
                      onChange={() => toggle(region)}
                      className="accent-portal-blue"
                    />
                    <span>{region}</span>
                  </label>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

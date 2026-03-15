'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { SearchSettingsPanel } from '@/components/SearchSettingsPanel';

const menuItems = [
  { label: 'Каталог СТЕ', href: '/catalog' },
  { label: 'Моя корзина', href: '/cart' },
  { label: 'Реестр закупок', href: '/procurement/registry' },
  { label: 'Котировочные сессии', href: '/quotation-session' },
  { label: 'Закупки по потребностям', href: '/needs/create' },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-border-portal flex flex-col p-4 sticky top-16 h-[calc(100vh-4rem)] overflow-y-auto">
      <nav className="flex-1 space-y-1">
        {menuItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center px-3 py-2 rounded-portal-sm text-sm font-bold transition-colors ${
                isActive
                  ? 'bg-bg-active-light text-portal-blue'
                  : 'text-text-muted hover:bg-bg-page hover:text-text-main'
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <SearchSettingsPanel />
    </aside>
  );
};

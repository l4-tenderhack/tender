'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { Button } from '../ui/Button';
import { getSuggest } from '@/lib/api';
import { useRouter } from 'next/navigation';

export const Navbar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const router = useRouter();
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchSuggest = async () => {
      if (query.trim().length < 2) {
        setSuggestions([]);
        return;
      }
      const sugs = await getSuggest(query, 5);
      setSuggestions(sugs || []);
    };
    
    const timeout = setTimeout(fetchSuggest, 300);
    return () => clearTimeout(timeout);
  }, [query]);

  // Click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [wrapperRef]);

  const handleSearch = (term: string) => {
    setShowDropdown(false);
    // Real implementation would navigate to /catalog?q=term
    router.push('/catalog');
  };

  return (
    <header className="h-16 bg-portal-blue text-white flex items-center justify-between px-6 sticky top-0 z-50">
      <div className="flex items-center gap-8">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-portal-red rounded flex items-center justify-center font-bold text-xl">
            П
          </div>
          <span className="font-bold tracking-tight text-lg uppercase">Портал Поставщиков</span>
        </Link>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3 px-3 py-1.5 bg-white/10 rounded-portal-sm">
          <div className="w-7 h-7 rounded-full bg-white text-portal-blue flex items-center justify-center text-xs font-bold">
            АЗ
          </div>
          <div>
            <p className="text-xs font-bold text-white leading-tight">Админ Заказчика</p>
            <p className="text-[10px] text-white/60 leading-tight">ГБОУ Школа № 554</p>
          </div>
        </div>
        <div className="w-px h-6 bg-white/20" />
        <Button variant="ghost" size="sm" className="text-white hover:bg-white/10" onClick={() => alert('По вопросам технической поддержки обращайтесь по адресу: support@portalpostavshikov.ru или по телефону: 8-800-555-35-35 (бесплатно)')}>
          Служба поддержки
        </Button>
      </div>
    </header>
  );
};

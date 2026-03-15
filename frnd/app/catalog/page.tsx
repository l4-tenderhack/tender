'use client';

import React from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { SmartPriceAdvisor } from '@/components/SmartPriceAdvisor';
import { RegionSelect } from '@/components/RegionSelect';
import { cteSearch, getFacets, CteSearchRequest, CteSearchResponse, CteMatch } from '@/lib/api';
import { useSearchSettings } from '@/context/SearchSettingsContext';

interface Product {
  id: string;
  name: string;
  category: string;
  price: number;
  oldPrice?: number;
  supplier: string;
  region: string;
  image: string;
  noData?: boolean;
  characteristics: Record<string, any>;
}

const mockProducts: Product[] = [
  {
    id: '1',
    name: 'Калькулятор настольный 12-разрядный Citizen SDC-888XBK',
    category: 'Канцелярские товары',
    price: 398.00,
    oldPrice: 440.00,
    supplier: 'ОфисМаг-Поволжье',
    region: 'г. Москва',
    image: 'https://placehold.co/400x400/f7f8f9/cccccc?text=СТЕ',
    characteristics: {}
  },
  {
    id: '3',
    name: 'Ноутбук Aquarius Cmp NS483 (Спец. конфигурация)',
    category: 'Вычислительная техника',
    price: 85000.00,
    supplier: 'Аквариус-Торг',
    region: 'г. Москва',
    image: 'https://placehold.co/400x400/f7f8f9/cccccc?text=СТЕ',
    noData: true,
    characteristics: {}
  }
];

export default function CatalogPage() {
  const { cteSearchN, scoreThreshold } = useSearchSettings();
  const [products, setProducts] = React.useState<Product[]>(mockProducts);
  const [loading, setLoading] = React.useState(true);
  const [query, setQuery] = React.useState('');
  const [region, setRegion] = React.useState('');
  const [inn, setInn] = React.useState('');
  const [searchInput, setSearchInput] = React.useState('');
  const [selectedRegions, setSelectedRegions] = React.useState<string[]>([]);
  const [innInput, setInnInput] = React.useState('');
  const [total, setTotal] = React.useState(2415);
  const [categories, setCategories] = React.useState<any[]>([]);
  
  // New state for client-side filtering
  const [availableCharacteristics, setAvailableCharacteristics] = React.useState<Record<string, string[]>>({});
  const [selectedFilters, setSelectedFilters] = React.useState<Record<string, string>>({});
  const [showFilters, setShowFilters] = React.useState(false);

  // Sorting
  type SortOption = 'price_asc' | 'price_desc' | 'name_asc' | 'name_desc' | 'category_asc';
  const [sortBy, setSortBy] = React.useState<SortOption | null>(null);
  const [showSortMenu, setShowSortMenu] = React.useState(false);

  const sortMenuRef = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (sortMenuRef.current && !sortMenuRef.current.contains(e.target as Node)) {
        setShowSortMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const sortOptions: { value: SortOption; label: string }[] = [
    { value: 'price_asc', label: 'По цене: сначала дешевле' },
    { value: 'price_desc', label: 'По цене: сначала дороже' },
    { value: 'name_asc', label: 'По названию: А → Я' },
    { value: 'name_desc', label: 'По названию: Я → А' },
    { value: 'category_asc', label: 'По категории: А → Я' },
  ];

  const handleSearch = () => {
    setQuery(searchInput);
    setRegion(selectedRegions.join(', '));
    setInn(innInput);
    setSelectedFilters({}); // Reset filters on new search
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const toggleFilter = (key: string, value: string) => {
    setSelectedFilters(prev => {
      const next = { ...prev };
      if (next[key] === value) {
        delete next[key];
      } else {
        next[key] = value;
      }
      return next;
    });
  };

  React.useEffect(() => {
    const fetchCatalog = async () => {
      setLoading(true);
      try {
        const req: CteSearchRequest = { 
          query: query || '*',
          n: cteSearchN,
          region: region || null,
          inn: inn || null,
          score_threshold: scoreThreshold,
        };
        const data: CteSearchResponse = await cteSearch(req);
        
        if (data.matched_ctes && data.matched_ctes.length > 0) {
           setTotal(data.total_contracts); // Or matched_ctes.length if we want CTE count
           setProducts(data.matched_ctes.map((p: CteMatch) => ({
             id: p.cte_id,
             name: p.description || p.cte_name,
             category: p.category || 'СТЕ',
             price: p.price,
             supplier: p.manufacturer || 'Неизвестен',
             region: p.region || 'Не указан',
             image: 'https://placehold.co/400x400/f7f8f9/cccccc?text=СТЕ',
             noData: p.price === 0,
             characteristics: p.characteristics || {}
           })));
           setAvailableCharacteristics(data.available_characteristics || {});
        } else {
           setProducts([]);
           setTotal(0);
           setAvailableCharacteristics({});
        }

        // Keep facets for categories if needed, though cteSearch might return them in matched_ctes or elsewhere
        const f = await getFacets(query || '*');
        if (f.category) {
           setCategories(f.category);
        }
      } catch (e) {
        console.error('Failed to load catalog from backend', e);
      } finally {
        setLoading(false);
      }
    };

    fetchCatalog();
  }, [query, region, inn, cteSearchN, scoreThreshold]);

  // Client-side filtering + sorting logic
  const filteredProducts = React.useMemo(() => {
    let result = Object.keys(selectedFilters).length === 0
      ? products
      : products.filter(product =>
          Object.entries(selectedFilters).every(([key, value]) => product.characteristics[key] === value)
        );

    if (sortBy) {
      result = [...result].sort((a, b) => {
        switch (sortBy) {
          case 'price_asc': return a.price - b.price;
          case 'price_desc': return b.price - a.price;
          case 'name_asc': return a.name.localeCompare(b.name, 'ru');
          case 'name_desc': return b.name.localeCompare(a.name, 'ru');
          case 'category_asc': return a.category.localeCompare(b.category, 'ru');
        }
      });
    }

    return result;
  }, [products, selectedFilters, sortBy]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-portal-blue">Каталог СТЕ</h1>
          <p className="text-text-muted text-sm">
            {total > 0 ? `Найдено ${total} товаров по вашему запросу` : 'Товары не найдены'}
          </p>
        </div>
        <div className="flex gap-3">
          <Button 
            variant={showFilters ? "primary" : "outline"} 
            size="sm" 
            onClick={() => setShowFilters(!showFilters)}
          >
            Фильтры {Object.keys(selectedFilters).length > 0 && `(${Object.keys(selectedFilters).length})`}
          </Button>
          <div className="relative" ref={sortMenuRef}>
            <Button variant="outline" size="sm" onClick={() => setShowSortMenu(v => !v)}>
              {sortBy ? sortOptions.find(o => o.value === sortBy)?.label : 'Сортировка'}
              <svg className="ml-1 w-3 h-3 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
            </Button>
            {showSortMenu && (
              <div className="absolute right-0 top-full mt-1 bg-white border border-border-portal rounded-portal-sm shadow-lg z-20 w-56 py-1">
                {sortOptions.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => { setSortBy(opt.value); setShowSortMenu(false); }}
                    className={`w-full text-left px-4 py-2 text-sm font-bold transition-colors ${sortBy === opt.value ? 'text-portal-blue bg-bg-active-light' : 'text-text-main hover:bg-bg-page'}`}
                  >
                    {opt.label}
                  </button>
                ))}
                {sortBy && (
                  <>
                    <div className="border-t border-border-portal my-1" />
                    <button
                      onClick={() => { setSortBy(null); setShowSortMenu(false); }}
                      className="w-full text-left px-4 py-2 text-sm font-bold text-portal-red hover:bg-bg-page"
                    >
                      Сбросить сортировку
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-3 mb-6">
        <div className="flex gap-4">
          <input 
            type="text" 
            placeholder="Поиск по наименованию СТЕ..." 
            className="flex-1 border border-border-portal rounded-portal-sm px-4 py-2 text-sm focus:ring-1 focus:ring-portal-blue outline-none"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <Button onClick={handleSearch} className="px-8">Найти</Button>
        </div>
        <div className="flex gap-4">
          <RegionSelect
            selected={selectedRegions}
            onChange={setSelectedRegions}
          />
          <input 
            type="text" 
            placeholder="ИНН организации..." 
            className="flex-1 border border-border-portal rounded-portal-sm px-4 py-2 text-xs"
            value={innInput}
            onChange={(e) => setInnInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>
      </div>

      <div className="flex gap-6">
        {/* Characteristics Sidebar */}
        {showFilters && Object.keys(availableCharacteristics).length > 0 && (
          <div className="w-64 flex-shrink-0 space-y-6 bg-white p-4 rounded-portal-sm border border-border-portal h-fit max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-2">
              <h3 className="font-bold text-sm">Характеристики</h3>
              {Object.keys(selectedFilters).length > 0 && (
                <button 
                  onClick={() => setSelectedFilters({})}
                  className="text-[10px] text-portal-blue hover:underline font-bold"
                >
                  Сбросить
                </button>
              )}
            </div>
            {Object.entries(availableCharacteristics)
              .sort(([, a], [, b]) => b.length - a.length)
              .map(([key, values]) => (
              <div key={key} className="space-y-2">
                <h4 className="text-xs font-bold text-text-main">{key}</h4>
                <div className="flex flex-wrap gap-1">
                  {values.map(value => (
                    <button
                      key={value}
                      onClick={() => toggleFilter(key, value)}
                      className={`text-[10px] px-2 py-1 rounded-full border transition-colors ${
                        selectedFilters[key] === value
                          ? "bg-portal-blue text-white border-portal-blue"
                          : "bg-bg-page text-text-muted border-border-portal hover:border-portal-blue"
                      }`}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex-1">
          {loading ? (
             <div className="flex justify-center p-12"><div className="animate-spin h-8 w-8 border-4 border-portal-blue border-t-transparent rounded-full" /></div>
          ) : filteredProducts.length > 0 ? (
            <div className={`grid grid-cols-1 md:grid-cols-2 ${showFilters ? 'lg:grid-cols-2 xl:grid-cols-3' : 'lg:grid-cols-3 xl:grid-cols-4'} gap-6`}>
              {filteredProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <div className="text-center p-12 text-text-muted font-bold block bg-bg-page rounded-portal-sm border border-dashed border-border-portal">
               {products.length === 0 
                 ? `Товары по запросу "${query}" не найдены`
                 : "Нет товаров, соответствующих выбранным фильтрам"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const ProductCard = ({ product }: { product: any }) => {
  const [showAdvisor, setShowAdvisor] = React.useState(false);
  const [customPrice, setCustomPrice] = React.useState(product.price);

  return (
    <Card className="flex flex-col h-full hover:shadow-md transition-shadow group">
      <div className="relative h-48 mb-4 bg-bg-page rounded-portal-sm overflow-hidden flex items-center justify-center">
        <img src={product.image} alt="" className="max-h-full transition-transform group-hover:scale-105" />
        <div className="absolute top-2 left-2">
          <Badge variant="active">{product.category}</Badge>
        </div>
      </div>
      
      <div className="flex-1 mb-4">
        <h3 className="font-bold text-sm text-text-main line-clamp-2 min-h-[40px] group-hover:text-portal-blue transition-colors">
          {product.name}
        </h3>
        <p className="text-[10px] text-text-muted mt-1 uppercase font-bold">{product.supplier}</p>
      </div>

      <div className="mb-4">
        <div className="flex items-baseline gap-2">
          <div className="flex flex-col">
            <span className="text-[10px] text-text-muted">Последняя закупочная цена</span>
            <span className="text-xl font-bold text-text-main">{product.price.toLocaleString('ru-RU')} ₽</span>
          </div>
          {product.oldPrice && (
            <span className="text-xs text-text-muted line-through">{product.oldPrice.toLocaleString('ru-RU')} ₽</span>
          )}
        </div>
        <p className="text-[10px] text-text-muted font-bold">{product.region}</p>
      </div>

      <div className="space-y-3">
        <div className="bg-bg-active-light/50 p-2 rounded border border-border-blue/30 cursor-pointer hover:bg-bg-active-light transition-colors" onClick={() => setShowAdvisor(!showAdvisor)}>
          <SmartPriceAdvisor compact noData={product.noData} cteId={product.id} cteName={product.name} />
        </div>
        
        {showAdvisor && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="max-w-5xl w-full">
              <SmartPriceAdvisor 
                noData={product.noData} 
                cteId={product.id}
                cteName={product.name}
                currentPrice={customPrice}
                onPriceChange={(price) => {
                  setCustomPrice(price);
                  setShowAdvisor(false);
                }}
              />
              <Button fullWidth variant="ghost" onClick={() => setShowAdvisor(false)} className="mt-2 bg-portal-red text-white hover:bg-portal-red hover:text-white">Закрыть</Button>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <Link href="/cart" className="flex-1">
            <Button fullWidth size="sm">В корзину</Button>
          </Link>
        </div>
      </div>
    </Card>
  );
};

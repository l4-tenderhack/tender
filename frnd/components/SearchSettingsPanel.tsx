'use client';

import React from 'react';
import { useSearchSettings } from '@/context/SearchSettingsContext';

export const SearchSettingsPanel: React.FC = () => {
  const { cteSearchN, setCteSearchN, scoreThreshold, setScoreThreshold } = useSearchSettings();

  return (
    <div className="mt-4 pt-4 border-t border-border-portal space-y-4">
      <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-2">
        Настройки запроса
      </p>
      <div className="space-y-1.5">
        <label className="text-[10px] font-bold text-text-muted uppercase tracking-tight block">
          n (кол-во КТЕ)
        </label>
        <input
          type="number"
          min={1}
          max={100}
          value={cteSearchN}
          onChange={(e) => setCteSearchN(parseInt(e.target.value, 10) || 10)}
          className="w-full text-sm border border-border-portal rounded px-2 py-1.5 focus:ring-1 focus:ring-portal-blue focus:border-portal-blue"
        />
      </div>
      <div className="space-y-1.5">
        <label className="text-[10px] font-bold text-text-muted uppercase tracking-tight block">
          Порог скора (score_threshold)
        </label>
        <input
          type="number"
          min={0}
          max={1}
          step={0.01}
          value={scoreThreshold}
          onChange={(e) => setScoreThreshold(parseFloat(e.target.value) || 0.53)}
          className="w-full text-sm border border-border-portal rounded px-2 py-1.5 focus:ring-1 focus:ring-portal-blue focus:border-portal-blue"
        />
      </div>
    </div>
  );
};

'use client';

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';

const STORAGE_KEY_N = 'search_settings_n';
const STORAGE_KEY_THRESHOLD = 'search_settings_score_threshold';

const DEFAULT_N = 10;
const DEFAULT_THRESHOLD = 0.53;

interface SearchSettingsContextValue {
  cteSearchN: number;
  setCteSearchN: (value: number) => void;
  scoreThreshold: number;
  setScoreThreshold: (value: number) => void;
}

const SearchSettingsContext = createContext<SearchSettingsContextValue | null>(null);

function readStoredN(): number {
  if (typeof window === 'undefined') return DEFAULT_N;
  try {
    const v = localStorage.getItem(STORAGE_KEY_N);
    if (v === null || v === '') return DEFAULT_N;
    const n = parseInt(v, 10);
    return Number.isFinite(n) && n >= 1 && n <= 100 ? n : DEFAULT_N;
  } catch {
    return DEFAULT_N;
  }
}

function readStoredThreshold(): number {
  if (typeof window === 'undefined') return DEFAULT_THRESHOLD;
  try {
    const v = localStorage.getItem(STORAGE_KEY_THRESHOLD);
    if (v === null || v === '') return DEFAULT_THRESHOLD;
    const t = parseFloat(v);
    return Number.isFinite(t) && t >= 0 && t <= 1 ? t : DEFAULT_THRESHOLD;
  } catch {
    return DEFAULT_THRESHOLD;
  }
}

export function SearchSettingsProvider({ children }: { children: React.ReactNode }) {
  const [cteSearchN, setCteSearchNState] = useState<number>(DEFAULT_N);
  const [scoreThreshold, setScoreThresholdState] = useState<number>(DEFAULT_THRESHOLD);

  useEffect(() => {
    setCteSearchNState(readStoredN());
    setScoreThresholdState(readStoredThreshold());
  }, []);

  const setCteSearchN = useCallback((value: number) => {
    const n = Math.min(100, Math.max(1, value));
    setCteSearchNState(n);
    try {
      localStorage.setItem(STORAGE_KEY_N, String(n));
    } catch {}
  }, []);

  const setScoreThreshold = useCallback((value: number) => {
    const t = Math.min(1, Math.max(0, value));
    setScoreThresholdState(t);
    try {
      localStorage.setItem(STORAGE_KEY_THRESHOLD, String(t));
    } catch {}
  }, []);

  return (
    <SearchSettingsContext.Provider
      value={{
        cteSearchN,
        setCteSearchN,
        scoreThreshold,
        setScoreThreshold,
      }}
    >
      {children}
    </SearchSettingsContext.Provider>
  );
}

export function useSearchSettings(): SearchSettingsContextValue {
  const ctx = useContext(SearchSettingsContext);
  if (!ctx) {
    return {
      cteSearchN: DEFAULT_N,
      setCteSearchN: () => {},
      scoreThreshold: DEFAULT_THRESHOLD,
      setScoreThreshold: () => {},
    };
  }
  return ctx;
}

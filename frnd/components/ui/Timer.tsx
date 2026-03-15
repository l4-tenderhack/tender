'use client';

import React, { useState, useEffect } from 'react';

interface TimerProps {
  initialSeconds: number;
  onExpire?: () => void;
  className?: string;
}

export const Timer: React.FC<TimerProps> = ({
  initialSeconds,
  onExpire,
  className = '',
}) => {
  const [timeLeft, setTimeLeft] = useState(initialSeconds);

  useEffect(() => {
    if (timeLeft <= 0) {
      if (onExpire) onExpire();
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, onExpire]);

  const formatTime = (seconds: number) => {
    const d = Math.floor(seconds / (3600 * 24));
    const h = Math.floor((seconds % (3600 * 24)) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;

    return {
      d: String(d).padStart(2, '0'),
      h: String(h).padStart(2, '0'),
      m: String(m).padStart(2, '0'),
      s: String(s).padStart(2, '0'),
    };
  };

  const { d, h, m, s } = formatTime(timeLeft);

  return (
    <div className={`flex gap-3 ${className}`}>
      <TimeUnit value={d} label="Дней" />
      <TimeUnit value={h} label="Часов" />
      <TimeUnit value={m} label="Минут" />
      <TimeUnit value={s} label="Секунд" />
    </div>
  );
};

const TimeUnit = ({ value, label }: { value: string; label: string }) => (
  <div className="flex flex-col items-center">
    <div className="bg-bg-page border border-border-portal rounded px-2 py-1 text-lg font-bold min-w-[40px] text-center">
      {value}
    </div>
    <span className="text-[10px] text-text-muted mt-1 uppercase font-bold tracking-wider">{label}</span>
  </div>
);

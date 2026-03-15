'use client';

import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';

interface Bid {
  id: string;
  bidder: string;
  amount: number;
  time: string;
  isMe?: boolean;
}

interface BiddingPanelProps {
  initialPrice: number;
  minStep?: number;
  onPlaceBid?: (amount: number) => void;
}

export const BiddingPanel: React.FC<BiddingPanelProps> = ({
  initialPrice,
  minStep = 1.0,
  onPlaceBid,
}) => {
  const [bids, setBids] = useState<Bid[]>([
    { id: '1', bidder: 'ООО "ТехноПром"', amount: initialPrice - 15, time: '14:20:15' },
    { id: '2', bidder: 'ИП Иванов А.В.', amount: initialPrice - 10, time: '14:15:00' },
  ]);
  const [myBid, setMyBid] = useState<number | null>(null);
  const [inputBid, setInputBid] = useState('');

  const currentBest = Math.min(...bids.map(b => b.amount));
  const nextTarget = currentBest - minStep;

  const handleBid = () => {
    const amount = parseFloat(inputBid);
    if (isNaN(amount) || amount >= currentBest) return;

    const newBid: Bid = {
      id: Date.now().toString(),
      bidder: 'Моя организация',
      amount,
      time: new Date().toLocaleTimeString('ru-RU', { hour12: false }),
      isMe: true,
    };

    setBids([newBid, ...bids]);
    setMyBid(amount);
    setInputBid('');
    onPlaceBid?.(amount);
  };

  return (
    <Card className="flex flex-col h-full bg-white border-2 border-portal-blue/10">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-portal-blue font-bold text-lg">Текущие торги</h3>
          <p className="text-xs text-text-muted mt-0.5 uppercase tracking-wider font-bold">Активные ставки поставщиков</p>
        </div>
        <Badge variant="active" className="bg-portal-blue text-white px-3 py-1 text-xs">LIVE</Badge>
      </div>

      <div className="flex items-center justify-between p-4 bg-bg-page rounded-portal-md border border-border-portal mb-6">
        <div>
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-tighter">Лучшее предложение</span>
          <div className="text-2xl font-black text-portal-blue">{currentBest.toLocaleString('ru-RU')} ₽</div>
        </div>
        <div className="text-right">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-tighter">Снижение</span>
          <div className="text-lg font-bold text-portal-green">-{((initialPrice - currentBest) / initialPrice * 100).toFixed(1)}%</div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 mb-6 pr-1 max-h-[300px]">
        {bids.map((bid) => (
          <div 
            key={bid.id} 
            className={`flex items-center justify-between p-3 rounded border transition-all ${
              bid.isMe ? 'bg-bg-active-light border-portal-blue shadow-portal-sm' : 'bg-white border-border-portal/50'
            }`}
          >
            <div>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-bold ${bid.isMe ? 'text-portal-blue' : 'text-text-main'}`}>
                  {bid.bidder}
                </span>
                {bid.isMe && <Badge className="text-[8px] px-1 py-0 bg-portal-blue text-white">ВЫ</Badge>}
              </div>
              <span className="text-[10px] text-text-muted font-medium">{bid.time}</span>
            </div>
            <div className="text-right">
              <div className={`font-black ${bid.isMe ? 'text-portal-blue text-lg' : 'text-text-main'}`}>
                {bid.amount.toLocaleString('ru-RU')} ₽
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-auto space-y-4 pt-4 border-t">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input 
              type="number" 
              placeholder={`Мин. шаг: ${nextTarget} ₽`}
              value={inputBid}
              onChange={(e) => setInputBid(e.target.value)}
              className="w-full bg-white border border-border-portal rounded-portal-sm pl-3 pr-8 py-3 text-sm font-bold focus:ring-2 focus:ring-portal-blue/20 outline-none"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted font-bold text-xs">₽</span>
          </div>
          <Button onClick={handleBid} className="min-w-[120px]">Ставка</Button>
        </div>
        
        <div className="grid grid-cols-2 gap-2">
           <Button variant="outline" size="sm" onClick={() => setInputBid(String(currentBest - 5))}>
             {currentBest - 5} ₽
           </Button>
           <Button variant="outline" size="sm" onClick={() => setInputBid(String(currentBest - 10))}>
             {currentBest - 10} ₽
           </Button>
        </div>
      </div>
    </Card>
  );
};

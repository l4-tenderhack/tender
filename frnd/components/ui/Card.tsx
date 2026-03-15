import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  noPadding = false,
}) => {
  return (
    <div className={`bg-bg-card border border-border-portal rounded-portal-md shadow-portal-light ${!noPadding ? 'p-4' : ''} ${className}`}>
      {children}
    </div>
  );
};

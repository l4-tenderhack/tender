import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'active' | 'success' | 'error' | 'default';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  className = '',
}) => {
  const baseStyles = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border';
  
  const variants = {
    active: 'bg-bg-active-light text-portal-blue border-border-blue',
    success: 'bg-bg-success-light text-portal-green-dark border-border-green',
    error: 'bg-bg-error-light text-portal-red border-border-red',
    default: 'bg-bg-page text-text-muted border-border-portal'
  };
  
  return (
    <span className={`${baseStyles} ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};

import { useEffect, useState } from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'w-5 h-5 border-2',
  md: 'w-8 h-8 border-2',
  lg: 'w-12 h-12 border-4',
};

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  return (
    <div
      className={`rounded-full border-t-2 border-primary-600 animate-spin ${sizeClasses[size]} ${className}`}
      style={{ borderTopColor: '#9333ea', borderColor: '#e9d5ff' }}
    />
  );
}

interface FullPageLoaderProps {
  message?: string;
}

export function FullPageLoader({ message = 'Loading...' }: FullPageLoaderProps) {
  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex flex-col items-center justify-center transition-opacity duration-300">
      <LoadingSpinner size="lg" />
      <p className="mt-4 text-white font-medium drop-shadow-md">{message}</p>
    </div>
  );
}

interface ButtonSpinnerProps {
  size?: 'sm' | 'md';
  className?: string;
}

export function ButtonSpinner({ size = 'sm', className = '' }: ButtonSpinnerProps) {
  const sizeClass = size === 'sm' ? 'w-4 h-4 border-2' : 'w-5 h-5 border-2';
  return (
    <div
      className={`rounded-full border-white/50 border-t-white animate-spin ${sizeClass} ${className}`}
      style={{ borderTopColor: '#ffffff' }}
    />
  );
}

interface InlineLoadingProps {
  text?: string;
  size?: 'sm' | 'md';
}

export function InlineLoading({ text = 'Loading...', size = 'sm' }: InlineLoadingProps) {
  return (
    <span className="flex items-center gap-2">
      <ButtonSpinner size={size} />
      <span className={size === 'sm' ? 'text-xs' : 'text-sm'}>{text}</span>
    </span>
  );
}

// Fade-in wrapper for content with loading state
interface FadeInContentProps {
  isLoading: boolean;
  children?: React.ReactNode;
  loadingComponent?: React.ReactNode;
  minHeight?: string;
}

export function FadeInContent({
  isLoading,
  children,
  loadingComponent,
  minHeight = 'min-h-[200px]'
}: FadeInContentProps) {
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      // Small delay for smooth fade-in effect
      const timer = setTimeout(() => setShowContent(true), 50);
      return () => clearTimeout(timer);
    } else {
      setShowContent(false);
    }
  }, [isLoading]);

  return (
    <div className={`relative ${minHeight}`}>
      {/* Loading State */}
      {isLoading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-10 transition-opacity duration-300">
          {loadingComponent || (
            <>
              <LoadingSpinner size="lg" />
              <p className="mt-4 text-dark-500 text-lg">Loading...</p>
            </>
          )}
        </div>
      )}

      {/* Content with fade-in */}
      <div
        className={`transition-opacity duration-300 ${
          showContent && !isLoading ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
      >
        {children}
      </div>
    </div>
  );
}

// Skeleton loader with primary purple accent
interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-gradient-to-r from-dark-100 via-dark-50 to-dark-100 bg-[length:200%_100%] rounded-lg ${className}`}
    />
  );
}

// KPI Card skeleton with purple spinner
export function KPICardSkeleton() {
  return (
    <div className="bg-surface-50 rounded-xl p-5 shadow-sm border border-dark-100">
      <div className="flex flex-col items-center justify-center min-h-[100px]">
        <LoadingSpinner size="lg" />
      </div>
    </div>
  );
}

export default LoadingSpinner;
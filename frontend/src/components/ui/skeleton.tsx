import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

/**
 * Animated Skeleton loader with shimmer effect
 */
function Skeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  ...props
}: SkeletonProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden bg-gray-200',
        variant === 'circular' && 'rounded-full',
        variant === 'rectangular' && 'rounded-lg',
        variant === 'text' && 'rounded',
        className
      )}
      style={{ width, height }}
      {...props}
    >
      <motion.div
        className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200"
        animate={{ x: ['0%', '100%'] }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
    </div>
  );
}

/**
 * Skeleton variants for common use cases
 */
function CardSkeleton() {
  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-4">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="space-y-2 flex-1">
          <Skeleton variant="text" height={16} className="w-3/4" />
          <Skeleton variant="text" height={12} className="w-1/2" />
        </div>
      </div>
      <Skeleton variant="rectangular" height={100} />
    </div>
  );
}

function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <div className="flex items-center space-x-4 p-4 border-b">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          height={16}
          className="flex-1"
          style={{ width: `${Math.random() * 40 + 60}%` }}
        />
      ))}
    </div>
  );
}

function StatsCardSkeleton() {
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton variant="circular" width={48} height={48} />
        <Skeleton variant="text" width={60} height={32} />
      </div>
      <Skeleton variant="text" height={14} className="w-2/3" />
      <Skeleton variant="text" height={12} className="w-1/3" />
    </div>
  );
}

export { Skeleton, CardSkeleton, TableRowSkeleton, StatsCardSkeleton };

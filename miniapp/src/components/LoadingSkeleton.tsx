/* ============================================
   LoadingSkeleton — Shimmer placeholders
   ============================================ */

interface SkeletonProps {
  className?: string;
}

/** Single skeleton bar */
export function Skeleton({ className = '' }: SkeletonProps) {
  return <div className={`skeleton ${className}`} />;
}

/** Stats cards skeleton (2x2 grid) */
export function StatsCardsSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-3">
      {[...Array(4)].map((_, i) => (
        <div
          key={i}
          className="rounded-2xl p-4"
          style={{ backgroundColor: 'var(--tg-secondary-bg)' }}
        >
          <Skeleton className="h-4 w-16 mb-2" />
          <Skeleton className="h-8 w-12" />
        </div>
      ))}
    </div>
  );
}

/** Gamification card skeleton */
export function GamificationCardSkeleton() {
  return (
    <div
      className="rounded-2xl p-5"
      style={{ backgroundColor: 'var(--tg-secondary-bg)' }}
    >
      <Skeleton className="h-5 w-32 mb-4" />
      <div className="flex justify-between">
        <div>
          <Skeleton className="h-4 w-16 mb-1" />
          <Skeleton className="h-7 w-20" />
        </div>
        <div>
          <Skeleton className="h-4 w-16 mb-1" />
          <Skeleton className="h-7 w-12" />
        </div>
        <div>
          <Skeleton className="h-4 w-16 mb-1" />
          <Skeleton className="h-7 w-10" />
        </div>
      </div>
    </div>
  );
}

/** Check-in history list skeleton */
export function HistoryListSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-3 rounded-xl p-3"
          style={{ backgroundColor: 'var(--tg-secondary-bg)' }}
        >
          <Skeleton className="h-10 w-10 rounded-full shrink-0" />
          <div className="flex-1">
            <Skeleton className="h-4 w-24 mb-1" />
            <Skeleton className="h-3 w-32" />
          </div>
          <Skeleton className="h-6 w-14 rounded-full" />
        </div>
      ))}
    </div>
  );
}

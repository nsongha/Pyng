/* ============================================
   LoadingSkeleton — Shimmer placeholders
   ============================================ */

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

/** Single skeleton bar */
export function Skeleton({ className = '', style }: SkeletonProps) {
  return <div className={`skeleton ${className}`} style={style} />;
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

/** Charts page — working hours chart skeleton */
export function ChartSkeleton() {
  return (
    <div
      className="rounded-2xl p-4"
      style={{
        backgroundColor: 'var(--tg-section-bg)',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      <Skeleton className="h-4 w-28 mb-3" />
      <Skeleton className="h-[180px] w-full rounded-xl" />
    </div>
  );
}

/** Charts page — 3-column stats summary skeleton */
export function StatsSummarySkeleton() {
  return (
    <div className="grid grid-cols-3 gap-3">
      {[...Array(3)].map((_, i) => (
        <div
          key={i}
          className="rounded-xl p-3 text-center"
          style={{
            backgroundColor: 'var(--tg-section-bg)',
            boxShadow: 'var(--shadow-card)',
          }}
        >
          <Skeleton className="h-6 w-12 mx-auto mb-1" />
          <Skeleton className="h-3 w-14 mx-auto" />
        </div>
      ))}
    </div>
  );
}

/** Leave page — balance card skeleton */
export function LeaveBalanceSkeleton() {
  return (
    <div
      className="rounded-2xl p-4"
      style={{
        background: 'linear-gradient(135deg, #5E5CE6 0%, #AF52DE 100%)',
      }}
    >
      <Skeleton className="h-3 w-24 mb-2" style={{ opacity: 0.3 }} />
      <Skeleton className="h-10 w-32 mb-3" style={{ opacity: 0.3 }} />
      <Skeleton className="h-1.5 w-full rounded-full" style={{ opacity: 0.3 }} />
    </div>
  );
}

/** Leave page — leave list items skeleton */
export function LeaveListItemsSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      {[...Array(3)].map((_, i) => (
        <div
          key={i}
          className="rounded-xl p-3.5"
          style={{
            backgroundColor: 'var(--tg-section-bg)',
            boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
          }}
        >
          <div className="flex justify-between mb-2">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <Skeleton className="h-4 w-32 mb-1" />
          <Skeleton className="h-3 w-48" />
        </div>
      ))}
    </div>
  );
}


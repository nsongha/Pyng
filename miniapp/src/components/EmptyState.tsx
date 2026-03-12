/* ============================================
   EmptyState — Reusable empty data display
   Cho first-time users hoặc khi chưa có data
   ============================================ */

interface EmptyStateProps {
  /** Large emoji icon */
  icon: string;
  /** Title text */
  title: string;
  /** Description / hướng dẫn */
  description: string;
  /** Optional CTA button */
  actionLabel?: string;
  /** CTA callback */
  onAction?: () => void;
  /** Custom class */
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className = '',
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center py-12 px-6 text-center animate-fade-in ${className}`}
    >
      {/* Large illustration icon */}
      <div className="text-6xl mb-4 animate-bounce-in">{icon}</div>

      <h3
        className="text-base font-semibold mb-1.5"
        style={{ color: 'var(--tg-text)' }}
      >
        {title}
      </h3>

      <p
        className="text-sm max-w-[260px] leading-relaxed mb-5"
        style={{ color: 'var(--tg-hint)' }}
      >
        {description}
      </p>

      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="px-5 py-2 rounded-full text-sm font-medium active:scale-95 transition-transform"
          style={{
            backgroundColor: 'var(--tg-secondary-bg)',
            color: 'var(--tg-text)',
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

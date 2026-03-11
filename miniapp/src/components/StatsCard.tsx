/* ============================================
   StatsCard — Hiển thị một stat metric
   ============================================ */

interface StatsCardProps {
  label: string;
  value: number | string;
  emoji: string;
  /** Optional accent color for value */
  accentColor?: string;
}

export function StatsCard({
  label,
  value,
  emoji,
  accentColor,
}: StatsCardProps) {
  return (
    <div
      className="rounded-2xl p-4 transition-transform active:scale-95"
      style={{ backgroundColor: 'var(--tg-section-bg)' }}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-base">{emoji}</span>
        <span
          className="text-xs font-medium"
          style={{ color: 'var(--tg-hint)' }}
        >
          {label}
        </span>
      </div>
      <div
        className="text-2xl font-bold tabular-nums"
        style={{ color: accentColor || 'var(--tg-text)' }}
      >
        {value}
      </div>
    </div>
  );
}

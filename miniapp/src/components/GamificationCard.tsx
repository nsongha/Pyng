/* ============================================
   GamificationCard — Điểm, streak, rank
   ============================================ */

import type { GamificationStats } from '../types';
import { getStreakMilestone } from '../types';

interface GamificationCardProps {
  stats: GamificationStats;
}

export function GamificationCard({ stats }: GamificationCardProps) {
  const milestone = getStreakMilestone(stats.current_streak);

  return (
    <div
      className="rounded-2xl p-5 relative overflow-hidden"
      style={{
        background:
          'linear-gradient(135deg, var(--color-brand) 0%, var(--color-brand-dark) 100%)',
      }}
    >
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-32 h-32 opacity-10">
        <svg viewBox="0 0 100 100" fill="white">
          <circle cx="80" cy="20" r="40" />
          <circle cx="60" cy="50" r="25" />
        </svg>
      </div>

      <h3 className="text-sm font-semibold text-white/70 mb-3 uppercase tracking-wide">
        🏆 Gamification
      </h3>

      <div className="flex justify-between items-end relative z-10">
        {/* Points */}
        <div>
          <div className="text-xs text-white/60 mb-0.5">Điểm</div>
          <div className="text-3xl font-bold text-white tabular-nums">
            {stats.total_points.toLocaleString()}
          </div>
        </div>

        {/* Streak */}
        <div className="text-center">
          <div className="text-xs text-white/60 mb-0.5">Streak</div>
          <div className="text-2xl font-bold text-white tabular-nums">
            {milestone?.icon || '🔥'} {stats.current_streak}
          </div>
          {milestone && (
            <div className="text-[10px] text-white/50 mt-0.5">
              {milestone.label}
            </div>
          )}
        </div>

        {/* Rank */}
        <div className="text-right">
          <div className="text-xs text-white/60 mb-0.5">Rank</div>
          <div className="text-2xl font-bold text-white tabular-nums">
            #{stats.rank}
          </div>
        </div>
      </div>

      {/* Sub-stats */}
      <div className="flex gap-4 mt-4 pt-3 border-t border-white/15">
        <div className="text-xs text-white/60">
          ✅ Đúng giờ:{' '}
          <span className="text-white font-medium">{stats.ontime_count}</span>
        </div>
        <div className="text-xs text-white/60">
          🐦 Sớm:{' '}
          <span className="text-white font-medium">{stats.early_count}</span>
        </div>
        <div className="text-xs text-white/60">
          🏅 Dài nhất:{' '}
          <span className="text-white font-medium">
            {stats.longest_streak} ngày
          </span>
        </div>
      </div>
    </div>
  );
}

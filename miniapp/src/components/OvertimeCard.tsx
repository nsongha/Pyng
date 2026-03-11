/* ============================================
   OvertimeCard — Tổng hợp OT tháng + sparkline
   ============================================ */

import {
  AreaChart,
  Area,
  ResponsiveContainer,
} from 'recharts';
import type { OvertimeResponse } from '../types';

interface OvertimeCardProps {
  data: OvertimeResponse;
}

/** Format phút → giờ:phút */
function formatOTDuration(totalMinutes: number): string {
  const hours = Math.floor(totalMinutes / 60);
  const mins = totalMinutes % 60;
  if (hours === 0) return `${mins} phút`;
  if (mins === 0) return `${hours} giờ`;
  return `${hours}h${mins.toString().padStart(2, '0')}`;
}

export function OvertimeCard({ data }: OvertimeCardProps) {
  // Chỉ render khi có OT data
  if (data.total_minutes === 0) return null;

  // Sparkline data — cắt tối đa 14 session gần nhất
  const sparklineData = data.sessions
    .slice(-14)
    .map((s) => ({ date: s.date, value: s.minutes }));

  return (
    <div
      className="rounded-2xl p-4"
      style={{
        backgroundColor: 'var(--tg-section-bg)',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      <h3
        className="text-xs font-semibold uppercase tracking-wide mb-3"
        style={{ color: 'var(--tg-section-header)' }}
      >
        ⏰ Overtime tháng này
      </h3>

      <div className="flex items-center gap-4">
        {/* Stats */}
        <div className="flex-1">
          <div
            className="text-2xl font-bold"
            style={{ color: 'var(--color-warning)' }}
          >
            {formatOTDuration(data.total_minutes)}
          </div>
          <div
            className="text-xs mt-1"
            style={{ color: 'var(--tg-hint)' }}
          >
            {data.total_days} lần tăng ca
          </div>
        </div>

        {/* Sparkline */}
        {sparklineData.length > 1 && (
          <div style={{ width: 100, height: 40 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sparklineData}>
                <defs>
                  <linearGradient id="otGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-warning)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--color-warning)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="var(--color-warning)"
                  strokeWidth={2}
                  fill="url(#otGradient)"
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Sessions list (last 3) */}
      {data.sessions.length > 0 && (
        <div className="mt-3 pt-3 space-y-1.5" style={{ borderTop: '1px solid var(--tg-secondary-bg)' }}>
          {data.sessions.slice(-3).reverse().map((session) => (
            <div key={session.date} className="flex items-center justify-between">
              <span className="text-xs" style={{ color: 'var(--tg-hint)' }}>
                {new Date(session.date).toLocaleDateString('vi-VN', {
                  weekday: 'short',
                  day: 'numeric',
                  month: 'numeric',
                })}
              </span>
              <span
                className="text-xs font-medium"
                style={{ color: 'var(--color-warning)' }}
              >
                +{formatOTDuration(session.minutes)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

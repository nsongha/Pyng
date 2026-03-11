/* ============================================
   AttendanceDonut — Donut chart phân bổ ngày
   Present / WFH / Leave / Absent
   ============================================ */

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import type { ChartSummary } from '../../types';

interface AttendanceDonutProps {
  summary: ChartSummary;
  totalDaysInMonth: number;
  wfhDays?: number;
  leaveDays?: number;
}

interface DonutEntry {
  name: string;
  value: number;
  color: string;
  emoji: string;
}

export function AttendanceDonut({
  summary,
  totalDaysInMonth,
  wfhDays = 0,
  leaveDays = 0,
}: AttendanceDonutProps) {
  // Tính phân bổ (business days rough estimate: 22 ngày/tháng)
  const businessDays = Math.min(totalDaysInMonth, 22);
  const presentDays = Math.max(0, summary.total_days - wfhDays);
  const absentDays = Math.max(0, businessDays - summary.total_days - leaveDays);

  const data: DonutEntry[] = [
    { name: 'Có mặt', value: presentDays, color: 'var(--color-ontime)', emoji: '✅' },
    { name: 'WFH', value: wfhDays, color: 'var(--color-wfh)', emoji: '🏠' },
    { name: 'Nghỉ phép', value: leaveDays, color: 'var(--color-leave)', emoji: '🌴' },
    { name: 'Vắng', value: absentDays, color: 'var(--color-absent)', emoji: '❌' },
  ].filter(d => d.value > 0);

  // Edge case: không có data, show placeholder
  if (data.length === 0) {
    data.push({ name: 'Chưa có dữ liệu', value: 1, color: 'var(--tg-secondary-bg)', emoji: '—' });
  }

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
        Phân bổ ngày làm
      </h3>

      <div className="flex items-center gap-4">
        {/* Donut chart */}
        <div className="relative" style={{ width: 120, height: 120 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={35}
                outerRadius={55}
                paddingAngle={2}
                dataKey="value"
                stroke="none"
              >
                {data.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          {/* Center label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className="text-xl font-bold leading-none"
              style={{ color: 'var(--tg-text)' }}
            >
              {summary.total_days}
            </span>
            <span
              className="text-[10px] leading-none mt-0.5"
              style={{ color: 'var(--tg-hint)' }}
            >
              ngày
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex-1 space-y-2">
          {data.map((entry) => (
            <div key={entry.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm">{entry.emoji}</span>
                <span
                  className="text-xs"
                  style={{ color: 'var(--tg-text)' }}
                >
                  {entry.name}
                </span>
              </div>
              <span
                className="text-xs font-semibold"
                style={{ color: 'var(--tg-text)' }}
              >
                {entry.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

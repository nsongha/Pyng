/* ============================================
   WorkingHoursChart — Bar chart giờ làm 30 ngày
   Recharts BarChart + touch-friendly tooltips
   ============================================ */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  Cell,
} from 'recharts';
import type { DailyHour } from '../../types';
import { METHOD_LABELS, MOOD_LABELS } from '../../types';

interface WorkingHoursChartProps {
  data: DailyHour[];
}

/** Custom tooltip — touch-friendly (min 44px height) */
function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: DailyHour }>;
}) {
  if (!active || !payload?.length) return null;

  const item = payload[0].payload;
  if (item.hours === 0 && !item.method) return null;

  const day = new Date(item.date).toLocaleDateString('vi-VN', {
    weekday: 'short',
    day: 'numeric',
    month: 'numeric',
  });

  const methodInfo = item.method ? METHOD_LABELS[item.method] : null;
  const moodInfo = item.mood ? MOOD_LABELS[item.mood] : null;

  return (
    <div
      className="chart-tooltip"
      style={{
        backgroundColor: 'var(--tg-section-bg)',
        color: 'var(--tg-text)',
        border: '1px solid var(--tg-secondary-bg)',
      }}
    >
      <div className="font-semibold mb-1">{day}</div>
      <div className="flex items-center gap-1">
        <span style={{ color: item.is_late ? 'var(--color-late)' : 'var(--color-ontime)' }}>
          {item.hours > 0 ? `${item.hours}h` : 'Không có dữ liệu'}
        </span>
        {item.is_late && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-full"
            style={{ backgroundColor: 'rgba(255, 159, 10, 0.15)', color: 'var(--color-late)' }}>
            Muộn
          </span>
        )}
      </div>
      {methodInfo && (
        <div className="text-xs mt-0.5" style={{ color: 'var(--tg-hint)' }}>
          {methodInfo.emoji} {methodInfo.label}
        </div>
      )}
      {moodInfo && (
        <div className="text-xs" style={{ color: 'var(--tg-hint)' }}>
          {moodInfo.emoji} {moodInfo.label}
        </div>
      )}
    </div>
  );
}

export function WorkingHoursChart({ data }: WorkingHoursChartProps) {
  // Chỉ hiển thị ngày có số > 0 hoặc tất cả nếu muốn xem pattern
  const chartData = data.map((d) => ({
    ...d,
    // Hiển thị ngày (chỉ số ngày)
    label: new Date(d.date).getDate().toString(),
  }));

  return (
    <div className="w-full" style={{ height: 200 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 8, right: 4, bottom: 0, left: -20 }}
          barCategoryGap="15%"
        >
          <XAxis
            dataKey="label"
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10, fill: 'var(--tg-hint)' }}
            interval="preserveStartEnd"
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10, fill: 'var(--tg-hint)' }}
            domain={[0, 12]}
            ticks={[0, 4, 8, 12]}
            tickFormatter={(v: number) => `${v}h`}
          />
          <ReferenceLine
            y={8}
            stroke="var(--tg-hint)"
            strokeDasharray="3 3"
            strokeOpacity={0.4}
          />
          <Tooltip
            content={<ChartTooltip />}
            cursor={{ fill: 'var(--tg-secondary-bg)', opacity: 0.5 }}
          />
          <Bar dataKey="hours" radius={[3, 3, 0, 0]} maxBarSize={12}>
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={
                  entry.hours === 0
                    ? 'var(--tg-secondary-bg)'
                    : entry.is_late
                      ? 'var(--color-late)'
                      : 'var(--color-ontime)'
                }
                fillOpacity={entry.hours === 0 ? 0.3 : 0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ============================================
   Charts Page — Thống kê biểu đồ
   Month selector + WorkingHoursChart +
   Stats summary + AttendanceDonut + OvertimeCard
   ============================================ */

import { useCallback, useEffect, useState } from 'react';
import { useTelegramContext } from '../contexts/TelegramContext';
import { fetchChartData, fetchOvertime } from '../lib/api';
import type { ChartDataResponse, OvertimeResponse } from '../types';
import { ChartSkeleton, StatsSummarySkeleton } from '../components/LoadingSkeleton';
import { WorkingHoursChart } from '../components/charts/WorkingHoursChart';
import { AttendanceDonut } from '../components/charts/AttendanceDonut';
import { OvertimeCard } from '../components/OvertimeCard';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

/** Format YYYY-MM cho API */
function formatMonth(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

/** Hiển thị tháng tiếng Việt */
function displayMonth(date: Date): string {
  return `Tháng ${date.getMonth() + 1}/${date.getFullYear()}`;
}

/** Lấy số ngày trong tháng */
function getDaysInMonth(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
}

export function Charts() {
  const { initData } = useTelegramContext();

  // Month navigation
  const [currentMonth, setCurrentMonth] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });

  // Data states
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [overtimeData, setOvertimeData] = useState<OvertimeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Không cho chọn tháng tương lai
  const isCurrentMonth = (() => {
    const now = new Date();
    return (
      currentMonth.getFullYear() === now.getFullYear() &&
      currentMonth.getMonth() === now.getMonth()
    );
  })();

  // Load data
  const loadData = useCallback(async () => {
    if (!initData) return;

    setIsLoading(true);
    setError(null);

    const monthStr = formatMonth(currentMonth);

    try {
      const [chart, overtime] = await Promise.all([
        fetchChartData(initData, monthStr),
        fetchOvertime(initData, monthStr).catch(() => null), // OT có thể không có
      ]);

      setChartData(chart);
      setOvertimeData(overtime);
    } catch (err) {
      console.error('[Charts] Failed to load data:', err);
      setError(err instanceof Error ? err.message : 'Không thể tải dữ liệu');
    } finally {
      setIsLoading(false);
    }
  }, [initData, currentMonth]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Navigation
  const goToPrevMonth = () => {
    setCurrentMonth(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  };

  const goToNextMonth = () => {
    if (!isCurrentMonth) {
      setCurrentMonth(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
    }
  };

  // Trend arrow
  const getTrendIndicator = (changePercent: number) => {
    if (changePercent > 0) return { icon: '↑', color: 'var(--color-success)' };
    if (changePercent < 0) return { icon: '↓', color: 'var(--color-danger)' };
    return { icon: '→', color: 'var(--tg-hint)' };
  };

  return (
    <div
      className="min-h-screen pb-20"
      style={{ backgroundColor: 'var(--tg-bg)' }}
    >
      {/* Header + Month Selector */}
      <header className="px-4 pt-4 pb-2">
        <h1
          className="text-lg font-bold mb-3"
          style={{ color: 'var(--tg-text)' }}
        >
          📈 Thống kê
        </h1>

        {/* Month selector */}
        <div className="flex items-center justify-between">
          <button
            onClick={goToPrevMonth}
            className="w-10 h-10 flex items-center justify-center rounded-full active:scale-95 transition-transform"
            style={{ backgroundColor: 'var(--tg-secondary-bg)' }}
          >
            <span style={{ color: 'var(--tg-text)' }}>←</span>
          </button>

          <span
            className="text-sm font-semibold"
            style={{ color: 'var(--tg-text)' }}
          >
            {displayMonth(currentMonth)}
          </span>

          <button
            onClick={goToNextMonth}
            disabled={isCurrentMonth}
            className="w-10 h-10 flex items-center justify-center rounded-full active:scale-95 transition-transform"
            style={{
              backgroundColor: 'var(--tg-secondary-bg)',
              opacity: isCurrentMonth ? 0.3 : 1,
            }}
          >
            <span style={{ color: 'var(--tg-text)' }}>→</span>
          </button>
        </div>
      </header>

      <main className="px-4 space-y-4 mt-2">
        {/* Loading state */}
        {isLoading && (
          <div className="space-y-4">
            <ChartSkeleton />
            <StatsSummarySkeleton />
            <ChartSkeleton />
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <ErrorState error={error} onRetry={loadData} />
        )}

        {/* Data loaded */}
        {!isLoading && !error && chartData && (
          <>
            {/* Empty state */}
            {chartData.summary.total_days === 0 ? (
              <EmptyState
                icon="📊"
                title={`Chưa có dữ liệu ${displayMonth(currentMonth)}`}
                description="Hãy check-in đều đặn để xem biểu đồ giờ làm việc và thống kê chi tiết tại đây."
              />
            ) : (
              <>
                {/* Working Hours Chart */}
                <section
                  className="rounded-2xl p-4"
                  style={{
                    backgroundColor: 'var(--tg-section-bg)',
                    boxShadow: 'var(--shadow-card)',
                  }}
                >
                  <h2
                    className="text-xs font-semibold uppercase tracking-wide mb-2"
                    style={{ color: 'var(--tg-section-header)' }}
                  >
                    Giờ làm hàng ngày
                  </h2>
                  <WorkingHoursChart data={chartData.daily_hours} />
                </section>

                {/* Stats Summary Row */}
                <section className="grid grid-cols-3 gap-3">
                  {/* Avg hours */}
                  <div
                    className="rounded-xl p-3 text-center"
                    style={{
                      backgroundColor: 'var(--tg-section-bg)',
                      boxShadow: 'var(--shadow-card)',
                    }}
                  >
                    <div
                      className="text-lg font-bold"
                      style={{ color: 'var(--tg-text)' }}
                    >
                      {chartData.summary.avg_hours}h
                    </div>
                    <div
                      className="text-[10px]"
                      style={{ color: 'var(--tg-hint)' }}
                    >
                      TB/ngày
                    </div>
                  </div>

                  {/* Ontime rate */}
                  <div
                    className="rounded-xl p-3 text-center"
                    style={{
                      backgroundColor: 'var(--tg-section-bg)',
                      boxShadow: 'var(--shadow-card)',
                    }}
                  >
                    <div
                      className="text-lg font-bold"
                      style={{ color: 'var(--color-ontime)' }}
                    >
                      {chartData.summary.ontime_rate}%
                    </div>
                    <div
                      className="text-[10px]"
                      style={{ color: 'var(--tg-hint)' }}
                    >
                      Đúng giờ
                    </div>
                  </div>

                  {/* Trend */}
                  <div
                    className="rounded-xl p-3 text-center"
                    style={{
                      backgroundColor: 'var(--tg-section-bg)',
                      boxShadow: 'var(--shadow-card)',
                    }}
                  >
                    {(() => {
                      const trend = getTrendIndicator(chartData.trend.change_percent);
                      return (
                        <>
                          <div
                            className="text-lg font-bold"
                            style={{ color: trend.color }}
                          >
                            {trend.icon}{' '}
                            {Math.abs(chartData.trend.change_percent)}%
                          </div>
                          <div
                            className="text-[10px]"
                            style={{ color: 'var(--tg-hint)' }}
                          >
                            vs tháng trước
                          </div>
                        </>
                      );
                    })()}
                  </div>
                </section>

                {/* Attendance Donut */}
                <section>
                  <AttendanceDonut
                    summary={chartData.summary}
                    totalDaysInMonth={getDaysInMonth(currentMonth)}
                  />
                </section>

                {/* Overtime Card */}
                {overtimeData && (
                  <section>
                    <OvertimeCard data={overtimeData} />
                  </section>
                )}
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}

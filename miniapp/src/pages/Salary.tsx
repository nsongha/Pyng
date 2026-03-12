/* ============================================
   Salary Page — Bảng lương tháng
   Month selector + breakdown + net salary
   Pattern: giống Charts.tsx
   ============================================ */

import { useCallback, useEffect, useState } from 'react';
import { useTelegramContext } from '../contexts/TelegramContext';
import { fetchSalary } from '../lib/api';
import type { SalaryResponse } from '../types';
import { StatsSummarySkeleton } from '../components/LoadingSkeleton';
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

/** Format VND currency */
function formatVND(amount: number): string {
  return new Intl.NumberFormat('vi-VN').format(amount);
}

/** Format OT minutes → hours string */
function formatOTHours(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins} phút`;
  if (mins === 0) return `${hours} giờ`;
  return `${hours}g ${mins}p`;
}

export function Salary() {
  const { initData } = useTelegramContext();

  // Month navigation
  const [currentMonth, setCurrentMonth] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });

  // Data states
  const [salaryData, setSalaryData] = useState<SalaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | string | null>(null);

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
      const data = await fetchSalary(initData, monthStr);
      setSalaryData(data);
    } catch (err) {
      console.error('[Salary] Failed to load data:', err);
      if (err instanceof Error) {
        setError(err);
      } else {
        setError('Không thể tải dữ liệu lương');
      }
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

  const salary = salaryData?.salary;

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
          💰 Bảng lương
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
            {/* Net salary skeleton */}
            <div
              className="rounded-2xl p-4"
              style={{
                background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
              }}
            >
              <div className="skeleton h-3 w-20 mb-2" style={{ opacity: 0.3 }} />
              <div className="skeleton h-10 w-40 mb-3" style={{ opacity: 0.3 }} />
              <div className="skeleton h-5 w-24 rounded-full" style={{ opacity: 0.3 }} />
            </div>
            <StatsSummarySkeleton />
            <StatsSummarySkeleton />
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <ErrorState error={error} onRetry={loadData} />
        )}

        {/* Data loaded */}
        {!isLoading && !error && salary && (
          <>
            {/* Net Salary — Hero card */}
            <section
              className="rounded-2xl p-5 relative overflow-hidden"
              style={{
                background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
              }}
            >
              {/* Decorative circles */}
              <div
                className="absolute -top-6 -right-6 w-24 h-24 rounded-full"
                style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}
              />
              <div
                className="absolute -bottom-4 -left-4 w-16 h-16 rounded-full"
                style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}
              />

              <div className="relative z-10">
                <div className="text-xs font-medium text-white/70 mb-1">
                  Lương ròng
                </div>
                <div className="text-3xl font-bold text-white mb-2">
                  {formatVND(salary.net_salary)}
                  <span className="text-sm font-normal text-white/60 ml-1">₫</span>
                </div>
                <div
                  className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full"
                  style={{
                    backgroundColor: salary.status === 'confirmed'
                      ? 'rgba(255,255,255,0.25)'
                      : 'rgba(255,255,255,0.15)',
                  }}
                >
                  <span>{salary.status === 'confirmed' ? '✅' : '📊'}</span>
                  <span className="text-white/90">
                    {salary.status === 'confirmed' ? 'Đã xác nhận' : 'Ước tính'}
                  </span>
                </div>
              </div>
            </section>

            {/* Income Section */}
            <section
              className="rounded-2xl p-4"
              style={{
                backgroundColor: 'var(--tg-section-bg)',
                boxShadow: 'var(--shadow-card)',
              }}
            >
              <h2
                className="text-xs font-semibold uppercase tracking-wide mb-3"
                style={{ color: 'var(--tg-section-header)' }}
              >
                Thu nhập
              </h2>

              {/* Basic salary */}
              <div className="flex justify-between items-center py-2.5">
                <div className="flex items-center gap-2.5">
                  <span className="text-lg">💼</span>
                  <div>
                    <div
                      className="text-sm font-medium"
                      style={{ color: 'var(--tg-text)' }}
                    >
                      Lương cơ bản
                    </div>
                    <div
                      className="text-xs"
                      style={{ color: 'var(--tg-hint)' }}
                    >
                      {salary.working_days} ngày làm việc
                    </div>
                  </div>
                </div>
                <span
                  className="text-sm font-semibold"
                  style={{ color: 'var(--tg-text)' }}
                >
                  +{formatVND(salary.basic_salary)}
                </span>
              </div>

              {/* Divider */}
              <div
                className="h-px my-0.5"
                style={{ backgroundColor: 'var(--tg-secondary-bg)' }}
              />

              {/* OT allowance */}
              <div className="flex justify-between items-center py-2.5">
                <div className="flex items-center gap-2.5">
                  <span className="text-lg">⏰</span>
                  <div>
                    <div
                      className="text-sm font-medium"
                      style={{ color: 'var(--tg-text)' }}
                    >
                      Phụ cấp OT
                    </div>
                    <div
                      className="text-xs"
                      style={{ color: 'var(--tg-hint)' }}
                    >
                      {salary.ot_minutes > 0
                        ? formatOTHours(salary.ot_minutes)
                        : 'Không có OT'}
                    </div>
                  </div>
                </div>
                <span
                  className="text-sm font-semibold"
                  style={{ color: salary.ot_allowance > 0 ? 'var(--color-success)' : 'var(--tg-hint)' }}
                >
                  +{formatVND(salary.ot_allowance)}
                </span>
              </div>
            </section>

            {/* Deductions Section */}
            <section
              className="rounded-2xl p-4"
              style={{
                backgroundColor: 'var(--tg-section-bg)',
                boxShadow: 'var(--shadow-card)',
              }}
            >
              <h2
                className="text-xs font-semibold uppercase tracking-wide mb-3"
                style={{ color: 'var(--tg-section-header)' }}
              >
                Khấu trừ
              </h2>

              {/* Late deductions */}
              <div className="flex justify-between items-center py-2.5">
                <div className="flex items-center gap-2.5">
                  <span className="text-lg">⏳</span>
                  <div>
                    <div
                      className="text-sm font-medium"
                      style={{ color: 'var(--tg-text)' }}
                    >
                      Đi muộn
                    </div>
                    <div
                      className="text-xs"
                      style={{ color: 'var(--tg-hint)' }}
                    >
                      {salary.late_count > 0
                        ? `${salary.late_count} lần · ${salary.late_total_minutes} phút`
                        : 'Không đi muộn 🎉'}
                    </div>
                  </div>
                </div>
                <span
                  className="text-sm font-semibold"
                  style={{ color: salary.late_deductions > 0 ? 'var(--color-danger)' : 'var(--tg-hint)' }}
                >
                  {salary.late_deductions > 0 ? '-' : ''}{formatVND(salary.late_deductions)}
                </span>
              </div>

              {/* Divider */}
              <div
                className="h-px my-0.5"
                style={{ backgroundColor: 'var(--tg-secondary-bg)' }}
              />

              {/* Unpaid leave */}
              <div className="flex justify-between items-center py-2.5">
                <div className="flex items-center gap-2.5">
                  <span className="text-lg">📋</span>
                  <div>
                    <div
                      className="text-sm font-medium"
                      style={{ color: 'var(--tg-text)' }}
                    >
                      Nghỉ không lương
                    </div>
                    <div
                      className="text-xs"
                      style={{ color: 'var(--tg-hint)' }}
                    >
                      {salary.unpaid_leave_days > 0
                        ? `${salary.unpaid_leave_days} ngày`
                        : 'Không có'}
                    </div>
                  </div>
                </div>
                <span
                  className="text-sm font-semibold"
                  style={{ color: salary.unpaid_leave_deduction > 0 ? 'var(--color-danger)' : 'var(--tg-hint)' }}
                >
                  {salary.unpaid_leave_deduction > 0 ? '-' : ''}{formatVND(salary.unpaid_leave_deduction)}
                </span>
              </div>
            </section>

            {/* Summary Stats Row */}
            <section className="grid grid-cols-3 gap-3">
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
                  {salary.working_days}
                </div>
                <div
                  className="text-[10px]"
                  style={{ color: 'var(--tg-hint)' }}
                >
                  Ngày làm
                </div>
              </div>

              <div
                className="rounded-xl p-3 text-center"
                style={{
                  backgroundColor: 'var(--tg-section-bg)',
                  boxShadow: 'var(--shadow-card)',
                }}
              >
                <div
                  className="text-lg font-bold"
                  style={{ color: salary.ot_minutes > 0 ? 'var(--color-success)' : 'var(--tg-text)' }}
                >
                  {formatOTHours(salary.ot_minutes)}
                </div>
                <div
                  className="text-[10px]"
                  style={{ color: 'var(--tg-hint)' }}
                >
                  Tổng OT
                </div>
              </div>

              <div
                className="rounded-xl p-3 text-center"
                style={{
                  backgroundColor: 'var(--tg-section-bg)',
                  boxShadow: 'var(--shadow-card)',
                }}
              >
                <div
                  className="text-lg font-bold"
                  style={{ color: salary.late_count > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}
                >
                  {salary.late_count}
                </div>
                <div
                  className="text-[10px]"
                  style={{ color: 'var(--tg-hint)' }}
                >
                  Lần muộn
                </div>
              </div>
            </section>
          </>
        )}

        {/* Empty state — khi salary trả null/undefined */}
        {!isLoading && !error && !salary && (
          <EmptyState
            icon="💰"
            title={`Chưa có dữ liệu lương ${displayMonth(currentMonth)}`}
            description="Lương sẽ được tính tự động dựa trên dữ liệu check-in, OT và nghỉ phép."
          />
        )}
      </main>
    </div>
  );
}

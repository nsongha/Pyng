/* ============================================
   Pyng Mini App — Leave List Component (Stream C)
   Danh sách đơn nghỉ + status badges + pull-to-refresh
   ============================================ */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { LeaveRequest } from '../types';
import { LEAVE_TYPE_LABELS, LEAVE_STATUS_LABELS } from '../types';

interface LeaveListProps {
  /** Leave requests data */
  leaves: LeaveRequest[];
  /** Loading state */
  isLoading: boolean;
  /** Callback to refresh data */
  onRefresh: () => Promise<void>;
}

/**
 * Format date string to Vietnamese display.
 * "2026-03-20" → "20/03"
 */
function formatDate(dateStr: string): string {
  const [, month, day] = dateStr.split('-');
  return `${day}/${month}`;
}

/**
 * Format date range display.
 */
function formatDateRange(start: string, end: string): string {
  if (start === end) return formatDate(start);
  return `${formatDate(start)} → ${formatDate(end)}`;
}

export function LeaveList({ leaves, isLoading, onRefresh }: LeaveListProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);
  const touchStartY = useRef(0);
  const isPulling = useRef(false);

  const PULL_THRESHOLD = 60;

  // Pull-to-refresh handlers
  const handleTouchStart = useCallback((e: TouchEvent) => {
    if (listRef.current && listRef.current.scrollTop <= 0) {
      touchStartY.current = e.touches[0].clientY;
      isPulling.current = true;
    }
  }, []);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!isPulling.current) return;
    const diff = e.touches[0].clientY - touchStartY.current;
    if (diff > 0) {
      setPullDistance(Math.min(diff * 0.5, 100));
    }
  }, []);

  const handleTouchEnd = useCallback(async () => {
    if (!isPulling.current) return;
    isPulling.current = false;

    if (pullDistance >= PULL_THRESHOLD) {
      setIsRefreshing(true);
      await onRefresh();
      setIsRefreshing(false);
    }
    setPullDistance(0);
  }, [pullDistance, onRefresh]);

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    el.addEventListener('touchstart', handleTouchStart, { passive: true });
    el.addEventListener('touchmove', handleTouchMove, { passive: true });
    el.addEventListener('touchend', handleTouchEnd);
    return () => {
      el.removeEventListener('touchstart', handleTouchStart);
      el.removeEventListener('touchmove', handleTouchMove);
      el.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton h-20 rounded-xl" />
        ))}
      </div>
    );
  }

  // Empty state
  if (leaves.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-3">
        <div className="text-5xl">📭</div>
        <p
          className="text-base font-medium"
          style={{ color: 'var(--tg-text)' }}
        >
          Chưa có đơn nghỉ nào
        </p>
        <p className="text-sm" style={{ color: 'var(--tg-hint)' }}>
          Nhấn tab "Xin nghỉ" để tạo đơn mới
        </p>
      </div>
    );
  }

  return (
    <div ref={listRef} className="flex flex-col gap-3 overflow-y-auto relative">
      {/* Pull-to-refresh indicator */}
      {pullDistance > 0 && (
        <div
          className="flex justify-center transition-all duration-150"
          style={{ height: pullDistance }}
        >
          <div
            className="flex items-center gap-2 text-sm"
            style={{ color: 'var(--tg-hint)' }}
          >
            {isRefreshing ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
                Đang tải...
              </>
            ) : pullDistance >= PULL_THRESHOLD ? (
              '↑ Thả để làm mới'
            ) : (
              '↓ Kéo để làm mới'
            )}
          </div>
        </div>
      )}

      {/* Leave cards */}
      {leaves.map((leave) => {
        const typeConfig = LEAVE_TYPE_LABELS[leave.leave_type];
        const statusConfig = LEAVE_STATUS_LABELS[leave.status];

        return (
          <div
            key={leave.id}
            className="rounded-xl p-3.5 transition-all duration-200"
            style={{
              backgroundColor: 'var(--tg-section-bg)',
              boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            }}
          >
            {/* Header: type + status */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{typeConfig.emoji}</span>
                <span
                  className="text-sm font-medium"
                  style={{ color: 'var(--tg-text)' }}
                >
                  {typeConfig.label}
                </span>
              </div>
              <span
                className="text-xs font-medium px-2 py-0.5 rounded-full"
                style={{
                  backgroundColor: statusConfig.bgColor,
                  color: statusConfig.color.replace('text-', ''),
                }}
              >
                {statusConfig.emoji} {statusConfig.label}
              </span>
            </div>

            {/* Date range + days */}
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm" style={{ color: 'var(--tg-text)' }}>
                📅 {formatDateRange(leave.start_date, leave.end_date)}
              </span>
              <span
                className="text-sm font-semibold"
                style={{ color: 'var(--tg-text)' }}
              >
                {leave.days_count} ngày
              </span>
            </div>

            {/* Reason (if any) */}
            {leave.reason && (
              <p
                className="text-xs mt-1 line-clamp-2"
                style={{ color: 'var(--tg-hint)' }}
              >
                📝 {leave.reason}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

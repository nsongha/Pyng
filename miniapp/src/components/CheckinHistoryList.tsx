/* ============================================
   CheckinHistoryList — Lịch sử check-in 30 ngày
   ============================================ */

import type { CheckinRecord } from '../types';
import { METHOD_LABELS, MOOD_LABELS } from '../types';

interface CheckinHistoryListProps {
  records: CheckinRecord[];
}

/** Format date string → "T2, 11/03" */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const days = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
  const day = days[date.getDay()];
  const dd = date.getDate().toString().padStart(2, '0');
  const mm = (date.getMonth() + 1).toString().padStart(2, '0');
  return `${day}, ${dd}/${mm}`;
}

/** Format time "HH:MM:SS" or "HH:MM" → "08:45" */
function formatTime(time: string | null): string {
  if (!time) return '--:--';
  return time.substring(0, 5);
}

/** Format working hours → "8h 30m" */
function formatWorkingHours(hours: number | null): string {
  if (hours === null || hours === undefined) return '';
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

export function CheckinHistoryList({ records }: CheckinHistoryListProps) {
  if (records.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-3">📋</div>
        <div className="text-sm" style={{ color: 'var(--tg-hint)' }}>
          Chưa có dữ liệu check-in
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {records.map((record) => {
        const method = METHOD_LABELS[record.method];
        const mood = record.mood ? MOOD_LABELS[record.mood] : null;

        return (
          <div
            key={record.id}
            className="flex items-center gap-3 rounded-xl p-3 transition-colors active:opacity-80"
            style={{ backgroundColor: 'var(--tg-section-bg)' }}
          >
            {/* Status indicator */}
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center text-lg shrink-0"
              style={{
                backgroundColor: record.is_ontime
                  ? 'var(--color-ontime)'
                  : record.method === 'wfh'
                    ? 'var(--color-wfh)'
                    : 'var(--color-late)',
                opacity: 0.15,
              }}
            >
              <span
                style={{
                  color: record.is_ontime
                    ? 'var(--color-ontime)'
                    : record.method === 'wfh'
                      ? 'var(--color-wfh)'
                      : 'var(--color-late)',
                }}
              >
                {record.is_ontime ? '✓' : record.method === 'wfh' ? '🏠' : '⏰'}
              </span>
            </div>

            {/* Main info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className="text-sm font-medium"
                  style={{ color: 'var(--tg-text)' }}
                >
                  {formatDate(record.date)}
                </span>
                {mood && (
                  <span className="text-xs" title={mood.label}>
                    {mood.emoji}
                  </span>
                )}
              </div>
              <div
                className="text-xs mt-0.5 flex items-center gap-2"
                style={{ color: 'var(--tg-hint)' }}
              >
                <span>
                  {formatTime(record.time_in)} → {formatTime(record.time_out)}
                </span>
                {record.working_hours && (
                  <span className="opacity-60">
                    ({formatWorkingHours(record.working_hours)})
                  </span>
                )}
              </div>
            </div>

            {/* Method badge */}
            <div
              className="shrink-0 px-2.5 py-1 rounded-full text-[11px] font-medium"
              style={{
                backgroundColor: 'var(--tg-secondary-bg)',
                color: 'var(--tg-hint)',
              }}
            >
              {method.emoji} {method.label}
            </div>
          </div>
        );
      })}
    </div>
  );
}

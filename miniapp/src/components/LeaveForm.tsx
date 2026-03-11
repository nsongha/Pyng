/* ============================================
   Pyng Mini App — Leave Request Form (Stream C)
   Telegram-native UX: haptic feedback, styled inputs
   ============================================ */

import { useState, useMemo, useCallback } from 'react';
import { useTelegram } from '../hooks/useTelegram';
import { useTelegramContext } from '../contexts/TelegramContext';
import { submitLeaveRequest, PyngApiError } from '../lib/api';
import type { LeaveType, LeaveBalance, LeaveFormData } from '../types';
import { LEAVE_TYPE_LABELS } from '../types';

interface LeaveFormProps {
  /** Leave balance (for annual leave display) */
  balance: LeaveBalance | null;
  /** Callback when leave request submitted successfully */
  onSuccess: () => void;
}

/**
 * Calculate business days between two dates (excluding Sat/Sun).
 * Mirrors _count_business_days() in leave_service.py.
 */
function calculateBusinessDays(startStr: string, endStr: string): number {
  if (!startStr || !endStr) return 0;

  const start = new Date(startStr);
  const end = new Date(endStr);
  if (end < start) return 0;

  let count = 0;
  const current = new Date(start);
  while (current <= end) {
    const day = current.getDay();
    // 0 = Sunday, 6 = Saturday
    if (day !== 0 && day !== 6) {
      count++;
    }
    current.setDate(current.getDate() + 1);
  }
  return count;
}

/**
 * Get today's date as YYYY-MM-DD string.
 */
function getTodayString(): string {
  const now = new Date();
  return now.toISOString().split('T')[0];
}

export function LeaveForm({ balance, onSuccess }: LeaveFormProps) {
  const { initData } = useTelegramContext();
  const { haptic } = useTelegram();

  // Form state
  const [leaveType, setLeaveType] = useState<LeaveType>('annual');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Calculated business days
  const businessDays = useMemo(
    () => calculateBusinessDays(startDate, endDate),
    [startDate, endDate],
  );

  // Whether reason is required (unpaid/compensatory)
  const isReasonRequired = leaveType === 'unpaid' || leaveType === 'compensatory';

  // Validation
  const isValid = useMemo(() => {
    if (!startDate || !endDate) return false;
    if (new Date(endDate) < new Date(startDate)) return false;
    if (isReasonRequired && !reason.trim()) return false;
    if (businessDays === 0) return false;
    return true;
  }, [startDate, endDate, reason, isReasonRequired, businessDays]);

  // Warning: not enough annual leave
  const showBalanceWarning = useMemo(() => {
    if (leaveType !== 'annual' || !balance) return false;
    return businessDays > balance.remaining;
  }, [leaveType, balance, businessDays]);

  const handleSubmit = useCallback(async () => {
    if (!isValid || isSubmitting) return;

    haptic.impact('medium');
    setIsSubmitting(true);
    setError(null);

    const data: LeaveFormData = {
      leave_type: leaveType,
      start_date: startDate,
      end_date: endDate,
      ...(reason.trim() ? { reason: reason.trim() } : {}),
    };

    try {
      await submitLeaveRequest(initData, data);
      haptic.notification('success');
      setSuccess(true);

      // Reset form after short delay
      setTimeout(() => {
        setLeaveType('annual');
        setStartDate('');
        setEndDate('');
        setReason('');
        setSuccess(false);
        onSuccess();
      }, 1500);
    } catch (err) {
      haptic.notification('error');
      if (err instanceof PyngApiError) {
        setError(err.message);
      } else {
        setError('Đã xảy ra lỗi. Vui lòng thử lại.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [isValid, isSubmitting, haptic, leaveType, startDate, endDate, reason, initData, onSuccess]);

  const today = getTodayString();

  // Success toast
  if (success) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4 animate-fade-in">
        <div className="text-5xl animate-bounce-in">✅</div>
        <p className="text-lg font-semibold" style={{ color: 'var(--tg-text)' }}>
          Đã gửi đơn nghỉ thành công!
        </p>
        <p className="text-sm" style={{ color: 'var(--tg-hint)' }}>
          Admin sẽ duyệt sớm nhất có thể
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Leave Type Selector */}
      <div className="flex flex-col gap-1.5">
        <label
          className="text-xs font-medium uppercase tracking-wider"
          style={{ color: 'var(--tg-section-header)' }}
        >
          Loại nghỉ phép
        </label>
        <div className="grid grid-cols-2 gap-2">
          {(Object.keys(LEAVE_TYPE_LABELS) as LeaveType[]).map((type) => {
            const config = LEAVE_TYPE_LABELS[type];
            const isActive = leaveType === type;
            return (
              <button
                key={type}
                type="button"
                onClick={() => {
                  haptic.selection();
                  setLeaveType(type);
                }}
                className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
                style={{
                  backgroundColor: isActive
                    ? 'var(--tg-button)'
                    : 'var(--tg-secondary-bg)',
                  color: isActive
                    ? 'var(--tg-button-text)'
                    : 'var(--tg-text)',
                  transform: isActive ? 'scale(0.98)' : 'scale(1)',
                  boxShadow: isActive
                    ? '0 2px 8px rgba(0,0,0,0.15)'
                    : 'none',
                }}
              >
                <span>{config.emoji}</span>
                <span>{config.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Annual leave balance display */}
      {leaveType === 'annual' && balance && (
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm"
          style={{
            backgroundColor: 'var(--tg-secondary-bg)',
            color: 'var(--tg-hint)',
          }}
        >
          <span>🏖️</span>
          <span>
            Phép còn lại:{' '}
            <strong style={{ color: 'var(--tg-text)' }}>
              {balance.remaining}/{balance.total} ngày
            </strong>
          </span>
        </div>
      )}

      {/* Date Fields */}
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label
            className="text-xs font-medium uppercase tracking-wider"
            style={{ color: 'var(--tg-section-header)' }}
          >
            Từ ngày
          </label>
          <input
            type="date"
            value={startDate}
            min={today}
            onChange={(e) => {
              setStartDate(e.target.value);
              // Auto-set end date if empty or before start
              if (!endDate || e.target.value > endDate) {
                setEndDate(e.target.value);
              }
            }}
            className="w-full px-3 py-2.5 rounded-xl text-sm border-0 outline-none"
            style={{
              backgroundColor: 'var(--tg-secondary-bg)',
              color: 'var(--tg-text)',
            }}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label
            className="text-xs font-medium uppercase tracking-wider"
            style={{ color: 'var(--tg-section-header)' }}
          >
            Đến ngày
          </label>
          <input
            type="date"
            value={endDate}
            min={startDate || today}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl text-sm border-0 outline-none"
            style={{
              backgroundColor: 'var(--tg-secondary-bg)',
              color: 'var(--tg-text)',
            }}
          />
        </div>
      </div>

      {/* Business Days Count */}
      {startDate && endDate && businessDays > 0 && (
        <div
          className="flex items-center justify-between px-3 py-2 rounded-lg text-sm"
          style={{
            backgroundColor: 'var(--tg-secondary-bg)',
          }}
        >
          <span style={{ color: 'var(--tg-hint)' }}>Số ngày nghỉ (trừ T7, CN)</span>
          <span className="font-bold text-base" style={{ color: 'var(--tg-text)' }}>
            {businessDays} ngày
          </span>
        </div>
      )}

      {/* Balance Warning */}
      {showBalanceWarning && (
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm"
          style={{
            backgroundColor: '#FFF3E0',
            color: '#E65100',
          }}
        >
          <span>⚠️</span>
          <span>
            Vượt quá phép còn lại ({balance?.remaining} ngày). Đơn vẫn được gửi nhưng có thể bị từ chối.
          </span>
        </div>
      )}

      {/* Reason */}
      <div className="flex flex-col gap-1.5">
        <label
          className="text-xs font-medium uppercase tracking-wider"
          style={{ color: 'var(--tg-section-header)' }}
        >
          Lý do {isReasonRequired && <span style={{ color: '#FF3B30' }}>*</span>}
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder={
            isReasonRequired
              ? 'Vui lòng nhập lý do (bắt buộc)'
              : 'Nhập lý do nghỉ (tùy chọn)'
          }
          rows={3}
          className="w-full px-3 py-2.5 rounded-xl text-sm border-0 outline-none resize-none"
          style={{
            backgroundColor: 'var(--tg-secondary-bg)',
            color: 'var(--tg-text)',
          }}
        />
      </div>

      {/* Error */}
      {error && (
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm"
          style={{
            backgroundColor: '#FFEBEE',
            color: '#C62828',
          }}
        >
          <span>❌</span>
          <span>{error}</span>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={!isValid || isSubmitting}
        className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-200 active:scale-[0.98]"
        style={{
          backgroundColor: isValid && !isSubmitting
            ? 'var(--tg-button)'
            : 'var(--tg-secondary-bg)',
          color: isValid && !isSubmitting
            ? 'var(--tg-button-text)'
            : 'var(--tg-hint)',
          opacity: isSubmitting ? 0.7 : 1,
        }}
      >
        {isSubmitting ? (
          <span className="flex items-center justify-center gap-2">
            <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Đang gửi...
          </span>
        ) : (
          '📨 Gửi đơn xin nghỉ'
        )}
      </button>
    </div>
  );
}

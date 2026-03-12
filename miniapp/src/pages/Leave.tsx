/* ============================================
   Pyng Mini App — Leave Page (Stream C)
   Balance card + tab toggle (list / form)
   ============================================ */

import { useState, useEffect, useCallback } from 'react';
import { useTelegramContext } from '../contexts/TelegramContext';
import { useTelegram } from '../hooks/useTelegram';
import { fetchMyLeaves } from '../lib/api';
import type { LeaveRequest, LeaveBalance } from '../types';
import { LeaveForm } from '../components/LeaveForm';
import { LeaveList } from '../components/LeaveList';
import { ErrorState } from '../components/ErrorState';

type Tab = 'list' | 'form';

export function Leave() {
  const { initData } = useTelegramContext();
  const { haptic } = useTelegram();

  const [activeTab, setActiveTab] = useState<Tab>('list');
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [balance, setBalance] = useState<LeaveBalance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!initData) return;

    try {
      setIsLoading(true);
      setError(null);
      const res = await fetchMyLeaves(initData);
      setLeaves(res.leaves);
      setBalance(res.balance);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Không thể tải dữ liệu';
      setError(message);
      console.error('[Leave] Failed to load data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [initData]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFormSuccess = useCallback(() => {
    // Switch to list tab and refresh data
    setActiveTab('list');
    loadData();
  }, [loadData]);

  const handleTabChange = useCallback(
    (tab: Tab) => {
      haptic.selection();
      setActiveTab(tab);
    },
    [haptic],
  );

  return (
    <div className="flex flex-col gap-4 pb-24">
      {/* Balance Card */}
      <div
        className="rounded-2xl p-4 relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #5E5CE6 0%, #AF52DE 100%)',
        }}
      >
        {/* Decorative circles */}
        <div
          className="absolute -top-6 -right-6 w-24 h-24 rounded-full"
          style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}
        />
        <div
          className="absolute -bottom-4 -left-4 w-16 h-16 rounded-full"
          style={{ backgroundColor: 'rgba(255,255,255,0.08)' }}
        />

        <div className="relative z-10">
          <p className="text-white/70 text-xs font-medium uppercase tracking-wider mb-1">
            Phép năm còn lại
          </p>
          {isLoading ? (
            <div className="skeleton h-10 w-32 rounded-lg" style={{ opacity: 0.3 }} />
          ) : balance ? (
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold text-white">
                {balance.remaining}
              </span>
              <span className="text-white/60 text-lg">
                / {balance.total} ngày
              </span>
            </div>
          ) : (
            <span className="text-white/60 text-sm">--</span>
          )}

          {balance && !isLoading && (
            <div className="flex items-center gap-3 mt-2">
              <div
                className="h-1.5 flex-1 rounded-full overflow-hidden"
                style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}
              >
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.max(0, (balance.remaining / balance.total) * 100)}%`,
                    backgroundColor: 'rgba(255,255,255,0.8)',
                  }}
                />
              </div>
              <span className="text-white/60 text-xs whitespace-nowrap">
                Đã dùng {balance.used}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Tab Toggle */}
      <div
        className="flex rounded-xl overflow-hidden p-1"
        style={{ backgroundColor: 'var(--tg-secondary-bg)' }}
      >
        <button
          type="button"
          onClick={() => handleTabChange('list')}
          className="flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200"
          style={{
            backgroundColor:
              activeTab === 'list' ? 'var(--tg-section-bg)' : 'transparent',
            color:
              activeTab === 'list'
                ? 'var(--tg-text)'
                : 'var(--tg-hint)',
            boxShadow:
              activeTab === 'list'
                ? '0 1px 3px rgba(0,0,0,0.08)'
                : 'none',
          }}
        >
          📋 Danh sách
        </button>
        <button
          type="button"
          onClick={() => handleTabChange('form')}
          className="flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200"
          style={{
            backgroundColor:
              activeTab === 'form' ? 'var(--tg-section-bg)' : 'transparent',
            color:
              activeTab === 'form'
                ? 'var(--tg-text)'
                : 'var(--tg-hint)',
            boxShadow:
              activeTab === 'form'
                ? '0 1px 3px rgba(0,0,0,0.08)'
                : 'none',
          }}
        >
          ➕ Xin nghỉ
        </button>
      </div>

      {/* Error State */}
      {error && (
        <ErrorState error={error} onRetry={loadData} />
      )}

      {/* Tab Content */}
      <div className="min-h-[200px]">
        {activeTab === 'list' ? (
          <LeaveList
            leaves={leaves}
            isLoading={isLoading}
            onRefresh={loadData}
          />
        ) : (
          <LeaveForm balance={balance} onSuccess={handleFormSuccess} />
        )}
      </div>
    </div>
  );
}

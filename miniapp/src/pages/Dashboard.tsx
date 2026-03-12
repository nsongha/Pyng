/* ============================================
   Dashboard — Trang chính Mini App
   Stats + Gamification + Check-in History
   ============================================ */

import { useRef, useState } from 'react';
import { useTelegramContext } from '../contexts/TelegramContext';
import { StatsCard } from '../components/StatsCard';
import { GamificationCard } from '../components/GamificationCard';
import { CheckinHistoryList } from '../components/CheckinHistoryList';
import {
  StatsCardsSkeleton,
  GamificationCardSkeleton,
  HistoryListSkeleton,
} from '../components/LoadingSkeleton';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

export function Dashboard() {
  const { user, profile, checkins, isLoading, checkinsLoading, error, refreshProfile } =
    useTelegramContext();

  // Pull-to-refresh state
  const [isRefreshing, setIsRefreshing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Pull-to-refresh handler
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshProfile();
    } finally {
      setIsRefreshing(false);
    }
  };

  // Touch-based pull-to-refresh
  const touchStartY = useRef(0);
  const [pullDistance, setPullDistance] = useState(0);

  const handleTouchStart = (e: React.TouchEvent) => {
    if (containerRef.current && containerRef.current.scrollTop === 0) {
      touchStartY.current = e.touches[0].clientY;
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!touchStartY.current) return;
    const currentY = e.touches[0].clientY;
    const diff = currentY - touchStartY.current;
    if (diff > 0 && containerRef.current?.scrollTop === 0) {
      setPullDistance(Math.min(diff * 0.5, 80));
    }
  };

  const handleTouchEnd = () => {
    if (pullDistance > 60) {
      handleRefresh();
    }
    setPullDistance(0);
    touchStartY.current = 0;
  };

  // Display name
  const displayName = user
    ? user.first_name + (user.last_name ? ` ${user.last_name}` : '')
    : 'Bạn';

  // Error state
  if (error && !isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--tg-bg)' }}>
        <ErrorState error={error} onRetry={handleRefresh} />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="min-h-screen pb-20"
      style={{ backgroundColor: 'var(--tg-bg)' }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull-to-refresh indicator */}
      {pullDistance > 0 && (
        <div
          className="flex justify-center items-center transition-all"
          style={{ height: pullDistance }}
        >
          <div
            className={`w-6 h-6 border-2 border-t-transparent rounded-full ${
              pullDistance > 60 ? 'animate-spin' : ''
            }`}
            style={{
              borderColor: 'var(--tg-hint)',
              borderTopColor: 'transparent',
              transform: `rotate(${pullDistance * 3}deg)`,
            }}
          />
        </div>
      )}

      {/* Refresh indicator */}
      {isRefreshing && (
        <div className="flex justify-center py-3">
          <div
            className="w-5 h-5 border-2 border-t-transparent rounded-full animate-spin"
            style={{
              borderColor: 'var(--color-brand)',
              borderTopColor: 'transparent',
            }}
          />
        </div>
      )}

      {/* Header */}
      <header className="px-4 pt-4 pb-2">
        <div className="flex items-center gap-3">
          {/* Avatar */}
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold text-white shrink-0"
            style={{
              background:
                'linear-gradient(135deg, var(--color-brand) 0%, var(--color-brand-dark) 100%)',
            }}
          >
            {displayName.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0">
            <h1
              className="text-lg font-bold truncate"
              style={{ color: 'var(--tg-text)' }}
            >
              Xin chào, {displayName}! 👋
            </h1>
            <p className="text-xs" style={{ color: 'var(--tg-hint)' }}>
              {new Date().toLocaleDateString('vi-VN', {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
                year: 'numeric',
              })}
            </p>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="px-4 space-y-4 mt-2">
        {/* Stats Cards */}
        <section>
          <h2
            className="text-xs font-semibold uppercase tracking-wide mb-2"
            style={{ color: 'var(--tg-section-header)' }}
          >
            Thống kê tháng này
          </h2>
          {isLoading ? (
            <StatsCardsSkeleton />
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <StatsCard
                emoji="📊"
                label="Tổng ngày đi"
                value={profile?.checkin_stats.total_days ?? 0}
              />
              <StatsCard
                emoji="⏰"
                label="Đi muộn"
                value={profile?.checkin_stats.late_days ?? 0}
                accentColor={
                  (profile?.checkin_stats.late_days ?? 0) > 0
                    ? 'var(--color-warning)'
                    : undefined
                }
              />
              <StatsCard
                emoji="🏠"
                label="WFH"
                value={profile?.checkin_stats.wfh_days ?? 0}
                accentColor="var(--color-wfh)"
              />
              <StatsCard
                emoji="🌴"
                label="Nghỉ phép"
                value={`${profile?.leave_balance.used ?? 0}/${profile?.leave_balance.total ?? 0}`}
                accentColor="var(--color-leave)"
              />
            </div>
          )}
        </section>

        {/* Gamification Card */}
        <section>
          {isLoading ? (
            <GamificationCardSkeleton />
          ) : profile?.gamification ? (
            <GamificationCard stats={profile.gamification} />
          ) : null}
        </section>

        {/* Check-in History */}
        <section>
          <h2
            className="text-xs font-semibold uppercase tracking-wide mb-2"
            style={{ color: 'var(--tg-section-header)' }}
          >
            Lịch sử check-in (30 ngày)
          </h2>
          {checkinsLoading ? (
            <HistoryListSkeleton />
          ) : checkins.length === 0 ? (
            <EmptyState
              icon="📋"
              title="Chưa có lịch sử check-in"
              description="Hãy check-in bằng GPS, WiFi, QR hoặc NFC qua bot Telegram để bắt đầu!"
            />
          ) : (
            <CheckinHistoryList records={checkins} />
          )}
        </section>
      </main>
    </div>
  );
}

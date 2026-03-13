/* ============================================
   Pyng Mini App — Telegram Context Provider
   Cung cấp user info + theme cho toàn app
   Parallel fetch: fetchMe + fetchCheckins cùng lúc
   ============================================ */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { useTelegram, type TelegramUser } from '../hooks/useTelegram';
import type { CheckinRecord, MeResponse } from '../types';
import { fetchMe, fetchCheckins } from '../lib/api';

interface TelegramContextValue {
  /** Telegram user info */
  user: TelegramUser | null;
  /** Raw initData for API auth */
  initData: string;
  /** Color scheme from Telegram */
  colorScheme: 'light' | 'dark';
  /** Whether running inside Telegram */
  isInTelegram: boolean;
  /** User profile + stats from API */
  profile: MeResponse | null;
  /** Recent check-in records (parallel-fetched) */
  checkins: CheckinRecord[];
  /** Loading state for profile + checkins */
  isLoading: boolean;
  /** Loading state specifically for checkins */
  checkinsLoading: boolean;
  /** Error state */
  error: Error | string | null;
  /** Reload all dashboard data (profile + checkins) */
  refreshProfile: () => Promise<void>;
}

const TelegramContext = createContext<TelegramContextValue | null>(null);

/**
 * Provider component — wrap quanh App.
 * Parallel fetch: gọi /api/me + /api/checkins cùng lúc khi mount.
 * Dùng Promise.allSettled để 1 call fail không ảnh hưởng call kia.
 */
export function TelegramProvider({ children }: { children: ReactNode }) {
  const telegram = useTelegram();
  const [profile, setProfile] = useState<MeResponse | null>(null);
  const [checkins, setCheckins] = useState<CheckinRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [checkinsLoading, setCheckinsLoading] = useState(true);
  const [error, setError] = useState<Error | string | null>(null);

  const loadDashboardData = async () => {
    if (!telegram.initData) {
      setIsLoading(false);
      setCheckinsLoading(false);
      setError('Vui lòng mở app từ Telegram');
      return;
    }

    setIsLoading(true);
    setCheckinsLoading(true);
    setError(null);

    // 2 promise chains chạy SONG SONG nhưng update state ĐỘC LẬP
    // → Profile hiện ngay khi fetchMe xong, không đợi fetchCheckins

    // Chain 1: Profile (isLoading)
    const profilePromise = fetchMe(telegram.initData)
      .then((data) => {
        setProfile(data);
      })
      .catch((err) => {
        if (err instanceof Error) {
          setError(err);
        } else {
          setError(String(err));
        }
        console.error('[TelegramProvider] Failed to load profile:', err);
      })
      .finally(() => {
        setIsLoading(false);
      });

    // Chain 2: Checkins (checkinsLoading) — fail không ảnh hưởng profile
    const checkinsPromise = fetchCheckins(telegram.initData, 30, 0)
      .then((data) => {
        setCheckins(data.data);
      })
      .catch((err) => {
        console.error('[TelegramProvider] Failed to load checkins:', err);
      })
      .finally(() => {
        setCheckinsLoading(false);
      });

    // Đợi cả 2 hoàn thành (cho refreshProfile await được)
    await Promise.all([profilePromise, checkinsPromise]);
  };

  useEffect(() => {
    loadDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [telegram.initData]);

  return (
    <TelegramContext.Provider
      value={{
        user: telegram.user,
        initData: telegram.initData,
        colorScheme: telegram.colorScheme,
        isInTelegram: telegram.isInTelegram,
        profile,
        checkins,
        isLoading,
        checkinsLoading,
        error,
        refreshProfile: loadDashboardData,
      }}
    >
      {children}
    </TelegramContext.Provider>
  );
}

/**
 * Hook để dùng TelegramContext trong components.
 * PHẢI dùng trong TelegramProvider.
 */
export function useTelegramContext(): TelegramContextValue {
  const context = useContext(TelegramContext);
  if (!context) {
    throw new Error('useTelegramContext must be used within TelegramProvider');
  }
  return context;
}

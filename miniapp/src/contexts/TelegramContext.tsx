/* ============================================
   Pyng Mini App — Telegram Context Provider
   Cung cấp user info + theme cho toàn app
   ============================================ */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { useTelegram, type TelegramUser } from '../hooks/useTelegram';
import type { MeResponse } from '../types';
import { fetchMe } from '../lib/api';

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
  /** Loading state for profile */
  isLoading: boolean;
  /** Error state */
  error: Error | string | null;
  /** Reload profile data */
  refreshProfile: () => Promise<void>;
}

const TelegramContext = createContext<TelegramContextValue | null>(null);

/**
 * Provider component — wrap quanh App.
 * Tự động gọi /api/me khi mount để load profile.
 */
export function TelegramProvider({ children }: { children: ReactNode }) {
  const telegram = useTelegram();
  const [profile, setProfile] = useState<MeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | string | null>(null);

  const loadProfile = async () => {
    if (!telegram.initData) {
      setIsLoading(false);
      setError('Vui lòng mở app từ Telegram');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchMe(telegram.initData);
      setProfile(data);
    } catch (err) {
      // Giữ nguyên error object để ErrorState phân biệt loại lỗi
      if (err instanceof Error) {
        setError(err);
      } else {
        setError(String(err));
      }
      console.error('[TelegramProvider] Failed to load profile:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
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
        isLoading,
        error,
        refreshProfile: loadProfile,
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

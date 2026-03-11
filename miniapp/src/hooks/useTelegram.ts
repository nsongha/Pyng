/* ============================================
   Pyng Mini App — Telegram WebApp Hook
   Wraps @twa-dev/sdk for React usage
   ============================================ */

import { useCallback, useEffect, useState } from 'react';
import WebApp from '@twa-dev/sdk';

export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
}

export interface UseTelegramReturn {
  /** Telegram WebApp SDK instance */
  webApp: typeof WebApp;
  /** Current user from initDataUnsafe */
  user: TelegramUser | null;
  /** Raw initData string for server auth */
  initData: string;
  /** Current color scheme */
  colorScheme: 'light' | 'dark';
  /** Whether running inside Telegram */
  isInTelegram: boolean;
  /** Close the Mini App */
  close: () => void;
  /** Show back button */
  showBackButton: () => void;
  /** Hide back button */
  hideBackButton: () => void;
  /** Haptic feedback */
  haptic: {
    impact: (style?: 'light' | 'medium' | 'heavy') => void;
    notification: (type: 'error' | 'success' | 'warning') => void;
    selection: () => void;
  };
}

/**
 * Hook để tương tác với Telegram WebApp SDK.
 *
 * Khởi tạo WebApp.ready() + expand(), lấy user info,
 * và expose các helpers (back button, haptic, etc.).
 */
export function useTelegram(): UseTelegramReturn {
  const [colorScheme, setColorScheme] = useState<'light' | 'dark'>(
    WebApp.colorScheme || 'light'
  );

  useEffect(() => {
    // Signal Telegram that Mini App is ready
    WebApp.ready();
    // Expand to full height
    WebApp.expand();

    // Listen for theme changes
    const handleThemeChanged = () => {
      setColorScheme(WebApp.colorScheme || 'light');
    };

    WebApp.onEvent('themeChanged', handleThemeChanged);

    return () => {
      WebApp.offEvent('themeChanged', handleThemeChanged);
    };
  }, []);

  const user: TelegramUser | null = WebApp.initDataUnsafe?.user
    ? {
        id: WebApp.initDataUnsafe.user.id,
        first_name: WebApp.initDataUnsafe.user.first_name,
        last_name: WebApp.initDataUnsafe.user.last_name,
        username: WebApp.initDataUnsafe.user.username,
        language_code: WebApp.initDataUnsafe.user.language_code,
        photo_url: WebApp.initDataUnsafe.user.photo_url,
      }
    : null;

  const initData = WebApp.initData || '';

  const isInTelegram = !!WebApp.initData;

  const close = useCallback(() => WebApp.close(), []);

  const showBackButton = useCallback(() => {
    WebApp.BackButton.show();
  }, []);

  const hideBackButton = useCallback(() => {
    WebApp.BackButton.hide();
  }, []);

  const haptic = {
    impact: (style: 'light' | 'medium' | 'heavy' = 'light') => {
      WebApp.HapticFeedback.impactOccurred(style);
    },
    notification: (type: 'error' | 'success' | 'warning') => {
      WebApp.HapticFeedback.notificationOccurred(type);
    },
    selection: () => {
      WebApp.HapticFeedback.selectionChanged();
    },
  };

  return {
    webApp: WebApp,
    user,
    initData,
    colorScheme,
    isInTelegram,
    close,
    showBackButton,
    hideBackButton,
    haptic,
  };
}

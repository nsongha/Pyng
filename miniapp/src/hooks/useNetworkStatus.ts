/* ============================================
   useNetworkStatus — Detect online/offline state
   Auto retry callback khi có mạng lại
   ============================================ */

import { useCallback, useEffect, useState } from 'react';

export interface UseNetworkStatusReturn {
  /** true khi có kết nối mạng */
  isOnline: boolean;
  /** true khi vừa reconnect (dùng để trigger auto retry) */
  wasOffline: boolean;
}

/**
 * Hook detect network status.
 *
 * - Lắng nghe `online` / `offline` events
 * - `wasOffline` = true khi vừa chuyển từ offline → online
 * - Dùng `onReconnect` callback để auto retry API calls
 */
export function useNetworkStatus(onReconnect?: () => void): UseNetworkStatusReturn {
  const [isOnline, setIsOnline] = useState(() =>
    typeof navigator !== 'undefined' ? navigator.onLine : true,
  );
  const [wasOffline, setWasOffline] = useState(false);

  const handleOnline = useCallback(() => {
    setIsOnline(true);
    setWasOffline(true);
    onReconnect?.();
    // Reset wasOffline flag after 3s
    setTimeout(() => setWasOffline(false), 3000);
  }, [onReconnect]);

  const handleOffline = useCallback(() => {
    setIsOnline(false);
  }, []);

  useEffect(() => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline]);

  return { isOnline, wasOffline };
}

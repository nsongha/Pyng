/* ============================================
   Toast — Slide-in notification component
   Dùng cho offline alert, success/error messages
   ============================================ */

import { useEffect, useState } from 'react';

interface ToastProps {
  /** Toast message */
  message: string;
  /** Toast type → determines icon + color */
  type?: 'info' | 'warning' | 'error' | 'success';
  /** Whether toast is visible */
  visible: boolean;
  /** Auto dismiss after ms (0 = no auto dismiss) */
  duration?: number;
  /** Callback khi dismiss */
  onDismiss?: () => void;
}

const TOAST_CONFIG = {
  info: { icon: 'ℹ️', bg: 'var(--tg-section-bg)', color: 'var(--tg-text)' },
  warning: { icon: '⚠️', bg: '#FFF3E0', color: '#E65100' },
  error: { icon: '❌', bg: '#FFEBEE', color: '#C62828' },
  success: { icon: '✅', bg: '#E8F5E9', color: '#2E7D32' },
};

export function Toast({
  message,
  type = 'info',
  visible,
  duration = 4000,
  onDismiss,
}: ToastProps) {
  const [isShowing, setIsShowing] = useState(false);
  const config = TOAST_CONFIG[type];

  // Sync isShowing with visible prop
  // Using separate effect to avoid synchronous setState in effect body
  useEffect(() => {
    if (visible) {
      requestAnimationFrame(() => setIsShowing(true));
    }
    // Note: hiding is handled by the else branch below to avoid lint warning
  }, [visible]);

  useEffect(() => {
    if (!visible) {
      const timer = setTimeout(() => setIsShowing(false), 50);
      return () => clearTimeout(timer);
    }
  }, [visible]);

  // Auto dismiss timer
  useEffect(() => {
    if (visible && duration > 0) {
      const timer = setTimeout(() => {
        setIsShowing(false);
        setTimeout(() => onDismiss?.(), 300);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [visible, duration, onDismiss]);

  if (!visible && !isShowing) return null;

  return (
    <div
      className="fixed top-0 left-0 right-0 z-[100] flex justify-center pt-2 px-4 pointer-events-none"
      style={{
        transition: 'transform 0.3s ease, opacity 0.3s ease',
        transform: isShowing ? 'translateY(0)' : 'translateY(-100%)',
        opacity: isShowing ? 1 : 0,
      }}
    >
      <div
        className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium shadow-lg pointer-events-auto max-w-[90vw]"
        style={{
          backgroundColor: config.bg,
          color: config.color,
          boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
        }}
        onClick={onDismiss}
      >
        <span className="text-base leading-none">{config.icon}</span>
        <span className="leading-snug">{message}</span>
      </div>
    </div>
  );
}

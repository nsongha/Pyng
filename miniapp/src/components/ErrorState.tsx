/* ============================================
   ErrorState — Reusable error display component
   Phân biệt loại lỗi: auth / not found / server / network
   ============================================ */

import { PyngApiError } from '../lib/api';

interface ErrorStateProps {
  /** Error object hoặc string message */
  error: PyngApiError | Error | string;
  /** Callback khi nhấn "Thử lại" */
  onRetry?: () => void;
  /** Cho phép tùy chỉnh class container */
  className?: string;
}

/** Lấy icon + title + description dựa trên loại lỗi */
function getErrorDisplay(error: PyngApiError | Error | string) {
  if (typeof error === 'string') {
    return {
      icon: '😵',
      title: 'Đã có lỗi xảy ra',
      description: error,
    };
  }

  if (error instanceof PyngApiError) {
    if (error.isNetworkError()) {
      return {
        icon: '📡',
        title: 'Không có kết nối',
        description: 'Kiểm tra kết nối mạng và thử lại.',
      };
    }
    if (error.isAuthError()) {
      return {
        icon: '🔐',
        title: 'Phiên hết hạn',
        description: error.message,
      };
    }
    if (error.isNotFound()) {
      return {
        icon: '🔍',
        title: 'Không tìm thấy',
        description: error.message,
      };
    }
    if (error.isServerError()) {
      return {
        icon: '💥',
        title: 'Lỗi server',
        description: error.message,
      };
    }
    return {
      icon: '😵',
      title: 'Đã có lỗi',
      description: error.message,
    };
  }

  return {
    icon: '😵',
    title: 'Đã có lỗi xảy ra',
    description: error.message || 'Không rõ nguyên nhân',
  };
}

export function ErrorState({ error, onRetry, className = '' }: ErrorStateProps) {
  const { icon, title, description } = getErrorDisplay(error);

  return (
    <div
      className={`flex flex-col items-center justify-center py-12 px-6 text-center animate-fade-in ${className}`}
    >
      <div className="text-5xl mb-4">{icon}</div>
      <h2
        className="text-base font-semibold mb-1.5"
        style={{ color: 'var(--tg-text)' }}
      >
        {title}
      </h2>
      <p
        className="text-sm mb-6 max-w-[260px] leading-relaxed"
        style={{ color: 'var(--tg-hint)' }}
      >
        {description}
      </p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="px-6 py-2.5 rounded-full text-sm font-medium text-white active:scale-95 transition-transform"
          style={{ backgroundColor: 'var(--color-brand)' }}
        >
          🔄 Thử lại
        </button>
      )}
    </div>
  );
}

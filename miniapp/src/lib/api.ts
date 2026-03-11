/* ============================================
   Pyng Mini App — API Client
   Auth: Telegram WebApp initData → header
   ============================================ */

import type {
  MeResponse,
  CheckinsResponse,
  LeaderboardResponse,
  ApiError,
} from '../types';

/** Base URL — cùng domain trên Vercel */
const API_BASE = '/api';

/** Custom error khi API trả lỗi */
export class PyngApiError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = 'PyngApiError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Gọi API với Telegram initData auth.
 *
 * Auth pattern: gửi raw initData qua header X-Telegram-Init-Data
 * → Server validate bằng HMAC-SHA256 (dùng BOT_TOKEN)
 */
async function apiFetch<T>(
  path: string,
  initData: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(initData ? { 'X-Telegram-Init-Data': initData } : {}),
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...(options?.headers as Record<string, string>),
    },
  });

  if (!response.ok) {
    let errorData: ApiError | null = null;
    try {
      errorData = await response.json();
    } catch {
      // JSON parse failed, use status text
    }

    throw new PyngApiError(
      response.status,
      errorData?.error || `HTTP ${response.status}`,
      errorData?.detail,
    );
  }

  return response.json();
}

/* ============================================
   API Functions
   ============================================ */

/**
 * GET /api/me — Lấy thông tin user + gamification stats
 */
export function fetchMe(initData: string): Promise<MeResponse> {
  return apiFetch<MeResponse>('/me', initData);
}

/**
 * GET /api/checkins — Lấy lịch sử check-in (paginated)
 */
export function fetchCheckins(
  initData: string,
  limit = 30,
  offset = 0,
): Promise<CheckinsResponse> {
  return apiFetch<CheckinsResponse>(
    `/checkins?limit=${limit}&offset=${offset}`,
    initData,
  );
}

/**
 * GET /api/leaderboard — Bảng xếp hạng
 */
export function fetchLeaderboard(
  initData: string,
  period: 'month' | 'alltime' = 'month',
): Promise<LeaderboardResponse> {
  return apiFetch<LeaderboardResponse>(
    `/leaderboard?period=${period}`,
    initData,
  );
}

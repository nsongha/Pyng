/* ============================================
   Pyng Mini App — API Client
   Auth: Telegram WebApp initData → header
   ============================================ */

import type {
  MeResponse,
  CheckinsResponse,
  LeaderboardResponse,
  ChartDataResponse,
  OvertimeResponse,
  ApiError,
  MyLeavesResponse,
  LeaveFormData,
  SubmitLeaveResponse,
  SalaryResponse,
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

  /** 401 — Token expired/invalid */
  isAuthError(): boolean {
    return this.status === 401 || this.status === 403;
  }

  /** 404 — Endpoint/resource not found */
  isNotFound(): boolean {
    return this.status === 404;
  }

  /** 500+ — Server error */
  isServerError(): boolean {
    return this.status >= 500;
  }

  /** 0 — Network/offline error */
  isNetworkError(): boolean {
    return this.status === 0;
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

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...(options?.headers as Record<string, string>),
      },
    });
  } catch (err) {
    // Network error (offline, DNS fail, CORS, etc.)
    throw new PyngApiError(
      0,
      'Không thể kết nối đến server',
      err instanceof Error ? err.message : 'Network error',
    );
  }

  if (!response.ok) {
    let errorData: ApiError | null = null;
    try {
      errorData = await response.json();
    } catch {
      // JSON parse failed, use status text
    }

    // User-friendly messages based on status
    let message = errorData?.error || `HTTP ${response.status}`;
    if (response.status === 401) {
      message = errorData?.error || 'Phiên đăng nhập hết hạn. Vui lòng mở lại app từ Telegram.';
    } else if (response.status === 404) {
      message = errorData?.error || 'Không tìm thấy dữ liệu';
    } else if (response.status >= 500) {
      message = errorData?.error || 'Lỗi server. Vui lòng thử lại sau.';
    }

    throw new PyngApiError(
      response.status,
      message,
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

/* ============================================
   Chart & Overtime API (Stream B)
   ============================================ */

/**
 * GET /api/checkins/chart — Chart data cho tháng
 */
export function fetchChartData(
  initData: string,
  month: string,
): Promise<ChartDataResponse> {
  return apiFetch<ChartDataResponse>(
    `/checkins/chart?month=${month}`,
    initData,
  );
}

/**
 * GET /api/overtime — Overtime data cho tháng
 */
export function fetchOvertime(
  initData: string,
  month: string,
): Promise<OvertimeResponse> {
  return apiFetch<OvertimeResponse>(
    `/overtime?month=${month}`,
    initData,
  );
}

/* ============================================
   Leave Management API (Stream C)
   ============================================ */

/**
 * GET /api/leave/my — Lấy danh sách đơn nghỉ + balance
 */
export function fetchMyLeaves(
  initData: string,
  year?: number,
): Promise<MyLeavesResponse> {
  const params = year ? `?year=${year}` : '';
  return apiFetch<MyLeavesResponse>(`/leave/my${params}`, initData);
}

/**
 * POST /api/leave/request — Tạo đơn xin nghỉ mới
 */
export function submitLeaveRequest(
  initData: string,
  data: LeaveFormData,
): Promise<SubmitLeaveResponse> {
  return apiFetch<SubmitLeaveResponse>('/leave/request', initData, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/* ============================================
   Salary API (Stream C — Phase 6)
   ============================================ */

/**
 * GET /api/salary — Lấy salary summary tháng
 */
export function fetchSalary(
  initData: string,
  month: string,
): Promise<SalaryResponse> {
  return apiFetch<SalaryResponse>(
    `/salary?month=${month}`,
    initData,
  );
}

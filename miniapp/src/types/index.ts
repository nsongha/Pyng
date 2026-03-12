/* ============================================
   Pyng Mini App — TypeScript Type Definitions
   ============================================ */

/** User info from API */
export interface User {
  id: number;
  telegram_id: number;
  full_name: string;
  username: string | null;
  role: 'employee' | 'admin';
  status: 'active' | 'pending' | 'rejected';
  created_at: string;
}

/** Gamification stats */
export interface GamificationStats {
  total_points: number;
  current_streak: number;
  longest_streak: number;
  ontime_count: number;
  early_count: number;
  rank: number;
}

/** Check-in summary stats */
export interface CheckinStats {
  total_days: number;
  late_days: number;
  wfh_days: number;
  leave_days: number;
  ontime_percentage: number;
}

/** Leave balance */
export interface LeaveBalance {
  total: number;
  used: number;
  remaining: number;
}

/** /api/me response */
export interface MeResponse {
  user: User;
  gamification: GamificationStats;
  checkin_stats: CheckinStats;
  leave_balance: LeaveBalance;
}

/** Single check-in record */
export interface CheckinRecord {
  id: number;
  user_id: number;
  date: string;
  time_in: string | null;
  time_out: string | null;
  method: 'gps' | 'wifi' | 'qr' | 'nfc' | 'manual' | 'wfh';
  mood: 'great' | 'good' | 'tired' | 'sos' | null;
  is_ontime: boolean;
  late_minutes: number;
  working_hours: number | null;
  note: string | null;
}

/** Paginated check-in response */
export interface CheckinsResponse {
  data: CheckinRecord[];
  total: number;
  limit: number;
  offset: number;
}

/** Leaderboard entry */
export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  full_name: string;
  total_points: number;
  current_streak: number;
}

/** Leaderboard response */
export interface LeaderboardResponse {
  leaderboard: LeaderboardEntry[];
  user_rank: number;
  user_points: number;
  period: 'month' | 'alltime';
}

/** Streak milestone info */
export interface StreakMilestone {
  icon: string;
  label: string;
  min_days: number;
}

/** API Error */
export interface ApiError {
  error: string;
  detail?: string;
}

/** Method display config */
export const METHOD_LABELS: Record<CheckinRecord['method'], { label: string; emoji: string; color: string }> = {
  gps: { label: 'GPS', emoji: '📍', color: 'text-blue-500' },
  wifi: { label: 'WiFi', emoji: '📶', color: 'text-green-500' },
  qr: { label: 'QR', emoji: '📱', color: 'text-purple-500' },
  nfc: { label: 'NFC', emoji: '🏷️', color: 'text-orange-500' },
  manual: { label: 'Manual', emoji: '📸', color: 'text-gray-500' },
  wfh: { label: 'WFH', emoji: '🏠', color: 'text-cyan-500' },
};

/** Mood display config */
export const MOOD_LABELS: Record<string, { label: string; emoji: string }> = {
  great: { label: 'Siêu năng suất', emoji: '🔥' },
  good: { label: 'Bình thường', emoji: '😊' },
  tired: { label: 'Hơi mệt', emoji: '😴' },
  sos: { label: 'Cần hỗ trợ', emoji: '🆘' },
};

/** Streak milestone config */
export const STREAK_MILESTONES: StreakMilestone[] = [
  { icon: '💎', label: 'Huyền thoại', min_days: 30 },
  { icon: '⚡', label: 'Chuyên nghiệp', min_days: 20 },
  { icon: '🔥🔥🔥', label: 'Ổn định', min_days: 10 },
  { icon: '🔥🔥', label: 'Vào guồng', min_days: 5 },
  { icon: '🔥', label: 'Đang khởi động', min_days: 1 },
];

/** Get streak milestone for given days */
export function getStreakMilestone(days: number): StreakMilestone | null {
  return STREAK_MILESTONES.find(m => days >= m.min_days) ?? null;
}

/* ============================================
   Chart Data Types (Phase 5 — Stream B)
   Matches /api/checkins/chart response
   ============================================ */

/** Single day entry for working hours chart */
export interface DailyHour {
  date: string;
  hours: number;
  is_late: boolean;
  method: CheckinRecord['method'] | null;
  mood: CheckinRecord['mood'] | null;
}

/** Chart summary stats */
export interface ChartSummary {
  avg_hours: number;
  total_days: number;
  ontime_rate: number;
  most_used_method: CheckinRecord['method'] | null;
}

/** Month-over-month trend */
export interface ChartTrend {
  prev_month_avg: number;
  current_avg: number;
  change_percent: number;
}

/** GET /api/checkins/chart response */
export interface ChartDataResponse {
  ok: boolean;
  month: string;
  daily_hours: DailyHour[];
  summary: ChartSummary;
  trend: ChartTrend;
}

/* ============================================
   Overtime Types (Phase 5 — Stream B)
   Matches /api/overtime response
   ============================================ */

/** Single overtime session */
export interface OvertimeSession {
  date: string;
  minutes: number;
  checkout_time: string;
}

/** GET /api/overtime response */
export interface OvertimeResponse {
  ok: boolean;
  month: string;
  total_minutes: number;
  total_days: number;
  sessions: OvertimeSession[];
}


/* ============================================
   Leave Management Types (Stream C)
   ============================================ */

/** Leave type options */
export type LeaveType = 'annual' | 'sick' | 'compensatory' | 'unpaid';

/** Leave request status */
export type LeaveStatus = 'pending' | 'approved' | 'rejected';

/** Single leave request record (from API) */
export interface LeaveRequest {
  id: number;
  user_id: number;
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  days_count: number;
  reason: string | null;
  status: LeaveStatus;
  approved_by: number | null;
  requested_at: string;
  processed_at: string | null;
}

/** Form submission data for POST /api/leave/request */
export interface LeaveFormData {
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  reason?: string;
}

/** GET /api/leave/my response */
export interface MyLeavesResponse {
  ok: boolean;
  year: number;
  leaves: LeaveRequest[];
  balance: LeaveBalance;
}

/** POST /api/leave/request response */
export interface SubmitLeaveResponse {
  ok: boolean;
  leave: LeaveRequest;
}

/** Leave type display config */
export const LEAVE_TYPE_LABELS: Record<LeaveType, { label: string; emoji: string; color: string }> = {
  annual: { label: 'Phép năm', emoji: '🏖️', color: 'text-blue-500' },
  sick: { label: 'Nghỉ ốm', emoji: '🏥', color: 'text-red-500' },
  compensatory: { label: 'Nghỉ bù', emoji: '🔄', color: 'text-purple-500' },
  unpaid: { label: 'Không lương', emoji: '💼', color: 'text-gray-500' },
};

/** Leave status display config */
export const LEAVE_STATUS_LABELS: Record<LeaveStatus, { label: string; emoji: string; color: string; bgColor: string }> = {
  pending: { label: 'Chờ duyệt', emoji: '🟡', color: '#CA8A04', bgColor: 'rgba(202, 138, 4, 0.1)' },
  approved: { label: 'Đã duyệt', emoji: '✅', color: '#16A34A', bgColor: 'rgba(22, 163, 74, 0.1)' },
  rejected: { label: 'Từ chối', emoji: '❌', color: '#DC2626', bgColor: 'rgba(220, 38, 38, 0.1)' },
};

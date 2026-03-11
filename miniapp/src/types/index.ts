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

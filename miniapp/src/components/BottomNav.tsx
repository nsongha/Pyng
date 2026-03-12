/* ============================================
   Bottom Navigation — 3 tabs
   Telegram theme-aware, fixed bottom
   ============================================ */

import { useLocation, useNavigate } from 'react-router-dom';

interface NavItem {
  path: string;
  label: string;
  emoji: string;
}

const NAV_ITEMS: NavItem[] = [
  { path: '/', label: 'Dashboard', emoji: '📊' },
  { path: '/charts', label: 'Thống kê', emoji: '📈' },
  { path: '/leave', label: 'Nghỉ phép', emoji: '📋' },
  { path: '/salary', label: 'Lương', emoji: '💰' },
];

export function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 safe-bottom"
      style={{
        backgroundColor: 'var(--tg-section-bg)',
        borderTop: '0.5px solid var(--tg-secondary-bg)',
      }}
    >
      <div className="flex items-stretch h-14 max-w-lg mx-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path;

          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className="flex-1 flex flex-col items-center justify-center gap-0.5 transition-colors duration-200"
              style={{
                color: isActive ? 'var(--tg-accent)' : 'var(--tg-hint)',
              }}
            >
              <span className="text-lg leading-none">{item.emoji}</span>
              <span
                className="text-[10px] font-medium leading-none"
                style={{
                  opacity: isActive ? 1 : 0.7,
                }}
              >
                {item.label}
              </span>
              {/* Active indicator dot */}
              {isActive && (
                <div
                  className="absolute bottom-1 w-1 h-1 rounded-full"
                  style={{ backgroundColor: 'var(--tg-accent)' }}
                />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

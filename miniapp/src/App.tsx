/* ============================================
   Pyng Mini App — Root Component
   Router + Bottom Navigation
   Lazy loading: Charts/Leave/Salary chỉ load khi navigate
   ============================================ */

import './index.css';
import { lazy, Suspense, useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { TelegramProvider } from './contexts/TelegramContext';
import { Dashboard } from './pages/Dashboard';
import { BottomNav } from './components/BottomNav';
import { Toast } from './components/Toast';
import { useNetworkStatus } from './hooks/useNetworkStatus';

// Lazy load pages — giảm initial bundle, chỉ tải khi user navigate
const Charts = lazy(() => import('./pages/Charts').then(m => ({ default: m.Charts })));
const Leave = lazy(() => import('./pages/Leave').then(m => ({ default: m.Leave })));
const Salary = lazy(() => import('./pages/Salary').then(m => ({ default: m.Salary })));

/** Lazy page fallback — nhẹ, hiện spinner nhỏ */
function PageFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--tg-bg)' }}>
      <div
        className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin"
        style={{
          borderColor: 'var(--color-brand)',
          borderTopColor: 'transparent',
        }}
      />
    </div>
  );
}

/** Offline Toast wrapper — nằm ngoài Router */
function OfflineToast() {
  const [showReconnected, setShowReconnected] = useState(false);
  const { isOnline } = useNetworkStatus(
    useCallback(() => setShowReconnected(true), []),
  );

  return (
    <>
      <Toast
        message="Không có kết nối mạng"
        type="warning"
        visible={!isOnline}
        duration={0}
      />
      <Toast
        message="Đã kết nối lại!"
        type="success"
        visible={showReconnected}
        duration={3000}
        onDismiss={() => setShowReconnected(false)}
      />
    </>
  );
}

function App() {
  return (
    <BrowserRouter basename="/miniapp">
      <OfflineToast />
      <TelegramProvider>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/charts" element={<Charts />} />
            <Route path="/leave" element={<Leave />} />
            <Route path="/salary" element={<Salary />} />
          </Routes>
        </Suspense>
        <BottomNav />
      </TelegramProvider>
    </BrowserRouter>
  );
}

export default App;


/* ============================================
   Pyng Mini App — Root Component
   Router + Bottom Navigation
   ============================================ */

import './index.css';
import { useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { TelegramProvider } from './contexts/TelegramContext';
import { Dashboard } from './pages/Dashboard';
import { Charts } from './pages/Charts';
import { Leave } from './pages/Leave';
import { BottomNav } from './components/BottomNav';
import { Toast } from './components/Toast';
import { useNetworkStatus } from './hooks/useNetworkStatus';

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
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/charts" element={<Charts />} />
          <Route path="/leave" element={<Leave />} />
        </Routes>
        <BottomNav />
      </TelegramProvider>
    </BrowserRouter>
  );
}

export default App;


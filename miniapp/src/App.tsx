/* ============================================
   Pyng Mini App — Root Component
   Router + Bottom Navigation
   ============================================ */

import './index.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { TelegramProvider } from './contexts/TelegramContext';
import { Dashboard } from './pages/Dashboard';
import { Charts } from './pages/Charts';
import { Leave } from './pages/Leave';
import { BottomNav } from './components/BottomNav';

function App() {
  return (
    <BrowserRouter basename="/miniapp">
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

/* ============================================
   Pyng Mini App — Root Component
   ============================================ */

import './index.css';
import { TelegramProvider } from './contexts/TelegramContext';
import { Dashboard } from './pages/Dashboard';

function App() {
  return (
    <TelegramProvider>
      <Dashboard />
    </TelegramProvider>
  );
}

export default App;

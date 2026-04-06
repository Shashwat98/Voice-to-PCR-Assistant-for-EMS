import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { SessionPage } from './pages/SessionPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/session" element={<SessionPage />} />
        <Route path="*" element={<Navigate to="/session" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

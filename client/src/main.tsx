import React, { useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { supabase } from './utils/supabaseClient';
import LoginPage from './components/LoginPage';
import ApiKeyPage from './components/ApiKeyPage';
import ReposPage from './components/ReposPage';
import './index.css';

function AppRoutes() {
  const navigate = useNavigate();
  
  useEffect(() => {
    if (window.location.hash && window.location.hash.includes('access_token=')) {
      console.log('Detected auth redirect with token');
      
      const checkSession = async () => {
        const { data } = await supabase.auth.getSession();
        if (data.session) {
          console.log('Session established, redirecting to API key page');
          navigate('/api-key');
        }
      };
      
      checkSession();
    }
  }, [navigate]);
  
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/api-key" element={<ApiKeyPage />} />
      <Route path="/repos" element={<ReposPage />} />
    </Routes>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  </React.StrictMode>
);


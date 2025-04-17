import React, { useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { supabase } from './utils/supabaseClient';
import LoginPage from './components/LoginPage';
import ApiKeyPage from './components/ApiKeyPage';
import ReposPage from './components/ReposPage';
import './index.css';

function AuthCheck() {
  const navigate = useNavigate();
  
  useEffect(() => {
    if (window.location.hash && window.location.hash.includes('access_token=')) {
      console.log('Auth redirect detected in AuthCheck');
      
      const processAuth = async () => {
        const { data } = await supabase.auth.getSession();
        
        if (data.session) {
          console.log('Session established in AuthCheck, redirecting to /api-key');
          navigate('/api-key', { replace: true });
        }
      };
      
      processAuth();
    }
  }, [navigate]);
  
  return null;
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-container">Loading...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <>
      <AuthCheck />
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/api-key" element={
          <ProtectedRoute>
            <ApiKeyPage />
          </ProtectedRoute>
        } />
        <Route path="/repos" element={
          <ProtectedRoute>
            <ReposPage />
          </ProtectedRoute>
        } />
      </Routes>
    </>
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


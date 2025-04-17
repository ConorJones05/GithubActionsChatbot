import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import LoginPage from './components/LoginPage';
import ApiKeyPage from './components/ApiKeyPage';
import ReposPage from './components/ReposPage';
import './index.css';

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/api-key" element={<ApiKeyPage />} />
          <Route path="/repos" element={<ReposPage />} />
        </Routes>
      </Router>
    </AuthProvider>
  </React.StrictMode>
);


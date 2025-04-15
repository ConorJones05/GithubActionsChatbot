import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { HashRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/login";
import ApiPage from "./pages/api-key";
import Repos from "./pages/repos";
import { AuthProvider, useAuth } from "./context/AuthContext";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div>
      <div></div> 
      {/* add the loading animation */}
    </div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/api-key" element={
        <ProtectedRoute>
          <ApiPage />
        </ProtectedRoute>
      } />
      <Route path="/repos" element={
        <ProtectedRoute>
          <Repos />
        </ProtectedRoute>
      } />
    </Routes>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  </React.StrictMode>
);

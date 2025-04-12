import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/login';
import ApiPage from './pages/api-key';
// import Repos from './pages/repos';

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/api-key" element={<ApiPage />} />
        {/* <Route path="/Repos" element={<Repos />} /> */}
      </Routes>
    </Router>
  </React.StrictMode>
);

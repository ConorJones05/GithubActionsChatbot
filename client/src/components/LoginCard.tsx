import React from "react";
import GithubButton from "./GithubButton";

interface LoginCardProps {
  onLogin: () => void;
  loading: boolean;
}

const LoginCard: React.FC<LoginCardProps> = ({ onLogin, loading }) => {
  return (
    <div className="login-card">
      <h1 className="login-title">Welcome to Build Sage</h1>
      <p className="login-subtitle">Sign in to get your API key and manage your repositories</p>
      
      <GithubButton onClick={onLogin} loading={loading} />
    </div>
  );
};

export default LoginCard;
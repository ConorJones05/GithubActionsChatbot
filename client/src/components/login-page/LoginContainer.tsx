import React from 'react';
import LoginCard from './LoginCard';

interface LoginContainerProps {
  onLogin: () => void;
  loading: boolean;
}

const LoginContainer: React.FC<LoginContainerProps> = ({ onLogin, loading }) => {
  console.log('LoginContainer rendering, loading state:', loading);
  
  return (
    <div className="login-container">
      <LoginCard onLogin={onLogin} loading={loading} />
    </div>
  );
};

export default LoginContainer;
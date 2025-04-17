import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../utils/supabaseClient';
import { useAuth } from '../context/AuthContext';
import LoginContainer from './login-page/LoginContainer';
import './LoginPage.css';

function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      console.log('User already logged in, redirecting to /api-key');
      navigate('/api-key');
    }
  }, [user, navigate]);

  const handleLogin = async () => {
    try {
      console.log('Login button clicked');
      setLoading(true);
      setError(null);

      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'github',
        options: {
          redirectTo: `${window.location.origin}/api-key`,
        },
      });

      if (error) {
        console.error('Login error:', error);
        setError(error.message);
        return;
      }

      console.log('Login initiated, redirecting to GitHub:', data);
    } catch (err) {
      console.error('Unexpected error during login:', err);
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <LoginContainer onLogin={handleLogin} loading={loading} />
      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default LoginPage;
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
      setLoading(true);
      setError(null);

      const redirectUrl = `${window.location.origin}`;
      console.log('Using redirect URL:', redirectUrl);

      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'github',
        options: {
          redirectTo: redirectUrl,
          scopes: 'read:user user:email repo',
        }
      });

      if (error) {
        console.error('Login error:', error);
        setError(error.message);
      }
    } catch (err) {
      console.error('Unexpected error:', err);
      setError('An unexpected error occurred');
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
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
    const handleAuthRedirect = async () => {
      if (window.location.hash && window.location.hash.includes('access_token=')) {
        console.log('Detected access token in URL');
        const { data } = await supabase.auth.getSession();
        if (data.session) {
          console.log('Session established, redirecting to API key page');
          navigate('/api-key');
        }
      }
    };

    handleAuthRedirect();

    if (user) {
      console.log('User already logged in, redirecting to /api-key');
      navigate('/api-key');
    }
  }, [user, navigate]);

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError(null);

      const redirectUrl = process.env.NODE_ENV === 'production'
        ? 'https://buildsage-sooty.vercel.app'
        : `${window.location.origin}`;
      
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
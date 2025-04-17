import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../utils/supabaseClient';

const AuthRedirectHandler: React.FC = () => {
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleRedirect = async () => {
      try {
        if (window.location.hash && window.location.hash.includes('access_token=')) {
          console.log('Processing auth redirect...');
          
          const { data, error: sessionError } = await supabase.auth.getSession();
          
          if (sessionError) {
            console.error('Error getting session:', sessionError);
            setError('Failed to log in. Please try again.');
            return;
          }

          if (data.session) {
            console.log('Authentication successful, redirecting to API key page');
            
            if (window.history && window.history.replaceState) {
              window.history.replaceState({}, document.title, window.location.pathname);
            }
            
            navigate('/api-key');
          }
        }
      } catch (err) {
        console.error('Error processing auth redirect:', err);
        setError('An error occurred during login. Please try again.');
      }
    };

    handleRedirect();
  }, [navigate]);

  if (error) {
    return (
      <div className="error-container">
        <div className="error-message">{error}</div>
        <button 
          className="primary-button" 
          onClick={() => navigate('/login')}
        >
          Return to Login
        </button>
      </div>
    );
  }

  return (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <p>Processing your login...</p>
    </div>
  );
};

export default AuthRedirectHandler;
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../utils/supabaseClient";
import { useAuth } from "../context/AuthContext";
import LoginContainer from "./login-page/LoginContainer";
import "./LoginPage.css";

function LoginPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();
  
  useEffect(() => {
    if (user) {
      navigate('/api-key');
    }
  }, [user, navigate]);

  const handleGithubLogin = async () => {
    try {
      setLoading(true);
      
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'github',
        options: {
          redirectTo: window.location.origin,
          scopes: 'read:user'
        }
      });

      if (error) {
        throw error;
      }
    } catch (error) {
      console.error("Error logging in with GitHub:", error);
      alert("Failed to login with GitHub");
      setLoading(false);
    }
  };

  return <LoginContainer onLogin={handleGithubLogin} loading={loading} />;
}

export default LoginPage;
import React, { createContext, useContext, useEffect, useState } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '../utils/supabaseClient';
import { useNavigate } from 'react-router-dom';

type AuthContextType = {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const handleRedirectState = async () => {
      if (window.location.hash && window.location.hash.includes('access_token')) {
        console.log("Detected access_token in URL, processing OAuth redirect");
        
        const { data, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error("Error processing auth redirect:", error);
        } else if (data.session) {
          console.log("Successfully processed redirect, session established");
          setSession(data.session);
          setUser(data.session.user);
          
          window.location.hash = '#/api-key';
          return true; 
        }
      }
      return false; 
    };

    const getSession = async () => {
      const handledRedirect = await handleRedirectState();
      if (handledRedirect) return; 
      
      const { data } = await supabase.auth.getSession();
      setSession(data.session);
      setUser(data.session?.user ?? null);
      
      const isLoginPage = window.location.hash === '#/login' || window.location.hash === '';
      
      if (data.session && isLoginPage) {
        console.log("User is logged in and on login page, redirecting to api-key");
        navigate('/api-key');
      }
      
      setLoading(false);
    };

    getSession();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      console.log("Auth state changed:", _event, session?.user?.id);
      setSession(session);
      setUser(session?.user ?? null);
      
      const isLoginPage = window.location.hash === '#/login' || window.location.hash === '';
      
      if (session && isLoginPage) {
        console.log("Auth change detected, redirecting to api-key");
        navigate('/api-key');
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  const signOut = async () => {
    await supabase.auth.signOut();
    navigate('/login');
  };

  return (
    <AuthContext.Provider value={{ session, user, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
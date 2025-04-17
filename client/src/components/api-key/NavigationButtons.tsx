import React from 'react';
import { useNavigate } from 'react-router-dom';

interface NavigationButtonsProps {
  onSignOut: () => Promise<void>;
}

const NavigationButtons: React.FC<NavigationButtonsProps> = ({ onSignOut }) => {
  const navigate = useNavigate();
  
  const handleSignOut = async () => {
    try {
      await onSignOut();
      navigate('/login');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };
  
  return (
    <div className="nav-buttons">
      <button 
        className="nav-button primary-button"
        onClick={() => navigate("/repos")}
      >
        View Recommendations
      </button>
      
      <button 
        className="nav-button secondary-button"
        onClick={handleSignOut}
      >
        Sign Out
      </button>
    </div>
  );
};

export default NavigationButtons;
import React from 'react';
import { useNavigate } from 'react-router-dom';

interface NavigationButtonsProps {
  onSignOut: () => void;
}

const NavigationButtons: React.FC<NavigationButtonsProps> = ({ onSignOut }) => {
  const navigate = useNavigate();
  
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
        onClick={onSignOut}
      >
        Sign Out
      </button>
    </div>
  );
};

export default NavigationButtons;
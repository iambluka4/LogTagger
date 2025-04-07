import React from 'react';
import { useServices } from '../context/ServicesContext';
import './OfflineBanner.css';

function OfflineBanner() {
  const { servicesStatus, toggleOfflineMode } = useServices();
  
  if (!servicesStatus.isOfflineMode) {
    return null;
  }
  
  return (
    <div className="offline-banner">
      <div className="offline-message">
        <span className="offline-icon">⚠️</span>
        <span>
          Працюєте в офлайн-режимі. Деякі функції обмежені.
        </span>
      </div>
      <button 
        className="retry-connection-btn"
        onClick={() => toggleOfflineMode(false)}
      >
        Спробувати знову
      </button>
    </div>
  );
}

export default OfflineBanner;

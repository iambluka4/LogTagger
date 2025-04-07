import React from 'react';
import { useDemoMode } from '../contexts/DemoModeContext';
import './DemoModeIndicator.css';

function DemoModeIndicator() {
  const { demoModeEnabled } = useDemoMode();

  if (!demoModeEnabled) return null;

  return (
    <div className="demo-mode-indicator">
      <i className="demo-icon">⚠️</i>
      DEMO MODE
    </div>
  );
}

export default DemoModeIndicator;

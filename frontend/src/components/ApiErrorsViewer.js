import React, { useState, useEffect } from 'react';
import './ApiErrorsViewer.css';

function ApiErrorsViewer() {
  const [errors, setErrors] = useState([]);
  const [collapsed, setCollapsed] = useState(true);
  
  // Обробник для прослуховування помилок API
  useEffect(() => {
    const errorHandler = (event) => {
      if (event.detail && event.detail.type === 'api-error') {
        setErrors(prevErrors => [event.detail.error, ...prevErrors].slice(0, 20));
      }
    };
    
    window.addEventListener('api-error', errorHandler);
    
    return () => {
      window.removeEventListener('api-error', errorHandler);
    };
  }, []);
  
  // Очищення всіх помилок
  const clearErrors = () => {
    setErrors([]);
  };
  
  // Перемикання стану згортання
  const toggleCollapsed = () => {
    setCollapsed(!collapsed);
  };
  
  if (errors.length === 0) return null;
  
  return (
    <div className={`api-errors-viewer ${collapsed ? 'api-errors-collapsed' : ''}`}>
      <div className="api-errors-header">
        <h3>API Errors ({errors.length})</h3>
        <div>
          <button className="api-errors-toggle-btn" onClick={toggleCollapsed}>
            {collapsed ? '▲' : '▼'}
          </button>
          <button className="clear-errors-btn" onClick={clearErrors}>Clear All</button>
        </div>
      </div>
      
      <div className="api-errors-content">
        {errors.length === 0 ? (
          <div className="no-errors-message">No recent API errors</div>
        ) : (
          <table className="api-errors-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>URL</th>
                <th>Status</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {errors.map((error, index) => (
                <tr key={index}>
                  <td>{new Date(error.timestamp).toLocaleTimeString()}</td>
                  <td>{error.url}</td>
                  <td>{error.status || 'N/A'}</td>
                  <td>{error.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default ApiErrorsViewer;

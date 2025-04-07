import React, { useState } from 'react';
import { testConnection } from '../services/api';
import './ConnectionTest.css';

function ConnectionTest({ onClose }) {
  const [connectionType, setConnectionType] = useState('ml');
  const [apiUrl, setApiUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const connectionData = {
        connection_type: connectionType,
        api_url: apiUrl,
        api_key: apiKey
      };
      
      const response = await testConnection(connectionData);
      setResult(response.data);
    } catch (error) {
      setError('Error testing connection: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="connection-test-dialog">
      <div className="connection-test-content">
        <div className="connection-test-header">
          <h3>Test Connection</h3>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>
        
        <form className="connection-test-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Connection Type:</label>
            <select 
              value={connectionType} 
              onChange={(e) => setConnectionType(e.target.value)}
            >
              <option value="ml">ML Service</option>
              <option value="wazuh">Wazuh SIEM</option>
              <option value="splunk">Splunk SIEM</option>
              <option value="elastic">Elastic SIEM</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>API URL:</label>
            <input 
              type="text" 
              value={apiUrl} 
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="Enter API URL"
              required
            />
          </div>
          
          <div className="form-group">
            <label>API Key:</label>
            <input 
              type="password" 
              value={apiKey} 
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter API Key"
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="test-button" 
            disabled={loading}
          >
            {loading ? 'Testing...' : 'Test Connection'}
          </button>
        </form>
        
        {error && (
          <div className="connection-error">
            {error}
          </div>
        )}
        
        {result && (
          <div className="connection-test-results">
            <h4>Test Results:</h4>
            <div className={`result-status ${result.success ? 'success' : 'error'}`}>
              <span className={`status-dot ${result.success ? 'success' : 'error'}`}></span>
              {result.success ? 'Connection Successful' : 'Connection Failed'}
            </div>
            
            <div className="result-details">
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ConnectionTest;

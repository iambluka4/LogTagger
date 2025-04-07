import React, { useState, useEffect } from 'react';
import { 
  getMLStatus, 
  getMLMetrics, 
  getUnverifiedEvents, 
  verifyEventLabel,
  updateMLMetrics,
  checkServicesHealth as checkServicesHealthApi
} from '../services/api';
import { Link } from 'react-router-dom';
import './MLDashboard.css';

function MLDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mlStatus, setMLStatus] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [unverifiedEvents, setUnverifiedEvents] = useState([]);
  const [currentEvent, setCurrentEvent] = useState(null);
  const [verificationData, setVerificationData] = useState({
    true_positive: null,
    attack_type: '',
    mitre_tactic: '',
    mitre_technique: '',
    verification_comment: ''
  });

  // Додаємо новий стан для відстеження здоров'я сервісів
  const [servicesHealth, setServicesHealth] = useState({
    ml: { status: 'unknown' },
    siem: { status: 'unknown' }
  });

  useEffect(() => {
    loadMLData();
  }, []);

  const loadMLData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Завантаження статусу ML
      const statusResponse = await getMLStatus();
      setMLStatus(statusResponse.data);
      
      // Якщо ML вимкнено, не намагаємося завантажувати дані
      if (statusResponse.data.status === 'disabled') {
        setMetrics([]);
        setUnverifiedEvents([]);
        setLoading(false);
        return;
      }
      
      // Завантаження метрик тільки якщо ML активний
      if (statusResponse.data.status === 'active') {
        try {
          const metricsResponse = await getMLMetrics();
          setMetrics(metricsResponse.data.metrics || []);
        } catch (metricsError) {
          console.error('Error loading metrics:', metricsError);
          // Не зупиняємо весь процес, якщо метрики недоступні
        }
        
        try {
          // Завантаження неперевірених подій
          const eventsResponse = await getUnverifiedEvents();
          setUnverifiedEvents(eventsResponse.data.events || []);
        } catch (eventsError) {
          console.error('Error loading unverified events:', eventsError);
          // Продовжуємо виконання навіть при помилці завантаження подій
        }
      }
    } catch (error) {
      setError('Error loading ML data: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateMetrics = async () => {
    try {
      setLoading(true);
      
      // Додаємо індикатор прогресу для довгих операцій
      const updateStartTime = new Date();
      const updateInProgress = setInterval(() => {
        const elapsedSeconds = Math.floor((new Date() - updateStartTime) / 1000);
        console.log(`Metrics update in progress: ${elapsedSeconds}s`);
      }, 1000);
      
      const response = await updateMLMetrics();
      
      clearInterval(updateInProgress);
      
      if (response.data.success) {
        if ("Notification" in window && Notification.permission === "granted") {
          new Notification("Metrics Updated", {
            body: "ML performance metrics were successfully updated"
          });
        } else {
          alert('Metrics updated successfully');
        }
        
        // Оновлюємо дані після успішного оновлення метрик
        loadMLData();
      } else {
        alert('Error updating metrics: ' + response.data.message);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message;
      setError('Error updating metrics: ' + errorMsg);
      console.error('Update metrics error details:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleViewEvent = (event) => {
    setCurrentEvent(event);
    setVerificationData({
      true_positive: event.true_positive,
      attack_type: event.attack_type || '',
      mitre_tactic: event.mitre_tactic || '',
      mitre_technique: event.mitre_technique || '',
      verification_comment: ''
    });
  };
  
  const handleVerificationChange = (e) => {
    const { name, value } = e.target;
    setVerificationData(prev => ({
      ...prev,
      [name]: name === 'true_positive' ? value === 'true' : value
    }));
  };
  
  const handleVerify = async () => {
    try {
      setLoading(true);
      
      const response = await verifyEventLabel(currentEvent.id, verificationData);
      
      if (response.data.success) {
        // Створюємо копію масиву щоб уникнути мутації стану
        const updatedEvents = unverifiedEvents.filter(e => e.id !== currentEvent.id);
        setUnverifiedEvents(updatedEvents);
        setCurrentEvent(null);
        
        showNotification("Event verified", "Event was successfully verified");
      } else {
        showNotification("Verification Error", 'Error verifying event: ' + response.data.message);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message;
      setError('Error verifying event: ' + errorMsg);
      console.error('Verification error details:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Додаємо функцію для перевірки стану сервісів
  const checkServicesHealth = async () => {
    try {
      const response = await checkServicesHealthApi();
      setServicesHealth(response.data);
    } catch (error) {
      console.error('Error checking services health:', error);
      setError('Error checking services health: ' + (error.response?.data?.message || error.message));
    }
  };

  // Викликаємо перевірку здоров'я сервісів при завантаженні
  useEffect(() => {
    checkServicesHealth();
    // Встановлюємо інтервал для періодичної перевірки стану сервісів (кожні 5 хвилин)
    const interval = setInterval(checkServicesHealth, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Додаємо виведення повідомлень про нотифікації
  const showNotification = (title, body) => {
    // Спочатку перевіряємо дозволи
    if (!("Notification" in window)) {
      alert(body);
      return;
    }
    // Якщо дозволи вже надані
    if (Notification.permission === "granted") {
      new Notification(title, { body });
    } 
    // Якщо дозволи не заборонені, запитуємо їх
    else if (Notification.permission !== "denied") {
      Notification.requestPermission().then(permission => {
        if (permission === "granted") {
          new Notification(title, { body });
        } else {
          alert(body);
        }
      });
    } else {
      // Якщо нотифікації заборонені, використовуємо alert
      alert(body);
    }
  };

  // Рендерінг метрик
  const renderMetrics = () => {
    if (!metrics || metrics.length === 0) {
      return <p>No metrics available</p>;
    }
    const latestMetric = metrics[0]; // Найсвіжіша метрика
    return (
      <div className="metrics-container">
        <div className="metrics-summary">
          <div className="metric-card">
            <h4>Precision</h4>
            <div className="metric-value">{(latestMetric.precision * 100).toFixed(2)}%</div>
          </div>
          <div className="metric-card">
            <h4>Recall</h4>
            <div className="metric-value">{(latestMetric.recall * 100).toFixed(2)}%</div>
          </div>
          <div className="metric-card">
            <h4>F1 Score</h4>
            <div className="metric-value">{(latestMetric.f1_score * 100).toFixed(2)}%</div>
          </div>
        </div>
        <div className="metrics-detail">
          <h4>Confusion Matrix</h4>
          <div className="confusion-matrix">
            <div className="matrix-row">
              <div className="matrix-cell header">Predicted Positive</div>
              <div className="matrix-cell header">Predicted Negative</div>
            </div>
            <div className="matrix-row">
              <div className="matrix-cell header">Actual Positive</div>
              <div className="matrix-cell value tp">{latestMetric.true_positives}</div>
              <div className="matrix-cell value fn">{latestMetric.false_negatives}</div>
            </div>
            <div className="matrix-row">
              <div className="matrix-cell header">Actual Negative</div>
              <div className="matrix-cell value fp">{latestMetric.false_positives}</div>
              <div className="matrix-cell value tn">{latestMetric.true_negatives}</div>
            </div>
          </div>
        </div>
        {latestMetric.class_metrics && Object.keys(latestMetric.class_metrics).length > 0 && (
          <div className="class-metrics">
            <h4>Performance by Attack Type</h4>
            <table className="class-metrics-table">
              <thead>
                <tr>
                  <th>Attack Type</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1 Score</th>
                  <th>Support</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(latestMetric.class_metrics).map(([type, metrics]) => (
                  <tr key={type}>
                    <td>{type}</td>
                    <td>{(metrics.precision * 100).toFixed(2)}%</td>
                    <td>{(metrics.recall * 100).toFixed(2)}%</td>
                    <td>{(metrics.f1_score * 100).toFixed(2)}%</td>
                    <td>{metrics.support}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  // Рендерінг інформації про ML-модель
  const renderModelInfo = () => {
    if (!mlStatus || !mlStatus.model_info) {
      return <p>No model information available</p>;
    }
    const modelInfo = mlStatus.model_info;
    return (
      <div className="model-info">
        <h4>ML Model Information</h4>
        <table className="model-info-table">
          <tbody>
            <tr>
              <td>Name:</td>
              <td>{modelInfo.name || 'Unknown'}</td>
            </tr>
            <tr>
              <td>Version:</td>
              <td>{modelInfo.version || 'Unknown'}</td>
            </tr>
            <tr>
              <td>Type:</td>
              <td>{modelInfo.type || 'Unknown'}</td>
            </tr>
            <tr>
              <td>Created:</td>
              <td>{modelInfo.created_at ? new Date(modelInfo.created_at).toLocaleString() : 'Unknown'}</td>
            </tr>
            <tr>
              <td>Description:</td>
              <td>{modelInfo.description || 'No description available'}</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  };

  // Рендерінг форми верифікації
  const renderVerificationForm = () => {
    if (!currentEvent) {
      return (
        <div className="verification-placeholder">
          <p>Select an event from the list to verify</p>
        </div>
      );
    }
    const attackTypes = [
      "SQL Injection", "Cross-Site Scripting", "Denial of Service", 
      "Brute Force", "Phishing", "Malware", "Ransomware", "Data Exfiltration", 
      "Reconnaissance", "Lateral Movement", "Command and Control"
    ];
    const mitreTactics = [
      "Initial Access", "Execution", "Persistence", "Privilege Escalation",
      "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement",
      "Collection", "Command and Control", "Exfiltration", "Impact"
    ];
    // Спрощені техніки для обраної тактики
    const mitreMapping = {
      "Initial Access": ["Phishing", "Valid Accounts", "External Remote Services"],
      "Execution": ["Command Line Interface", "Scripting", "Windows Management Instrumentation"],
      "Persistence": ["Registry Run Keys", "Scheduled Task", "Create Account"],
      "Privilege Escalation": ["Access Token Manipulation", "Bypass User Account Control", "Sudo and Sudo Caching"],
      "Defense Evasion": ["Disable Security Tools", "Obfuscated Files", "Rootkit"],
      "Credential Access": ["Brute Force", "Credential Dumping", "Keylogging"],
      "Discovery": ["Account Discovery", "Network Service Scanning", "System Information Discovery"],
      "Lateral Movement": ["Remote Services", "Internal Spearphishing", "Pass the Hash"],
      "Collection": ["Audio Capture", "Data from Local System", "Screen Capture"],
      "Command and Control": ["Remote Access Software", "Web Service", "Standard Application Layer Protocol"],
      "Exfiltration": ["Data Transfer Size Limits", "Exfiltration Over Alternative Protocol", "Scheduled Transfer"],
      "Impact": ["Data Destruction", "Service Stop", "System Shutdown/Reboot"]
    };
    return (
      <div className="verification-form">
        <h3>Verify ML Classification</h3>
        <div className="event-summary">
          <p><strong>Event ID:</strong> {currentEvent.event_id}</p>
          <p><strong>Source IP:</strong> {currentEvent.source_ip}</p>
          <p><strong>Severity:</strong> <span className={`severity-badge ${currentEvent.severity}`}>{currentEvent.severity}</span></p>
          <p><strong>ML Confidence:</strong> {(currentEvent.ml_confidence * 100).toFixed(2)}%</p>
        </div>
        <div className="ml-classification">
          <h4>ML Classification Result</h4>
          <p><strong>True Positive:</strong> {currentEvent.true_positive ? 'Yes' : 'No'}</p>
          <p><strong>Attack Type:</strong> {currentEvent.attack_type || 'Not classified'}</p>
          <p><strong>MITRE Tactic:</strong> {currentEvent.mitre_tactic || 'Not classified'}</p>
          <p><strong>MITRE Technique:</strong> {currentEvent.mitre_technique || 'Not classified'}</p>
        </div>
        <form onSubmit={(e) => { e.preventDefault(); handleVerify(); }}>
          <div className="form-group">
            <label>Is this a true positive?</label>
            <div className="radio-group">
              <label>
                <input
                  type="radio"
                  name="true_positive"
                  value="true"
                  checked={verificationData.true_positive === true}
                  onChange={handleVerificationChange}
                />
                Yes
              </label>
              <label>
                <input
                  type="radio"
                  name="true_positive"
                  value="false"
                  checked={verificationData.true_positive === false}
                  onChange={handleVerificationChange}
                />
                No
              </label>
            </div>
          </div>
          <div className="form-group">
            <label>Attack Type:</label>
            <select
              name="attack_type"
              value={verificationData.attack_type}
              onChange={handleVerificationChange}
            >
              <option value="">Select Attack Type</option>
              {attackTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>MITRE ATT&CK Tactic:</label>
            <select
              name="mitre_tactic"
              value={verificationData.mitre_tactic}
              onChange={handleVerificationChange}
            >
              <option value="">Select MITRE Tactic</option>
              {mitreTactics.map(tactic => (
                <option key={tactic} value={tactic}>{tactic}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>MITRE ATT&CK Technique:</label>
            <select
              name="mitre_technique"
              value={verificationData.mitre_technique}
              onChange={handleVerificationChange}
              disabled={!verificationData.mitre_tactic}
            >
              <option value="">Select MITRE Technique</option>
              {verificationData.mitre_tactic && mitreMapping[verificationData.mitre_tactic] && 
                mitreMapping[verificationData.mitre_tactic].map(technique => (
                  <option key={technique} value={technique}>{technique}</option>
                ))
              }
            </select>
          </div>
          <div className="form-group">
            <label>Verification Comment:</label>
            <textarea
              name="verification_comment"
              value={verificationData.verification_comment}
              onChange={handleVerificationChange}
              placeholder="Enter your comment about this classification"
              rows={3}
            />
          </div>
          <button type="submit" className="verify-btn" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify Classification'}
          </button>
        </form>
      </div>
    );
  };

  // Додаємо відображення стану сервісів
  const renderServicesHealth = () => {
    return (
      <div className="services-health">
        <h4>Services Status</h4>
        <div className="services-grid">
          <div className={`service-card ${servicesHealth.ml.status}`}>
            <h5>ML Service</h5>
            <div className="status-badge">{servicesHealth.ml.status}</div>
            {servicesHealth.ml.message && (
              <div className="status-message">{servicesHealth.ml.message}</div>
            )}
          </div>
          <div className={`service-card ${servicesHealth.siem.status}`}>
            <h5>SIEM Integration</h5>
            <div className="status-badge">{servicesHealth.siem.status}</div>
            {servicesHealth.siem.wazuh && (
              <div className="integration-item">Wazuh: {servicesHealth.siem.wazuh.status}</div>
            )}
            {servicesHealth.siem.splunk && (
              <div className="integration-item">Splunk: {servicesHealth.siem.splunk.status}</div>
            )}
            {servicesHealth.siem.elastic && (
              <div className="integration-item">Elastic: {servicesHealth.siem.elastic.status}</div>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (loading && !mlStatus) {
    return <div className="loading">Loading ML Dashboard...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  // ML не активований
  if (mlStatus && mlStatus.status === 'disabled') {
    return (
      <div className="ml-dashboard">
        <h2>ML Dashboard</h2>
        <div className="ml-disabled-message">
          <p>Machine Learning classification is currently disabled in system settings.</p>
          <p>Go to <Link to="/config" className="config-link">System Configuration</Link> to enable ML classification.</p>
        </div>
        {renderServicesHealth()}
      </div>
    );
  }

  return (
    <div className="ml-dashboard">
      <h2>ML Dashboard</h2>
      {/* Відображення стану сервісів */}
      {renderServicesHealth()}
      {/* ML Status інформація */}
      <div className="ml-status">
        <div className={`status-indicator ${mlStatus?.status || 'error'}`}>
          <span className="status-dot"></span>
          <span className="status-text">
            ML Status: {mlStatus?.status === 'active' ? 'Active' : 'Error'}
          </span>
        </div>
        <div className="status-message">
          {mlStatus?.message || 'ML service status unknown'}
        </div>
        <button 
          className="update-metrics-btn" 
          onClick={handleUpdateMetrics}
          disabled={loading}
        >
          {loading ? 'Updating...' : 'Update Performance Metrics'}
        </button>
      </div>
      {/* ML Model Information */}
      <div className="dashboard-section">
        <h3>Model Information</h3>
        {renderModelInfo()}
      </div>
      {/* ML Performance Metrics */}
      <div className="dashboard-section">
        <h3>Performance Metrics</h3>
        {renderMetrics()}
      </div>
      {/* Verification Section */}
      <div className="dashboard-section verification-section">
        <h3>Verification</h3>
        <div className="verification-layout">
          {/* Events List */}
          <div className="unverified-events">
            <h4>Unverified Events ({unverifiedEvents.length})</h4>
            {unverifiedEvents.length === 0 ? (
              <p className="no-events-message">No unverified events found</p>
            ) : (
              <div className="events-list">
                {unverifiedEvents.map(event => (
                  <div 
                    key={event.id} 
                    className={`event-item ${currentEvent && currentEvent.id === event.id ? 'selected' : ''}`}
                    onClick={() => handleViewEvent(event)}
                  >
                    <div className="event-header">
                      <span className={`severity-badge ${event.severity}`}>{event.severity}</span>
                      <span className="event-timestamp">{new Date(event.timestamp).toLocaleString()}</span>
                    </div>
                    <div className="event-source">{event.source_ip}</div>
                    <div className="event-ml-info">
                      <span>Type: {event.attack_type || 'Unknown'}</span>
                      <span>Confidence: {(event.ml_confidence * 100).toFixed(2)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          {/* Verification Form */}
          <div className="verification-container">
            {renderVerificationForm()}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MLDashboard;
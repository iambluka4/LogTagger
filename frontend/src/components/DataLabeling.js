import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types'; 
import { getEvents, getEvent, labelEvent, fetchEvents as fetchSIEMEvents, getApiConfig, verifyEventLabels } from '../services/api';
import './DataLabeling.css';
import AutoLabelsVerifier from './AutoLabelsVerifier';

function DataLabeling({ demoMode }) {
  const [events, setEvents] = useState([]);
  const [currentEvent, setCurrentEvent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    severity: '',
    source_ip: '',
    siem_source: '',
    manual_review: '',
    page: 1
  });
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 0
  });
  const [labelFormData, setLabelFormData] = useState({
    true_positive: null,
    attack_type: '',
    mitre_tactic: '',
    mitre_technique: '',
    manual_tags: [] // Changed from string to array
  });
  const [tagInput, setTagInput] = useState('');
  const [fetchingLogs, setFetchingLogs] = useState(false);
  const [fetchSuccess, setFetchSuccess] = useState(null);
  const [mlSuggestions, setMlSuggestions] = useState({
    attack_type: '',
    mitre_tactic: '',
    mitre_technique: '',
    confidence: 0,
    ml_tags: []
  });

  // Attack types and MITRE options for select dropdowns
  const attackTypes = [
    "Brute Force", "SQL Injection", "Cross-Site Scripting", "Denial of Service", 
    "Phishing", "Malware", "Ransomware", "Data Exfiltration", "Privilege Escalation",
    "Reconnaissance", "Lateral Movement", "Command and Control"
  ];

  const mitreTactics = [
    "Initial Access", "Execution", "Persistence", "Privilege Escalation",
    "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement",
    "Collection", "Command and Control", "Exfiltration", "Impact"
  ];

  // Simplified techniques for demo purposes
  const mitreTechniques = {
    "Initial Access": ["Phishing", "Valid Accounts", "External Remote Services"],
    "Execution": ["Command Line Interface", "Scripting", "Windows Management Instrumentation"],
    "Persistence": ["Registry Run Keys", "Scheduled Task", "Create Account"],
    "Privilege Escalation": ["Access Token Manipulation", "Bypass User Account Control", "Sudo and Sudo Caching"],
    "Defense Evasion": ["Disable Security Tools", "Obfuscated Files", "Rootkit"],
    "Credential Access": ["Brute Force", "Credential Dumping", "Keylogging"],
    "Discovery": ["Account Discovery", "Network Service Scanning", "System Information Discovery"],
    "Lateral Movement": ["Remote Services", "Internal Spearphishing", "Pass the Hash"],
    "Collection": ["Data from Local System", "Email Collection", "Screen Capture"],
    "Command and Control": ["Encrypted Channel", "Web Service", "Remote Access Tools"],
    "Exfiltration": ["Data Transfer Size Limits", "Exfiltration Over C2", "Scheduled Transfer"],
    "Impact": ["Data Destruction", "Service Stop", "Endpoint Denial of Service"]
  };

  // Винесення fetchData за межі useEffect для повторного використання
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Prepare query params
      const queryParams = { 
        ...filters,
        page_size: pagination.pageSize
      };
      
      // Remove empty filter values
      Object.keys(queryParams).forEach(key => {
        if (queryParams[key] === '') {
          delete queryParams[key];
        }
      });
      
      const response = await getEvents(queryParams);
      
      setEvents(response.data.events);
      setPagination({
        page: response.data.page,
        pageSize: response.data.page_size,
        totalCount: response.data.total_count,
        totalPages: response.data.total_pages
      });
    } catch (error) {
      setError('Error fetching events: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const queryParams = { 
          ...filters,
          page_size: pagination.pageSize
        };
        
        Object.keys(queryParams).forEach(key => {
          if (queryParams[key] === '') {
            delete queryParams[key];
          }
        });
        
        const response = await getEvents(queryParams);
        
        if (isMounted) {
          setEvents(response.data.events);
          setPagination({
            page: response.data.page,
            pageSize: response.data.page_size,
            totalCount: response.data.total_count,
            totalPages: response.data.total_pages
          });
        }
      } catch (error) {
        if (isMounted) {
          setError('Error fetching events: ' + (error.response?.data?.message || error.message));
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    
    loadData();
    
    return () => {
      isMounted = false;
    };
  }, [filters, pagination.pageSize]);

  // Валідація форми маркування
  const validateLabelForm = () => {
    const errors = {};
    
    // Валідація attack_type
    if (labelFormData.attack_type && !attackTypes.includes(labelFormData.attack_type)) {
      errors.attack_type = "Invalid attack type selected";
    }
    
    // Валідація mitre_tactic
    if (labelFormData.mitre_tactic && !mitreTactics.includes(labelFormData.mitre_tactic)) {
      errors.mitre_tactic = "Invalid MITRE tactic selected";
    }
    
    // Валідація mitre_technique
    if (labelFormData.mitre_technique && labelFormData.mitre_tactic && 
        (!mitreTechniques[labelFormData.mitre_tactic] || 
         !mitreTechniques[labelFormData.mitre_tactic].includes(labelFormData.mitre_technique))) {
      errors.mitre_technique = "Invalid MITRE technique for selected tactic";
    }
    
    // Валідація manual_tags
    if (labelFormData.manual_tags.some(tag => tag.length > 50)) {
      errors.manual_tags = "Tag length should not exceed 50 characters";
    }
    
    return {
      isValid: Object.keys(errors).length === 0,
      errors
    };
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters({
      ...filters,
      [name]: value,
      page: 1 // Reset to first page when filters change
    });
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    fetchData();
  };

  const handleViewEvent = async (eventId) => {
    try {
      setLoading(true);
      setError(null);
      const response = await getEvent(eventId);
      setCurrentEvent(response.data);
      
      // Pre-fill the label form with existing data
      setLabelFormData({
        true_positive: response.data.true_positive,
        attack_type: response.data.attack_type || '',
        mitre_tactic: response.data.mitre_tactic || '',
        mitre_technique: response.data.mitre_technique || '',
        manual_tags: Array.isArray(response.data.manual_tags) ? response.data.manual_tags : []
      });

      // Встановлюємо форму мітками з події
      const labels = response.data.labels || {};
      
      // Отримуємо ML мітки, якщо доступні
      const mlLabels = labels.ml_labels || {};
      setMlSuggestions({
        attack_type: mlLabels.attack_type || '',
        mitre_tactic: mlLabels.mitre_tactic || '',
        mitre_technique: mlLabels.mitre_technique || '',
        confidence: mlLabels.confidence || 0,
        ml_tags: mlLabels.tags || []
      });
      
      // Встановлюємо ручні мітки
      setLabelFormData({
        true_positive: labels.true_positive !== undefined ? labels.true_positive : null,
        attack_type: labels.attack_type || '',
        mitre_tactic: labels.mitre_tactic || '',
        mitre_technique: labels.mitre_technique || '',
        manual_tags: labels.manual_tags || []
      });
    } catch (error) {
      setError('Error fetching event details: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleLabelSubmit = async (e) => {
    e.preventDefault();
    
    if (!currentEvent) return;
    
    // Додаємо валідацію
    const { isValid, errors } = validateLabelForm();
    if (!isValid) {
      setNotification({
        type: 'error',
        message: 'Validation error: ' + Object.values(errors).join(', ')
      });
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      await labelEvent(currentEvent.id, labelFormData);
      
      // Отримуємо актуальні дані з сервера замість локального оновлення
      const response = await getEvent(currentEvent.id);
      setCurrentEvent(response.data);
      
      // Оновлюємо подію у списку також з даними з сервера
      setEvents(events.map(event => 
        event.id === currentEvent.id ? response.data : event
      ));
      
      // Показуємо повідомлення про успіх через компонент сповіщень
      setNotification({
        type: 'success',
        message: 'Event labeled successfully'
      });
    } catch (error) {
      setError('Error labeling event: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleLabelChange = (e) => {
    const { name, value } = e.target;
    
    // Special handling for true_positive boolean
    if (name === 'true_positive') {
      setLabelFormData({
        ...labelFormData,
        true_positive: value === 'true'
      });
    } else {
      setLabelFormData({
        ...labelFormData,
        [name]: value
      });
    }
  };

  const handleAddTag = () => {
    const trimmedTag = tagInput.trim();
    if (trimmedTag === '') return;
    
    // Add the tag if it doesn't already exist
    if (!labelFormData.manual_tags.includes(trimmedTag)) {
      setLabelFormData({
        ...labelFormData,
        manual_tags: [...labelFormData.manual_tags, trimmedTag]
      });
    }
    setTagInput('');
  };

  const handleRemoveTag = (tag) => {
    setLabelFormData({
      ...labelFormData,
      manual_tags: labelFormData.manual_tags.filter(t => t !== tag)
    });
  };

  const handleTacticChange = (e) => {
    const tactic = e.target.value;
    setLabelFormData({
      ...labelFormData,
      mitre_tactic: tactic,
      mitre_technique: '' // Reset technique when tactic changes
    });
  };
  
  const handleFetchSIEMLogs = async (siemType) => {
    // Якщо активовано демо-режим, використовуємо демо-дані замість справжніх API
    if (demoMode) {
      try {
        setFetchingLogs(true);
        const response = await fetchSIEMEvents({ 
          siem_type: siemType,
          num_events: 10 // Генеруємо 10 демо-подій
        });
        
        setFetchSuccess({
          success: true,
          message: `Згенеровано ${response.data.new_logs} нових демонстраційних подій`
        });
        
        // Оновлюємо список подій
        fetchData();
      } catch (error) {
        setFetchSuccess({
          success: false,
          message: `Помилка при генерації демо-подій: ${error.message}`
        });
      } finally {
        setFetchingLogs(false);
      }
      return;
    }
    
    // Перевірка наявності конфігурації перед запитом до API
    try {
      // Спочатку отримуємо поточні налаштування API
      setFetchingLogs(true);
      setFetchSuccess(null);
      
      const configResponse = await getApiConfig();
      const config = configResponse.data;
      
      // Перевірка наявності необхідних налаштувань для вибраного SIEM
      let missingConfig = false;
      let configMessage = "";
      
      if (siemType === 'wazuh' && (!config.wazuh_api_url || !config.wazuh_api_key)) {
        missingConfig = true;
        configMessage = "Wazuh API не налаштовано. Перейдіть до розділу API Configuration для налаштування.";
      } else if (siemType === 'splunk' && (!config.splunk_api_url || !config.splunk_api_key)) {
        missingConfig = true;
        configMessage = "Splunk API не налаштовано. Перейдіть до розділу API Configuration для налаштування.";
      } else if (siemType === 'elastic' && (!config.elastic_api_url || !config.elastic_api_key)) {
        missingConfig = true;
        configMessage = "Elastic API не налаштовано. Перейдіть до розділу API Configuration для налаштування.";
      }
      
      if (missingConfig) {
        setFetchSuccess({
          success: false,
          message: configMessage,
          missingConfig: true
        });
        setFetchingLogs(false);
        return;
      }
      
      // Якщо конфігурація є, продовжуємо з запитом
      const response = await fetchSIEMEvents({ siem_type: siemType });
      
      setFetchSuccess({
        success: true,
        message: `Successfully fetched ${response.data.new_logs} new logs from ${siemType}`
      });
      
      // Refresh the events list
      fetchData();
    } catch (error) {
      let errorMessage = 'Failed to fetch logs';
      
      // Покращена обробка помилок з сервера
      if (error.response) {
        if (error.response.data.error === "No SIEM settings configured") {
          errorMessage = `${siemType} API не налаштовано. Перейдіть до розділу API Configuration для налаштування.`;
        } else if (error.response.data.error === `${siemType} API not configured`) {
          errorMessage = `${siemType} API не налаштовано правильно. Переконайтесь, що ви ввели URL та ключ API.`;
        } else {
          errorMessage = error.response.data.error || errorMessage;
        }
      } else if (error.request) {
        errorMessage = "Не вдалося з'єднатися з сервером. Переконайтеся, що сервер працює.";
      }
      
      setFetchSuccess({
        success: false,
        message: errorMessage
      });
    } finally {
      setFetchingLogs(false);
    }
  };

  // Додаємо обробник для верифікації міток
  const handleVerifyLabels = async (eventId, verifiedLabels) => {
    try {
      setLoading(true);
      setError(null);
      await verifyEventLabels(eventId, verifiedLabels);
      
      // Оновлюємо дані події
      handleViewEvent(eventId);
      
      alert('Labels verified successfully');
    } catch (error) {
      setError('Error verifying labels: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  // Properly fixed formatTimestamp function
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp).toLocaleString();
    } catch (e) {
      console.error("Invalid timestamp format:", e);
      return timestamp;
    }
  };

  // Додайте функцію для прийняття ML пропозицій
  const acceptMlSuggestion = (field) => {
    setLabelFormData({
      ...labelFormData,
      [field]: mlSuggestions[field]
    });
  };

  // Додаємо кастомний компонент сповіщень замість alert
  const Notification = ({ type, message, onClose }) => (
    <div className={`notification ${type}`}>
      <div className="notification-message">{message}</div>
      <button className="notification-close" onClick={onClose}>×</button>
    </div>
  );

  // Додаємо стан для сповіщень
  const [notification, setNotification] = useState(null);

  return (
    <div className="data-labeling-container">
      <h2>Data Labeling</h2>
      
      {notification && (
        <Notification 
          type={notification.type} 
          message={notification.message} 
          onClose={() => setNotification(null)} 
        />
      )}
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      {demoMode && (
        <div className="demo-notice">
          <p>Ви працюєте в демонстраційному режимі. Всі дані є синтетичними і використовуються тільки для демонстрації можливостей системи.</p>
          <p>Для роботи з реальними даними, <a href="/api-config">налаштуйте підключення до SIEM</a>.</p>
        </div>
      )}
      
      {fetchSuccess && (
        <div className={`fetch-result ${fetchSuccess.success ? 'success' : 'error'}`}>
          <div className="fetch-message">{fetchSuccess.message}</div>
          
          {/* Додаємо кнопку для швидкого переходу до налаштувань */}
          {fetchSuccess.missingConfig && !demoMode && (
            <button 
              className="setup-config-btn"
              onClick={() => window.location.href = '/api-config'}
            >
              Налаштувати API
            </button>
          )}
        </div>
      )}
      
      <div className="fetch-controls">
        <h3>{demoMode ? 'Генерація демо-даних' : 'Fetch New Logs'}</h3>
        <div className="fetch-buttons">
          <button 
            onClick={() => handleFetchSIEMLogs('wazuh')}
            disabled={fetchingLogs}
            className="fetch-btn"
          >
            {fetchingLogs ? 'Fetching...' : demoMode ? 'Згенерувати демо-дані' : 'Fetch from Wazuh'}
          </button>
          
          {!demoMode && (
            <>
              <button 
                onClick={() => handleFetchSIEMLogs('splunk')}
                disabled={fetchingLogs}
                className="fetch-btn"
              >
                {fetchingLogs ? 'Fetching...' : 'Fetch from Splunk'}
              </button>
              
              <button 
                onClick={() => handleFetchSIEMLogs('elastic')}
                disabled={fetchingLogs}
                className="fetch-btn"
              >
                {fetchingLogs ? 'Fetching...' : 'Fetch from Elastic'}
              </button>
            </>
          )}
        </div>
      </div>
      
      <div className="data-labeling-layout">
        {/* Left side: Filters and Events List */}
        <div className="events-panel">
          <div className="filters-section">
            <h3>Filters</h3>
            <form onSubmit={handleFilterSubmit}>
              <div className="form-group">
                <label>Severity:</label>
                <select
                  name="severity"
                  value={filters.severity}
                  onChange={handleFilterChange}
                >
                  <option value="">All</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Source IP:</label>
                <input
                  type="text"
                  name="source_ip"
                  value={filters.source_ip}
                  onChange={handleFilterChange}
                  placeholder="Filter by source IP"
                />
              </div>
              
              <div className="form-group">
                <label>SIEM Source:</label>
                <select
                  name="siem_source"
                  value={filters.siem_source}
                  onChange={handleFilterChange}
                >
                  <option value="">All</option>
                  <option value="wazuh">Wazuh</option>
                  <option value="splunk">Splunk</option>
                  <option value="elastic">Elastic</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Reviewed:</label>
                <select
                  name="manual_review"
                  value={filters.manual_review}
                  onChange={handleFilterChange}
                >
                  <option value="">All</option>
                  <option value="true">Reviewed</option>
                  <option value="false">Not Reviewed</option>
                </select>
              </div>
              
              <button type="submit" className="filter-btn" disabled={loading}>
                Apply Filters
              </button>
            </form>
          </div>
          
          <div className="events-list">
            <h3>Security Events</h3>
            {loading && <p className="loading-text">Loading events...</p>}
            {events.length === 0 && !loading ? (
              <p className="no-events">No events found matching your criteria</p>
            ) : (
              <table className="events-table">
                <thead>
                  <tr>
                    <th>Severity</th>
                    <th>Source IP</th>
                    <th>Timestamp</th>
                    <th>Review Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map(event => (
                    <tr 
                      key={event.id} 
                      onClick={() => handleViewEvent(event.id)}
                      className={currentEvent && currentEvent.id === event.id ? 'selected' : ''}
                    >
                      <td>
                        <span className={`severity-badge ${event.severity}`}>
                          {event.severity}
                        </span>
                      </td>
                      <td>{event.source_ip || 'N/A'}</td>
                      <td>{formatTimestamp(event.timestamp)}</td>
                      <td>
                        <span className={`review-status ${event.manual_review ? 'reviewed' : 'not-reviewed'}`}>
                          {event.manual_review ? 'Reviewed' : 'Not Reviewed'}
                        </span>
                      </td>
                      <td>
                        <button 
                          onClick={() => handleViewEvent(event.id)}
                          className="view-btn"
                        >
                          View & Label
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            
            {/* Pagination Controls */}
            <div className="pagination">
              <button 
                disabled={pagination.page === 1 || loading} 
                onClick={() => setFilters({...filters, page: pagination.page - 1})}
                className="pagination-btn"
              >
                Previous
              </button>
              <span className="page-info">
                Page {pagination.page} of {pagination.totalPages || 1}
              </span>
              <button 
                disabled={pagination.page === pagination.totalPages || pagination.totalPages === 0 || loading}
                onClick={() => setFilters({...filters, page: pagination.page + 1})}
                className="pagination-btn"
              >
                Next
              </button>
            </div>
          </div>
        </div>
        
        {/* Right side: Event Details and Labeling */}
        <div className="event-details-panel">
          {currentEvent ? (
            <div className="event-details">
              <h3>Event Details</h3>
              
              <div className="event-header">
                <div className="event-id">
                  <strong>ID:</strong> {currentEvent.event_id}
                </div>
                <span className={`severity-badge ${currentEvent.severity}`}>
                  {currentEvent.severity}
                </span>
              </div>
              
              <div className="detail-group">
                <strong>Source IP:</strong> {currentEvent.source_ip || 'N/A'}
              </div>
              
              <div className="detail-group">
                <strong>Timestamp:</strong> {formatTimestamp(currentEvent.timestamp)}
              </div>
              
              <div className="detail-group">
                <strong>SIEM Source:</strong> {currentEvent.siem_source}
              </div>
              
              {currentEvent.alert_data && (
                <div className="detail-group">
                  <strong>Related Alert:</strong> {currentEvent.alert_data.rule_name}
                  <div className="alert-details">
                    <span>Severity: {currentEvent.alert_data.severity}</span>
                    <span>Time: {formatTimestamp(currentEvent.alert_data.timestamp)}</span>
                  </div>
                </div>
              )}
              
              {currentEvent.labels && typeof currentEvent.labels === 'object' && Object.keys(currentEvent.labels).length > 0 && (
                <div className="detail-group">
                  <strong>Auto Labels:</strong>
                  <div className="auto-labels">
                    {Object.entries(currentEvent.labels).map(([key, value]) => (
                      <span key={key} className="auto-label">
                        {key}: {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="raw-log-section">
                <h4>Raw Log Data</h4>
                {currentEvent.raw_logs && currentEvent.raw_logs.length > 0 ? (
                  <pre className="raw-log">
                    {JSON.stringify(currentEvent.raw_logs[0].raw_log, null, 2)}
                  </pre>
                ) : (
                  <div className="no-raw-log">No raw log data available</div>
                )}
              </div>
              
              {/* Додаємо компонент верифікації автоматичних міток */}
              {currentEvent.labels && typeof currentEvent.labels === 'object' && 
               Object.keys(currentEvent.labels).length > 0 && (
                <AutoLabelsVerifier 
                  labels={currentEvent.labels} 
                  eventId={currentEvent.id}
                  onVerify={handleVerifyLabels}
                />
              )}
              
              <div className="labeling-form">
                <h4>Label This Event</h4>
                <form onSubmit={handleLabelSubmit}>
                  <div className="form-group">
                    <label>Is this a true positive?</label>
                    <div className="radio-group">
                      <label>
                        <input
                          type="radio"
                          name="true_positive"
                          value="true"
                          checked={labelFormData.true_positive === true}
                          onChange={handleLabelChange}
                        />
                        Yes
                      </label>
                      <label>
                        <input
                          type="radio"
                          name="true_positive"
                          value="false"
                          checked={labelFormData.true_positive === false}
                          onChange={handleLabelChange}
                        />
                        No
                      </label>
                    </div>
                  </div>
                  
                  <div className="form-group">
                    <label>Attack Type:</label>
                    <select
                      name="attack_type"
                      value={labelFormData.attack_type}
                      onChange={handleLabelChange}
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
                      value={labelFormData.mitre_tactic}
                      onChange={handleTacticChange}
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
                      value={labelFormData.mitre_technique}
                      onChange={handleLabelChange}
                      disabled={!labelFormData.mitre_tactic}
                    >
                      <option value="">Select MITRE Technique</option>
                      {labelFormData.mitre_tactic && mitreTechniques[labelFormData.mitre_tactic] && 
                       mitreTechniques[labelFormData.mitre_tactic].map(technique => (
                        <option key={technique} value={technique}>{technique}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Manual Tags:</label>
                    <div className="tags-input">
                      <input
                        type="text"
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        placeholder="Add a tag"
                      />
                      <button 
                        type="button" 
                        onClick={handleAddTag}
                        className="add-tag-btn"
                      >
                        Add
                      </button>
                    </div>
                    
                    <div className="tags-list">
                      {labelFormData.manual_tags.map(tag => (
                        <div key={tag} className="tag">
                          {tag}
                          <button 
                            type="button" 
                            onClick={() => handleRemoveTag(tag)}
                            className="remove-tag-btn"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <button 
                    type="submit" 
                    className="submit-btn"
                    disabled={loading}
                  >
                    {loading ? 'Saving...' : 'Save Labels'}
                  </button>
                </form>
              </div>

              {/* Додаємо до UI секцію для відображення ML пропозицій */}
              {mlSuggestions.attack_type || mlSuggestions.mitre_tactic || mlSuggestions.ml_tags.length > 0 ? (
                <div className="ml-suggestions">
                  <h4>ML Recommendations</h4>
                  
                  {mlSuggestions.confidence > 0 && (
                    <div className="confidence-indicator">
                      <label>Confidence:</label>
                      <div className="confidence-bar">
                        <div 
                          className="confidence-level" 
                          style={{width: `${mlSuggestions.confidence}%`}}
                        ></div>
                      </div>
                      <span>{mlSuggestions.confidence}%</span>
                    </div>
                  )}
                  
                  {mlSuggestions.attack_type && (
                    <div className="suggestion-item">
                      <span>Attack Type: <strong>{mlSuggestions.attack_type}</strong></span>
                      <button 
                        type="button" 
                        onClick={() => acceptMlSuggestion('attack_type')}
                        className="accept-suggestion-btn"
                      >
                        Accept
                      </button>
                    </div>
                  )}
                  
                  {mlSuggestions.mitre_tactic && (
                    <div className="suggestion-item">
                      <span>MITRE Tactic: <strong>{mlSuggestions.mitre_tactic}</strong></span>
                      <button 
                        type="button" 
                        onClick={() => acceptMlSuggestion('mitre_tactic')}
                        className="accept-suggestion-btn"
                      >
                        Accept
                      </button>
                    </div>
                  )}
                  
                  {mlSuggestions.ml_tags.length > 0 && (
                    <div className="suggestion-item">
                      <span>Suggested Tags:</span>
                      <div className="suggestion-tags">
                        {mlSuggestions.ml_tags.map(tag => (
                          <div key={tag} className="suggestion-tag">
                            {tag}
                            <button 
                              type="button" 
                              onClick={() => {
                                if (!labelFormData.manual_tags.includes(tag)) {
                                  setLabelFormData({
                                    ...labelFormData,
                                    manual_tags: [...labelFormData.manual_tags, tag]
                                  });
                                }
                              }}
                              className="accept-tag-btn"
                            >
                              +
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          ) : (
            <div className="no-event-selected">
              <p>Select an event from the list to view details and add labels.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Додаємо валідацію props
DataLabeling.propTypes = {
  demoMode: PropTypes.bool
};

DataLabeling.defaultProps = {
  demoMode: false
};

export default DataLabeling;

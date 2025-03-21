import React, { useState, useEffect } from 'react';
import { getEvents, getEvent, labelEvent, fetchEvents as fetchSIEMEvents } from '../services/api';
import './DataLabeling.css';

function DataLabeling() {
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
    manual_tags: []
  });
  const [tagInput, setTagInput] = useState('');
  const [fetchingLogs, setFetchingLogs] = useState(false);
  const [fetchSuccess, setFetchSuccess] = useState(null);

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

  useEffect(() => {
    fetchEvents();
  }, [filters.page]);

  const fetchEvents = async () => {
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
    fetchEvents();
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
        manual_tags: response.data.manual_tags || []
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
    
    try {
      setLoading(true);
      setError(null);
      await labelEvent(currentEvent.id, labelFormData);
      
      // Update current event with new labels
      setCurrentEvent({
        ...currentEvent,
        ...labelFormData,
        manual_review: true
      });
      
      // Update the event in the list
      setEvents(events.map(event => {
        if (event.id === currentEvent.id) {
          return {
            ...event,
            ...labelFormData,
            manual_review: true
          };
        }
        return event;
      }));
      
      alert('Event labeled successfully');
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
    if (tagInput.trim() === '') return;
    
    // Add the tag if it doesn't already exist
    if (!labelFormData.manual_tags.includes(tagInput.trim())) {
      setLabelFormData({
        ...labelFormData,
        manual_tags: [...labelFormData.manual_tags, tagInput.trim()]
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
    try {
      setFetchingLogs(true);
      setFetchSuccess(null);
      
      const response = await fetchSIEMEvents({ siem_type: siemType });
      
      setFetchSuccess({
        success: true,
        message: `Successfully fetched ${response.data.new_logs} new logs from ${siemType}`
      });
      
      // Refresh the events list
      fetchEvents();
    } catch (error) {
      setFetchSuccess({
        success: false,
        message: 'Failed to fetch logs: ' + (error.response?.data?.message || error.message)
      });
    } finally {
      setFetchingLogs(false);
    }
  };

  return (
    <div className="data-labeling-container">
      <h2>Data Labeling</h2>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      {fetchSuccess && (
        <div className={`fetch-result ${fetchSuccess.success ? 'success' : 'error'}`}>
          {fetchSuccess.message}
        </div>
      )}
      
      <div className="fetch-controls">
        <h3>Fetch New Logs</h3>
        <div className="fetch-buttons">
          <button 
            onClick={() => handleFetchSIEMLogs('wazuh')}
            disabled={fetchingLogs}
            className="fetch-btn"
          >
            {fetchingLogs ? 'Fetching...' : 'Fetch from Wazuh'}
          </button>
          
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
                      className={currentEvent && currentEvent.id === event.id ? 'selected' : ''}
                    >
                      <td>
                        <span className={`severity-badge ${event.severity}`}>
                          {event.severity}
                        </span>
                      </td>
                      <td>{event.source_ip || 'N/A'}</td>
                      <td>{new Date(event.timestamp).toLocaleString()}</td>
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
                <strong>Timestamp:</strong> {new Date(currentEvent.timestamp).toLocaleString()}
              </div>
              
              <div className="detail-group">
                <strong>SIEM Source:</strong> {currentEvent.siem_source}
              </div>
              
              {currentEvent.labels && Object.keys(currentEvent.labels).length > 0 && (
                <div className="detail-group">
                  <strong>Auto Labels:</strong>
                  <div className="auto-labels">
                    {Object.entries(currentEvent.labels).map(([key, value]) => (
                      <span key={key} className="auto-label">
                        {key}: {value.toString()}
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

export default DataLabeling;

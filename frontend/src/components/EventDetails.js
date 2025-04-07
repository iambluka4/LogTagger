import React, { useState, useEffect } from "react";
import { getEvent } from "../services/api";
import "./EventDetails.css";

function EventDetails({ eventId }) {
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rawLogs, setRawLogs] = useState([]);

  useEffect(() => {
    if (eventId) {
      fetchEventDetails(eventId);
    }
  }, [eventId]);

  const fetchEventDetails = async (id) => {
    try {
      setLoading(true);
      setError(null);
      const response = await getEvent(id);
      setEvent(response.data);

      // Use the new has_raw_logs flag to determine if we need to fetch raw logs
      if (response.data.has_raw_logs) {
        // If raw logs aren't already included, we can fetch them separately
        // but in this case they're already in the response
        if (response.data.raw_logs) {
          setRawLogs(response.data.raw_logs);
        }
      }
    } catch (error) {
      setError(
        "Error fetching event details: " +
          (error.response?.data?.message || error.message),
      );
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return "N/A";
    try {
      return new Date(timestamp).toLocaleString();
    } catch (e) {
      console.error("Invalid timestamp format:", e);
      return timestamp;
    }
  };

  if (loading) {
    return <div className="loading">Loading event details...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!event) {
    return <div className="no-event">No event selected</div>;
  }

  return (
    <div className="event-details-container">
      <h2>Event Details</h2>

      <div className="event-header">
        <div className="event-id">
          <strong>ID:</strong> {event.event_id}
        </div>
        <span className={`severity-badge ${event.severity}`}>
          {event.severity}
        </span>
      </div>

      <div className="details-section">
        <div className="detail-group">
          <strong>Source IP:</strong> {event.source_ip || "N/A"}
        </div>

        <div className="detail-group">
          <strong>Timestamp:</strong> {formatTimestamp(event.timestamp)}
        </div>

        <div className="detail-group">
          <strong>SIEM Source:</strong> {event.siem_source}
        </div>

        {event.alert_data && (
          <div className="detail-group">
            <strong>Related Alert:</strong> {event.alert_data.rule_name}
            <div className="alert-details">
              <span>Severity: {event.alert_data.severity}</span>
              <span>Time: {formatTimestamp(event.alert_data.timestamp)}</span>
            </div>
          </div>
        )}
      </div>

      {/* Display event labels */}
      {!event.labels && event.true_positive !== undefined && (
        <div className="labels-section">
          <h3>Event Labels</h3>

          <div className="detail-group">
            <strong>True Positive:</strong>{" "}
            {event.true_positive === null
              ? "Not Evaluated"
              : event.true_positive
                ? "Yes"
                : "No"}
          </div>

          {event.attack_type && (
            <div className="detail-group">
              <strong>Attack Type:</strong> {event.attack_type}
            </div>
          )}

          {event.mitre_tactic && (
            <div className="detail-group">
              <strong>MITRE Tactic:</strong> {event.mitre_tactic}
            </div>
          )}

          {event.mitre_technique && (
            <div className="detail-group">
              <strong>MITRE Technique:</strong> {event.mitre_technique}
            </div>
          )}

          {event.manual_tags && event.manual_tags.length > 0 && (
            <div className="detail-group">
              <strong>Manual Tags:</strong>
              <div className="tags-list">
                {event.manual_tags.map((tag, index) => (
                  <span key={index} className="tag">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Display raw logs if available */}
      {event.has_raw_logs && (
        <div className="raw-log-section">
          <h3>Raw Log Data</h3>
          {rawLogs.length > 0 ? (
            <div className="raw-logs">
              {rawLogs.map((log, index) => (
                <pre key={index} className="raw-log">
                  {JSON.stringify(log.raw_log, null, 2)}
                </pre>
              ))}
            </div>
          ) : (
            <p>Loading raw logs...</p>
          )}
        </div>
      )}

      {!event.has_raw_logs && (
        <div className="no-raw-logs">
          <p>No raw logs available for this event.</p>
        </div>
      )}

      {/* Improved labels display */}
      {event.labels && (
        <div className="event-labels">
          <h3>Event Labels</h3>
          
          <div className="labels-grid">
            {/* True/False Positive */}
            <div className="label-group">
              <h4>Classification</h4>
              {event.labels.true_positive === true && (
                <div className="true-positive">True Positive</div>
              )}
              {event.labels.true_positive === false && (
                <div className="false-positive">False Positive</div>
              )}
              {(event.labels.true_positive === null || event.labels.true_positive === undefined) && (
                <div className="unclassified">Not Classified</div>
              )}
            </div>
            
            {/* Attack Type */}
            {event.labels.attack_type && (
              <div className="label-group">
                <h4>Attack Type</h4>
                <div className="attack-type">{event.labels.attack_type}</div>
              </div>
            )}
            
            {/* MITRE ATT&CK */}
            {(event.labels.mitre_tactic || event.labels.mitre_technique) && (
              <div className="label-group">
                <h4>MITRE ATT&CK</h4>
                {event.labels.mitre_tactic && (
                  <div className="mitre-item">
                    <span className="mitre-label">Tactic:</span> 
                    <span className="mitre-value">{event.labels.mitre_tactic}</span>
                  </div>
                )}
                {event.labels.mitre_technique && (
                  <div className="mitre-item">
                    <span className="mitre-label">Technique:</span> 
                    <span className="mitre-value">{event.labels.mitre_technique}</span>
                  </div>
                )}
              </div>
            )}
            
            {/* Manual Tags */}
            {event.labels.manual_tags && event.labels.manual_tags.length > 0 && (
              <div className="label-group">
                <h4>Manual Tags</h4>
                <div className="tags-container">
                  {Array.isArray(event.labels.manual_tags) 
                    ? event.labels.manual_tags.map((tag, index) => (
                        <span key={index} className="tag manual-tag">{tag}</span>
                      ))
                    : typeof event.labels.manual_tags === 'string' && event.labels.manual_tags.split(',').map((tag, index) => (
                        <span key={index} className="tag manual-tag">{tag.trim()}</span>
                      ))
                  }
                </div>
              </div>
            )}
            
            {/* ML Tags if available */}
            {event.labels.ml_labels && (
              <div className="label-group ml-labels">
                <h4>ML Suggestions</h4>
                
                {event.labels.ml_labels.confidence && (
                  <div className="confidence-indicator">
                    <span>Confidence: {event.labels.ml_labels.confidence}%</span>
                    <div className="confidence-bar">
                      <div 
                        className="confidence-level" 
                        style={{width: `${event.labels.ml_labels.confidence}%`}}
                      ></div>
                    </div>
                  </div>
                )}
                
                {event.labels.ml_labels.attack_type && (
                  <div className="ml-item">
                    <span className="ml-label">Attack Type:</span> 
                    <span className="ml-value">{event.labels.ml_labels.attack_type}</span>
                  </div>
                )}
                
                {event.labels.ml_labels.tags && event.labels.ml_labels.tags.length > 0 && (
                  <div className="ml-tags">
                    <span className="ml-label">Suggested Tags:</span>
                    <div className="tags-container">
                      {event.labels.ml_labels.tags.map((tag, index) => (
                        <span key={index} className="tag ml-tag">{tag}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default EventDetails;

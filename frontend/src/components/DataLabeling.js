import React, { useEffect, useState } from 'react';
import { getAlerts, labelAlert } from '../services/api';

function DataLabeling() {
  const [alerts, setAlerts] = useState([]);
  const [selectedAlertId, setSelectedAlertId] = useState(null);
  const [labelData, setLabelData] = useState({
    detected_rule: '',
    true_positive: false,
    event_chain_id: '',
    attack_type: '',
    manual_tag: '',
    event_severity: ''
  });

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await getAlerts();
      setAlerts(response.data);
    } catch (error) {
      console.log('Error fetching alerts:', error);
    }
  };

  const handleLabelSubmit = async () => {
    if (!selectedAlertId) return;
    try {
      await labelAlert(selectedAlertId, labelData);
      alert('Label added successfully');
      // Очищення форми
      setLabelData({
        detected_rule: '',
        true_positive: false,
        event_chain_id: '',
        attack_type: '',
        manual_tag: '',
        event_severity: ''
      });
      // Оновити список
      fetchAlerts();
    } catch (error) {
      console.log('Error labeling alert:', error);
    }
  };

  return (
    <div>
      <h2>Data Labeling</h2>
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ width: '300px' }}>
          <h4>Alerts</h4>
          <ul>
            {alerts.map(alert => (
              <li key={alert.alert_id}>
                <button onClick={() => {
                  setSelectedAlertId(alert.alert_id);
                  // Заповнити поля для зручності
                  setLabelData(prev => ({
                    ...prev,
                    detected_rule: alert.rule_name || '',
                    event_severity: alert.severity || ''
                  }));
                }}>
                  {alert.rule_name} (ID: {alert.alert_id})
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div style={{ width: '400px' }}>
          <h4>Label Form</h4>
          {selectedAlertId ? (
            <div>
              <p>Selected Alert ID: {selectedAlertId}</p>
              <label>Detected Rule:</label><br/>
              <input 
                type="text"
                value={labelData.detected_rule}
                onChange={e => setLabelData({...labelData, detected_rule: e.target.value})}
              /><br/>

              <label>True Positive:</label><br/>
              <input 
                type="checkbox"
                checked={labelData.true_positive}
                onChange={e => setLabelData({...labelData, true_positive: e.target.checked})}
              /><br/>

              <label>Event Chain ID:</label><br/>
              <input 
                type="text"
                value={labelData.event_chain_id}
                onChange={e => setLabelData({...labelData, event_chain_id: e.target.value})}
              /><br/>

              <label>Attack Type:</label><br/>
              <input 
                type="text"
                value={labelData.attack_type}
                onChange={e => setLabelData({...labelData, attack_type: e.target.value})}
              /><br/>

              <label>Manual Tag:</label><br/>
              <input 
                type="text"
                value={labelData.manual_tag}
                onChange={e => setLabelData({...labelData, manual_tag: e.target.value})}
              /><br/>

              <label>Event Severity:</label><br/>
              <input 
                type="text"
                value={labelData.event_severity}
                onChange={e => setLabelData({...labelData, event_severity: e.target.value})}
              /><br/><br/>

              <button onClick={handleLabelSubmit}>Save Label</button>
            </div>
          ) : (
            <p>Select an alert to label</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default DataLabeling;

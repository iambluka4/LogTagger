import React, { useEffect, useState } from 'react';
import { getConfig, updateConfig } from '../services/api';

function ApiConfiguration() {
  const [configData, setConfigData] = useState({
    wazuh_api_url: '',
    wazuh_api_key: ''
  });

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await getConfig();
      if (response.data) {
        setConfigData(response.data);
      }
    } catch (error) {
      console.log('Error fetching config:', error);
    }
  };

  const handleSave = async () => {
    try {
      await updateConfig(configData);
      alert('Config updated successfully');
    } catch (error) {
      console.log('Error updating config:', error);
    }
  };

  return (
    <div>
      <h2>API Configuration</h2>
      <label>Wazuh API URL:</label><br/>
      <input
        type="text"
        value={configData.wazuh_api_url}
        onChange={e => setConfigData({...configData, wazuh_api_url: e.target.value})}
      />
      <br/>
      <label>Wazuh API Key:</label><br/>
      <input
        type="text"
        value={configData.wazuh_api_key}
        onChange={e => setConfigData({...configData, wazuh_api_key: e.target.value})}
      />
      <br/><br/>
      <button onClick={handleSave}>Save</button>
    </div>
  );
}

export default ApiConfiguration;

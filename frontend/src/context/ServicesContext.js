import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API_BASE } from '../services/api';

export const ServicesContext = createContext();

export const useServices = () => useContext(ServicesContext);

export const ServicesProvider = ({ children }) => {
  const [servicesStatus, setServicesStatus] = useState({
    siem: {
      wazuh: { status: 'unknown' },
      splunk: { status: 'unknown' },
      elastic: { status: 'unknown' }
    },
    ml: { status: 'unknown' },
    isAnyServiceOnline: false,
    isOfflineMode: false
  });
  
  const checkServicesStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/services/status`);
      
      const status = response.data;
      const isAnyServiceOnline = 
        status.siem.wazuh.status === 'online' ||
        status.siem.splunk.status === 'online' ||
        status.siem.elastic.status === 'online';
      
      setServicesStatus({
        ...status,
        isAnyServiceOnline,
        isOfflineMode: !isAnyServiceOnline
      });
      
      return status;
    } catch (error) {
      console.error('Error checking services status:', error);
      setServicesStatus(prev => ({
        ...prev,
        isAnyServiceOnline: false,
        isOfflineMode: true
      }));
      return null;
    }
  };
  
  const toggleOfflineMode = (enabled) => {
    setServicesStatus(prev => ({
      ...prev,
      isOfflineMode: enabled !== undefined ? enabled : !prev.isOfflineMode
    }));
  };
  
  useEffect(() => {
    checkServicesStatus();
    const intervalId = setInterval(checkServicesStatus, 120000);
    return () => clearInterval(intervalId);
  }, []);
  
  return (
    <ServicesContext.Provider 
      value={{ 
        servicesStatus, 
        checkServicesStatus, 
        toggleOfflineMode 
      }}
    >
      {children}
    </ServicesContext.Provider>
  );
};

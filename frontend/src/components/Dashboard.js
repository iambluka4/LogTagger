import React, { useEffect, useState } from 'react';
import { getAlerts } from '../services/api';

function Dashboard() {
  const [alerts, setAlerts] = useState([]);

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

  return (
    <div>
      <h2>Dashboard</h2>
      <p>Total Alerts: {alerts.length}</p>
      {/* Можна додати графіки, статистику тощо */}
    </div>
  );
}

export default Dashboard;

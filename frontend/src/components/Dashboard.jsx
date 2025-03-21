import React, { useState, useEffect } from 'react';
import { getDashboardStats } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState({
    events_count: 0,
    alerts_count: 0,
    labels_count: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const response = await getDashboardStats();
        setStats(response.data);
        setError(null);
      } catch (err) {
        setError('Помилка завантаження статистики');
        console.error("Dashboard error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="dashboard">
      <h1>Dashbooard</h1>
      
      {loading && <p>Завантаження...</p>}
      {error && <p className="error">{error}</p>}
      
      {!loading && !error && (
        <div className="stats-container">
          <div className="stat-card">
            <h3>Події</h3>
            <p className="stat-value">{stats.events_count}</p>
          </div>
          <div className="stat-card">
            <h3>Сповіщення</h3>
            <p className="stat-value">{stats.alerts_count}</p>
          </div>
          <div className="stat-card">
            <h3>Мітки</h3>
            <p className="stat-value">{stats.labels_count}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;

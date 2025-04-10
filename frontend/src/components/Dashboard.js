import React, { useState, useEffect } from "react";
import {
  getDashboardStats,
  getTopAttackTypes,
  getEventTimeline,
  getSeverityDistribution,
} from "../services/api";
import "./Dashboard.css";

function Dashboard() {
  const [stats, setStats] = useState({
    total_events: 0,
    events_today: 0,
    labeled_events: 0,
    true_positives: 0,
    siem_sources: []
  });
  
  const [severityData, setSeverityData] = useState({
    low: 0,
    medium: 0,
    high: 0,
    critical: 0
  });
  
  const [topAttacks, setTopAttacks] = useState([]);
  const [timelineData, setTimelineData] = useState([]);
  const [timeRange, setTimeRange] = useState("24hours");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Функція для отримання даних з API з обробкою помилок
  const fetchTimeRangeData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch dashboard statistics
      try {
        const statsResponse = await getDashboardStats({ timeRange });
        setStats(statsResponse.data || {
          total_events: 0,
          events_today: 0,
          labeled_events: 0,
          true_positives: 0,
          siem_sources: []
        });
      } catch (err) {
        console.error("Error fetching dashboard stats:", err);
        // Встановлюємо дефолтні дані, щоб UI не зламався
        setStats({
          total_events: 0,
          events_today: 0,
          labeled_events: 0,
          true_positives: 0,
          siem_sources: []
        });
      }
      
      // Calculate severity data
      try {
        const severityResponse = await getSeverityDistribution({ timeRange });
        setSeverityData(severityResponse.data || {
          low: 0,
          medium: 0,
          high: 0,
          critical: 0
        });
      } catch (err) {
        console.error("Error fetching severity data:", err);
        setSeverityData({
          low: 0,
          medium: 0,
          high: 0,
          critical: 0
        });
      }
      
      // Fetch top attack types
      try {
        const attacksResponse = await getTopAttackTypes({ timeRange, limit: 5 });
        setTopAttacks(attacksResponse.data || []);
      } catch (err) {
        console.error("Error fetching attack types:", err);
        setTopAttacks([]);
      }
      
      // Fetch event timeline data
      try {
        const timelineResponse = await getEventTimeline({ timeRange });
        setTimelineData(timelineResponse.data || []);
      } catch (err) {
        console.error("Error fetching timeline data:", err);
        setTimelineData([]);
      }
      
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      setError('Error fetching dashboard data. SIEM might not be connected.');
    } finally {
      setLoading(false);
    }
  };

  // Викликаємо запит даних при зміні timeRange
  useEffect(() => {
    fetchTimeRangeData();
  }, [timeRange]);

  const handleTimeRangeChange = (e) => {
    setTimeRange(e.target.value);
  };

  if (loading) {
    return <div className="loading">Loading dashboard data...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  return (
    <div className="dashboard-container">
      <h2>Security Events Dashboard</h2>

      {/* Summary Statistics */}
      <div className="stats-cards">
        <div className="stat-card">
          <h3>Total Events</h3>
          <div className="stat-value">{stats.total_events}</div>
        </div>

        <div className="stat-card">
          <h3>Events Today</h3>
          <div className="stat-value">{stats.events_today}</div>
        </div>

        <div className="stat-card">
          <h3>Labeled Events</h3>
          <div className="stat-value">{stats.labeled_events}</div>
          <div className="stat-percentage">
            {stats.total_events > 0
              ? `${Math.round((stats.labeled_events / stats.total_events) * 100)}%`
              : "0%"}
          </div>
        </div>

        <div className="stat-card">
          <h3>True Positives</h3>
          <div className="stat-value">{stats.true_positives}</div>
          <div className="stat-percentage">
            {stats.labeled_events > 0
              ? `${Math.round((stats.true_positives / stats.labeled_events) * 100)}%`
              : "0%"}
          </div>
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="time-range-selector">
        <h3>Time Range</h3>
        <select value={timeRange} onChange={handleTimeRangeChange}>
          <option value="24hours">Last 24 Hours</option>
          <option value="7days">Last 7 Days</option>
          <option value="30days">Last 30 Days</option>
          <option value="90days">Last 90 Days</option>
        </select>
      </div>

      {/* Event Timeline Chart would go here */}
      <div className="chart-container">
        <h3>Event Timeline</h3>
        <div className="chart-placeholder">
          {/* In a real implementation, this would be a chart component */}
          <div className="timeline-chart">
            Timeline chart would be rendered here using a chart library
          </div>
        </div>
      </div>

      {/* Top Attack Types */}
      <div className="data-section">
        <h3>Top Attack Types</h3>
        {topAttacks.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Attack Type</th>
                <th>Count</th>
                <th>Percentage</th>
              </tr>
            </thead>
            <tbody>
              {topAttacks.map((attack, index) => (
                <tr key={index}>
                  <td>{attack.attack_type || "Unclassified"}</td>
                  <td>{attack.count}</td>
                  <td>{attack.percentage}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="no-data">No attack type data available</p>
        )}
      </div>

      {/* Severity Distribution */}
      <div className="data-section">
        <h3>Severity Distribution</h3>
        <div className="severity-bars">
          {Object.entries(severityData).map(([severity, count]) => (
            <div className="severity-item" key={severity}>
              <div className="severity-label">{severity}</div>
              <div className="severity-bar-container">
                <div
                  className={`severity-bar severity-${severity.toLowerCase()}`}
                  style={{ width: `${(count / stats.total_events) * 100}%` }}
                ></div>
              </div>
              <div className="severity-count">{count}</div>
            </div>
          ))}
        </div>
      </div>

      {/* SIEM Source Distribution */}
      <div className="data-section">
        <h3>SIEM Sources</h3>
        <div className="source-distribution">
          {stats.siem_sources && stats.siem_sources.length > 0 ? (
            stats.siem_sources.map((source) => (
              <div className="source-item" key={source.name}>
                <div className="source-name">{source.name}</div>
                <div className="source-count">{source.count} events</div>
              </div>
            ))
          ) : (
            <p className="no-data">No SIEM source data available</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

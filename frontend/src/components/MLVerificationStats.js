import React, { useState, useEffect } from 'react';
import { getMLMetrics } from '../services/api';
import './MLVerificationStats.css';

function MLVerificationStats() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const response = await getMLMetrics();
      setMetrics(response.data);
    } catch (error) {
      setError('Помилка отримання метрик: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Завантаження метрик...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!metrics) return null;

  return (
    <div className="ml-verification-stats">
      <h3>Статистика верифікації ML-моделі</h3>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <h4>Точність класифікації</h4>
          <div className="metric-value">{(metrics.accuracy * 100).toFixed(2)}%</div>
        </div>
        
        <div className="metric-card">
          <h4>Кількість верифікованих подій</h4>
          <div className="metric-value">{metrics.verified_events_count}</div>
        </div>
        
        <div className="metric-card">
          <h4>Прийняті мітки</h4>
          <div className="metric-value">{metrics.accepted_labels_count}</div>
        </div>
        
        <div className="metric-card">
          <h4>Відхилені мітки</h4>
          <div className="metric-value">{metrics.rejected_labels_count}</div>
        </div>
      </div>
      
      <div className="metrics-chart">
        {/* Тут можна додати візуалізацію метрик з використанням бібліотеки візуалізації */}
      </div>
    </div>
  );
}

export default MLVerificationStats;

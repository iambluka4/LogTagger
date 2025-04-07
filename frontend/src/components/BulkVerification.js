import React, { useState } from 'react';
import { verifyEventLabels } from '../services/api';
import './BulkVerification.css';

function BulkVerification({ events, onComplete }) {
  const [selectedEvents, setSelectedEvents] = useState([]);
  const [labelsToVerify, setLabelsToVerify] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Функція для отримання унікальних ключів міток з усіх подій
  const getLabelKeys = () => {
    const keys = new Set();
    events.forEach(event => {
      if (event.labels && typeof event.labels === 'object') {
        Object.keys(event.labels).forEach(key => {
          if (!['id', 'event_id', 'timestamp', 'manual_review', 'meta'].includes(key)) {
            keys.add(key);
          }
        });
      }
    });
    return Array.from(keys);
  };

  const handleToggleEvent = (eventId) => {
    setSelectedEvents(prev => {
      if (prev.includes(eventId)) {
        return prev.filter(id => id !== eventId);
      } else {
        return [...prev, eventId];
      }
    });
  };

  const handleToggleLabel = (labelKey) => {
    setLabelsToVerify(prev => {
      if (prev.includes(labelKey)) {
        return prev.filter(key => key !== labelKey);
      } else {
        return [...prev, labelKey];
      }
    });
  };

  const handleVerify = async (isAccepted) => {
    if (selectedEvents.length === 0 || labelsToVerify.length === 0) {
      setError('Виберіть хоча б одну подію та мітку для верифікації');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Створюємо об'єкт верифікації для кожної мітки
      const verifiedLabels = {};
      labelsToVerify.forEach(key => {
        verifiedLabels[key] = isAccepted;
      });

      // Верифікуємо кожну вибрану подію
      const promises = selectedEvents.map(eventId => 
        verifyEventLabels(eventId, verifiedLabels)
      );

      await Promise.all(promises);
      
      setSuccess(`Успішно ${isAccepted ? 'підтверджено' : 'відхилено'} ${labelsToVerify.length} міток для ${selectedEvents.length} подій`);
      
      // Скидаємо вибір
      setSelectedEvents([]);
      setLabelsToVerify([]);
      
      // Оповіщаємо батьківський компонент про завершення
      if (onComplete) onComplete();
    } catch (error) {
      setError('Помилка масової верифікації: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  const labelKeys = getLabelKeys();

  return (
    <div className="bulk-verification">
      <h3>Масова верифікація міток</h3>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      
      <div className="verification-panels">
        <div className="events-selection">
          <h4>Виберіть події для верифікації</h4>
          <div className="selection-controls">
            <button onClick={() => setSelectedEvents(events.map(e => e.id))}>Вибрати всі</button>
            <button onClick={() => setSelectedEvents([])}>Очистити вибір</button>
          </div>
          <div className="events-list">
            {events.map(event => (
              <div 
                key={event.id} 
                className={`event-item ${selectedEvents.includes(event.id) ? 'selected' : ''}`}
                onClick={() => handleToggleEvent(event.id)}
              >
                <input 
                  type="checkbox" 
                  checked={selectedEvents.includes(event.id)} 
                  onChange={() => {}} 
                />
                <span className={`severity-badge ${event.severity}`}>{event.severity}</span>
                <span className="event-source">{event.source_ip}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="labels-selection">
          <h4>Виберіть мітки для верифікації</h4>
          <div className="selection-controls">
            <button onClick={() => setLabelsToVerify(labelKeys)}>Вибрати всі</button>
            <button onClick={() => setLabelsToVerify([])}>Очистити вибір</button>
          </div>
          <div className="labels-list">
            {labelKeys.map(key => (
              <div 
                key={key} 
                className={`label-item ${labelsToVerify.includes(key) ? 'selected' : ''}`}
                onClick={() => handleToggleLabel(key)}
              >
                <input 
                  type="checkbox" 
                  checked={labelsToVerify.includes(key)} 
                  onChange={() => {}} 
                />
                <span className="label-key">{key}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      <div className="verification-actions">
        <button 
          onClick={() => handleVerify(true)} 
          disabled={loading || selectedEvents.length === 0 || labelsToVerify.length === 0}
          className="accept-btn"
        >
          {loading ? 'Обробка...' : 'Підтвердити вибрані мітки'}
        </button>
        <button 
          onClick={() => handleVerify(false)} 
          disabled={loading || selectedEvents.length === 0 || labelsToVerify.length === 0}
          className="reject-btn"
        >
          {loading ? 'Обробка...' : 'Відхилити вибрані мітки'}
        </button>
      </div>
    </div>
  );
}

export default BulkVerification;

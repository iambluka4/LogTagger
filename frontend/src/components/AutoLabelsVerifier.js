import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './AutoLabelsVerifier.css';

function AutoLabelsVerifier({ labels, eventId, onVerify }) {
  const [verifiedLabels, setVerifiedLabels] = useState({});
  const [verifying, setVerifying] = useState(false);

  // Додаємо перевірку на null/undefined
  if (!labels) return null;
  
  // Додаємо дужки для виправлення попередження з оператором
  const hasLabels = (
    (labels.attack_type || labels.mitre_tactic || labels.mitre_technique) || 
    (labels.ml_labels && labels.ml_labels.attack_type)
  );

  if (!hasLabels) return null;

  // Покращуємо перевірку наявності ml_labels
  const mlLabels = labels && labels.ml_labels || {};
  
  // Перевіряємо, чи є ml_labels непорожнім об'єктом
  if (!mlLabels || Object.keys(mlLabels).length === 0) {
    return null;
  }
  
  // Якщо мітки вже верифіковані, показуємо іншу версію компонента
  const isVerified = labels.meta && labels.meta.last_verified_at;
  
  // Функція для генерації класів кнопок - перенесена вище
  const getButtonClass = (type, key) => {
    const baseClass = type === 'accept' ? 'accept-btn' : 'reject-btn';
    const isSelected = type === 'accept' 
      ? verifiedLabels[key] === true 
      : verifiedLabels[key] === false;
    
    return `${baseClass}${isSelected ? ' selected' : ''}`;
  };
  
  const handleAccept = (key) => {
    setVerifiedLabels({
      ...verifiedLabels,
      [key]: true
    });
  };
  
  const handleReject = (key) => {
    setVerifiedLabels({
      ...verifiedLabels,
      [key]: false
    });
  };
  
  const handleSubmitVerification = async () => {
    if (Object.keys(verifiedLabels).length === 0) {
      alert('Виберіть хоча б одну мітку для верифікації');
      return;
    }
    
    setVerifying(true);
    try {
      await onVerify(eventId, verifiedLabels);
      // Очищаємо стан після успішної верифікації
      setVerifiedLabels({});
    } catch (error) {
      console.error('Error verifying labels:', error);
      alert('Помилка при верифікації міток: ' + (error.message || 'Невідома помилка'));
    } finally {
      setVerifying(false);
    }
  };
  
  // Список міток для верифікації (виключаємо службові поля)
  const verifiableLabels = Object.entries(mlLabels).filter(
    ([key]) => !['confidence', 'classified_at', 'tags'].includes(key)
  );
  
  if (verifiableLabels.length === 0) {
    return null;
  }

  return (
    <div className="auto-labels-verifier">
      <h4>Verify ML Labels</h4>
      
      {isVerified ? (
        <div className="verified-info">
          <div className="verified-badge">Verified</div>
          <div className="verified-time">
            Verified at: {new Date(labels.meta.last_verified_at).toLocaleString()}
          </div>
        </div>
      ) : (
        <>
          <div className="verification-list">
            {verifiableLabels.map(([key, value]) => (
              <div key={key} className="verification-item">
                <div className="label-info">
                  <span className="label-key">{key.replace(/_/g, ' ')}:</span>
                  <span className="label-value">
                    {typeof value === 'boolean' 
                      ? (value ? 'True' : 'False')
                      : (value || 'N/A')}
                  </span>
                </div>
                <div className="verification-actions">
                  <button
                    type="button"
                    className={getButtonClass('accept', key)}
                    onClick={() => handleAccept(key)}
                  >
                    Accept
                  </button>
                  <button
                    type="button"
                    className={getButtonClass('reject', key)}
                    onClick={() => handleReject(key)}
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          <button
            type="button"
            className="submit-verification-btn"
            disabled={verifying || Object.keys(verifiedLabels).length === 0}
            onClick={handleSubmitVerification}
          >
            {verifying ? 'Verifying...' : 'Submit Verification'}
          </button>
        </>
      )}
    </div>
  );
}

// Уточнюємо PropTypes для кращої валідації типів
AutoLabelsVerifier.propTypes = {
  labels: PropTypes.shape({
    ml_labels: PropTypes.object,
    meta: PropTypes.shape({
      last_verified_at: PropTypes.string
    })
  }),
  eventId: PropTypes.oneOfType([PropTypes.number, PropTypes.string]).isRequired,
  onVerify: PropTypes.func.isRequired
};

export default AutoLabelsVerifier;

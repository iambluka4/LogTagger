import React, { useState } from "react";
import { updateApiConfig } from "../services/api";
import "./SetupWizard.css";

function SetupWizard({ onComplete, onSkip }) {
  const [step, setStep] = useState(1);
  const [siemType, setSiemType] = useState("");
  const [apiUrl, setApiUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSiemSelect = (type) => {
    setSiemType(type);
    setStep(2);
  };

  const handlePrevious = () => {
    setStep(step - 1);
  };

  const handleSkipSetup = () => {
    // Повідомляємо батьківському компоненту про пропуск налаштувань
    onSkip();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const configData = {};

      if (siemType === "wazuh") {
        configData.wazuh_api_url = apiUrl;
        configData.wazuh_api_key = apiKey;
      } else if (siemType === "splunk") {
        configData.splunk_api_url = apiUrl;
        configData.splunk_api_key = apiKey;
      } else if (siemType === "elastic") {
        configData.elastic_api_url = apiUrl;
        configData.elastic_api_key = apiKey;
      }

      await updateApiConfig(configData);
      setStep(3);
    } catch (error) {
      setError(
        "Failed to save configuration: " +
          (error.response?.data?.message || error.message),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="setup-wizard">
      <div className="setup-wizard-content">
        <h2>Setup Wizard</h2>

        {step === 1 && (
          <div className="wizard-step">
            <h3>Step 1: Select SIEM System</h3>
            <p>Choose the SIEM system you want to connect to:</p>

            <div className="siem-options">
              <button
                className="siem-option"
                onClick={() => handleSiemSelect("wazuh")}
              >
                <div className="siem-icon wazuh-icon">W</div>
                <span>Wazuh</span>
              </button>

              <button
                className="siem-option"
                onClick={() => handleSiemSelect("splunk")}
              >
                <div className="siem-icon splunk-icon">S</div>
                <span>Splunk</span>
              </button>

              <button
                className="siem-option"
                onClick={() => handleSiemSelect("elastic")}
              >
                <div className="siem-icon elastic-icon">E</div>
                <span>Elastic</span>
              </button>
            </div>

            {/* Додано кнопку для пропуску налаштувань */}
            <div className="skip-setup-container">
              <p>Хочете спочатку протестувати систему без підключення SIEM?</p>
              <button className="button-skip" onClick={handleSkipSetup}>
                Пропустити налаштування і використати демо-режим
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="wizard-step">
            <h3>
              Step 2: Configure{" "}
              {siemType.charAt(0).toUpperCase() + siemType.slice(1)} Connection
            </h3>

            {error && <div className="error-message">{error}</div>}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>API URL:</label>
                <input
                  type="text"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder={`Enter ${siemType} API URL`}
                  required
                />
                <small className="form-hint">
                  {siemType === "wazuh"
                    ? "Example: https://wazuh-server:55000"
                    : siemType === "splunk"
                      ? "Example: https://splunk-server:8089"
                      : "Example: https://elastic-server:9200"}
                </small>
              </div>

              <div className="form-group">
                <label>API Key:</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={`Enter ${siemType} API key`}
                  required
                />
                <small className="form-hint">
                  {siemType === "wazuh"
                    ? "Format: user:password (will be base64 encoded)"
                    : siemType === "splunk"
                      ? "Your Splunk API token"
                      : "Your Elastic API key"}
                </small>
              </div>

              <div className="wizard-buttons">
                <button
                  type="button"
                  className="button-secondary"
                  onClick={handlePrevious}
                >
                  Previous
                </button>

                <button
                  type="submit"
                  className="button-primary"
                  disabled={loading}
                >
                  {loading ? "Saving..." : "Save Configuration"}
                </button>
              </div>
            </form>
          </div>
        )}

        {step === 3 && (
          <div className="wizard-step">
            <div className="success-message">
              <h3>Setup Complete!</h3>
              <p>
                Your {siemType.charAt(0).toUpperCase() + siemType.slice(1)}{" "}
                connection has been configured successfully.
              </p>
              <p>You can now start fetching security logs and events.</p>
            </div>

            <div className="wizard-buttons">
              <button className="button-primary" onClick={onComplete}>
                Start Using LogTagger
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SetupWizard;

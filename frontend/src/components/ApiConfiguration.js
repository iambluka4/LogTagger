import React, { useState, useEffect, useCallback } from "react";
import { getApiConfig, updateApiConfig, testConnection } from "../services/api";
import "./ApiConfiguration.css";

function ApiConfiguration() {
  const [configData, setConfigData] = useState({
    wazuh_api_url: "",
    wazuh_api_key: "",
    splunk_api_url: "",
    splunk_api_key: "",
    elastic_api_url: "",
    elastic_api_key: "",
    ml_api_url: "",
    ml_api_key: "",
  });

  const [activeTab, setActiveTab] = useState("wazuh");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Використовуємо useCallback для запобігання повторних створень функції
  const fetchConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      try {
        const response = await getApiConfig();
        console.log("Fetched API configuration:", response.data);

        if (response.data) {
          // Only update fields that exist in the response
          const newConfigData = { ...configData };

          // Process all API configs
          [
            "wazuh_api_url",
            "wazuh_api_key",
            "splunk_api_url",
            "splunk_api_key",
            "elastic_api_url",
            "elastic_api_key",
            "ml_api_url",
            "ml_api_key",
          ].forEach((field) => {
            if (
              response.data[field] !== undefined &&
              response.data[field] !== null
            ) {
              // Don't replace masked API keys ('****') with actual values
              if (field.includes("_api_key") && response.data[field] === "****") {
                // Keep existing value
              } else {
                newConfigData[field] = response.data[field];
              }
            }
          });

          setConfigData(newConfigData);
        }
      } catch (apiError) {
        console.error("API config may not be available yet:", apiError);
        // Залишаємо поточні значення configData
      }
    } catch (error) {
      console.error("Error fetching API config:", error);
      setError(
        "Error fetching config: " +
          (error.response?.data?.message || error.message),
      );
    } finally {
      setLoading(false);
    }
  }, []); // Видаляємо configData з залежностей, щоб уникнути нескінченного циклу

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfigData({
      ...configData,
      [name]: value,
    });

    // Clear status messages when user makes changes
    setError(null);
    setSaveSuccess(false);
    setTestResult(null);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);
      setSaveSuccess(false);
      setTestResult(null);

      console.log("Saving API configuration:", configData);
      await updateApiConfig(configData); // Changed from updateConfig() // This posts to /api/system-config

      setSaveSuccess(true);

      // Refresh the configuration after saving
      await fetchConfig();

      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error("Error saving API config:", error);
      setError(
        "Error updating config: " +
          (error.response?.data?.message || error.message),
      );
    } finally {
      setLoading(false);
    }
  };

  // Enhanced connection test with detailed diagnostics
  const handleTestConnection = async (type) => {
    let testData = {};

    if (type === "wazuh") {
      testData = {
        type: "wazuh",
        api_url: configData.wazuh_api_url,
        api_key: configData.wazuh_api_key,
      };
    } else if (type === "splunk") {
      testData = {
        type: "splunk",
        api_url: configData.splunk_api_url,
        api_key: configData.splunk_api_key,
      };
    } else if (type === "elastic") {
      testData = {
        type: "elastic",
        api_url: configData.elastic_api_url,
        api_key: configData.elastic_api_key,
      };
    } else if (type === "ml_api") {
      testData = {
        type: "ml_api",
        api_url: configData.ml_api_url,
        api_key: configData.ml_api_key,
      };
    }

    try {
      setLoading(true);
      setTestResult(null);
      const response = await testConnection(testData);

      // Enhanced result display with details
      const result = {
        success: response.data.success,
        message: response.data.message,
        details: response.data.details || {},
      };

      setTestResult(result);
      console.log("Connection test result:", result);
    } catch (error) {
      // More detailed error handling
      console.error("Connection test error:", error);

      let errorMessage = "Connection test failed";
      let errorDetails = {};

      if (error.response) {
        // Server responded with an error
        errorMessage = error.response.data.message || errorMessage;
        errorDetails = error.response.data.details || {
          status: error.response.status,
          data: error.response.data,
        };
      } else if (error.request) {
        // Request made but no response received
        errorMessage = "No response from server - check if the API is running";
        errorDetails = { error_type: "network_error" };
      } else {
        // Error in setting up the request
        errorMessage = error.message;
        errorDetails = { error_type: "request_setup_error" };
      }

      setTestResult({
        success: false,
        message: errorMessage,
        details: errorDetails,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="api-config-container">
      <h2>API Configuration</h2>

      {/* Tabs for different integrations */}
      <div className="config-tabs">
        <button
          className={`tab-btn ${activeTab === "wazuh" ? "active" : ""}`}
          onClick={() => setActiveTab("wazuh")}
        >
          Wazuh
        </button>
        <button
          className={`tab-btn ${activeTab === "splunk" ? "active" : ""}`}
          onClick={() => setActiveTab("splunk")}
        >
          Splunk
        </button>
        <button
          className={`tab-btn ${activeTab === "elastic" ? "active" : ""}`}
          onClick={() => setActiveTab("elastic")}
        >
          Elastic
        </button>
        <button
          className={`tab-btn ${activeTab === "ml_api" ? "active" : ""}`}
          onClick={() => setActiveTab("ml_api")}
        >
          ML API
        </button>
      </div>

      {/* Status messages */}
      {error && <div className="error-message">{error}</div>}

      {saveSuccess && (
        <div className="success-message">Configuration saved successfully!</div>
      )}

      {/* Enhanced test result display */}
      {testResult && (
        <div
          className={`test-result ${testResult.success ? "success" : "error"}`}
        >
          <div className="test-message">{testResult.message}</div>

          {/* Display additional details if available */}
          {testResult.details && Object.keys(testResult.details).length > 0 && (
            <div className="test-details">
              <details>
                <summary>Technical Details</summary>
                <div className="details-content">
                  {Object.entries(testResult.details).map(([key, value]) => (
                    <div key={key} className="detail-item">
                      <strong>{key}:</strong>{" "}
                      {typeof value === "object"
                        ? JSON.stringify(value)
                        : value}
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}
        </div>
      )}

      {/* Wazuh Configuration */}
      {activeTab === "wazuh" && (
        <div className="config-section">
          <h3>Wazuh API Configuration</h3>
          <div className="form-group">
            <label>Wazuh API URL:</label>
            <input
              type="text"
              name="wazuh_api_url"
              value={configData.wazuh_api_url || ""}
              onChange={handleChange}
              placeholder="https://wazuh-server:55000"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Wazuh API Key:</label>
            <input
              type="password"
              name="wazuh_api_key"
              value={configData.wazuh_api_key || ""}
              onChange={handleChange}
              placeholder="Enter Wazuh API key"
              disabled={loading}
            />
          </div>

          <button
            onClick={() => handleTestConnection("wazuh")}
            disabled={
              loading || !configData.wazuh_api_url || !configData.wazuh_api_key
            }
            className="test-btn"
          >
            {loading ? "Testing..." : "Test Connection"}
          </button>
        </div>
      )}

      {/* Splunk Configuration */}
      {activeTab === "splunk" && (
        <div className="config-section">
          <h3>Splunk API Configuration</h3>
          <div className="form-group">
            <label>Splunk API URL:</label>
            <input
              type="text"
              name="splunk_api_url"
              value={configData.splunk_api_url || ""}
              onChange={handleChange}
              placeholder="https://splunk-server:8089"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Splunk API Key:</label>
            <input
              type="password"
              name="splunk_api_key"
              value={configData.splunk_api_key || ""}
              onChange={handleChange}
              placeholder="Enter Splunk API key"
              disabled={loading}
            />
          </div>

          <button
            onClick={() => handleTestConnection("splunk")}
            disabled={
              loading ||
              !configData.splunk_api_url ||
              !configData.splunk_api_key
            }
            className="test-btn"
          >
            {loading ? "Testing..." : "Test Connection"}
          </button>
        </div>
      )}

      {/* Elastic Configuration */}
      {activeTab === "elastic" && (
        <div className="config-section">
          <h3>Elastic API Configuration</h3>
          <div className="form-group">
            <label>Elastic API URL:</label>
            <input
              type="text"
              name="elastic_api_url"
              value={configData.elastic_api_url || ""}
              onChange={handleChange}
              placeholder="https://elastic-server:9200"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Elastic API Key:</label>
            <input
              type="password"
              name="elastic_api_key"
              value={configData.elastic_api_key || ""}
              onChange={handleChange}
              placeholder="Enter Elastic API key"
              disabled={loading}
            />
          </div>

          <button
            onClick={() => handleTestConnection("elastic")}
            disabled={
              loading ||
              !configData.elastic_api_url ||
              !configData.elastic_api_key
            }
            className="test-btn"
          >
            {loading ? "Testing..." : "Test Connection"}
          </button>
        </div>
      )}

      {/* ML API Configuration */}
      {activeTab === "ml_api" && (
        <div className="config-section">
          <h3>ML API Configuration</h3>
          <div className="form-group">
            <label>ML API URL:</label>
            <input
              type="text"
              name="ml_api_url"
              value={configData.ml_api_url || ""}
              onChange={handleChange}
              placeholder="https://ml-api-server/api/v1"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>ML API Key:</label>
            <input
              type="password"
              name="ml_api_key"
              value={configData.ml_api_key || ""}
              onChange={handleChange}
              placeholder="Enter ML API key"
              disabled={loading}
            />
          </div>

          <button
            onClick={() => handleTestConnection("ml_api")}
            disabled={
              loading || !configData.ml_api_url || !configData.ml_api_key
            }
            className="test-btn"
          >
            {loading ? "Testing..." : "Test Connection"}
          </button>
        </div>
      )}

      {/* Save button */}
      <div className="actions">
        <button onClick={handleSave} disabled={loading} className="save-btn">
          {loading ? "Saving..." : "Save All Configurations"}
        </button>
      </div>
    </div>
  );
}

export default ApiConfiguration;

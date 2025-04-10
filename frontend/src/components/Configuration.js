import React, { useState, useEffect, useCallback } from "react";
import "./Configuration.css";
import { getConfig, updateConfig } from "../services/api";
import { useDemoMode } from '../context/DemoModeContext';

function Configuration() {
  const { demoModeEnabled, updateDemoMode } = useDemoMode();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [generalSettings, setGeneralSettings] = useState({
    data_retention_days: 90,
    auto_tagging_enabled: true,
    ml_classification_enabled: true,
    refresh_interval_minutes: 30,
    demo_mode_enabled: demoModeEnabled, // Синхронізуємо з контекстом
  });

  const [mitreSettings, setMitreSettings] = useState({
    mitre_version: "v10",
    use_custom_mappings: false,
    custom_mappings_path: "",
  });

  const [exportSettings, setExportSettings] = useState({
    default_export_format: "csv",
    include_raw_logs: false,
    max_records_per_export: 5000,
  });

  // Синхронізуємо стан компонента зі станом контексту
  useEffect(() => {
    setGeneralSettings(prev => ({
      ...prev,
      demo_mode_enabled: demoModeEnabled
    }));
  }, [demoModeEnabled]);

  // Використовуємо useCallback для уникнення помилок з ESLint
  const fetchConfiguration = useCallback(async () => {
    try {
      setLoading(true);
      
      try {
        const response = await getConfig();
        // Extract configuration settings
        const config = response.data || {};

        if (config.general) {
          // Convert string values to appropriate types
          const parsedGeneral = {
            ...config.general,
            data_retention_days:
              parseInt(config.general.data_retention_days, 10) || 90,
            refresh_interval_minutes:
              parseInt(config.general.refresh_interval_minutes, 10) || 30,
            auto_tagging_enabled:
              config.general.auto_tagging_enabled === true ||
              config.general.auto_tagging_enabled === "true",
            ml_classification_enabled:
              config.general.ml_classification_enabled === true ||
              config.general.ml_classification_enabled === "true",
            demo_mode_enabled: demoModeEnabled, // Використовуємо значення з контексту
          };
          setGeneralSettings(parsedGeneral);
        }

        if (config.mitre) {
          // Convert string values to appropriate types
          const parsedMitre = {
            ...config.mitre,
            use_custom_mappings:
              config.mitre.use_custom_mappings === true ||
              config.mitre.use_custom_mappings === "true",
          };
          setMitreSettings(parsedMitre);
        }

        if (config.export) {
          // Convert string values to appropriate types
          const parsedExport = {
            ...config.export,
            max_records_per_export:
              parseInt(config.export.max_records_per_export, 10) || 5000,
            include_raw_logs:
              config.export.include_raw_logs === true ||
              config.export.include_raw_logs === "true",
          };
          setExportSettings(parsedExport);
        }

        console.log("Loaded configuration:", config);
      } catch (apiError) {
        console.error("Configuration API may not be available:", apiError);
        // Залишаємо дефолтні значення на формі
      }
    } catch (error) {
      console.error("Error loading configuration:", error);
      setError(
        "Error fetching configuration: " +
          (error.response?.data?.message || error.message),
      );
    } finally {
      setLoading(false);
    }
  }, [demoModeEnabled]); // Додаємо залежність

  useEffect(() => {
    fetchConfiguration();
  }, [fetchConfiguration]);

  const handleGeneralChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === "checkbox" ? checked : value;
    
    // Оновлюємо тільки локальний стан, без виклику API
    setGeneralSettings({
      ...generalSettings,
      [name]: newValue
    });
  };

  const handleMitreChange = (e) => {
    const { name, value, type, checked } = e.target;
    setMitreSettings({
      ...mitreSettings,
      [name]: type === "checkbox" ? checked : value
    });
  };

  const handleExportChange = (e) => {
    const { name, value, type, checked } = e.target;
    setExportSettings({
      ...exportSettings,
      [name]:
        type === "checkbox"
          ? checked
          : type === "number"
            ? parseInt(value, 10)
            : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      // Ensure numeric values are properly formatted
      const formattedGeneralSettings = {
        ...generalSettings,
        data_retention_days: parseInt(generalSettings.data_retention_days, 10),
        refresh_interval_minutes: parseInt(
          generalSettings.refresh_interval_minutes,
          10,
        ),
      };

      const formattedExportSettings = {
        ...exportSettings,
        max_records_per_export: parseInt(
          exportSettings.max_records_per_export, 10,
        ),
      };

      // Combine all settings
      const configData = {
        general: formattedGeneralSettings,
        mitre: mitreSettings,
        export: formattedExportSettings,
      };

      console.log("Saving configuration:", configData);
      await updateConfig(configData);
      setSuccess("Configuration saved successfully");

      // Оновлюємо стан демо-режиму в контексті
      await updateDemoMode(formattedGeneralSettings.demo_mode_enabled);

      // Refresh the configuration to ensure we display the saved values
      await fetchConfiguration();

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      console.error("Error saving configuration:", error);
      setError(
        "Error saving configuration: " +
          (error.response?.data?.message || error.message),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="configuration-container">
      <h2>System Configuration</h2>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <form onSubmit={handleSubmit}>
        {/* General Settings */}
        <div className="config-section">
          <h3>General Settings</h3>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="data_retention_days">
                Data Retention Period (Days):
              </label>
              <input
                type="number"
                id="data_retention_days"
                name="data_retention_days"
                value={generalSettings.data_retention_days}
                onChange={handleGeneralChange}
                min="1"
                max="365"
              />
            </div>

            <div className="form-group">
              <label htmlFor="refresh_interval_minutes">
                Data Refresh Interval (Minutes):
              </label>
              <input
                type="number"
                id="refresh_interval_minutes"
                name="refresh_interval_minutes"
                value={generalSettings.refresh_interval_minutes}
                onChange={handleGeneralChange}
                min="5"
                max="1440"
              />
            </div>
          </div>

          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                name="auto_tagging_enabled"
                checked={generalSettings.auto_tagging_enabled}
                onChange={handleGeneralChange}
              />
              Enable Automatic Tagging
            </label>
          </div>

          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                name="ml_classification_enabled"
                checked={generalSettings.ml_classification_enabled}
                onChange={handleGeneralChange}
              />
              Enable ML Classification
            </label>
          </div>

          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                name="demo_mode_enabled"
                checked={generalSettings.demo_mode_enabled}
                onChange={handleGeneralChange}
              />
              Enable Demo Mode
            </label>
          </div>
        </div>

        {/* MITRE ATT&CK Settings */}
        <div className="config-section">
          <h3>MITRE ATT&CK Settings</h3>

          <div className="form-group">
            <label htmlFor="mitre_version">MITRE ATT&CK Version:</label>
            <select
              id="mitre_version"
              name="mitre_version"
              value={mitreSettings.mitre_version}
              onChange={handleMitreChange}
            >
              <option value="v10">Version 10</option>
              <option value="v9">Version 9</option>
              <option value="v8">Version 8</option>
            </select>
          </div>

          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                name="use_custom_mappings"
                checked={mitreSettings.use_custom_mappings}
                onChange={handleMitreChange}
              />
              Use Custom MITRE Mappings
            </label>
          </div>

          {mitreSettings.use_custom_mappings && (
            <div className="form-group">
              <label htmlFor="custom_mappings_path">
                Custom Mappings Path:
              </label>
              <input
                type="text"
                id="custom_mappings_path"
                name="custom_mappings_path"
                value={mitreSettings.custom_mappings_path}
                onChange={handleMitreChange}
                placeholder="/path/to/mappings.json"
              />
            </div>
          )}
        </div>

        {/* Export Settings */}
        <div className="config-section">
          <h3>Export Settings</h3>

          <div className="form-group">
            <label htmlFor="default_export_format">
              Default Export Format:
            </label>
            <select
              id="default_export_format"
              name="default_export_format"
              value={exportSettings.default_export_format}
              onChange={handleExportChange}
            >
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="max_records_per_export">
              Maximum Records per Export:
            </label>
            <input
              type="number"
              id="max_records_per_export"
              name="max_records_per_export"
              value={exportSettings.max_records_per_export}
              onChange={handleExportChange}
              min="100"
              max="50000"
            />
          </div>

          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                name="include_raw_logs"
                checked={exportSettings.include_raw_logs}
                onChange={handleExportChange}
              />
              Include Raw Logs in Export
            </label>
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="save-btn" disabled={loading}>
            {loading ? "Saving..." : "Save Configuration"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default Configuration;
import React, { useState, useEffect } from "react";
import { exportEvents, getExportJobs, downloadExport } from "../services/api";
import "./DataExport.css";

function DataExport() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [filters, setFilters] = useState({
    severity: "",
    siem_source: "",
    manual_review: true,
    date_from: "",
    date_to: "",
  });
  const [exportFormat, setExportFormat] = useState("csv");

  useEffect(() => {
    fetchExportJobs();
  }, []);

  const fetchExportJobs = async () => {
    try {
      setLoading(true);
      const response = await getExportJobs();
      setJobs(response.data);
    } catch (error) {
      setError(
        "Error fetching export jobs: " +
          (error.response?.data?.message || error.message),
      );
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;

    let processedValue = value;
    if (name === "manual_review") {
      processedValue = value === "true";
    }

    setFilters({
      ...filters,
      [name]: processedValue,
    });
  };

  const handleFormatChange = (e) => {
    setExportFormat(e.target.value);
  };

  const handleExport = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await exportEvents(exportFormat, filters);

      setSuccess(
        `Export completed successfully. ${response.data.record_count} records exported.`,
      );
      fetchExportJobs(); // Refresh the jobs list
    } catch (error) {
      setError(
        "Error exporting data: " +
          (error.response?.data?.message || error.message),
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (filePath) => {
    try {
      setLoading(true);
      const response = await downloadExport(filePath);

      // Create a blob from the response data
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);

      // Create a temporary link and trigger download
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filePath.split("/").pop());
      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError(
        "Error downloading file: " +
          (error.response?.data?.message || error.message),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="data-export-container">
      <h2>Data Export</h2>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="export-form-container">
        <h3>Create New Export</h3>
        <form onSubmit={handleExport}>
          <div className="form-row">
            <div className="form-group">
              <label>Export Format:</label>
              <select
                value={exportFormat}
                onChange={handleFormatChange}
                disabled={loading}
              >
                <option value="csv">CSV</option>
                <option value="json">JSON</option>
              </select>
            </div>

            <div className="form-group">
              <label>Severity:</label>
              <select
                name="severity"
                value={filters.severity}
                onChange={handleFilterChange}
                disabled={loading}
              >
                <option value="">All</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>SIEM Source:</label>
              <select
                name="siem_source"
                value={filters.siem_source}
                onChange={handleFilterChange}
                disabled={loading}
              >
                <option value="">All</option>
                <option value="wazuh">Wazuh</option>
                <option value="splunk">Splunk</option>
                <option value="elastic">Elastic</option>
              </select>
            </div>

            <div className="form-group">
              <label>Reviewed Only:</label>
              <select
                name="manual_review"
                value={filters.manual_review.toString()}
                onChange={handleFilterChange}
                disabled={loading}
              >
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Date From:</label>
              <input
                type="date"
                name="date_from"
                value={filters.date_from}
                onChange={handleFilterChange}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Date To:</label>
              <input
                type="date"
                name="date_to"
                value={filters.date_to}
                onChange={handleFilterChange}
                disabled={loading}
              />
            </div>
          </div>

          <button type="submit" className="export-btn" disabled={loading}>
            {loading ? "Processing..." : "Export Data"}
          </button>
        </form>
      </div>

      <div className="export-jobs-container">
        <h3>Previous Exports</h3>

        {jobs.length === 0 ? (
          <p className="no-jobs">No previous exports found</p>
        ) : (
          <table className="export-jobs-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Format</th>
                <th>Status</th>
                <th>Records</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>{new Date(job.created_at).toLocaleString()}</td>
                  <td>{job.format.toUpperCase()}</td>
                  <td>
                    <span className={`status-badge status-${job.status}`}>
                      {job.status}
                    </span>
                  </td>
                  <td>{job.record_count || "-"}</td>
                  <td>
                    {job.status === "completed" && (
                      <button
                        onClick={() => handleDownload(job.file_path)}
                        className="download-btn"
                        disabled={loading}
                      >
                        Download
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default DataExport;

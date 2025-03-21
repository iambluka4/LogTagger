// frontend/src/components/Layout.js
import React from 'react';
import { Link } from 'react-router-dom';
import './Layout.css';

function Layout({ children }) {
  return (
    <div className="app-container">
      <nav className="nav-bar">
        <div className="nav-links">
          <Link to="/">Dashboard</Link>
          <Link to="/labeling">Data Labeling</Link>
          <Link to="/export">Data Export</Link>
          <Link to="/api-config">API Config</Link>
          <Link to="/config">Configuration</Link>
        </div>
      </nav>
      <hr />
      <div className="content-container">
        {children}
      </div>
      <footer className="footer">
        <p>&copy; {new Date().getFullYear()} LogTagger - Automated Security Log Tagging Tool</p>
      </footer>
    </div>
  );
}

export default Layout;
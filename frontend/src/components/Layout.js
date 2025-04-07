import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Layout.css';

function Layout({ children }) {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  // Видаляємо будь-які перевірки автентифікації
  
  return (
    <div className="app-container" data-testid="app-layout">
      <nav className="nav-bar">
        <div className="nav-links">
          <Link to="/" className={isActive("/") ? "active" : ""}>
            Dashboard
          </Link>
          <Link
            to="/labeling"
            className={isActive("/labeling") ? "active" : ""}
          >
            Data Labeling
          </Link>
          <Link to="/export" className={isActive("/export") ? "active" : ""}>
            Data Export
          </Link>
          <Link
            to="/api-config"
            className={isActive("/api-config") ? "active" : ""}
          >
            API Config
          </Link>
          <Link to="/config" className={isActive("/config") ? "active" : ""}>
            Configuration
          </Link>
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

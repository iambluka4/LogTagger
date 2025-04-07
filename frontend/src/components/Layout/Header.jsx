import React from "react";
import { Link, useLocation } from "react-router-dom";
import "./Header.css";

function Header() {
  const location = useLocation();

  // Функція для визначення активного посилання
  const isActive = (path) => {
    return location.pathname === path ? "active" : "";
  };

  return (
    <header className="app-header">
      <div className="logo">LogTagger</div>
      <nav className="nav-links">
        <Link to="/dashboard" className={isActive("/dashboard")}>
          Dashboard
        </Link>
        <Link to="/labeling" className={isActive("/labeling")}>
          Data Labeling
        </Link>
        <Link to="/export" className={isActive("/export")}>
          Export
        </Link>
        <Link to="/api-config" className={isActive("/api-config")}>
          API Config
        </Link>
        <Link to="/config" className={isActive("/config")}>
          Settings
        </Link>
      </nav>
      <div className="version-info">
        <span className="version-badge">MVP</span>
      </div>
    </header>
  );
}

export default Header;

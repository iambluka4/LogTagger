import React from "react";
import { Link, useLocation } from "react-router-dom";
import "./Navigation.css";

function Navigation() {
  const location = useLocation();

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: 'dashboard' },
    { path: '/labeling', label: 'Data Labeling', icon: 'label' },
    { path: '/export', label: 'Export', icon: 'download' },
    { path: '/ml-dashboard', label: 'ML Dashboard', icon: 'psychology' }, // Додано ML Dashboard
    { path: '/api-config', label: 'API Configuration', icon: 'settings' },
    { path: '/config', label: 'System Configuration', icon: 'build' },
  ];

  return (
    <nav className="app-navigation">
      <div className="logo">
        <h1>LogTagger</h1>
        <span className="version">v1.0.0</span>
      </div>
      <ul className="nav-links">
        {menuItems.map((item) => (
          <li key={item.path} className={location.pathname === item.path ? "active" : ""}>
            <Link to={item.path}>
              <span className="icon material-icons">{item.icon}</span>
              <span className="label">{item.label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export default Navigation;

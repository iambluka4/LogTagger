// frontend/src/components/Layout.js
import React from 'react';
import { Link } from 'react-router-dom';
import './Layout.css';

function Layout({ children }) {
  return (
    <div className="app-container">
      <nav className="nav-bar">
        <Link to="/">Dashboard</Link>
        <Link to="/labeling">Data Labeling</Link>
        <Link to="/api-config">API Config</Link>
        <Link to="/users">Users</Link>
        <Link to="/config">Configuration</Link>
      </nav>
      <hr />
      <div className="content-container">
        {children}
      </div>
    </div>
  );
}

export default Layout;
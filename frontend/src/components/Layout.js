// frontend/src/components/Layout.js
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Layout.css';

function Layout({ children }) {
  const { user, logoutUser, isAdmin, isAnalyst } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  return (
    <div className="app-container">
      <nav className="nav-bar">
        <div className="nav-links">
          <Link to="/">Dashboard</Link>
          
          {/* Only show labeling and export to analysts and admins */}
          {isAnalyst() && (
            <>
              <Link to="/labeling">Data Labeling</Link>
              <Link to="/export">Data Export</Link>
            </>
          )}
          
          {/* Only show admin links to admins */}
          {isAdmin() && (
            <>
              <Link to="/api-config">API Config</Link>
              <Link to="/users">Users</Link>
              <Link to="/config">Configuration</Link>
            </>
          )}
        </div>
        
        <div className="user-menu">
          <span className="username">{user?.username || 'User'}</span>
          <button onClick={handleLogout} className="logout-btn">Logout</button>
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
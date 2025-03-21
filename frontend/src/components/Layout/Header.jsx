import React from 'react';
import { Link } from 'react-router-dom';

function Header() {
  return (
    <header className="app-header">
      <div className="logo">LogTagger</div>
      <nav className="nav-links">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/events">Events</Link>
        <Link to="/configuration">Configuration</Link>
      </nav>
      <div className="version-info">
        <span className="version-badge">MVP</span>
      </div>
    </header>
  );
}

export default Header;
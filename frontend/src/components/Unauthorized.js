import React from "react";
import { Link } from "react-router-dom";
import "./Unauthorized.css";

function Unauthorized() {
  return (
    <div className="unauthorized-container">
      <div className="unauthorized-content">
        <h1>Access Denied</h1>
        <p>You don't have permission to access this page.</p>
        <Link to="/" className="back-link">
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}

export default Unauthorized;

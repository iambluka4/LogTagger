import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import DataLabeling from './components/DataLabeling';
import ApiConfiguration from './components/ApiConfiguration';
import Users from './components/Users';
import Configuration from './components/Configuration';

function App() {
  return (
    <Router>
      <div style={{ margin: '20px' }}>
        <nav>
          <Link to="/">Dashboard</Link> |{" "}
          <Link to="/labeling">Data Labeling</Link> |{" "}
          <Link to="/api-config">API Config</Link> |{" "}
          <Link to="/users">Users</Link> |{" "}
          <Link to="/config">Configuration</Link>
        </nav>

        <hr />

        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/labeling" element={<DataLabeling />} />
          <Route path="/api-config" element={<ApiConfiguration />} />
          <Route path="/users" element={<Users />} />
          <Route path="/config" element={<Configuration />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

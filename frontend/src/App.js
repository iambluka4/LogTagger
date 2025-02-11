import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import DataLabeling from './components/DataLabeling';
import ApiConfiguration from './components/ApiConfiguration';
import Users from './components/Users';
import Configuration from './components/Configuration';
import Layout from './components/Layout';
import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/labeling" element={<DataLabeling />} />
          <Route path="/api-config" element={<ApiConfiguration />} />
          <Route path="/users" element={<Users />} />
          <Route path="/config" element={<Configuration />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;

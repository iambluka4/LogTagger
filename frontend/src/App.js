import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import DataLabeling from './components/DataLabeling';
import ApiConfiguration from './components/ApiConfiguration';
import Configuration from './components/Configuration';
import DataExport from './components/DataExport';
import Layout from './components/Layout';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        {/* All routes are accessible without authentication */}
        <Route path="/" element={
          <Layout>
            <Dashboard />
          </Layout>
        } />
        
        <Route path="/labeling" element={
          <Layout>
            <DataLabeling />
          </Layout>
        } />
        
        <Route path="/export" element={
          <Layout>
            <DataExport />
          </Layout>
        } />
        
        <Route path="/api-config" element={
          <Layout>
            <ApiConfiguration />
          </Layout>
        } />
        
        {/* Removed Users route */}
        
        <Route path="/config" element={
          <Layout>
            <Configuration />
          </Layout>
        } />
        
        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
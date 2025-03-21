import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import DataLabeling from './components/DataLabeling';
import ApiConfiguration from './components/ApiConfiguration';
import Users from './components/Users';
import Configuration from './components/Configuration';
import DataExport from './components/DataExport';
import Login from './components/Login';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Unauthorized from './components/Unauthorized';
import { AuthProvider } from './contexts/AuthContext';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/labeling" element={
            <ProtectedRoute requiredRole="analyst">
              <Layout>
                <DataLabeling />
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/export" element={
            <ProtectedRoute requiredRole="analyst">
              <Layout>
                <DataExport />
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/api-config" element={
            <ProtectedRoute requiredRole="admin">
              <Layout>
                <ApiConfiguration />
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/users" element={
            <ProtectedRoute requiredRole="admin">
              <Layout>
                <Users />
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/config" element={
            <ProtectedRoute requiredRole="admin">
              <Layout>
                <Configuration />
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import DataLabeling from "./components/DataLabeling";
import DataExport from "./components/DataExport";
import ApiConfiguration from "./components/ApiConfiguration";
import Configuration from "./components/Configuration";
import { DemoModeProvider } from "./context/DemoModeContext";
import { ServicesProvider } from "./context/ServicesContext";
import OfflineBanner from "./components/OfflineBanner";
import MLDashboard from "./components/MLDashboard";
import ApiErrorsViewer from "./components/ApiErrorsViewer";
import "./App.css";

function App() {
  return (
    <ServicesProvider>
      <DemoModeProvider>
        <Router>
          <OfflineBanner />
          <ApiErrorsViewer />
          <Routes>
            {/* Перенаправляємо login на головну сторінку */}
            <Route path="/login" element={<Navigate to="/" replace />} />
            
            {/* Базовий маршрут на Dashboard */}
            <Route
              path="/"
              element={
                <Layout>
                  <Dashboard />
                </Layout>
              }
            />

            <Route
              path="/dashboard"
              element={
                <Layout>
                  <Dashboard />
                </Layout>
              }
            />

            <Route
              path="/labeling"
              element={
                <Layout>
                  <DataLabeling />
                </Layout>
              }
            />

            <Route
              path="/export"
              element={
                <Layout>
                  <DataExport />
                </Layout>
              }
            />

            <Route
              path="/api-config"
              element={
                <Layout>
                  <ApiConfiguration />
                </Layout>
              }
            />

            <Route
              path="/config"
              element={
                <Layout>
                  <Configuration />
                </Layout>
              }
            />

            <Route
              path="/ml-dashboard"
              element={
                <Layout>
                  <MLDashboard />
                </Layout>
              }
            />

            {/* Перенаправляємо всі невідомі маршрути на головну */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </DemoModeProvider>
    </ServicesProvider>
  );
}

export default App;

import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Header from './components/Layout/Header';
import Dashboard from './components/Dashboard';
import EventList from './components/EventList';
import ConfigurationPage from './components/ConfigurationPage';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/events" element={<EventList />} />
            <Route path="/configuration" element={<ConfigurationPage />} />
            {/* Всі інші шляхи перенаправляються на дашборд */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
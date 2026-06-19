import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import MarketAnalysis from './pages/MarketAnalysis';
import Predictions from './pages/Predictions';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';

function App() {
  return (
    <AnimatePresence mode="wait">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="market-analysis" element={<MarketAnalysis />} />
          <Route path="predictions" element={<Predictions />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}

export default App;

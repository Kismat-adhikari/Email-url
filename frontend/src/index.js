import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import './ErrorBoundary.css';
import './BatchValidation.css';
import App from './App';
import HomePage from './HomePage';

import Login from './Login';
import Signup from './Signup';
import Profile from './Profile';
import TeamManagement from './TeamManagement';
import TeamInvite from './TeamInvite';

import AdminLogin from './AdminLogin';
import AdminDashboard from './AdminDashboard';
import ErrorBoundary from './ErrorBoundary';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/app" element={<App />} />
          <Route path="/testing" element={<App />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/team" element={<TeamManagement />} />
          <Route path="/invite/:token" element={<TeamInvite />} />

          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>
);

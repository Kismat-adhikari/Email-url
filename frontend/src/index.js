import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import './ErrorBoundary.css';
import App from './App';
import Testing from './Testing';
import Login from './Login';
import Signup from './Signup';
import Profile from './Profile';
import TeamManagement from './TeamManagement';
import TeamInvite from './TeamInvite';
import TestSend from './TestSend';
import AdminLogin from './AdminLogin';
import AdminDashboard from './AdminDashboard';
import ErrorBoundary from './ErrorBoundary';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/testing" element={<Testing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/team" element={<TeamManagement />} />
          <Route path="/invite/:token" element={<TeamInvite />} />
          <Route path="/testsend" element={<TestSend />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>
);

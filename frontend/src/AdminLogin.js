import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMail, FiLock, FiEye, FiEyeOff, FiShield, FiAlertCircle } from 'react-icons/fi';
import './AdminLogin.css';

const AdminLogin = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(''); // Clear error when user types
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/admin/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        // Store admin token and data
        localStorage.setItem('adminToken', data.token);
        localStorage.setItem('adminUser', JSON.stringify(data.admin));
        localStorage.setItem('adminMode', 'true'); // Set admin mode flag
        
        // Redirect to admin dashboard
        navigate('/admin/dashboard');
      } else {
        setError(data.error || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-container">
      <div className="admin-login-background">
        <div className="admin-login-overlay"></div>
      </div>
      
      <div className="admin-login-card">
        <div className="admin-login-header">
          <div className="admin-logo">
            <FiShield className="admin-logo-icon" />
            <span className="admin-logo-text">ADMIN</span>
          </div>
          <h1>Admin Portal</h1>
          <p>Secure access to system administration</p>
        </div>

        <form onSubmit={handleSubmit} className="admin-login-form">
          {error && (
            <div className="admin-error-message">
              <FiAlertCircle />
              <span>{error}</span>
            </div>
          )}

          <div className="admin-form-group">
            <label htmlFor="email">Email Address</label>
            <div className="admin-input-wrapper">
              <FiMail className="admin-input-icon" />
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="admin@emailvalidator.com"
                required
                disabled={loading}
              />
            </div>
          </div>

          <div className="admin-form-group">
            <label htmlFor="password">Password</label>
            <div className="admin-input-wrapper">
              <FiLock className="admin-input-icon" />
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                required
                disabled={loading}
              />
              <button
                type="button"
                className="admin-password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="admin-login-btn"
            disabled={loading || !formData.email || !formData.password}
          >
            {loading ? (
              <>
                <div className="admin-spinner"></div>
                Authenticating...
              </>
            ) : (
              <>
                <FiShield />
                Access Admin Panel
              </>
            )}
          </button>
        </form>

        <div className="admin-login-footer">
          <p>
            <strong>Security Notice:</strong> This is a restricted area. 
            All access attempts are logged and monitored.
          </p>
          <button 
            className="back-to-app-btn"
            onClick={() => navigate('/')}
          >
            ← Back to Main App
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
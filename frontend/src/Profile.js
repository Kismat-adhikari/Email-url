import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUser, FiMail, FiCalendar, FiKey, FiSave, FiEdit3, FiActivity, FiAward, FiArrowLeft, FiLogOut, FiMoon, FiSun, FiZap } from 'react-icons/fi';
import './Profile.css';

const Profile = () => {
  const navigate = useNavigate();
  
  // Get user data from localStorage
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  
  const [authToken] = useState(() => {
    return localStorage.getItem('authToken');
  });
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    sendgridApiKey: ''
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  
  // Dark mode state
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    if (user) {
      setFormData({
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        email: user.email || '',
        sendgridApiKey: user.sendgridApiKey || ''
      });
    }
  }, [user]);

  useEffect(() => {
    // Apply dark mode class
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);

    try {
      const response = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: 'Profile updated successfully!' });
        setIsEditing(false);
        // Update localStorage with new user data
        localStorage.setItem('user', JSON.stringify(data.user));
        setUser(data.user);
      } else {
        setMessage({ type: 'error', text: data.message || 'Failed to update profile' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const maskApiKey = (apiKey) => {
    if (!apiKey) return 'Not set';
    if (apiKey.length <= 8) return apiKey;
    return apiKey.substring(0, 8) + '•'.repeat(apiKey.length - 8);
  };

  const handleLogout = async () => {
    try {
      if (authToken) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      
      // Redirect to home
      navigate('/');
    }
  };

  if (!user) {
    return (
      <div className="App">
        {/* Top Navigation Bar */}
        <nav className="top-navbar">
          <div className="navbar-container">
            {/* Logo Section */}
            <div className="navbar-logo">
              <span className="logo-text" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>LAGCI</span>
            </div>

            {/* Right Section */}
            <div className="navbar-right">
              {/* Dark Mode Toggle */}
              <button className="navbar-btn dark-mode-btn" onClick={toggleDarkMode} title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
                {darkMode ? <FiSun /> : <FiMoon />}
              </button>

              {/* Authentication Buttons */}
              <div className="auth-buttons">
                <button className="navbar-btn login-btn" onClick={() => navigate('/login')}>
                  Login
                </button>
                <button className="navbar-btn signup-btn" onClick={() => navigate('/signup')}>
                  Sign Up
                </button>
              </div>
            </div>
          </div>
        </nav>

        <div className="pro-container">
          <div className="pro-main-card">
            <div className="pro-content">
              <div className="profile-error">
                <h2>Access Denied</h2>
                <p>Please log in to view your profile.</p>
                <button className="pro-validate-btn" onClick={() => navigate('/login')}>
                  Go to Login
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      {/* Top Navigation Bar */}
      <nav className="top-navbar">
        <div className="navbar-container">
          {/* Logo Section */}
          <div className="navbar-logo">
            <span className="logo-text" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>LAGCI</span>
          </div>

          {/* Center Section - User Info */}
          <div className="navbar-center">
            <div className="user-greeting">
              <span className="wave-icon">👋</span>
              <span className="greeting-text">Welcome, {user.firstName}!</span>
            </div>
          </div>

          {/* Right Section - API Usage & Controls */}
          <div className="navbar-right">
            {/* Dark Mode Toggle */}
            <button className="navbar-btn dark-mode-btn" onClick={toggleDarkMode} title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
              {darkMode ? <FiSun /> : <FiMoon />}
            </button>

            {/* API Usage Counter */}
            <div className={`api-usage-counter ${user.apiCallsCount >= user.apiCallsLimit ? 'limit-reached' : user.apiCallsCount >= user.apiCallsLimit * 0.8 ? 'limit-warning' : ''}`}>
              <FiActivity className="usage-icon" />
              <span className="usage-text">{user.apiCallsCount || 0}/{user.apiCallsLimit}</span>
              <span className="usage-label">
                {user.subscriptionTier === 'free' ? 'Free' : 'API Calls'}
              </span>
              {user.subscriptionTier === 'free' && user.apiCallsCount >= user.apiCallsLimit && (
                <div className="upgrade-hint">
                  <FiZap style={{marginRight: '4px'}} /> Upgrade for unlimited!
                </div>
              )}
            </div>

            {/* Navigation Buttons */}
            <div className="auth-buttons">
              <button className="navbar-btn" onClick={() => navigate('/')}>
                <FiArrowLeft /> Back to App
              </button>
              <button className="navbar-btn logout-btn" onClick={handleLogout}>
                <FiLogOut /> Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="pro-container">
        <div className="pro-main-card">
          <div className="pro-content">
      <div className="profile-header">
        <div className="profile-avatar">
          <FiUser size={48} />
        </div>
        <div className="profile-title">
          <h1>Profile Settings</h1>
          <p>Manage your account information and preferences</p>
        </div>
        <button
          className={`edit-btn ${isEditing ? 'cancel' : 'edit'}`}
          onClick={() => {
            setIsEditing(!isEditing);
            if (isEditing) {
              // Reset form data when canceling
              setFormData({
                firstName: user.firstName || '',
                lastName: user.lastName || '',
                email: user.email || '',
                sendgridApiKey: user.sendgridApiKey || ''
              });
              setMessage(null);
            }
          }}
        >
          <FiEdit3 />
          {isEditing ? 'Cancel' : 'Edit Profile'}
        </button>
      </div>

      {message && (
        <div className={`profile-message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="profile-content">
        {/* Personal Information */}
        <div className="profile-section">
          <h3><FiUser /> Personal Information</h3>
          <div className="profile-grid">
            <div className="profile-field">
              <label>First Name</label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => setFormData(prev => ({ ...prev, firstName: e.target.value }))}
                  className="profile-input"
                />
              ) : (
                <div className="profile-value">{user.firstName}</div>
              )}
            </div>

            <div className="profile-field">
              <label>Last Name</label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => setFormData(prev => ({ ...prev, lastName: e.target.value }))}
                  className="profile-input"
                />
              ) : (
                <div className="profile-value">{user.lastName}</div>
              )}
            </div>

            <div className="profile-field">
              <label><FiMail /> Email Address</label>
              {isEditing ? (
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  className="profile-input"
                />
              ) : (
                <div className="profile-value">{user.email}</div>
              )}
            </div>

            <div className="profile-field">
              <label><FiCalendar /> Member Since</label>
              <div className="profile-value">{formatDate(user.createdAt)}</div>
            </div>
          </div>
        </div>

        {/* Account Information */}
        <div className="profile-section">
          <h3><FiAward /> Account Information</h3>
          <div className="profile-grid">
            <div className="profile-field">
              <label>Subscription Tier</label>
              <div className="profile-value">
                <span className={`tier-badge tier-${user.subscriptionTier}`}>
                  {user.subscriptionTier.toUpperCase()}
                </span>
              </div>
            </div>

            <div className="profile-field">
              <label><FiActivity /> API Usage</label>
              <div className="profile-value">
                <div className="usage-display">
                  <span className="usage-numbers">
                    {user.apiCallsCount || 0} / {user.apiCallsLimit || 10}
                  </span>
                  <div className="usage-bar">
                    <div 
                      className="usage-fill"
                      style={{ 
                        width: `${Math.min(((user.apiCallsCount || 0) / (user.apiCallsLimit || 10)) * 100, 100)}%` 
                      }}
                    />
                  </div>
                  <span className="usage-percentage">
                    {Math.round(((user.apiCallsCount || 0) / (user.apiCallsLimit || 10)) * 100)}% used
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* API Configuration */}
        <div className="profile-section">
          <h3><FiKey /> API Configuration</h3>
          <div className="profile-grid">
            <div className="profile-field full-width">
              <label>SendGrid API Key</label>
              <div className="api-key-field">
                {isEditing ? (
                  <input
                    type="password"
                    placeholder="SG.your_sendgrid_api_key_here"
                    value={formData.sendgridApiKey}
                    onChange={(e) => setFormData(prev => ({ ...prev, sendgridApiKey: e.target.value }))}
                    className="profile-input api-key-input"
                  />
                ) : (
                  <div className="profile-value api-key-display">
                    {maskApiKey(user.sendgridApiKey)}
                  </div>
                )}
              </div>
              <div className="field-help">
                {isEditing ? (
                  <p>Enter your SendGrid API key to enable email sending features. Get one at <a href="https://sendgrid.com" target="_blank" rel="noopener noreferrer">sendgrid.com</a></p>
                ) : (
                  <p>API key is used for sending emails through SendGrid service.</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        {isEditing && (
          <div className="profile-actions">
            <button
              className="save-btn"
              onClick={handleSave}
              disabled={saving}
            >
              <FiSave />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        )}
      </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
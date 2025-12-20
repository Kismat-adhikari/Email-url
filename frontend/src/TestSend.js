import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMail, FiSend, FiKey, FiUsers, FiActivity, FiZap, FiArrowLeft, FiLogOut, FiMoon, FiSun, FiUser } from 'react-icons/fi';
import './TestSend.css';

const TestSend = () => {
  const navigate = useNavigate();
  
  // Get user data from localStorage
  const [user] = useState(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  
  const [authToken] = useState(() => {
    return localStorage.getItem('authToken');
  });
  
  // Dark mode state
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });
  
  // Email sending state
  const [emailData, setEmailData] = useState({
    sendgridApiKey: '',
    fromEmail: '',
    fromName: '',
    toEmails: '',
    subject: '',
    message: ''
  });
  
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
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
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      navigate('/');
    }
  };

  const handleSendEmail = async (e) => {
    e.preventDefault();
    
    if (!emailData.sendgridApiKey || !emailData.fromEmail || !emailData.toEmails || !emailData.subject) {
      setMessage({ type: 'error', text: 'Please fill in all required fields' });
      return;
    }

    setSending(true);
    setMessage(null);

    try {
      // This is just a demo - no actual backend endpoint yet
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API call
      
      setMessage({ 
        type: 'success', 
        text: `Demo: Email would be sent to ${emailData.toEmails.split(',').length} recipient(s)` 
      });
      
      // Reset form
      setEmailData({
        ...emailData,
        toEmails: '',
        subject: '',
        message: ''
      });
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Demo: This is just a UI preview - no actual sending yet' });
    } finally {
      setSending(false);
    }
  };

  // Check if user is authenticated
  if (!user || !authToken) {
    return (
      <div className="App">
        <nav className="top-navbar">
          <div className="navbar-container">
            <div className="navbar-logo">
              <span className="logo-text" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>LAGCI</span>
            </div>
            <div className="navbar-right">
              <button className="navbar-btn dark-mode-btn" onClick={toggleDarkMode}>
                {darkMode ? <FiSun /> : <FiMoon />}
              </button>
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
                <p>Please log in to access the email sending demo.</p>
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
          <div className="navbar-logo">
            <span className="logo-text" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>LAGCI</span>
          </div>

          <div className="navbar-center">
            <div className="user-greeting">
              <span className="wave-icon">👋</span>
              <span className="greeting-text">Welcome, {user.firstName}!</span>
            </div>
          </div>

          <div className="navbar-right">
            <button className="navbar-btn dark-mode-btn" onClick={toggleDarkMode}>
              {darkMode ? <FiSun /> : <FiMoon />}
            </button>

            <div className="auth-buttons">
              <button className="navbar-btn" onClick={() => navigate('/')}>
                <FiArrowLeft /> Back to App
              </button>
              <button className="navbar-btn profile-btn" onClick={() => navigate('/profile')}>
                <FiUser /> Profile
              </button>
              <button className="navbar-btn logout-btn" onClick={handleLogout}>
                <FiLogOut /> Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="pro-container">
        {/* Header */}
        <header className="pro-header-simple">
          <div className="pro-header-title">
            <h1><FiMail /> Email Sending Demo</h1>
          </div>
          <p className="pro-header-subtitle">
            SendGrid Integration Preview - UI Demo Only
          </p>
        </header>

        {/* Main Card */}
        <div className="pro-main-card">
          <div className="testsend-container">
            
            {/* Demo Notice */}
            <div className="demo-notice">
              <div className="demo-icon">🚧</div>
              <div className="demo-content">
                <h3>Demo Mode</h3>
                <p>This is a UI preview of the SendGrid email sending feature. No actual emails are sent.</p>
              </div>
            </div>

            {message && (
              <div className={`message ${message.type}`}>
                {message.text}
              </div>
            )}

            <form onSubmit={handleSendEmail} className="email-form">
              
              {/* SendGrid Configuration */}
              <div className="form-section">
                <h3><FiKey /> SendGrid Configuration</h3>
                
                <div className="form-group">
                  <label>SendGrid API Key *</label>
                  <input
                    type="password"
                    placeholder="SG.your_sendgrid_api_key_here"
                    value={emailData.sendgridApiKey}
                    onChange={(e) => setEmailData(prev => ({ ...prev, sendgridApiKey: e.target.value }))}
                    required
                  />
                  <div className="field-help">
                    Get your API key from <a href="https://sendgrid.com" target="_blank" rel="noopener noreferrer">SendGrid Dashboard</a>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>From Email *</label>
                    <input
                      type="email"
                      placeholder="noreply@yourdomain.com"
                      value={emailData.fromEmail}
                      onChange={(e) => setEmailData(prev => ({ ...prev, fromEmail: e.target.value }))}
                      required
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>From Name</label>
                    <input
                      type="text"
                      placeholder="Your Company"
                      value={emailData.fromName}
                      onChange={(e) => setEmailData(prev => ({ ...prev, fromName: e.target.value }))}
                    />
                  </div>
                </div>
              </div>

              {/* Email Content */}
              <div className="form-section">
                <h3><FiMail /> Email Content</h3>
                
                <div className="form-group">
                  <label>To Emails *</label>
                  <textarea
                    placeholder="user1@example.com, user2@example.com, user3@example.com"
                    value={emailData.toEmails}
                    onChange={(e) => setEmailData(prev => ({ ...prev, toEmails: e.target.value }))}
                    rows="3"
                    required
                  />
                  <div className="field-help">
                    Separate multiple emails with commas
                  </div>
                </div>

                <div className="form-group">
                  <label>Subject *</label>
                  <input
                    type="text"
                    placeholder="Your email subject"
                    value={emailData.subject}
                    onChange={(e) => setEmailData(prev => ({ ...prev, subject: e.target.value }))}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Message</label>
                  <textarea
                    placeholder="Your email message..."
                    value={emailData.message}
                    onChange={(e) => setEmailData(prev => ({ ...prev, message: e.target.value }))}
                    rows="6"
                  />
                </div>
              </div>

              {/* Send Button */}
              <div className="form-actions">
                <button 
                  type="submit" 
                  className="send-btn"
                  disabled={sending}
                >
                  <FiSend />
                  {sending ? 'Sending Demo...' : 'Send Email (Demo)'}
                </button>
              </div>
            </form>

            {/* Features Preview */}
            <div className="features-preview">
              <h3><FiZap /> Planned Features</h3>
              <div className="features-grid">
                <div className="feature-item">
                  <FiMail className="feature-icon" />
                  <div className="feature-content">
                    <h4>Bulk Email Sending</h4>
                    <p>Send to thousands of validated email addresses</p>
                  </div>
                </div>
                
                <div className="feature-item">
                  <FiUsers className="feature-icon" />
                  <div className="feature-content">
                    <h4>Contact Management</h4>
                    <p>Organize and segment your email lists</p>
                  </div>
                </div>
                
                <div className="feature-item">
                  <FiActivity className="feature-icon" />
                  <div className="feature-content">
                    <h4>Delivery Tracking</h4>
                    <p>Track opens, clicks, and bounces</p>
                  </div>
                </div>
                
                <div className="feature-item">
                  <FiZap className="feature-icon" />
                  <div className="feature-content">
                    <h4>Email Templates</h4>
                    <p>Pre-designed templates for campaigns</p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default TestSend;
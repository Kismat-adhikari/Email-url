 import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// ============================================================================
// ANONYMOUS USER ID SYSTEM
// ============================================================================

/**
 * Generate a UUIDv4 for anonymous user identification
 */
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Get or create anonymous user ID
 * Stored in localStorage for persistence across sessions
 */
function getAnonUserId() {
  let anonUserId = localStorage.getItem('anon_user_id');
  
  if (!anonUserId) {
    anonUserId = generateUUID();
    localStorage.setItem('anon_user_id', anonUserId);
    console.log('🆔 Generated new anonymous user ID:', anonUserId);
  }
  
  return anonUserId;
}

function App() {
  const [email, setEmail] = useState('');
  const [mode, setMode] = useState('advanced'); // 'basic' or 'advanced'
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [batchMode, setBatchMode] = useState(false);
  const [batchEmails, setBatchEmails] = useState('');
  const [batchResults, setBatchResults] = useState(null);
  const [uploadMode, setUploadMode] = useState('text'); // 'text' or 'file'
  const [selectedFile, setSelectedFile] = useState(null);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });
  
  // New state for dashboard features
  const [activeTab, setActiveTab] = useState('validate'); // 'validate', 'history', 'analytics'
  const [validationHistory, setValidationHistory] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  
  // Anonymous User ID
  const [anonUserId] = useState(() => getAnonUserId());

  // API URL - use relative path in production, localhost in development
  const API_URL = process.env.NODE_ENV === 'production' 
    ? ''  // Empty string for relative URLs in production
    : 'http://localhost:5000';  // Localhost for development
  
  // Axios instance with anonymous user ID header
  const api = axios.create({
    baseURL: API_URL,
    headers: {
      'X-User-ID': anonUserId
    }
  });

  // Toggle dark mode 
  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem('darkMode', JSON.stringify(newMode));
    document.body.classList.toggle('dark-mode', newMode);
  };

  // Apply dark mode on mount
  useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode);
  }, [darkMode]);

  // Load validation history when switching to history tab
  useEffect(() => {
    if (activeTab === 'history') {
      loadValidationHistory();
    } else if (activeTab === 'analytics') {
      loadAnalytics();
    }
  }, [activeTab]);

  // Load validation history from Supabase
  const loadValidationHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await api.get('/api/records', {
        params: { limit: 100 }
      });
      console.log('History response:', response.data);
      console.log('Records:', response.data.records);
      setValidationHistory(response.data.records || []);
    } catch (err) {
      console.error('Failed to load history:', err);
      setValidationHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Clear history function
  const clearHistory = () => {
    if (window.confirm('Are you sure you want to clear all history? This cannot be undone.')) {
      setValidationHistory([]);
      // Note: This only clears the display. To delete from Supabase, you'd need to call DELETE endpoints
    }
  };

  // Load analytics data from Supabase
  const loadAnalytics = async () => {
    setHistoryLoading(true);
    try {
      const response = await api.get('/api/statistics');
      setAnalytics(response.data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Export to CSV
  const exportToCSV = () => {
    if (!batchResults || !batchResults.results) return;

    const headers = mode === 'advanced' 
      ? ['Email', 'Valid', 'Confidence Score', 'Reason', 'Suggestion']
      : ['Email', 'Valid'];

    const rows = batchResults.results.map(r => {
      if (mode === 'advanced') {
        return [
          r.email,
          r.valid ? 'Yes' : 'No',
          r.confidence_score || 'N/A',
          r.reason || '',
          r.suggestion || ''
        ];
      } else {
        return [r.email, r.valid ? 'Yes' : 'No'];
      }
    });

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `email-validation-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Copy to clipboard
  const copyToClipboard = () => {
    if (!batchResults || !batchResults.results) return;

    const text = batchResults.results
      .map(r => `${r.valid ? '✓' : '✗'} ${r.email}`)
      .join('\n');

    navigator.clipboard.writeText(text).then(() => {
      alert('Results copied to clipboard!');
    });
  };

  const validateEmail = async () => {
    if (!email.trim()) {
      setError('Please enter an email address');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const endpoint = mode === 'advanced' 
        ? '/api/validate/advanced'
        : '/api/validate';
      const response = await api.post(endpoint, { email });
      
      setResult(response.data);
      
      // Refresh history if on history tab
      if (activeTab === 'history') {
        loadValidationHistory();
      }
    } catch (err) {
      console.error('Validation error:', err);
      const errorMsg = err.response?.data?.message 
        || err.message 
        || 'Validation failed. Make sure the backend is running on port 5000.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'text/plain' && !file.name.endsWith('.txt')) {
        setError('Please select a .txt file');
        return;
      }
      setSelectedFile(file);
      setError(null);
      
      // Read file and populate textarea
      const reader = new FileReader();
      reader.onload = (event) => {
        setBatchEmails(event.target.result);
      };
      reader.readAsText(file);
    }
  };

  const validateBatch = async () => {
    const emails = batchEmails
      .split('\n')
      .map(e => e.trim())
      .filter(e => e.length > 0);

    if (emails.length === 0) {
      setError('Please enter at least one email address or upload a file');
      return;
    }

    setLoading(true);
    setError(null);
    setBatchResults(null);

    try {
      const response = await api.post('/api/validate/batch', {
        emails,
        advanced: mode === 'advanced'
      });
      setBatchResults(response.data);
      
      // Refresh history if on history tab
      if (activeTab === 'history') {
        loadValidationHistory();
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Batch validation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !batchMode) {
      validateEmail();
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 90) return '#10b981';
    if (score >= 70) return '#f59e0b';
    return '#ef4444';
  };

  const getConfidenceLabel = (score) => {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    return 'Poor';
  };

  const getRiskLevelColor = (level) => {
    const colors = {
      'low': '#10b981',
      'medium': '#f59e0b',
      'high': '#ef4444',
      'critical': '#991b1b'
    };
    return colors[level?.toLowerCase()] || '#64748b';
  };

  const getRiskLevelLabel = (level) => {
    return level ? level.charAt(0).toUpperCase() + level.slice(1) : 'Unknown';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <div className="header-content">
            <div>
              <h1>✉️ Email Validator</h1>
              <p>Advanced email validation with DNS, MX, and disposable detection</p>
            </div>
            <button className="dark-mode-toggle" onClick={toggleDarkMode} title="Toggle Dark Mode">
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </header>

        <div className="tab-selector">
          <button
            className={`tab-btn ${activeTab === 'validate' ? 'active' : ''}`}
            onClick={() => setActiveTab('validate')}
          >
            🔍 Validate
          </button>
          <button
            className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            📜 History
          </button>
          <button
            className={`tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            📊 Analytics
          </button>
        </div>

        {activeTab === 'validate' && (
          <>
            <div className="mode-selector">
              <button
                className={`mode-btn ${!batchMode ? 'active' : ''}`}
                onClick={() => {
                  setBatchMode(false);
                  setResult(null);
                  setBatchResults(null);
                  setError(null);
                }}
              >
                Single Email
              </button>
              <button
                className={`mode-btn ${batchMode ? 'active' : ''}`}
                onClick={() => {
                  setBatchMode(true);
                  setResult(null);
                  setBatchResults(null);
                  setError(null);
                }}
              >
                Batch Validation
              </button>
            </div>

        <div className="validation-mode">
          <label>
            <input
              type="radio"
              value="basic"
              checked={mode === 'basic'}
              onChange={(e) => {
                setMode(e.target.value);
                setResult(null); // Clear result when switching modes
                setError(null);
              }}
            />
            <span>Basic - Syntax Only (Fast)</span>
          </label>
          <label>
            <input
              type="radio"
              value="advanced"
              checked={mode === 'advanced'}
              onChange={(e) => {
                setMode(e.target.value);
                setResult(null); // Clear result when switching modes
                setError(null);
              }}
            />
            <span>Advanced - Full Check (DNS, MX, Disposable)</span>
          </label>
        </div>

        {!batchMode ? (
          <div className="input-section">
            <input
              type="email"
              className="email-input"
              placeholder="Enter email address..."
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button
              className="validate-btn"
              onClick={validateEmail}
              disabled={loading}
            >
              {loading ? 'Validating...' : 'Validate'}
            </button>
          </div>
        ) : (
          <div className="batch-section">
            <div className="upload-mode-selector">
              <button
                className={`upload-mode-btn ${uploadMode === 'text' ? 'active' : ''}`}
                onClick={() => setUploadMode('text')}
              >
                ✏️ Type Emails
              </button>
              <button
                className={`upload-mode-btn ${uploadMode === 'file' ? 'active' : ''}`}
                onClick={() => setUploadMode('file')}
              >
                📁 Upload File
              </button>
            </div>

            {uploadMode === 'text' ? (
              <textarea
                className="batch-input"
                placeholder="Enter email addresses (one per line)..."
                value={batchEmails}
                onChange={(e) => setBatchEmails(e.target.value)}
                disabled={loading}
                rows={10}
              />
            ) : (
              <div className="file-upload-section">
                <div className="file-upload-box">
                  <input
                    type="file"
                    id="file-input"
                    accept=".txt"
                    onChange={handleFileSelect}
                    disabled={loading}
                    style={{ display: 'none' }}
                  />
                  <label htmlFor="file-input" className="file-upload-label">
                    <div className="upload-icon">📄</div>
                    <div className="upload-text">
                      {selectedFile ? (
                        <>
                          <strong>{selectedFile.name}</strong>
                          <br />
                          <small>Click to change file</small>
                        </>
                      ) : (
                        <>
                          <strong>Click to upload .txt file</strong>
                          <br />
                          <small>One email per line</small>
                        </>
                      )}
                    </div>
                  </label>
                </div>
                {batchEmails && (
                  <div className="file-preview">
                    <strong>Preview ({batchEmails.split('\n').filter(e => e.trim()).length} emails):</strong>
                    <textarea
                      className="batch-input preview"
                      value={batchEmails}
                      onChange={(e) => setBatchEmails(e.target.value)}
                      disabled={loading}
                      rows={8}
                    />
                  </div>
                )}
              </div>
            )}

            <button
              className="validate-btn"
              onClick={validateBatch}
              disabled={loading || (!batchEmails.trim())}
            >
              {loading ? 'Validating...' : 'Validate Batch'}
            </button>
          </div>
        )}

        {error && (
          <div className="error-box">
            <strong>Error:</strong> {error}
          </div>
        )}

        {result && !batchMode && (
          <div className={`result-box ${result.valid ? 'valid' : 'invalid'}`}>
            <div className="result-header">
              <h2>{result.valid ? '✓ Valid Email' : '✗ Invalid Email'}</h2>
              <span className="email-display">{result.email}</span>
            </div>

            {mode === 'advanced' && result.checks && (
              <>
                <div className="confidence-section">
                  <div className="confidence-label">Confidence Score</div>
                  <div className="confidence-bar-container">
                    <div
                      className="confidence-bar"
                      style={{
                        width: `${result.confidence_score || 0}%`,
                        backgroundColor: getConfidenceColor(result.confidence_score || 0)
                      }}
                    />
                  </div>
                  <div className="confidence-value">
                    {result.confidence_score || 0}/100 - {getConfidenceLabel(result.confidence_score || 0)}
                  </div>
                </div>

                {/* Risk Score Section */}
                {result.risk_score !== undefined && (
                  <div className="risk-section">
                    <div className="risk-header">
                      <span className="risk-label">Risk Assessment</span>
                      <span 
                        className="risk-badge"
                        style={{ backgroundColor: getRiskLevelColor(result.risk_level) }}
                      >
                        {getRiskLevelLabel(result.risk_level)} Risk
                      </span>
                    </div>
                    <div className="risk-score">Score: {result.risk_score}/100</div>
                    {result.risk_factors && result.risk_factors.length > 0 && (
                      <div className="risk-factors">
                        <strong>Risk Factors:</strong>
                        <ul>
                          {result.risk_factors.map((factor, idx) => (
                            <li key={idx}>{factor}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Enrichment Data Section */}
                {result.enrichment && (
                  <div className="enrichment-section">
                    <h3>📧 Email Intelligence</h3>
                    <div className="enrichment-grid">
                      {result.enrichment.domain_type && (
                        <div className="enrichment-item">
                          <span className="enrichment-label">Domain Type:</span>
                          <span className="enrichment-value">{result.enrichment.domain_type}</span>
                        </div>
                      )}
                      {result.enrichment.country && (
                        <div className="enrichment-item">
                          <span className="enrichment-label">Country:</span>
                          <span className="enrichment-value">{result.enrichment.country}</span>
                        </div>
                      )}
                      {result.enrichment.engagement_score !== undefined && (
                        <div className="enrichment-item">
                          <span className="enrichment-label">Engagement Score:</span>
                          <span className="enrichment-value">{result.enrichment.engagement_score}/100</span>
                        </div>
                      )}
                      {result.enrichment.company_name && (
                        <div className="enrichment-item">
                          <span className="enrichment-label">Company:</span>
                          <span className="enrichment-value">{result.enrichment.company_name}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="checks-grid">
                  <div className={`check-item ${result.checks.syntax ? 'pass' : 'fail'}`}>
                    <span className="check-icon">{result.checks.syntax ? '✓' : '✗'}</span>
                    <span>Syntax</span>
                  </div>
                  <div className={`check-item ${result.checks.dns_valid ? 'pass' : 'fail'}`}>
                    <span className="check-icon">{result.checks.dns_valid ? '✓' : '✗'}</span>
                    <span>DNS</span>
                  </div>
                  <div className={`check-item ${result.checks.mx_records ? 'pass' : 'fail'}`}>
                    <span className="check-icon">{result.checks.mx_records ? '✓' : '✗'}</span>
                    <span>MX Records</span>
                  </div>
                  <div className={`check-item ${!result.checks.is_disposable ? 'pass' : 'warn'}`}>
                    <span className="check-icon">{!result.checks.is_disposable ? '✓' : '⚠'}</span>
                    <span>Not Disposable</span>
                  </div>
                  <div className={`check-item ${!result.checks.is_role_based ? 'pass' : 'warn'}`}>
                    <span className="check-icon">{!result.checks.is_role_based ? '✓' : '⚠'}</span>
                    <span>Not Role-Based</span>
                  </div>
                </div>

                {result.suggestion && (
                  <div className="suggestion-box">
                    <strong>💡 Suggestion:</strong> Did you mean <strong>{result.suggestion}</strong>?
                  </div>
                )}

                {result.reason && (
                  <div className="reason-box">
                    <strong>Details:</strong> {result.reason}
                  </div>
                )}
              </>
            )}

            {mode === 'advanced' && !result.checks && (
              <div className="info-box">
                <strong>ℹ️ Note:</strong> This result is from Basic mode. Click "Validate" again to get Advanced validation with confidence score and detailed checks.
              </div>
            )}

            <div className="meta-info">
              Processing time: {result.processing_time}s
            </div>
          </div>
        )}

        {batchResults && (
          <div className="batch-results">
            <div className="batch-summary">
              <div className="batch-header">
                <h2>Batch Results</h2>
                <div className="export-buttons">
                  <button className="export-btn" onClick={exportToCSV} title="Export to CSV">
                    📥 Export CSV
                  </button>
                  <button className="export-btn" onClick={copyToClipboard} title="Copy to Clipboard">
                    📋 Copy
                  </button>
                </div>
              </div>
              <div className="summary-stats">
                <div className="stat">
                  <span className="stat-value">{batchResults.total}</span>
                  <span className="stat-label">Total</span>
                </div>
                <div className="stat valid">
                  <span className="stat-value">{batchResults.valid_count}</span>
                  <span className="stat-label">Valid</span>
                </div>
                <div className="stat invalid">
                  <span className="stat-value">{batchResults.invalid_count}</span>
                  <span className="stat-label">Invalid</span>
                </div>
              </div>
              <div className="meta-info">
                Processing time: {batchResults.processing_time}s
              </div>
            </div>

            <div className="batch-list">
              {batchResults.results.map((item, index) => (
                <div key={index} className={`batch-item ${item.valid ? 'valid' : 'invalid'}`}>
                  <span className="batch-icon">{item.valid ? '✓' : '✗'}</span>
                  <span className="batch-email">{item.email}</span>
                  {mode === 'advanced' && (
                    <span className="batch-score">
                      Score: {item.confidence_score}
                    </span>
                  )}
                  {mode === 'advanced' && item.suggestion && (
                    <span className="batch-suggestion">
                      → {item.suggestion}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="history-section">
            <div className="history-header">
              <h2>📜 Validation History</h2>
              <div className="history-controls">
                <button className="refresh-btn" onClick={loadValidationHistory} disabled={historyLoading}>
                  {historyLoading ? '⏳ Loading...' : '🔄 Refresh'}
                </button>
                {validationHistory.length > 0 && (
                  <button className="clear-btn" onClick={clearHistory}>
                    🗑️ Clear History
                  </button>
                )}
              </div>
            </div>

            <div className="info-box" style={{ margin: '0 32px 20px' }}>
              <strong>🔐 Private History:</strong> Your validation history is stored securely and linked to your anonymous ID. 
              Only you can see your history - no login required!
              <br />
              <small style={{ opacity: 0.8 }}>Anonymous ID: {anonUserId.substring(0, 8)}...</small>
            </div>

            {historyLoading ? (
              <div className="loading-state">Loading history...</div>
            ) : validationHistory.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📭</div>
                <p>No validation history yet</p>
                <small>Start validating emails to see them here</small>
              </div>
            ) : (
              <>
                <div className="history-stats">
                  <span>📊 {validationHistory.length} validation{validationHistory.length !== 1 ? 's' : ''} in your history</span>
                </div>
                <div className="history-list">
                  {validationHistory.map((item, index) => (
                    <div key={item.id || index} className={`history-item ${item.valid ? 'valid' : 'invalid'}`}>
                      <div className="history-main">
                        <span className="history-icon">{item.valid ? '✓' : '✗'}</span>
                        <div className="history-details">
                          <div className="history-email">{item.email}</div>
                          <div className="history-meta">
                            {formatDate(item.validated_at)} • 
                            Score: {item.confidence_score || 'N/A'}
                            {item.risk_level && (
                              <>
                                {' • '}
                                Risk: <span style={{ color: getRiskLevelColor(item.risk_level) }}>
                                  {getRiskLevelLabel(item.risk_level)}
                                </span>
                              </>
                            )}
                          </div>
                        </div>

                      </div>
                      {item.enrichment && (
                        <div className="history-enrichment">
                          {item.enrichment.domain_type && (
                            <span className="enrichment-tag">{item.enrichment.domain_type}</span>
                          )}
                          {item.enrichment.country && (
                            <span className="enrichment-tag">🌍 {item.enrichment.country}</span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="analytics-section">
            <div className="analytics-header">
              <h2>📊 Analytics Dashboard</h2>
              <button className="refresh-btn" onClick={loadAnalytics} disabled={historyLoading}>
                {historyLoading ? '⏳ Loading...' : '🔄 Refresh'}
              </button>
            </div>

            {historyLoading ? (
              <div className="loading-state">Loading analytics...</div>
            ) : !analytics ? (
              <div className="empty-state">
                <div className="empty-icon">📊</div>
                <p>No analytics data available</p>
                <small>Validate some emails to see analytics</small>
              </div>
            ) : (
              <>
                <div className="analytics-grid">
                  <div className="analytics-card">
                    <div className="analytics-value">{analytics.total_validations || 0}</div>
                    <div className="analytics-label">Total Validations</div>
                  </div>
                  <div className="analytics-card valid">
                    <div className="analytics-value">{analytics.valid_count || 0}</div>
                    <div className="analytics-label">Valid Emails</div>
                  </div>
                  <div className="analytics-card invalid">
                    <div className="analytics-value">{analytics.invalid_count || 0}</div>
                    <div className="analytics-label">Invalid Emails</div>
                  </div>
                  <div className="analytics-card">
                    <div className="analytics-value">
                      {analytics.total_validations > 0 
                        ? Math.round((analytics.valid_count / analytics.total_validations) * 100) 
                        : 0}%
                    </div>
                    <div className="analytics-label">Success Rate</div>
                  </div>
                </div>

                {analytics.risk_distribution && (
                  <div className="risk-distribution">
                    <h3>Risk Distribution</h3>
                    <div className="risk-bars">
                      {Object.entries(analytics.risk_distribution).map(([level, count]) => (
                        <div key={level} className="risk-bar-item">
                          <div className="risk-bar-label">
                            <span>{getRiskLevelLabel(level)}</span>
                            <span>{count}</span>
                          </div>
                          <div className="risk-bar-container">
                            <div 
                              className="risk-bar-fill"
                              style={{
                                width: `${(count / analytics.total_validations) * 100}%`,
                                backgroundColor: getRiskLevelColor(level)
                              }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {analytics.domain_types && (
                  <div className="domain-types">
                    <h3>Domain Types</h3>
                    <div className="domain-type-grid">
                      {Object.entries(analytics.domain_types).map(([type, count]) => (
                        <div key={type} className="domain-type-card">
                          <div className="domain-type-count">{count}</div>
                          <div className="domain-type-label">{type}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {analytics.top_domains && analytics.top_domains.length > 0 && (
                  <div className="top-domains">
                    <h3>Top Domains</h3>
                    <div className="top-domains-list">
                      {analytics.top_domains.map((item, idx) => (
                        <div key={idx} className="top-domain-item">
                          <span className="domain-rank">#{idx + 1}</span>
                          <span className="domain-name">{item.domain}</span>
                          <span className="domain-count">{item.count} emails</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
        </>
        )}

        <footer className="footer">
          <p>Powered by RFC 5321 compliant validation engine with AI-powered risk scoring</p>
          <p>Features: DNS • MX • SMTP • Risk Scoring • Email Enrichment • Bounce Tracking</p>
        </footer>
      </div>
    </div>
  );
}

export default App;

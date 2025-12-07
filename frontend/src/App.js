import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { 
  FiMail, FiSun, FiMoon, FiRefreshCw, 
  FiTrash2, FiDownload, FiCopy
} from 'react-icons/fi';

// ============================================================================
// ANONYMOUS USER ID SYSTEM
// ============================================================================

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

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
  const [mode, setMode] = useState('advanced');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [batchMode, setBatchMode] = useState(false);
  const [historyMode, setHistoryMode] = useState(false);
  const [batchEmails, setBatchEmails] = useState('');
  const [batchResults, setBatchResults] = useState(null);
  const [uploadMode, setUploadMode] = useState('text');
  const [selectedFile, setSelectedFile] = useState(null);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });
  
  const [history, setHistory] = useState([]);
  const [filteredHistory, setFilteredHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [historyLoading, setHistoryLoading] = useState(false);
  
  const [anonUserId] = useState(() => getAnonUserId());

  const API_URL = process.env.NODE_ENV === 'production' 
    ? ''
    : 'http://localhost:5000';
  
  const api = axios.create({
    baseURL: API_URL,
    headers: {
      'X-User-ID': anonUserId
    }
  });

  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem('darkMode', JSON.stringify(newMode));
    document.body.classList.toggle('dark-mode', newMode);
  };

  useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode);
  }, [darkMode]);

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
      const response = await api.post('/api/validate', { 
        email,
        advanced: mode === 'advanced'
      });
      
      setResult(response.data);
      
      // Refresh history if on history tab
      if (historyMode) {
        loadHistory();
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
      
      const reader = new FileReader();
      reader.onload = (event) => {
        setBatchEmails(event.target.result);
      };
      reader.readAsText(file);
    }
  };

  const parseEmails = (text) => {
    // Smart email parser that handles:
    // - Newlines
    // - Commas
    // - Semicolons
    // - Quotes
    // - Extra whitespace
    
    let emails = [];
    
    // First split by newlines, commas, and semicolons
    const parts = text.split(/[\n,;]+/);
    
    parts.forEach(part => {
      // Remove quotes and extra whitespace
      let cleaned = part
        .replace(/["']/g, '')  // Remove quotes
        .trim();
      
      // Check if it looks like an email
      if (cleaned && cleaned.includes('@')) {
        emails.push(cleaned);
      }
    });
    
    // Remove duplicates
    return [...new Set(emails)];
  };

  const validateBatch = async () => {
    const emails = parseEmails(batchEmails);

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
      if (historyMode) {
        loadHistory();
      }
    } catch (err) {
      const errorMsg = err.response?.data?.message 
        || err.message 
        || 'Batch validation failed';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await api.get('/api/history?limit=100');
      setHistory(response.data.history || []);
      setFilteredHistory(response.data.history || []);
    } catch (err) {
      setError('Failed to load history');
    } finally {
      setHistoryLoading(false);
    }
  };



  const filterHistory = () => {
    let filtered = [...history];
    
    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(item => 
        item.email.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(item => {
        if (statusFilter === 'valid') return item.valid;
        if (statusFilter === 'invalid') return !item.valid;
        if (statusFilter === 'disposable') return item.checks?.is_disposable;
        return true;
      });
    }
    
    setFilteredHistory(filtered);
  };

  const deleteHistoryItem = async (id) => {
    if (!window.confirm('Delete this record?')) return;
    
    try {
      await api.delete(`/api/history/${id}`);
      // Auto-refresh after delete
      await loadHistory();
    } catch (err) {
      alert('Failed to delete record');
    }
  };

  const clearAllHistory = async () => {
    if (!window.confirm('Clear ALL history? This cannot be undone!')) return;
    
    try {
      await api.delete('/api/history');
      // Immediately clear UI
      setHistory([]);
      setFilteredHistory([]);
      alert('History cleared');
    } catch (err) {
      alert('Failed to clear history');
    }
  };

  useEffect(() => {
    if (historyMode) {
      filterHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, statusFilter, history]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !batchMode && !historyMode) {
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



  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <div className="header-content">
            <div>
              <h1><FiMail className="header-icon" /> Email Validator</h1>
              <p>Advanced email validation with DNS, MX, and disposable detection</p>
            </div>
            <button className="dark-mode-toggle" onClick={toggleDarkMode} title="Toggle Dark Mode">
              {darkMode ? <FiSun /> : <FiMoon />}
            </button>
          </div>
        </header>

        <div className="mode-selector">
          <button
            className={`mode-btn ${!batchMode && !historyMode ? 'active' : ''}`}
            onClick={() => {
              setBatchMode(false);
              setHistoryMode(false);
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
              setHistoryMode(false);
              setResult(null);
              setBatchResults(null);
              setError(null);
            }}
          >
            Batch Validation
          </button>
          <button
            className={`mode-btn ${historyMode ? 'active' : ''}`}
            onClick={() => {
              setHistoryMode(true);
              setBatchMode(false);
              setResult(null);
              setBatchResults(null);
              setError(null);
              loadHistory();
            }}
          >
            History
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
                setResult(null);
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
                setResult(null);
                setError(null);
              }}
            />
            <span>Advanced - Full Check (DNS, MX, Disposable)</span>
          </label>
        </div>



        {historyMode ? (
          <div className="history-section">
            <div className="history-controls">
              <input
                type="text"
                className="history-search"
                placeholder="Search emails..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <select
                className="history-filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All Status</option>
                <option value="valid">Valid Only</option>
                <option value="invalid">Invalid Only</option>
                <option value="disposable">Disposable Only</option>
              </select>
              <button className="refresh-btn" onClick={loadHistory}>
                <FiRefreshCw /> Refresh
              </button>
              <button className="clear-all-btn" onClick={clearAllHistory}>
                <FiTrash2 /> Clear All
              </button>
            </div>

            {historyLoading ? (
              <div className="loading-message">Loading history...</div>
            ) : filteredHistory.length === 0 ? (
              <div className="empty-history">
                <p>No validation history yet</p>
                <p>Validate some emails to see them here!</p>
              </div>
            ) : (
              <div className="history-table-container">
                <table className="history-table">
                  <thead>
                    <tr>
                      <th>Email</th>
                      <th>Status</th>
                      <th>Score</th>
                      <th>Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredHistory.map((item, index) => (
                      <tr key={index}>
                        <td className="email-cell">{item.email}</td>
                        <td>
                          <span className={`table-status-badge ${item.valid ? 'valid' : 'invalid'}`}>
                            {item.valid ? 'Valid' : 'Invalid'}
                          </span>
                        </td>
                        <td>{item.confidence_score || 0}/100</td>
                        <td>{new Date(item.validated_at).toLocaleDateString()}</td>
                        <td>
                          <button
                            className="table-action-btn delete"
                            onClick={() => deleteHistoryItem(item.id)}
                            title="Delete"
                          >
                            <FiTrash2 />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="history-summary">
                  Showing {filteredHistory.length} of {history.length} records
                </div>
              </div>
            )}
          </div>
        ) : !batchMode ? (
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
              <>
                <div className="format-info">
                  💡 Paste emails in any format: one per line, comma-separated, or from Excel
                </div>
                <textarea
                  className="batch-input"
                  placeholder="Enter email addresses (one per line, comma-separated, or any format)..."
                  value={batchEmails}
                  onChange={(e) => setBatchEmails(e.target.value)}
                  disabled={loading}
                  rows={10}
                />
              </>
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
                    <strong>Preview ({parseEmails(batchEmails).length} emails detected):</strong>
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
              <div className="result-title-row">
                <h2>{result.valid ? 'Valid Email' : 'Invalid Email'}</h2>
                {result.status && (
                  <span className={`status-badge status-${result.status.color}`}>
                    {result.status.status.toUpperCase()}
                  </span>
                )}
              </div>
              <span className="email-display">{result.email}</span>
              {result.status && result.status.description && (
                <span className="status-description">{result.status.description}</span>
              )}
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

                {result.deliverability && (
                  <div className="deliverability-section">
                    <div className="deliverability-header">
                      <span className="deliverability-label">Deliverability Score</span>
                      <span 
                        className="deliverability-grade"
                        style={{ 
                          backgroundColor: result.deliverability.deliverability_score >= 80 ? '#10b981' : 
                                         result.deliverability.deliverability_score >= 60 ? '#f59e0b' : '#ef4444'
                        }}
                      >
                        Grade: {result.deliverability.deliverability_grade}
                      </span>
                    </div>
                    <div className="deliverability-score">{result.deliverability.deliverability_score}/100</div>
                    <div className="deliverability-recommendation">
                      {result.deliverability.recommendation}
                    </div>
                    {result.deliverability.pattern_analysis && result.deliverability.pattern_analysis.flags && (
                      <div className="pattern-flags">
                        {result.deliverability.pattern_analysis.flags.map((flag, idx) => (
                          <span key={idx} className="pattern-flag">{flag}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}



                {result.risk_check && result.risk_check.overall_risk !== 'low' && (
                  <div className={`risk-warning-section ${result.risk_check.overall_risk}`}>
                    <h3>Risk Detection</h3>
                    <div className="risk-warning-content">
                      <div className="risk-level">
                        Risk Level: <strong>{result.risk_check.overall_risk.toUpperCase()}</strong>
                      </div>
                      <div className="risk-recommendation">
                        {result.risk_check.recommendation}
                      </div>
                      {result.risk_check.risk_factors && result.risk_check.risk_factors.length > 0 && (
                        <div className="risk-factors-list">
                          <strong>Detected Issues:</strong>
                          <ul>
                            {result.risk_check.risk_factors.map((factor, idx) => (
                              <li key={idx}>{factor}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {result.bounce_check && result.bounce_check.bounce_history.has_bounced && (
                  <div className={`bounce-warning-section ${result.bounce_check.risk_level}`}>
                    <h3>Bounce History</h3>
                    <div className="bounce-warning-content">
                      <div className="bounce-stats">
                        <div className="bounce-stat">
                          <strong>{result.bounce_check.bounce_history.total_bounces}</strong>
                          <span>Total Bounces</span>
                        </div>
                        <div className="bounce-stat">
                          <strong>{result.bounce_check.bounce_history.hard_bounces}</strong>
                          <span>Hard Bounces</span>
                        </div>
                        <div className="bounce-stat">
                          <strong>{result.bounce_check.bounce_history.soft_bounces}</strong>
                          <span>Soft Bounces</span>
                        </div>
                      </div>
                      {result.bounce_check.warning && (
                        <div className="bounce-warning">
                          {result.bounce_check.warning}
                        </div>
                      )}
                    </div>
                  </div>
                )}

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
                    <FiDownload /> Export CSV
                  </button>
                  <button className="export-btn" onClick={copyToClipboard} title="Copy to Clipboard">
                    <FiCopy /> Copy
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
                <div key={index} className={`batch-item ${item.valid ? 'valid' : 'invalid'} ${mode === 'advanced' ? 'detailed' : ''}`}>
                  <div className="batch-item-header">
                    <span className="batch-icon">{item.valid ? '✓' : '✗'}</span>
                    <span className="batch-email">{item.email}</span>
                    {item.status && (
                      <span className={`batch-status-badge status-${item.status.color}`}>
                        {item.status.status}
                      </span>
                    )}
                    {mode === 'advanced' && item.confidence_score !== undefined && (
                      <span className="batch-score">
                        {item.confidence_score}/100
                      </span>
                    )}
                  </div>
                  
                  {mode === 'advanced' && item.checks && (
                    <div className="batch-item-details">
                      <div className="batch-checks">
                        {item.checks.syntax !== undefined && (
                          <span className={`mini-check ${item.checks.syntax ? 'pass' : 'fail'}`}>
                            {item.checks.syntax ? '✓' : '✗'} Syntax
                          </span>
                        )}
                        {item.checks.dns_valid !== undefined && (
                          <span className={`mini-check ${item.checks.dns_valid ? 'pass' : 'fail'}`}>
                            {item.checks.dns_valid ? '✓' : '✗'} DNS
                          </span>
                        )}
                        {item.checks.mx_records !== undefined && (
                          <span className={`mini-check ${item.checks.mx_records ? 'pass' : 'fail'}`}>
                            {item.checks.mx_records ? '✓' : '✗'} MX
                          </span>
                        )}
                        {item.checks.is_disposable !== undefined && item.checks.is_disposable && (
                          <span className="mini-check warn">⚠ Disposable</span>
                        )}
                        {item.checks.is_role_based !== undefined && item.checks.is_role_based && (
                          <span className="mini-check warn">⚠ Role-based</span>
                        )}
                      </div>
                      {item.suggestion && (
                        <div className="batch-suggestion">
                          💡 Did you mean: <strong>{item.suggestion}</strong>
                        </div>
                      )}
                      {item.reason && (
                        <div className="batch-reason">
                          {item.reason}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {mode === 'basic' && item.suggestion && (
                    <span className="batch-suggestion">
                      → {item.suggestion}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <footer className="footer">
          <p>Powered by RFC 5321 compliant validation engine with AI-powered analysis</p>
          <p>Features: DNS • MX • Pattern Analysis • Email Enrichment • Deliverability Scoring</p>
        </footer>
      </div>
    </div>
  );
}

export default App;

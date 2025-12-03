 import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

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

  // API URL - use relative path in production, localhost in development
  const API_URL = process.env.NODE_ENV === 'production' 
    ? ''  // Empty string for relative URLs in production
    : 'http://localhost:5000';  // Localhost for development

  // Toggle dark mode 
  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem('darkMode', JSON.stringify(newMode));
    document.body.classList.toggle('dark-mode', newMode);
  };

  // Apply dark mode on mount
  React.useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode);
  }, [darkMode]);

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
        ? `${API_URL}/api/validate/advanced`
        : `${API_URL}/api/validate`;

      const response = await axios.post(endpoint, { email });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Validation failed');
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
      const response = await axios.post(`${API_URL}/api/validate/batch`, {
        emails,
        advanced: mode === 'advanced'
      });
      setBatchResults(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Batch validation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
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
              onKeyPress={handleKeyPress}
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

        <footer className="footer">
          <p>Powered by RFC 5321 compliant validation engine</p>
          <p>Features: DNS checking • MX verification • Disposable detection • Typo suggestions</p>
        </footer>
      </div>
    </div>
  );
}

export default App;

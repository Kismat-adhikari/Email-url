import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import { 
  FiMail, FiRefreshCw, 
  FiTrash2, FiDownload, FiCopy
} from 'react-icons/fi';

// ============================================================================
// ANONYMOUS USER ID SYSTEM
// ============================================================================

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : ((r & 0x3) | 0x8);
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
  const navigate = useNavigate();
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
  const [removeDuplicates, setRemoveDuplicates] = useState(true);
  const [showDomainStats, setShowDomainStats] = useState(true);
  const [progress, setProgress] = useState({ current: 0, total: 0, percentage: 0, eta: 0, speed: 0 });
  const [shareLink, setShareLink] = useState(null);
  const [showShareModal, setShowShareModal] = useState(false);
  
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

  useEffect(() => {
    // Remove any dark mode class on mount
    document.body.classList.remove('dark-mode');
  }, []);

  const exportToCSV = () => {
    if (!batchResults || !batchResults.results) return;

    const headers = mode === 'advanced' 
      ? [
          'Email', 'Valid', 'Confidence Score', 'Deliverability Score', 'Deliverability Grade',
          'Status', 'Risk Level', 'Domain', 'Provider Type', 
          'Is Disposable', 'Is Role Based', 'Has MX Records', 'DNS Valid',
          'Bounce Risk', 'Reason', 'Suggestion'
        ]
      : ['Email', 'Valid', 'Domain', 'Reason'];

    const rows = batchResults.results.map(r => {
      const domain = r.email.includes('@') ? r.email.split('@')[1] : '';
      
      if (mode === 'advanced') {
        return [
          r.email,
          r.valid ? 'Yes' : 'No',
          r.confidence_score || 'N/A',
          r.deliverability?.deliverability_score || 'N/A',
          r.deliverability?.deliverability_grade || 'N/A',
          r.status?.status || 'N/A',
          r.risk_check?.overall_risk || 'N/A',
          domain,
          r.enrichment?.domain_type || 'N/A',
          r.checks?.is_disposable ? 'Yes' : 'No',
          r.checks?.is_role_based ? 'Yes' : 'No',
          r.checks?.mx_records ? 'Yes' : 'No',
          r.checks?.dns_valid ? 'Yes' : 'No',
          r.bounce_check?.risk_level || 'N/A',
          r.reason || '',
          r.suggestion || ''
        ];
      } else {
        return [
          r.email, 
          r.valid ? 'Yes' : 'No',
          domain,
          r.reason || ''
        ];
      }
    });

    // Add summary section at the top
    const summary = [
      ['Email Validation Report'],
      ['Generated:', new Date().toLocaleString()],
      ['Total Emails:', batchResults.total],
      ['Valid:', batchResults.valid_count],
      ['Invalid:', batchResults.invalid_count],
      ['Duplicates Removed:', batchResults.duplicates_removed || 0],
      ['Processing Time:', `${batchResults.processing_time}s`],
      [''],
      ['']
    ];

    // Add domain stats if available
    if (batchResults.domain_stats && batchResults.domain_stats.top_domains) {
      summary.push(['Top Domains:']);
      summary.push(['Domain', 'Count', 'Percentage', 'Valid Rate']);
      batchResults.domain_stats.top_domains.slice(0, 5).forEach(d => {
        summary.push([d.domain, d.count, `${d.percentage}%`, `${d.validity_rate}%`]);
      });
      summary.push(['']);
      summary.push(['']);
    }

    const csvContent = [
      ...summary.map(row => row.map(cell => `"${cell}"`).join(',')),
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `email-validation-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const exportToJSON = () => {
    if (!batchResults || !batchResults.results) return;

    const exportData = {
      metadata: {
        generated_at: new Date().toISOString(),
        total_emails: batchResults.total,
        valid_count: batchResults.valid_count,
        invalid_count: batchResults.invalid_count,
        duplicates_removed: batchResults.duplicates_removed || 0,
        processing_time: batchResults.processing_time,
        validation_mode: mode
      },
      domain_statistics: batchResults.domain_stats || null,
      results: batchResults.results
    };

    const jsonString = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `email-validation-${Date.now()}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const generateShareLink = () => {
    if (!batchResults || !batchResults.results) return;

    // Create shareable data
    const shareData = {
      metadata: {
        generated_at: new Date().toISOString(),
        total_emails: batchResults.total,
        valid_count: batchResults.valid_count,
        invalid_count: batchResults.invalid_count,
        duplicates_removed: batchResults.duplicates_removed || 0,
        processing_time: batchResults.processing_time,
        validation_mode: mode
      },
      domain_statistics: batchResults.domain_stats || null,
      results: batchResults.results
    };

    // Generate unique ID
    const shareId = `share_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Store in localStorage (in production, this would be a backend API call)
    localStorage.setItem(shareId, JSON.stringify(shareData));
    
    // Generate shareable URL
    const shareUrl = `${window.location.origin}${window.location.pathname}?share=${shareId}`;
    setShareLink(shareUrl);
    setShowShareModal(true);
  };

  const copyShareLink = () => {
    if (!shareLink) return;
    
    navigator.clipboard.writeText(shareLink).then(() => {
      alert('✓ Share link copied to clipboard!');
    }).catch(() => {
      alert('Failed to copy link');
    });
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
      // Accept multiple file types
      const allowedTypes = [
        'text/plain',
        'text/csv',
        'application/pdf',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      ];
      
      const allowedExtensions = ['.txt', '.csv', '.pdf', '.xls', '.xlsx', '.doc', '.docx'];
      const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      
      if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
        setError('Please select a valid file (.txt, .csv, .pdf, .doc, .docx, .xls, .xlsx)');
        return;
      }
      
      setSelectedFile(file);
      setError(null);
      
      // For text and CSV files, read directly
      if (file.type === 'text/plain' || file.type === 'text/csv' || fileExtension === '.txt' || fileExtension === '.csv') {
        const reader = new FileReader();
        reader.onload = (event) => {
          setBatchEmails(event.target.result);
        };
        reader.readAsText(file);
      } else {
        // For other file types, show a message that we'll extract emails
        setBatchEmails(`📄 File loaded: ${file.name}\n\nEmails will be extracted automatically when you click "Validate Batch".\n\nSupported formats: PDF, Word, Excel`);
      }
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
    
    return emails;
  };

  const detectDuplicates = (emails) => {
    const seen = new Set();
    const duplicates = [];
    const unique = [];
    
    emails.forEach(email => {
      const emailLower = email.toLowerCase().trim();
      if (seen.has(emailLower)) {
        duplicates.push(email);
      } else {
        seen.add(emailLower);
        unique.push(email);
      }
    });
    
    return {
      total: emails.length,
      unique: unique.length,
      duplicates: duplicates.length,
      duplicateList: duplicates
    };
  };

  const validateBatch = async () => {
    const emails = parseEmails(batchEmails);

    if (emails.length === 0) {
      setError('Please enter at least one email address or upload a file');
      return;
    }

    // Detect duplicates for display
    detectDuplicates(emails);

    const startTime = Date.now();
    setLoading(true);
    setError(null);
    setBatchResults({ results: [], total: emails.length, valid_count: 0, invalid_count: 0 });
    setProgress({ current: 0, total: emails.length, percentage: 0, eta: 0, speed: 0 });

    try {
      const response = await fetch(`${API_URL}/api/validate/batch/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': anonUserId
        },
        body: JSON.stringify({
          emails,
          advanced: mode === 'advanced',
          remove_duplicates: removeDuplicates
        })
      });

      if (!response.ok) {
        throw new Error('Stream validation failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === 'start') {
              // Duplicate info is handled by backend
            } else if (data.type === 'result') {
              // Calculate ETA and speed
              const elapsed = (Date.now() - startTime) / 1000; // seconds
              const current = data.progress.current;
              const total = data.progress.total;
              const speed = current / elapsed; // emails per second
              const remaining = total - current;
              const eta = remaining / speed; // seconds

              // Update progress
              setProgress({
                current,
                total,
                percentage: data.progress.percentage,
                eta: Math.ceil(eta),
                speed: speed.toFixed(1)
              });

              // Add result to the list in real-time
              setBatchResults(prev => ({
                ...prev,
                results: [...prev.results, data.result],
                valid_count: data.progress.valid,
                invalid_count: data.progress.invalid,
                total: data.progress.total
              }));
            } else if (data.type === 'complete') {
              // Calculate actual processing time
              const processingTime = ((Date.now() - startTime) / 1000).toFixed(1);
              
              // Final progress update
              setProgress({
                current: data.total,
                total: data.total,
                percentage: 100,
                eta: 0,
                speed: (data.total / parseFloat(processingTime)).toFixed(1)
              });
              
              // Final update
              setBatchResults(prev => ({
                ...prev,
                valid_count: data.valid_count,
                invalid_count: data.invalid_count,
                total: data.total,
                original_count: data.original_count,
                duplicates_removed: data.duplicates_removed,
                domain_stats: data.domain_stats,
                processing_time: processingTime
              }));
            }
          }
        }
      }
      
      // Refresh history if on history tab
      if (historyMode) {
        loadHistory();
      }
    } catch (err) {
      const errorMsg = err.message || 'Batch validation failed';
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

  const exportHistoryToCSV = () => {
    if (!filteredHistory || filteredHistory.length === 0) {
      alert('No history to export');
      return;
    }

    const headers = [
      'Email', 'Valid', 'Confidence Score', 'Date', 
      'Is Disposable', 'Is Role Based', 'Has MX Records'
    ];

    const rows = filteredHistory.map(item => [
      item.email,
      item.valid ? 'Yes' : 'No',
      item.confidence_score || 'N/A',
      new Date(item.validated_at).toLocaleString(),
      item.checks?.is_disposable ? 'Yes' : 'No',
      item.checks?.is_role_based ? 'Yes' : 'No',
      item.checks?.mx_records ? 'Yes' : 'No'
    ]);

    const summary = [
      ['Email Validation History'],
      ['Exported:', new Date().toLocaleString()],
      ['Total Records:', filteredHistory.length],
      [''],
      ['']
    ];

    const csvContent = [
      ...summary.map(row => row.map(cell => `"${cell}"`).join(',')),
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `email-history-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
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
              <h1>
                <FiMail className="header-icon" /> Email Validator
                <span className="lagic-badge">LAGIC</span>
              </h1>
              <p>Advanced email validation with DNS, MX, and disposable detection</p>
            </div>
            <div>
              <button className="landing-btn" onClick={() => navigate('/testing')}>
                🚀 Landing Page
              </button>
            </div>
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
              <button className="export-btn csv" onClick={() => exportHistoryToCSV()}>
                <FiDownload /> CSV
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
          <>
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
                Validate
              </button>
            </div>
            
            {loading && !batchMode && (
              <div className="single-loading">
                <div className="loading-spinner"></div>
                <span>Validating email...</span>
              </div>
            )}
          </>
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

            <div className="duplicate-control">
              <label className="duplicate-checkbox">
                <input
                  type="checkbox"
                  checked={removeDuplicates}
                  onChange={(e) => setRemoveDuplicates(e.target.checked)}
                />
                <span>🔄 Automatically remove duplicate emails</span>
              </label>
              {batchEmails && (() => {
                const emails = parseEmails(batchEmails);
                const dupInfo = detectDuplicates(emails);
                if (dupInfo.duplicates > 0) {
                  return (
                    <div className="duplicate-warning">
                      ⚠️ Found {dupInfo.duplicates} duplicate{dupInfo.duplicates > 1 ? 's' : ''} out of {dupInfo.total} emails
                      {removeDuplicates && ` (will be removed automatically)`}
                    </div>
                  );
                }
                return null;
              })()}
            </div>

            {uploadMode === 'text' ? (
              <>
                <div className="format-info">
                  💡 Paste emails in any format: one per line, comma-separated, or copy from Excel/Sheets
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
                    accept=".txt,.csv,.pdf,.doc,.docx,.xls,.xlsx"
                    onChange={handleFileSelect}
                    disabled={loading}
                    style={{ display: 'none' }}
                  />
                  <label htmlFor="file-input" className="file-upload-label">
                    <div className="upload-icon">📎</div>
                    <div className="upload-text">
                      {selectedFile ? (
                        <>
                          <strong>{selectedFile.name}</strong>
                          <br />
                          <small>Click to change file</small>
                        </>
                      ) : (
                        <>
                          <strong>Click to upload file</strong>
                          <br />
                          <small>Supports: TXT, CSV, PDF, Word, Excel</small>
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

        {loading && batchMode && progress.total > 0 && (
          <div className="progress-container">
            <div className="progress-header">
              <span className="progress-text">
                Processing {progress.current} of {progress.total} emails ({progress.percentage}%)
              </span>
              <span className="progress-stats">
                {progress.speed} emails/sec • ETA: {progress.eta}s
              </span>
            </div>
            <div className="progress-bar-wrapper">
              <div 
                className="progress-bar-fill" 
                style={{ width: `${progress.percentage}%` }}
              >
                <span className="progress-bar-text">{progress.percentage}%</span>
              </div>
            </div>
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
                  <button className="export-btn csv" onClick={exportToCSV} title="Export to CSV (Excel-ready)">
                    <FiDownload /> CSV
                  </button>
                  <button className="export-btn json" onClick={exportToJSON} title="Export to JSON (Full data)">
                    <FiDownload /> JSON
                  </button>
                  <button className="export-btn copy" onClick={copyToClipboard} title="Copy to Clipboard">
                    <FiCopy /> Copy
                  </button>
                  <button className="export-btn share" onClick={generateShareLink} title="Generate shareable link">
                    🔗 Share
                  </button>
                </div>
              </div>
              {batchResults.duplicates_removed > 0 && (
                <div className="duplicate-info-banner">
                  🔄 Removed {batchResults.duplicates_removed} duplicate email{batchResults.duplicates_removed > 1 ? 's' : ''} 
                  {batchResults.original_count && ` (${batchResults.original_count} → ${batchResults.total})`}
                </div>
              )}
              <div className="summary-stats">
                <div className="stat">
                  <span className="stat-value">{batchResults.total}</span>
                  <span className="stat-label">Validated</span>
                </div>
                <div className="stat valid">
                  <span className="stat-value">{batchResults.valid_count}</span>
                  <span className="stat-label">Valid</span>
                </div>
                <div className="stat invalid">
                  <span className="stat-value">{batchResults.invalid_count}</span>
                  <span className="stat-label">Invalid</span>
                </div>
                {batchResults.duplicates_removed > 0 && (
                  <div className="stat duplicate">
                    <span className="stat-value">{batchResults.duplicates_removed}</span>
                    <span className="stat-label">Duplicates</span>
                  </div>
                )}
              </div>
              <div className="meta-info">
                Processing time: {batchResults.processing_time}s
              </div>
            </div>

            {batchResults.domain_stats && (
              <div className="domain-stats-section">
                <div className="domain-stats-header">
                  <h3>📊 Domain Statistics</h3>
                  <button 
                    className="toggle-stats-btn"
                    onClick={() => setShowDomainStats(!showDomainStats)}
                  >
                    {showDomainStats ? '▼ Hide' : '▶ Show'}
                  </button>
                </div>

                {showDomainStats && (
                  <>
                    {/* Provider Distribution */}
                    {batchResults.domain_stats.provider_distribution && Object.keys(batchResults.domain_stats.provider_distribution).length > 0 && (
                      <div className="stats-card">
                        <h4>📧 Provider Types</h4>
                        <div className="provider-grid">
                          {Object.entries(batchResults.domain_stats.provider_distribution).map(([type, data]) => (
                            <div key={type} className={`provider-item provider-${type}`}>
                              <div className="provider-icon">
                                {type === 'free' && '🆓'}
                                {type === 'business' && '💼'}
                                {type === 'disposable' && '🗑️'}
                                {type === 'educational' && '🎓'}
                                {type === 'government' && '🏛️'}
                                {type === 'unknown' && '❓'}
                              </div>
                              <div className="provider-info">
                                <span className="provider-type">{type.charAt(0).toUpperCase() + type.slice(1)}</span>
                                <span className="provider-count">{data.count} ({data.percentage}%)</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Top Domains */}
                    {batchResults.domain_stats.top_domains && batchResults.domain_stats.top_domains.length > 0 && (
                      <div className="stats-card">
                        <h4>🏆 Top Domains ({batchResults.domain_stats.total_domains} unique)</h4>
                        <div className="domain-table">
                          <table>
                            <thead>
                              <tr>
                                <th>Domain</th>
                                <th>Count</th>
                                <th>% of Total</th>
                                <th>Valid Rate</th>
                                <th>Risk</th>
                              </tr>
                            </thead>
                            <tbody>
                              {batchResults.domain_stats.top_domains.map((domain, idx) => (
                                <tr key={idx}>
                                  <td className="domain-name">{domain.domain}</td>
                                  <td>{domain.count}</td>
                                  <td>{domain.percentage}%</td>
                                  <td>
                                    <span className={`validity-badge ${domain.validity_rate >= 80 ? 'high' : domain.validity_rate >= 50 ? 'medium' : 'low'}`}>
                                      {domain.validity_rate}%
                                    </span>
                                  </td>
                                  <td>
                                    {domain.high_risk_count > 0 ? (
                                      <span className="risk-badge high">⚠️ {domain.high_risk_count}</span>
                                    ) : (
                                      <span className="risk-badge low">✓</span>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            <div className="batch-list">
              {batchResults.results.map((item, index) => (
                <div key={index} className={`result-box ${item.valid ? 'valid' : 'invalid'}`} style={{marginBottom: '1.5rem'}}>
                  <div className="result-header">
                    <div className="result-title-row">
                      <h3 style={{fontSize: '1.2rem', margin: 0}}>{item.valid ? 'Valid Email' : 'Invalid Email'}</h3>
                      {item.status && (
                        <span className={`status-badge status-${item.status.color}`}>
                          {item.status.status.toUpperCase()}
                        </span>
                      )}
                    </div>
                    <span className="email-display">{item.email}</span>
                    {item.status && item.status.description && (
                      <span className="status-description">{item.status.description}</span>
                    )}
                  </div>

                  {mode === 'advanced' && item.checks && (
                    <>
                      <div className="confidence-section">
                        <div className="confidence-label">Confidence Score</div>
                        <div className="confidence-bar-container">
                          <div
                            className="confidence-bar"
                            style={{
                              width: `${item.confidence_score || 0}%`,
                              backgroundColor: getConfidenceColor(item.confidence_score || 0)
                            }}
                          />
                        </div>
                        <div className="confidence-value">
                          {item.confidence_score || 0}/100 - {getConfidenceLabel(item.confidence_score || 0)}
                        </div>
                      </div>

                      {item.deliverability && (
                        <div className="deliverability-section">
                          <div className="deliverability-header">
                            <span className="deliverability-label">Deliverability Score</span>
                            <span 
                              className="deliverability-grade"
                              style={{ 
                                backgroundColor: item.deliverability.deliverability_score >= 80 ? '#10b981' : 
                                               item.deliverability.deliverability_score >= 60 ? '#f59e0b' : '#ef4444'
                              }}
                            >
                              Grade: {item.deliverability.deliverability_grade}
                            </span>
                          </div>
                          <div className="deliverability-score">{item.deliverability.deliverability_score}/100</div>
                          <div className="deliverability-recommendation">
                            {item.deliverability.recommendation}
                          </div>
                        </div>
                      )}

                      {item.risk_check && item.risk_check.overall_risk !== 'low' && (
                        <div className={`risk-warning-section ${item.risk_check.overall_risk}`}>
                          <h4 style={{margin: '0 0 0.5rem 0'}}>Risk Detection</h4>
                          <div className="risk-warning-content">
                            <div className="risk-level">
                              Risk Level: <strong>{item.risk_check.overall_risk.toUpperCase()}</strong>
                            </div>
                            <div className="risk-recommendation">
                              {item.risk_check.recommendation}
                            </div>
                          </div>
                        </div>
                      )}

                      {item.bounce_check && item.bounce_check.bounce_history.has_bounced && (
                        <div className={`bounce-warning-section ${item.bounce_check.risk_level}`}>
                          <h4 style={{margin: '0 0 0.5rem 0'}}>Bounce History</h4>
                          <div className="bounce-warning-content">
                            <div className="bounce-stats">
                              <div className="bounce-stat">
                                <strong>{item.bounce_check.bounce_history.total_bounces}</strong>
                                <span>Total Bounces</span>
                              </div>
                              <div className="bounce-stat">
                                <strong>{item.bounce_check.bounce_history.hard_bounces}</strong>
                                <span>Hard Bounces</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="checks-grid">
                        <div className={`check-item ${item.checks.syntax ? 'pass' : 'fail'}`}>
                          <span className="check-icon">{item.checks.syntax ? '✓' : '✗'}</span>
                          <span>Syntax</span>
                        </div>
                        <div className={`check-item ${item.checks.dns_valid ? 'pass' : 'fail'}`}>
                          <span className="check-icon">{item.checks.dns_valid ? '✓' : '✗'}</span>
                          <span>DNS</span>
                        </div>
                        <div className={`check-item ${item.checks.mx_records ? 'pass' : 'fail'}`}>
                          <span className="check-icon">{item.checks.mx_records ? '✓' : '✗'}</span>
                          <span>MX Records</span>
                        </div>
                        <div className={`check-item ${!item.checks.is_disposable ? 'pass' : 'warn'}`}>
                          <span className="check-icon">{!item.checks.is_disposable ? '✓' : '⚠'}</span>
                          <span>Not Disposable</span>
                        </div>
                        <div className={`check-item ${!item.checks.is_role_based ? 'pass' : 'warn'}`}>
                          <span className="check-icon">{!item.checks.is_role_based ? '✓' : '⚠'}</span>
                          <span>Not Role-Based</span>
                        </div>
                      </div>

                      {item.suggestion && (
                        <div className="suggestion-box">
                          <strong>💡 Suggestion:</strong> Did you mean <strong>{item.suggestion}</strong>?
                        </div>
                      )}

                      {item.reason && (
                        <div className="reason-box">
                          <strong>Details:</strong> {item.reason}
                        </div>
                      )}
                    </>
                  )}

                  {mode === 'basic' && item.suggestion && (
                    <div className="suggestion-box">
                      <strong>💡 Suggestion:</strong> Did you mean <strong>{item.suggestion}</strong>?
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {showShareModal && (
          <div className="modal-overlay" onClick={() => setShowShareModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>🔗 Share Results</h3>
                <button className="modal-close" onClick={() => setShowShareModal(false)}>✕</button>
              </div>
              <div className="modal-body">
                <p className="share-description">
                  Anyone with this link can view your validation results. The link will expire in 24 hours.
                </p>
                <div className="share-link-container">
                  <input 
                    type="text" 
                    className="share-link-input" 
                    value={shareLink || ''} 
                    readOnly 
                  />
                  <button className="copy-link-btn" onClick={copyShareLink}>
                    <FiCopy /> Copy
                  </button>
                </div>
                <div className="share-stats">
                  <div className="share-stat">
                    <strong>{batchResults?.total || 0}</strong>
                    <span>Emails</span>
                  </div>
                  <div className="share-stat">
                    <strong>{batchResults?.valid_count || 0}</strong>
                    <span>Valid</span>
                  </div>
                  <div className="share-stat">
                    <strong>{batchResults?.invalid_count || 0}</strong>
                    <span>Invalid</span>
                  </div>
                </div>
                <div className="share-note">
                  💡 Tip: Share this link via email, Slack, or any messaging app
                </div>
              </div>
            </div>
          </div>
        )}

        <footer className="footer">
          <p>Powered by RFC 5321 compliant validation engine with AI-powered analysis</p>
          <p>Features: DNS • MX • Pattern Analysis • Email Enrichment • Deliverability Scoring</p>
          <div className="footer-lagic">
            <p><strong>LAGIC</strong> - Lead Audience Growth Intelligence Computing</p>
            <p>© 2025 LAGIC. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;

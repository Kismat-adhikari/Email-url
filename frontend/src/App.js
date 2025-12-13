import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import './AppModern.css';
import './AppPro.css';
import { 
  FiMail, FiRefreshCw, 
  FiTrash2, FiDownload, FiCopy, FiCheckCircle, FiXCircle,
  FiZap, FiCpu, FiInbox, FiList, FiClock, FiAlertTriangle,
  FiAlertCircle, FiFileText, FiSend,
  FiShield, FiActivity, FiAward, FiMoon, FiSun, FiUser, FiLogOut
} from 'react-icons/fi';
import EmailComposer from './EmailComposer';


// ============================================================================
// ANONYMOUS USER ID SYSTEM & LOCAL STORAGE HISTORY
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

// Local storage history management for anonymous users
function saveValidationToLocalStorage(validationResult) {
  try {
    const history = JSON.parse(localStorage.getItem('validation_history') || '[]');
    
    // Add new validation with timestamp
    const record = {
      id: Date.now(), // Simple ID for local storage
      email: validationResult.email,
      valid: validationResult.valid,
      confidence_score: validationResult.confidence_score || 0,
      checks: validationResult.checks || {},
      validated_at: new Date().toISOString(),
      // Store other relevant data
      deliverability: validationResult.deliverability,
      risk_check: validationResult.risk_check,
      bounce_check: validationResult.bounce_check,
      status: validationResult.status,
      reason: validationResult.reason,
      suggestion: validationResult.suggestion
    };
    
    // Add to beginning of array (newest first)
    history.unshift(record);
    
    // Keep only last 1000 records to prevent localStorage bloat
    if (history.length > 1000) {
      history.splice(1000);
    }
    
    localStorage.setItem('validation_history', JSON.stringify(history));
    console.log('💾 Saved validation to localStorage:', validationResult.email);
    
    return record;
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
    return null;
  }
}

function getLocalStorageHistory() {
  try {
    return JSON.parse(localStorage.getItem('validation_history') || '[]');
  } catch (error) {
    console.error('Failed to load from localStorage:', error);
    return [];
  }
}

// deleteLocalStorageRecord function removed - no longer needed since we only remove from display

function clearLocalStorageHistory() {
  try {
    localStorage.removeItem('validation_history');
    return true;
  } catch (error) {
    console.error('Failed to clear localStorage:', error);
    return false;
  }
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
  const [emailMode, setEmailMode] = useState(false);

  const [batchEmails, setBatchEmails] = useState('');
  const [batchResults, setBatchResults] = useState(null);
  const [uploadMode, setUploadMode] = useState('text');
  const [selectedFile, setSelectedFile] = useState(null);
  const [removeDuplicates, setRemoveDuplicates] = useState(true);
  const [showDomainStats, setShowDomainStats] = useState(true);
  const [progress, setProgress] = useState({ current: 0, total: 0, percentage: 0, eta: 0, speed: 0 });
  const [shareLink, setShareLink] = useState(null);
  const [showShareModal, setShowShareModal] = useState(false);
  const [showBatchResults, setShowBatchResults] = useState(true);
  
  const [history, setHistory] = useState([]);
  const [filteredHistory, setFilteredHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [historyLoading, setHistoryLoading] = useState(false);
  
  // Authentication state
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [authToken, setAuthToken] = useState(() => {
    return localStorage.getItem('authToken');
  });
  
  const [anonUserId] = useState(() => getAnonUserId());
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  // Admin mode detection
  const [adminMode, setAdminMode] = useState(() => {
    const isAdmin = localStorage.getItem('adminMode') === 'true';
    console.log('🛡️ Initial admin mode:', isAdmin);
    return isAdmin;
  });
  const [adminToken, setAdminToken] = useState(() => {
    const token = localStorage.getItem('adminToken');
    console.log('🔑 Initial admin token:', token ? `${token.substring(0, 20)}...` : 'null');
    return token;
  });
  const [adminUser, setAdminUser] = useState(() => {
    const savedAdminUser = localStorage.getItem('adminUser');
    const user = savedAdminUser ? JSON.parse(savedAdminUser) : null;
    console.log('👤 Initial admin user:', user);
    return user;
  });

  // Listen for admin mode changes (when opened from admin dashboard)
  useEffect(() => {
    const checkAdminMode = () => {
      const isAdmin = localStorage.getItem('adminMode') === 'true';
      const token = localStorage.getItem('adminToken');
      const user = localStorage.getItem('adminUser');
      
      if (isAdmin !== adminMode) {
        console.log('🛡️ Admin mode changed:', isAdmin);
        setAdminMode(isAdmin);
      }
      if (token !== adminToken) {
        console.log('🔑 Admin token changed:', token ? `${token.substring(0, 20)}...` : 'null');
        setAdminToken(token);
      }
      if (user) {
        try {
          const parsedUser = JSON.parse(user);
          if (JSON.stringify(parsedUser) !== JSON.stringify(adminUser)) {
            console.log('👤 Admin user changed:', parsedUser);
            setAdminUser(parsedUser);
          }
        } catch (e) {
          console.error('Failed to parse admin user:', e);
        }
      } else if (adminUser) {
        console.log('👤 Admin user cleared');
        setAdminUser(null);
      }
    };

    // Check immediately
    checkAdminMode();
    
    // Check periodically for changes (when opened from admin dashboard)
    const interval = setInterval(checkAdminMode, 1000);
    
    return () => clearInterval(interval);
  }, [adminMode, adminToken, adminUser]);

  const API_URL = process.env.NODE_ENV === 'production' 
    ? ''
    : 'http://localhost:5000';
  
  // Create API instance with dynamic headers
  const api = axios.create({
    baseURL: API_URL,
    headers: {
      'X-User-ID': anonUserId,
      ...(adminMode && adminToken && { 'Authorization': `Bearer ${adminToken}` }),
      ...(!adminMode && authToken && { 'Authorization': `Bearer ${authToken}` })
    }
  });

  // Update API headers when auth token changes
  useEffect(() => {
    if (adminMode && adminToken) {
      api.defaults.headers['Authorization'] = `Bearer ${adminToken}`;
    } else if (authToken) {
      api.defaults.headers['Authorization'] = `Bearer ${authToken}`;
    } else {
      delete api.defaults.headers['Authorization'];
    }
  }, [authToken, adminMode, adminToken, api]);

  // Logout function
  const handleLogout = useCallback(async () => {
    try {
      if (authToken) {
        await api.post('/api/auth/logout');
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      setAuthToken(null);
      setUser(null);
      
      // Redirect to landing page
      window.location.href = '/testing';
    }
  }, [authToken, api]);

  useEffect(() => {
    // Apply dark mode class
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  // Refresh user data on app load if user is logged in
  useEffect(() => {
    const refreshUserData = async () => {
      if (authToken && user) {
        try {
          const response = await api.get('/api/auth/me');
          if (response.status === 200) {
            const updatedUser = response.data.user;
            setUser(updatedUser);
            localStorage.setItem('user', JSON.stringify(updatedUser));
            console.log('🔄 User data refreshed from server');
          }
        } catch (error) {
          console.error('Failed to refresh user data:', error);
          // If token is invalid, logout
          if (error.response?.status === 401) {
            handleLogout();
          }
        }
      }
    };

    refreshUserData();
  }, [api, authToken, user, handleLogout]); // Run once on app load

  // Helper function for immediate suspension checking
  const checkUserStatus = useCallback(async () => {
    if (!user || !authToken) return true; // Not logged in, no need to check
    
    try {
      await api.get('/api/auth/check-status');
      return true; // User is still active
    } catch (error) {
      if (error.response?.status === 403 && error.response?.data?.suspended) {
        // User has been suspended!
        const suspensionData = error.response.data;
        
        // Show suspension notification
        alert(`🚫 Account Suspended\n\nYour account has been suspended.\nReason: ${suspensionData.reason}\nDate: ${new Date(suspensionData.suspended_at).toLocaleString()}\n\nYou will be logged out automatically.`);
        
        // Force logout
        handleLogout();
        return false; // User is suspended
      }
      return true; // Other errors, assume user is still active
    }
  }, [user, authToken, api, handleLogout]);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      if (user) {
        // Authenticated user - load from database
        const response = await api.get('/api/history?limit=100');
        const historyData = response.data.history || [];
        
        setHistory(historyData);
        setFilteredHistory(historyData);
        
        console.log(`📊 Loaded ${historyData.length} database records for authenticated user: ${user.firstName} ${user.lastName}`);
      } else {
        // Anonymous user - load from localStorage
        const localHistory = getLocalStorageHistory();
        
        setHistory(localHistory);
        setFilteredHistory(localHistory);
        
        console.log(`📊 Loaded ${localHistory.length} localStorage records for anonymous user`);
      }
      
    } catch (err) {
      console.error('History loading error:', err);
      if (user) {
        setError('Failed to load history from server');
      } else {
        // Fallback to empty history for localStorage errors
        setHistory([]);
        setFilteredHistory([]);
      }
    } finally {
      setHistoryLoading(false);
    }
  }, [user, api]);

  useEffect(() => {
    // Clean up signup success URL parameter (no alert needed)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('signup') === 'success') {
      // Clean up URL without showing alert
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    // Reload history when user authentication changes
    if (historyMode) {
      loadHistory();
    }
  }, [user, historyMode, loadHistory]);

  // Real-time suspension monitoring
  useEffect(() => {
    if (!user || !authToken) return;

    // Check status every 2 seconds for instant detection
    const statusInterval = setInterval(checkUserStatus, 2000);

    // Cleanup interval on unmount
    return () => clearInterval(statusInterval);
  }, [user, authToken, checkUserStatus]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const exportToCSV = () => {
    if (!batchResults || !batchResults.results) return;

    const headers = mode === 'advanced' 
      ? [
          'Email', 'Valid', 'Confidence Score', 'Deliverability Score', 'Deliverability Grade',
          'Status', 'Risk Level', 'Domain', 'Provider Type', 
          'Is Disposable', 'Is Role Based', 'Has MX Records', 'DNS Valid',
          'Bounce Count', 'Reason', 'Suggestion'
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
          r.bounce_info?.bounce_count || 0,
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

    // Immediate suspension check before any action
    if (user && !(await checkUserStatus())) {
      return; // User is suspended, checkUserStatus handles logout
    }

    // Check if authenticated user has reached their limit (skip for admin mode)
    if (!adminMode && user && user.apiCallsCount >= user.apiCallsLimit) {
      setError(`You've reached your limit of ${user.apiCallsLimit} API calls. ${user.subscriptionTier === 'free' ? 'Upgrade to a paid plan for unlimited validations!' : 'Please contact support to increase your limit.'}`);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Choose endpoint based on mode
      let endpoint;
      if (adminMode) {
        endpoint = '/api/admin/validate'; // Admin unlimited endpoint
      } else if (user) {
        endpoint = '/api/validate'; // Regular authenticated endpoint
      } else {
        endpoint = '/api/validate/local'; // Anonymous endpoint
      }
      
      const response = await api.post(endpoint, { 
        email,
        advanced: mode === 'advanced'
      });
      
      setResult(response.data);
      
      // Update user API usage if authenticated
      if (user && response.data.api_usage) {
        const updatedUser = {
          ...user,
          apiCallsCount: response.data.api_usage.calls_used
        };
        setUser(updatedUser);
        localStorage.setItem('user', JSON.stringify(updatedUser));
        console.log(`🔄 API usage updated: ${response.data.api_usage.calls_used}/${response.data.api_usage.calls_limit}`);
      }
      
      // Save to localStorage for anonymous users
      if (!user && response.data) {
        saveValidationToLocalStorage(response.data);
      }
      
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
      
      // Handle API limit exceeded error specifically
      if (err.response?.status === 429) {
        // Update user state to reflect limit reached
        if (user && err.response?.data?.current_usage) {
          setUser(prev => ({
            ...prev,
            apiCallsCount: err.response.data.current_usage
          }));
        }
      }
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

    // Check if authenticated user has reached their limit (skip for admin mode)
    if (!adminMode && user && user.apiCallsCount >= user.apiCallsLimit) {
      setError(`You've reached your limit of ${user.apiCallsLimit} API calls. ${user.subscriptionTier === 'free' ? 'Upgrade to a paid plan for unlimited validations!' : 'Please contact support to increase your limit.'}`);
      return;
    }

    // Check if batch would exceed user's remaining limit (skip for admin mode)
    if (!adminMode && user) {
      const remainingCalls = user.apiCallsLimit - user.apiCallsCount;
      if (emails.length > remainingCalls) {
        setError(`This batch contains ${emails.length} emails, but you only have ${remainingCalls} API calls remaining. ${user.subscriptionTier === 'free' ? 'Upgrade to a paid plan for unlimited validations!' : 'Please reduce the batch size or contact support.'}`);
        return;
      }
    }

    // Detect duplicates for display
    detectDuplicates(emails);

    const startTime = Date.now();
    setLoading(true);
    setError(null);
    setBatchResults({ results: [], total: emails.length, valid_count: 0, invalid_count: 0 });
    setProgress({ current: 0, total: emails.length, percentage: 0, eta: 0, speed: 0 });

    try {
      // Use different endpoint based on mode
      let endpoint;
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (adminMode) {
        // Admin mode: Use regular JSON endpoint (not streaming)
        endpoint = '/api/admin/validate/batch';
        headers['Authorization'] = `Bearer ${adminToken}`;
        
        console.log('🛡️ Admin batch validation:', {
          adminMode,
          adminToken: adminToken ? `${adminToken.substring(0, 20)}...` : 'null',
          endpoint,
          emailCount: emails.length
        });
        
        const response = await fetch(`${API_URL}${endpoint}`, {
          method: 'POST',
          headers: headers,
          body: JSON.stringify({
            emails,
            advanced: mode === 'advanced'
          })
        });

        if (!response.ok) {
          const errorData = await response.json();
          console.error('❌ Admin batch validation failed:', errorData);
          throw new Error(errorData.message || 'Admin batch validation failed');
        }

        const data = await response.json();
        
        // Simulate progress for admin (instant completion)
        setProgress({
          current: data.total,
          total: data.total,
          percentage: 100,
          eta: 0,
          speed: data.processing_time > 0 ? (data.total / data.processing_time).toFixed(1) : data.total
        });

        // Set final results with domain stats
        setBatchResults({
          results: data.results,
          valid_count: data.valid_count,
          invalid_count: data.invalid_count,
          total: data.total,
          original_count: data.original_count,
          duplicates_removed: data.duplicates_removed,
          processing_time: data.processing_time,
          admin_validation: true,
          domain_stats: data.domain_stats || null
        });

      } else {
        // Regular users: Use streaming endpoint
        if (user) {
          endpoint = '/api/validate/batch/stream'; // Regular authenticated endpoint
          headers['Authorization'] = `Bearer ${authToken}`;
        } else {
          endpoint = '/api/validate/batch/local'; // Anonymous endpoint
          headers['X-User-ID'] = anonUserId;
        }

        const response = await fetch(`${API_URL}${endpoint}`, {
          method: 'POST',
          headers: headers,
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

                // Save to localStorage for anonymous users
                if (!user && data.result) {
                  saveValidationToLocalStorage(data.result);
                }

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
    // Custom confirmation dialog
    const confirmed = window.confirm(
      'Remove this record from view?\n\n' +
      'Note: This will only hide the record from this page. ' +
      'Your API usage count will not change.'
    );
    
    if (!confirmed) return;
    
    try {
      // Only remove from the current display, not from actual data
      const updatedHistory = history.filter(item => item.id !== id);
      const updatedFilteredHistory = filteredHistory.filter(item => item.id !== id);
      
      setHistory(updatedHistory);
      setFilteredHistory(updatedFilteredHistory);
      
      // Show success message
      console.log('✅ Record removed from view (API usage unchanged)');
    } catch (err) {
      alert('Failed to remove record from view');
    }
  };

  const clearAllHistory = async () => {
    if (!window.confirm('Clear ALL history? This cannot be undone!')) return;
    
    try {
      if (user) {
        // Authenticated user - clear database
        await api.delete('/api/history');
        setHistory([]);
        setFilteredHistory([]);
        alert('History cleared');
      } else {
        // Anonymous user - clear localStorage
        if (clearLocalStorageHistory()) {
          setHistory([]);
          setFilteredHistory([]);
          alert('History cleared');
        } else {
          alert('Failed to clear history');
        }
      }
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
    if (score >= 95) return '#059669'; // Emerald for premium
    if (score >= 85) return '#10b981'; // Green for excellent
    if (score >= 70) return '#f59e0b'; // Amber for good
    if (score >= 40) return '#f97316'; // Orange for fair
    return '#ef4444'; // Red for poor
  };

  const getConfidenceLabel = (score) => {
    if (score >= 95) return 'Premium';
    if (score >= 85) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  };

  const getConfidenceTextColor = (score) => {
    if (score >= 95) return '#064e3b'; // Darkest green for premium
    if (score >= 85) return '#065f46'; // Dark green for excellent
    if (score >= 70) return '#92400e'; // Dark amber for good
    if (score >= 40) return '#b45309'; // Orange for fair
    return '#991b1b'; // Dark red for poor
  };



  return (
    <div className="App">
      {/* Top Navigation Bar */}
      <nav className="top-navbar">
        <div className="navbar-container">
          {/* Logo Section */}
          <div className="navbar-logo">
            <span className="logo-text">LAGCI</span>
          </div>

          {/* Center Section - User Info */}
          <div className="navbar-center">
            {adminMode ? (
              <div className="user-greeting admin-mode">
                <span className="wave-icon">🛡️</span>
                <span className="greeting-text">Admin Mode: {adminUser?.first_name || 'Admin'}!</span>
                <span className="admin-badge">UNLIMITED ACCESS</span>
              </div>
            ) : user ? (
              <div className="user-greeting">
                <span className="wave-icon">👋</span>
                <span className="greeting-text">Welcome, {user.firstName}!</span>
              </div>
            ) : null}
          </div>

          {/* Right Section - API Usage & Controls */}
          <div className="navbar-right">
            {/* Dark Mode Toggle */}
            <button className="navbar-btn dark-mode-btn" onClick={toggleDarkMode} title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
              {darkMode ? <FiSun /> : <FiMoon />}
            </button>

            {/* API Usage Counter */}
            {adminMode ? (
              <div className="api-usage-counter admin-unlimited">
                <FiShield className="usage-icon" />
                <span className="usage-text">∞/∞</span>
                <span className="usage-label">Admin</span>
                <div className="admin-hint">
                  <FiZap style={{marginRight: '4px'}} /> Unlimited Access!
                </div>
              </div>
            ) : user ? (
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
            ) : (
              <div className="anonymous-usage-counter" title="Sign up to save your validation history and get API access">
                <FiActivity className="usage-icon" />
                <span className="usage-text">Free Mode</span>
                <span className="usage-label">Unlimited</span>
                <div className="signup-hint">
                  <span>💾 Sign up!</span>
                </div>
              </div>
            )}

            {/* Authentication Buttons */}
            {(() => {
              console.log('🔍 Auth state:', { adminMode, adminUser: !!adminUser, user: !!user });
              return null;
            })()}
            {adminMode ? (
              <div className="auth-buttons">
                <button className="navbar-btn admin-dashboard-btn" onClick={() => window.open('/admin/dashboard', '_blank')}>
                  <FiShield /> Admin Dashboard
                </button>
                <button className="navbar-btn logout-btn" onClick={() => {
                  console.log('🚪 Admin logout clicked');
                  // Clear admin mode and redirect to admin login
                  localStorage.removeItem('adminMode');
                  localStorage.removeItem('adminToken');
                  localStorage.removeItem('adminUser');
                  // Also clear regular user data if any
                  localStorage.removeItem('authToken');
                  localStorage.removeItem('user');
                  window.location.href = '/admin/login';
                }}>
                  <FiLogOut /> Admin Logout
                </button>
              </div>
            ) : user ? (
              <div className="auth-buttons">
                <button className="navbar-btn profile-btn" onClick={() => navigate('/profile')}>
                  <FiUser /> Profile
                </button>
                <button className="navbar-btn logout-btn" onClick={handleLogout}>
                  <FiLogOut /> Logout
                </button>
              </div>
            ) : (
              <div className="auth-buttons">
                <button className="navbar-btn login-btn" onClick={() => navigate('/login')}>
                  Login
                </button>
                <button className="navbar-btn signup-btn" onClick={() => navigate('/signup')}>
                  Sign Up
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      <div className="pro-container">
        {/* Simplified Header */}
        <header className="pro-header-simple">
          <div className="pro-header-title">
            <h1><FiMail /> Email Validator</h1>
          </div>
          <p className="pro-header-subtitle">
            Enterprise-grade email validation with AI-powered analysis, DNS verification, and deliverability scoring
          </p>
        </header>

        {/* Main Card */}
        <div className="pro-main-card">
          {/* Tabs */}
          <div className="pro-tabs">
            <button
              className={`pro-tab ${!batchMode && !historyMode && !emailMode ? 'active' : ''}`}
              onClick={() => {
                setBatchMode(false);
                setHistoryMode(false);
                setEmailMode(false);
                setResult(null);
                setBatchResults(null);
                setError(null);
              }}
            >
              <span className="pro-tab-icon"><FiInbox /></span>
              Single Email
            </button>
            <button
              className={`pro-tab ${batchMode ? 'active' : ''} ${!adminMode && user && user.subscriptionTier === 'free' ? 'disabled pro-feature' : ''}`}
              onClick={() => {
                if (!adminMode && user && user.subscriptionTier === 'free') {
                  setError('Batch validation is only available for Pro plans. Upgrade to validate multiple emails at once!');
                  return;
                }
                setBatchMode(true);
                setHistoryMode(false);
                setEmailMode(false);
                setResult(null);
                setBatchResults(null);
                setError(null);
              }}
              disabled={!adminMode && user && user.subscriptionTier === 'free'}
              title={!adminMode && user && user.subscriptionTier === 'free' ? 'Upgrade to Pro for batch validation' : 'Validate multiple emails at once'}
            >
              <div className="pro-tab-content">
                <span className="pro-tab-icon"><FiList /></span>
                <span className="pro-tab-text">
                  Batch Validation
                  {!adminMode && user && user.subscriptionTier === 'free' && (
                    <span className="pro-badge">PRO</span>
                  )}
                  {adminMode && (
                    <span className="admin-badge">ADMIN</span>
                  )}
                </span>
              </div>
            </button>
            <button
              className={`pro-tab ${emailMode ? 'active' : ''} ${!adminMode && user && user.subscriptionTier === 'free' ? 'disabled pro-feature' : ''}`}
              onClick={() => {
                if (!adminMode && user && user.subscriptionTier === 'free') {
                  setError('Email sending is only available for Pro plans. Upgrade to send emails to validated addresses!');
                  return;
                }
                setEmailMode(true);
                setBatchMode(false);
                setHistoryMode(false);
                setResult(null);
                setBatchResults(null);
                setError(null);
              }}
              disabled={!adminMode && user && user.subscriptionTier === 'free'}
              title={!adminMode && user && user.subscriptionTier === 'free' ? 'Upgrade to Pro for email sending' : 'Send emails to validated addresses'}
            >
              <div className="pro-tab-content">
                <span className="pro-tab-icon"><FiSend /></span>
                <span className="pro-tab-text">
                  Send Emails
                  {!adminMode && user && user.subscriptionTier === 'free' && (
                    <span className="pro-badge">PRO</span>
                  )}
                  {adminMode && (
                    <span className="admin-badge">ADMIN</span>
                  )}
                </span>
              </div>
            </button>
            <button
              className={`pro-tab ${historyMode ? 'active' : ''}`}
              onClick={() => {
                setHistoryMode(true);
                setBatchMode(false);
                setEmailMode(false);
                setResult(null);
                setBatchResults(null);
                setError(null);
                loadHistory();
              }}
            >
              <span className="pro-tab-icon"><FiClock /></span>
              History
            </button>

          </div>

          {/* Content */}
          <div className="pro-content">
            {/* Mode Selector - Only show when NOT in history mode */}
            {!historyMode && (
              <div className={`pro-mode-selector ${loading ? 'disabled' : ''}`}>
                <div 
                  className={`pro-mode-option ${mode === 'basic' ? 'active' : ''} ${loading ? 'disabled' : ''}`}
                  onClick={() => {
                    if (loading) return; // Prevent mode switching during validation
                    setMode('basic');
                    setResult(null);
                    setError(null);
                  }}
                >
                  <input
                    type="radio"
                    className="pro-mode-radio"
                    value="basic"
                    checked={mode === 'basic'}
                    disabled={loading}
                    onChange={(e) => {
                      if (loading) return; // Prevent mode switching during validation
                      setMode(e.target.value);
                      setResult(null);
                      setError(null);
                    }}
                  />
                  <div className="pro-mode-label">
                    <div className="pro-mode-title"><FiZap style={{display: 'inline', marginRight: '8px'}} /> Basic Mode</div>
                    <div className="pro-mode-desc">Syntax validation only - Lightning fast</div>
                  </div>
                </div>
                <div 
                  className={`pro-mode-option ${mode === 'advanced' ? 'active' : ''} ${loading ? 'disabled' : ''}`}
                  onClick={() => {
                    if (loading) return; // Prevent mode switching during validation
                    setMode('advanced');
                    setResult(null);
                    setError(null);
                  }}
                >
                  <input
                    type="radio"
                    className="pro-mode-radio"
                    value="advanced"
                    checked={mode === 'advanced'}
                    disabled={loading}
                    onChange={(e) => {
                      if (loading) return; // Prevent mode switching during validation
                      setMode(e.target.value);
                      setResult(null);
                      setError(null);
                    }}
                  />
                  <div className="pro-mode-label">
                    <div className="pro-mode-title"><FiCpu style={{display: 'inline', marginRight: '8px'}} /> Advanced Mode</div>
                    <div className="pro-mode-desc">Full validation - DNS, MX, Disposable, AI Analysis</div>
                  </div>
                </div>
              </div>
            )}



        {emailMode ? (
          <EmailComposer />
        ) : historyMode ? (
          <div className="history-section">
            {/* User-specific history header */}
            <div className="history-header">
              <h3 className="history-title">
                <FiList style={{ marginRight: '8px' }} />
                {user ? (
                  <>Validation History for {user.firstName} {user.lastName}</>
                ) : (
                  <>Anonymous Validation History</>
                )}
              </h3>

            </div>
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
                {user ? (
                  <>
                    <div className="empty-icon">📊</div>
                    <h3>No validation history yet</h3>
                    <p>Your validated emails will appear here with full database backup</p>
                    <p className="empty-hint">Start validating emails to build your history!</p>
                  </>
                ) : (
                  <>
                    <div className="empty-icon">📱</div>
                    <h3>No validations yet</h3>
                    <p>Anonymous users get browser-only storage</p>
                    <p className="empty-hint">
                      <strong>Sign up</strong> for database backup and unlimited validations!
                    </p>
                    <button 
                      className="signup-cta-btn"
                      onClick={() => navigate('/signup')}
                    >
                      Create Free Account
                    </button>
                  </>
                )}
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
            {/* Single Email Input */}
            <div className="pro-input-section">
              {/* Free Tier Limit Warning (hidden for admin) */}
              {!adminMode && user && user.subscriptionTier === 'free' && user.apiCallsCount >= user.apiCallsLimit && (
                <div className="limit-reached-banner">
                  <div className="limit-banner-content">
                    <div className="limit-banner-icon">🚫</div>
                    <div className="limit-banner-text">
                      <h3>Free Tier Limit Reached</h3>
                      <p>You've used all {user.apiCallsLimit} free validations. Upgrade to continue validating emails!</p>
                    </div>
                    <button className="upgrade-btn" onClick={() => navigate('/profile')}>
                      <FiZap style={{marginRight: '6px'}} /> Upgrade Now
                    </button>
                  </div>
                </div>
              )}
              
              {/* Approaching Limit Warning (hidden for admin) */}
              {!adminMode && user && user.subscriptionTier === 'free' && user.apiCallsCount >= user.apiCallsLimit * 0.8 && user.apiCallsCount < user.apiCallsLimit && (
                <div className="limit-warning-banner">
                  <div className="limit-banner-content">
                    <div className="limit-banner-icon">⚠️</div>
                    <div className="limit-banner-text">
                      <h3>Approaching Limit</h3>
                      <p>You have {user.apiCallsLimit - user.apiCallsCount} validations remaining out of {user.apiCallsLimit}.</p>
                    </div>
                    <button className="upgrade-btn-small" onClick={() => navigate('/profile')}>
                      Upgrade
                    </button>
                  </div>
                </div>
              )}

              <div className="pro-input-wrapper">
                <input
                  type="email"
                  className={`pro-email-input ${!adminMode && user && user.apiCallsCount >= user.apiCallsLimit ? 'disabled' : ''}`}
                  placeholder={!adminMode && user && user.apiCallsCount >= user.apiCallsLimit ? 'Upgrade to continue validating...' : adminMode ? 'Admin: Unlimited validation access...' : 'Enter email address to validate...'}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={loading || (!adminMode && user && user.apiCallsCount >= user.apiCallsLimit)}
                />
                <button
                  className={`pro-validate-btn ${!adminMode && user && user.apiCallsCount >= user.apiCallsLimit ? 'disabled' : ''}`}
                  onClick={validateEmail}
                  disabled={loading || !email.trim() || (!adminMode && user && user.apiCallsCount >= user.apiCallsLimit)}
                >
                  {!adminMode && user && user.apiCallsCount >= user.apiCallsLimit ? 'Limit Reached' : loading ? 'Validating...' : adminMode ? 'Validate Email (Admin)' : 'Validate Email'}
                </button>
              </div>
            </div>
            
            {/* Loading State */}
            {loading && !batchMode && (
              <div className="pro-loading">
                <div className="pro-spinner"></div>
                <div className="pro-loading-text">Analyzing email address...</div>
              </div>
            )}
          </>
        ) : (
          <div className="batch-section">
            {/* Free Tier Batch Restriction (hidden for admin) */}
            {!adminMode && user && user.subscriptionTier === 'free' && (
              <div className="feature-restriction-banner">
                <div className="restriction-banner-content">
                  <div className="restriction-banner-icon"><FiZap /></div>
                  <div className="restriction-banner-text">
                    <h3>Batch Validation - Pro Feature</h3>
                    <p>Batch validation is available for Pro users only. Upgrade to validate multiple emails at once, upload files, and access advanced batch analytics!</p>
                    <div className="feature-list">
                      <span>✅ Unlimited batch processing</span>
                      <span>✅ File upload support (CSV, Excel, PDF)</span>
                      <span>✅ Domain statistics & analytics</span>
                      <span>✅ Export results (CSV, JSON)</span>
                    </div>
                  </div>
                  <button className="upgrade-btn-large" onClick={() => navigate('/profile')}>
                    <FiZap style={{marginRight: '8px'}} /> Upgrade to Pro
                  </button>
                </div>
              </div>
            )}

            {/* Admin Access Banner */}
            {adminMode && (
              <div className="admin-access-banner">
                <div className="admin-banner-content">
                  <div className="admin-banner-icon"><FiShield /></div>
                  <div className="admin-banner-text">
                    <h3>Admin Access - All Features Unlocked</h3>
                    <p>You have unlimited access to all premium features including batch validation, file uploads, and advanced analytics!</p>
                    <div className="feature-list">
                      <span>🛡️ Unlimited batch processing</span>
                      <span>🛡️ All file formats supported</span>
                      <span>🛡️ Advanced analytics & exports</span>
                      <span>🛡️ No API limits or restrictions</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="upload-mode-selector">
              <button
                className={`upload-mode-btn ${uploadMode === 'text' ? 'active' : ''} ${!adminMode && user && user.apiCallsCount >= user.apiCallsLimit ? 'disabled' : ''}`}
                onClick={() => setUploadMode('text')}
                disabled={!adminMode && user && user.apiCallsCount >= user.apiCallsLimit}
              >
                ✏️ Type Emails {adminMode && '(Admin)'}
              </button>
              <button
                className={`upload-mode-btn ${uploadMode === 'file' ? 'active' : ''} ${!adminMode && user && user.apiCallsCount >= user.apiCallsLimit ? 'disabled' : ''}`}
                onClick={() => setUploadMode('file')}
                disabled={!adminMode && user && user.apiCallsCount >= user.apiCallsLimit}
              >
                📁 Upload File {adminMode && '(Admin)'}
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
                const finalCount = removeDuplicates ? dupInfo.unique : dupInfo.total;
                
                return (
                  <div className="batch-analysis">
                    {/* Email count and duplicate info */}
                    <div className="email-count-info">
                      📧 {finalCount} email{finalCount !== 1 ? 's' : ''} ready for validation
                      {dupInfo.duplicates > 0 && (
                        <span className="duplicate-note">
                          {removeDuplicates 
                            ? ` (${dupInfo.duplicates} duplicate${dupInfo.duplicates > 1 ? 's' : ''} will be removed)`
                            : ` (${dupInfo.duplicates} duplicate${dupInfo.duplicates > 1 ? 's' : ''} detected)`
                          }
                        </span>
                      )}
                    </div>
                    
                    {/* API limit warning for authenticated users (hidden for admin) */}
                    {!adminMode && user && user.subscriptionTier === 'free' && (
                      <div className={`api-limit-check ${
                        finalCount > (user.apiCallsLimit - user.apiCallsCount) ? 'exceeds-limit' : 
                        finalCount > (user.apiCallsLimit - user.apiCallsCount) * 0.5 ? 'approaching-limit' : 'within-limit'
                      }`}>
                        {finalCount > (user.apiCallsLimit - user.apiCallsCount) ? (
                          <>
                            ❌ Batch size ({finalCount}) exceeds your remaining limit ({user.apiCallsLimit - user.apiCallsCount})
                            <div className="limit-suggestion">
                              Reduce batch size or <strong>upgrade to unlimited</strong>
                            </div>
                          </>
                        ) : finalCount > (user.apiCallsLimit - user.apiCallsCount) * 0.5 ? (
                          <>
                            ⚠️ This will use {finalCount} of your {user.apiCallsLimit - user.apiCallsCount} remaining validations
                          </>
                        ) : (
                          <>
                            ✅ Within your limit ({user.apiCallsLimit - user.apiCallsCount} remaining)
                          </>
                        )}
                      </div>
                    )}
                    
                    {/* Admin unlimited access indicator */}
                    {adminMode && batchEmails && (
                      <div className="admin-unlimited-indicator">
                        🛡️ Admin Mode: Unlimited batch validation ({parseEmails(batchEmails).length} emails ready)
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>

            {uploadMode === 'text' ? (
              <>
                <div className="format-info">
                  💡 Paste emails in any format: one per line, comma-separated, or copy from Excel/Sheets
                  {!adminMode && user && user.subscriptionTier === 'free' && (
                    <div className="batch-limit-info">
                      ⚠️ Free tier: {user.apiCallsLimit - user.apiCallsCount} validations remaining
                    </div>
                  )}
                  {adminMode && (
                    <div className="admin-batch-info">
                      🛡️ Admin Mode: Unlimited batch validation access
                    </div>
                  )}
                </div>
                <textarea
                  className={`batch-input ${!adminMode && user && user.apiCallsCount >= user.apiCallsLimit ? 'disabled' : ''}`}
                  placeholder={!adminMode && user && user.apiCallsCount >= user.apiCallsLimit ? 'Upgrade to continue batch validation...' : adminMode ? 'Admin: Enter unlimited emails for batch validation...' : 'Enter email addresses (one per line, comma-separated, or any format)...'}
                  value={batchEmails}
                  onChange={(e) => setBatchEmails(e.target.value)}
                  disabled={loading || (!adminMode && user && user.apiCallsCount >= user.apiCallsLimit)}
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
              className={`validate-btn ${!adminMode && user && user.apiCallsCount >= user.apiCallsLimit ? 'disabled' : ''}`}
              onClick={validateBatch}
              disabled={loading || (!batchEmails.trim()) || (!adminMode && user && user.apiCallsCount >= user.apiCallsLimit)}
            >
              {!adminMode && user && user.apiCallsCount >= user.apiCallsLimit ? 'Limit Reached - Upgrade Required' : loading ? 'Validating...' : adminMode ? 'Validate Batch (Admin - Unlimited)' : 'Validate Batch'}
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

        {/* Error Display */}
        {error && (
          <div className={`pro-error-box ${error.includes('Pro plans') || error.includes('Email sending') ? 'upgrade-error' : ''}`}>
            <strong><FiAlertTriangle style={{display: 'inline', marginRight: '8px'}} /> {error.includes('Pro plans') || error.includes('Email sending') ? 'Upgrade Required:' : 'Error:'}</strong> {error}
            {(error.includes('Pro plans') || error.includes('Email sending')) && (
              <button className="error-upgrade-btn" onClick={() => navigate('/profile')}>
                Upgrade Now
              </button>
            )}
          </div>
        )}

        {/* Single Email Result */}
        {result && !batchMode && (
          <div className={`pro-result-card ${result.valid ? 'valid' : 'invalid'}`}>
            {/* Anonymous User Signup Encouragement */}
            {!user && (
              <div className="anonymous-signup-banner">
                <div className="signup-banner-content">
                  <div className="signup-banner-icon">💾</div>
                  <div className="signup-banner-text">
                    <h3>Save Your Validation History</h3>
                    <p>Sign up for free to save your results, access advanced features, and get API access!</p>
                  </div>
                  <button className="signup-banner-btn" onClick={() => navigate('/signup')}>
                    Sign Up Free
                  </button>
                </div>
              </div>
            )}

            {/* Result Header */}
            <div className={`pro-result-header ${result.valid ? 'valid' : 'invalid'}`}>
              <div className="pro-result-title-row">
                <h2 className="pro-result-title">
                  {result.valid ? <><FiCheckCircle /> Valid Email</> : <><FiXCircle /> Invalid Email</>}
                </h2>
                {result.status && (
                  <span className="pro-status-badge">
                    {result.status.status.toUpperCase()}
                  </span>
                )}
              </div>
              <div className="pro-email-display">{result.email}</div>
              {result.status && result.status.description && (
                <div className="pro-status-description">{result.status.description}</div>
              )}
            </div>

            {/* Result Body */}
            <div className="pro-result-body">
            {mode === 'advanced' && result.checks && (
              <>
                {/* Score Cards */}
                <div className="pro-score-grid">
                  {/* Confidence Score */}
                  <div className="pro-score-card confidence">
                    <div className="pro-score-label">Confidence Score</div>
                    <div className="pro-score-value" style={{
                      color: getConfidenceTextColor(result.confidence_score || 0)
                    }}>
                      {result.confidence_score || 0}<span style={{fontSize: '1.5rem', color: '#6b7280'}}>/100</span>
                    </div>
                    <div className="pro-score-bar">
                      <div
                        className="pro-score-bar-fill"
                        style={{
                          width: `${result.confidence_score || 0}%`,
                          backgroundColor: getConfidenceColor(result.confidence_score || 0)
                        }}
                      />
                    </div>
                    <div className="pro-score-text" style={{
                      color: getConfidenceTextColor(result.confidence_score || 0),
                      fontWeight: '600'
                    }}>
                      {getConfidenceLabel(result.confidence_score || 0)} Quality
                    </div>
                    
                    {/* Tiered Validation Info */}
                    {result.tier && (
                      <div className="tier-info" style={{marginTop: '12px', fontSize: '0.85rem', color: '#6b7280'}}>
                        Validation Tier: <strong style={{textTransform: 'uppercase'}}>{result.tier}</strong>
                      </div>
                    )}
                  </div>

                  {/* Deliverability Score */}
                  {result.deliverability && (
                    <div className="pro-score-card deliverability">
                      <div className="pro-score-label">Deliverability Score</div>
                      <div className="pro-score-value">{result.deliverability.deliverability_score}<span style={{fontSize: '1.5rem', color: '#6b7280'}}>/100</span></div>
                      <div className="pro-score-bar">
                        <div
                          className="pro-score-bar-fill"
                          style={{
                            width: `${result.deliverability.deliverability_score}%`,
                            backgroundColor: result.deliverability.deliverability_score >= 80 ? '#10b981' : 
                                           result.deliverability.deliverability_score >= 60 ? '#f59e0b' : '#ef4444'
                          }}
                        />
                      </div>
                      <span 
                        className="pro-score-grade"
                        style={{ 
                          backgroundColor: result.deliverability.deliverability_score >= 80 ? '#10b981' : 
                                         result.deliverability.deliverability_score >= 60 ? '#f59e0b' : '#ef4444'
                        }}
                      >
                        Grade {result.deliverability.deliverability_grade}
                      </span>
                      <div className="pro-score-text" style={{marginTop: '12px'}}>{result.deliverability.recommendation}</div>
                    </div>
                  )}
                </div>

                {/* Confidence-Based Warning Banner */}
                {result.confidence_score !== undefined && result.confidence_score < 70 && (
                  <div className="confidence-warning-banner" style={{
                    backgroundColor: result.confidence_score < 30 ? '#fee2e2' : '#fef3c7',
                    border: `2px solid ${result.confidence_score < 30 ? '#ef4444' : '#f59e0b'}`,
                    borderRadius: '12px',
                    padding: '16px 20px',
                    marginBottom: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                  }}>
                    <FiAlertTriangle style={{
                      fontSize: '24px',
                      color: result.confidence_score < 30 ? '#ef4444' : '#f59e0b',
                      flexShrink: 0
                    }} />
                    <div>
                      <div style={{
                        fontWeight: '600',
                        fontSize: '1rem',
                        color: result.confidence_score < 30 ? '#991b1b' : '#92400e',
                        marginBottom: '4px'
                      }}>
                        {result.confidence_score < 40 ? '⚠️ Critical: Bad Email Quality' : '⚠️ Warning: Low Confidence Email'}
                      </div>
                      <div style={{
                        fontSize: '0.9rem',
                        color: result.confidence_score < 30 ? '#7f1d1d' : '#78350f'
                      }}>
                        {result.confidence_score < 40 
                          ? 'This email has very low confidence score. It is likely invalid or risky. We recommend not using this email address.'
                          : 'This email has a low confidence score. Additional verification may be needed before using this address.'}
                      </div>
                      {result.tier && (
                        <div style={{
                          fontSize: '0.85rem',
                          color: '#6b7280',
                          marginTop: '8px',
                          fontStyle: 'italic'
                        }}>
                          Applied {result.tier.toUpperCase()} tier validation - {
                            result.tier === 'low' ? 'minimal filters (syntax only)' :
                            result.tier === 'medium' ? 'moderate filters (DNS, MX, disposable)' :
                            'all filters (DNS, MX, disposable, role-based, typo detection)'
                          }
                        </div>
                      )}
                    </div>
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

                {result.bounce_check && result.bounce_check.has_bounced && (
                  <div className={`bounce-warning-section ${result.bounce_check?.risk_level || 'medium'}`}>
                    <h3>⚠️ Bounce History Detected</h3>
                    <div className="bounce-warning-content">
                      <div className="bounce-stats">
                        <div className="bounce-stat">
                          <strong>{result.bounce_check?.total_bounces || 0}</strong>
                          <span>Total Bounces</span>
                        </div>
                        <div className="bounce-stat">
                          <strong>{result.bounce_check?.hard_bounces || 0}</strong>
                          <span>Hard Bounces</span>
                        </div>
                        <div className="bounce-stat">
                          <strong>{result.bounce_check?.soft_bounces || 0}</strong>
                          <span>Soft Bounces</span>
                        </div>
                      </div>
                      
                      {result.bounce_check?.warning && (
                        <div className="bounce-warning">
                          {result.bounce_check.warning}
                        </div>
                      )}
                      
                      {result.bounce_info?.last_bounce && (
                        <div style={{
                          marginTop: '12px',
                          fontSize: '0.9rem',
                          color: '#6b7280'
                        }}>
                          Last bounce: {new Date(result.bounce_info?.last_bounce).toLocaleDateString()}
                        </div>
                      )}
                      
                      <div style={{
                        marginTop: '16px',
                        padding: '12px 16px',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid #ef4444',
                        borderRadius: '8px',
                        color: '#991b1b',
                        fontWeight: '600'
                      }}>
                        ⚠️ This email has failed delivery before. Use with caution.
                      </div>
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

                {/* Validation Checks */}
                <div className="pro-checks-grid">
                  <div className={`pro-check-item ${result.checks.syntax ? 'pass' : 'fail'}`}>
                    <span className="pro-check-icon">{result.checks.syntax ? '✓' : '✗'}</span>
                    <span>Valid Syntax</span>
                  </div>
                  <div className={`pro-check-item ${result.checks.dns_valid ? 'pass' : 'fail'}`}>
                    <span className="pro-check-icon">{result.checks.dns_valid ? '✓' : '✗'}</span>
                    <span>DNS Valid</span>
                  </div>
                  <div className={`pro-check-item ${result.checks.mx_records ? 'pass' : 'fail'}`}>
                    <span className="pro-check-icon">{result.checks.mx_records ? '✓' : '✗'}</span>
                    <span>MX Records Found</span>
                  </div>
                  <div className={`pro-check-item ${!result.checks.is_disposable ? 'pass' : 'warn'}`}>
                    <span className="pro-check-icon">{!result.checks.is_disposable ? '✓' : '⚠'}</span>
                    <span>{result.checks.is_disposable ? 'Disposable Email' : 'Not Disposable'}</span>
                  </div>
                  <div className={`pro-check-item ${!result.checks.is_role_based ? 'pass' : 'warn'}`}>
                    <span className="pro-check-icon">{!result.checks.is_role_based ? '✓' : '⚠'}</span>
                    <span>{result.checks.is_role_based ? 'Role-Based Email' : 'Personal Email'}</span>
                  </div>
                  {result.bounce_info && (
                    <div className={`pro-check-item ${
                      result.bounce_info?.has_bounced ? 'warn' : 'pass'
                    }`}>
                      <span className="pro-check-icon">
                        {result.bounce_info?.has_bounced ? '⚠' : '✓'}
                      </span>
                      <span>
                        {result.bounce_check?.has_bounced 
                          ? `${result.bounce_check.total_bounces || 0} Bounce${(result.bounce_check.total_bounces || 0) > 1 ? 's' : ''}`
                          : 'No Bounces'}
                      </span>
                    </div>
                  )}
                </div>

                {/* Warnings */}
                {(result.checks.is_disposable || result.checks.is_role_based) && (
                  <div className="pro-info-box warning">
                    <strong><FiAlertTriangle style={{display: 'inline', marginRight: '8px'}} /> Warning:</strong> {' '}
                    {result.checks.is_disposable && 'This is a disposable/temporary email address. '}
                    {result.checks.is_role_based && 'This is a role-based email (e.g., info@, support@). '}
                    Not recommended for important communications.
                  </div>
                )}

                {/* Suggestion */}
                {result.suggestion && (
                  <div className="pro-info-box suggestion">
                    <strong><FiAlertCircle style={{display: 'inline', marginRight: '8px'}} /> Did you mean:</strong> <strong>{result.suggestion}</strong>?
                  </div>
                )}

                {/* Reason/Details */}
                {result.reason && (
                  <div className="pro-info-box reason">
                    <strong><FiFileText style={{display: 'inline', marginRight: '8px'}} /> Details:</strong> {result.reason}
                  </div>
                )}
              </>
            )}

            {/* Basic Mode Note */}
            {mode === 'basic' && (
              <div className="pro-info-box" style={{background: 'linear-gradient(135deg, #fef3c7 0%, white 100%)', borderColor: '#f59e0b', color: '#92400e'}}>
                <strong><FiZap style={{display: 'inline', marginRight: '8px'}} /> Basic Mode:</strong> Switch to Advanced Mode for full validation with DNS, MX records, deliverability scoring, and AI-powered analysis.
              </div>
            )}

            {/* Processing Time */}
            <div className="pro-meta-info">
              <FiActivity style={{display: 'inline', marginRight: '8px'}} /> Processing time: {result.processing_time}s
            </div>
            </div>

          </div>
        )}

        {batchResults && (
          <div className="batch-results">
            <div className="batch-summary">
              <div className="batch-header">
                <h2>Batch Results</h2>
                
                {/* Compact Progress & Controls */}
                {loading && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px',
                    marginBottom: '16px',
                    padding: '12px 16px',
                    background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
                    borderRadius: '12px',
                    color: 'white',
                    fontSize: '0.875rem'
                  }}>
                    <span>🚀 {progress.current}/{progress.total} ({progress.percentage}%)</span>
                    <span>✅ {batchResults?.valid_count || 0} Valid</span>
                    <span>❌ {batchResults?.invalid_count || 0} Invalid</span>
                    <span>⚡ {progress.speed}/sec</span>
                    <span>⏱️ {progress.eta}s ETA</span>
                    <button 
                      onClick={() => setShowBatchResults(!showBatchResults)}
                      style={{
                        background: 'rgba(255,255,255,0.2)',
                        border: '1px solid rgba(255,255,255,0.3)',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.75rem'
                      }}
                    >
                      {showBatchResults ? 'Hide' : 'Show'} Results
                    </button>
                  </div>
                )}
                
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
                {batchResults.results && batchResults.results[0]?.batch_performance && (
                  <div className="performance-metrics" style={{
                    marginTop: '12px',
                    padding: '12px',
                    backgroundColor: '#f8fafc',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0'
                  }}>
                    <h4 style={{margin: '0 0 8px 0', fontSize: '0.9rem', color: '#374151'}}>
                      ⚡ Performance Metrics
                    </h4>
                    <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '8px', fontSize: '0.85rem'}}>
                      <div>
                        <strong>Speed:</strong> {batchResults.results[0].batch_performance.emails_per_second} emails/sec
                      </div>
                      <div>
                        <strong>Workers:</strong> {batchResults.results[0].batch_performance.parallel_workers_used}
                      </div>
                      {batchResults.results[0].batch_performance.dns_cache_hit_rate !== undefined && (
                        <div>
                          <strong>Cache Hit Rate:</strong> {batchResults.results[0].batch_performance.dns_cache_hit_rate}%
                        </div>
                      )}
                      <div>
                        <strong>Validity Rate:</strong> {batchResults.results[0].batch_performance.validity_rate}%
                      </div>
                    </div>
                    
                    {batchResults.results[0].batch_performance.tier_distribution && (
                      <div style={{marginTop: '8px'}}>
                        <strong>Tier Distribution:</strong>
                        <div style={{display: 'flex', gap: '12px', marginTop: '4px', flexWrap: 'wrap'}}>
                          {Object.entries(batchResults.results[0].batch_performance.tier_distribution).map(([tier, count]) => (
                            <span key={tier} style={{
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontSize: '0.8rem',
                              backgroundColor: tier === 'premium' ? '#dcfce7' : 
                                             tier === 'high' ? '#dbeafe' :
                                             tier === 'medium' ? '#fef3c7' :
                                             tier === 'basic' ? '#fed7aa' : '#fee2e2',
                              color: tier === 'premium' ? '#166534' : 
                                     tier === 'high' ? '#1e40af' :
                                     tier === 'medium' ? '#92400e' :
                                     tier === 'basic' ? '#c2410c' : '#991b1b'
                            }}>
                              {tier}: {count}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {batchResults.results[0].batch_performance.dns_queries_saved > 0 && (
                      <div style={{marginTop: '8px', color: '#059669', fontSize: '0.85rem'}}>
                        💰 Saved {batchResults.results[0].batch_performance.dns_queries_saved} DNS queries through caching
                      </div>
                    )}
                  </div>
                )}
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

            {showBatchResults && (
              <div className="batch-list" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {batchResults.results.map((item, index) => (
                <div key={index} className={`result-box batch-result-card ${item.valid ? 'valid' : 'invalid'}`}>
                  <div className="result-header">
                    <div className="result-title-row">
                      <h3 className="batch-result-title">{item.valid ? 'Valid Email' : 'Invalid Email'}</h3>
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

                  <div className="result-body">
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
                        <div className="confidence-value" style={{
                          color: getConfidenceTextColor(item.confidence_score || 0),
                          fontWeight: '600'
                        }}>
                          {item.confidence_score || 0}/100 - {getConfidenceLabel(item.confidence_score || 0)}
                        </div>
                        
                        {/* Low Confidence Warning */}
                        {item.confidence_score !== undefined && item.confidence_score < 70 && (
                          <div style={{
                            marginTop: '12px',
                            padding: '10px 12px',
                            backgroundColor: item.confidence_score < 40 ? '#fee2e2' : '#fef3c7',
                            border: `1px solid ${item.confidence_score < 40 ? '#ef4444' : '#f59e0b'}`,
                            borderRadius: '8px',
                            fontSize: '0.85rem',
                            color: item.confidence_score < 40 ? '#991b1b' : '#92400e'
                          }}>
                            <strong>{item.confidence_score < 40 ? '⚠️ Bad Email' : '⚠️ Low Confidence'}</strong>
                            <div style={{marginTop: '4px', fontSize: '0.8rem'}}>
                              {item.confidence_score < 40 
                                ? 'Very low quality - not recommended for use'
                                : 'Additional verification recommended'}
                            </div>
                          </div>
                        )}
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
                          <h4>Risk Detection</h4>
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

                      {item.bounce_check?.bounce_history?.has_bounced && (
                        <div className={`bounce-warning-section ${item.bounce_check?.risk_level || 'medium'}`}>
                          <h4>Bounce History</h4>
                          <div className="bounce-warning-content">
                            <div className="bounce-stats">
                              <div className="bounce-stat">
                                <strong>{item.bounce_check?.bounce_history?.total_bounces || 0}</strong>
                                <span>Total Bounces</span>
                              </div>
                              <div className="bounce-stat">
                                <strong>{item.bounce_check?.bounce_history?.hard_bounces || 0}</strong>
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
                </div>
              ))}
              </div>
            )}
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

          </div>
          {/* End pro-content */}
        </div>
        {/* End pro-main-card */}
      </div>
      {/* End pro-container */}

      {/* Footer */}
      <footer className="pro-footer">
        <p><FiShield style={{display: 'inline', marginRight: '8px'}} /> Powered by RFC 5321 compliant validation engine with AI-powered analysis</p>
        <p><FiAward style={{display: 'inline', marginRight: '8px'}} /> Features: DNS Verification • MX Records • Pattern Analysis • Email Enrichment • Deliverability Scoring • Disposable Detection</p>
        <div className="pro-footer-lagic">
          <p><strong>LAGIC</strong> - Lead Audience Growth Intelligence Computing</p>
          <p>© 2025 LAGIC. All rights reserved. | Enterprise Email Validation Solution</p>
        </div>
      </footer>
    </div>
  );
}

export default App;

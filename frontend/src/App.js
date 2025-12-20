import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import './AppModern.css';
import './AppPro.css';
import { 
  FiMail, FiRefreshCw, 
  FiTrash2, FiDownload, FiCopy, FiCheckCircle, FiXCircle,
  FiZap, FiCpu, FiInbox, FiList, FiClock, FiAlertTriangle,
  FiAlertCircle, FiFileText,
  FiShield, FiActivity, FiAward, FiMoon, FiSun, FiUser, FiLogOut,
  FiInfo, FiHelpCircle, FiX, FiLink, FiUsers
} from 'react-icons/fi';
import BatchResultsPaginated from './BatchResultsPaginated';
import HistoryPaginated from './HistoryPaginated';
import { getCorrectApiLimit, formatApiLimit, formatApiUsageWithPeriod } from './utils/apiUtils';


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

// Local storage history management for anonymous users ONLY
function saveValidationToLocalStorage(validationResult, user) {
  // Skip localStorage for authenticated users - they use database storage
  if (user) {
    console.log('🔐 Authenticated user - using database storage, skipping localStorage');
    return null;
  }
  
  // Skip test emails completely
  if (validationResult.email && (
    validationResult.email.includes('example.test') || 
    validationResult.email.includes('@temp.com') ||
    validationResult.email.startsWith('user0')
  )) {
    console.log('🧪 Skipping test email localStorage save:', validationResult.email);
    return null;
  }
  
  try {
    const historyData = localStorage.getItem('validation_history');
    const history = historyData && historyData !== 'undefined' ? JSON.parse(historyData) : [];
    
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
    
    // Keep only last 50 records for anonymous users (reduced from 1000)
    if (history.length > 50) {
      history.splice(50);
    }
    
    localStorage.setItem('validation_history', JSON.stringify(history));
    // Reduced logging for performance
    if (history.length % 10 === 0) {
      console.log(`💾 Saved ${history.length} validations to localStorage (anonymous only)`);
    }
    
    return record;
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
    return null;
  }
}

function cleanupTestDataFromLocalStorage() {
  try {
    const historyData = localStorage.getItem('validation_history');
    if (!historyData || historyData === 'undefined') return;
    
    const history = JSON.parse(historyData);
    const cleanHistory = history.filter(record => 
      record.email && 
      !record.email.includes('example.test') && 
      !record.email.includes('@temp.com') &&
      !record.email.startsWith('user0')
    );
    
    if (cleanHistory.length !== history.length) {
      localStorage.setItem('validation_history', JSON.stringify(cleanHistory));
      console.log(`🧹 Cleaned ${history.length - cleanHistory.length} test emails from localStorage`);
    }
  } catch (error) {
    console.error('Failed to cleanup test data:', error);
  }
}

function getLocalStorageHistory() {
  try {
    const historyData = localStorage.getItem('validation_history');
    return historyData && historyData !== 'undefined' ? JSON.parse(historyData) : [];
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
  
  // Custom modal system
  const [showModal, setShowModal] = useState(false);
  const [modalConfig, setModalConfig] = useState({
    title: '',
    message: '',
    type: 'info', // 'info', 'confirm', 'warning', 'error', 'success'
    onConfirm: null,
    onCancel: null,
    confirmText: 'OK',
    cancelText: 'Cancel'
  });

  // Modal helper functions
  const showInfoModal = (title, message) => {
    setModalConfig({
      title,
      message,
      type: 'info',
      onConfirm: () => setShowModal(false),
      onCancel: null,
      confirmText: 'OK',
      cancelText: 'Cancel'
    });
    setShowModal(true);
  };

  const showSuccessModal = (title, message) => {
    setModalConfig({
      title,
      message,
      type: 'success',
      onConfirm: () => setShowModal(false),
      onCancel: null,
      confirmText: 'OK',
      cancelText: 'Cancel'
    });
    setShowModal(true);
  };

  const showErrorModal = (title, message) => {
    setModalConfig({
      title,
      message,
      type: 'error',
      onConfirm: () => setShowModal(false),
      onCancel: null,
      confirmText: 'OK',
      cancelText: 'Cancel'
    });
    setShowModal(true);
  };

  const showConfirmModal = (title, message, onConfirm, confirmText = 'Confirm', cancelText = 'Cancel') => {
    setModalConfig({
      title,
      message,
      type: 'confirm',
      onConfirm: () => {
        setShowModal(false);
        if (onConfirm) onConfirm();
      },
      onCancel: () => setShowModal(false),
      confirmText,
      cancelText
    });
    setShowModal(true);
  };

  
  // User status cache to avoid frequent API calls
  const [lastStatusCheck, setLastStatusCheck] = useState(0);
  const STATUS_CHECK_INTERVAL = 30000; // 30 seconds
  
  // Anonymous user validation tracking
  const [anonValidationCount, setAnonValidationCount] = useState(() => {
    try {
      return parseInt(localStorage.getItem('anon_validation_count') || '0');
    } catch {
      return 0;
    }
  });
  const ANON_VALIDATION_LIMIT = 2;
  
  const [history, setHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('today'); // Default to today
  const [historyLoading, setHistoryLoading] = useState(false);
  
  // Authentication state
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('user');
      return savedUser && savedUser !== 'undefined' ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [authToken, setAuthToken] = useState(() => {
    return localStorage.getItem('authToken') || null;
  });
  
  const [anonUserId] = useState(() => getAnonUserId());
  const [darkMode, setDarkMode] = useState(() => {
    try {
      const saved = localStorage.getItem('darkMode');
      return saved && saved !== 'undefined' ? JSON.parse(saved) : false;
    } catch {
      return false;
    }
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
    try {
      const savedAdminUser = localStorage.getItem('adminUser');
      const user = savedAdminUser && savedAdminUser !== 'undefined' ? JSON.parse(savedAdminUser) : null;
      console.log('👤 Initial admin user:', user);
      return user;
    } catch {
      console.log('👤 Failed to parse admin user from localStorage');
      return null;
    }
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
      if (user && user !== 'undefined') {
        try {
          const parsedUser = JSON.parse(user);
          if (JSON.stringify(parsedUser) !== JSON.stringify(adminUser)) {
            console.log('👤 Admin user changed:', parsedUser);
            setAdminUser(parsedUser);
          }
        } catch (e) {
          console.error('Failed to parse admin user:', e);
          setAdminUser(null);
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
    // Clean up test data from localStorage on app load
    cleanupTestDataFromLocalStorage();
    
    const refreshUserData = async (forceRefresh = false) => {
      if (authToken && user) {
        try {
          const response = await api.get('/api/auth/me');
          if (response.status === 200) {
            const updatedUser = response.data.user;
            
            // Check if tier has changed (team membership effect)
            const tierChanged = user.subscriptionTier !== updatedUser.subscriptionTier;
            if (tierChanged) {
              console.log(`🔄 Tier changed: ${user.subscriptionTier} → ${updatedUser.subscriptionTier}`);
            }
            
            setUser(updatedUser);
            localStorage.setItem('user', JSON.stringify(updatedUser));
            console.log('🔄 User data refreshed from server', forceRefresh ? '(forced)' : '');
            
            // If tier changed to pro due to team membership, show notification
            if (tierChanged && updatedUser.subscriptionTier === 'pro' && updatedUser.teamId) {
              console.log('✅ Pro access activated via team membership!');
            }
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

    refreshUserData(true); // Force refresh on app load
    
    // Set up periodic refresh every 60 seconds (reduced from 10s to prevent token issues)
    const userRefreshInterval = setInterval(() => {
      if (authToken && user) {
        refreshUserData();
      }
    }, 60000); // Refresh every 60 seconds (much less aggressive)
    
    // Refresh when page becomes visible (user comes back from invitation)
    const handleVisibilityChange = () => {
      if (!document.hidden && authToken && user) {
        console.log('🔄 Page visible, force refreshing user data...');
        refreshUserData(true); // Force refresh when page becomes visible
      }
    };
    
    // Refresh when window gets focus (user switches back to tab)
    const handleFocus = () => {
      if (authToken && user) {
        console.log('🔄 Window focused, force refreshing user data...');
        refreshUserData(true); // Force refresh when window gets focus
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);
    
    // Cleanup
    return () => {
      clearInterval(userRefreshInterval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [authToken, user, handleLogout, api]); // Run once on app load

  // Check for team join success and refresh user data immediately
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('joined') === 'success' && authToken && user) {
      console.log('🎉 Team join detected, refreshing user data immediately...');
      
      // Immediate refresh for team join with retry logic
      const immediateRefresh = async (retryCount = 0) => {
        try {
          const response = await api.get('/api/auth/me');
          if (response.status === 200) {
            const updatedUser = response.data.user;
            
            // Check if user now has Pro tier
            if (updatedUser.subscriptionTier === 'pro' && updatedUser.teamId) {
              setUser(updatedUser);
              localStorage.setItem('user', JSON.stringify(updatedUser));
              console.log('✅ User data updated after team join - now Pro tier!');
              
              // Show success message
              showInfoModal('Welcome to the Team!', 'You now have Pro access with shared team quota. Your subscription tier has been updated.');
            } else if (retryCount < 3) {
              // If still not Pro tier, retry after a short delay
              console.log(`🔄 User still not Pro tier, retrying in 1 second... (attempt ${retryCount + 1}/3)`);
              setTimeout(() => immediateRefresh(retryCount + 1), 1000);
            } else {
              // After 3 retries, update anyway and show manual refresh option
              setUser(updatedUser);
              localStorage.setItem('user', JSON.stringify(updatedUser));
              console.log('⚠️ User data updated but tier may not be current. Manual refresh may be needed.');
            }
          }
        } catch (error) {
          console.error('Failed to refresh user data after team join:', error);
          if (retryCount < 3) {
            setTimeout(() => immediateRefresh(retryCount + 1), 1000);
          }
        }
      };
      
      immediateRefresh();
      
      // Clean up URL parameter
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  }, [authToken, user, api, showInfoModal]);

  // Helper function for immediate suspension checking
  const checkUserStatus = useCallback(async (forceCheck = false) => {
    if (!user || !authToken) return true; // Not logged in, no need to check
    
    // Skip check if recently checked (unless forced)
    const now = Date.now();
    if (!forceCheck && (now - lastStatusCheck) < STATUS_CHECK_INTERVAL) {
      return true; // Assume user is still active
    }
    
    try {
      await api.get('/api/auth/check-status');
      setLastStatusCheck(now);
      return true; // User is still active
    } catch (error) {
      if (error.response?.status === 403 && error.response?.data?.suspended) {
        // User has been suspended!
        const suspensionData = error.response.data;
        
        // Show suspension notification
        showErrorModal(
          'Account Suspended',
          `Your account has been suspended.\n\nReason: ${suspensionData.reason}\nDate: ${new Date(suspensionData.suspended_at).toLocaleString()}\n\nYou will be logged out automatically.`
        );
        
        // Force logout
        handleLogout();
        return false; // User is suspended
      }
      setLastStatusCheck(now);
      return true; // Other errors, assume user is still active
    }
  }, [user, authToken, api, handleLogout, lastStatusCheck]);

  const [historyLoaded, setHistoryLoaded] = useState(false);

  // Reset history loaded state when user changes
  useEffect(() => {
    setHistoryLoaded(false);
  }, [user?.id]);

  const loadHistory = useCallback(async (forceReload = false) => {
    // Don't reload if already loaded unless forced
    if (historyLoaded && !forceReload) {
      return;
    }

    try {
      if (user) {
        // Only show loading for authenticated users (database calls)
        setHistoryLoading(true);
        
        // Authenticated user - load from database with pagination
        const response = await api.get('/api/history?limit=500'); // Load more but still reasonable
        const historyData = response.data.history || [];
        
        setHistory(historyData);
        setHistoryLoaded(true);
        
        console.log(`📊 Loaded ${historyData.length} database records for authenticated user: ${user.firstName} ${user.lastName}`);
      } else {
        // Anonymous user - load from localStorage (instant, no loading state)
        const localHistory = getLocalStorageHistory();
        
        setHistory(localHistory);
        setHistoryLoaded(true);
        
        console.log(`📊 Loaded ${localHistory.length} localStorage records for anonymous user`);
      }
      
    } catch (err) {
      console.error('History loading error:', err);
      if (user) {
        setError('Failed to load history from server');
      } else {
        // Fallback to empty history for localStorage errors
        setHistory([]);
        setHistoryLoaded(true);
      }
    } finally {
      if (user) {
        setHistoryLoading(false);
      }
    }
  }, [user, api, historyLoaded]);

  useEffect(() => {
    // Clean up signup success URL parameter (no alert needed)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('signup') === 'success') {
      // Clean up URL without showing alert
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    // Handle shared batch results
    const shareId = urlParams.get('share');
    if (shareId) {
      const loadSharedData = async () => {
        try {
          setLoading(true);
          
          // Get shared data from backend API
          const response = await api.get(`/api/share/${shareId}`);
          
          if (response.data.success) {
            const sharedData = response.data.data;
            
            // Set batch mode and load shared results
            setBatchMode(true);
            setHistoryMode(false);
            setBatchResults({
              results: sharedData.results,
              valid_count: sharedData.metadata.valid_count,
              invalid_count: sharedData.metadata.invalid_count,
              total: sharedData.metadata.total_emails,
              original_count: sharedData.metadata.total_emails,
              duplicates_removed: sharedData.metadata.duplicates_removed,
              processing_time: sharedData.metadata.processing_time,
              domain_stats: sharedData.domain_statistics,
              shared: true, // Mark as shared data
              sharedBy: sharedData.shared_by,
              generatedAt: sharedData.created_at
            });
            
            // Set mode based on shared data
            if (sharedData.metadata.validation_mode) {
              setMode(sharedData.metadata.validation_mode);
            }
            
            console.log('📤 Loaded shared batch results from backend:', sharedData.metadata);
            
          } else {
            setError('Shared results not found or have expired.');
          }
          
        } catch (error) {
          console.error('❌ Failed to load shared data:', error);
          if (error.response?.status === 404) {
            setError('Shared results not found or have expired.');
          } else if (error.response?.status === 410) {
            setError('This shared link has expired. Shared results are only available for 7 days.');
          } else {
            setError('Failed to load shared results.');
          }
        } finally {
          setLoading(false);
          // Clean up URL after loading (success or failure)
          window.history.replaceState({}, document.title, window.location.pathname);
        }
      };
      
      loadSharedData();
    }
    
    // Load history in background when user changes (but don't show loading)
    if (user || (!user && !historyLoaded)) {
      loadHistory();
    }
  }, [user, historyMode, loadHistory]);

  // Real-time suspension monitoring
  useEffect(() => {
    if (!user || !authToken) return;

    // Check status every 30 seconds for suspension detection
    const statusInterval = setInterval(() => checkUserStatus(true), 30000);

    // Cleanup interval on unmount
    return () => clearInterval(statusInterval);
  }, [user, authToken, checkUserStatus]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  // Helper functions for confidence scoring
  const getConfidenceColor = (score) => {
    if (score >= 90) return '#10b981'; // Green
    if (score >= 70) return '#f59e0b'; // Yellow
    if (score >= 50) return '#ef4444'; // Red
    return '#6b7280'; // Gray
  };

  const getConfidenceTextColor = (score) => {
    if (score >= 90) return '#059669';
    if (score >= 70) return '#d97706';
    if (score >= 50) return '#dc2626';
    return '#4b5563';
  };

  const getConfidenceLabel = (score) => {
    if (score >= 90) return 'Excellent';
    if (score >= 80) return 'Very Good';
    if (score >= 70) return 'Good';
    if (score >= 60) return 'Fair';
    if (score >= 50) return 'Poor';
    return 'Very Poor';
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



  const generateShareLink = async () => {
    if (!batchResults || !batchResults.results) return;

    setLoading(true);
    
    try {
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
        results: batchResults.results,
        shared_by: user ? `${user.firstName} ${user.lastName}` : 'Anonymous User'
      };

      // Send to backend API
      const response = await api.post('/api/share', shareData);
      
      if (response.data.success) {
        const shareUrl = `${window.location.origin}${window.location.pathname}?share=${response.data.share_id}`;
        setShareLink(shareUrl);
        setShowShareModal(true);
        
        console.log('🔗 Generated share link:', shareUrl);
        console.log('📅 Expires:', new Date(response.data.expires_at).toLocaleDateString());
      } else {
        setError('Failed to create share link');
      }
      
    } catch (error) {
      console.error('Share creation failed:', error);
      setError('Failed to create share link. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const copyShareLink = () => {
    if (!shareLink) return;
    
    navigator.clipboard.writeText(shareLink).then(() => {
      showSuccessModal('Success', 'Share link copied to clipboard!');
    }).catch(() => {
      showErrorModal('Error', 'Failed to copy link');
    });
  };

  const copyToClipboard = () => {
    if (!batchResults || !batchResults.results) return;

    const text = batchResults.results
      .map(r => `${r.valid ? '✓' : '✗'} ${r.email}`)
      .join('\n');

    navigator.clipboard.writeText(text).then(() => {
      showSuccessModal('Success', 'Results copied to clipboard!');
    });
  };

  const validateEmail = async () => {
    if (!email.trim()) {
      setError('Please enter an email address');
      return;
    }

    // Clear previous results
    setError(null);
    setResult(null);

    // Check if authenticated user has reached their limit (skip for admin mode)
    const correctLimit = getCorrectApiLimit(user?.subscriptionTier);
    if (!adminMode && user && user.apiCallsCount >= correctLimit) {
      setError(`You've reached your limit of ${formatApiLimit(user.subscriptionTier)} API calls. ${
        user.subscriptionTier === 'free' ? 'Upgrade to Starter (10K calls) or Pro (10M calls) for more validations!' : 
        user.subscriptionTier === 'starter' ? 'Upgrade to Pro (10M calls) for more validations!' : 
        'You have reached your Pro tier limit. Please contact support if you need more.'
      }`);
      return;
    }
    
    // Check if anonymous user has reached their limit
    if (!adminMode && !user && anonValidationCount >= ANON_VALIDATION_LIMIT) {
      setError(`Anonymous users can only validate ${ANON_VALIDATION_LIMIT} emails. Please sign up for unlimited access!`);
      return;
    }

    // Show loading only after limit checks pass
    setLoading(true);

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
        const updatedUser = { ...user };
        
        // Check if this is team quota or individual quota
        if (response.data.api_usage.is_team_quota && user.teamInfo) {
          // Update team quota
          updatedUser.teamInfo = {
            ...user.teamInfo,
            quota_used: response.data.api_usage.calls_used
          };
          console.log(`🔄 Team quota updated: ${response.data.api_usage.calls_used}/${response.data.api_usage.calls_limit} (${response.data.api_usage.team_name})`);
        } else {
          // Update individual quota
          updatedUser.apiCallsCount = response.data.api_usage.calls_used;
          console.log(`🔄 Individual API usage updated: ${response.data.api_usage.calls_used}/${response.data.api_usage.calls_limit}`);
        }
        
        setUser(updatedUser);
        localStorage.setItem('user', JSON.stringify(updatedUser));
      }
      
      // Save to localStorage for anonymous users and increment count
      if (!user && response.data) {
        saveValidationToLocalStorage(response.data, user);
        const newCount = anonValidationCount + 1;
        setAnonValidationCount(newCount);
        localStorage.setItem('anon_validation_count', newCount.toString());
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
    const correctLimit = getCorrectApiLimit(user?.subscriptionTier);
    if (!adminMode && user && user.apiCallsCount >= correctLimit) {
      setError(`You've reached your limit of ${formatApiLimit(user.subscriptionTier)} API calls. ${
        user.subscriptionTier === 'free' ? 'Upgrade to Starter (10K calls) or Pro (10M calls) for more validations!' : 
        user.subscriptionTier === 'starter' ? 'Upgrade to Pro (10M calls) for more validations!' : 
        'You have reached your Pro tier limit. Please contact support if you need more.'
      }`);
      return;
    }

    // Check if batch would exceed user's remaining limit (skip for admin mode)
    if (!adminMode && user) {
      const remainingCalls = correctLimit - user.apiCallsCount;
      if (emails.length > remainingCalls) {
        setError(`This batch contains ${emails.length} emails, but you only have ${remainingCalls.toLocaleString()} API calls remaining. ${
          user.subscriptionTier === 'free' ? 'Upgrade to Starter (10K calls) or Pro (10M calls) for more validations!' : 
          user.subscriptionTier === 'starter' ? 'Upgrade to Pro (10M calls) for more validations!' : 
          'Please reduce the batch size or contact support if you need more capacity.'
        }`);
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

    // Declare timeout variables outside try block
    let controller = null;
    let timeoutId = null;

    try {
      // Use different endpoint based on mode
      let endpoint;
      
      // Ensure anonUserId is always available
      const currentAnonUserId = anonUserId || getAnonUserId();
      
      const headers = {
        'Content-Type': 'application/json',
        'X-User-ID': currentAnonUserId // Always include X-User-ID for backend tracking
      };
      
      if (adminMode) {
        // Admin mode: Use admin endpoint (non-streaming, unlimited)
        endpoint = '/api/admin/validate/batch';
        headers['Authorization'] = `Bearer ${adminToken}`;
        delete headers['X-User-ID']; // Admin doesn't need X-User-ID
        
        console.log('🛡️ Admin batch validation:', {
          adminMode,
          endpoint,
          emailCount: emails.length
        });
      } else if (user) {
        // Authenticated users: Use STREAMING endpoint with auth token
        endpoint = '/api/validate/batch/stream';
        headers['Authorization'] = `Bearer ${authToken}`;
        // Keep X-User-ID for backend compatibility
        
        console.log('🔐 Authenticated batch validation (streaming):', {
          user: user.email,
          endpoint,
          emailCount: emails.length
        });
      } else {
        // Anonymous users: Use local streaming endpoint
        endpoint = '/api/validate/batch/local';
        // Keep X-User-ID for anonymous users
        
        console.log('👤 Anonymous batch validation (streaming):', {
          endpoint,
          emailCount: emails.length,
          anonUserId: currentAnonUserId
        });
      }

        // Debug: Log request details
        console.log('📤 Sending batch validation request:', {
          endpoint: `${API_URL}${endpoint}`,
          fullUrl: `${API_URL}${endpoint}`,
          headers: headers,
          emailCount: emails.length,
          mode: mode,
          adminMode: adminMode,
          user: user ? user.email : 'anonymous'
        });

        // Create timeout controller for better browser compatibility
        controller = new AbortController();
        timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout

        const response = await fetch(`${API_URL}${endpoint}`, {
          method: 'POST',
          headers: headers,
          body: JSON.stringify({
            emails,
            advanced: mode === 'advanced',
            remove_duplicates: removeDuplicates
          }),
          signal: controller.signal
        });

        clearTimeout(timeoutId); // Clear timeout if request succeeds

        console.log('📥 Response status:', response.status, response.statusText);

        if (!response.ok) {
          let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
          try {
            const errorData = await response.json();
            errorMessage = errorData.message || errorMessage;
          } catch (e) {
            console.log('Could not parse error response as JSON');
          }
          throw new Error(errorMessage);
        }

        // Check if this is a streaming response (anonymous and authenticated users, but not admin)
        const isStreaming = !adminMode;

        if (isStreaming) {
          // Handle streaming response for anonymous users
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          
          // Optimized batch updates to eliminate lag
          let pendingResults = [];
          let lastUpdateTime = Date.now();
          const UPDATE_INTERVAL = 100; // Update UI every 100ms to reduce re-renders
          const BATCH_SIZE = 20; // Larger batches for fewer updates

          // Initialize results immediately for real-time display
          setBatchResults({
            results: [],
            valid_count: 0,
            invalid_count: 0,
            total: emails.length,
            original_count: emails.length,
            duplicates_removed: 0,
            processing_time: 0,
            domain_stats: null
          });

          const flushPendingResults = () => {
            if (pendingResults.length === 0) return;
            
            // Use functional update with pre-calculated values for speed
            const newResults = pendingResults.slice(); // Copy array
            const validCount = newResults.filter(r => r.valid).length;
            const invalidCount = newResults.length - validCount;
            
            setBatchResults(prev => ({
              ...prev,
              results: prev.results.concat(newResults), // Faster than spread
              valid_count: prev.valid_count + validCount,
              invalid_count: prev.invalid_count + invalidCount
            }));
            
            // Save to localStorage in batch (only for anonymous users)
            if (!user) {
              newResults.forEach(result => {
                if (result) saveValidationToLocalStorage(result, user);
              });
            }
            
            pendingResults = [];
          };

          try {
            while (true) {
              const { done, value } = await reader.read();
              
              if (done) {
                // Flush any remaining results
                flushPendingResults();
                break;
              }
              
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');
              buffer = lines.pop() || '';

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6));
                
                if (data.type === 'start') {
                  console.log('🚀 Streaming validation started:', data);
                  setBatchResults(prev => ({
                    ...prev,
                    total: data.total || prev.total,
                    original_count: data.original_count || prev.original_count,
                    duplicates_removed: data.duplicates_removed || 0
                  }));
                } else if (data.type === 'result') {
                  // Add to pending batch instead of immediate update
                  if (data.result) {
                    pendingResults.push(data.result);
                  }

                  // Update progress immediately for responsiveness (separate from result batching)
                  const elapsed = (Date.now() - startTime) / 1000;
                  const current = data.progress.current;
                  const total = data.progress.total;
                  const speed = current / elapsed;
                  const remaining = total - current;
                  const eta = remaining / speed;

                  // Always update progress immediately - don't batch this
                  setProgress({
                    current,
                    total,
                    percentage: data.progress.percentage,
                    eta: Math.ceil(eta) || 0,
                    speed: speed.toFixed(1)
                  });

                  // Flush results more frequently for faster display
                  const now = Date.now();
                  if (pendingResults.length >= BATCH_SIZE || (now - lastUpdateTime) >= UPDATE_INTERVAL) {
                    flushPendingResults();
                    lastUpdateTime = now;
                  }

                  console.log(`✅ Real-time result ${current}/${total}:`, data.result.email, data.result.valid ? '✓' : '✗');
                } else if (data.type === 'complete') {
                  // Final flush
                  flushPendingResults();
                  
                  const processingTime = ((Date.now() - startTime) / 1000).toFixed(1);
                  
                  // Update API usage if provided
                  if (user && data.api_usage) {
                    const updatedUser = { ...user };
                    
                    if (data.api_usage.is_team_quota && user.teamInfo) {
                      // Update team quota
                      updatedUser.teamInfo = {
                        ...user.teamInfo,
                        quota_used: data.api_usage.calls_used
                      };
                      console.log(`🔄 Team quota updated from batch: ${data.api_usage.calls_used}/${data.api_usage.calls_limit} (${data.api_usage.team_name})`);
                    } else {
                      // Update individual quota
                      updatedUser.apiCallsCount = data.api_usage.calls_used;
                      console.log(`🔄 Individual API usage updated from batch: ${data.api_usage.calls_used}/${data.api_usage.calls_limit}`);
                    }
                    
                    setUser(updatedUser);
                    localStorage.setItem('user', JSON.stringify(updatedUser));
                  }
                  
                  // Final progress update - ensure completion is shown
                  setProgress({
                    current: data.total,
                    total: data.total,
                    percentage: 100,
                    eta: 0,
                    speed: (data.total / parseFloat(processingTime)).toFixed(1)
                  });

                  // Also update loading state to show completion
                  setLoading(false);
                  
                  setBatchResults(prev => ({
                    ...prev,
                    valid_count: data.valid_count,
                    invalid_count: data.invalid_count,
                    total: data.total,
                    original_count: data.original_count || prev.original_count,
                    duplicates_removed: data.duplicates_removed || prev.duplicates_removed,
                    domain_stats: data.domain_stats,
                    processing_time: processingTime
                  }));
                }
                  } catch (parseError) {
                    console.warn('Failed to parse streaming data:', line, parseError);
                    // Continue processing other lines
                  }
                }
              }
            }
          } catch (streamError) {
            console.error('Streaming error:', streamError);
            // Flush any pending results before throwing
            flushPendingResults();
            
            // If we have some results, don't fail completely
            if (pendingResults.length > 0 || (batchResults && batchResults.results.length > 0)) {
              console.log('⚠️ Streaming interrupted but partial results available');
              setError(`Network error after processing ${batchResults?.results?.length || 0} emails. Partial results shown.`);
            } else {
              throw new Error(`Network error during streaming: ${streamError.message}`);
            }
          }
        } else {
          // Handle regular JSON response for authenticated/admin users
          let data;
          try {
            data = await response.json();
            console.log('🎉 Batch validation completed:', data);
          } catch (e) {
            console.error('Failed to parse JSON response:', e);
            throw new Error('Invalid response format from server');
          }
          
          if (!data || !data.results) {
            throw new Error('Invalid response: missing results');
          }
          
          // Fast batch display for admin/authenticated users (no artificial delays)
          setBatchResults({
            results: [],
            valid_count: 0,
            invalid_count: 0,
            total: data.total,
            original_count: data.original_count,
            duplicates_removed: data.duplicates_removed,
            processing_time: data.processing_time,
            domain_stats: data.domain_stats,
            admin_validation: adminMode
          });

          // Ultra-fast display - show all results immediately for admin/authenticated users
          if (data.results.length <= 1000) {
            // For smaller batches, show all results immediately
            setBatchResults(prev => ({
              ...prev,
              results: data.results,
              valid_count: data.valid_count,
              invalid_count: data.invalid_count,
              processing_time: data.processing_time
            }));
            
            setProgress({
              current: data.total,
              total: data.total,
              percentage: 100,
              eta: 0,
              speed: data.processing_time > 0 ? (data.total / data.processing_time).toFixed(1) : '∞'
            });
            
            console.log(`✅ Instantly displayed all ${data.results.length} results`);
          } else {
            // For larger batches, use optimized chunking with minimal delays
            const CHUNK_SIZE = 200; // Larger chunks for faster display
            const chunks = [];
            for (let i = 0; i < data.results.length; i += CHUNK_SIZE) {
              chunks.push(data.results.slice(i, i + CHUNK_SIZE));
            }

            for (let chunkIndex = 0; chunkIndex < chunks.length; chunkIndex++) {
              const chunk = chunks[chunkIndex];
              const actualTotal = Math.min((chunkIndex + 1) * CHUNK_SIZE, data.results.length);
              const percentage = Math.round((actualTotal / data.total) * 100);
              
              // Update progress
              setProgress({
                current: actualTotal,
                total: data.total,
                percentage,
                eta: 0,
                speed: data.processing_time > 0 ? (data.total / data.processing_time).toFixed(1) : '∞'
              });

              // Add chunk efficiently using concat
              setBatchResults(prev => ({
                ...prev,
                results: prev.results.concat(chunk),
                valid_count: prev.valid_count + chunk.filter(r => r.valid).length,
                invalid_count: prev.invalid_count + chunk.filter(r => !r.valid).length
              }));

              console.log(`✅ Added chunk ${chunkIndex + 1}/${chunks.length}: ${chunk.length} results (${actualTotal}/${data.total} total)`);

              // Minimal delay only between chunks (5ms for ultra-fast display)
              if (chunkIndex < chunks.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 5));
              }
            }
          }

          // Final update
          setProgress({
            current: data.total,
            total: data.total,
            percentage: 100,
            eta: 0,
            speed: data.processing_time > 0 ? (data.total / data.processing_time).toFixed(1) : '∞'
          });

          setBatchResults(prev => ({
            ...prev,
            valid_count: data.valid_count,
            invalid_count: data.invalid_count,
            processing_time: data.processing_time
          }));
        }
        
        // Refresh history if on history tab
        if (historyMode) {
          loadHistory();
        }
    } catch (err) {
      console.error('❌ Batch validation error:', err);
      
      let errorMsg = 'Batch validation failed';
      
      if (err.name === 'AbortError') {
        errorMsg = 'Request timed out after 5 minutes. Please try with a smaller batch.';
      } else if (err.message.includes('fetch')) {
        errorMsg = `Connection failed: ${err.message}. Make sure the backend is running on port 5000.`;
      } else {
        errorMsg = err.message || 'Batch validation failed';
      }
      
      setError(errorMsg);
    } finally {
      if (timeoutId) clearTimeout(timeoutId); // Ensure timeout is cleared
      setLoading(false);
    }
  };

  // Memoized filtered history to prevent unnecessary re-renders
  const filteredHistory = useMemo(() => {
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

    // Date filter
    if (dateFilter !== 'all') {
      const now = new Date();
      const filterDate = new Date();
      
      switch (dateFilter) {
        case 'today':
          filterDate.setHours(0, 0, 0, 0);
          break;
        case 'week':
          filterDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          filterDate.setMonth(now.getMonth() - 1);
          break;
        case '3months':
          filterDate.setMonth(now.getMonth() - 3);
          break;
        default:
          filterDate.setFullYear(1970); // Show all
      }
      
      filtered = filtered.filter(item => {
        const itemDate = new Date(item.validated_at);
        return itemDate >= filterDate;
      });
    }

    // Sort by date (newest first)
    filtered.sort((a, b) => new Date(b.validated_at) - new Date(a.validated_at));
    
    return filtered;
  }, [history, searchTerm, statusFilter, dateFilter]);

  const deleteHistoryItem = async (id) => {
    // Custom confirmation dialog
    showConfirmModal(
      'Remove Record',
      'Remove this record from view?\n\nNote: This will only hide the record from this page. Your API usage count will not change.',
      () => {
        try {
          // Only remove from the current display, not from actual data
          const updatedHistory = history.filter(item => item.id !== id);
          
          setHistory(updatedHistory);
          
          // Show success message
          showSuccessModal('Success', 'Record removed from view');
          console.log('✅ Record removed from view (API usage unchanged)');
        } catch (err) {
          showErrorModal('Error', 'Failed to remove record from view');
        }
      },
      'Remove',
      'Cancel'
    );
  };

  const clearAllHistory = async () => {
    showConfirmModal(
      'Clear All History',
      'Clear ALL history? This cannot be undone!\n\nThis will permanently delete all your validation records.',
      async () => {
        try {
          if (user) {
            // Authenticated user - clear database
            await api.delete('/api/history');
            setHistory([]);
            showSuccessModal('Success', 'History cleared successfully');
          } else {
            // Anonymous user - clear localStorage
            if (clearLocalStorageHistory()) {
              setHistory([]);
              showSuccessModal('Success', 'History cleared successfully');
            } else {
              showErrorModal('Error', 'Failed to clear history');
            }
          }
        } catch (err) {
          showErrorModal('Error', 'Failed to clear history');
        }
      },
      'Clear All',
      'Cancel'
    );
  };

  const exportHistoryToCSV = () => {
    if (!filteredHistory || filteredHistory.length === 0) {
      showInfoModal('No Data', 'No history to export. Try adjusting your filters or validate some emails first.');
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



  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !batchMode && !historyMode) {
      validateEmail();
    }
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
              <div className={`api-usage-counter ${
                user.subscriptionTier === 'pro' ? 'pro-tier' : ''
              } ${(() => {
                // Use team quota if user is in a team, otherwise individual quota
                const isInTeam = user.teamId && user.teamInfo;
                const currentUsage = isInTeam ? (user.teamInfo.quota_used || 0) : (user.apiCallsCount || 0);
                const currentLimit = isInTeam ? (user.teamInfo.quota_limit || 10000000) : getCorrectApiLimit(user.subscriptionTier);
                
                return currentUsage >= currentLimit ? 'limit-reached' : 
                       currentUsage >= currentLimit * 0.8 ? 'limit-warning' : '';
              })()}`}>
                <FiActivity className="usage-icon" />
                <span className="usage-text">
                  {(() => {
                    // Display team quota if user is in a team
                    const isInTeam = user.teamId && user.teamInfo;
                    if (isInTeam) {
                      const teamUsage = user.teamInfo.quota_used || 0;
                      const teamLimit = user.teamInfo.quota_limit || 10000000;
                      return `${teamUsage.toLocaleString()}/${teamLimit.toLocaleString()} (Team)`;
                    } else {
                      return formatApiUsageWithPeriod(user.apiCallsCount || 0, user.apiCallsLimit, user.subscriptionTier);
                    }
                  })()}
                </span>
                <span className="usage-label">
                  {user.teamId && user.teamInfo ? 'Team Quota' : 
                   user.subscriptionTier === 'free' ? 'Free' : 
                   user.subscriptionTier === 'starter' ? 'Starter' : 
                   user.subscriptionTier === 'pro' ? 'Pro' : 'API Calls'}
                </span>
                {['free', 'starter'].includes(user.subscriptionTier) && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) && (
                  <div className="upgrade-hint">
                    <FiZap style={{marginRight: '4px'}} /> {user.subscriptionTier === 'free' ? 'Upgrade to Starter!' : 'Upgrade to Pro!'}
                  </div>
                )}
                {user.subscriptionTier === 'pro' && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) * 0.8 && (
                  <div className="usage-hint">
                    <FiActivity style={{marginRight: '4px'}} /> High usage!
                  </div>
                )}
                {user.subscriptionTier === 'pro' && !user.sendgridApiKey && (
                  <div className="setup-hint">
                    <FiMail style={{marginRight: '4px'}} /> Setup SendGrid!
                  </div>
                )}
                {user.subscriptionTier === 'pro' && (
                  <div className="pro-badge-hint">
                    💎 Pro Features Unlocked!
                  </div>
                )}
              </div>
            ) : (
              <div className={`anonymous-usage-counter ${anonValidationCount >= ANON_VALIDATION_LIMIT ? 'limit-reached' : anonValidationCount >= ANON_VALIDATION_LIMIT * 0.8 ? 'limit-warning' : ''}`} title="Sign up to save your validation history and get API access">
                <FiActivity className="usage-icon" />
                <span className="usage-text">{anonValidationCount}/{ANON_VALIDATION_LIMIT}</span>
                <span className="usage-label">Free</span>
                {anonValidationCount >= ANON_VALIDATION_LIMIT && (
                  <div className="upgrade-hint">
                    <FiZap style={{marginRight: '4px'}} /> Sign up for more!
                  </div>
                )}
                {anonValidationCount < ANON_VALIDATION_LIMIT && (
                  <div className="signup-hint">
                    <span>💾 Sign up!</span>
                  </div>
                )}
              </div>
            )}

            {/* Authentication Buttons */}
            {(() => {
              console.log('🔍 Auth state:', { 
                adminMode, 
                adminUser: !!adminUser, 
                user: !!user,
                adminToken: !!adminToken,
                localStorage_adminMode: localStorage.getItem('adminMode'),
                localStorage_adminToken: !!localStorage.getItem('adminToken'),
                localStorage_adminUser: !!localStorage.getItem('adminUser')
              });
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
                <button className="navbar-btn team-btn" onClick={() => navigate('/team')}>
                  <FiUsers /> Team
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

        {/* Debug Panel (development only) */}
        {process.env.NODE_ENV === 'development' && user && (
          <div style={{
            background: '#f8f9fa', 
            border: '1px solid #dee2e6', 
            borderRadius: '6px', 
            padding: '12px', 
            margin: '10px 0',
            fontSize: '12px',
            fontFamily: 'monospace'
          }}>
            <strong>🔍 Debug Info:</strong> Tier: {user.subscriptionTier} | Team: {user.teamId ? 'Yes' : 'No'} | Team ID: {user.teamId || 'None'}
          </div>
        )}

        {/* Main Card */}
        <div className="pro-main-card">
          {/* Tabs */}
          <div className="pro-tabs">
            <button
              className={`pro-tab ${!batchMode && !historyMode ? 'active' : ''}`}
              onClick={() => {
                setBatchMode(false);
                setHistoryMode(false);
                setResult(null);
                setBatchResults(null);
                setError(null);
              }}
            >
              <span className="pro-tab-icon"><FiInbox /></span>
              Single Email
            </button>
            <button
              className={`pro-tab ${batchMode ? 'active' : ''} ${!adminMode && (!user || (user && user.subscriptionTier === 'free')) ? 'disabled pro-feature' : ''}`}
              onClick={async () => {
                // Debug logging
                console.log('🔍 Batch validation clicked - User tier check:', {
                  user: user,
                  subscriptionTier: user?.subscriptionTier,
                  teamId: user?.teamId,
                  adminMode: adminMode
                });
                
                if (!adminMode && (!user || (user && user.subscriptionTier === 'free'))) {
                  // If user is in a team but still showing free tier, force refresh user data
                  if (user && user.teamId && user.subscriptionTier === 'free') {
                    console.log('🔄 User in team but showing free tier, force refreshing...');
                    try {
                      const response = await api.get('/api/auth/me');
                      if (response.status === 200) {
                        const updatedUser = response.data.user;
                        setUser(updatedUser);
                        localStorage.setItem('user', JSON.stringify(updatedUser));
                        console.log('✅ User data refreshed, new tier:', updatedUser.subscriptionTier);
                        
                        // If now pro tier, allow batch validation
                        if (updatedUser.subscriptionTier !== 'free') {
                          setBatchMode(true);
                          setHistoryMode(false);
                          setResult(null);
                          setBatchResults(null);
                          setError(null);
                          return;
                        }
                      }
                    } catch (error) {
                      console.error('Failed to refresh user data:', error);
                    }
                  }
                  
                  if (!user) {
                    setError('Batch validation requires an account. Sign up for free to get started!');
                  } else {
                    setError('Batch validation is available for Starter tier and above. Upgrade to validate multiple emails at once!');
                  }
                  return;
                }
                setBatchMode(true);
                setHistoryMode(false);
                setResult(null);
                setBatchResults(null);
                setError(null);
              }}
              disabled={!adminMode && (!user || (user && user.subscriptionTier === 'free'))}
              title={!adminMode && (!user || (user && user.subscriptionTier === 'free')) ? (!user ? 'Sign up to access batch validation' : 'Upgrade to Starter for batch validation') : 'Validate multiple emails at once'}
            >
              <div className="pro-tab-content">
                <span className="pro-tab-icon"><FiList /></span>
                <span className="pro-tab-text">
                  Batch Validation
                  {!adminMode && (!user || (user && user.subscriptionTier === 'free')) && (
                    <span className="pro-badge">STARTER+</span>
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



        {historyMode ? (
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
              <select
                className="history-filter"
                value={dateFilter}
                onChange={(e) => {
                  setDateFilter(e.target.value);
                  console.log('📅 Date filter changed to:', e.target.value);
                }}
              >
                <option value="today">Today</option>
                <option value="week">Last 7 Days</option>
                <option value="month">Last Month</option>
                <option value="3months">Last 3 Months</option>
                <option value="all">All Time</option>
              </select>
              <button className="refresh-btn" onClick={() => loadHistory(true)}>
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
                {user || adminMode ? (
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
              <HistoryPaginated
                results={filteredHistory}
                itemsPerPage={50}
                onDeleteItem={deleteHistoryItem}
              />
            )}
          </div>
        ) : !batchMode ? (
          <>
            {/* Single Email Input */}
            <div className="pro-input-section">
              {/* Free Tier Limit Warning (hidden for admin) */}
              {!adminMode && user && user.subscriptionTier === 'free' && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) && (
                <div className="limit-reached-banner">
                  <div className="limit-banner-content">
                    <div className="limit-banner-icon">🚫</div>
                    <div className="limit-banner-text">
                      <h3>Free Tier Limit Reached</h3>
                      <p>You've used all {formatApiLimit(user.subscriptionTier)} free validations. Upgrade to continue validating emails!</p>
                    </div>
                    <button className="upgrade-btn" onClick={() => navigate('/profile')}>
                      <FiZap style={{marginRight: '6px'}} /> Upgrade Now
                    </button>
                  </div>
                </div>
              )}
              
              {/* Approaching Limit Warning (hidden for admin) */}
              {!adminMode && user && user.subscriptionTier === 'free' && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) * 0.8 && user.apiCallsCount < getCorrectApiLimit(user.subscriptionTier) && (
                <div className="limit-warning-banner">
                  <div className="limit-banner-content">
                    <div className="limit-banner-icon">⚠️</div>
                    <div className="limit-banner-text">
                      <h3>Approaching Limit</h3>
                      <p>You have {getCorrectApiLimit(user.subscriptionTier) - user.apiCallsCount} validations remaining out of {formatApiLimit(user.subscriptionTier)}.</p>
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
                  className={`pro-email-input ${!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) ? 'disabled' : ''}`}
                  placeholder={(!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier)) || (!adminMode && !user && anonValidationCount >= ANON_VALIDATION_LIMIT) ? (!user ? 'Sign up to continue validating...' : 'Upgrade to continue validating...') : adminMode ? 'Admin: Unlimited validation access...' : 'Enter email address to validate...'}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={loading || (!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier))}
                />
                <button
                  className={`pro-validate-btn ${(!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier)) || (!adminMode && !user && anonValidationCount >= ANON_VALIDATION_LIMIT) ? 'disabled' : ''}`}
                  onClick={validateEmail}
                  disabled={loading || !email.trim() || (!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier)) || (!adminMode && !user && anonValidationCount >= ANON_VALIDATION_LIMIT)}
                >
                  {(!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier)) || (!adminMode && !user && anonValidationCount >= ANON_VALIDATION_LIMIT) ? 'Limit Reached' : loading ? 'Validating...' : adminMode ? 'Validate Email (Admin)' : 'Validate Email'}
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
            {/* Free Tier Batch Restriction (hidden for admin and starter+) */}
            {!adminMode && user && user.subscriptionTier === 'free' && !user.teamId && (
              <div className="feature-restriction-banner">
                <div className="restriction-banner-content">
                  <div className="restriction-banner-icon"><FiZap /></div>
                  <div className="restriction-banner-text">
                    <h3>Batch Validation - Starter Feature</h3>
                    <p>Batch validation is available for Starter tier and above. Upgrade to validate multiple emails at once, upload files, and access advanced batch analytics!</p>
                    <div className="feature-list">
                      <span>✅ Unlimited batch processing</span>
                      <span>✅ File upload support (CSV, Excel, PDF)</span>
                      <span>✅ Domain statistics & analytics</span>
                      <span>✅ Export results (CSV, JSON)</span>
                    </div>
                  </div>
                  <button className="upgrade-btn-large" onClick={() => navigate('/profile')}>
                    <FiZap style={{marginRight: '8px'}} /> Upgrade to Starter
                  </button>
                </div>
              </div>
            )}
            
            {/* Team Member with Stale Data - Force Refresh */}
            {!adminMode && user && user.subscriptionTier === 'free' && user.teamId && (
              <div className="feature-restriction-banner" style={{background: '#fff3cd', border: '1px solid #ffc107'}}>
                <div className="restriction-banner-content">
                  <div className="restriction-banner-icon">🔄</div>
                  <div className="restriction-banner-text">
                    <h3>Updating Your Access...</h3>
                    <p>You're a team member but your access is still updating. Click refresh to get your Pro access!</p>
                  </div>
                  <button 
                    className="upgrade-btn-large" 
                    style={{background: '#28a745'}}
                    onClick={async () => {
                      console.log('🔄 Manual refresh triggered by user...');
                      try {
                        const response = await api.get('/api/auth/me');
                        if (response.status === 200) {
                          const updatedUser = response.data.user;
                          setUser(updatedUser);
                          localStorage.setItem('user', JSON.stringify(updatedUser));
                          console.log('✅ User data refreshed manually, new tier:', updatedUser.subscriptionTier);
                          
                          if (updatedUser.subscriptionTier !== 'free') {
                            setError(null); // Clear any errors
                          }
                        }
                      } catch (error) {
                        console.error('Failed to refresh user data:', error);
                        setError('Failed to refresh user data. Please try again.');
                      }
                    }}
                  >
                    🔄 Refresh Access
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
                className={`upload-mode-btn ${uploadMode === 'text' ? 'active' : ''} ${!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) ? 'disabled' : ''}`}
                onClick={() => setUploadMode('text')}
                disabled={!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier)}
              >
                ✏️ Type Emails {adminMode && '(Admin)'}
              </button>
              <button
                className={`upload-mode-btn ${uploadMode === 'file' ? 'active' : ''} ${!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) ? 'disabled' : ''}`}
                onClick={() => setUploadMode('file')}
                disabled={!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier)}
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
                    {!adminMode && user && ['free', 'starter', 'pro'].includes(user.subscriptionTier) && (
                      <div className={`api-limit-check ${(() => {
                        const correctLimit = getCorrectApiLimit(user.subscriptionTier);
                        const remaining = correctLimit - user.apiCallsCount;
                        return finalCount > remaining ? 'exceeds-limit' : 
                               finalCount > remaining * 0.5 ? 'approaching-limit' : 'within-limit';
                      })()}`}>
                        {(() => {
                          const correctLimit = getCorrectApiLimit(user.subscriptionTier);
                          const remaining = correctLimit - user.apiCallsCount;
                          
                          if (finalCount > remaining) {
                            return (
                              <>
                                ❌ Batch size ({finalCount}) exceeds your remaining limit ({remaining.toLocaleString()})
                                <div className="limit-suggestion">
                                  Reduce batch size or <strong>{
                                    user.subscriptionTier === 'free' ? 'upgrade to starter/pro' : 
                                    user.subscriptionTier === 'starter' ? 'upgrade to pro (10M calls)' : 
                                    'contact support for more capacity'
                                  }</strong>
                                </div>
                              </>
                            );
                          } else if (finalCount > remaining * 0.5) {
                            return (
                              <>
                                ⚠️ This will use {finalCount} of your {remaining.toLocaleString()} remaining validations
                              </>
                            );
                          } else {
                            return (
                              <>
                                ✅ Within your limit ({remaining.toLocaleString()} remaining)
                              </>
                            );
                          }
                        })()}
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
                  {!adminMode && user && ['free', 'starter'].includes(user.subscriptionTier) && (
                    <div className="batch-limit-info">
                      ⚠️ {user.subscriptionTier === 'free' ? 'Free' : 'Starter'} tier: {getCorrectApiLimit(user.subscriptionTier) - user.apiCallsCount} validations remaining
                    </div>
                  )}
                  {adminMode && (
                    <div className="admin-batch-info">
                      🛡️ Admin Mode: Unlimited batch validation access
                    </div>
                  )}
                </div>
                <textarea
                  className={`batch-input ${!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) ? 'disabled' : ''}`}
                  placeholder={!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) ? 'Upgrade to continue batch validation...' : adminMode ? 'Admin: Enter unlimited emails for batch validation...' : 'Enter email addresses (one per line, comma-separated, or any format)...'}
                  value={batchEmails}
                  onChange={(e) => setBatchEmails(e.target.value)}
                  disabled={loading || (!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier))}
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
              className={`validate-btn ${!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) ? 'disabled' : ''}`}
              onClick={validateBatch}
              disabled={loading || (!batchEmails.trim()) || (!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier))}
            >
              {!adminMode && user && user.apiCallsCount >= getCorrectApiLimit(user.subscriptionTier) ? 'Limit Reached - Upgrade Required' : loading ? 'Validating...' : adminMode ? 'Validate Batch (Admin - Unlimited)' : 'Validate Batch'}
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
            {!user && !adminMode && (
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
                
                {/* Shared Results Banner */}
                {batchResults.shared && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    marginBottom: '16px',
                    padding: '12px 16px',
                    background: 'linear-gradient(135deg, #10b981, #059669)',
                    borderRadius: '12px',
                    color: 'white',
                    fontSize: '0.9rem',
                    fontWeight: '500'
                  }}>
                    <span style={{fontSize: '1.2rem'}}>🔗</span>
                    <div style={{flex: 1}}>
                      <div style={{fontWeight: '600'}}>Shared Batch Results</div>
                      <div style={{fontSize: '0.8rem', opacity: '0.9'}}>
                        {batchResults.sharedBy && `Shared by: ${batchResults.sharedBy} • `}
                        Generated: {batchResults.generatedAt ? new Date(batchResults.generatedAt).toLocaleDateString() : 'Unknown'}
                      </div>
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      opacity: '0.8',
                      textAlign: 'right'
                    }}>
                      <div>📊 {batchResults.total} emails</div>
                      <div>✅ {batchResults.valid_count} valid</div>
                    </div>
                  </div>
                )}
                
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
              <BatchResultsPaginated
                results={batchResults.results}
                mode={mode}
                itemsPerPage={30}
                getConfidenceColor={getConfidenceColor}
                getConfidenceTextColor={getConfidenceTextColor}
                getConfidenceLabel={getConfidenceLabel}
                isStreaming={loading}
              />
            )}
          </div>
        )}

        {showShareModal && (
          <div className="modal-overlay" onClick={() => setShowShareModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3><FiLink style={{marginRight: '8px'}} /> Share Results</h3>
                <button className="modal-close" onClick={() => setShowShareModal(false)}>
                  <FiX />
                </button>
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
                  <FiInfo style={{marginRight: '6px'}} /> Tip: Share this link via email, Slack, or any messaging app
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Custom Modal */}
        {showModal && (
          <div className="custom-modal-overlay" onClick={() => setShowModal(false)}>
            <div className="custom-modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="custom-modal-header">
                <h3 className={`custom-modal-title ${modalConfig.type}`}>
                  {modalConfig.type === 'success' && <FiCheckCircle style={{marginRight: '8px'}} />}
                  {modalConfig.type === 'error' && <FiXCircle style={{marginRight: '8px'}} />}
                  {modalConfig.type === 'warning' && <FiAlertTriangle style={{marginRight: '8px'}} />}
                  {modalConfig.type === 'confirm' && <FiHelpCircle style={{marginRight: '8px'}} />}
                  {modalConfig.type === 'info' && <FiInfo style={{marginRight: '8px'}} />}
                  {modalConfig.title}
                </h3>
                <button className="custom-modal-close" onClick={() => setShowModal(false)}>
                  <FiX />
                </button>
              </div>
              <div className="custom-modal-body">
                <p className="custom-modal-message">
                  {modalConfig.message.split('\n').map((line, index) => (
                    <span key={index}>
                      {line}
                      {index < modalConfig.message.split('\n').length - 1 && <br />}
                    </span>
                  ))}
                </p>
              </div>
              <div className="custom-modal-footer">
                {modalConfig.type === 'confirm' ? (
                  <>
                    <button 
                      className="custom-modal-btn cancel" 
                      onClick={modalConfig.onCancel}
                    >
                      {modalConfig.cancelText}
                    </button>
                    <button 
                      className="custom-modal-btn confirm" 
                      onClick={modalConfig.onConfirm}
                    >
                      {modalConfig.confirmText}
                    </button>
                  </>
                ) : (
                  <button 
                    className="custom-modal-btn primary" 
                    onClick={modalConfig.onConfirm}
                  >
                    {modalConfig.confirmText}
                  </button>
                )}
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

import React, { useState, useMemo, useCallback } from 'react';
import { 
  FiChevronLeft, FiChevronRight, FiChevronsLeft, FiChevronsRight,
  FiCheck, FiX, FiAlertTriangle, FiInfo, FiMail, FiShield, FiTrash2
} from 'react-icons/fi';
import './BatchResultsPaginated.css';

// Memoized individual card component for better performance
const ResultCard = React.memo(({ 
  item, 
  originalIndex, 
  isNewlyAdded, 
  mode, 
  getConfidenceColor, 
  getConfidenceTextColor, 
  getConfidenceLabel,
  isHistory = false,
  onDeleteItem = null
}) => (
  <div className={`batch-result-card ${item.valid ? 'valid' : 'invalid'} ${isNewlyAdded ? 'streaming-new' : ''}`}>
    {/* Card Header */}
    <div className="card-header">
      <div className="card-number">#{originalIndex}</div>
      <div className="card-header-right">
        {isHistory && (
          <div className="history-date">
            {new Date(item.validated_at).toLocaleDateString()}
          </div>
        )}
        <div className={`status-indicator ${item.valid ? 'valid' : 'invalid'}`}>
          {item.valid ? <FiCheck /> : <FiX />}
        </div>
        {isHistory && onDeleteItem && (
          <button
            className="delete-btn"
            onClick={() => onDeleteItem(item.id)}
            title="Delete from history"
          >
            <FiX />
          </button>
        )}
      </div>
    </div>

    {/* Email */}
    <div className="card-email">
      <FiMail className="email-icon" />
      <span className="email-text" title={item.email}>{item.email}</span>
    </div>

    {/* Status Badge */}
    {item.status && (
      <div className={`status-badge status-${item.status.color}`}>
        {item.status.status.toUpperCase()}
      </div>
    )}

    {/* Advanced Mode Details */}
    {mode === 'advanced' && (
      <div className="card-details">
        {/* Confidence Score */}
        {item.confidence_score !== undefined && (
          <div className="confidence-section">
            <div className="confidence-header">
              <span className="confidence-label">Confidence</span>
              <span 
                className="confidence-value"
                style={{ color: getConfidenceTextColor(item.confidence_score) }}
              >
                {item.confidence_score}/100
              </span>
            </div>
            <div className="confidence-bar-container">
              <div
                className="confidence-bar"
                style={{
                  width: `${item.confidence_score}%`,
                  backgroundColor: getConfidenceColor(item.confidence_score)
                }}
              />
            </div>
            <div className="confidence-grade">
              {getConfidenceLabel(item.confidence_score)}
            </div>
          </div>
        )}

        {/* Deliverability */}
        {item.deliverability && (
          <div className="deliverability-section">
            <div className="deliverability-header">
              <span>Deliverability</span>
              <span 
                className="deliverability-grade"
                style={{ 
                  backgroundColor: item.deliverability.deliverability_score >= 80 ? '#10b981' : 
                                 item.deliverability.deliverability_score >= 60 ? '#f59e0b' : '#ef4444'
                }}
              >
                {item.deliverability.deliverability_grade}
              </span>
            </div>
            <div className="deliverability-score">
              {item.deliverability.deliverability_score}/100
            </div>
          </div>
        )}

        {/* Risk Warning */}
        {item.risk_check && item.risk_check.overall_risk !== 'low' && (
          <div className={`risk-warning ${item.risk_check.overall_risk}`}>
            <FiAlertTriangle />
            <span>Risk: {item.risk_check.overall_risk.toUpperCase()}</span>
          </div>
        )}

        {/* Bounce Warning */}
        {item.bounce_check?.bounce_history?.has_bounced && (
          <div className="bounce-warning">
            <FiShield />
            <span>{item.bounce_check.bounce_history.total_bounces} bounces</span>
          </div>
        )}

        {/* Quick Checks */}
        <div className="quick-checks">
          <div className={`quick-check ${item.checks?.syntax ? 'pass' : 'fail'}`}>
            {item.checks?.syntax ? <FiCheck /> : <FiX />}
            <span>Syntax</span>
          </div>
          <div className={`quick-check ${item.checks?.dns_valid ? 'pass' : 'fail'}`}>
            {item.checks?.dns_valid ? <FiCheck /> : <FiX />}
            <span>DNS</span>
          </div>
          <div className={`quick-check ${item.checks?.mx_records ? 'pass' : 'fail'}`}>
            {item.checks?.mx_records ? <FiCheck /> : <FiX />}
            <span>MX</span>
          </div>
        </div>

        {/* Warnings */}
        <div className="warnings">
          {item.checks?.is_disposable && (
            <div className="warning-item disposable">
              <FiAlertTriangle />
              <span>Disposable</span>
            </div>
          )}
          {item.checks?.is_role_based && (
            <div className="warning-item role-based">
              <FiInfo />
              <span>Role-based</span>
            </div>
          )}
        </div>
      </div>
    )}

    {/* Suggestion */}
    {item.suggestion && (
      <div className="suggestion">
        <span className="suggestion-label">💡 Did you mean:</span>
        <span className="suggestion-text">{item.suggestion}</span>
      </div>
    )}

    {/* Reason (for invalid emails) */}
    {!item.valid && item.reason && (
      <div className="reason">
        <span className="reason-text">{item.reason}</span>
      </div>
    )}
  </div>
));

const BatchResultsPaginated = React.memo(({ 
  results, 
  mode, 
  itemsPerPage = 30,
  getConfidenceColor,
  getConfidenceTextColor,
  getConfidenceLabel,
  isStreaming = false,
  isHistory = false,
  onDeleteItem = null
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [filterStatus, setFilterStatus] = useState('all'); // all, valid, invalid
  const [sortBy, setSortBy] = useState('index'); // index, confidence, email
  const [followLatest, setFollowLatest] = useState(true); // Auto-follow latest results during streaming
  const [newlyAdded, setNewlyAdded] = useState(new Set()); // Track newly added items for animation

  // Filter and sort results
  const filteredAndSortedResults = useMemo(() => {
    let filtered = results;

    // Apply status filter
    if (filterStatus === 'valid') {
      filtered = results.filter(item => item.valid);
    } else if (filterStatus === 'invalid') {
      filtered = results.filter(item => !item.valid);
    }

    // Apply sorting
    const sorted = [...filtered];
    switch (sortBy) {
      case 'confidence':
        sorted.sort((a, b) => (b.confidence_score || 0) - (a.confidence_score || 0));
        break;
      case 'email':
        sorted.sort((a, b) => a.email.localeCompare(b.email));
        break;
      case 'index':
      default:
        // Keep original order (already sorted by index)
        break;
    }

    return sorted;
  }, [results, filterStatus, sortBy]);

  // Calculate pagination
  const totalItems = filteredAndSortedResults.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const currentItems = filteredAndSortedResults.slice(startIndex, endIndex);

  // Reset to page 1 when filters change
  React.useEffect(() => {
    setCurrentPage(1);
  }, [filterStatus, sortBy]);

  // Auto-follow latest results during streaming
  React.useEffect(() => {
    if (isStreaming && followLatest && results.length > 0) {
      const lastPage = Math.ceil(filteredAndSortedResults.length / itemsPerPage);
      if (lastPage > 0 && currentPage !== lastPage) {
        setCurrentPage(lastPage);
      }
    }
  }, [results.length, isStreaming, followLatest, filteredAndSortedResults.length, itemsPerPage, currentPage]);

  // Track newly added items for animation (optimized)
  const prevResultsLength = React.useRef(0);
  const animationTimeoutRef = React.useRef(null);
  
  React.useEffect(() => {
    if (isStreaming && results.length > prevResultsLength.current) {
      // Only highlight if we're adding a reasonable number of new items
      const newItemsCount = results.length - prevResultsLength.current;
      
      if (newItemsCount <= 50) { // Only animate if adding 50 or fewer items
        const newItems = new Set();
        for (let i = prevResultsLength.current; i < results.length; i++) {
          newItems.add(results[i].email);
        }
        setNewlyAdded(newItems);
        
        // Clear previous timeout
        if (animationTimeoutRef.current) {
          clearTimeout(animationTimeoutRef.current);
        }
        
        // Remove the highlight after 2 seconds (reduced from 3)
        animationTimeoutRef.current = setTimeout(() => {
          setNewlyAdded(new Set());
        }, 2000);
      }
    }
    prevResultsLength.current = results.length;
  }, [results, isStreaming]);

  // Cleanup timeout on unmount
  React.useEffect(() => {
    return () => {
      if (animationTimeoutRef.current) {
        clearTimeout(animationTimeoutRef.current);
      }
    };
  }, []);

  // Optimize index lookup with memoization
  const emailToIndexMap = React.useMemo(() => {
    const map = new Map();
    results.forEach((result, index) => {
      map.set(result.email, index + 1);
    });
    return map;
  }, [results]);

  const getOriginalIndex = (item) => {
    return emailToIndexMap.get(item.email) || 1;
  };

  const goToPage = useCallback((page) => {
    const newPage = Math.max(1, Math.min(page, totalPages));
    setCurrentPage(newPage);
    
    // If user manually navigates during streaming, disable auto-follow
    if (isStreaming && followLatest) {
      setFollowLatest(false);
    }
  }, [totalPages, isStreaming, followLatest]);

  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 7;
    
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 4) {
        for (let i = 1; i <= 5; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 3) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      }
    }
    
    return pages;
  };

  // Pagination Component (reusable for top and bottom)
  const PaginationControls = () => (
    <div className="pagination">
      <button 
        className="pagination-btn"
        onClick={() => goToPage(1)}
        disabled={currentPage === 1}
        title="First page"
      >
        <FiChevronsLeft />
      </button>
      
      <button 
        className="pagination-btn"
        onClick={() => goToPage(currentPage - 1)}
        disabled={currentPage === 1}
        title="Previous page"
      >
        <FiChevronLeft />
      </button>

      <div className="pagination-numbers">
        {getPageNumbers().map((page, index) => (
          page === '...' ? (
            <span key={`ellipsis-${index}`} className="pagination-ellipsis">...</span>
          ) : (
            <button
              key={page}
              className={`pagination-number ${currentPage === page ? 'active' : ''}`}
              onClick={() => goToPage(page)}
            >
              {page}
            </button>
          )
        ))}
      </div>

      <button 
        className="pagination-btn"
        onClick={() => goToPage(currentPage + 1)}
        disabled={currentPage === totalPages}
        title="Next page"
      >
        <FiChevronRight />
      </button>
      
      <button 
        className="pagination-btn"
        onClick={() => goToPage(totalPages)}
        disabled={currentPage === totalPages}
        title="Last page"
      >
        <FiChevronsRight />
      </button>
    </div>
  );

  return (
    <div className="batch-results-paginated">
      {/* Streaming Indicator */}
      {isStreaming && (
        <div className="streaming-indicator">
          <div className="pulse-dot"></div>
          <span>🚀 Real-time validation in progress - Results appear as they're validated!</span>
          {results.length > 0 && (
            <span style={{ marginLeft: '12px', opacity: 0.9 }}>
              📊 {results.length} processed so far
            </span>
          )}
        </div>
      )}

      {/* Controls */}
      <div className="batch-controls">
        <div className="batch-filters">
          <select 
            value={filterStatus} 
            onChange={(e) => setFilterStatus(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Results ({results.length})</option>
            <option value="valid">Valid Only ({results.filter(r => r.valid).length})</option>
            <option value="invalid">Invalid Only ({results.filter(r => !r.valid).length})</option>
          </select>
          
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="sort-select"
          >
            <option value="index">Sort by Order</option>
            <option value="confidence">Sort by Confidence</option>
            <option value="email">Sort by Email</option>
          </select>

          {isStreaming && (
            <button
              className={`follow-latest-btn ${followLatest ? 'active' : ''}`}
              onClick={() => setFollowLatest(!followLatest)}
              title={followLatest ? 'Stop following latest results' : 'Follow latest results'}
            >
              {followLatest ? '📍 Following' : '📍 Follow Latest'}
            </button>
          )}
        </div>

        <div className="batch-info">
          <span>Showing {startIndex + 1}-{endIndex} of {totalItems} results</span>
          {totalPages > 5 && (
            <div className="quick-jump">
              <span>Go to page:</span>
              <input
                type="number"
                min="1"
                max={totalPages}
                value={currentPage}
                onChange={(e) => {
                  const page = parseInt(e.target.value);
                  if (page >= 1 && page <= totalPages) {
                    goToPage(page);
                  }
                }}
                className="page-jump-input"
              />
              <span>of {totalPages}</span>
            </div>
          )}
        </div>
      </div>

      {/* Pagination - TOP */}
      {totalPages > 1 && <PaginationControls />}

      {/* Page Info - TOP */}
      {totalPages > 1 && (
        <div className="page-info page-info-top">
          Page {currentPage} of {totalPages} • {totalItems} total results
        </div>
      )}

      {/* Results Grid */}
      <div className="batch-results-grid">
        {currentItems.map((item, index) => {
          const originalIndex = getOriginalIndex(item);
          const isNewlyAdded = newlyAdded.has(item.email);
          
          return (
            <ResultCard 
              key={`${item.email}-${originalIndex}`}
              item={item}
              originalIndex={originalIndex}
              isNewlyAdded={isNewlyAdded}
              mode={mode}
              getConfidenceColor={getConfidenceColor}
              getConfidenceTextColor={getConfidenceTextColor}
              getConfidenceLabel={getConfidenceLabel}
              isHistory={isHistory}
              onDeleteItem={onDeleteItem}
            />
          );
        })}
      </div>

      {/* Pagination - BOTTOM */}
      {totalPages > 1 && <PaginationControls />}

      {/* Page Info - BOTTOM */}
      {totalPages > 1 && (
        <div className="page-info">
          Page {currentPage} of {totalPages} • {totalItems} total results
        </div>
      )}
    </div>
  );
});

export default BatchResultsPaginated;
import React, { useState, useMemo, useCallback } from 'react';
import { 
  FiChevronLeft, FiChevronRight, FiChevronsLeft, FiChevronsRight,
  FiCheck, FiX, FiTrash2
} from 'react-icons/fi';
import './HistoryPaginated.css';

// Lightweight history row component
const HistoryRow = React.memo(({ item, index, onDeleteItem }) => (
  <div className="history-row">
    <div className="history-index">#{index}</div>
    <div className="history-email">{item.email}</div>
    <div className={`history-status ${item.valid ? 'valid' : 'invalid'}`}>
      {item.valid ? <FiCheck /> : <FiX />}
      <span>{item.valid ? 'Valid' : 'Invalid'}</span>
    </div>
    <div className="history-score">{item.confidence_score || 0}/100</div>
    <div className="history-date">{new Date(item.validated_at).toLocaleDateString()}</div>
    <div className="history-actions">
      <button
        className="history-delete-btn"
        onClick={() => onDeleteItem(item.id)}
        title="Delete"
      >
        <FiTrash2 />
      </button>
    </div>
  </div>
));

const HistoryPaginated = React.memo(({ 
  results, 
  itemsPerPage = 50,
  onDeleteItem = null
}) => {
  const [currentPage, setCurrentPage] = useState(1);

  // Reset to page 1 when results change significantly
  const resultsLength = results.length;
  React.useEffect(() => {
    setCurrentPage(1);
  }, [resultsLength]);

  // Memoized pagination calculations
  const paginationData = useMemo(() => {
    const totalItems = results.length;
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
    const currentItems = results.slice(startIndex, endIndex);
    
    return {
      totalItems,
      totalPages,
      startIndex,
      endIndex,
      currentItems
    };
  }, [results, currentPage, itemsPerPage]);

  const { totalItems, totalPages, startIndex, endIndex, currentItems } = paginationData;

  const goToPage = useCallback((page) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  }, [totalPages]);

  const pageNumbers = useMemo(() => {
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
  }, [currentPage, totalPages]);

  // Memoized Pagination Component
  const PaginationControls = React.memo(() => (
    <div className="history-pagination">
      <button 
        className="history-pagination-btn"
        onClick={() => goToPage(1)}
        disabled={currentPage === 1}
        title="First page"
      >
        <FiChevronsLeft />
      </button>
      
      <button 
        className="history-pagination-btn"
        onClick={() => goToPage(currentPage - 1)}
        disabled={currentPage === 1}
        title="Previous page"
      >
        <FiChevronLeft />
      </button>

      <div className="history-pagination-numbers">
        {pageNumbers.map((page, index) => (
          page === '...' ? (
            <span key={`ellipsis-${index}`} className="history-pagination-ellipsis">...</span>
          ) : (
            <button
              key={page}
              className={`history-pagination-number ${currentPage === page ? 'active' : ''}`}
              onClick={() => goToPage(page)}
            >
              {page}
            </button>
          )
        ))}
      </div>

      <button 
        className="history-pagination-btn"
        onClick={() => goToPage(currentPage + 1)}
        disabled={currentPage === totalPages}
        title="Next page"
      >
        <FiChevronRight />
      </button>
      
      <button 
        className="history-pagination-btn"
        onClick={() => goToPage(totalPages)}
        disabled={currentPage === totalPages}
        title="Last page"
      >
        <FiChevronsRight />
      </button>
    </div>
  ));

  return (
    <div className="history-paginated">
      {/* Info */}
      <div className="history-info">
        <span>Showing {startIndex + 1}-{endIndex} of {totalItems} records</span>
        {totalPages > 5 && (
          <div className="history-quick-jump">
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
              className="history-page-jump-input"
            />
            <span>of {totalPages}</span>
          </div>
        )}
      </div>

      {/* Pagination - TOP */}
      {totalPages > 1 && <PaginationControls />}

      {/* Header */}
      <div className="history-header-row">
        <div className="history-header-index">#</div>
        <div className="history-header-email">Email</div>
        <div className="history-header-status">Status</div>
        <div className="history-header-score">Score</div>
        <div className="history-header-date">Date</div>
        <div className="history-header-actions">Actions</div>
      </div>

      {/* Results */}
      <div className="history-results">
        {currentItems.map((item, index) => (
          <HistoryRow
            key={`${item.email}-${item.id}`}
            item={item}
            index={startIndex + index + 1}
            onDeleteItem={onDeleteItem}
          />
        ))}
      </div>

      {/* Pagination - BOTTOM */}
      {totalPages > 1 && <PaginationControls />}

      {/* Page Info - BOTTOM */}
      {totalPages > 1 && (
        <div className="history-page-info">
          Page {currentPage} of {totalPages} • {totalItems} total records
        </div>
      )}
    </div>
  );
});

export default HistoryPaginated;
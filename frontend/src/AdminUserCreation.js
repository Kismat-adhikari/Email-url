import React, { useState } from 'react';
import { FiUser, FiMail, FiLock, FiUsers, FiX, FiCheck, FiAlertCircle } from 'react-icons/fi';
import './AdminDashboard.css';

const AdminUserCreation = ({ isOpen, onClose, onUserCreated }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    firstName: '',
    lastName: '',
    subscriptionTier: 'free'
  });
  
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState(null);

  const tierOptions = [
    { 
      value: 'free', 
      label: 'Free Tier', 
      description: '10 API calls, basic validation only',
      features: ['10 email validations', 'Basic validation', 'No batch processing']
    },
    { 
      value: 'starter', 
      label: 'Starter Tier', 
      description: '10,000 API calls, batch validation enabled',
      features: ['10,000 email validations', 'Advanced validation', 'Batch processing', 'No email sending']
    },
    { 
      value: 'pro', 
      label: 'Pro Tier', 
      description: '10 million API calls, all features unlocked',
      features: ['10,000,000 email validations', 'Advanced validation', 'Batch processing', 'Email sending with SendGrid']
    }
  ];

  const validateForm = () => {
    const newErrors = {};

    // Email validation
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters long';
    }

    // Name validation
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    }

    // Tier validation
    if (!formData.subscriptionTier) {
      newErrors.subscriptionTier = 'Subscription tier is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setErrors({});
    setSuccess(null);

    try {
      const token = localStorage.getItem('adminToken');
      const response = await fetch('/admin/users/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess({
          message: 'User account created successfully!',
          user: data.user
        });
        
        // Reset form
        setFormData({
          email: '',
          password: '',
          firstName: '',
          lastName: '',
          subscriptionTier: 'free'
        });

        // Notify parent component
        if (onUserCreated) {
          onUserCreated(data.user);
        }

        // Auto-close after 2 seconds
        setTimeout(() => {
          onClose();
          setSuccess(null);
        }, 2000);

      } else {
        setErrors({
          submit: data.message || 'Failed to create user account'
        });
      }
    } catch (error) {
      console.error('User creation error:', error);
      setErrors({
        submit: 'Network error. Please check your connection and try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setFormData({
        email: '',
        password: '',
        firstName: '',
        lastName: '',
        subscriptionTier: 'free'
      });
      setErrors({});
      setSuccess(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  const selectedTier = tierOptions.find(tier => tier.value === formData.subscriptionTier);

  return (
    <div className="admin-modal-overlay">
      <div className="admin-modal admin-user-creation-modal">
        {/* Header */}
        <div className="admin-modal-header">
          <h3>
            <FiUsers style={{ marginRight: '8px' }} />
            Create New User Account
          </h3>
          <button 
            className="admin-modal-close"
            onClick={handleClose}
            disabled={loading}
          >
            <FiX />
          </button>
        </div>

        {/* Body */}
        <div className="admin-modal-body">
          {success ? (
            <div className="admin-success-message">
              <div className="admin-success-icon">
                <FiCheck />
              </div>
              <div className="admin-success-content">
                <h4>Account Created Successfully!</h4>
                <p>User <strong>{success.user.email}</strong> has been created with <strong>{success.user.subscription_tier}</strong> tier.</p>
                <div className="admin-success-details">
                  <span>API Limit: {success.user.api_calls_limit} validations</span>
                  <span>Status: Active</span>
                </div>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="admin-user-creation-form">
              {/* Error Message */}
              {errors.submit && (
                <div className="admin-error-message">
                  <FiAlertCircle />
                  <span>{errors.submit}</span>
                </div>
              )}

              {/* Email Field */}
              <div className="admin-form-group">
                <label htmlFor="email">
                  <FiMail style={{ marginRight: '6px' }} />
                  Email Address *
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="user@example.com"
                  className={errors.email ? 'error' : ''}
                  disabled={loading}
                />
                {errors.email && <span className="admin-field-error">{errors.email}</span>}
              </div>

              {/* Password Field */}
              <div className="admin-form-group">
                <label htmlFor="password">
                  <FiLock style={{ marginRight: '6px' }} />
                  Password *
                </label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="Minimum 8 characters"
                  className={errors.password ? 'error' : ''}
                  disabled={loading}
                />
                {errors.password && <span className="admin-field-error">{errors.password}</span>}
              </div>

              {/* Name Fields */}
              <div className="admin-form-row">
                <div className="admin-form-group">
                  <label htmlFor="firstName">
                    <FiUser style={{ marginRight: '6px' }} />
                    First Name *
                  </label>
                  <input
                    type="text"
                    id="firstName"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleInputChange}
                    placeholder="John"
                    className={errors.firstName ? 'error' : ''}
                    disabled={loading}
                  />
                  {errors.firstName && <span className="admin-field-error">{errors.firstName}</span>}
                </div>

                <div className="admin-form-group">
                  <label htmlFor="lastName">Last Name *</label>
                  <input
                    type="text"
                    id="lastName"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleInputChange}
                    placeholder="Doe"
                    className={errors.lastName ? 'error' : ''}
                    disabled={loading}
                  />
                  {errors.lastName && <span className="admin-field-error">{errors.lastName}</span>}
                </div>
              </div>

              {/* Subscription Tier */}
              <div className="admin-form-group">
                <label htmlFor="subscriptionTier">
                  <FiUsers style={{ marginRight: '6px' }} />
                  Subscription Tier *
                </label>
                <select
                  id="subscriptionTier"
                  name="subscriptionTier"
                  value={formData.subscriptionTier}
                  onChange={handleInputChange}
                  className={errors.subscriptionTier ? 'error' : ''}
                  disabled={loading}
                >
                  {tierOptions.map(tier => (
                    <option key={tier.value} value={tier.value}>
                      {tier.label} - {tier.description}
                    </option>
                  ))}
                </select>
                {errors.subscriptionTier && <span className="admin-field-error">{errors.subscriptionTier}</span>}
              </div>

              {/* Tier Features Preview */}
              {selectedTier && (
                <div className="admin-tier-preview">
                  <h4>{selectedTier.label} Features:</h4>
                  <ul>
                    {selectedTier.features.map((feature, index) => (
                      <li key={index}>
                        <FiCheck style={{ color: '#10b981', marginRight: '6px' }} />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </form>
          )}
        </div>

        {/* Footer */}
        {!success && (
          <div className="admin-modal-footer">
            <button 
              type="button"
              className="admin-btn-secondary"
              onClick={handleClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button 
              type="submit"
              className="admin-btn-primary"
              onClick={handleSubmit}
              disabled={loading || !formData.email || !formData.password || !formData.firstName || !formData.lastName}
            >
              {loading ? (
                <>
                  <div className="admin-spinner-small"></div>
                  Creating Account...
                </>
              ) : (
                <>
                  <FiCheck style={{ marginRight: '6px' }} />
                  Create Account
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminUserCreation;
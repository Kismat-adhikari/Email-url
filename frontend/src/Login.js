import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, ArrowLeft, Shield, Zap } from 'lucide-react';

function Login() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Store JWT token in localStorage
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Check if there's a pending invitation to accept
        const returnUrl = localStorage.getItem('returnUrl');
        if (returnUrl && returnUrl.includes('/invite/')) {
          // Extract invitation token from URL
          const inviteToken = returnUrl.split('/invite/')[1];
          
          // Automatically accept the invitation
          try {
            const inviteResponse = await fetch(`/api/team/invite/${inviteToken}/accept`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${data.token}`,
                'Content-Type': 'application/json'
              }
            });
            
            if (inviteResponse.ok) {
              // Clear the return URL
              localStorage.removeItem('returnUrl');
              // Redirect to team page with success message
              window.location.href = '/team?joined=success';
            } else {
              // If invitation acceptance fails, still redirect but show the invitation page
              window.location.href = returnUrl;
            }
          } catch (inviteErr) {
            console.error('Failed to accept invitation:', inviteErr);
            // Fallback to invitation page
            window.location.href = returnUrl;
          }
        } else {
          // Normal login flow - redirect to main app
          window.location.href = '/';
        }
      } else {
        // Handle suspension error specially
        if (response.status === 403 && data.error === 'Account suspended') {
          const suspendedDate = data.suspended_at ? new Date(data.suspended_at).toLocaleDateString() : 'Unknown date';
          setError(
            `🚫 Account Suspended\n\nYour account was suspended on ${suspendedDate}.\nReason: ${data.suspension_reason}\n\nPlease create a new account if you wish to continue using our service.`
          );
        } else {
          setError(data.message || 'Login failed. Please try again.');
        }
      }
      
    } catch (err) {
      console.error('Login error:', err);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Background Pattern */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `
          radial-gradient(circle at 25% 25%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
          radial-gradient(circle at 75% 75%, rgba(255, 255, 255, 0.1) 0%, transparent 50%)
        `,
        pointerEvents: 'none'
      }} />

      {/* Login Card */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '24px',
        padding: '48px',
        width: '100%',
        maxWidth: '440px',
        boxShadow: '0 25px 50px rgba(0, 0, 0, 0.15)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        position: 'relative',
        zIndex: 1
      }}>
        {/* Back Button */}
        <button
          onClick={() => window.location.href = '/testing'}
          style={{
            position: 'absolute',
            top: '24px',
            left: '24px',
            background: 'transparent',
            border: 'none',
            color: '#64748b',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.9rem',
            fontWeight: '500',
            transition: 'color 0.2s'
          }}
          onMouseOver={(e) => e.target.style.color = '#3b82f6'}
          onMouseOut={(e) => e.target.style.color = '#64748b'}
        >
          <ArrowLeft style={{ width: '18px', height: '18px' }} />
          Back
        </button>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '40px', marginTop: '20px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            marginBottom: '16px'
          }}>
            <Mail style={{ width: '32px', height: '32px', color: '#3b82f6' }} />
            <span style={{
              fontSize: '1.5rem',
              fontWeight: '700',
              color: '#1e293b'
            }}>
              EmailValidator
            </span>
          </div>
          
          <h1 style={{
            fontSize: '2rem',
            fontWeight: '700',
            color: '#1e293b',
            margin: '0 0 8px 0'
          }}>
            Welcome Back
          </h1>
          
          <p style={{
            color: '#64748b',
            fontSize: '1rem',
            margin: 0
          }}>
            Sign in to your account to continue
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          {/* Email Field */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: '0.9rem',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '8px'
            }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail style={{
                position: 'absolute',
                left: '16px',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '20px',
                height: '20px',
                color: '#9ca3af'
              }} />
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
                required
                style={{
                  width: '100%',
                  padding: '16px 16px 16px 48px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '12px',
                  fontSize: '1rem',
                  transition: 'all 0.2s',
                  background: '#fff',
                  boxSizing: 'border-box'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#3b82f6';
                  e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#e5e7eb';
                  e.target.style.boxShadow = 'none';
                }}
              />
            </div>
          </div>

          {/* Password Field */}
          <div style={{ marginBottom: '32px' }}>
            <label style={{
              display: 'block',
              fontSize: '0.9rem',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '8px'
            }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock style={{
                position: 'absolute',
                left: '16px',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '20px',
                height: '20px',
                color: '#9ca3af'
              }} />
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                required
                style={{
                  width: '100%',
                  padding: '16px 48px 16px 48px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '12px',
                  fontSize: '1rem',
                  transition: 'all 0.2s',
                  background: '#fff',
                  boxSizing: 'border-box'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#3b82f6';
                  e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#e5e7eb';
                  e.target.style.boxShadow = 'none';
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '16px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  color: '#9ca3af',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                {showPassword ? 
                  <EyeOff style={{ width: '20px', height: '20px' }} /> : 
                  <Eye style={{ width: '20px', height: '20px' }} />
                }
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              background: error.includes('🚫 Account Suspended') ? '#fef2f2' : '#fee2e2',
              border: error.includes('🚫 Account Suspended') ? '2px solid #ef4444' : '1px solid #fecaca',
              color: '#dc2626',
              padding: error.includes('🚫 Account Suspended') ? '16px' : '12px 16px',
              borderRadius: '8px',
              fontSize: '0.9rem',
              marginBottom: '24px',
              whiteSpace: 'pre-line',
              fontWeight: error.includes('🚫 Account Suspended') ? '500' : 'normal'
            }}>
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              background: isLoading ? '#9ca3af' : 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              border: 'none',
              color: 'white',
              padding: '16px',
              borderRadius: '12px',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
            onMouseOver={(e) => {
              if (!isLoading) {
                e.target.style.transform = 'translateY(-1px)';
                e.target.style.boxShadow = '0 6px 16px rgba(59, 130, 246, 0.4)';
              }
            }}
            onMouseOut={(e) => {
              if (!isLoading) {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
              }
            }}
          >
            {isLoading ? (
              <>
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  borderTop: '2px solid white',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
                Signing In...
              </>
            ) : (
              <>
                <Shield style={{ width: '20px', height: '20px' }} />
                Sign In
              </>
            )}
          </button>
        </form>

        {/* Footer Links */}
        <div style={{
          textAlign: 'center',
          marginTop: '32px',
          paddingTop: '24px',
          borderTop: '1px solid #e5e7eb'
        }}>
          <p style={{
            color: '#64748b',
            fontSize: '0.9rem',
            margin: '0 0 16px 0'
          }}>
            Don't have an account?
          </p>
          <button
            onClick={() => window.location.href = '/signup'}
            style={{
              background: 'transparent',
              border: '2px solid #3b82f6',
              color: '#3b82f6',
              padding: '12px 24px',
              borderRadius: '8px',
              fontSize: '0.9rem',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.target.style.background = '#3b82f6';
              e.target.style.color = 'white';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'transparent';
              e.target.style.color = '#3b82f6';
            }}
          >
            Create Account
          </button>
        </div>

        {/* Features Preview */}
        <div style={{
          marginTop: '32px',
          padding: '20px',
          background: 'linear-gradient(135deg, #f8fafc, #e0e7ff)',
          borderRadius: '12px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            marginBottom: '12px'
          }}>
            <Zap style={{ width: '20px', height: '20px', color: '#3b82f6' }} />
            <span style={{
              fontSize: '0.9rem',
              fontWeight: '600',
              color: '#1e293b'
            }}>
              What you get with an account:
            </span>
          </div>
          <ul style={{
            margin: 0,
            padding: '0 0 0 20px',
            color: '#64748b',
            fontSize: '0.85rem',
            lineHeight: '1.6'
          }}>
            <li>Save and manage validation history</li>
            <li>API access with higher rate limits</li>
            <li>Advanced analytics and reporting</li>
            <li>Priority customer support</li>
          </ul>
        </div>
      </div>

      {/* CSS Animation */}
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default Login;
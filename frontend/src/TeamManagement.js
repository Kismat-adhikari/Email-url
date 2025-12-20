import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUsers, FiUser, FiLogOut, FiMoon, FiSun, FiActivity, FiZap } from 'react-icons/fi';
import './TeamManagement.css';
import { getCorrectApiLimit, formatApiUsageWithPeriod } from './utils/apiUtils';

const TeamManagement = () => {
    const navigate = useNavigate();
    
    // Get user data from localStorage and auth token
    const [user, setUser] = useState(() => {
        const savedUser = localStorage.getItem('user');
        return savedUser ? JSON.parse(savedUser) : null;
    });
    
    // Update user when localStorage changes
    useEffect(() => {
        const handleStorageChange = () => {
            const savedUser = localStorage.getItem('user');
            const newUser = savedUser ? JSON.parse(savedUser) : null;
            setUser(newUser);
        };
        
        // Listen for storage changes
        window.addEventListener('storage', handleStorageChange);
        
        // Also check periodically in case of same-tab changes
        const interval = setInterval(() => {
            const savedUser = localStorage.getItem('user');
            const newUser = savedUser ? JSON.parse(savedUser) : null;
            if (JSON.stringify(newUser) !== JSON.stringify(user)) {
                setUser(newUser);
            }
        }, 1000);
        
        return () => {
            window.removeEventListener('storage', handleStorageChange);
            clearInterval(interval);
        };
    }, [user]);
    
    const [authToken, setAuthToken] = useState(() => {
        return localStorage.getItem('authToken');
    });
    
    // Update auth token when localStorage changes
    useEffect(() => {
        const handleStorageChange = () => {
            const newToken = localStorage.getItem('authToken');
            setAuthToken(newToken);
        };
        
        // Listen for storage changes
        window.addEventListener('storage', handleStorageChange);
        
        // Also check periodically in case of same-tab changes
        const interval = setInterval(() => {
            const newToken = localStorage.getItem('authToken');
            if (newToken !== authToken) {
                setAuthToken(newToken);
            }
        }, 1000);
        
        return () => {
            window.removeEventListener('storage', handleStorageChange);
            clearInterval(interval);
        };
    }, [authToken]);
    
    const [teamInfo, setTeamInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [buttonLoading, setButtonLoading] = useState(false); // Separate loading state for buttons
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    
    // Dark mode state
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem('darkMode');
        return saved ? JSON.parse(saved) : false;
    });
    
    // Team creation
    const [showCreateTeam, setShowCreateTeam] = useState(false);
    const [teamName, setTeamName] = useState('');
    const [teamDescription, setTeamDescription] = useState('');
    
    // Team invitation
    const [generatedInviteLink, setGeneratedInviteLink] = useState('');
    const [showLinkModal, setShowLinkModal] = useState(false);
    
    // Team eligibility
    const [canCreateTeam, setCanCreateTeam] = useState(false);

    // Dark mode effect
    useEffect(() => {
        if (darkMode) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
        localStorage.setItem('darkMode', JSON.stringify(darkMode));
    }, [darkMode]);

    const toggleDarkMode = () => {
        setDarkMode(!darkMode);
    };

    const handleLogout = async () => {
        try {
            if (authToken) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local storage
            localStorage.removeItem('authToken');
            localStorage.removeItem('user');
            
            // Redirect to home
            navigate('/');
        }
    };

    const getAuthHeaders = useCallback(() => {
        return {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        };
    }, [authToken]);

    const checkUserStatus = useCallback(async () => {
        try {
            setLoading(true);
            setError(''); // Clear previous errors
            
            // OPTIMIZED: Make both API calls in parallel for faster loading
            const promises = [];
            
            // Add user data refresh if authenticated
            if (authToken) {
                promises.push(
                    fetch('/api/auth/me', {
                        headers: getAuthHeaders()
                    }).then(response => ({ type: 'user', response }))
                );
            }
            
            // Add team status call
            promises.push(
                fetch('/api/team/status', {
                    headers: getAuthHeaders()
                }).then(response => ({ type: 'team', response }))
            );
            
            // Execute both calls in parallel
            const results = await Promise.all(promises);
            
            // Process results
            for (const result of results) {
                if (result.type === 'user') {
                    if (result.response.ok) {
                        const userData = await result.response.json();
                        const updatedUser = userData.user;
                        setUser(updatedUser);
                        localStorage.setItem('user', JSON.stringify(updatedUser));
                    } else if (result.response.status === 401) {
                        // Only redirect on actual 401 from server, and only if we don't have valid user data
                        console.log('Authentication failed for user data refresh');
                        if (!user) {
                            // Only redirect if we don't have any user data at all
                            console.log('No user data available, redirecting to login');
                            localStorage.removeItem('authToken');
                            localStorage.removeItem('user');
                            navigate('/login');
                            return;
                        }
                        // If we have user data, just log the error but don't redirect
                        console.log('User data refresh failed but keeping existing user data');
                    }
                } else if (result.type === 'team') {
                    if (result.response.ok) {
                        const data = await result.response.json();
                        setCanCreateTeam(data.can_create_team);
                        
                        // Set team info if user is in a team
                        if (data.team_info && data.team_info.success) {
                            setTeamInfo(data.team_info);
                        } else {
                            setTeamInfo(null);
                        }
                    } else if (result.response.status === 401) {
                        // Only redirect on actual 401 from server, and only if critical
                        console.log('Team API authentication failed');
                        if (!user && !teamInfo) {
                            // Only redirect if we have no user data AND no team info
                            console.log('No user or team data available, redirecting to login');
                            localStorage.removeItem('authToken');
                            localStorage.removeItem('user');
                            navigate('/login');
                            return;
                        }
                        // If we have some data, just log the error but don't redirect
                        console.log('Team API failed but keeping existing data');
                    } else {
                        // Don't show errors for other status codes to avoid spam
                        console.log('Team status error:', result.response.status);
                    }
                }
            }
        } catch (err) {
            console.error('Team status error:', err);
            // Don't show network errors to avoid spam
        } finally {
            setLoading(false);
        }
    }, [authToken, user, teamInfo, navigate, getAuthHeaders]);

    useEffect(() => {
        // Initial load
        checkUserStatus();
        
        // Real-time polling every 60 seconds for team updates (reduced to prevent token issues)
        const interval = setInterval(() => {
            if (!loading) {
                checkUserStatus();
            }
        }, 60000); // Reduced frequency to prevent authentication issues
        
        // Immediate refresh when page becomes visible
        const handleVisibilityChange = () => {
            if (!document.hidden) {
                checkUserStatus();
            }
        };
        
        // Immediate refresh when window gets focus
        const handleFocus = () => {
            checkUserStatus();
        };
        
        document.addEventListener('visibilitychange', handleVisibilityChange);
        window.addEventListener('focus', handleFocus);
        
        // Cleanup interval and event listeners on unmount
        return () => {
            clearInterval(interval);
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            window.removeEventListener('focus', handleFocus);
        };
    }, [checkUserStatus, loading]); // Include dependencies

    const createTeam = async (e) => {
        e.preventDefault();
        
        if (!teamName.trim()) {
            setError('Team name is required');
            return;
        }

        try {
            setButtonLoading(true);
            const response = await fetch('/api/team/create', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    name: teamName.trim(),
                    description: teamDescription.trim()
                })
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess('Team created successfully!');
                setShowCreateTeam(false);
                setTeamName('');
                setTeamDescription('');
                checkUserStatus(); // Refresh team info
            } else {
                setError(data.error || 'Failed to create team');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setButtonLoading(false);
        }
    };

    const generateInviteLink = async () => {
        try {
            setButtonLoading(true); // Use separate button loading state
            setError('');
            
            // Generate a unique email to avoid "already invited" errors
            const randomId = Math.random().toString(36).substring(7);
            const genericEmail = `invite-${randomId}@temp.com`;
            
            const response = await fetch('/api/team/invite', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    email: genericEmail,
                    message: 'Join our team!'
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Show the invitation link in a modal
                const inviteLink = data.invite_link;
                setGeneratedInviteLink(inviteLink);
                setShowLinkModal(true);
                
                // Copy link to clipboard automatically
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(inviteLink);
                    setSuccess('Invite link generated and copied to clipboard!');
                }
                
                // Real-time refresh after generating link (don't block button)
                setTimeout(() => checkUserStatus(), 500);
            } else {
                setError(data.error || 'Failed to generate invite link');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setButtonLoading(false); // Reset button loading state
        }
    };



    const removeMember = async (memberId) => {
        if (!window.confirm('Are you sure you want to remove this member?')) {
            return;
        }

        try {
            setButtonLoading(true);
            const response = await fetch(`/api/team/members/${memberId}/remove`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess('Member removed successfully');
                setTimeout(() => checkUserStatus(), 500); // Refresh team info
            } else {
                setError(data.error || 'Failed to remove member');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setButtonLoading(false);
        }
    };

    const leaveTeam = async () => {
        if (!window.confirm('Are you sure you want to leave this team? You will lose Pro access.')) {
            return;
        }

        try {
            setButtonLoading(true);
            const response = await fetch('/api/team/leave', {
                method: 'POST',
                headers: getAuthHeaders()
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess('Successfully left the team');
                setTimeout(() => checkUserStatus(), 500); // Refresh status
            } else {
                setError(data.error || 'Failed to leave team');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setButtonLoading(false);
        }
    };

    // Check if user is authenticated - but be less aggressive about redirects
    // Only redirect if we're sure there's no auth token at all
    if (!authToken) {
        return (
            <div className="App">
                {/* Top Navigation Bar */}
                <nav className="top-navbar">
                    <div className="navbar-container">
                        {/* Logo Section */}
                        <div className="navbar-logo">
                            <span className="logo-text" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>LAGCI</span>
                        </div>

                        {/* Right Section */}
                        <div className="navbar-right">
                            {/* Dark Mode Toggle */}
                            <button className="navbar-btn dark-mode-btn" onClick={toggleDarkMode} title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
                                {darkMode ? <FiSun /> : <FiMoon />}
                            </button>

                            {/* Authentication Buttons */}
                            <div className="auth-buttons">
                                <button className="navbar-btn login-btn" onClick={() => navigate('/login')}>
                                    Login
                                </button>
                                <button className="navbar-btn signup-btn" onClick={() => navigate('/signup')}>
                                    Sign Up
                                </button>
                            </div>
                        </div>
                    </div>
                </nav>

                <div className="pro-container">
                    <div className="pro-main-card">
                        <div className="pro-content">
                            <div className="profile-error">
                                <h2>Access Denied</h2>
                                <p>Please log in to access team management.</p>
                                <button className="pro-validate-btn" onClick={() => navigate('/login')}>
                                    Go to Login
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // If we have a token but no user data yet, show loading (don't redirect)
    if (!user && authToken) {
        return (
            <div className="App">
                {/* Top Navigation Bar */}
                <nav className="top-navbar">
                    <div className="navbar-container">
                        {/* Logo Section */}
                        <div className="navbar-logo">
                            <span className="logo-text" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>LAGCI</span>
                        </div>

                        {/* Right Section */}
                        <div className="navbar-right">
                            {/* Dark Mode Toggle */}
                            <button className="navbar-btn dark-mode-btn" onClick={toggleDarkMode} title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
                                {darkMode ? <FiSun /> : <FiMoon />}
                            </button>
                        </div>
                    </div>
                </nav>

                <div className="pro-container">
                    <div className="pro-main-card">
                        <div className="loading-skeleton">
                            <div className="skeleton-card">
                                <div className="skeleton-line skeleton-title"></div>
                                <div className="skeleton-line skeleton-text"></div>
                                <div className="skeleton-line skeleton-text short"></div>
                            </div>
                        </div>
                        <style jsx>{`
                            .loading-skeleton {
                                padding: 20px;
                            }
                            .skeleton-card {
                                background: #f8f9fa;
                                border-radius: 8px;
                                padding: 24px;
                                margin-bottom: 16px;
                            }
                            .skeleton-line {
                                height: 16px;
                                background: linear-gradient(90deg, #e0e0e0 25%, #f0f0f0 50%, #e0e0e0 75%);
                                background-size: 200% 100%;
                                animation: loading 1.5s infinite;
                                border-radius: 4px;
                                margin-bottom: 12px;
                            }
                            .skeleton-title {
                                height: 24px;
                                width: 60%;
                            }
                            .skeleton-text {
                                width: 80%;
                            }
                            .skeleton-text.short {
                                width: 40%;
                            }
                            @keyframes loading {
                                0% { background-position: 200% 0; }
                                100% { background-position: -200% 0; }
                            }
                        `}</style>
                    </div>
                </div>
            </div>
        );
    }

    if (loading && !teamInfo && !canCreateTeam) {
        return (
            <div className="App">
                {/* Top Navigation Bar */}
                <nav className="top-navbar">
                    <div className="navbar-container">
                        {/* Logo Section */}
                        <div className="navbar-logo">
                            <span className="logo-text" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>LAGCI</span>
                        </div>

                        {/* Center Section - User Info */}
                        <div className="navbar-center">
                            <div className="user-greeting">
                                <span className="wave-icon">👋</span>
                                <span className="greeting-text">Welcome, {user.firstName}!</span>
                            </div>
                        </div>

                        {/* Right Section - API Usage & Controls */}
                        <div className="navbar-right">
                            {/* Dark Mode Toggle */}
                            <button className="navbar-btn dark-mode-btn" onClick={toggleDarkMode} title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
                                {darkMode ? <FiSun /> : <FiMoon />}
                            </button>

                            {/* API Usage Counter */}
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
                            </div>

                            {/* Authentication Buttons */}
                            <div className="auth-buttons">
                                <button className="navbar-btn profile-btn" onClick={() => navigate('/profile')}>
                                    <FiUser /> Profile
                                </button>
                                <button className="navbar-btn team-btn" onClick={() => navigate('/team')} style={{background: '#007bff'}}>
                                    <FiUsers /> Team
                                </button>
                                <button className="navbar-btn logout-btn" onClick={handleLogout}>
                                    <FiLogOut /> Logout
                                </button>
                            </div>
                        </div>
                    </div>
                </nav>

                <div className="pro-container">
                    <div className="pro-main-card">
                        <div className="loading-skeleton">
                            <div className="skeleton-card">
                                <div className="skeleton-line skeleton-title"></div>
                                <div className="skeleton-line skeleton-text"></div>
                                <div className="skeleton-line skeleton-text short"></div>
                            </div>
                        </div>
                        <style jsx>{`
                            .loading-skeleton {
                                padding: 20px;
                            }
                            .skeleton-card {
                                background: #f8f9fa;
                                border-radius: 8px;
                                padding: 24px;
                                margin-bottom: 16px;
                            }
                            .skeleton-line {
                                height: 16px;
                                background: linear-gradient(90deg, #e0e0e0 25%, #f0f0f0 50%, #e0e0e0 75%);
                                background-size: 200% 100%;
                                animation: loading 1.5s infinite;
                                border-radius: 4px;
                                margin-bottom: 12px;
                            }
                            .skeleton-title {
                                height: 24px;
                                width: 60%;
                            }
                            .skeleton-text {
                                width: 80%;
                            }
                            .skeleton-text.short {
                                width: 40%;
                            }
                            @keyframes loading {
                                0% { background-position: 200% 0; }
                                100% { background-position: -200% 0; }
                            }
                        `}</style>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="App">
            {/* Top Navigation Bar */}
            <nav className="top-navbar">
                <div className="navbar-container">
                    {/* Logo Section */}
                    <div className="navbar-logo">
                        <span className="logo-text" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>LAGCI</span>
                    </div>

                    {/* Center Section - User Info */}
                    <div className="navbar-center">
                        <div className="user-greeting">
                            <span className="wave-icon">👋</span>
                            <span className="greeting-text">Welcome, {user.firstName}!</span>
                        </div>
                    </div>

                    {/* Right Section - API Usage & Controls */}
                    <div className="navbar-right">
                        {/* Dark Mode Toggle */}
                        <button className="navbar-btn dark-mode-btn" onClick={toggleDarkMode} title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
                            {darkMode ? <FiSun /> : <FiMoon />}
                        </button>

                        {/* API Usage Counter */}
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
                            {user.subscriptionTier === 'pro' && (
                                <div className="pro-badge-hint">
                                    💎 Pro Features Unlocked!
                                </div>
                            )}
                        </div>

                        {/* Authentication Buttons */}
                        <div className="auth-buttons">
                            <button className="navbar-btn profile-btn" onClick={() => navigate('/profile')}>
                                <FiUser /> Profile
                            </button>
                            <button className="navbar-btn team-btn" onClick={() => navigate('/team')} style={{background: '#007bff'}}>
                                <FiUsers /> Team
                            </button>
                            <button className="navbar-btn logout-btn" onClick={handleLogout}>
                                <FiLogOut /> Logout
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <div className="pro-container">
                {/* Simplified Header */}
                <header className="pro-header-simple">
                    <div className="pro-header-title">
                        <h1><FiUsers /> Team Management</h1>
                    </div>
                    <p className="pro-header-subtitle">
                        Collaborate with your team and share validation quotas
                    </p>
                </header>

                {/* Main Card */}
                <div className="pro-main-card">
                    <div className="team-management">
                        <div className="team-header">
                            {error && <div className="error-message">{error}</div>}
                            {success && <div className="success-message">{success}</div>}
                        </div>

            {/* No Team - Show Create Option */}
            {canCreateTeam && !teamInfo && (
                <div className="no-team-section">
                    <div className="team-benefits">
                        <h3>Create Your Team</h3>
                        <p>As a Starter/Pro user, you can create a team and invite members to share your monthly validations.</p>
                        
                        <div className="benefits-list">
                            <div className="benefit">✅ Share 10 million lifetime validations</div>
                            <div className="benefit">✅ Invite up to 10 team members</div>
                            <div className="benefit">✅ Centralized team management</div>
                            <div className="benefit">✅ Shared validation history</div>
                        </div>
                        
                        <button 
                            className="create-team-btn"
                            onClick={() => setShowCreateTeam(true)}
                        >
                            Create Team
                        </button>
                    </div>
                </div>
            )}



            {/* Create Team Modal */}
            {showCreateTeam && (
                <div className="modal-overlay">
                    <div className="modal">
                        <div className="modal-header">
                            <h3>Create New Team</h3>
                            <button 
                                className="close-btn"
                                onClick={() => setShowCreateTeam(false)}
                            >
                                ×
                            </button>
                        </div>
                        
                        <form onSubmit={createTeam}>
                            <div className="form-group">
                                <label>Team Name *</label>
                                <input
                                    type="text"
                                    value={teamName}
                                    onChange={(e) => setTeamName(e.target.value)}
                                    placeholder="Enter team name"
                                    required
                                />
                            </div>
                            
                            <div className="form-group">
                                <label>Description (Optional)</label>
                                <textarea
                                    value={teamDescription}
                                    onChange={(e) => setTeamDescription(e.target.value)}
                                    placeholder="Describe your team"
                                    rows="3"
                                />
                            </div>
                            
                            <div className="modal-actions">
                                <button type="button" onClick={() => setShowCreateTeam(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="primary" disabled={buttonLoading}>
                                    {buttonLoading ? 'Creating...' : 'Create Team'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Team Dashboard */}
            {teamInfo && (
                <div className="team-dashboard">
                    <div className="team-overview">
                        <div className="team-info">
                            <h3>{teamInfo.team.name}</h3>
                            <p className="team-description">{teamInfo.team.description}</p>
                            <div className="team-stats">
                                <div className="stat">
                                    <span className="label">Members:</span>
                                    <span className="value">{teamInfo.team.member_count}/{teamInfo.team.max_members}</span>
                                </div>
                                <div className="stat">
                                    <span className="label">Your Role:</span>
                                    <span className="value role">{teamInfo.user_role}</span>
                                </div>
                            </div>
                        </div>

                        <div className="quota-info">
                            <h4>Team Quota Usage</h4>
                            <div className="quota-bar">
                                <div 
                                    className="quota-fill"
                                    style={{ 
                                        width: `${(() => {
                                            const quotaUsed = teamInfo.team.quota_used || 0;
                                            const quotaLimit = teamInfo.team.quota_limit || 10000000;
                                            const percentage = (quotaUsed / quotaLimit) * 100;
                                            // Ensure minimum visible width for small percentages (0.5% minimum)
                                            return Math.max(percentage, quotaUsed > 0 ? 0.5 : 0);
                                        })()}%` 
                                    }}
                                />
                            </div>
                            <div className="quota-details">
                                <span>{teamInfo.team.quota_used.toLocaleString()} / {teamInfo.team.quota_limit.toLocaleString()} validations</span>
                                <span>
                                    {(() => {
                                        const quotaUsed = teamInfo.team.quota_used || 0;
                                        const quotaLimit = teamInfo.team.quota_limit || 10000000;
                                        const percentage = (quotaUsed / quotaLimit) * 100;
                                        // Show 3 decimal places for small percentages, round for larger ones
                                        return percentage < 1 && percentage > 0 ? percentage.toFixed(3) : Math.round(percentage);
                                    })()}% used
                                </span>
                            </div>
                            <p className="quota-reset">
                                Lifetime quota (no reset)
                            </p>
                        </div>
                    </div>

                    {/* Team Actions */}
                    {(teamInfo.user_role === 'owner' || teamInfo.user_role === 'admin') && (
                        <div className="team-actions">
                            <button 
                                className="invite-btn"
                                onClick={generateInviteLink}
                                disabled={buttonLoading}
                                style={{
                                    background: buttonLoading ? '#6c757d' : '#28a745',
                                    color: 'white',
                                    border: 'none',
                                    padding: '12px 24px',
                                    borderRadius: '6px',
                                    cursor: buttonLoading ? 'not-allowed' : 'pointer',
                                    fontSize: '16px',
                                    fontWeight: '500',
                                    opacity: buttonLoading ? 0.7 : 1,
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                {buttonLoading ? 'Generating...' : '🔗 Generate Invite Link'}
                            </button>
                        </div>
                    )}

                    {/* Team Members */}
                    <div className="team-members">
                        <h4>Team Members ({teamInfo.members.length})</h4>
                        <div className="members-list">
                            {teamInfo.members.map(member => (
                                <div key={member.id} className="member-card">
                                    <div className="member-info">
                                        <div className="member-name">{member.full_name}</div>
                                        <div className="member-email">{member.email}</div>
                                        <div className="member-role">{member.role}</div>
                                    </div>
                                    <div className="member-stats">
                                        <span>{member.validations_count} validations</span>
                                    </div>
                                    {(teamInfo.user_role === 'owner' || teamInfo.user_role === 'admin') && 
                                     member.role !== 'owner' && (
                                        <button 
                                            className="remove-btn"
                                            onClick={() => removeMember(member.user_id)}
                                        >
                                            Remove
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Pending Invitations - Only show real email invitations, not temp ones */}
                    {teamInfo.pending_invitations && teamInfo.pending_invitations.filter(invite => 
                        !invite.email.includes('@temp.com') && 
                        !invite.email.startsWith('invite-')
                    ).length > 0 && (
                        <div className="pending-invitations">
                            <h4>Pending Invitations ({teamInfo.pending_invitations.filter(invite => 
                                !invite.email.includes('@temp.com') && 
                                !invite.email.startsWith('invite-')
                            ).length})</h4>
                            <div className="invitations-list">
                                {teamInfo.pending_invitations
                                    .filter(invite => !invite.email.includes('@temp.com') && !invite.email.startsWith('invite-'))
                                    .map(invite => (
                                    <div key={invite.id} className="invitation-card">
                                        <div className="invite-email">{invite.email}</div>
                                        <div className="invite-date">
                                            Sent {new Date(invite.created_at).toLocaleDateString()}
                                        </div>
                                        <div className="invite-expires">
                                            Expires {new Date(invite.expires_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Leave Team */}
                    {teamInfo.user_role !== 'owner' && (
                        <div className="danger-zone">
                            <h4>Danger Zone</h4>
                            <button 
                                className="leave-team-btn"
                                onClick={leaveTeam}
                            >
                                Leave Team
                            </button>
                            <p className="warning">
                                Warning: Leaving the team will remove your Pro access unless you have your own Pro subscription.
                            </p>
                        </div>
                    )}
                </div>
            )}



            {/* Invitation Link Modal */}
            {showLinkModal && (
                <div className="modal-overlay">
                    <div className="modal">
                        <div className="modal-header">
                            <h3>🔗 Team Invite Link</h3>
                            <button 
                                className="close-btn"
                                onClick={() => setShowLinkModal(false)}
                            >
                                ×
                            </button>
                        </div>
                        
                        <div style={{ padding: '24px' }}>
                            <p><strong>Your team invite link is ready!</strong></p>
                            <p>Anyone with this link can join your team:</p>
                            
                            <div className="link-container" style={{
                                background: '#f8f9fa',
                                border: '1px solid #dee2e6',
                                borderRadius: '6px',
                                padding: '12px',
                                marginBottom: '16px',
                                wordBreak: 'break-all',
                                fontFamily: 'monospace',
                                fontSize: '14px'
                            }}>
                                {generatedInviteLink}
                            </div>
                            
                            <div className="link-actions" style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                                <button 
                                    className="btn-primary"
                                    onClick={() => {
                                        navigator.clipboard.writeText(generatedInviteLink);
                                        setSuccess('Link copied to clipboard!');
                                    }}
                                >
                                    📋 Copy Link
                                </button>
                                
                                <button 
                                    className="btn-secondary"
                                    onClick={() => {
                                        const text = `Join our team! ${generatedInviteLink}`;
                                        if (navigator.share) {
                                            navigator.share({ title: 'Team Invitation', text: text });
                                        } else {
                                            const subject = encodeURIComponent('Join our team!');
                                            const body = encodeURIComponent(`You're invited to join our team!\n\nClick this link to accept: ${generatedInviteLink}`);
                                            window.open(`mailto:?subject=${subject}&body=${body}`);
                                        }
                                    }}
                                >
                                    📤 Share Link
                                </button>
                            </div>
                            
                            <div style={{ fontSize: '14px', color: '#666' }}>
                                <p><strong>How it works:</strong></p>
                                <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                                    <li>Share this link via WhatsApp, Slack, email, or any method</li>
                                    <li>They'll see an invitation page with team details</li>
                                    <li>They can register a new account or login</li>
                                    <li>They'll automatically get Pro access and join your team</li>
                                </ul>
                                <p><em>Link expires in 7 days</em></p>
                            </div>
                            
                            <div className="modal-actions">
                                <button 
                                    className="btn-primary"
                                    onClick={() => setShowLinkModal(false)}
                                >
                                    Done
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Not Eligible */}
            {!canCreateTeam && !teamInfo && (
                <div className="not-eligible">
                    <h3>Team Features</h3>
                    <p>Team collaboration is available for Starter and Pro users.</p>
                    

                    
                    <div className="upgrade-prompt">
                        <p>Upgrade to Starter or Pro to:</p>
                        <ul>
                            <li>Create teams and invite members</li>
                            <li>Share 10 million lifetime validations</li>
                            <li>Collaborate with your team</li>
                            <li>Centralized team management</li>
                        </ul>
                        <button className="upgrade-btn">
                            Upgrade Now
                        </button>
                    </div>
                </div>
            )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TeamManagement;
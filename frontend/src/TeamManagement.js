import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUsers, FiUser, FiLogOut, FiMoon, FiSun, FiActivity, FiZap } from 'react-icons/fi';
import './TeamManagement.css';
import { getCorrectApiLimit, formatApiUsageWithPeriod } from './utils/apiUtils';

const TeamManagement = () => {
    const navigate = useNavigate();
    
    // ============ STATE MANAGEMENT ============
    const [user, setUser] = useState(() => {
        const saved = localStorage.getItem('user');
        return saved ? JSON.parse(saved) : null;
    });

    const [authToken, setAuthToken] = useState(() => localStorage.getItem('authToken'));
    
    const [teamInfo, setTeamInfo] = useState(null);
    const [teamQuickInfo, setTeamQuickInfo] = useState(null);
    const [inTeam, setInTeam] = useState(false);
    const [loading, setLoading] = useState(true);
    const [loadingFullTeamInfo, setLoadingFullTeamInfo] = useState(false);
    const [buttonLoading, setButtonLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem('darkMode');
        return saved ? JSON.parse(saved) : false;
    });

    // Modal and form states
    const [showCreateTeam, setShowCreateTeam] = useState(false);
    const [teamName, setTeamName] = useState('');
    const [teamDescription, setTeamDescription] = useState('');
    const [generatedInviteLink, setGeneratedInviteLink] = useState('');
    const [showLinkModal, setShowLinkModal] = useState(false);
    const [canCreateTeam, setCanCreateTeam] = useState(false);

    const isFetchingStatus = useRef(false);
    const isLoadingQuickInfo = useRef(false);
    const isLoadingFullInfo = useRef(false);
    const lastStatusCheck = useRef(0);

    // ============ API UTILITIES ============
    const apiTargets = useMemo(() => {
        const targets = [''];
        try {
            if (typeof window !== 'undefined' && window.location?.port === '3000') {
                targets.unshift('http://localhost:5000');
            }
        } catch (e) {
            // ignore
        }
        return targets;
    }, []);

    const fetchTeamApi = useCallback(async (path, options = {}) => {
        let lastError = null;
        for (const base of apiTargets) {
            try {
                return await fetch(`${base}${path}`, options);
            } catch (err) {
                lastError = err;
            }
        }
        throw lastError || new Error('All API endpoints failed');
    }, [apiTargets]);

    const getAuthHeaders = useCallback(() => ({
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
    }), [authToken]);

    // ============ SYNC WITH LOCALSTORAGE ============
    useEffect(() => {
        const checkAuth = () => {
            const newToken = localStorage.getItem('authToken');
            const newUser = localStorage.getItem('user');
            
            if (newToken !== authToken) {
                setAuthToken(newToken);
            }
            if (newUser !== JSON.stringify(user)) {
                try {
                    setUser(newUser ? JSON.parse(newUser) : null);
                } catch (e) {
                    setUser(null);
                }
            }
        };

        // Only listen to cross-tab storage changes; avoid same-tab polling
        window.addEventListener('storage', checkAuth);
        return () => {
            window.removeEventListener('storage', checkAuth);
        };
    }, [authToken, user]);

    // ============ HYDRATE USER ============
    useEffect(() => {
        let abort = false;

        const hydrateUser = async () => {
            if (!authToken || user) return;

            try {
                const res = await fetchTeamApi('/api/auth/me', {
                    headers: getAuthHeaders()
                });

                if (res.ok && !abort) {
                    const data = await res.json();
                    if (data.user) {
                        setUser(data.user);
                        localStorage.setItem('user', JSON.stringify(data.user));
                    }
                }
            } catch (err) {
                console.error('Hydrate user error:', err);
            }
        };

        hydrateUser();
        return () => { abort = true; };
    }, [authToken]); // Simplified deps - fetchTeamApi and getAuthHeaders are stable

    // ============ LOAD TEAM DATA ============
    const loadTeamQuickInfo = useCallback(async () => {
        if (isLoadingQuickInfo.current) return;
        isLoadingQuickInfo.current = true;
        try {
            // Parallel load: try quick-info and full-info together
            const [qRes, fRes] = await Promise.all([
                fetchTeamApi('/api/team/quick-info', { headers: getAuthHeaders() }),
                fetchTeamApi('/api/team/info', { headers: getAuthHeaders() })
            ]);

            if (qRes.ok) {
                const qData = await qRes.json();
                setTeamQuickInfo(qData);
            } else if (qRes.status === 404) {
                setTeamQuickInfo(null);
                setTeamInfo(null);
            } else {
                setTeamQuickInfo(null);
            }

            if (fRes.ok) {
                const fData = await fRes.json();
                setTeamInfo(fData);
            }
        } catch (err) {
            console.error('Quick info error:', err);
            setError('Failed to load team info');
        } finally {
            isLoadingQuickInfo.current = false;
        }
    }, [fetchTeamApi, getAuthHeaders]);


    // No longer needed - integrated into loadTeamQuickInfo for parallel loading

    const checkUserStatus = useCallback(async () => {
        if (isFetchingStatus.current || !authToken) return;
        
        isFetchingStatus.current = true;
        try {
            // Only set loading if we have no data yet to avoid flicker
            if (!teamInfo && !teamQuickInfo) {
                setLoading(true);
            }
            setError('');

            const res = await fetchTeamApi('/api/team/status', {
                headers: getAuthHeaders()
            });

            if (!res.ok) {
                if (res.status === 401) {
                    localStorage.removeItem('authToken');
                    localStorage.removeItem('user');
                    navigate('/login');
                    return;
                }
                throw new Error('Status check failed');
            }

            const data = await res.json();

            // Update subscription tier if provided
            if (data.subscription_tier && user?.subscriptionTier !== data.subscription_tier) {
                const updated = { ...user, subscriptionTier: data.subscription_tier };
                setUser(updated);
                localStorage.setItem('user', JSON.stringify(updated));
            }

            // Track membership and eligibility
            const inTeamNow = !!data.in_team;
            setInTeam(inTeamNow);
            // Set eligibility
            const isEligible = user && ['starter', 'pro'].includes((user.subscriptionTier || '').toLowerCase());
            setCanCreateTeam(data.can_create_team || (!data.in_team && isEligible));

            // Load team if in team
            if (data.in_team) {
                if (!isLoadingQuickInfo.current && !isLoadingFullInfo.current) {
                    loadTeamQuickInfo();
                }
            } else {
                setTeamInfo(null);
                setTeamQuickInfo(null);
            }
        } catch (err) {
            console.error('Status error:', err);
            const isEligible = user && ['starter', 'pro'].includes((user.subscriptionTier || '').toLowerCase());
            setCanCreateTeam(isEligible);
            setError('Unable to load team status');
        } finally {
            setLoading(false);
            isFetchingStatus.current = false;
        }
    }, [authToken, fetchTeamApi, getAuthHeaders, user, navigate, loadTeamQuickInfo]);

    // ============ LIFECYCLE EFFECTS ============
    useEffect(() => {
        const safeCheck = () => {
            const now = Date.now();
            if (now - lastStatusCheck.current < 30000) return; // throttle 30s
            lastStatusCheck.current = now;
            checkUserStatus();
        };

        // Initial load
        safeCheck();

        // Poll less frequently and through throttle
        const interval = setInterval(safeCheck, 180000); // every 3 minutes

        const handleVisibility = () => { if (!document.hidden) safeCheck(); };
        const handleFocus = () => { safeCheck(); };

        document.addEventListener('visibilitychange', handleVisibility);
        window.addEventListener('focus', handleFocus);

        return () => {
            clearInterval(interval);
            document.removeEventListener('visibilitychange', handleVisibility);
            window.removeEventListener('focus', handleFocus);
        };
    }, [checkUserStatus]);

    // Trigger check when user hydrates
    useEffect(() => {
        if (user && authToken && loading) {
            checkUserStatus();
        }
    }, [user, authToken]);

    // ============ DARK MODE ============
    useEffect(() => {
        if (darkMode) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
        localStorage.setItem('darkMode', JSON.stringify(darkMode));
    }, [darkMode]);

    // ============ HANDLERS ============
    const handleLogout = async () => {
        try {
            if (authToken) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
            }
        } catch (err) {
            console.error('Logout error:', err);
        } finally {
            localStorage.removeItem('authToken');
            localStorage.removeItem('user');
            navigate('/');
        }
    };

    const handleCreateTeam = async (e) => {
        e.preventDefault();
        if (!teamName.trim()) {
            setError('Team name is required');
            return;
        }

        setButtonLoading(true);
        try {
            const res = await fetchTeamApi('/api/team/create', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    name: teamName.trim(),
                    description: teamDescription.trim()
                })
            });

            const data = await res.json();
            if (res.ok) {
                setSuccess('Team created!');
                setShowCreateTeam(false);
                setTeamName('');
                setTeamDescription('');
                setTimeout(() => checkUserStatus(), 500);
            } else {
                setError(data.error || 'Failed to create team');
            }
        } catch (err) {
            setError('Network error');
        } finally {
            setButtonLoading(false);
        }
    };

    const handleGenerateInvite = async () => {
        setButtonLoading(true);
        setError('');

        try {
            const randomId = Math.random().toString(36).substring(7);
            const res = await fetchTeamApi('/api/team/invite', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    email: `invite-${randomId}@temp.com`,
                    message: 'Join our team!'
                })
            });

            const data = await res.json();
            if (res.ok) {
                setGeneratedInviteLink(data.invite_link);
                setShowLinkModal(true);
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(data.invite_link);
                    setSuccess('Link copied!');
                }
                setTimeout(() => checkUserStatus(), 500);
            } else {
                setError(data.error || 'Failed to generate link');
            }
        } catch (err) {
            setError('Network error');
        } finally {
            setButtonLoading(false);
        }
    };

    const handleRemoveMember = async (memberId) => {
        if (!window.confirm('Remove this member?')) return;

        setButtonLoading(true);
        try {
            const res = await fetchTeamApi(`/api/team/members/${memberId}/remove`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });

            if (res.ok) {
                setSuccess('Member removed');
                setTimeout(() => checkUserStatus(), 500);
            } else {
                const data = await res.json();
                setError(data.error || 'Failed to remove member');
            }
        } catch (err) {
            setError('Network error');
        } finally {
            setButtonLoading(false);
        }
    };

    const handleLeaveTeam = async () => {
        if (!window.confirm('Leave this team? You will lose Pro access unless you have your own subscription.')) return;

        setButtonLoading(true);
        try {
            const res = await fetchTeamApi('/api/team/leave', {
                method: 'POST',
                headers: getAuthHeaders()
            });

            if (res.ok) {
                setSuccess('Left team');
                setTimeout(() => checkUserStatus(), 500);
            } else {
                const data = await res.json();
                setError(data.error || 'Failed to leave team');
            }
        } catch (err) {
            setError('Network error');
        } finally {
            setButtonLoading(false);
        }
    };

    // ============ RENDERS ============
    const renderNavBar = () => (
        <nav className="top-navbar">
            <div className="navbar-container">
                <div className="navbar-logo">
                    <span className="logo-text" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>LAGCI</span>
                </div>

                {user && (
                    <div className="navbar-center">
                        <div className="user-greeting">
                            <span className="wave-icon">👋</span>
                            <span className="greeting-text">Welcome, {user?.firstName || 'User'}!</span>
                        </div>
                    </div>
                )}

                <div className="navbar-right">
                    <button className="navbar-btn dark-mode-btn" onClick={() => setDarkMode(!darkMode)} 
                        title={darkMode ? 'Light Mode' : 'Dark Mode'}>
                        {darkMode ? <FiSun /> : <FiMoon />}
                    </button>

                    {user && (
                        <>
                            <div className={`api-usage-counter ${
                                (user?.subscriptionTier || '').toLowerCase() === 'pro' ? 'pro-tier' : ''
                            }`}>
                                <FiActivity className="usage-icon" />
                                <span className="usage-text">
                                    {user?.teamId && user?.teamInfo 
                                        ? `${(user?.teamInfo?.quota_used || 0).toLocaleString()}/${(user?.teamInfo?.quota_limit || 10000000).toLocaleString()} (Team)`
                                        : formatApiUsageWithPeriod((user?.apiCallsCount || 0), user?.apiCallsLimit, user?.subscriptionTier || 'free')
                                    }
                                </span>
                                <span className="usage-label">
                                    {user?.teamId && user?.teamInfo ? 'Team Quota' : 
                                     (user?.subscriptionTier || 'free') === 'free' ? 'Free' : 
                                     (user?.subscriptionTier || '').toLowerCase() === 'starter' ? 'Starter' : 
                                     (user?.subscriptionTier || '').toLowerCase() === 'pro' ? 'Pro' : 'API'}
                                </span>
                            </div>

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
                        </>
                    )}

                    {!user && (
                        <div className="auth-buttons">
                            <button className="navbar-btn login-btn" onClick={() => navigate('/login')}>Login</button>
                            <button className="navbar-btn signup-btn" onClick={() => navigate('/signup')}>Sign Up</button>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );

    const renderSkeleton = () => (
        <div className="loading-skeleton">
            <div className="skeleton-card">
                <div className="skeleton-line skeleton-title"></div>
                <div className="skeleton-line skeleton-text"></div>
                <div className="skeleton-line skeleton-text short"></div>
            </div>
        </div>
    );

    // Not authenticated
    if (!authToken) {
        return (
            <div className="App">
                {renderNavBar()}
                <div className="pro-container">
                    <div className="pro-main-card">
                        <div style={{textAlign: 'center', padding: '48px 24px'}}>
                            <h2>Access Denied</h2>
                            <p>Please log in to manage teams.</p>
                            <button className="pro-validate-btn" onClick={() => navigate('/login')}>
                                Go to Login
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Hydrating user
    if (!user) {
        return (
            <div className="App">
                {renderNavBar()}
                <div className="pro-container">
                    <div className="pro-main-card">
                        {renderSkeleton()}
                    </div>
                </div>
            </div>
        );
    }

    // Loading handled within main render with skeletons

    // ============ MAIN RENDER ============
    return (
        <div className="App">
            {renderNavBar()}

            <div className="pro-container">
                <header className="pro-header-simple">
                    <h1><FiUsers /> Team Management</h1>
                    <p className="pro-header-subtitle">Collaborate with your team and share validation quotas</p>
                </header>

                <div className="pro-main-card">
                    <div className="team-management">
                        <div className="team-header">
                            {error && <div className="error-message">{error}</div>}
                            {success && <div className="success-message">{success}</div>}
                            {inTeam && (!teamQuickInfo && !teamInfo) && (
                                <div className="loading-bar" />
                            )}
                        </div>

                        {/* No Team - Show Create Option */}
                        {canCreateTeam && !inTeam && !teamInfo && (
                            <div className="no-team-section">
                                <div className="team-benefits">
                                    <h3>Create Your Team</h3>
                                    <p>As a Starter/Pro user, you can create a team and invite members to share 10 million lifetime validations.</p>
                                    <div className="benefits-list">
                                        <div className="benefit">✅ Share 10 million lifetime validations</div>
                                        <div className="benefit">✅ Invite up to 10 team members</div>
                                        <div className="benefit">✅ Centralized team management</div>
                                        <div className="benefit">✅ Shared validation history</div>
                                    </div>
                                    <button className="create-team-btn" onClick={() => setShowCreateTeam(true)}>
                                        Create Team
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Team Dashboard */}
                        {inTeam && !teamQuickInfo && !teamInfo && (
                            <div className="team-dashboard fade-in">
                                <div className="team-overview">
                                    <div className="team-info">
                                        <div className="skeleton-line skeleton-title"></div>
                                        <div className="skeleton-line skeleton-text"></div>
                                        <div className="skeleton-line skeleton-text short"></div>
                                    </div>
                                    <div className="quota-info">
                                        <h4>Team Quota Usage</h4>
                                        <div className="quota-bar">
                                            <div className="skeleton-line" style={{ height: '12px', width: '80%' }}></div>
                                        </div>
                                        <div className="quota-details">
                                            <span className="skeleton-line" style={{ height: '12px', width: '50%' }}></span>
                                            <span className="skeleton-line" style={{ height: '12px', width: '30%' }}></span>
                                        </div>
                                    </div>
                                </div>
                                <div className="team-members">
                                    <h4>Team Members</h4>
                                    <div className="members-list">
                                        <div className="member-card skeleton-card">
                                            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                                                <div className="skeleton-avatar" />
                                                <div style={{ flex: 1 }}>
                                                    <div className="skeleton-line" style={{ width: '30%' }}></div>
                                                    <div className="skeleton-line" style={{ width: '50%' }}></div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="member-card skeleton-card">
                                            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                                                <div className="skeleton-avatar" />
                                                <div style={{ flex: 1 }}>
                                                    <div className="skeleton-line" style={{ width: '40%' }}></div>
                                                    <div className="skeleton-line" style={{ width: '55%' }}></div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="member-card skeleton-card">
                                            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                                                <div className="skeleton-avatar" />
                                                <div style={{ flex: 1 }}>
                                                    <div className="skeleton-line" style={{ width: '35%' }}></div>
                                                    <div className="skeleton-line" style={{ width: '45%' }}></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                        {(teamQuickInfo || teamInfo) && (
                            <div className="team-dashboard fade-in">
                                <div className="team-overview">
                                    <div className="team-info">
                                        <h3>{teamQuickInfo?.team?.name || teamInfo?.team?.name}</h3>
                                        <p className="team-description">{teamQuickInfo?.team?.description || teamInfo?.team?.description}</p>
                                        <div className="team-stats">
                                            <div className="stat">
                                                <span className="label">Members:</span>
                                                <span className="value">{teamQuickInfo?.team?.member_count || teamInfo?.members?.length || 0}/{teamInfo?.team?.max_members || 10}</span>
                                            </div>
                                            <div className="stat">
                                                <span className="label">Your Role:</span>
                                                <span className="value role">{teamInfo?.user_role || 'member'}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="quota-info">
                                        <h4>Team Quota Usage</h4>
                                        <div className="quota-bar">
                                            <div className="quota-fill" style={{
                                                width: `${Math.min((((teamQuickInfo?.team?.monthly_validations_used || teamInfo?.team?.quota_used) || 0) / ((teamQuickInfo?.team?.monthly_validations || teamInfo?.team?.quota_limit) || 10000000)) * 100, 100)}%`
                                            }} />
                                        </div>
                                        <div className="quota-details">
                                            <span>{((teamQuickInfo?.team?.monthly_validations_used || teamInfo?.team?.quota_used) || 0).toLocaleString()} / {((teamQuickInfo?.team?.monthly_validations || teamInfo?.team?.quota_limit) || 10000000).toLocaleString()}</span>
                                            <span>{Math.round((((teamQuickInfo?.team?.monthly_validations_used || teamInfo?.team?.quota_used) || 0) / ((teamQuickInfo?.team?.monthly_validations || teamInfo?.team?.quota_limit) || 10000000)) * 100)}% used</span>
                                        </div>
                                        <p className="quota-reset">Lifetime quota (no reset)</p>
                                    </div>
                                </div>

                                {/* Team Actions */}
                                {(teamInfo?.user_role === 'owner' || teamInfo?.user_role === 'admin') && (
                                    <div className="team-actions">
                                        <button className="invite-btn" onClick={handleGenerateInvite} disabled={buttonLoading}>
                                            {buttonLoading ? 'Generating...' : '🔗 Generate Invite Link'}
                                        </button>
                                    </div>
                                )}

                                {/* Team Members */}
                                <div className="team-members">
                                    <h4>Team Members ({teamInfo?.members?.length || 0})</h4>
                                    {!loadingFullTeamInfo && teamInfo?.members ? (
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
                                                    {(teamInfo.user_role === 'owner' || teamInfo.user_role === 'admin') && member.role !== 'owner' && (
                                                        <button className="remove-btn" onClick={() => handleRemoveMember(member.user_id)} disabled={buttonLoading}>
                                                            Remove
                                                        </button>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div style={{padding: '20px', textAlign: 'center'}}>Loading members...</div>
                                    )}
                                </div>

                                {/* Pending Invitations */}
                                {teamInfo?.pending_invitations && teamInfo.pending_invitations.filter(i => !i.email.includes('@temp.com')).length > 0 && (
                                    <div className="pending-invitations">
                                        <h4>Pending Invitations ({teamInfo.pending_invitations.filter(i => !i.email.includes('@temp.com')).length})</h4>
                                        <div className="invitations-list">
                                            {teamInfo.pending_invitations.filter(i => !i.email.includes('@temp.com')).map(invite => (
                                                <div key={invite.id} className="invitation-card">
                                                    <div className="invite-email">{invite.email}</div>
                                                    <div className="invite-date">Sent {new Date(invite.created_at).toLocaleDateString()}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Leave Team */}
                                {teamInfo?.user_role !== 'owner' && (
                                    <div className="danger-zone">
                                        <h4>Danger Zone</h4>
                                        <button className="leave-team-btn" onClick={handleLeaveTeam} disabled={buttonLoading}>
                                            Leave Team
                                        </button>
                                        <p className="warning">Leaving will remove your Pro access unless you have your own subscription.</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Not Eligible (only show when user is not in a team and not eligible) */}
                        {!inTeam && ((user?.subscriptionTier || '').toLowerCase() === 'free') && !teamInfo && !teamQuickInfo && (
                            <div className="not-eligible">
                                <h3>Team Features</h3>
                                <p>Team collaboration is available for Starter and Pro users.</p>
                                <div className="upgrade-prompt">
                                    <p>Upgrade to Starter or Pro to:</p>
                                    <ul>
                                        <li>Create teams and invite members</li>
                                        <li>Share 10 million lifetime validations</li>
                                        <li>Collaborate with your team</li>
                                    </ul>
                                    <button className="upgrade-btn" onClick={() => navigate('/pricing')}>
                                        Upgrade Now
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Create Team Modal */}
            {showCreateTeam && (
                <div className="modal-overlay">
                    <div className="modal">
                        <div className="modal-header">
                            <h3>Create New Team</h3>
                            <button className="close-btn" onClick={() => setShowCreateTeam(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreateTeam}>
                            <div className="form-group">
                                <label>Team Name *</label>
                                <input type="text" value={teamName} onChange={(e) => setTeamName(e.target.value)} 
                                    placeholder="Enter team name" required />
                            </div>
                            <div className="form-group">
                                <label>Description (Optional)</label>
                                <textarea value={teamDescription} onChange={(e) => setTeamDescription(e.target.value)} 
                                    placeholder="Describe your team" rows="3" />
                            </div>
                            <div className="modal-actions">
                                <button type="button" onClick={() => setShowCreateTeam(false)}>Cancel</button>
                                <button type="submit" className="primary" disabled={buttonLoading}>
                                    {buttonLoading ? 'Creating...' : 'Create Team'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Invite Link Modal */}
            {showLinkModal && (
                <div className="modal-overlay">
                    <div className="modal">
                        <div className="modal-header">
                            <h3>🔗 Team Invite Link</h3>
                            <button className="close-btn" onClick={() => setShowLinkModal(false)}>×</button>
                        </div>
                        <div style={{padding: '24px'}}>
                            <p><strong>Your team invite link is ready!</strong></p>
                            <div className="link-container" style={{
                                background: '#f8f9fa', border: '1px solid #dee2e6', borderRadius: '6px',
                                padding: '12px', marginBottom: '16px', wordBreak: 'break-all', fontFamily: 'monospace'
                            }}>
                                {generatedInviteLink}
                            </div>
                            <div style={{display: 'flex', gap: '12px', marginBottom: '16px'}}>
                                <button onClick={() => {
                                    navigator.clipboard.writeText(generatedInviteLink);
                                    setSuccess('Copied!');
                                }}>📋 Copy Link</button>
                                <button onClick={() => {
                                    const text = `Join our team! ${generatedInviteLink}`;
                                    if (navigator.share) {
                                        navigator.share({title: 'Team Invite', text});
                                    }
                                }}>📤 Share</button>
                            </div>
                            <p style={{fontSize: '14px', color: '#666'}}>Link expires in 7 days</p>
                            <button onClick={() => setShowLinkModal(false)} className="primary">Done</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TeamManagement;

import React, { useState, useEffect } from 'react';
import './TeamManagement.css';

const TeamManagement = () => {
    const [user, setUser] = useState(null);
    const [teamInfo, setTeamInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    
    // Team creation
    const [showCreateTeam, setShowCreateTeam] = useState(false);
    const [teamName, setTeamName] = useState('');
    const [teamDescription, setTeamDescription] = useState('');
    
    // Team invitation
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteMessage, setInviteMessage] = useState('');
    const [generatedInviteLink, setGeneratedInviteLink] = useState('');
    const [showLinkModal, setShowLinkModal] = useState(false);
    
    // Team eligibility
    const [canCreateTeam, setCanCreateTeam] = useState(false);

    useEffect(() => {
        // Initial load
        checkUserStatus();
        
        // Set up auto-refresh every 30 seconds (reduced from 10 for better performance)
        const interval = setInterval(() => {
            if (teamInfo && !loading) {
                checkUserStatus();
            }
        }, 30000); // Refresh every 30 seconds
        
        // Refresh when page becomes visible (user comes back from invitation)
        const handleVisibilityChange = () => {
            if (!document.hidden) {
                checkUserStatus();
            }
        };
        
        document.addEventListener('visibilitychange', handleVisibilityChange);
        
        // Cleanup interval and event listener on unmount
        return () => {
            clearInterval(interval);
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, []); // Empty dependency array - only run once on mount

    const getAuthHeaders = () => {
        const token = localStorage.getItem('authToken');
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    };

    const checkUserStatus = async () => {
        try {
            setLoading(true);
            setError(''); // Clear previous errors
            
            // Single optimized API call to get all team status
            const response = await fetch('/api/team/status', {
                headers: getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                setCanCreateTeam(data.can_create_team);
                
                // Set team info if user is in a team
                if (data.team_info && data.team_info.success) {
                    setTeamInfo(data.team_info);
                } else {
                    setTeamInfo(null);
                }
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Failed to load team information');
            }
        } catch (err) {
            setError('Network error. Please check your connection.');
            console.error('Team status error:', err);
        } finally {
            setLoading(false);
        }
    };

    const createTeam = async (e) => {
        e.preventDefault();
        
        if (!teamName.trim()) {
            setError('Team name is required');
            return;
        }

        try {
            setLoading(true);
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
            setLoading(false);
        }
    };

    const generateInviteLink = async () => {
        try {
            setLoading(true);
            setError('');
            
            // Generate a unique email to avoid "already invited" errors
            const randomId = Math.random().toString(36).substring(7);
            const genericEmail = `invite-${randomId}@temp.com`;
            
            const response = await fetch('/api/team/invite', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    email: genericEmail, // Use random email to avoid conflicts
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
                
                checkUserStatus(); // Refresh team info
            } else {
                setError(data.error || 'Failed to generate invite link');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const removeMember = async (memberId) => {
        if (!window.confirm('Are you sure you want to remove this member?')) {
            return;
        }

        try {
            setLoading(true);
            const response = await fetch(`/api/team/members/${memberId}/remove`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess('Member removed successfully');
                checkUserStatus(); // Refresh team info
            } else {
                setError(data.error || 'Failed to remove member');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const leaveTeam = async () => {
        if (!window.confirm('Are you sure you want to leave this team? You will lose Pro access.')) {
            return;
        }

        try {
            setLoading(true);
            const response = await fetch('/api/team/leave', {
                method: 'POST',
                headers: getAuthHeaders()
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess('Successfully left the team');
                checkUserStatus(); // Refresh status
            } else {
                setError(data.error || 'Failed to leave team');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (loading && !teamInfo && !canCreateTeam) {
        return (
            <div className="team-management">
                <div className="team-header">
                    <h2>Team Management</h2>
                </div>
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
        );
    }

    return (
        <div className="team-management">
            <div className="team-header">
                <h2>Team Management</h2>
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
                                <button type="submit" className="primary">
                                    Create Team
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
                                    style={{ width: `${teamInfo.team.usage_percentage}%` }}
                                />
                            </div>
                            <div className="quota-details">
                                <span>{teamInfo.team.quota_used.toLocaleString()} / {teamInfo.team.quota_limit.toLocaleString()} validations</span>
                                <span>{teamInfo.team.usage_percentage}% used</span>
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
                                disabled={loading}
                            >
                                {loading ? 'Generating...' : '🔗 Generate Invite Link'}
                            </button>
                            
                            <button 
                                className="refresh-btn"
                                onClick={() => checkUserStatus()}
                                disabled={loading}
                                style={{
                                    marginLeft: '12px',
                                    background: '#6c757d',
                                    color: 'white',
                                    border: 'none',
                                    padding: '10px 20px',
                                    borderRadius: '6px',
                                    cursor: 'pointer'
                                }}
                            >
                                🔄 Refresh
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

                    {/* Pending Invitations */}
                    {teamInfo.pending_invitations && teamInfo.pending_invitations.length > 0 && (
                        <div className="pending-invitations">
                            <h4>Pending Invitations ({teamInfo.pending_invitations.length})</h4>
                            <div className="invitations-list">
                                {teamInfo.pending_invitations.map(invite => (
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
                                        const subject = encodeURIComponent('Join our team!');
                                        const body = encodeURIComponent(`You're invited to join our team!\n\nClick this link to accept: ${generatedInviteLink}`);
                                        window.open(`mailto:?subject=${subject}&body=${body}`);
                                    }}
                                >
                                    📧 Open Email
                                </button>
                            </div>
                            
                            <div style={{ fontSize: '14px', color: '#666' }}>
                                <p><strong>How it works:</strong></p>
                                <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                                    <li>Send this link to the person you want to invite</li>
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
    );
};

export default TeamManagement;
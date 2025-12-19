import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './TeamInvite.css';

const TeamInvite = () => {
    const { token } = useParams();
    const navigate = useNavigate();
    const [invitation, setInvitation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [accepting, setAccepting] = useState(false);
    const [user, setUser] = useState(null);

    useEffect(() => {
        checkAuthAndLoadInvitation();
    }, [token]);

    const checkAuthAndLoadInvitation = async () => {
        try {
            setLoading(true);
            
            // Check if user is logged in
            const authToken = localStorage.getItem('authToken');
            if (authToken) {
                // Get user info
                const userResponse = await fetch('/api/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                });
                
                if (userResponse.ok) {
                    const userData = await userResponse.json();
                    setUser(userData);
                }
            }
            
            // Load invitation details
            const inviteResponse = await fetch(`/api/team/invite/${token}`);
            const inviteData = await inviteResponse.json();
            
            if (inviteResponse.ok) {
                setInvitation(inviteData.invitation);
            } else {
                setError(inviteData.error || 'Invalid invitation');
            }
        } catch (err) {
            setError('Failed to load invitation');
        } finally {
            setLoading(false);
        }
    };

    const acceptInvitation = async () => {
        const authToken = localStorage.getItem('authToken');
        
        if (!authToken) {
            // Redirect to login with return URL
            localStorage.setItem('returnUrl', `/invite/${token}`);
            navigate('/login');
            return;
        }

        try {
            setAccepting(true);
            
            const response = await fetch(`/api/team/invite/${token}/accept`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.ok) {
                // Success! Redirect to team page
                navigate('/team', { 
                    state: { 
                        message: 'Successfully joined the team!' 
                    }
                });
            } else {
                setError(data.error || 'Failed to accept invitation');
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setAccepting(false);
        }
    };

    if (loading) {
        return (
            <div className="team-invite-container">
                <div className="invite-card">
                    <div className="loading">Loading invitation...</div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="team-invite-container">
                <div className="invite-card error-card">
                    <div className="error-icon">❌</div>
                    <h2>Invitation Error</h2>
                    <p>{error}</p>
                    <button 
                        className="btn-primary"
                        onClick={() => navigate('/')}
                    >
                        Go to Home
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="team-invite-container">
            <div className="invite-card">
                <div className="invite-header">
                    <div className="team-icon">👥</div>
                    <h1>Team Invitation</h1>
                </div>

                <div className="invite-details">
                    <h2>You're invited to join</h2>
                    <div className="team-name">{invitation.team_name}</div>
                    
                    {invitation.team_description && (
                        <p className="team-description">{invitation.team_description}</p>
                    )}
                    
                    <div className="inviter-info">
                        <p>
                            <strong>{invitation.invited_by}</strong> 
                            <span className="inviter-email"> ({invitation.inviter_email})</span>
                            <span> invited you to join their team</span>
                        </p>
                    </div>

                    {invitation.message && (
                        <div className="personal-message">
                            <h4>Personal Message:</h4>
                            <p>"{invitation.message}"</p>
                        </div>
                    )}
                </div>

                <div className="team-benefits">
                    <h3>What you'll get:</h3>
                    <ul>
                        <li>✅ Pro tier access with shared 10,000 monthly validations</li>
                        <li>✅ Advanced email validation features</li>
                        <li>✅ Team collaboration and shared results</li>
                        <li>✅ Access to team dashboard and analytics</li>
                    </ul>
                </div>

                <div className="invite-actions">
                    {user ? (
                        <>
                            <button 
                                className="btn-primary accept-btn"
                                onClick={acceptInvitation}
                                disabled={accepting}
                            >
                                {accepting ? 'Joining...' : 'Accept Invitation'}
                            </button>
                            <button 
                                className="btn-secondary"
                                onClick={() => navigate('/')}
                            >
                                Decline
                            </button>
                        </>
                    ) : (
                        <>
                            <p className="login-prompt">
                                You need to be logged in to accept this invitation.
                            </p>
                            <button 
                                className="btn-primary"
                                onClick={() => {
                                    localStorage.setItem('returnUrl', `/invite/${token}`);
                                    navigate('/login');
                                }}
                            >
                                Login to Accept
                            </button>
                            <button 
                                className="btn-secondary"
                                onClick={() => {
                                    localStorage.setItem('returnUrl', `/invite/${token}`);
                                    navigate('/signup');
                                }}
                            >
                                Sign Up to Accept
                            </button>
                        </>
                    )}
                </div>

                <div className="invite-footer">
                    <p className="expires-info">
                        This invitation expires on {new Date(invitation.expires_at).toLocaleDateString()}
                    </p>
                </div>
            </div>
        </div>
    );
};

export default TeamInvite;
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FiUsers, FiActivity, FiMail, FiShield, FiLogOut, FiRefreshCw,
  FiTrendingUp, FiCheckCircle, FiClock, FiBarChart2, FiSettings, FiSearch
} from 'react-icons/fi';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [adminUser, setAdminUser] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [userFilters, setUserFilters] = useState({
    search: '',
    tier: '',
    status: '',
    page: 1
  });

  useEffect(() => {
    // Check admin authentication
    const token = localStorage.getItem('adminToken');
    const user = localStorage.getItem('adminUser');
    
    if (!token || !user) {
      navigate('/admin/login');
      return;
    }
    
    setAdminUser(JSON.parse(user));
    loadDashboardData();
  }, [navigate]);

  const apiCall = async (endpoint, options = {}) => {
    const token = localStorage.getItem('adminToken');
    const response = await fetch(`/admin${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (response.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('adminToken');
      localStorage.removeItem('adminUser');
      navigate('/admin/login');
      return null;
    }

    return response.json();
  };

  const loadDashboardData = async () => {
    try {
      const data = await apiCall('/dashboard');
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const params = new URLSearchParams({
        page: userFilters.page,
        limit: 20,
        ...(userFilters.search && { search: userFilters.search }),
        ...(userFilters.tier && { tier: userFilters.tier }),
        ...(userFilters.status && { status: userFilters.status })
      });
      
      const data = await apiCall(`/users?${params}`);
      setUsers(data);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
    }
  }, [activeTab, userFilters]);

  const handleLogout = async () => {
    try {
      await apiCall('/auth/logout', { method: 'POST' });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('adminToken');
      localStorage.removeItem('adminUser');
      navigate('/admin/login');
    }
  };

  const suspendUser = async (userId, reason) => {
    try {
      await apiCall(`/users/${userId}/suspend`, {
        method: 'POST',
        body: JSON.stringify({ reason })
      });
      loadUsers(); // Refresh user list
    } catch (error) {
      console.error('Failed to suspend user:', error);
    }
  };

  const unsuspendUser = async (userId) => {
    try {
      await apiCall(`/users/${userId}/unsuspend`, { method: 'POST' });
      loadUsers(); // Refresh user list
    } catch (error) {
      console.error('Failed to unsuspend user:', error);
    }
  };

  if (loading) {
    return (
      <div className="admin-loading">
        <div className="admin-spinner-large"></div>
        <p>Loading Admin Dashboard...</p>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      {/* Admin Header */}
      <header className="admin-header">
        <div className="admin-header-left">
          <div className="admin-logo">
            <FiShield className="admin-logo-icon" />
            <span>Admin Panel</span>
          </div>
        </div>
        
        <div className="admin-header-right">
          <div className="admin-user-info">
            <span>Welcome, {adminUser?.first_name}</span>
            <span className="admin-role">{adminUser?.role}</span>
          </div>
          <button 
            className="admin-nav-btn"
            onClick={() => window.open('/', '_blank')}
            style={{ marginRight: '10px' }}
          >
            <FiMail /> Email Validator
          </button>
          <button className="admin-logout-btn" onClick={handleLogout}>
            <FiLogOut /> Logout
          </button>
        </div>
      </header>

      {/* Admin Navigation */}
      <nav className="admin-nav">
        <button 
          className={`admin-nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <FiBarChart2 /> Dashboard
        </button>
        <button 
          className={`admin-nav-btn ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          <FiUsers /> Users
        </button>
        <button 
          className={`admin-nav-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          <FiActivity /> Analytics
        </button>
        <button 
          className={`admin-nav-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          <FiSettings /> Settings
        </button>
      </nav>

      {/* Main Content */}
      <main className="admin-main">
        {activeTab === 'dashboard' && (
          <div className="admin-dashboard-content">
            <div className="admin-page-header">
              <h1>System Overview</h1>
              <button className="admin-refresh-btn" onClick={loadDashboardData}>
                <FiRefreshCw /> Refresh
              </button>
            </div>

            {/* Stats Cards */}
            <div className="admin-stats-grid">
              <div className="admin-stat-card">
                <div className="admin-stat-icon users">
                  <FiUsers />
                </div>
                <div className="admin-stat-content">
                  <h3>Total Users</h3>
                  <p className="admin-stat-number">{dashboardData?.stats?.total_users || 0}</p>
                  <span className="admin-stat-change positive">
                    <FiTrendingUp /> +{dashboardData?.stats?.users_today || 0} today
                  </span>
                </div>
              </div>

              <div className="admin-stat-card">
                <div className="admin-stat-icon validations">
                  <FiMail />
                </div>
                <div className="admin-stat-content">
                  <h3>Validations</h3>
                  <p className="admin-stat-number">{dashboardData?.stats?.total_validations || 0}</p>
                  <span className="admin-stat-change positive">
                    <FiTrendingUp /> +{dashboardData?.stats?.validations_today || 0} today
                  </span>
                </div>
              </div>

              <div className="admin-stat-card">
                <div className="admin-stat-icon success">
                  <FiCheckCircle />
                </div>
                <div className="admin-stat-content">
                  <h3>Success Rate</h3>
                  <p className="admin-stat-number">
                    {dashboardData?.stats?.total_validations > 0 
                      ? Math.round((dashboardData.stats.valid_emails / dashboardData.stats.total_validations) * 100)
                      : 0}%
                  </p>
                  <span className="admin-stat-change neutral">
                    <FiActivity /> {dashboardData?.stats?.valid_emails || 0} valid
                  </span>
                </div>
              </div>

              <div className="admin-stat-card">
                <div className="admin-stat-icon activity">
                  <FiActivity />
                </div>
                <div className="admin-stat-content">
                  <h3>Active Admins</h3>
                  <p className="admin-stat-number">{dashboardData?.stats?.active_admins || 0}</p>
                  <span className="admin-stat-change neutral">
                    <FiClock /> Online now
                  </span>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="admin-section">
              <h2>Recent Activity</h2>
              <div className="admin-activity-list">
                {dashboardData?.recent_activity?.map((activity, index) => (
                  <div key={index} className="admin-activity-item">
                    <div className="admin-activity-icon">
                      <FiActivity />
                    </div>
                    <div className="admin-activity-content">
                      <p><strong>{activity.admin_name || 'System'}</strong> {activity.action.replace('_', ' ')}</p>
                      <span className="admin-activity-time">
                        {new Date(activity.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="admin-users-content">
            <div className="admin-page-header">
              <h1>User Management</h1>
              <div className="admin-user-filters">
                <div className="admin-search-box">
                  <FiSearch />
                  <input
                    type="text"
                    placeholder="Search users..."
                    value={userFilters.search}
                    onChange={(e) => setUserFilters({...userFilters, search: e.target.value, page: 1})}
                  />
                </div>
                <select
                  value={userFilters.tier}
                  onChange={(e) => setUserFilters({...userFilters, tier: e.target.value, page: 1})}
                >
                  <option value="">All Tiers</option>
                  <option value="free">Free</option>
                  <option value="pro">Pro</option>
                  <option value="enterprise">Enterprise</option>
                </select>
                <select
                  value={userFilters.status}
                  onChange={(e) => setUserFilters({...userFilters, status: e.target.value, page: 1})}
                >
                  <option value="">All Status</option>
                  <option value="active">Active</option>
                  <option value="suspended">Suspended</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>

            {/* Users Table */}
            <div className="admin-users-table">
              <table>
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Tier</th>
                    <th>Usage</th>
                    <th>Status</th>
                    <th>Joined</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users?.users?.map((user) => (
                    <tr key={user.id}>
                      <td>
                        <div className="admin-user-info">
                          <strong>{user.first_name} {user.last_name}</strong>
                          <span>{user.email}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`admin-tier-badge ${user.subscription_tier}`}>
                          {user.subscription_tier}
                        </span>
                      </td>
                      <td>
                        <div className="admin-usage-info">
                          <span>{user.api_calls_count}/{user.api_calls_limit}</span>
                          <div className="admin-usage-bar">
                            <div 
                              className="admin-usage-fill"
                              style={{
                                width: `${Math.min((user.api_calls_count / user.api_calls_limit) * 100, 100)}%`
                              }}
                            />
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className={`admin-status-badge ${
                          user.is_suspended ? 'suspended' : 
                          user.is_active ? 'active' : 'inactive'
                        }`}>
                          {user.is_suspended ? 'Suspended' : 
                           user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>{new Date(user.created_at).toLocaleDateString()}</td>
                      <td>
                        <div className="admin-user-actions">
                          {user.is_suspended ? (
                            <button 
                              className="admin-action-btn unsuspend"
                              onClick={() => unsuspendUser(user.id)}
                            >
                              Unsuspend
                            </button>
                          ) : (
                            <button 
                              className="admin-action-btn suspend"
                              onClick={() => {
                                const reason = prompt('Suspension reason:');
                                if (reason) suspendUser(user.id, reason);
                              }}
                            >
                              Suspend
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {users?.pagination && (
              <div className="admin-pagination">
                <button 
                  disabled={userFilters.page <= 1}
                  onClick={() => setUserFilters({...userFilters, page: userFilters.page - 1})}
                >
                  Previous
                </button>
                <span>Page {userFilters.page} of {users.pagination.pages}</span>
                <button 
                  disabled={userFilters.page >= users.pagination.pages}
                  onClick={() => setUserFilters({...userFilters, page: userFilters.page + 1})}
                >
                  Next
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="admin-analytics-content">
            <h1>Analytics & Reports</h1>
            <p>Advanced analytics coming soon...</p>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="admin-settings-content">
            <h1>System Settings</h1>
            <p>System configuration coming soon...</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminDashboard;
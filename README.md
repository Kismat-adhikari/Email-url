# Email Validator Platform

A professional email validation platform with real-time validation, user management, admin dashboard, and team collaboration features.

## 🚀 Quick Start

### Easiest Way (Windows)
```bash
# Just double-click this file:
start_app.bat
```

### Manual Start (Any OS)
```bash
# Terminal 1 - Backend
python app_anon_history.py

# Terminal 2 - Frontend  
cd frontend
npm start

# Open browser
http://localhost:3000
```

## 🛠️ Setup (First Time Only)

### Prerequisites
- Python 3.8+
- Node.js 14+
- Supabase account (free tier works)

### Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
cd frontend
npm install
```

### Configuration
Create `.env` file in root directory:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
JWT_SECRET=your_jwt_secret_key
ADMIN_JWT_SECRET=your_admin_jwt_secret
```

## ✨ Features

### Core Validation
- **Advanced Email Validation** - Syntax, DNS, MX records, deliverability scoring
- **SMTP Verification** - Real-time SMTP checks
- **Risk Assessment** - Spam trap detection, disposable email detection
- **Batch Processing** - Validate multiple emails with real-time streaming
- **Pattern Analysis** - Advanced email pattern recognition

### User Management
- **Free Tier** - 10 validations per user
- **Authentication System** - JWT-based secure login
- **Real-time Monitoring** - 2-second status checks
- **API Usage Tracking** - Real-time usage counters

### Admin Dashboard
- **Real-time Statistics** - Live user counts, validation metrics
- **User Management** - View, suspend, unsuspend users
- **Activity Logging** - Complete audit trail
- **Instant Suspension** - Real-time account suspension with immediate enforcement

### Team Features
- **Team Creation** - Create and manage teams
- **Member Invitations** - Invite team members via email
- **Shared Quotas** - Team-based validation limits
- **Collaboration** - Shared validation history

## 🏗️ Tech Stack

### Backend
- **Python Flask** - Main API server (`app_anon_history.py`)
- **Supabase** - Database and authentication
- **JWT** - Secure token-based authentication
- **Real-time APIs** - WebSocket-like streaming for batch validation

### Frontend
- **React** - Modern UI framework
- **Professional Design** - Glassmorphic dark/light themes
- **Real-time Updates** - Live status monitoring
- **Responsive Design** - Mobile-friendly interface

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `GET /api/auth/check-status` - Real-time status check

### Validation
- `POST /api/validate` - Single email validation (authenticated)
- `POST /api/validate/local` - Anonymous validation (2 limit)
- `POST /api/validate/batch/stream` - Batch validation with streaming

### Admin
- `POST /admin/auth/login` - Admin login
- `GET /admin/dashboard` - Dashboard statistics
- `GET /admin/users` - User management
- `POST /admin/users/{id}/suspend` - Suspend user
- `POST /admin/users/{id}/unsuspend` - Unsuspend user

### Teams
- `GET /api/team/status` - Get team status
- `POST /api/team/create` - Create new team
- `POST /api/team/invite` - Invite team member

## 📊 Admin Access

### Default Admin Credentials
- **Email**: `admin@emailvalidator.com`
- **Password**: `admin123`
- **⚠️ Change immediately after first login**

## 🚀 Deployment

### Render Deployment
1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy automatically with `render.yaml` configuration

### Database Setup
Run the SQL schema in your Supabase dashboard:
```sql
-- Use complete_fresh_schema.sql for full setup
-- Or supabase_schema.sql for basic setup
```

## 📁 Project Structure

```
Email-url/
├── app_anon_history.py          # Main Flask backend
├── requirements.txt             # Python dependencies
├── .env                         # Configuration (create this)
├── start_app.bat               # Windows quick start
├── render.yaml                 # Production deployment config
│
├── frontend/                   # React application
│   ├── package.json
│   ├── src/
│   │   ├── App.js             # Main component
│   │   ├── index.css          # Design system
│   │   └── ... (components)
│   └── public/
│
├── Support modules (imported by backend)
│   ├── admin_simple.py        # Admin dashboard
│   ├── team_api.py           # Team endpoints
│   ├── emailvalidator_unified.py # Core validation
│   └── ... (15+ more modules)
│
└── SQL schema files
    ├── complete_fresh_schema.sql
    ├── supabase_schema.sql
    └── ... (other schemas)
```

## 🔒 Security Features

- **JWT Tokens** - Secure authentication
- **Real-time Monitoring** - Instant suspension detection
- **Rate Limiting** - API abuse protection
- **Input Validation** - SQL injection prevention
- **Admin Authentication** - Separate admin security layer

## 🎯 Production Ready

- ✅ **Security** - JWT authentication, rate limiting, input validation
- ✅ **Scalability** - Efficient database queries, streaming APIs
- ✅ **Monitoring** - Real-time statistics, activity logging
- ✅ **User Experience** - Professional UI, instant feedback
- ✅ **Admin Control** - Complete user management system

---

**Built with ❤️ for professional email validation**
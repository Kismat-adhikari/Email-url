# Email Validator Platform

A professional email validation platform with real-time suspension system, admin dashboard, and comprehensive validation features.

## 🚀 Features

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

### Security Features
- **Real-time Suspension Detection** - Users logged out within 2 seconds
- **Enhanced Login Protection** - Detailed suspension error messages
- **Admin Authentication** - Secure admin panel access
- **Rate Limiting** - API protection against abuse

## 🛠️ Tech Stack

### Backend
- **Python Flask** - Main API server
- **Supabase** - Database and authentication
- **JWT** - Secure token-based authentication
- **Real-time APIs** - WebSocket-like streaming for batch validation

### Frontend
- **React** - Modern UI framework
- **Professional Design** - Glassmorphic dark/light themes
- **Real-time Updates** - Live status monitoring
- **Responsive Design** - Mobile-friendly interface

## 🚀 Deployment

### Environment Variables
```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# JWT Secret
JWT_SECRET=your_jwt_secret_key

# Admin JWT Secret  
ADMIN_JWT_SECRET=your_admin_jwt_secret

# Optional: SendGrid for email sending
SENDGRID_API_KEY=your_sendgrid_key
```

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

## 📊 Admin Access

### Default Admin Credentials
- **Email**: `admin@emailvalidator.com`
- **Password**: `admin123`
- **⚠️ Change immediately after first login**

### Admin Features
- Real-time user statistics
- User suspension/unsuspension
- Activity monitoring
- System health dashboard

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

## 🎯 Key Features

### Real-time Suspension System
- **Instant Detection** - 2-second status checks
- **Immediate Enforcement** - API calls blocked instantly
- **Professional UI** - Modal-based suspension interface
- **Activity Logging** - Complete audit trail

### Free Tier Management
- **10 API Calls** - Per registered user
- **2 Anonymous Validations** - For non-registered users
- **Usage Tracking** - Real-time counters
- **Upgrade Prompts** - Clear upgrade paths

### Professional UI
- **Dark/Light Themes** - Glassmorphic design
- **Real-time Updates** - Live data everywhere
- **Mobile Responsive** - Works on all devices
- **Professional Admin Panel** - Complete management interface

## 📈 Production Ready

- ✅ **Security** - JWT authentication, rate limiting, input validation
- ✅ **Scalability** - Efficient database queries, streaming APIs
- ✅ **Monitoring** - Real-time statistics, activity logging
- ✅ **User Experience** - Professional UI, instant feedback
- ✅ **Admin Control** - Complete user management system

## 🔒 Security

- **JWT Tokens** - Secure authentication
- **Real-time Monitoring** - Instant suspension detection
- **Rate Limiting** - API abuse protection
- **Input Validation** - SQL injection prevention
- **Admin Authentication** - Separate admin security layer

---

**Built with ❤️ for professional email validation**
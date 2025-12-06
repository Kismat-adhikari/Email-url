# 🏗️ System Architecture

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│                     http://localhost:3000                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP Requests
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      REACT FRONTEND                             │
│  ┌──────────────┬──────────────┬──────────────┐                │
│  │  🔍 Validate │  📜 History  │ 📊 Analytics │                │
│  │              │              │              │                │
│  │ • Single     │ • View all   │ • Statistics │                │
│  │ • Batch      │ • Timestamps │ • Charts     │                │
│  │ • Risk       │ • Risk       │ • Insights   │                │
│  │ • Enrichment │ • Tags       │ • Trends     │                │
│  └──────────────┴──────────────┴──────────────┘                │
│                                                                  │
│  Components: App.js, App.css                                    │
│  State: React Hooks (useState, useEffect)                       │
│  HTTP Client: Axios                                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ API Calls
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK BACKEND API                            │
│                  http://localhost:5000                          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              app_dashboard.py (Main API)                │   │
│  │                                                          │   │
│  │  Endpoints:                                             │   │
│  │  • POST /api/supabase/validate                         │   │
│  │  • GET  /api/supabase/history                          │   │
│  │  • GET  /api/supabase/analytics                        │   │
│  │  • POST /api/validate/batch                            │   │
│  │  • POST /api/webhook/send                              │   │
│  │  • POST /api/feedback/bounce                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
        ┌──────────────┐ ┌──────────┐ ┌──────────────┐
        │  Validation  │ │   Risk   │ │  Enrichment  │
        │    Engine    │ │  Scoring │ │    Engine    │
        └──────────────┘ └──────────┘ └──────────────┘
                    │           │           │
                    └───────────┼───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   SUPABASE DATABASE   │
                    │                       │
                    │  Tables:              │
                    │  • email_validations  │
                    │  • risk_scores        │
                    │  • enrichment_data    │
                    │  • bounce_history     │
                    └───────────────────────┘
```

---

## Component Breakdown

### 1. Frontend Layer (React)

```
┌─────────────────────────────────────────┐
│           React Application             │
├─────────────────────────────────────────┤
│                                         │
│  State Management:                      │
│  ├─ email                              │
│  ├─ mode (basic/advanced)              │
│  ├─ result                             │
│  ├─ activeTab (validate/history/...)   │
│  ├─ validationHistory []               │
│  ├─ analytics {}                       │
│  └─ darkMode                           │
│                                         │
│  Components:                            │
│  ├─ Header (with dark mode toggle)     │
│  ├─ TabSelector                        │
│  ├─ ValidateTab                        │
│  │   ├─ SingleEmailInput              │
│  │   ├─ BatchEmailInput               │
│  │   ├─ ResultDisplay                 │
│  │   │   ├─ ConfidenceScore           │
│  │   │   ├─ RiskAssessment            │
│  │   │   ├─ EnrichmentData            │
│  │   │   └─ ValidationChecks          │
│  │   └─ BatchResults                  │
│  ├─ HistoryTab                         │
│  │   ├─ HistoryList                   │
│  │   └─ HistoryItem                   │
│  ├─ AnalyticsTab                       │
│  │   ├─ SummaryCards                  │
│  │   ├─ RiskDistribution              │
│  │   ├─ DomainTypes                   │
│  │   └─ TopDomains                    │
│  └─ Footer                             │
│                                         │
└─────────────────────────────────────────┘
```

### 2. Backend Layer (Flask)

```
┌─────────────────────────────────────────┐
│         Flask Application               │
├─────────────────────────────────────────┤
│                                         │
│  app_dashboard.py                       │
│  ├─ /api/supabase/validate             │
│  │   └─ Calls: validate + enrich +     │
│  │             risk_score + save       │
│  │                                      │
│  ├─ /api/supabase/history              │
│  │   └─ Calls: get_validations()       │
│  │                                      │
│  ├─ /api/supabase/analytics            │
│  │   └─ Calls: get_analytics()         │
│  │                                      │
│  ├─ /api/validate/batch                │
│  │   └─ Calls: validate_batch()        │
│  │                                      │
│  └─ /api/webhook/send                  │
│      └─ Calls: send_webhook()          │
│                                         │
└─────────────────────────────────────────┘
```

### 3. Core Modules

```
┌─────────────────────────────────────────┐
│      emailvalidator_unified.py          │
│  ├─ validate_email()                    │
│  ├─ check_syntax()                      │
│  ├─ check_dns()                         │
│  ├─ check_mx_records()                  │
│  ├─ check_disposable()                  │
│  └─ suggest_correction()                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│      email_validator_smtp.py            │
│  ├─ verify_smtp()                       │
│  ├─ check_mailbox()                     │
│  ├─ detect_catch_all()                  │
│  └─ calculate_confidence()              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         risk_scoring.py                 │
│  ├─ calculate_risk_score()              │
│  ├─ check_bounce_history()              │
│  ├─ check_spam_traps()                  │
│  ├─ check_blacklist()                   │
│  └─ determine_risk_level()              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│       email_enrichment.py               │
│  ├─ enrich_email()                      │
│  ├─ classify_domain()                   │
│  ├─ infer_country()                     │
│  ├─ predict_engagement()                │
│  └─ get_company_info()                  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│       supabase_storage.py               │
│  ├─ save_validation()                   │
│  ├─ get_validations()                   │
│  ├─ get_analytics()                     │
│  ├─ update_risk_score()                 │
│  └─ query_by_email()                    │
└─────────────────────────────────────────┘
```

---

## Data Flow

### Validation Flow

```
User Input
    │
    ▼
[React: Validate Tab]
    │
    │ POST /api/supabase/validate
    │ { email: "test@example.com" }
    ▼
[Flask: app_dashboard.py]
    │
    ├─► [emailvalidator_unified.py]
    │   └─► Syntax, DNS, MX checks
    │       └─► Returns: valid, checks, confidence
    │
    ├─► [email_validator_smtp.py]
    │   └─► SMTP verification
    │       └─► Returns: smtp_valid, catch_all
    │
    ├─► [risk_scoring.py]
    │   └─► Calculate risk
    │       └─► Returns: risk_score, risk_level, factors
    │
    ├─► [email_enrichment.py]
    │   └─► Enrich data
    │       └─► Returns: domain_type, country, engagement
    │
    └─► [supabase_storage.py]
        └─► Save to database
            └─► Returns: validation_id
    │
    ▼
[Response JSON]
{
  "valid": true,
  "email": "test@example.com",
  "confidence_score": 95,
  "risk_score": 15,
  "risk_level": "low",
  "enrichment": {
    "domain_type": "corporate",
    "country": "United States",
    "engagement_score": 85
  },
  "checks": {...}
}
    │
    ▼
[React: Display Results]
    └─► Show confidence, risk, enrichment
```

### History Flow

```
User Clicks History Tab
    │
    ▼
[React: useEffect Hook]
    │
    │ GET /api/supabase/history?limit=50
    ▼
[Flask: app_dashboard.py]
    │
    ▼
[supabase_storage.py]
    │
    │ SELECT * FROM email_validations
    │ ORDER BY validated_at DESC
    │ LIMIT 50
    ▼
[Supabase Database]
    │
    ▼
[Response JSON]
{
  "validations": [
    {
      "email": "test@example.com",
      "valid": true,
      "confidence_score": 95,
      "risk_level": "low",
      "validated_at": "2024-12-05T14:30:00",
      "enrichment": {...}
    },
    ...
  ]
}
    │
    ▼
[React: Display History List]
    └─► Show all validations with details
```

### Analytics Flow

```
User Clicks Analytics Tab
    │
    ▼
[React: useEffect Hook]
    │
    │ GET /api/supabase/analytics
    ▼
[Flask: app_dashboard.py]
    │
    ▼
[supabase_storage.py]
    │
    ├─► COUNT total validations
    ├─► COUNT valid emails
    ├─► COUNT invalid emails
    ├─► GROUP BY risk_level
    ├─► GROUP BY domain_type
    └─► TOP domains by count
    │
    ▼
[Supabase Database]
    │
    ▼
[Response JSON]
{
  "total_validations": 1234,
  "valid_count": 987,
  "invalid_count": 247,
  "risk_distribution": {
    "low": 650,
    "medium": 400,
    "high": 150,
    "critical": 34
  },
  "domain_types": {
    "corporate": 750,
    "free": 350,
    "education": 134
  },
  "top_domains": [...]
}
    │
    ▼
[React: Display Charts & Stats]
    └─► Show analytics dashboard
```

---

## Database Schema

```sql
-- Supabase Tables

CREATE TABLE email_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    valid BOOLEAN NOT NULL,
    confidence_score INTEGER,
    risk_score INTEGER,
    risk_level VARCHAR(20),
    checks JSONB,
    enrichment JSONB,
    validated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_email ON email_validations(email);
CREATE INDEX idx_validated_at ON email_validations(validated_at DESC);
CREATE INDEX idx_risk_level ON email_validations(risk_level);

-- Example Row:
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "john@company.com",
    "valid": true,
    "confidence_score": 95,
    "risk_score": 15,
    "risk_level": "low",
    "checks": {
        "syntax": true,
        "dns_valid": true,
        "mx_records": true,
        "is_disposable": false,
        "is_role_based": false
    },
    "enrichment": {
        "domain_type": "corporate",
        "country": "United States",
        "engagement_score": 85,
        "company_name": "Company Inc"
    },
    "validated_at": "2024-12-05T14:30:00Z"
}
```

---

## Technology Stack

### Frontend
```
React 18.3.1
├─ React Hooks (useState, useEffect)
├─ Axios 1.13.2 (HTTP client)
├─ CSS3 (Custom styling)
└─ LocalStorage (Dark mode preference)
```

### Backend
```
Python 3.8+
├─ Flask 2.3.0 (Web framework)
├─ Flask-CORS (Cross-origin requests)
├─ Supabase-py (Database client)
├─ dnspython (DNS queries)
├─ email-validator (Syntax validation)
└─ requests (HTTP requests)
```

### Database
```
Supabase (PostgreSQL)
├─ Real-time subscriptions
├─ Row-level security
├─ RESTful API
└─ Built-in authentication
```

---

## Request/Response Examples

### 1. Validate Email

**Request:**
```http
POST /api/supabase/validate HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "email": "john@company.com",
  "advanced": true
}
```

**Response:**
```json
{
  "valid": true,
  "email": "john@company.com",
  "confidence_score": 95,
  "risk_score": 15,
  "risk_level": "low",
  "risk_factors": [],
  "checks": {
    "syntax": true,
    "dns_valid": true,
    "mx_records": true,
    "is_disposable": false,
    "is_role_based": false,
    "smtp_valid": true,
    "catch_all": false
  },
  "enrichment": {
    "domain_type": "corporate",
    "country": "United States",
    "engagement_score": 85,
    "company_name": "Company Inc"
  },
  "processing_time": 1.23
}
```

### 2. Get History

**Request:**
```http
GET /api/supabase/history?limit=10 HTTP/1.1
Host: localhost:5000
```

**Response:**
```json
{
  "validations": [
    {
      "email": "john@company.com",
      "valid": true,
      "confidence_score": 95,
      "risk_level": "low",
      "validated_at": "2024-12-05T14:30:00Z",
      "enrichment": {
        "domain_type": "corporate",
        "country": "United States"
      }
    },
    ...
  ],
  "total": 10
}
```

### 3. Get Analytics

**Request:**
```http
GET /api/supabase/analytics HTTP/1.1
Host: localhost:5000
```

**Response:**
```json
{
  "total_validations": 1234,
  "valid_count": 987,
  "invalid_count": 247,
  "success_rate": 80.0,
  "risk_distribution": {
    "low": 650,
    "medium": 400,
    "high": 150,
    "critical": 34
  },
  "domain_types": {
    "corporate": 750,
    "free": 350,
    "education": 134
  },
  "top_domains": [
    {"domain": "gmail.com", "count": 245},
    {"domain": "company.com", "count": 189},
    {"domain": "outlook.com", "count": 156}
  ]
}
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PRODUCTION                           │
└─────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐
│   Render.com │         │   Vercel     │
│   (Backend)  │◄────────┤  (Frontend)  │
│              │  API    │              │
│  Flask App   │  Calls  │  React App   │
│  Port 5000   │         │  Static      │
└──────┬───────┘         └──────────────┘
       │
       │ Database
       │ Connection
       ▼
┌──────────────┐
│   Supabase   │
│  (Database)  │
│              │
│  PostgreSQL  │
│  + REST API  │
└──────────────┘

Alternative: Single Server Deployment

┌─────────────────────────────────────┐
│         VPS / Cloud Server          │
│                                     │
│  ┌─────────────────────────────┐   │
│  │         Nginx               │   │
│  │  (Reverse Proxy)            │   │
│  │                             │   │
│  │  /:3000 → React Build       │   │
│  │  /api → Flask :5000         │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │    Gunicorn + Flask         │   │
│  │    Port 5000                │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │    React Build              │   │
│  │    /var/www/html            │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│   Supabase   │
└──────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────┐
│          Security Layers                │
├─────────────────────────────────────────┤
│                                         │
│  1. Frontend Security                   │
│     ├─ Input validation                │
│     ├─ XSS prevention                  │
│     ├─ HTTPS only                      │
│     └─ No sensitive data in localStorage│
│                                         │
│  2. API Security                        │
│     ├─ CORS configuration              │
│     ├─ Rate limiting                   │
│     ├─ Input sanitization              │
│     ├─ Error handling                  │
│     └─ API key validation              │
│                                         │
│  3. Database Security                   │
│     ├─ Row-level security (RLS)        │
│     ├─ Encrypted connections           │
│     ├─ Parameterized queries           │
│     ├─ Access control                  │
│     └─ Audit logging                   │
│                                         │
│  4. Data Privacy                        │
│     ├─ No email content stored         │
│     ├─ Metadata only                   │
│     ├─ GDPR compliant                  │
│     └─ Data retention policies         │
│                                         │
└─────────────────────────────────────────┘
```

---

## Performance Optimization

```
┌─────────────────────────────────────────┐
│       Performance Strategies            │
├─────────────────────────────────────────┤
│                                         │
│  Frontend:                              │
│  ├─ Code splitting                     │
│  ├─ Lazy loading                       │
│  ├─ Memoization (React.memo)           │
│  ├─ Debounced API calls                │
│  └─ Optimized re-renders               │
│                                         │
│  Backend:                               │
│  ├─ Connection pooling                 │
│  ├─ Caching (Redis)                    │
│  ├─ Async operations                   │
│  ├─ Batch processing                   │
│  └─ Query optimization                 │
│                                         │
│  Database:                              │
│  ├─ Indexed columns                    │
│  ├─ Query optimization                 │
│  ├─ Connection pooling                 │
│  └─ Read replicas                      │
│                                         │
└─────────────────────────────────────────┘
```

---

## Monitoring & Logging

```
┌─────────────────────────────────────────┐
│         Monitoring Stack                │
├─────────────────────────────────────────┤
│                                         │
│  Application Logs:                      │
│  ├─ Flask logging                      │
│  ├─ Error tracking                     │
│  ├─ Performance metrics                │
│  └─ User actions                       │
│                                         │
│  Database Logs:                         │
│  ├─ Query performance                  │
│  ├─ Connection stats                   │
│  ├─ Error logs                         │
│  └─ Audit trail                        │
│                                         │
│  Frontend Logs:                         │
│  ├─ Console errors                     │
│  ├─ API failures                       │
│  ├─ User interactions                  │
│  └─ Performance metrics                │
│                                         │
└─────────────────────────────────────────┘
```

---

## Scalability

```
Current Capacity:
├─ 100 validations/minute
├─ 10,000 validations/day
├─ 1M validations/month
└─ < 2 second response time

Scaling Options:

Horizontal Scaling:
├─ Multiple Flask instances
├─ Load balancer (Nginx)
├─ Database read replicas
└─ CDN for static assets

Vertical Scaling:
├─ Increase server resources
├─ Optimize database queries
├─ Add caching layer
└─ Use async workers

Future Enhancements:
├─ Queue system (Celery)
├─ Microservices architecture
├─ Kubernetes deployment
└─ Auto-scaling groups
```

---

**This architecture supports enterprise-scale email validation! 🚀**

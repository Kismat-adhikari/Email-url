# Flask + React Email Validator Setup Guide

## 🏗️ Project Structure

```
email/
├── app.py                          # Flask backend API
├── emailvalidator_unified.py       # Email validation engine
├── requirements.txt                # Python dependencies
├── frontend/                       # React frontend
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.js
│       ├── index.css
│       ├── App.js
│       └── App.css
└── test files...
```

---

## 🚀 Setup Instructions

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `dnspython` - For DNS/MX checking
- `flask` - Web framework
- `flask-cors` - CORS support for React

---

### Step 2: Install Node.js Dependencies

```bash
cd frontend
npm install
```

This installs:
- `react` - Frontend framework
- `react-dom` - React DOM rendering
- `axios` - HTTP client
- `react-scripts` - Build tools

---

### Step 3: Start the Backend (Flask)

Open a terminal and run:

```bash
python app.py
```

**Expected output:**
```
============================================================
Email Validator API Starting...
============================================================

Endpoints:
  - http://localhost:5000/
  - http://localhost:5000/api/health
  - http://localhost:5000/api/validate
  - http://localhost:5000/api/validate/advanced
  - http://localhost:5000/api/validate/batch
  - http://localhost:5000/api/stats

Frontend:
  - React app will connect to this API

============================================================

 * Running on http://0.0.0.0:5000
```

**Backend is now running on http://localhost:5000** ✅

---

### Step 4: Start the Frontend (React)

Open a **NEW terminal** (keep Flask running) and run:

```bash
cd frontend
npm start
```

**Expected output:**
```
Compiled successfully!

You can now view email-validator-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

**Frontend is now running on http://localhost:3000** ✅

Your browser should automatically open to http://localhost:3000

---

## 🎯 How to Use

### Single Email Validation

1. Enter an email address in the input field
2. Choose "Basic" or "Advanced" mode
3. Click "Validate" or press Enter
4. See results with confidence score and detailed checks

### Batch Validation

1. Click "Batch Validation" tab
2. Enter multiple emails (one per line)
3. Choose "Basic" or "Advanced" mode
4. Click "Validate Batch"
5. See summary statistics and individual results

---

## 🔧 API Endpoints

### GET /
API documentation

### GET /api/health
Health check endpoint

### POST /api/validate
Basic email validation (fast)

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "email": "user@example.com",
  "valid": true,
  "processing_time": 0.001,
  "timestamp": 1234567890.123
}
```

### POST /api/validate/advanced
Advanced email validation (comprehensive)

**Request:**
```json
{
  "email": "user@gmail.com",
  "check_dns": true,
  "check_mx": true,
  "check_disposable": true,
  "check_typos": true,
  "check_role_based": true
}
```

**Response:**
```json
{
  "email": "user@gmail.com",
  "valid": true,
  "checks": {
    "syntax": true,
    "dns_valid": true,
    "mx_records": true,
    "is_disposable": false,
    "is_role_based": false
  },
  "confidence_score": 100,
  "suggestion": null,
  "reason": "Valid email",
  "processing_time": 0.123,
  "timestamp": 1234567890.123
}
```

### POST /api/validate/batch
Batch email validation

**Request:**
```json
{
  "emails": ["user@example.com", "test@test.com"],
  "advanced": true
}
```

**Response:**
```json
{
  "total": 2,
  "valid_count": 2,
  "invalid_count": 0,
  "results": [...],
  "processing_time": 0.234,
  "timestamp": 1234567890.123
}
```

### GET /api/stats
Get validation statistics and configuration

---

## 🎨 Features

### Frontend Features:
- ✅ Single email validation
- ✅ Batch email validation
- ✅ Basic and Advanced modes
- ✅ Real-time validation
- ✅ Confidence score visualization
- ✅ Detailed check results
- ✅ Typo suggestions
- ✅ Responsive design
- ✅ Beautiful gradient UI
- ✅ Smooth animations

### Backend Features:
- ✅ RFC 5321 syntax validation
- ✅ DNS record checking
- ✅ MX record verification
- ✅ Disposable email detection
- ✅ Role-based email detection
- ✅ Typo suggestion
- ✅ Confidence scoring (0-100)
- ✅ Batch processing
- ✅ CORS enabled
- ✅ Error handling
- ✅ Performance metrics

---

## 🧪 Testing

### Test Backend API

```bash
# Health check
curl http://localhost:5000/api/health

# Basic validation
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# Advanced validation
curl -X POST http://localhost:5000/api/validate/advanced \
  -H "Content-Type: application/json" \
  -d '{"email":"user@gmail.com"}'
```

### Test Frontend

1. Open http://localhost:3000
2. Try these test cases:
   - `user@gmail.com` - Should get 100 confidence
   - `user@gmial.com` - Should suggest gmail.com
   - `test@tempmail.com` - Should flag as disposable
   - `info@company.com` - Should flag as role-based

---

## 🛠️ Development

### Backend Development

Edit `app.py` and Flask will auto-reload (debug mode is on)

### Frontend Development

Edit files in `frontend/src/` and React will hot-reload automatically

---

## 📦 Building for Production

### Build Frontend

```bash
cd frontend
npm run build
```

This creates an optimized production build in `frontend/build/`

### Serve Frontend with Flask

Update `app.py` to serve the React build:

```python
from flask import send_from_directory
import os

# Add this route
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Set static folder
app.static_folder = 'frontend/build'
```

Then run:
```bash
python app.py
```

Now everything runs on http://localhost:5000

---

## 🚨 Troubleshooting

### Backend won't start
- Check if port 5000 is already in use
- Make sure all dependencies are installed: `pip install -r requirements.txt`

### Frontend won't start
- Check if port 3000 is already in use
- Make sure dependencies are installed: `cd frontend && npm install`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

### CORS errors
- Make sure Flask backend is running
- Check that `flask-cors` is installed
- Verify API_URL in frontend matches backend URL

### DNS checks failing
- Make sure `dnspython` is installed
- Check internet connection
- DNS lookups require network access

---

## 📝 Environment Variables

### Frontend (.env file in frontend/)

```
REACT_APP_API_URL=http://localhost:5000
```

### Backend

No environment variables needed for development.

For production, set:
- `FLASK_ENV=production`
- `FLASK_DEBUG=0`

---

## 🎯 Quick Start Summary

```bash
# Terminal 1: Start Backend
pip install -r requirements.txt
python app.py

# Terminal 2: Start Frontend
cd frontend
npm install
npm start

# Open browser to http://localhost:3000
```

**That's it! Your email validator is running!** 🚀

---

## 📚 Additional Resources

- Flask Documentation: https://flask.palletsprojects.com/
- React Documentation: https://react.dev/
- Axios Documentation: https://axios-http.com/
- Email Validation RFC: https://tools.ietf.org/html/rfc5321

---

## ✨ Features to Add (Future)

- [ ] User authentication
- [ ] Save validation history
- [ ] Export results to CSV
- [ ] API rate limiting
- [ ] Email verification via SMTP
- [ ] Custom domain blacklist/whitelist
- [ ] Bulk file upload
- [ ] Real-time validation as you type
- [ ] Dark mode
- [ ] Multiple language support

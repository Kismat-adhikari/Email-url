# 🚀 How to Run the Email Validator

## ✅ Backend is Already Running!

The Flask backend is running on **http://localhost:5000**

You can test it:
```bash
curl http://localhost:5000/api/health
```

---

## 🎨 Start the Frontend

### Option 1: Open New Terminal (Recommended)

1. Open a **NEW terminal window** (don't close the backend)
2. Navigate to the frontend folder:
   ```bash
   cd frontend
   ```
3. Install dependencies (first time only):
   ```bash
   npm install
   ```
4. Start the development server:
   ```bash
   npm start
   ```
5. Your browser will automatically open to **http://localhost:3000**
   - If port 3000 is busy, it will ask to use another port (press Y)

### Option 2: Use the Batch Script (Windows)

1. Double-click `frontend/start_frontend.bat`
2. Wait for it to compile
3. Browser will open automatically

---

## 🎯 What You'll See

### Frontend (http://localhost:3000 or 3001)

A beautiful web interface with:
- **Single Email Validation** - Test one email at a time
- **Batch Validation** - Test multiple emails
- **Two Modes:**
  - **Basic** - Quick syntax check only
  - **Advanced** - Full check with DNS, MX, disposable detection

### Try These Test Cases:

1. **Perfect Email:**
   ```
   user@gmail.com
   ```
   Result: ✅ 100 confidence, all checks pass

2. **Typo Detection:**
   ```
   user@gmial.com
   ```
   Result: ❌ Suggests "gmail.com"

3. **Disposable Email:**
   ```
   test@tempmail.com
   ```
   Result: ⚠️ Valid but warns it's disposable

4. **Role-Based:**
   ```
   info@company.com
   ```
   Result: ⚠️ Valid but warns it's role-based

5. **Invalid:**
   ```
   invalid@
   ```
   Result: ❌ Invalid syntax

---

## 📊 Understanding the Modes

### Basic Mode (Fast)
- ✅ Checks email format only
- ✅ Very fast (< 1ms)
- ✅ No internet required
- ❌ Doesn't check if domain exists

**Use when:** You just need format validation

### Advanced Mode (Comprehensive)
- ✅ Checks format
- ✅ Checks if domain exists (DNS)
- ✅ Checks if domain can receive email (MX)
- ✅ Detects disposable emails
- ✅ Detects role-based emails
- ✅ Suggests typo corrections
- ✅ Gives confidence score (0-100)
- ⚠️ Slower (100-200ms due to network checks)

**Use when:** You need real validation for user signups

---

## 🔧 Current Status

### ✅ Running:
- Backend (Flask): http://localhost:5000
- Process ID: 3

### ⏳ To Start:
- Frontend (React): Open new terminal and run `cd frontend && npm start`

---

## 🧪 Test the Backend API

While frontend is starting, test the backend:

```bash
# Health check
curl http://localhost:5000/api/health

# Basic validation
curl -X POST http://localhost:5000/api/validate -H "Content-Type: application/json" -d "{\"email\":\"user@example.com\"}"

# Advanced validation
curl -X POST http://localhost:5000/api/validate/advanced -H "Content-Type: application/json" -d "{\"email\":\"user@gmail.com\"}"
```

Or run the test script:
```bash
python test_api.py
```

---

## 🛑 To Stop Everything

### Stop Backend:
```bash
# Press Ctrl+C in the terminal running Flask
```

Or use the process manager:
```bash
# In Python
from kiro import stop_process
stop_process(3)
```

### Stop Frontend:
```bash
# Press Ctrl+C in the terminal running React
```

---

## 📁 Quick Reference

### Backend Files:
- `app.py` - Flask API server
- `emailvalidator_unified.py` - Validation engine

### Frontend Files:
- `frontend/src/App.js` - Main React component
- `frontend/src/App.css` - Styles

### Documentation:
- `VALIDATION_MODES_EXPLAINED.md` - Explains Basic vs Advanced
- `FULLSTACK_README.md` - Complete documentation
- `START_HERE.md` - Quick start guide

---

## 🎉 You're Almost There!

**Backend:** ✅ Running on port 5000
**Frontend:** ⏳ Just open a new terminal and run:

```bash
cd frontend
npm start
```

Then open http://localhost:3000 in your browser!

**Happy validating!** 🚀

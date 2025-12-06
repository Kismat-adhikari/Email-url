# 🚀 Quick Start Instructions

## Step 1: Stop Everything Currently Running

**Double-click:** `STOP_EVERYTHING.bat`

This will stop any Python or Node processes.

---

## Step 2: Start Everything

**Double-click:** `START_EVERYTHING.bat`

This will:
1. Start the backend (app_dashboard.py) in one window
2. Start the frontend (React) in another window
3. Automatically open your browser to http://localhost:3000

---

## Step 3: Test It!

### Test Validation
1. Go to **Validate** tab
2. Enter: `test@gmail.com`
3. Click **Validate**
4. ✅ Should see results with confidence score, risk level, enrichment

### Test History
1. Go to **History** tab
2. ✅ Should see the email you just validated
3. Shows timestamp, score, risk level

### Test on Different Browser
1. Open Chrome → Validate some emails
2. Open Firefox → Should have empty history
3. ✅ Each browser has separate history!

---

## 🐛 If Something Goes Wrong

### Backend won't start?
```bash
# Manually run in terminal:
python app_dashboard.py
```

### Frontend won't start?
```bash
# Manually run in terminal:
cd frontend
npm start
```

### Port already in use?
Run `STOP_EVERYTHING.bat` first, then try again.

---

## ✅ What You Should See

### Backend Window
```
* Running on http://127.0.0.1:5000
* Debug mode: on
```

### Frontend Window
```
Compiled successfully!
Local: http://localhost:3000
```

### Browser
- Opens automatically to http://localhost:3000
- Shows Email Validator dashboard
- Three tabs: Validate, History, Analytics

---

## 🎯 Quick Test Checklist

- [ ] Backend running (port 5000)
- [ ] Frontend running (port 3000)
- [ ] Browser opens automatically
- [ ] Can validate an email
- [ ] Email appears in History tab
- [ ] Different browsers have different histories

---

**That's it! You're ready to test! 🎉**

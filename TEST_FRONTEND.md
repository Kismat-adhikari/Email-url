# 🧪 Frontend Testing Guide

## Quick Test Checklist

### ✅ Pre-Test Setup

1. **Backend Running:**
   ```bash
   python app_dashboard.py
   ```
   Should see: `Running on http://127.0.0.1:5000`

2. **Frontend Running:**
   ```bash
   cd frontend
   npm start
   ```
   Should open: `http://localhost:3000`

3. **Supabase Configured:**
   Check `.env` has:
   ```
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key
   ```

---

## 🔍 Test 1: Validate Tab

### Single Email Validation

1. Click **"Validate"** tab (should be active by default)
2. Select **"Single Email"** mode
3. Choose **"Advanced"** validation mode
4. Enter: `test@gmail.com`
5. Click **"Validate"**

**Expected Result:**
- ✅ Green "Valid Email" box appears
- ✅ Confidence score shows (e.g., 85/100)
- ✅ Risk assessment displays (e.g., "Low Risk")
- ✅ Email intelligence shows:
  - Domain Type: Free
  - Country: United States
  - Engagement Score: XX/100
- ✅ All checks show green ✓
- ✅ Processing time displayed

### Batch Email Validation

1. Click **"Batch Validation"** mode
2. Select **"Type Emails"**
3. Paste these emails:
   ```
   valid@gmail.com
   invalid@fake-domain-xyz.com
   test@outlook.com
   ```
4. Click **"Validate Batch"**

**Expected Result:**
- ✅ Summary shows: 3 Total, 2 Valid, 1 Invalid
- ✅ Each email listed with ✓ or ✗
- ✅ Scores displayed for each
- ✅ Export CSV button appears
- ✅ Copy button works

### File Upload

1. Click **"Upload File"** tab
2. Click upload area
3. Select `test_emails.txt`
4. Preview shows emails
5. Click **"Validate Batch"**

**Expected Result:**
- ✅ All emails from file validated
- ✅ Results displayed correctly
- ✅ Can export to CSV

---

## 📜 Test 2: History Tab

1. Click **"History"** tab
2. Wait for data to load

**Expected Result:**
- ✅ Shows all previously validated emails
- ✅ Each item shows:
  - Email address
  - Timestamp
  - Confidence score
  - Risk level (color-coded)
  - Enrichment tags
- ✅ Valid emails have green left border
- ✅ Invalid emails have red left border
- ✅ Hover effect works
- ✅ Refresh button reloads data

**If Empty:**
- ✅ Shows empty state with icon
- ✅ Message: "No validation history yet"
- ✅ Instruction to validate emails

---

## 📊 Test 3: Analytics Tab

1. Click **"Analytics"** tab
2. Wait for data to load

**Expected Result:**
- ✅ Four summary cards show:
  - Total Validations
  - Valid Emails
  - Invalid Emails
  - Success Rate %
- ✅ Risk Distribution chart displays
  - Bars for Low/Medium/High/Critical
  - Color-coded bars
  - Count for each level
- ✅ Domain Types section shows
  - Corporate count
  - Free count
  - Education count
- ✅ Top Domains list displays
  - Ranked #1, #2, #3...
  - Domain names
  - Email counts

**If Empty:**
- ✅ Shows empty state
- ✅ Message: "No analytics data available"

---

## 🌙 Test 4: Dark Mode

1. Click moon icon (🌙) in header
2. Page switches to dark theme
3. Click sun icon (☀️)
4. Page switches back to light theme
5. Refresh page
6. Theme persists

**Expected Result:**
- ✅ All components change color
- ✅ Text remains readable
- ✅ Borders and backgrounds adapt
- ✅ Preference saved to localStorage
- ✅ Works across all tabs

---

## 📥 Test 5: Export Features

### CSV Export

1. Validate batch of emails
2. Click **"📥 Export CSV"**
3. File downloads

**Expected Result:**
- ✅ CSV file downloads
- ✅ Filename includes timestamp
- ✅ Opens in Excel/Sheets
- ✅ Contains all validation data

### Copy to Clipboard

1. Validate batch of emails
2. Click **"📋 Copy"**
3. Alert shows "Results copied"
4. Paste in text editor

**Expected Result:**
- ✅ Alert appears
- ✅ Text copied to clipboard
- ✅ Format: `✓ email@domain.com`

---

## 🔄 Test 6: Refresh Functionality

### History Refresh

1. Go to History tab
2. Open new browser tab
3. Validate new email via API or another window
4. Return to History tab
5. Click **"🔄 Refresh"**

**Expected Result:**
- ✅ New validation appears
- ✅ List updates without page reload
- ✅ Button shows loading state

### Analytics Refresh

1. Go to Analytics tab
2. Validate more emails
3. Click **"🔄 Refresh"**

**Expected Result:**
- ✅ Counts update
- ✅ Charts update
- ✅ No page reload needed

---

## 📱 Test 7: Responsive Design

### Desktop (1920x1080)
- ✅ Multi-column layouts
- ✅ All features visible
- ✅ No horizontal scroll

### Tablet (768x1024)
- ✅ Adaptive grids
- ✅ Buttons stack properly
- ✅ Readable text

### Mobile (375x667)
- ✅ Single column layout
- ✅ Touch-friendly buttons
- ✅ No content cut off
- ✅ Scrollable lists

---

## 🐛 Common Issues & Fixes

### Issue: "Network Error" when validating

**Cause:** Backend not running or wrong URL

**Fix:**
```bash
# Check backend is running
curl http://localhost:5000/health

# If not, start it
python app_dashboard.py
```

### Issue: History/Analytics show empty

**Cause:** No data in Supabase or connection issue

**Fix:**
1. Check Supabase credentials in `.env`
2. Validate some emails first
3. Check browser console (F12) for errors
4. Verify backend logs

### Issue: Dark mode not working

**Cause:** localStorage disabled or browser issue

**Fix:**
1. Check browser is not in incognito mode
2. Clear browser cache
3. Check browser console for errors

### Issue: CSV export not working

**Cause:** Browser blocking download or no data

**Fix:**
1. Check browser allows downloads
2. Ensure batch results exist
3. Try different browser

### Issue: Enrichment data not showing

**Cause:** Using old endpoint or enrichment disabled

**Fix:**
1. Ensure using `app_dashboard.py` (not `app.py`)
2. Check endpoint is `/api/supabase/validate`
3. Verify enrichment module works: `python test_enrichment.py`

---

## ✅ Success Criteria

All tests pass if:

- ✅ All 3 tabs load without errors
- ✅ Validation works in both modes
- ✅ Risk scores display correctly
- ✅ Enrichment data appears
- ✅ History shows past validations
- ✅ Analytics displays charts
- ✅ Dark mode toggles properly
- ✅ Export functions work
- ✅ Refresh buttons update data
- ✅ Responsive on all screen sizes
- ✅ No console errors (F12)

---

## 🎯 Performance Checks

### Load Times
- ✅ Initial page load: < 2 seconds
- ✅ Tab switching: Instant
- ✅ Validation: < 3 seconds
- ✅ History load: < 2 seconds
- ✅ Analytics load: < 2 seconds

### Smooth Animations
- ✅ Tab transitions
- ✅ Progress bars
- ✅ Hover effects
- ✅ Dark mode toggle

---

## 📊 Browser Compatibility

Test in:
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Edge (latest)

All features should work identically.

---

## 🚀 Next Steps After Testing

If all tests pass:
1. ✅ Frontend is production-ready
2. ✅ Can deploy to hosting
3. ✅ Can share with users
4. ✅ Can integrate with other systems

If tests fail:
1. Check error messages
2. Review browser console
3. Verify backend is running
4. Check Supabase connection
5. Review documentation

---

## 📝 Test Report Template

```
Frontend Test Report
Date: ___________
Tester: ___________

✅ Validate Tab: PASS / FAIL
✅ History Tab: PASS / FAIL
✅ Analytics Tab: PASS / FAIL
✅ Dark Mode: PASS / FAIL
✅ Export Features: PASS / FAIL
✅ Refresh Functions: PASS / FAIL
✅ Responsive Design: PASS / FAIL

Issues Found:
1. ___________
2. ___________

Overall Status: PASS / FAIL
```

---

**Happy Testing! 🎉**

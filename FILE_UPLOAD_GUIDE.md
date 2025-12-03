# 📁 File Upload Feature Guide

## ✨ New Feature: Upload .txt Files

You can now upload text files containing multiple email addresses for batch validation!

---

## 🚀 How to Use

### Step 1: Go to Batch Validation Mode
Click the **"Batch Validation"** tab in the app

### Step 2: Choose Upload Method
You'll see two options:
- **✏️ Type Emails** - Manually type or paste emails
- **📁 Upload File** - Upload a .txt file

### Step 3: Upload Your File
1. Click **"📁 Upload File"**
2. Click the upload box
3. Select your .txt file
4. The emails will automatically load into the preview

### Step 4: Validate
Click **"Validate Batch"** to check all emails

---

## 📄 File Format

Your .txt file should have **one email per line**:

```
user@example.com
john.doe@company.com
test@gmail.com
admin@business.org
```

**Example file:** `frontend/public/sample_emails.txt`

---

## ✅ Supported Formats

- ✅ `.txt` files only
- ✅ One email per line
- ✅ Empty lines are ignored
- ✅ Whitespace is trimmed
- ✅ Up to 1,000 emails per file

---

## 🎯 Features

### After Upload:
- ✅ See preview of all emails
- ✅ Edit emails in the preview if needed
- ✅ See count of emails loaded
- ✅ Choose Basic or Advanced validation
- ✅ Get detailed results for each email

### Results Show:
- Total emails processed
- Valid count
- Invalid count
- Individual results for each email
- Confidence scores (Advanced mode)
- Typo suggestions (Advanced mode)
- Warnings for disposable/role-based emails

---

## 📊 Example Workflow

### 1. Prepare Your File
Create `my_emails.txt`:
```
user@gmail.com
test@example.com
admin@company.com
```

### 2. Upload in App
1. Open http://localhost:3000
2. Click "Batch Validation"
3. Click "📁 Upload File"
4. Select `my_emails.txt`

### 3. Review Preview
- See all 3 emails loaded
- Edit if needed

### 4. Validate
- Choose "Advanced" mode
- Click "Validate Batch"

### 5. View Results
```
Total: 3
Valid: 3
Invalid: 0

✓ user@gmail.com - Score: 100
✓ test@example.com - Score: 100
✓ admin@company.com - Score: 90 (Warning: Role-based)
```

---

## 🧪 Test Files Included

### Sample File
Location: `frontend/public/sample_emails.txt`

Contains 10 test emails including:
- Valid emails
- Typos (gmial.com)
- Disposable emails
- Role-based emails
- Invalid emails

**Try it:** Download and upload this file to test the feature!

### Your Test Files
You can also use:
- `test_emails.txt` - 67 test cases
- `bulk_test_emails.txt` - 571 emails
- `stress_test_emails.txt` - Edge cases

---

## 💡 Tips

### For Best Results:
1. **Clean your file** - Remove headers, footers, extra text
2. **One per line** - Each email on its own line
3. **Check encoding** - Use UTF-8 encoding
4. **Remove duplicates** - The app doesn't auto-dedupe
5. **Use Advanced mode** - For comprehensive validation

### File Size Limits:
- Maximum: 1,000 emails per batch
- For larger files: Split into multiple files
- Or use the CLI: `python emailvalidator_unified.py large_file.txt`

---

## 🔧 Troubleshooting

### "Please select a .txt file"
- Only .txt files are supported
- Rename your file to end with .txt

### "Please enter at least one email address"
- File might be empty
- Check file has emails (one per line)
- Make sure emails aren't commented out

### File not loading
- Check file encoding (should be UTF-8)
- Try opening file in notepad to verify format
- Make sure each email is on a new line

---

## 📝 File Format Examples

### ✅ Good Format:
```
user@example.com
john@company.com
test@gmail.com
```

### ❌ Bad Format:
```
user@example.com, john@company.com
Email: test@gmail.com
<user@example.com>
```

### ✅ With Empty Lines (OK):
```
user@example.com

john@company.com

test@gmail.com
```

---

## 🎨 UI Features

### Upload Box:
- Drag-and-drop style interface
- Shows selected filename
- Click to change file
- Visual feedback on hover

### Preview:
- Shows all loaded emails
- Editable textarea
- Email count display
- Scrollable for long lists

### Results:
- Color-coded (green/red)
- Sortable by status
- Confidence scores
- Detailed breakdown

---

## 🚀 Quick Start

1. **Create a test file:**
   ```bash
   echo "user@gmail.com" > test.txt
   echo "test@example.com" >> test.txt
   ```

2. **Open the app:**
   ```
   http://localhost:3000
   ```

3. **Upload and validate:**
   - Click "Batch Validation"
   - Click "📁 Upload File"
   - Select `test.txt`
   - Click "Validate Batch"

**Done!** 🎉

---

## 📚 Related Documentation

- `HOW_TO_RUN.md` - How to start the app
- `VALIDATION_MODES_EXPLAINED.md` - Basic vs Advanced modes
- `FULLSTACK_README.md` - Complete documentation

---

## ✨ Summary

**New Feature:** Upload .txt files with emails for batch validation

**Benefits:**
- ✅ No need to copy-paste large lists
- ✅ Easy to validate email lists from exports
- ✅ Preview before validation
- ✅ Edit after upload if needed
- ✅ Works with existing test files

**Try it now!** Upload `sample_emails.txt` to see it in action! 🚀

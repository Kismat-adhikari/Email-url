# Validation Modes Explained

## 🎯 Two Validation Modes

### 1. **Basic - Syntax Only (Fast)**

**What it checks:**
- ✅ Email format is correct (has @ symbol, proper characters, etc.)
- ✅ Follows RFC 5321 rules
- ✅ Length limits (254 chars max)
- ✅ No spaces or invalid characters

**What it DOESN'T check:**
- ❌ If the domain exists
- ❌ If the domain can receive email
- ❌ If it's a disposable email
- ❌ If it's a role-based email

**Speed:** Very fast (< 1ms per email)

**Use when:**
- You just need quick format validation
- You're validating thousands of emails
- You don't need to verify if email actually exists

**Example:**
```
Input: user@example.com
Output: ✅ Valid (syntax is correct)

Input: invalid@
Output: ❌ Invalid (missing domain)
```

---

### 2. **Advanced - Full Check (DNS, MX, Disposable)**

**What it checks:**
- ✅ Everything from Basic mode
- ✅ Domain exists (DNS check)
- ✅ Domain can receive email (MX records)
- ✅ Not a disposable/temporary email service
- ✅ Not a role-based email (info@, admin@, etc.)
- ✅ Suggests corrections for typos

**Speed:** Slower (100-200ms per email due to network checks)

**Use when:**
- You need to verify email actually exists
- You want to block disposable emails
- You want to catch typos (gmial.com → gmail.com)
- Quality is more important than speed

**Example:**
```
Input: user@gmail.com
Output: ✅ Valid
  - Syntax: ✅
  - DNS: ✅
  - MX Records: ✅
  - Not Disposable: ✅
  - Not Role-Based: ✅
  - Confidence: 100/100

Input: user@gmial.com (typo)
Output: ❌ Invalid
  - Syntax: ✅
  - DNS: ❌ (domain doesn't exist)
  - Suggestion: Did you mean gmail.com?
  - Confidence: 60/100

Input: test@tempmail.com
Output: ✅ Valid (but warning)
  - Syntax: ✅
  - DNS: ✅
  - MX Records: ✅
  - Disposable: ⚠️ Warning!
  - Confidence: 90/100
```

---

## 📊 Comparison

| Feature | Basic | Advanced |
|---------|-------|----------|
| Syntax Check | ✅ | ✅ |
| DNS Check | ❌ | ✅ |
| MX Records | ❌ | ✅ |
| Disposable Detection | ❌ | ✅ |
| Role-Based Detection | ❌ | ✅ |
| Typo Suggestions | ❌ | ✅ |
| Confidence Score | ❌ | ✅ |
| Speed | Very Fast | Slower |
| Network Required | No | Yes |

---

## 🎯 Which Should You Use?

### Use **Basic** when:
- ✅ You just need format validation
- ✅ Speed is critical
- ✅ You're validating thousands of emails
- ✅ You don't have internet connection
- ✅ You'll verify emails later (e.g., send confirmation email)

### Use **Advanced** when:
- ✅ You need to verify email actually works
- ✅ You want to block fake/disposable emails
- ✅ You want typo suggestions
- ✅ Quality is more important than speed
- ✅ You're validating user signups
- ✅ You want detailed validation reports

---

## 💡 Real-World Examples

### Example 1: User Registration Form
**Use Advanced** - You want to ensure users provide real, working emails

### Example 2: Email List Cleaning
**Use Basic first** - Quick syntax check on 100,000 emails
**Then Advanced** - Deep check on the valid ones

### Example 3: Contact Form
**Use Advanced** - Catch typos and suggest corrections in real-time

### Example 4: Data Import
**Use Basic** - Fast validation of imported data

---

## 🔧 Technical Details

### Basic Mode
- Checks: Syntax only
- Time: < 1ms per email
- Network: Not required
- Returns: True/False

### Advanced Mode
- Checks: Syntax + DNS + MX + Disposable + Role-based + Typos
- Time: 100-200ms per email (due to DNS lookups)
- Network: Required (for DNS/MX checks)
- Returns: Detailed object with confidence score

---

## 🎨 In the UI

When you select a mode in the web interface:

**Basic Mode:**
- Shows simple ✅ Valid or ❌ Invalid
- No confidence score
- No detailed checks
- Very fast response

**Advanced Mode:**
- Shows confidence score (0-100)
- Shows all individual checks
- Shows typo suggestions
- Shows warnings for disposable/role-based
- Slower response (due to network checks)

---

## 📝 Summary

**Basic = Quick format check**
- Just checks if email looks right
- Super fast
- Good for bulk validation

**Advanced = Full verification**
- Checks if email actually works
- Includes DNS, MX, disposable detection
- Slower but comprehensive
- Good for user signups

Choose based on your needs! 🚀

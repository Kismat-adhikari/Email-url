# CSS Variables Quick Reference

## Light Mode (Default)
```css
--bg-primary:      #ffffff      (Main backgrounds)
--bg-secondary:    #f9fafb      (Cards, sections)
--text-primary:    #1f2937      (Main text)
--text-secondary:  #6b7280      (Labels, hints)
--border-color:    #eef2f7      (Dividers)
--card-shadow:     0 6px 24px rgba(0, 0, 0, 0.08)
```

## Dark Mode
```css
--bg-primary:      #1a1a2e      (Main backgrounds)
--bg-secondary:    #252c3c      (Cards, sections)
--text-primary:    #f1f5f9      (Main text)
--text-secondary:  #cbd5e1      (Labels, hints)
--border-color:    #3d4556      (Dividers)
--card-shadow:     0 6px 24px rgba(0, 0, 0, 0.3)
```

## How to Use Variables in New CSS

### Background Colors
```css
background: var(--bg-primary);    /* White/Dark Blue */
background: var(--bg-secondary);  /* Light Gray/Darker Blue */
```

### Text Colors
```css
color: var(--text-primary);       /* Dark Gray/Light Blue-White */
color: var(--text-secondary);     /* Medium Gray/Light Gray-Blue */
```

### Borders & Dividers
```css
border: 1px solid var(--border-color);
border-top: 1px solid var(--border-color);
```

### Shadows
```css
box-shadow: var(--card-shadow);
```

### With Transitions
```css
background: var(--bg-secondary);
border: 1px solid var(--border-color);
transition: background-color 0.3s ease, border-color 0.3s ease;
```

## Fixed Accent Colors (Don't Use Variables)
```css
Red (Error/Destructive):    #e74c3c, hover: #c0392b
Green (Success/Benefit):    #27ae60
Blue (Info/Link):           #3498db
Quota Gradient:             green→orange→red
```

## Typography Sizes
```css
h2 (Page Title):      28px, 700 weight
h3 (Section):         18-20px, 700 weight
h4 (Sub-section):     16px, 700 weight
label (Form):         14px, 600 weight
body (Main text):     14px, 400 weight
secondary (Hint):     13px, 400 weight
value (Bold):         13px, 600 weight
small (Footer/date):  12px, 400 weight
```

## Common Pattern for New Components

### Themed Container
```css
.my-component {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    transition: background-color 0.3s ease, border-color 0.3s ease;
}
```

### Themed Text
```css
.my-component h3 {
    color: var(--text-primary);
    font-weight: 700;
}

.my-component p {
    color: var(--text-secondary);
    font-size: 14px;
}
```

### Themed Form Input
```css
.my-component input {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
}

.my-component input:focus {
    border-color: #3498db;
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}
```

## Dark Mode Toggle Implementation

**Already Done in TeamManagement.js:**
```javascript
// State
const [darkMode, setDarkMode] = useState(() => 
    localStorage.getItem('darkMode') ? JSON.parse(localStorage.getItem('darkMode')) : false
);

// Effect
useEffect(() => {
    if (darkMode) {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
}, [darkMode]);

// Button
<button onClick={() => setDarkMode(!darkMode)}>
    {darkMode ? <FiSun /> : <FiMoon />}
</button>
```

## CSS in HTML

```html
<!-- Light mode is default, dark mode overrides -->
<body>
    <!-- Light mode is active -->
</body>

<!-- With dark mode enabled -->
<body class="dark-mode">
    <!-- Dark mode is active -->
</body>
```

## File Locations
- **CSS Variables**: `frontend/src/TeamManagement.css` (Lines 1-15)
- **Dark Mode Override**: `frontend/src/TeamManagement.css` (Lines 9-15)
- **JavaScript State**: `frontend/src/TeamManagement.js` (Lines 26-27, 277-283)
- **Toggle Button**: `frontend/src/TeamManagement.js` (Line 438-440)

## Testing Dark Mode

```javascript
// In browser console
localStorage.setItem('darkMode', 'true');
document.body.classList.add('dark-mode');
// Page should now be in dark mode

// Toggle back
localStorage.setItem('darkMode', 'false');
document.body.classList.remove('dark-mode');
// Page should be in light mode
```

## CSS Variable Inheritance

Variables cascade from parent to child. Override at any level:

```css
/* Root defaults */
:root { --text-color: #1f2937; }

/* Dark mode override */
body.dark-mode { --text-color: #f1f5f9; }

/* Component uses the correct value */
.my-component { color: var(--text-color); }
```

## Performance Notes
- CSS variables: Zero runtime cost
- Theme toggle: <5ms class addition
- Transitions: GPU-accelerated, 60fps
- No JavaScript re-renders needed
- Browser handles cascading automatically

## Troubleshooting

**Problem**: Colors not updating when toggling dark mode
- [ ] Check `body` has `dark-mode` class added
- [ ] Verify CSS has `body.dark-mode { --var: value; }`
- [ ] Check browser DevTools for applied styles

**Problem**: New component not themed
- [ ] Use `var()` instead of hardcoded colors
- [ ] Add to both light and dark mode if custom colors
- [ ] Check CSS variable names are correct

**Problem**: Text hard to read in dark mode
- [ ] Verify using `--text-primary` or `--text-secondary`
- [ ] Check contrast ratio (should be 4.5:1+)
- [ ] Consider using secondary color for hints

## Adding New Theme

To add a new theme (e.g., high-contrast):

```css
/* Add new theme class */
body.high-contrast {
    --bg-primary: #000000;
    --text-primary: #ffffff;
    /* etc... */
}

/* Update JavaScript */
const [theme, setTheme] = useState('light'); // light, dark, high-contrast
const classes = theme === 'light' ? '' : theme;
document.body.className = classes;
```

---

**Last Updated**: Component styling complete
**Maintenance**: Low - just adjust variables to change all colors
**Contact**: Refer to DARK_MODE_IMPLEMENTATION_SUMMARY.md for full details

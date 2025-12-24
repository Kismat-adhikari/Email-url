# 🎨 DESIGN SYSTEM USAGE GUIDE

## Quick Reference for Developers

### Using CSS Variables

All styling uses CSS variables defined in `index.css`. Always use these instead of hardcoding colors.

```css
/* ✅ CORRECT - Using CSS Variables */
.my-component {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-md);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  transition: var(--transition-base);
}

/* ❌ WRONG - Hardcoding Colors */
.my-component {
  background: #ffffff;
  color: #111827;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

---

## Available CSS Variables

### Colors

#### Primary Colors
```css
--primary: #4f46e5           /* Main brand color */
--primary-dark: #4338ca      /* Darker variant for hover */
--primary-light: #e0e7ff     /* Light variant for backgrounds */
--primary-bg: #f0f9ff        /* Very light background color */
```

#### Secondary Colors
```css
--secondary: #7c3aed         /* Accent color */
--secondary-dark: #6d28d9    /* Darker variant */
--secondary-light: #edd5ff   /* Light variant */
```

#### Status Colors
```css
--success: #059669           /* Success/Valid state */
--success-dark: #065f46      /* Darker variant */
--success-light: #d1fae5     /* Light background */
--success-bg: #f0fdf4        /* Very light background */

--danger: #dc2626            /* Error/Invalid state */
--danger-dark: #991b1b       /* Darker variant */
--danger-light: #fee2e2      /* Light background */
--danger-bg: #fef2f2         /* Very light background */

--warning: #d97706           /* Warning state */
--warning-dark: #92400e      /* Darker variant */
--warning-light: #fed7aa     /* Light background */
--warning-bg: #fffbeb        /* Very light background */
```

#### Neutral Colors
```css
--text-primary: #111827      /* Main text */
--text-secondary: #6b7280    /* Secondary text */
--text-tertiary: #9ca3af     /* Tertiary text */

--bg-primary: #ffffff        /* Main background */
--bg-secondary: #f9fafb      /* Secondary background */
--bg-tertiary: #f3f4f6       /* Tertiary background */

--border-light: #e5e7eb      /* Light borders */
--border-medium: #d1d5db     /* Medium borders */
--border-dark: #9ca3af       /* Dark borders */
```

#### Gradients
```css
--gradient-primary: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)
--gradient-warm: linear-gradient(135deg, #f97316 0%, #f59e0b 100%)
--gradient-cool: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)
```

### Shadows

```css
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1)
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1)
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.15)
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.2)
```

### Spacing

```css
--spacing-xs: 4px
--spacing-sm: 8px
--spacing-md: 12px
--spacing-lg: 16px
--spacing-xl: 24px
--spacing-2xl: 32px
--spacing-3xl: 48px
```

### Border Radius

```css
--radius-sm: 4px
--radius-md: 6px
--radius-lg: 8px
--radius-xl: 12px
--radius-2xl: 16px
```

### Transitions

```css
--transition-fast: all 0.15s cubic-bezier(0.4, 0, 0.2, 1)
--transition-base: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)
--transition-slow: all 0.5s cubic-bezier(0.4, 0, 0.2, 1)
```

---

## Component Templates

### Button

```css
/* Primary Button */
.btn-primary {
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  font-weight: 700;
  cursor: pointer;
  transition: var(--transition-base);
  box-shadow: var(--shadow-lg);
}

.btn-primary:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-xl);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
```

### Input Field

```css
.form-input {
  padding: 12px 16px;
  border: 2px solid var(--border-light);
  border-radius: var(--radius-lg);
  font-size: 0.95rem;
  font-weight: 500;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: var(--transition-base);
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
  background: var(--primary-bg);
  box-shadow: 0 0 0 3px var(--primary-bg);
}

.form-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: var(--bg-secondary);
}
```

### Card

```css
.card {
  background: var(--bg-primary);
  border: 1.5px solid var(--border-light);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
  transition: var(--transition-base);
}

.card:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow-lg);
  transform: translateY(-6px);
}
```

### Status Badge

```css
/* Success Badge */
.badge-success {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: var(--success-bg);
  color: var(--success-dark);
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* Invalid Badge */
.badge-danger {
  background: var(--danger-bg);
  color: var(--danger-dark);
}

/* Warning Badge */
.badge-warning {
  background: var(--warning-bg);
  color: var(--warning-dark);
}
```

### Modal

```css
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  padding: var(--spacing-xl);
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideInFade 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## Animation Templates

### Fade In
```css
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.element {
  animation: fadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Slide In
```css
@keyframes slideInFade {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.element {
  animation: slideInFade 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Pulse (Loading)
```css
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.loading {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

### Spin (Loading)
```css
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spinner {
  animation: spin 1s linear infinite;
}
```

---

## Best Practices

### ✅ DO

1. **Use CSS Variables**
   ```css
   /* Good */
   background: var(--bg-primary);
   color: var(--text-primary);
   ```

2. **Use Consistent Spacing**
   ```css
   /* Good */
   padding: var(--spacing-lg);
   margin-bottom: var(--spacing-xl);
   gap: var(--spacing-md);
   ```

3. **Use Proper Border Radius**
   ```css
   /* Good */
   border-radius: var(--radius-lg);
   ```

4. **Use Smooth Transitions**
   ```css
   /* Good */
   transition: var(--transition-base);
   ```

5. **Use Professional Shadows**
   ```css
   /* Good */
   box-shadow: var(--shadow-md);
   ```

### ❌ DON'T

1. **Don't Hardcode Colors**
   ```css
   /* Bad */
   color: #111827;
   ```

2. **Don't Use Inconsistent Spacing**
   ```css
   /* Bad */
   padding: 15px;
   margin: 20px;
   gap: 13px;
   ```

3. **Don't Use Hard Edges**
   ```css
   /* Bad */
   border-radius: 0;
   ```

4. **Don't Make Things Instantly Appear**
   ```css
   /* Bad */
   transition: none;
   ```

5. **Don't Use Flat Design**
   ```css
   /* Bad */
   box-shadow: none;
   ```

---

## Responsive Design

Always include these breakpoints:

```css
/* Tablet */
@media (max-width: 1024px) {
  /* Adjust layouts, reduce spacing slightly */
}

/* Mobile */
@media (max-width: 768px) {
  /* Single column layouts, larger touch targets */
  .element {
    min-height: 44px; /* Touch target size */
  }
}

/* Small Mobile */
@media (max-width: 480px) {
  /* Minimal padding, simplified layouts */
}
```

---

## Dark Mode

All components should support dark mode:

```css
/* Default Light Mode */
.component {
  background: var(--bg-primary);
  color: var(--text-primary);
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  .component {
    /* Colors automatically adjust via CSS variables */
  }
}
```

The design system automatically supports dark mode when using CSS variables.

---

## Testing Your Styles

1. **Check responsiveness** - Test on mobile, tablet, and desktop
2. **Test dark mode** - Verify colors are readable
3. **Test accessibility** - Check color contrast (4.5:1 for text)
4. **Test animations** - Ensure smooth at 60fps
5. **Test focus states** - Verify keyboard navigation
6. **Test disabled states** - Ensure clear visual feedback

---

## Questions?

Refer to these files:
- **Variables:** `index.css` (lines 1-100)
- **Typography:** `index.css` (lines 100-150)
- **Components:** `App.css`, `BatchResultsPaginated.css`, `EmailComposer.css`
- **Responsive:** Check media queries at end of each file

The entire design system is production-ready and professionally maintained! 🎉

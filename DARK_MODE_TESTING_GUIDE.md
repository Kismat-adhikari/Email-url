# Dark Mode Testing Guide

## Visual Reference for Testing

### Light Mode (Default)
**Color Palette:**
- Background Primary: #ffffff (white)
- Background Secondary: #f9fafb (light gray)
- Text Primary: #1f2937 (dark gray)
- Text Secondary: #6b7280 (medium gray)
- Border: #eef2f7 (very light blue-gray)

**Visual Characteristics:**
- Clean, bright interface
- High contrast text
- Subtle shadows
- Professional appearance

### Dark Mode
**Color Palette:**
- Background Primary: #1a1a2e (very dark blue)
- Background Secondary: #252c3c (dark blue)
- Text Primary: #f1f5f9 (light blue-white)
- Text Secondary: #cbd5e1 (light gray-blue)
- Border: #3d4556 (dark gray-blue)

**Visual Characteristics:**
- Warm, low-light interface
- Readable light text on dark background
- Stronger shadows for depth
- Eye-friendly for extended use

## Component Checklist for Testing

### Dashboard Header
- [ ] Page title text color matches theme
- [ ] Background adapts to theme
- [ ] Dark mode button visible and functional

### Team Info Card
- [ ] Background changes with theme toggle
- [ ] "Team Information" heading is properly styled
- [ ] Team description text is readable in both modes
- [ ] Stats labels are secondary color
- [ ] Stats values are primary color and bold

### Quota Section
- [ ] "Team Quota" heading matches theme
- [ ] Progress bar background uses theme border color
- [ ] Quota labels are secondary color with good weight
- [ ] Usage percentages are clear and readable

### Member Cards
- [ ] Card backgrounds change with theme
- [ ] Borders are visible in both modes
- [ ] Member names are bold and primary color
- [ ] Email addresses use secondary color
- [ ] Role badges maintain blue accent
- [ ] Remove button remains red in both modes

### Modal/Forms
- [ ] Modal background adapts to theme
- [ ] Form labels use primary text color
- [ ] Input fields show theme colors
- [ ] Input focus states work in both modes
- [ ] Input text is readable in both themes

### Invitation Cards
- [ ] Card background is yellowish in light mode
- [ ] Card background is darker in dark mode
- [ ] Email is bold in both modes
- [ ] Date/expiry text uses secondary color

### Danger Zone
- [ ] Border line is visible in both modes
- [ ] "Danger Zone" heading is red
- [ ] Warning text uses secondary color
- [ ] Leave button is red and functional

### Loading States
- [ ] Skeleton lines use theme colors
- [ ] Skeleton cards match component backgrounds
- [ ] Loading animations are visible and smooth
- [ ] Shimmer effect is subtle but visible

### Error/Success Messages
- [ ] Error messages are readable (red on light)
- [ ] Success messages are readable (green on light)
- [ ] Both adapt appropriately in dark mode

## Dark Mode Toggle Testing

1. **Initial State**
   - Load page
   - Check localStorage has `darkMode: false`
   - Interface is in light mode

2. **Toggle to Dark**
   - Click moon icon button
   - Body should add `dark-mode` class
   - All colors should update smoothly
   - localStorage should update to `darkMode: true`
   - Check console for any CSS errors

3. **Toggle Back to Light**
   - Click sun icon button
   - Body should remove `dark-mode` class
   - All colors should revert smoothly
   - localStorage should update to `darkMode: false`

4. **Persistence**
   - Toggle dark mode on
   - Refresh page
   - Page should load in dark mode
   - Switch to light mode
   - Refresh page
   - Page should load in light mode

## Contrast Verification

### Light Mode
- Main text (#1f2937) on white: 12.6:1 ratio ✅ WCAG AAA
- Secondary text (#6b7280) on light gray (#f9fafb): ~4.5:1 ratio ✅ WCAG AA

### Dark Mode
- Main text (#f1f5f9) on dark (#1a1a2e): 10.2:1 ratio ✅ WCAG AAA
- Secondary text (#cbd5e1) on dark: ~5:1 ratio ✅ WCAG AA

All combinations meet WCAG AA standards minimum.

## Typography Testing

### Headings
- [ ] Page title (28px, 700): Bold and prominent
- [ ] Section headings (16-20px, 700): Clear hierarchy
- [ ] Label headings (16px, 700): Properly weighted

### Body Text
- [ ] Primary text (14px, 400): Default weight, readable
- [ ] Secondary text (14px, 400): Color distinguishes importance
- [ ] Labels (13px, 500): Slightly bolder than body
- [ ] Values (13px, 600): Bold to stand out
- [ ] Small text (12px): Clear but not too small

### Font Family
- All text uses Inter font via Google Fonts
- Fallback to system fonts if CDN unavailable

## Performance Notes

- CSS variables have minimal performance impact
- Transition effects are 200-300ms (snappy, not jarring)
- No JavaScript transitions (pure CSS)
- Dark mode class toggle is instant
- localStorage updates don't block rendering

## Known Limitations

1. **Accent Colors**: Some colors remain fixed:
   - Red button (#e74c3c, #c0392b hover)
   - Green benefit text (#27ae60)
   - Blue role badge (#3498db)
   - Quota gradient (green→orange→red)
   
   These don't change between modes as they're semantic colors.

2. **Invitation Card**: Has special dark mode override for yellow background
   - Light: #fffbeb with #fcd34d border
   - Dark: rgba(180, 83, 9, 0.2) with rgba(217, 119, 6, 0.4)

3. **Form Input Focus**: Blue accent (#3498db) remains fixed
   - This is a standard UI convention for focus states

## Browser Compatibility

- ✅ Chrome/Edge 49+
- ✅ Firefox 31+
- ✅ Safari 9.1+
- ✅ All modern versions

CSS variables are well-supported in all modern browsers.

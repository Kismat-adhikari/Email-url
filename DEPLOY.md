# 🚀 Render Deployment Guide

## Quick Deploy

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Click "New +"** → **"Web Service"**
3. **Connect your GitHub repo**: `Kismat-adhikari/Email-url`
4. **Render will auto-detect** the `render.yaml` configuration

## Manual Configuration (if needed)

### Build Settings
- **Build Command**: 
  ```bash
  pip install -r requirements.txt && cd frontend && npm install && npm run build
  ```

- **Start Command**:
  ```bash
  python app_anon_history.py
  ```

### Environment Variables
Add these in Render dashboard:

1. **SUPABASE_URL**: Your Supabase project URL
2. **SUPABASE_KEY**: Your Supabase anon/public key
3. **PYTHON_VERSION**: `3.12.0`

## After Deployment

Your app will be live at: `https://your-app-name.onrender.com`

### Features Included:
✅ Duplicate email remover
✅ Domain statistics
✅ CSV/JSON export
✅ Real-time progress bar with ETA
✅ Share results links
✅ Role-based email detection
✅ Disposable email detection
✅ Typo suggestions
✅ Risk scoring
✅ Bounce tracking

## Troubleshooting

If build fails:
1. Check Python version is 3.12
2. Verify Supabase credentials
3. Check build logs in Render dashboard

## Local Testing

```bash
# Backend
python app_anon_history.py

# Frontend (separate terminal)
cd frontend
npm start
```

Backend: http://localhost:5000
Frontend: http://localhost:3000

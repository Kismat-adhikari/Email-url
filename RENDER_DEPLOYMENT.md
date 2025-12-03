# Deploy to Render.com - Step by Step

Your app is now configured as a **single web service** that serves both the Flask API and React frontend together.

## Quick Deploy Steps

### 1. Go to Render Dashboard
Visit: https://dashboard.render.com/

### 2. Create New Web Service
- Click **"New +"** → **"Web Service"**
- Connect your GitHub account if not already connected
- Select repository: **`Kismat-adhikari/Email-url`**

### 3. Configure Service
Render should auto-detect settings from `render.yaml`, but verify:

- **Name**: `email-validator` (or your choice)
- **Environment**: `Python 3`
- **Branch**: `main`
- **Build Command**: 
  ```bash
  pip install -r requirements.txt && cd frontend && npm install && npm run build && cd ..
  ```
- **Start Command**: 
  ```bash
  gunicorn app:app
  ```
- **Instance Type**: `Free` (or paid for better performance)

### 4. Environment Variables (Optional)
Add these if needed:
- `PYTHON_VERSION`: `3.9.0`
- `NODE_VERSION`: `18.17.0`

### 5. Deploy!
- Click **"Create Web Service"**
- Wait 5-10 minutes for build to complete
- Watch the logs for any errors

### 6. Access Your App
Once deployed, you'll get a URL like:
```
https://email-validator.onrender.com
```

Visit this URL to see your full-stack app running!

## How It Works

1. **Build Process**:
   - Installs Python dependencies
   - Installs Node.js dependencies
   - Builds React app to `frontend/build/`
   - Flask serves the built React files

2. **Routing**:
   - `/` → React frontend
   - `/api/*` → Flask API endpoints
   - All other routes → React (for client-side routing)

3. **Single Service**:
   - No CORS issues
   - Simpler deployment
   - Lower cost (one service instead of two)

## Troubleshooting

### Build Fails
- Check logs in Render dashboard
- Verify `requirements.txt` has all dependencies
- Ensure `frontend/package.json` is correct

### App Won't Start
- Check start command is `gunicorn app:app`
- Verify `app.py` is in root directory
- Check logs for Python errors

### 404 Errors
- Ensure `frontend/build/` directory exists after build
- Check Flask static folder configuration
- Verify API routes start with `/api/`

## Free Tier Limitations

Render free tier:
- App sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- 750 hours/month free
- Upgrade to paid for always-on service

## Need Help?

Check the logs in Render dashboard for detailed error messages.

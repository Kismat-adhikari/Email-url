@echo off
echo ============================================================
echo Starting Flask Backend...
echo ============================================================
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting server on http://localhost:5000
echo.
python app.py

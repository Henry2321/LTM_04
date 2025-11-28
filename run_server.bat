@echo off
echo Starting Expense Management Server...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing dependencies...
pip install -r requirements.txt

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set JWT_SECRET_KEY=your-secret-key-here

REM Create database if not exists
echo Initializing database...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized!')"

REM Start the server
echo.
echo Starting server on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause
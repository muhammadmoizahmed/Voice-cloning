@echo off
echo ===================================
echo VoiceForge AI - Startup Script
echo ===================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate

REM Install/Update requirements
echo [INFO] Installing dependencies...
pip install -q -r requirements.txt

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found! Please install FFmpeg for video processing.
    echo Download from: https://ffmpeg.org/download.html
)

REM Create directories if they don't exist
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs
if not exist "models_cache" mkdir models_cache

echo.
echo ===================================
echo Starting VoiceForge AI Server...
echo ===================================
echo.
echo API will be available at:
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo.

REM Start server
python main.py

pause

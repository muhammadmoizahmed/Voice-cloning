#!/bin/bash

echo "==================================="
echo "VoiceForge AI - Startup Script"
echo "==================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found! Please install Python 3.10+"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Install/Update requirements
echo "[INFO] Installing dependencies..."
pip install -q -r requirements.txt

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "[WARNING] FFmpeg not found! Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  MacOS: brew install ffmpeg"
fi

# Create directories if they don't exist
mkdir -p uploads outputs models_cache

echo ""
echo "==================================="
echo "Starting VoiceForge AI Server..."
echo "==================================="
echo ""
echo "API will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo ""

# Start server
python main.py

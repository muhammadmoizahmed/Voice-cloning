@echo off
REM VoiceForge AI - Quick Deploy Script for Windows
REM This script deploys VoiceForge AI in demo mode without external API keys

echo 🚀 VoiceForge AI - Demo Deployment Script
echo ==========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop for Windows.
    echo Visit: https://docs.docker.com/desktop/windows/install/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose.
    echo Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

REM Create necessary directories
echo 📁 Creating directories...
if not exist backend\uploads mkdir backend\uploads
if not exist backend\outputs mkdir backend\outputs
if not exist nginx\ssl mkdir nginx\ssl

REM Copy demo environment file
echo ⚙️ Setting up environment...
if not exist .env (
    copy .env.demo .env >nul
    echo ✅ Created .env file with demo settings
) else (
    echo ⚠️ .env file already exists. Using existing configuration.
)

REM Build and start containers
echo 🐳 Building Docker containers...
docker-compose build

echo 🚀 Starting VoiceForge AI...
docker-compose up -d

REM Wait for services to start
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check if services are running
echo 🔍 Checking service status...
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo ✅ VoiceForge AI is running successfully!
    echo.
    echo 🌐 Access Points:
    echo    • Frontend: http://localhost
    echo    • Backend API: http://localhost/api
    echo    • API Docs: http://localhost/docs
    echo    • Health Check: http://localhost/health
    echo.
    echo 👤 Default Admin Login:
    echo    • Email: admin@voiceforge.ai
    echo    • Password: admin123
    echo.
    echo 📝 Demo Mode Features:
    echo    • ✅ Complete UI functionality
    echo    • ✅ User management
    echo    • ✅ Admin panel
    echo    • ✅ File upload/storage
    echo    • ❌ Real voice cloning (demo only)
    echo    • ❌ Real payments (demo only)
    echo    • ❌ Email sending (console only)
    echo.
    echo 🔧 Useful Commands:
    echo    • View logs: docker-compose logs -f
    echo    • Stop services: docker-compose down
    echo    • Restart services: docker-compose restart
    echo    • Update code: docker-compose up -d --build
    echo.
    echo 📚 Documentation:
    echo    • Complete Guide: DEPLOYMENT_GUIDE.md
    echo    • Architecture: ARCHITECTURE.md
    echo    • API Connections: API_CONNECTIONS.md
) else (
    echo ❌ Failed to start services. Check logs:
    docker-compose logs
    pause
    exit /b 1
)

echo 🎉 Deployment completed successfully!
echo Enjoy testing VoiceForge AI in demo mode!
pause

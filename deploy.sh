#!/bin/bash

# VoiceForge AI - Quick Deploy Script
# This script deploys VoiceForge AI in demo mode without external API keys

echo "🚀 VoiceForge AI - Demo Deployment Script"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads outputs nginx/ssl

# Copy demo environment file
echo "⚙️ Setting up environment..."
if [ ! -f .env ]; then
    cp .env.demo .env
    echo "✅ Created .env file with demo settings"
else
    echo "⚠️ .env file already exists. Using existing configuration."
fi

# Set proper permissions
echo "🔒 Setting permissions..."
chmod 755 backend/uploads
chmod 755 backend/outputs
chmod 644 .env

# Build and start containers
echo "🐳 Building Docker containers..."
docker-compose build

echo "🚀 Starting VoiceForge AI..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ VoiceForge AI is running successfully!"
    echo ""
    echo "🌐 Access Points:"
    echo "   • Frontend: http://localhost"
    echo "   • Backend API: http://localhost/api"
    echo "   • API Docs: http://localhost/docs"
    echo "   • Health Check: http://localhost/health"
    echo ""
    echo "👤 Default Admin Login:"
    echo "   • Email: admin@voiceforge.ai"
    echo "   • Password: admin123"
    echo ""
    echo "📝 Demo Mode Features:"
    echo "   • ✅ Complete UI functionality"
    echo "   • ✅ User management"
    echo "   • ✅ Admin panel"
    echo "   • ✅ File upload/storage"
    echo "   • ❌ Real voice cloning (demo only)"
    echo "   • ❌ Real payments (demo only)"
    echo "   • ❌ Email sending (console only)"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   • View logs: docker-compose logs -f"
    echo "   • Stop services: docker-compose down"
    echo "   • Restart services: docker-compose restart"
    echo "   • Update code: docker-compose up -d --build"
    echo ""
    echo "📚 Documentation:"
    echo "   • Complete Guide: DEPLOYMENT_GUIDE.md"
    echo "   • Architecture: ARCHITECTURE.md"
    echo "   • API Connections: API_CONNECTIONS.md"
else
    echo "❌ Failed to start services. Check logs:"
    docker-compose logs
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo "Enjoy testing VoiceForge AI in demo mode!"

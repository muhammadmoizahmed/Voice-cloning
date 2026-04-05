# VoiceForge AI - Quick Start Guide

## 🚀 One-Click Deployment (Demo Mode)

### Prerequisites
- Docker & Docker Compose installed
- Git (to clone repository)

### Quick Deploy

#### Linux/Mac:
```bash
# Clone repository
git clone <repository-url>
cd voiceforge-ai

# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

#### Windows:
```cmd
# Clone repository
git clone <repository-url>
cd voiceforge-ai

# Run deployment
deploy.bat
```

## 🎯 What You Get

### ✅ **Fully Functional Demo**
- Complete UI/UX experience
- User registration and login
- Admin panel with all features
- File upload and management
- Dashboard and analytics
- Mobile responsive design

### 🎭 **Demo Mode Features**
- **Voice Cloning**: Mock voice generation with demo files
- **Audio Generation**: Pre-generated demo audio samples
- **Avatar Videos**: Demo video generation with stock content
- **Payments**: Mock payment processing (accepts all transactions)
- **Email**: Console logging instead of real emails

### 👤 **Demo Users**
- **Admin**: admin@voiceforge.ai / admin123
- **User**: user@voiceforge.ai / user123

## 🌐 Access Points

After deployment, access the application at:

- **Frontend**: http://localhost
- **Backend API**: http://localhost/api
- **API Documentation**: http://localhost/docs
- **Health Check**: http://localhost/health

## 🔧 Manual Deployment

If you prefer manual setup:

### 1. Environment Setup
```bash
# Copy demo environment
cp .env.demo .env

# Create directories
mkdir -p backend/uploads backend/outputs nginx/ssl
```

### 2. Docker Deployment
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Setup Demo Data
```bash
# Run demo setup script
chmod +x setup-demo.sh
./setup-demo.sh
```

## 📱 Testing the Demo

### 1. **User Registration**
- Visit http://localhost
- Click "Sign Up"
- Enter email/password
- Verify OTP (auto-verified in demo mode)

### 2. **Voice Cloning Demo**
- Go to "Voice Library"
- Upload any audio file
- System will create a mock voice clone
- Try generating audio with the "cloned" voice

### 3. **Audio Generation Demo**
- Go to "Generate Audio"
- Select a demo voice
- Enter text
- Get pre-generated demo audio

### 4. **Avatar Video Demo**
- Go to "AI Avatar Video"
- Upload any image
- Enter text
- Get demo video output

### 5. **Admin Panel**
- Login as admin@voiceforge.ai / admin123
- Access all admin features
- Manage users, voices, plans
- View analytics and reports

## 🔍 Demo Limitations

### ❌ **Not Available in Demo Mode**
- Real voice cloning (mock only)
- Real audio generation (pre-generated files)
- Real payments (mock processing)
- Real email sending (console logs)
- External API integrations

### ⚠️ **Demo Data**
- All uploaded files are stored locally
- Database is SQLite (not production-ready)
- No real external service connections
- Mock API responses

## 🚀 Production Upgrade

When ready for production:

### 1. **Get Real API Keys**
- ElevenLabs API key
- Fish.Audio API key
- Resemble AI API key
- Stripe API keys
- Email service credentials

### 2. **Update Environment**
```bash
# Edit .env file
nano .env

# Add real API keys
ELEVENLABS_API_KEY=your-real-key
FISH_AUDIO_API_KEY=your-real-key
RESEMBLE_API_KEY=your-real-key
STRIPE_SECRET_KEY=your-stripe-key
# ... etc
```

### 3. **Disable Demo Mode**
```bash
# Set demo mode to false
DEMO_MODE=false
MOCK_API_CALLS=false
SKIP_EXTERNAL_APIS=false
```

### 4. **Restart Services**
```bash
docker-compose down
docker-compose up -d --build
```

## 📚 Documentation

- **[Complete Documentation](./PROJECT_DOCUMENTATION.md)** - Full project guide
- **[Deployment Guide](./DEPLOYMENT_GUIDE.md)** - Detailed deployment instructions
- **[Architecture Overview](./ARCHITECTURE.md)** - System architecture
- **[API Connections](./API_CONNECTIONS.md)** - External integrations

## 🛠️ Troubleshooting

### Common Issues

#### **Docker Issues**
```bash
# Check Docker status
docker --version
docker-compose --version

# Reset Docker
docker system prune -a
docker-compose down -v
docker-compose up -d --build
```

#### **Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep :80
netstat -tulpn | grep :8002

# Kill processes
sudo kill -9 <PID>
```

#### **Permission Issues**
```bash
# Fix file permissions
sudo chown -R $USER:$USER backend/
chmod -R 755 backend/
```

### Getting Help

1. **Check Logs**: `docker-compose logs -f`
2. **Health Check**: `curl http://localhost/health`
3. **API Status**: `curl http://localhost/api/info`
4. **Documentation**: See links above

## 🎉 Enjoy the Demo!

This demo gives you a complete experience of VoiceForge AI without needing any external API keys or services. Perfect for:

- 🎓 **Education & Learning**
- 🏢 **Corporate Demos**
- 💼 **Sales Presentations**
- 🔬 **Development & Testing**
- 🌐 **Website Showcases**

**Ready to go live? Just add your API keys and disable demo mode!** 🚀

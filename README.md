# VoiceForge AI - Complete Voice Cloning Platform

🚀 **Transform your voice into a digital, scalable asset with AI-powered voice cloning and audio generation**

VoiceForge AI is a comprehensive AI voice cloning platform that allows users to clone their voice, generate audio from text, and create AI avatar videos with advanced features like user management, subscription plans, and admin panels.

## ✨ Key Features

### 🎤 **Voice Cloning**
- Clone any voice with high accuracy
- Support for multiple voice providers (ElevenLabs, Fish.Audio, Resemble AI)
- Voice quality scoring and validation
- Ownership verification system

### 🎵 **Audio Generation**
- Text-to-speech with cloned voices
- Customizable audio parameters (stability, similarity boost)
- Batch processing capabilities
- Watermarking for copyright protection

### 🎭 **AI Avatar Videos**
- Face detection and validation
- Talking head video generation
- Lip-sync with generated audio
- Multiple aspect ratios support

### 💰 **Monetization Ready**
- Subscription-based pricing model
- Bulk credit packages
- Stripe payment integration
- Automated billing and webhooks

### 🛡️ **Enterprise Security**
- JWT-based authentication
- Role-based access control (RBAC)
- Email OTP verification
- Comprehensive audit logging

### 📱 **Modern UI/UX**
- Responsive mobile-first design
- Glassmorphism design system
- Real-time progress tracking
- Intuitive admin dashboard

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.9+)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Jinja2 + TailwindCSS + Vanilla JavaScript
- **Authentication**: JWT with email verification
- **File Storage**: Local filesystem (S3 compatible)
- **External APIs**: ElevenLabs, Fish.Audio, Resemble AI, Stripe

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+ (optional for frontend dev)
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd voiceforge-ai

# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# Initialize database
python -c "from app.database import create_tables; create_tables()"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### Environment Configuration

Create a `.env` file in the `backend` directory:

```bash
# Database
DATABASE_URL=sqlite:///./voiceforge.db

# JWT Secret (change in production!)
JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External API Keys
ELEVENLABS_API_KEY=your-elevenlabs-api-key
FISH_AUDIO_API_KEY=your-fish-audio-api-key
RESEMBLE_API_KEY=your-resemble-api-key

# Stripe Payment
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@voiceforge.ai
FROM_NAME=VoiceForge AI

# File Storage
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
MAX_UPLOAD_SIZE=52428800  # 50MB

# Frontend URL
FRONTEND_URL=http://localhost:8003

# Security
WATERMARK_ENABLED=true
REQUIRE_VOICE_OWNERSHIP=true
```

### Access Points

- **Frontend**: http://localhost:8003
- **Backend API**: http://localhost:8002
- **API Documentation**: http://localhost:8002/docs
- **Admin Panel**: http://localhost:8003/admin

## 📊 Pricing Model

### Subscription Plans
- **Free**: 3 audio generations, 1 voice clone, watermark
- **Starter**: $5/month, 50 audios, 3 voice clones, no watermark
- **Pro**: $15/month, 200 audios, 10 voice clones, API access
- **Business**: $30/month, 500 audios, 25 voice clones, team features

### Bulk Credit Packages
- **50 Credits**: $20 (save $30)
- **100 Credits**: $35 (save $65) - Most Popular
- **200 Credits**: $60 (save $140) - Best Value

## 🎯 User Roles

- **Guest**: Limited access, registration required
- **User**: Full voice cloning and generation features
- **Moderator**: Voice moderation and user management
- **Admin**: Complete system control and analytics

## 📚 Documentation

- **[Complete Documentation](./PROJECT_DOCUMENTATION.md)** - Comprehensive project guide
- **[Architecture Overview](./ARCHITECTURE.md)** - System architecture and design
- **[API Connections](./API_CONNECTIONS.md)** - External services and integrations

## 🔧 Development

### Project Structure
```
voiceforge-ai/
├── backend/
│   ├── app/
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── database.py       # Database models
│   │   ├── config.py         # Configuration
│   │   └── main.py           # FastAPI app
│   ├── templates/            # HTML templates
│   ├── static/               # CSS/JS assets
│   ├── uploads/              # User uploads
│   ├── outputs/              # Generated files
│   └── requirements.txt      # Python dependencies
├── PROJECT_DOCUMENTATION.md  # Complete documentation
├── ARCHITECTURE.md           # Architecture overview
├── API_CONNECTIONS.md        # API integrations
└── README.md                 # This file
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

### Database Management
```bash
# Create tables
python -c "from app.database import create_tables; create_tables()"

# Seed default plans
python -c "from app.database import seed_default_plans; seed_default_plans()"

# Reset database (dangerous!)
rm voiceforge.db
python -c "from app.database import create_tables; create_tables()"
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build Docker image
docker build -t voiceforge-ai .

# Run container
docker run -p 8002:8002 -p 8003:8003 voiceforge-ai
```

### Production Deployment
1. Set up PostgreSQL database
2. Configure Redis for caching
3. Set up S3 for file storage
4. Configure SSL certificates
5. Set up environment variables
6. Run with Gunicorn + Nginx

## 🔐 Security Features

- **Authentication**: JWT with secure cookies
- **Authorization**: Role-based access control
- **Data Protection**: Encrypted passwords, audit logging
- **File Security**: Upload validation, watermarking
- **API Security**: Rate limiting, input validation, CORS

## 📱 Mobile Support

- Fully responsive design
- Mobile-first approach
- Touch-friendly interface
- Collapsible navigation
- Optimized for all screen sizes

## 🤝 API Integrations

### Voice Services
- **ElevenLabs**: Primary voice cloning and TTS
- **Fish.Audio**: Alternative TTS service
- **Resemble AI**: Enhanced voice cloning

### Payment Processing
- **Stripe**: Payment processing and subscriptions
- **Webhooks**: Real-time payment updates

### Communication
- **SMTP**: Email notifications and OTP
- **Templates**: Transactional emails

## 📈 Monitoring & Analytics

- Built-in analytics dashboard
- User activity tracking
- Revenue monitoring
- System health checks
- Audit log viewing
- Performance metrics

## 🛠️ Troubleshooting

### Common Issues

1. **Voice cloning fails**
   - Check API keys in `.env`
   - Verify file format (MP3/WAV)
   - Check file size (< 50MB)

2. **Audio generation timeout**
   - Reduce text length
   - Check internet connection
   - Verify voice provider status

3. **Payment issues**
   - Verify Stripe configuration
   - Check webhook endpoints
   - Ensure domain is whitelisted

4. **Email not sending**
   - Check SMTP settings
   - Verify app password for Gmail
   - Check firewall settings

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=debug

# Run with verbose output
uvicorn app.main:app --reload --log-level debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and inquiries:

- **Email**: support@voiceforge.ai
- **Documentation**: [PROJECT_DOCUMENTATION.md](./PROJECT_DOCUMENTATION.md)
- **API Reference**: http://localhost:8002/docs
- **Status Page**: http://localhost:8002/health

## 🌟 Show Your Support

If you find this project useful, please give it a ⭐ on GitHub!

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Framework**: FastAPI + Jinja2 + TailwindCSS  
**Made with ❤️ by VoiceForge AI Team

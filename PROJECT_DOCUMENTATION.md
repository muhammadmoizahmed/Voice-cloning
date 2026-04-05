# VoiceForge AI - Complete Documentation

## 🎯 Overview

VoiceForge AI is a comprehensive AI voice cloning platform built with FastAPI backend and modern frontend. It allows users to clone their voice, generate audio from text, and create AI avatar videos with advanced features like user management, subscription plans, and admin panels.

## 🏗️ Architecture

### Backend Stack
- **Framework**: FastAPI (Python 3.9+)
- **Database**: SQLite (with SQLAlchemy ORM)
- **Authentication**: JWT with email OTP verification
- **File Storage**: Local filesystem (configurable to S3)
- **External APIs**: ElevenLabs, Fish.Audio, Resemble AI, Stripe
- **Email**: SMTP for OTP and notifications

### Frontend Stack
- **Templates**: Jinja2 with modern HTML5
- **Styling**: TailwindCSS with custom glassmorphism design
- **Icons**: Lucide Icons
- **JavaScript**: Vanilla JS with Axios for API calls
- **Responsive**: Mobile-first design with sidebar navigation

## 📊 Database Schema

### Core Tables

#### Users
```sql
- id (PK)
- email (unique)
- hashed_password
- full_name
- role (enum: guest, user, moderator, admin)
- plan (enum: free, starter, pro, business)
- total_audios_generated
- monthly_audios_used
- purchased_credits
- is_active, is_verified, email_verified
- consent_given, consent_date
- otp_code, otp_expires_at, is_otp_verified
- reset_token, reset_token_expires_at
- timestamps: created_at, updated_at, last_login
```

#### Voices
```sql
- id (PK)
- user_id (FK)
- name, description
- file_path, file_name, file_size, duration_seconds
- elevenlabs_voice_id
- is_active, is_default
- language, quality_score
- ownership_verified, ownership_notes
- timestamps: created_at, updated_at
```

#### Audio Generations
```sql
- id (PK)
- user_id (FK), voice_id (FK)
- script_text
- output_file_path, output_file_name
- duration_seconds, file_size
- language, stability, similarity_boost
- watermark_id, watermark_data
- status (pending, processing, completed, failed)
- error_message
- is_favorite, tags
- created_at
```

#### Plans
```sql
- id (PK)
- name (unique: FREE, STARTER, PRO, BUSINESS, CREDIT_*)
- display_name, description
- price_monthly, price_yearly, currency
- audio_limit, video_limit, voice_clone_limit
- features (JSON array)
- is_active, is_popular
- sort_order
- timestamps: created_at, updated_at
```

#### Payments
```sql
- id (PK)
- user_id (FK)
- plan (enum)
- amount, currency
- stripe_payment_intent_id, stripe_subscription_id
- status (pending, completed, failed, refunded)
- period_start, period_end
- created_at
```

#### Audit Logs
```sql
- id (PK)
- user_id (FK)
- action, resource_type, resource_id
- ip_address, user_agent, details (JSON)
- created_at
```

## 🚀 API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - User login
- `POST /verify-otp` - Email verification
- `POST /forgot-password` - Password reset request
- `POST /reset-password` - Password reset
- `GET /me` - Get current user info
- `POST /logout` - Logout

### Voices (`/api/v1/voices`)
- `GET /` - List user voices
- `POST /upload` - Upload and clone voice
- `GET /{id}` - Get voice details
- `PUT /{id}` - Update voice
- `DELETE /{id}` - Delete voice

### Generations (`/api/v1/generations`)
- `GET /` - List audio generations
- `POST /` - Generate audio from text
- `GET /{id}` - Get generation details
- `PUT /{id}` - Update generation
- `DELETE /{id}` - Delete generation
- `GET /{id}/download` - Download audio file

### Dashboard (`/api/v1/dashboard`)
- `GET /stats` - User statistics
- `GET /usage` - Usage reports
- `GET /recent` - Recent activity

### Payments (`/api/v1/payments`)
- `POST /create-checkout-session` - Stripe checkout
- `POST /webhook` - Stripe webhook
- `GET /` - Payment history

### Admin (`/api/v1/admin`)
- `GET /users` - List all users
- `GET /voices` - Voice moderation
- `POST /plans` - Create plan
- `GET /plans` - List plans
- `PUT /plans/{id}` - Update plan
- `DELETE /plans/{id}` - Delete plan
- `GET /analytics` - Platform analytics
- `GET /audit-logs` - System logs

### Face Detection (`/api/face-detection`)
- `POST /validate` - Validate face in image

## 🎨 Frontend Pages

### User Pages
- `/` - Landing page
- `/login` - User login
- `/signup` - User registration
- `/verify-otp` - Email verification
- `/forgot-password` - Password reset
- `/dashboard` - User dashboard
- `/voices` - Voice library
- `/generate` - Audio generation
- `/avatar` - AI avatar video
- `/history` - Generation history
- `/settings` - User settings
- `/upgrade` - Subscription plans

### Admin Pages
- `/admin/login` - Admin login
- `/admin` - Admin dashboard
- `/admin/users` - User management
- `/admin/voices` - Voice moderation
- `/admin/plans` - Plan management
- `/admin/settings` - Admin settings
- `/admin/sub-admins` - Sub-admin management

### Sub-Admin Pages
- `/sub-admin` - Sub-admin dashboard
- `/sub-admin/users` - User management (limited)
- `/sub-admin/voices` - Voice review
- `/sub-admin/reports` - Reports

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=sqlite:///./voiceforge.db

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External APIs
ELEVENLABS_API_KEY=your-elevenlabs-key
FISH_AUDIO_API_KEY=your-fish-audio-key
RESEMBLE_API_KEY=your-resemble-key

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@voiceforge.ai
FROM_NAME=VoiceForge AI

# File Paths
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
MAX_UPLOAD_SIZE=52428800  # 50MB

# Frontend
FRONTEND_URL=http://localhost:8003

# Security
WATERMARK_ENABLED=true
REQUIRE_VOICE_OWNERSHIP=true
```

## 🔐 Security Features

### Authentication
- JWT-based authentication with secure cookies
- Email OTP verification for account activation
- Password reset with secure tokens
- Role-based access control (RBAC)

### Data Protection
- Password hashing with bcrypt
- File upload validation (type, size)
- Watermarking for generated audio
- Audit logging for all actions

### API Security
- CORS middleware
- Rate limiting (configurable)
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy

## 💰 Pricing Model

### Subscription Plans
- **Free**: 3 audio generations, 1 voice clone, watermark
- **Starter**: $5/month, 50 audios, 3 voice clones, no watermark
- **Pro**: $15/month, 200 audios, 10 voice clones, API access
- **Business**: $30/month, 500 audios, 25 voice clones, team features

### Bulk Credit Packages
- **50 Credits**: $20 (save $30)
- **100 Credits**: $35 (save $65) - Most Popular
- **200 Credits**: $60 (save $140) - Best Value

### Cost Structure
- API Cost: $0.15 per audio (ElevenLabs)
- Selling Price: $1.00 per audio
- Profit Margin: 6.7x markup

## 🔄 User Flow

### Registration Flow
1. User signs up with email/password
2. OTP sent to email
3. User verifies OTP
4. Account activated, logged in
5. Redirected to dashboard

### Voice Cloning Flow
1. User uploads voice sample (MP3/WAV)
2. File validated and stored
3. Voice sent to external API (ElevenLabs/Fish.Audio)
4. Voice ID received and stored
5. Voice available for generation

### Audio Generation Flow
1. User selects voice and enters text
2. Usage limits checked
3. Text sent to TTS API
4. Audio generated and stored
5. Watermark applied (if needed)
6. Download link provided

### Payment Flow
1. User selects plan
2. Stripe checkout session created
3. User redirected to Stripe
4. Payment completed
5. Webhook updates user plan
6. Credits/subscription activated

## 🛠️ Development Setup

### Prerequisites
- Python 3.9+
- Node.js 16+ (for frontend dev)
- Git

### Backend Setup
```bash
# Clone repository
git clone <repo-url>
cd voiceforge-ai/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python -c "from app.database import create_tables; create_tables()"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### Frontend Setup
```bash
# Navigate to static directory
cd static

# Install dependencies (if using build tools)
npm install

# Run development server (if applicable)
npm run dev
```

### Access Points
- **Frontend**: http://localhost:8003
- **Backend API**: http://localhost:8002
- **API Docs**: http://localhost:8002/docs
- **Admin Panel**: http://localhost:8003/admin

## 📱 Mobile Responsiveness

### Responsive Features
- Mobile-first design approach
- Collapsible sidebar navigation
- Touch-friendly interface
- Responsive modals and forms
- Optimized for mobile devices

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

## 🔧 Deployment

### Production Deployment

#### Backend (FastAPI)
```bash
# Using Docker
docker build -t voiceforge-backend .
docker run -p 8002:8002 voiceforge-backend

# Using systemd (Linux)
sudo systemctl start voiceforge
sudo systemctl enable voiceforge
```

#### Frontend (Nginx)
```nginx
server {
    listen 8003;
    server_name localhost;
    
    location / {
        root /path/to/templates;
        try_files $uri $uri/ @backend;
    }
    
    location @backend {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /path/to/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Environment Configuration
- Production database (PostgreSQL)
- Redis for caching
- S3 for file storage
- CDN for static assets
- SSL certificates
- Domain configuration

## 📊 Monitoring & Analytics

### Built-in Analytics
- User registration tracking
- Voice upload statistics
- Audio generation metrics
- Payment analytics
- Usage patterns

### Admin Dashboard
- Real-time user statistics
- Revenue tracking
- System health monitoring
- Audit log viewing
- Performance metrics

### External Monitoring
- Error tracking (Sentry)
- Performance monitoring
- Uptime monitoring
- Log aggregation

## 🧪 Testing

### Test Coverage
- Unit tests for core functions
- Integration tests for API endpoints
- End-to-end tests for user flows
- Security tests for authentication

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## 🤝 API Integration

### Voice Service Providers
- **ElevenLabs**: Primary TTS service
- **Fish.Audio**: Alternative TTS service
- **Resemble AI**: Voice cloning service

### Payment Processing
- **Stripe**: Payment processing
- **Webhooks**: Real-time payment updates

### Email Service
- **SMTP**: Transactional emails
- **Templates**: OTP, notifications, password reset

## 📈 Scalability Considerations

### Database Optimization
- Indexing for frequently queried fields
- Connection pooling
- Query optimization
- Caching strategies

### File Storage
- CDN integration for static files
- S3 for audio files
- Compression for uploads
- Cleanup policies for old files

### API Performance
- Async operations
- Rate limiting
- Caching headers
- Load balancing

## 🔍 Troubleshooting

### Common Issues
1. **Voice cloning fails**: Check API keys and file format
2. **Audio generation timeout**: Increase timeout or check text length
3. **Payment issues**: Verify Stripe configuration
4. **Email not sending**: Check SMTP settings
5. **Database errors**: Check connection and permissions

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with hot reload
uvicorn app.main:app --reload --log-level debug
```

## 📝 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make your changes
4. Add tests
5. Submit pull request

## 📞 Support

For support and inquiries:
- Email: support@voiceforge.ai
- Documentation: /docs
- API Reference: /docs
- Status Page: /health

---

**Last Updated**: January 2024
**Version**: 1.0.0
**Framework**: FastAPI + Jinja2 + TailwindCSS

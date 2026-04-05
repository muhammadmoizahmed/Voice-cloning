# VoiceForge AI - Deployment Guide

## 🚀 Deployment Without API Keys

This guide helps you deploy VoiceForge AI without external API keys for testing and development purposes.

## 📋 Prerequisites

- **Server**: Linux/Windows with Docker installed
- **Domain**: Optional but recommended for production
- **SSL**: Let's Encrypt (recommended for production)

## 🔧 Configuration Setup

### 1. Environment Variables

Create a `.env` file without external API keys:

```bash
# Database
DATABASE_URL=sqlite:///./voiceforge.db

# JWT Secret (change in production!)
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External API Keys (leave empty for demo mode)
ELEVENLABS_API_KEY=
FISH_AUDIO_API_KEY=
RESEMBLE_API_KEY=

# Stripe Payment (leave empty for demo mode)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# Email Configuration (use demo mode)
SMTP_SERVER=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
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
REQUIRE_VOICE_OWNERSHIP=false  # Disabled for demo

# Demo Mode Settings
DEMO_MODE=true
MOCK_API_CALLS=true
SKIP_EXTERNAL_APIS=true
```

### 2. Demo Mode Configuration

The application will automatically detect missing API keys and switch to demo mode:

- **Voice Cloning**: Mock voice generation with sample files
- **Audio Generation**: Pre-generated demo audio files
- **Payments**: Mock payment processing
- **Email**: Console logging instead of actual emails

## 🐳 Docker Deployment

### 1. Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs

# Expose ports
EXPOSE 8002 8003

# Set environment variables
ENV PYTHONPATH=/app
ENV DEMO_MODE=true

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  voiceforge:
    build: .
    ports:
      - "8002:8002"
      - "8003:8003"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./voiceforge.db:/app/voiceforge.db
    environment:
      - DEMO_MODE=true
      - MOCK_API_CALLS=true
      - SKIP_EXTERNAL_APIS=true
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - voiceforge
    restart: unless-stopped
```

### 3. Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream voiceforge_backend {
        server voiceforge:8002;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security Headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # Frontend
        location / {
            proxy_pass http://voiceforge_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static Files
        location /static/ {
            proxy_pass http://voiceforge_backend;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API Endpoints
        location /api/ {
            proxy_pass http://voiceforge_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # File Downloads
        location /uploads/ {
            proxy_pass http://voiceforge_backend;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        location /outputs/ {
            proxy_pass http://voiceforge_backend;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## 🚀 Deployment Steps

### 1. Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create project directory
mkdir -p /opt/voiceforge
cd /opt/voiceforge
```

### 2. Deploy Application

```bash
# Clone repository (or copy files)
git clone <repository-url> .

# Set up environment
cp .env.example .env
# Edit .env with demo settings

# Build and run
docker-compose up -d --build

# Check status
docker-compose ps
docker-compose logs voiceforge
```

### 3. Setup SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🎭 Demo Mode Features

### What Works in Demo Mode

✅ **User Interface**
- Complete frontend functionality
- User registration and login
- Dashboard and navigation
- Admin panel access

✅ **Mock Features**
- Voice upload (stored locally)
- Audio generation (pre-generated samples)
- User management
- Plan management
- Analytics dashboard

✅ **File Management**
- File upload and storage
- Local file serving
- Download functionality

### What's Limited in Demo Mode

❌ **External API Features**
- Real voice cloning
- Real audio generation
- Payment processing
- Email notifications

❌ **Advanced Features**
- Real-time processing
- External service integration
- Live webhooks

## 🔍 Testing Demo Mode

### 1. Access Application

```bash
# Check if running
curl http://localhost:8002/health

# Should return:
{"status": "healthy", "timestamp": "..."}
```

### 2. Test User Registration

```bash
# Register a new user
curl -X POST http://localhost:8002/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","full_name":"Test User"}'
```

### 3. Test Admin Access

```bash
# Create admin user (manually in database)
python -c "
from app.database import SessionLocal, User, UserRole
db = SessionLocal()
admin = User(
    email='admin@example.com',
    hashed_password='$2b$12$...',  # Use bcrypt hash
    full_name='Admin User',
    role=UserRole.ADMIN,
    is_active=True,
    is_verified=True
)
db.add(admin)
db.commit()
"
```

## 📊 Monitoring Demo Mode

### Health Checks

```bash
# Application health
curl http://localhost:8002/health

# API info
curl http://localhost:8002/api/info
```

### Logs

```bash
# View logs
docker-compose logs voiceforge

# Follow logs
docker-compose logs -f voiceforge
```

### Database Access

```bash
# Access database
docker-compose exec voiceforge sqlite3 voiceforge.db

# View tables
.tables

# View users
SELECT * FROM users;
```

## 🔧 Production Considerations

### Security

1. **Change Default Credentials**
   - Update JWT secret key
   - Create strong admin passwords
   - Enable HTTPS

2. **Network Security**
   - Configure firewall
   - Use SSL certificates
   - Limit exposed ports

3. **Data Protection**
   - Regular database backups
   - File system backups
   - Access logging

### Performance

1. **Database Optimization**
   - Use PostgreSQL for production
   - Configure connection pooling
   - Add database indexes

2. **File Storage**
   - Use S3 or similar for file storage
   - Configure CDN for static assets
   - Implement file cleanup policies

3. **Caching**
   - Add Redis for session storage
   - Configure application caching
   - Use browser caching

### Scaling

1. **Horizontal Scaling**
   - Load balancer configuration
   - Multiple app instances
   - Database replication

2. **Resource Management**
   - Memory limits
   - CPU allocation
   - Disk space monitoring

## 🎯 Next Steps

### Add Real API Keys

When ready for production:

1. **Get API Keys**
   - ElevenLabs API key
   - Stripe API keys
   - Email service credentials

2. **Update Environment**
   - Add real API keys to .env
   - Disable demo mode
   - Restart services

3. **Configure Services**
   - Set up payment processing
   - Configure email templates
   - Test integrations

### Custom Development

1. **Add Custom Features**
   - Brand customization
   - Additional voice providers
   - Custom analytics

2. **Integration**
   - Third-party services
   - Custom APIs
   - Webhook endpoints

## 🆘 Troubleshooting

### Common Issues

1. **Container Won't Start**
   ```bash
   # Check logs
   docker-compose logs voiceforge
   
   # Check configuration
   docker-compose config
   ```

2. **Database Issues**
   ```bash
   # Reset database
   docker-compose down
   rm voiceforge.db
   docker-compose up -d
   ```

3. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tulpn | grep :8002
   
   # Change ports in docker-compose.yml
   ```

4. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER uploads/
   sudo chown -R $USER:$USER outputs/
   ```

### Getting Help

- **Documentation**: Check PROJECT_DOCUMENTATION.md
- **Logs**: Review application logs
- **Community**: GitHub Issues
- **Support**: Contact development team

---

**Demo mode allows you to test the complete application without external dependencies. Perfect for development, testing, and demonstrations!** 🚀

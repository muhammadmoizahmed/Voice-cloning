#!/bin/bash

# VoiceForge AI - Render Start Script
# This script runs on Render to initialize and start the application

echo "🚀 Starting VoiceForge AI on Render..."
echo "======================================"

# Set default values
export PORT=${PORT:-8002}
export DATABASE_URL=${DATABASE_URL:-sqlite:///./voiceforge.db}

# Create data directories if they don't exist
echo "📁 Creating data directories..."
mkdir -p /data/uploads /data/outputs
chmod 755 /data/uploads /data/outputs

# Initialize database if needed
echo "🗄️ Checking database..."
python3 -c "
from app.database import create_tables, seed_default_plans
import os

# Create tables
create_tables()
print('✅ Database tables created')

# Seed default plans if none exist
seed_default_plans()
print('✅ Default plans seeded')
"

# Create admin user if it doesn't exist
echo "👤 Checking admin user..."
python3 -c "
from app.database import SessionLocal, User, UserRole
from app.utils.auth import hash_password
import datetime
import os

db = SessionLocal()

# Check if admin exists
admin = db.query(User).filter(User.email == 'admin@voiceforge.ai').first()
if not admin:
    admin = User(
        email='admin@voiceforge.ai',
        hashed_password=hash_password('admin123'),
        full_name='Admin User',
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        email_verified=True,
        plan='business',
        created_at=datetime.datetime.utcnow()
    )
    db.add(admin)
    db.commit()
    print('✅ Admin user created: admin@voiceforge.ai / admin123')
else:
    print('✅ Admin user already exists')

db.close()
"

# Verify environment
echo "🔍 Environment check..."
echo "   PORT: $PORT"
echo "   DATABASE_URL: $DATABASE_URL"
echo "   DEMO_MODE: $DEMO_MODE"

# Start the application
echo "🌐 Starting application on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1

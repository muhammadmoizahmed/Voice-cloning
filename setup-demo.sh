#!/bin/bash

# VoiceForge AI - Demo Mode Setup Script
# This script adds demo data and mock functionality

echo "🎭 Setting up VoiceForge AI Demo Mode"
echo "====================================="

# Navigate to backend directory
cd backend

# Create demo admin user
echo "👤 Creating demo admin user..."
python3 -c "
from app.database import SessionLocal, User, UserRole
from app.utils.auth import hash_password
import datetime

db = SessionLocal()

# Check if admin already exists
existing_admin = db.query(User).filter(User.email == 'admin@voiceforge.ai').first()
if not existing_admin:
    admin = User(
        email='admin@voiceforge.ai',
        hashed_password=hash_password('admin123'),
        full_name='Demo Admin',
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        email_verified=True,
        plan='business',  # Give full access
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    db.add(admin)
    db.commit()
    print('✅ Demo admin user created')
else:
    print('⚠️ Demo admin user already exists')

db.close()
"

# Create demo regular user
echo "👤 Creating demo regular user..."
python3 -c "
from app.database import SessionLocal, User, UserRole
from app.utils.auth import hash_password
import datetime

db = SessionLocal()

# Check if user already exists
existing_user = db.query(User).filter(User.email == 'user@voiceforge.ai').first()
if not existing_user:
    user = User(
        email='user@voiceforge.ai',
        hashed_password=hash_password('user123'),
        full_name='Demo User',
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
        email_verified=True,
        plan='starter',
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    db.add(user)
    db.commit()
    print('✅ Demo regular user created')
else:
    print('⚠️ Demo regular user already exists')

db.close()
"

# Create demo voice files directory
echo "📁 Creating demo voice files..."
mkdir -p uploads/demo_voices

# Create demo audio files directory
echo "📁 Creating demo audio files..."
mkdir -p outputs/demo_audio

# Download or create demo files (placeholder)
echo "🎵 Setting up demo audio samples..."
cat > uploads/demo_voices/demo_voice_info.txt << EOF
Demo Voice Files
================

This directory contains demo voice files for testing.
In a real deployment, these would be actual voice recordings.

Demo Voices:
1. female_voice_1.wav - Female voice sample
2. male_voice_1.wav - Male voice sample
3. child_voice_1.wav - Child voice sample

Note: These are placeholder files. In demo mode, the application
will generate mock responses for voice cloning and audio generation.
EOF

# Create demo output files
cat > outputs/demo_audio/demo_output_info.txt << EOF
Demo Audio Outputs
==================

This directory contains demo audio generation outputs.
In a real deployment, these would be generated audio files.

Demo Outputs:
1. welcome_message.mp3 - Welcome message demo
2. sample_generation_1.mp3 - Sample audio generation
3. test_tts_output.mp3 - Text-to-speech demo

Note: These are placeholder files. In demo mode, the application
will serve pre-generated demo files for audio generation requests.
EOF

# Create demo images directory
echo "🖼️ Creating demo images..."
mkdir -p uploads/demo_images

# Create demo image info
cat > uploads/demo_images/demo_image_info.txt << EOF
Demo Images
===========

This directory contains demo images for avatar video generation.
In a real deployment, these would be user-uploaded face images.

Demo Images:
1. face_sample_1.jpg - Female face sample
2. face_sample_2.jpg - Male face sample
3. avatar_demo.png - Avatar demo image

Note: These are placeholder files. In demo mode, the application
will use stock images or generate mock responses for avatar video requests.
EOF

echo "✅ Demo mode setup completed!"
echo ""
echo "🎭 Demo Features Enabled:"
echo "   • Mock voice cloning (returns demo voice IDs)"
echo "   • Mock audio generation (serves demo audio files)"
echo "   • Mock payment processing (accepts all payments)"
echo "   • Mock email sending (logs to console)"
echo "   • Demo admin and regular users created"
echo ""
echo "👤 Demo Login Credentials:"
echo "   • Admin: admin@voiceforge.ai / admin123"
echo "   • User: user@voiceforge.ai / user123"
echo ""
echo "🚀 You can now start the application with:"
echo "   docker-compose up -d"
echo ""
echo "🌐 Access the application at: http://localhost"

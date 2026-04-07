#!/usr/bin/env python3
"""Auto-create admin user on startup"""
import sys
sys.path.insert(0, '/app')

try:
    from app.database import SessionLocal, User, UserRole
    from app.utils.auth import get_password_hash
    
    db = SessionLocal()
    try:
        # Check if admin exists
        existing = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if existing:
            print("✅ Admin user already exists")
            sys.exit(0)
        
        # Create admin - truncate password to 72 bytes for bcrypt
        password = "admin123"[:72]  # Ensure it's under 72 bytes
        admin = User(
            email="admin@voiceforge.ai",
            hashed_password=get_password_hash(password),
            full_name="Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            email_verified=True
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created: admin@voiceforge.ai / admin123")
    finally:
        db.close()
except Exception as e:
    print(f"⚠️ Error creating admin: {e}")
    print("⚠️ Continuing without admin creation...")
    # Don't exit with error - let the app start anyway
    sys.exit(0)

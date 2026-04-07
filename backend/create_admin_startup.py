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
        
        # Create admin
        admin = User(
            email="admin@voiceforge.ai",
            hashed_password=get_password_hash("admin123"),
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
    sys.exit(1)

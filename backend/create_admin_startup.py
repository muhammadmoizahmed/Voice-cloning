#!/usr/bin/env python3
"""Auto-create admin user on startup"""
import sys
import time
sys.path.insert(0, '/app')

try:
    from app.database import SessionLocal, User, UserRole, Base, engine
    from app.utils.auth import get_password_hash
    
    print("🔄 Checking/Creating database tables...")
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    print("✅ Tables checked/created")
    
    # Wait a moment for database to be ready
    time.sleep(2)
    
    db = SessionLocal()
    try:
        # Check if admin exists
        existing = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if existing:
            print(f"✅ Admin user already exists: {existing.email}")
            sys.exit(0)
        
        print("🔄 Creating admin user...")
        # Create admin - truncate password to 72 bytes for bcrypt
        password = "admin123"[:72]
        hashed = get_password_hash(password)
        print(f"🔄 Password hashed (length: {len(hashed)})")
        admin = User(
            email="admin@voiceforge.ai",
            hashed_password=hashed,
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
    import traceback
    traceback.print_exc()
    print("⚠️ Continuing without admin creation...")
    sys.exit(0)

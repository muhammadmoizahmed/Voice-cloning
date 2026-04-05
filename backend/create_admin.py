#!/usr/bin/env python3
"""
Admin User Creation Script

Usage:
    python create_admin.py email@example.com
    python create_admin.py email@example.com --create --password yourpassword
"""

import sys
import argparse
from app.database import SessionLocal, User, UserRole
from app.utils.auth import get_password_hash

def make_admin(email: str, create: bool = False, password: str = None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user and create:
            if not password:
                print("Error: --password required when creating new user")
                sys.exit(1)
            
            # Create new admin user
            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name="Admin User",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                email_verified=True
            )
            db.add(user)
            db.commit()
            print(f"✅ Admin user created: {email}")
            print(f"   Password: {password}")
            print(f"   Role: ADMIN")
            
        elif user:
            # Upgrade existing user to admin
            old_role = user.role.value
            user.role = UserRole.ADMIN
            db.commit()
            print(f"✅ User upgraded to admin: {email}")
            print(f"   Previous role: {old_role}")
            print(f"   New role: ADMIN")
        else:
            print(f"❌ User not found: {email}")
            print("   Use --create flag to create new admin user")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        db.close()

def list_admins():
    db = SessionLocal()
    try:
        admins = db.query(User).filter(User.role == UserRole.ADMIN).all()
        print(f"\n👑 Admin Users ({len(admins)} total):\n")
        for admin in admins:
            print(f"   • {admin.email} ({admin.full_name})")
            print(f"     Active: {admin.is_active} | Verified: {admin.is_verified}")
        print()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage admin users")
    parser.add_argument("email", nargs="?", help="User email")
    parser.add_argument("--create", action="store_true", help="Create new admin user")
    parser.add_argument("--password", help="Password for new admin user")
    parser.add_argument("--list", action="store_true", help="List all admin users")
    
    args = parser.parse_args()
    
    if args.list:
        list_admins()
    elif args.email:
        make_admin(args.email, args.create, args.password)
    else:
        parser.print_help()

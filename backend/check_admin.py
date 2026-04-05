#!/usr/bin/env python3
"""Create admin user for app_full_flask.py"""

import sys
import os
import hashlib

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_full_flask import app, db, Admin

with app.app_context():
    # Check if admin exists
    admin = Admin.query.filter_by(username='admin').first()
    
    if admin:
        print(f"Admin found: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Password hash: {admin.password}")
        
        # Verify password
        test_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        print(f"\nTest password 'admin123':")
        print(f"Expected hash: {test_hash}")
        print(f"Match: {admin.password == test_hash}")
    else:
        print("Admin not found! Creating default admin...")
        
        admin = Admin(
            username='admin',
            password=hashlib.sha256('admin123'.encode()).hexdigest(),
            email='admin@voiceforge.com',
            full_name='Administrator',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        
        print("\n✅ Default admin created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("Email: admin@voiceforge.com")

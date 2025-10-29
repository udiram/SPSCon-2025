#!/usr/bin/env python3
"""
Quick script to reset admin password
Run this on Railway to fix admin login
"""

from app import create_app
from models import db, User

def reset_admin():
    app = create_app()
    with app.app_context():
        # Try to find admin user
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            print("❌ Admin user not found! Creating new one...")
            admin = User(
                username='admin',
                email='admin@spscon2025.com',
                first_name='System',
                last_name='Administrator'
            )
            db.session.add(admin)
        
        # Set password
        admin.set_password('Admin97034122!')
        db.session.commit()
        
        print("✅ Admin password reset successfully!")
        print(f"   Username: admin")
        print(f"   Password: Admin97034122!")
        print(f"   Email: {admin.email}")
        print(f"   Is Admin: {admin.is_admin}")
        
        # Test password
        if admin.check_password('Admin97034122!'):
            print("✅ Password verification: SUCCESS")
        else:
            print("❌ Password verification: FAILED")

if __name__ == '__main__':
    reset_admin()


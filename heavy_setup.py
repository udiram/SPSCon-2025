#!/usr/bin/env python3
"""
Heavy setup operations - run AFTER app is deployed and healthy
This script can be run manually or as a one-time job
Does NOT block app startup
"""

import os
import sys
from app import create_app
from models import db, User, Poster
from sqlalchemy import text

def fix_password_hash_column():
    """Extend password_hash column to 255 chars if needed"""
    try:
        print("\n🔧 Checking password_hash column...")
        
        # Check if we need to resize
        user_count = User.query.count()
        if user_count == 0:
            print("   ✅ No users exist, column will be correct on first use")
            return True
        
        # Get database type
        db_url = os.environ.get('DATABASE_URL', '')
        
        if 'mysql' in db_url or 'postgresql' in db_url:
            print(f"   📊 Extending password_hash for {user_count} users...")
            
            if 'mysql' in db_url:
                sql = "ALTER TABLE user MODIFY COLUMN password_hash VARCHAR(255) NOT NULL"
            else:  # PostgreSQL
                sql = "ALTER TABLE user ALTER COLUMN password_hash TYPE VARCHAR(255)"
            
            db.session.execute(text(sql))
            db.session.commit()
            print("   ✅ Column extended successfully")
        else:
            print("   ℹ️  SQLite database, no ALTER needed")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Column resize warning: {e}")
        return False

def update_qr_codes():
    """Update QR codes for all posters"""
    try:
        print("\n📱 Updating QR codes...")
        
        from utils.qr_generator import generate_qr_code
        posters = Poster.query.all()
        
        updated = 0
        for poster in posters:
            try:
                qr_path = generate_qr_code(poster.id, poster.title)
                if qr_path:
                    poster.qr_code_path = qr_path
                    updated += 1
            except Exception as e:
                print(f"   ⚠️  Failed to generate QR for poster {poster.id}: {e}")
                continue
        
        db.session.commit()
        print(f"   ✅ Updated {updated}/{len(posters)} QR codes")
        return True
        
    except Exception as e:
        print(f"   ⚠️  QR code update warning: {e}")
        return False

def create_admin_user():
    """Create or reset admin user"""
    try:
        print("\n👤 Setting up admin user...")
        from models import User
        from werkzeug.security import generate_password_hash
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@spscon2025.com',
                first_name='System',
                last_name='Administrator'
            )
            admin.set_password('Admin97034122!')
            db.session.add(admin)
            print("   ✅ Admin user created")
        else:
            admin.set_password('Admin97034122!')
            print("   ✅ Admin password reset")
        
        db.session.commit()
        
        # Verify it works
        if admin.check_password('Admin97034122!'):
            print("   ✅ Admin login verified")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Admin user setup warning: {e}")
        db.session.rollback()
        return False

def run_heavy_setup():
    """Run all heavy setup operations"""
    print("🔨 Running heavy setup operations...")
    print("   (This may take 30-60 seconds)")
    
    app = create_app()
    
    with app.app_context():
        # Fix password hash column (slow on large tables)
        fix_password_hash_column()
        
        # Create/reset admin user (now that column is fixed)
        create_admin_user()
        
        # Update QR codes (slow with many posters)
        update_qr_codes()
        
        print("\n✅ Heavy setup complete!")
        print("   🔑 Admin login: username=admin, password=Admin97034122!")

if __name__ == '__main__':
    run_heavy_setup()


#!/usr/bin/env python3
"""
Railway Deployment Script for SPSCon 2025
Handles database migration and data preservation during deployment
Based on TradeGrade deployment structure
"""

import os
import sys
import json
from datetime import datetime
from models import db, User, Poster, Favorite, Visit, PresenterStatus
from app import create_app
from seed_data import import_excel_data, check_data_integrity
from utils.qr_generator import generate_qr_code
from werkzeug.security import generate_password_hash

def check_environment():
    """Check deployment environment and configuration"""
    print("🔍 Checking deployment environment...")
    
    # Check if we're in Railway
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
    print(f"   Railway Environment: {'Yes' if is_railway else 'No'}")
    
    # Check database URL
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        if 'mysql' in db_url:
            print("   Database: MySQL")
        elif 'postgresql' in db_url:
            print("   Database: PostgreSQL")
        else:
            print("   Database: Other")
    else:
        print("   Database: SQLite (fallback)")
    
    # Check secret key
    secret_key = os.getenv('SECRET_KEY')
    if secret_key and secret_key != 'dev-secret-key-change-in-production':
        print("   Secret Key: ✅ Configured")
    else:
        print("   Secret Key: ⚠️  Using default")
    
    return is_railway

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Checking for admin user...")
            
            # Check if admin user already exists
            admin = User.query.filter_by(username='admin').first()
            
            if admin:
                print(f"   Found existing admin: {admin.email}")
                # Admin exists, ALWAYS reset password to ensure it's correct
                print("   Resetting password to default...")
                admin.set_password('Admin97034122!')
                db.session.commit()
                
                # Verify password was set correctly
                if admin.check_password('Admin97034122!'):
                    print("✅ Admin user password VERIFIED and working!")
                    print(f"   Username: admin")
                    print(f"   Password: Admin97034122!")
                    print(f"   Email: {admin.email}")
                    print(f"   Is Admin: {admin.is_admin}")
                    print(f"   Login at: /login")
                    return True
                else:
                    print("❌ Password verification failed!")
                    return False
            
            # Create new admin user
            print("   No admin found, creating new one...")
            admin = User(
                username='admin',  # This makes is_admin property return True
                email='admin@spscon2025.com',
                first_name='System',
                last_name='Administrator'
            )
            admin.set_password('Admin97034122!')
            
            db.session.add(admin)
            db.session.commit()
            
            # Verify new admin works
            admin = User.query.filter_by(username='admin').first()
            if admin and admin.check_password('Admin97034122!'):
                print("✅ New admin user created and VERIFIED!")
                print(f"   Username: admin")
                print(f"   Password: Admin97034122!")
                print(f"   Email: {admin.email}")
                print(f"   Is Admin: {admin.is_admin}")
                print(f"   Login at: /login")
                return True
            else:
                print("❌ Admin created but verification failed!")
                return False
            
        except Exception as e:
            print(f"❌ Error with admin user: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

def update_qr_codes():
    """Update QR codes for all posters with correct domain"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get base URL based on environment
            if os.getenv('RAILWAY_ENVIRONMENT'):
                base_url = "https://spscon2025.up.railway.app"
            else:
                base_url = "http://localhost:5000"
            
            # Get all posters
            posters = Poster.query.all()
            print(f"🔄 Updating QR codes for {len(posters)} posters...")
            
            updated_count = 0
            for poster in posters:
                # Generate new QR code with correct URL
                qr_data = f"{base_url}/poster/{poster.poster_number}"
                poster.qr_code_data = generate_qr_code(qr_data)
                updated_count += 1
            
            # Commit all changes
            db.session.commit()
            print(f"✅ Updated {updated_count} QR codes with base URL: {base_url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating QR codes: {e}")
            db.session.rollback()
            return False

def seed_database():
    """Seed the database with poster data if it's empty"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if database already has data
            poster_count = Poster.query.count()
            
            if poster_count > 0:
                print(f"📊 Database already has {poster_count} posters, skipping seeding")
                return True
            
            print("🌱 Database is empty, starting data seeding...")
            
            # Check if Excel file exists
            excel_file = "2025 SPSCon Poster Assignments_Student View.xlsx"
            if not os.path.exists(excel_file):
                print(f"⚠️  Excel file '{excel_file}' not found")
                print("   Data seeding skipped - you can import data later via admin panel")
                return True
            
            # Import data from Excel
            print(f"📥 Importing data from {excel_file}...")
            imported_count = import_excel_data(excel_file)
            
            if imported_count > 0:
                print(f"✅ Successfully imported {imported_count} posters")
                
                # Verify data integrity
                print("🔍 Verifying data integrity...")
                check_data_integrity()
                
                return True
            else:
                print("❌ No data imported from Excel file")
                return False
                
        except Exception as e:
            print(f"❌ Error during database seeding: {e}")
            import traceback
            traceback.print_exc()
            return False

def backup_data():
    """Create a backup of existing data before migration"""
    app = create_app()
    
    with app.app_context():
        try:
            from sqlalchemy import text
            
            backup = {
                'users': [],
                'posters': [],
                'favorites': [],
                'visits': [],
                'presenter_statuses': []
            }
            
            # Backup users using raw SQL to avoid model field issues
            try:
                # Try to get users with new model (includes is_admin)
                for user in User.query.all():
                    user_data = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'password_hash': user.password_hash,
                        'created_at': user.created_at.isoformat() if user.created_at else None
                    }
                    # Only include is_admin if it exists
                    try:
                        user_data['is_admin'] = user.is_admin
                    except AttributeError:
                        user_data['is_admin'] = False
                    
                    backup['users'].append(user_data)
            except Exception as e:
                # If model query fails (e.g., column doesn't exist), use raw SQL
                print(f"   Model query failed, using raw SQL for user backup: {e}")
                with db.engine.connect() as conn:
                    result = conn.execute(text(
                        "SELECT id, username, email, first_name, last_name, password_hash, created_at FROM user"
                    ))
                    for row in result:
                        backup['users'].append({
                            'id': row[0],
                            'username': row[1],
                            'email': row[2],
                            'first_name': row[3],
                            'last_name': row[4],
                            'password_hash': row[5],
                            'is_admin': False,  # Default for old data
                            'created_at': row[6].isoformat() if row[6] else None
                        })
            
            # Backup posters
            for poster in Poster.query.all():
                backup['posters'].append({
                    'id': poster.id,
                    'poster_number': poster.poster_number,
                    'session': poster.session,
                    'first_name': poster.first_name,
                    'last_name': poster.last_name,
                    'institution': poster.institution,
                    'title': poster.title,
                    'category': poster.category,
                    'tags': poster.tags,
                    'qr_code_data': poster.qr_code_data,
                    'presenter_id': poster.presenter_id
                })
            
            # Backup favorites
            for fav in Favorite.query.all():
                backup['favorites'].append({
                    'id': fav.id,
                    'user_id': fav.user_id,
                    'poster_id': fav.poster_id,
                    'created_at': fav.created_at.isoformat() if fav.created_at else None
                })
            
            # Backup visits
            for visit in Visit.query.all():
                backup['visits'].append({
                    'id': visit.id,
                    'user_id': visit.user_id,
                    'poster_id': visit.poster_id,
                    'visited_at': visit.visited_at.isoformat() if visit.visited_at else None
                })
            
            # Backup presenter statuses
            for status in PresenterStatus.query.all():
                backup['presenter_statuses'].append({
                    'id': status.id,
                    'user_id': status.user_id,
                    'poster_id': status.poster_id,
                    'is_available': status.is_available,
                    'last_updated': status.last_updated.isoformat() if status.last_updated else None
                })
            
            # Save backup to file
            with open('data_backup.json', 'w') as f:
                json.dump(backup, f, indent=2)
            
            print(f"Backup created: {len(backup['users'])} users, {len(backup['posters'])} posters")
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

def restore_data():
    """Restore data from backup after migration"""
    app = create_app()
    
    if not os.path.exists('data_backup.json'):
        print("No backup file found, skipping restore")
        return True
    
    with app.app_context():
        try:
            with open('data_backup.json', 'r') as f:
                backup = json.load(f)
            
            # Clear existing data
            db.session.query(PresenterStatus).delete()
            db.session.query(Visit).delete()
            db.session.query(Favorite).delete()
            db.session.query(Poster).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            # Restore users
            for user_data in backup['users']:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    password_hash=user_data['password_hash'],
                    is_admin=user_data.get('is_admin', False)
                )
                user.id = user_data['id']  # Preserve original ID
                if user_data.get('created_at'):
                    from datetime import datetime
                    user.created_at = datetime.fromisoformat(user_data['created_at'])
                db.session.add(user)
            
            db.session.commit()
            
            # Restore posters
            for poster_data in backup['posters']:
                poster = Poster(
                    poster_number=poster_data['poster_number'],
                    session=poster_data['session'],
                    first_name=poster_data['first_name'],
                    last_name=poster_data['last_name'],
                    institution=poster_data['institution'],
                    title=poster_data['title'],
                    category=poster_data['category'],
                    tags=poster_data['tags'],
                    qr_code_data=poster_data['qr_code_data'],
                    presenter_id=poster_data['presenter_id']
                )
                poster.id = poster_data['id']  # Preserve original ID
                db.session.add(poster)
            
            db.session.commit()
            
            # Restore favorites
            for fav_data in backup['favorites']:
                favorite = Favorite(
                    user_id=fav_data['user_id'],
                    poster_id=fav_data['poster_id']
                )
                if fav_data['created_at']:
                    from datetime import datetime
                    favorite.created_at = datetime.fromisoformat(fav_data['created_at'])
                db.session.add(favorite)
            
            # Restore visits
            for visit_data in backup['visits']:
                visit = Visit(
                    user_id=visit_data['user_id'],
                    poster_id=visit_data['poster_id']
                )
                if visit_data['visited_at']:
                    from datetime import datetime
                    visit.visited_at = datetime.fromisoformat(visit_data['visited_at'])
                db.session.add(visit)
            
            # Restore presenter statuses
            for status_data in backup['presenter_statuses']:
                status = PresenterStatus(
                    user_id=status_data['user_id'],
                    poster_id=status_data['poster_id'],
                    is_available=status_data['is_available']
                )
                if status_data.get('last_updated'):
                    from datetime import datetime
                    status.last_updated = datetime.fromisoformat(status_data['last_updated'])
                db.session.add(status)
            
            db.session.commit()
            
            print(f"Data restored: {len(backup['users'])} users, {len(backup['posters'])} posters")
            
            # Clean up backup file
            os.remove('data_backup.json')
            return True
            
        except Exception as e:
            print(f"Error restoring data: {e}")
            return False

def migrate_database():
    """Safe database migration that preserves data"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🗄️  Starting database migration...")
            
            # Check if database exists and has data
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            has_data = False
            if 'poster' in existing_tables:
                try:
                    poster_count = Poster.query.count()
                    has_data = poster_count > 0
                    print(f"   Found {poster_count} existing posters")
                except Exception as e:
                    print(f"   Could not count posters: {e}")
                    has_data = False
            
            if has_data:
                print("📦 Database has existing data, creating backup...")
                if not backup_data():
                    print("❌ Backup failed, aborting migration")
                    return False
            
            # Create/update tables
            print("🔨 Creating/updating database tables...")
            db.create_all()
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            current_tables = inspector.get_table_names()
            expected_tables = {'user', 'poster', 'favorite', 'visit', 'presenter_status'}
            
            missing_tables = expected_tables - set(current_tables)
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            
            print(f"✅ All tables created: {current_tables}")
            
            # Fix password_hash column length if needed (before creating admin)
            # Skip if no users exist - no need to modify empty table
            print("\n🔧 Checking password_hash column length...")
            user_count = User.query.count()
            
            if user_count == 0:
                print("   ℹ️  No users exist, skipping column resize (will be correct on first use)")
            else:
                try:
                    from sqlalchemy import text
                    with db.engine.connect() as conn:
                        db_type = db.engine.dialect.name
                        
                        if db_type in ['mysql', 'mariadb']:
                            print(f"   Extending password_hash to VARCHAR(255) for {user_count} users...")
                            conn.execute(text(
                                "ALTER TABLE user MODIFY COLUMN password_hash VARCHAR(255) NOT NULL"
                            ))
                            conn.commit()
                            print("   ✅ Password hash column extended")
                        elif db_type == 'postgresql':
                            print(f"   Extending password_hash to VARCHAR(255) for {user_count} users...")
                            conn.execute(text(
                                "ALTER TABLE user ALTER COLUMN password_hash TYPE VARCHAR(255)"
                            ))
                            conn.commit()
                            print("   ✅ Password hash column extended")
                        else:
                            print("   ℹ️  SQLite doesn't need column resize")
                except Exception as e:
                    print(f"   ⚠️  Column resize failed: {str(e)[:100]}")
                    print("   ⚠️  Skipping - will try again on next deploy")
                    # Don't fail deployment, just continue
            
            if has_data:
                print("📥 Restoring data from backup...")
                if not restore_data():
                    print("❌ Restore failed, but tables are created")
                    return False
            else:
                # No existing data, try to seed the database
                print("🌱 No existing data found, attempting to seed database...")
                if not seed_database():
                    print("⚠️  Database seeding failed, but tables are created")
                    print("   You can import data later via admin panel")
            
            # Update QR codes for all posters (new or existing)
            print("🔄 Updating QR codes with correct domain...")
            if not update_qr_codes():
                print("⚠️  QR code update failed, but migration continues")
            
            # Create/update default admin user (always at the end)
            print("\n👤 Setting up admin user...")
            print("=" * 50)
            if not create_default_admin():
                print("⚠️  Failed to create admin user, but migration continues")
            print("=" * 50)
            
            print("✅ Database migration completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            import traceback
            traceback.print_exc()
            return False

def check_deployment_environment():
    """Check if we're in Railway deployment environment"""
    return os.getenv('RAILWAY_ENVIRONMENT') is not None

def main():
    """Main deployment function"""
    print("🚀 SPSCon 2025 Railway Deployment Script")
    print("=" * 50)
    
    # Check environment
    is_railway = check_environment()
    
    print(f"\n🌍 Environment: {'Railway Production' if is_railway else 'Local Development'}")
    
    # Run migration
    print("\n📊 Starting database migration...")
    success = migrate_database()
    
    if success:
        print("\n🎉 Deployment preparation completed successfully!")
        print("✅ Ready to start Flask application")
        return True
    else:
        print("\n💥 Deployment preparation failed!")
        print("❌ Check logs above for details")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

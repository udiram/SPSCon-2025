#!/usr/bin/env python3
"""
Migration script for user profile enhancements.
Adds new columns to user_settings and creates Connection table.
Safe to run multiple times - checks for existing columns/tables.
"""

import os
import sys
from app import create_app
from models import db

def migrate_user_settings_columns():
    """Add new columns to user_settings table if they don't exist"""
    try:
        from sqlalchemy import text
        
        # Get database type
        db_type = db.engine.dialect.name
        print(f"   Database type: {db_type}")
        
        # Check existing columns
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user_settings')]
        print(f"   Existing columns: {len(columns)}")
        
        added_columns = []
        
        with db.engine.connect() as conn:
            # Add show_presented_posters if missing
            if 'show_presented_posters' not in columns:
                print("   Adding show_presented_posters column...")
                
                if db_type == 'sqlite':
                    conn.execute(text(
                        "ALTER TABLE user_settings ADD COLUMN show_presented_posters BOOLEAN DEFAULT 1"
                    ))
                elif db_type in ['mysql', 'mariadb']:
                    conn.execute(text(
                        "ALTER TABLE user_settings ADD COLUMN show_presented_posters TINYINT(1) DEFAULT 1"
                    ))
                elif db_type == 'postgresql':
                    conn.execute(text(
                        "ALTER TABLE user_settings ADD COLUMN show_presented_posters BOOLEAN DEFAULT TRUE"
                    ))
                
                conn.commit()
                added_columns.append('show_presented_posters')
                print("      ✓ Added show_presented_posters")
            
            # Add show_research_interests if missing
            if 'show_research_interests' not in columns:
                print("   Adding show_research_interests column...")
                
                if db_type == 'sqlite':
                    conn.execute(text(
                        "ALTER TABLE user_settings ADD COLUMN show_research_interests BOOLEAN DEFAULT 1"
                    ))
                elif db_type in ['mysql', 'mariadb']:
                    conn.execute(text(
                        "ALTER TABLE user_settings ADD COLUMN show_research_interests TINYINT(1) DEFAULT 1"
                    ))
                elif db_type == 'postgresql':
                    conn.execute(text(
                        "ALTER TABLE user_settings ADD COLUMN show_research_interests BOOLEAN DEFAULT TRUE"
                    ))
                
                conn.commit()
                added_columns.append('show_research_interests')
                print("      ✓ Added show_research_interests")
        
        if added_columns:
            print(f"   ✅ Added {len(added_columns)} new columns")
        else:
            print("   ✓ All columns already exist")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error migrating user_settings: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_connection_table():
    """Create Connection table if it doesn't exist"""
    try:
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'connection' in tables:
            print("   ✓ Connection table already exists")
            return True
        
        print("   Creating Connection table...")
        # Use db.create_all() which will only create missing tables
        db.create_all()
        
        # Verify it was created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'connection' in tables:
            print("   ✅ Connection table created successfully")
            return True
        else:
            print("   ❌ Connection table creation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error creating Connection table: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all migrations"""
    print("=" * 60)
    print("🔄 User Profile & Networking Migration")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        success = True
        
        # Check if user_settings table exists
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'user_settings' not in tables:
            print("\n⚠️  user_settings table doesn't exist yet")
            print("   This migration will run automatically after base tables are created")
            return True  # Not an error, just too early
        
        # Migrate user_settings columns
        print("\n1️⃣  Updating user_settings table...")
        if not migrate_user_settings_columns():
            success = False
        
        # Create connection table
        print("\n2️⃣  Creating Connection table...")
        if not create_connection_table():
            success = False
        
        # Verify all changes
        print("\n🔍 Verification:")
        
        # Check user_settings columns
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user_settings')]
        
        required_columns = ['show_presented_posters', 'show_research_interests']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"   ❌ Missing columns: {missing_columns}")
            success = False
        else:
            print("   ✅ All user_settings columns present")
        
        # Check connection table
        if 'connection' in inspector.get_table_names():
            print("   ✅ Connection table exists")
        else:
            print("   ❌ Connection table missing")
            success = False
        
        if success:
            print("\n" + "=" * 60)
            print("✅ Migration completed successfully!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ Migration completed with errors")
            print("=" * 60)
        
        return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Migration failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



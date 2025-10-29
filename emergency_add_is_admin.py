#!/usr/bin/env python3
"""
Emergency script to add is_admin column directly
Run this if normal migrations fail
"""

import os
import sys

def add_is_admin_column():
    """Add is_admin column using raw SQL"""
    # Import here to avoid model loading issues
    from sqlalchemy import create_engine, text
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL', 'sqlite:///spscon.db')
    
    # Handle mysql2:// prefix from Railway
    if database_url.startswith('mysql2://'):
        database_url = database_url.replace('mysql2://', 'mysql+pymysql://', 1)
    
    print(f"Connecting to database...")
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("SELECT is_admin FROM user LIMIT 1"))
            print("✅ Column 'is_admin' already exists!")
            return True
        except Exception as e:
            print(f"Column doesn't exist, adding it...")
            
            # Detect database type
            db_type = engine.dialect.name
            print(f"Database type: {db_type}")
            
            # Add column based on database type
            try:
                if db_type in ['mysql', 'mariadb']:
                    conn.execute(text(
                        "ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL"
                    ))
                elif db_type == 'postgresql':
                    conn.execute(text(
                        "ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL"
                    ))
                elif db_type == 'sqlite':
                    conn.execute(text(
                        "ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL"
                    ))
                
                conn.commit()
                print("✅ Successfully added is_admin column!")
                
                # Verify
                result = conn.execute(text("SELECT COUNT(*) FROM user"))
                user_count = result.scalar()
                print(f"✅ Verified: {user_count} users can now have admin status")
                return True
                
            except Exception as add_error:
                print(f"❌ Error adding column: {add_error}")
                return False

if __name__ == '__main__':
    print("🚨 Emergency Migration: Adding is_admin Column")
    print("=" * 50)
    
    success = add_is_admin_column()
    
    if success:
        print("\n✅ SUCCESS! The is_admin column has been added.")
        print("You can now restart your application.")
        sys.exit(0)
    else:
        print("\n❌ FAILED! Please check the error above.")
        sys.exit(1)


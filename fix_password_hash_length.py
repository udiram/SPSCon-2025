#!/usr/bin/env python3
"""
Migration script to fix password_hash column length
"""

from app import create_app
from models import db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        try:
            # Alter the password_hash column to be longer
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE user MODIFY COLUMN password_hash VARCHAR(255) NOT NULL"))
                conn.commit()
            print("✅ Password hash column updated to VARCHAR(255)")
            
            # Also add the change_request table if it doesn't exist
            db.create_all()
            print("✅ ChangeRequest table created (if not exists)")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            print("This might be okay if using SQLite (column already correct) or if change already applied")
        
if __name__ == '__main__':
    migrate()


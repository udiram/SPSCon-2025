#!/usr/bin/env python3
"""
Quick initialization script - FAST startup only
Only does essential operations, defers everything else
"""

import os
import sys
from app import create_app
from models import db

def quick_init():
    """Fast initialization - only create tables if needed"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if tables exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'user' in existing_tables and 'poster' in existing_tables:
                print("✅ Tables already exist, skipping creation")
                return True
            
            # Create tables if they don't exist
            print("🔨 Creating database tables...")
            db.create_all()
            print("✅ Tables created")
            return True
            
        except Exception as e:
            print(f"⚠️  Initialization warning: {e}")
            # Don't fail - app can still start
            return True

if __name__ == '__main__':
    print("🚀 Quick initialization...")
    success = quick_init()
    sys.exit(0 if success else 1)


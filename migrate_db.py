from models import db
from app import create_app
import os

def migrate_db():
    """Check for schema changes and apply migrations"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if database exists
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"Existing tables: {existing_tables}")
            
            # Create all tables (this will only create missing ones)
            db.create_all()
            
            # Check what was created
            inspector = db.inspect(db.engine)
            current_tables = inspector.get_table_names()
            
            new_tables = set(current_tables) - set(existing_tables)
            if new_tables:
                print(f"Created new tables: {new_tables}")
            else:
                print("No new tables needed")
            
            return True
            
        except Exception as e:
            print(f"Error during migration: {e}")
            return False

def check_schema_version():
    """Check current schema version"""
    app = create_app()
    
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            # Expected tables
            expected_tables = {'user', 'poster', 'favorite', 'visit', 'presenter_status'}
            missing_tables = expected_tables - set(tables)
            
            if missing_tables:
                print(f"Missing tables: {missing_tables}")
                return False
            else:
                print("All required tables present")
                return True
                
        except Exception as e:
            print(f"Error checking schema: {e}")
            return False

if __name__ == "__main__":
    print("Checking database schema...")
    
    if check_schema_version():
        print("Schema is up to date")
    else:
        print("Applying migrations...")
        migrate_db()


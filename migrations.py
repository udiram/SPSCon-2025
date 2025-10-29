#!/usr/bin/env python3
"""
Database migrations system
Tracks which migrations have been run and only runs new ones
"""

from app import create_app
from models import db
from sqlalchemy import text, inspect
from datetime import datetime

class MigrationRunner:
    def __init__(self):
        self.app = create_app()
        
    def ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        with self.app.app_context():
            with db.engine.connect() as conn:
                # Check if migrations table exists
                inspector = inspect(db.engine)
                if 'migrations' not in inspector.get_table_names():
                    db_type = db.engine.dialect.name
                    
                    # SQLite uses AUTOINCREMENT, MySQL uses AUTO_INCREMENT
                    if db_type == 'sqlite':
                        create_sql = """
                            CREATE TABLE migrations (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                migration_name VARCHAR(255) UNIQUE NOT NULL,
                                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """
                    else:
                        create_sql = """
                            CREATE TABLE migrations (
                                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                                migration_name VARCHAR(255) UNIQUE NOT NULL,
                                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """
                    
                    conn.execute(text(create_sql))
                    conn.commit()
                    print("✅ Created migrations tracking table")
    
    def has_run(self, migration_name):
        """Check if a migration has already been run"""
        with self.app.app_context():
            with db.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM migrations WHERE migration_name = :name"),
                    {"name": migration_name}
                )
                return result.scalar() > 0
    
    def mark_as_run(self, migration_name):
        """Mark a migration as completed"""
        with self.app.app_context():
            with db.engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO migrations (migration_name) VALUES (:name)"),
                    {"name": migration_name}
                )
                conn.commit()
                print(f"✅ Marked migration '{migration_name}' as completed")
    
    def run_migration_001_password_hash_length(self):
        """Migration 001: Increase password_hash column length to 255"""
        migration_name = "001_password_hash_length"
        
        if self.has_run(migration_name):
            print(f"⏭️  Skipping '{migration_name}' - already applied")
            return
        
        print(f"🔄 Running migration: {migration_name}")
        
        with self.app.app_context():
            try:
                with db.engine.connect() as conn:
                    # Check if using MySQL/MariaDB or SQLite
                    db_type = db.engine.dialect.name
                    
                    if db_type in ['mysql', 'mariadb']:
                        conn.execute(text(
                            "ALTER TABLE user MODIFY COLUMN password_hash VARCHAR(255) NOT NULL"
                        ))
                    elif db_type == 'postgresql':
                        conn.execute(text(
                            "ALTER TABLE user ALTER COLUMN password_hash TYPE VARCHAR(255)"
                        ))
                    # SQLite doesn't need alteration, it's flexible with string lengths
                    
                    conn.commit()
                print(f"✅ Migration '{migration_name}' completed successfully")
                self.mark_as_run(migration_name)
            except Exception as e:
                print(f"❌ Migration '{migration_name}' failed: {e}")
                # If it's SQLite or already correct size, mark as run anyway
                if "doesn't exist" in str(e).lower() or db.engine.dialect.name == 'sqlite':
                    print("   (Likely already correct or using SQLite - marking as complete)")
                    self.mark_as_run(migration_name)
                else:
                    raise
    
    def run_migration_002_change_request_table(self):
        """Migration 002: Create change_request table"""
        migration_name = "002_change_request_table"
        
        if self.has_run(migration_name):
            print(f"⏭️  Skipping '{migration_name}' - already applied")
            return
        
        print(f"🔄 Running migration: {migration_name}")
        
        with self.app.app_context():
            try:
                # Use SQLAlchemy's create_all which is safe (won't recreate existing tables)
                db.create_all()
                print(f"✅ Migration '{migration_name}' completed successfully")
                self.mark_as_run(migration_name)
            except Exception as e:
                print(f"❌ Migration '{migration_name}' failed: {e}")
                raise
    
    def run_migration_003_add_is_admin(self):
        """Migration 003: Add is_admin column to user table"""
        migration_name = "003_add_is_admin"
        
        if self.has_run(migration_name):
            print(f"⏭️  Skipping '{migration_name}' - already applied")
            return
        
        print(f"🔄 Running migration: {migration_name}")
        
        with self.app.app_context():
            try:
                with db.engine.connect() as conn:
                    db_type = db.engine.dialect.name
                    
                    # Check if column already exists
                    try:
                        result = conn.execute(text("SELECT is_admin FROM user LIMIT 1"))
                        print(f"   Column 'is_admin' already exists")
                    except:
                        # Column doesn't exist, add it
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
                        print(f"   Added 'is_admin' column to user table")
                    
                print(f"✅ Migration '{migration_name}' completed successfully")
                self.mark_as_run(migration_name)
            except Exception as e:
                print(f"❌ Migration '{migration_name}' failed: {e}")
                # If column already exists, mark as complete anyway
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("   (Column already exists - marking as complete)")
                    self.mark_as_run(migration_name)
                else:
                    raise
    
    def run_all_migrations(self):
        """Run all pending migrations in order"""
        print("\n" + "="*60)
        print("Starting Database Migrations")
        print("="*60 + "\n")
        
        # Ensure migrations tracking table exists
        self.ensure_migrations_table()
        
        # Run migrations in order
        self.run_migration_001_password_hash_length()
        self.run_migration_002_change_request_table()
        self.run_migration_003_add_is_admin()
        
        print("\n" + "="*60)
        print("All Migrations Completed")
        print("="*60 + "\n")

def main():
    """Run all pending migrations"""
    runner = MigrationRunner()
    runner.run_all_migrations()

if __name__ == '__main__':
    main()


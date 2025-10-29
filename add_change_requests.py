#!/usr/bin/env python3
"""
Migration script to add ChangeRequest table
"""

from app import create_app
from models import db, ChangeRequest

def migrate():
    app = create_app()
    with app.app_context():
        # Create the change_request table
        db.create_all()
        print("✅ ChangeRequest table created successfully!")
        
if __name__ == '__main__':
    migrate()


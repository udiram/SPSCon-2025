#!/usr/bin/env python3
"""
Script to make a user an admin
Usage: python make_admin.py <email_or_username>
"""

import sys
from app import create_app
from models import db, User

def make_admin(identifier):
    """Make a user an admin by email or username"""
    app = create_app()
    with app.app_context():
        # Try to find user by email or username
        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()
        
        if not user:
            print(f"❌ User not found: {identifier}")
            print("\nAvailable users:")
            for u in User.query.all():
                admin_status = "✅ ADMIN" if u.is_admin else ""
                print(f"  - {u.username} ({u.email}) {admin_status}")
            return False
        
        if user.is_admin:
            print(f"ℹ️  User '{user.username}' is already an admin!")
            return True
        
        # Make them admin
        user.is_admin = True
        db.session.commit()
        
        print(f"✅ SUCCESS! User '{user.username}' ({user.email}) is now an admin!")
        print(f"\nThey can now access the admin panel at: /admin")
        return True

def list_admins():
    """List all current admins"""
    app = create_app()
    with app.app_context():
        admins = User.query.filter_by(is_admin=True).all()
        
        if not admins:
            print("No admin users found.")
        else:
            print(f"Current Admins ({len(admins)}):")
            for admin in admins:
                print(f"  - {admin.username} ({admin.email})")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python make_admin.py <email_or_username>  - Make a user admin")
        print("  python make_admin.py --list                - List current admins")
        print("\nExample:")
        print("  python make_admin.py john@example.com")
        print("  python make_admin.py john")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        list_admins()
    else:
        identifier = sys.argv[1]
        make_admin(identifier)

if __name__ == '__main__':
    main()


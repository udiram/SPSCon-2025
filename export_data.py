#!/usr/bin/env python3
"""
Data Export Script for SPSCon 2025
Exports all data to JSON for backup or migration purposes
"""

import json
import os
from datetime import datetime
from models import db, User, Poster, Favorite, Visit, PresenterStatus
from app import create_app

def export_all_data():
    """Export all data to JSON file"""
    app = create_app()
    
    with app.app_context():
        try:
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0',
                    'description': 'SPSCon 2025 Complete Data Export'
                },
                'users': [],
                'posters': [],
                'favorites': [],
                'visits': [],
                'presenter_statuses': []
            }
            
            # Export users
            print("Exporting users...")
            for user in User.query.all():
                export_data['users'].append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'password_hash': user.password_hash,
                    'is_admin': user.is_admin,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                })
            
            # Export posters
            print("Exporting posters...")
            for poster in Poster.query.all():
                export_data['posters'].append({
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
            
            # Export favorites
            print("Exporting favorites...")
            for fav in Favorite.query.all():
                export_data['favorites'].append({
                    'id': fav.id,
                    'user_id': fav.user_id,
                    'poster_id': fav.poster_id,
                    'created_at': fav.created_at.isoformat() if fav.created_at else None
                })
            
            # Export visits
            print("Exporting visits...")
            for visit in Visit.query.all():
                export_data['visits'].append({
                    'id': visit.id,
                    'user_id': visit.user_id,
                    'poster_id': visit.poster_id,
                    'visited_at': visit.visited_at.isoformat() if visit.visited_at else None
                })
            
            # Export presenter statuses
            print("Exporting presenter statuses...")
            for status in PresenterStatus.query.all():
                export_data['presenter_statuses'].append({
                    'id': status.id,
                    'user_id': status.user_id,
                    'poster_id': status.poster_id,
                    'is_available': status.is_available,
                    'updated_at': status.updated_at.isoformat() if status.updated_at else None
                })
            
            # Save to file
            filename = f"spscon_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"\n✅ Export completed successfully!")
            print(f"📁 File saved as: {filename}")
            print(f"📊 Data exported:")
            print(f"   - {len(export_data['users'])} users")
            print(f"   - {len(export_data['posters'])} posters")
            print(f"   - {len(export_data['favorites'])} favorites")
            print(f"   - {len(export_data['visits'])} visits")
            print(f"   - {len(export_data['presenter_statuses'])} presenter statuses")
            
            return filename
            
        except Exception as e:
            print(f"❌ Error during export: {e}")
            return None

def export_posters_only():
    """Export only poster data (for data import/backup)"""
    app = create_app()
    
    with app.app_context():
        try:
            posters = []
            for poster in Poster.query.all():
                posters.append({
                    'poster_number': poster.poster_number,
                    'session': poster.session,
                    'first_name': poster.first_name,
                    'last_name': poster.last_name,
                    'institution': poster.institution,
                    'title': poster.title,
                    'category': poster.category,
                    'tags': poster.tags
                })
            
            filename = f"posters_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump({
                    'export_info': {
                        'timestamp': datetime.now().isoformat(),
                        'type': 'posters_only'
                    },
                    'posters': posters
                }, f, indent=2)
            
            print(f"✅ Posters exported to: {filename}")
            print(f"📊 {len(posters)} posters exported")
            
            return filename
            
        except Exception as e:
            print(f"❌ Error exporting posters: {e}")
            return None

if __name__ == "__main__":
    print("SPSCon 2025 Data Export Tool")
    print("=" * 40)
    
    choice = input("Export options:\n1. All data (users, posters, etc.)\n2. Posters only\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        export_all_data()
    elif choice == "2":
        export_posters_only()
    else:
        print("Invalid choice. Exiting.")

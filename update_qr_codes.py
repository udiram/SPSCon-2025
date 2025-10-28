#!/usr/bin/env python3
"""
Update QR codes for existing posters to use the correct Railway domain
"""

import os
from models import db, Poster
from utils.qr_generator import generate_qr_code
from app import create_app

def update_qr_codes():
    """Update QR codes for all existing posters"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get base URL based on environment
            if os.getenv('RAILWAY_ENVIRONMENT'):
                base_url = "https://spscon2025.up.railway.app"
                print("🌐 Updating QR codes for Railway production environment")
            else:
                base_url = "http://localhost:5000"
                print("🏠 Updating QR codes for local development environment")
            
            # Get all posters
            posters = Poster.query.all()
            print(f"📊 Found {len(posters)} posters to update")
            
            updated_count = 0
            
            for poster in posters:
                # Generate new QR code with correct URL
                qr_data = f"{base_url}/poster/{poster.poster_number}"
                poster.qr_code_data = generate_qr_code(qr_data)
                updated_count += 1
                
                if updated_count % 50 == 0:
                    print(f"   Updated {updated_count} QR codes...")
            
            # Commit all changes
            db.session.commit()
            print(f"✅ Successfully updated {updated_count} QR codes")
            print(f"   Base URL: {base_url}")
            
            return updated_count
            
        except Exception as e:
            print(f"❌ Error updating QR codes: {e}")
            db.session.rollback()
            return 0

if __name__ == "__main__":
    print("🔄 QR Code Update Script")
    print("=" * 30)
    
    count = update_qr_codes()
    
    if count > 0:
        print(f"\n🎉 Successfully updated {count} QR codes!")
    else:
        print("\n❌ No QR codes were updated")

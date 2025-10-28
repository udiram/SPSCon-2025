import pandas as pd
import json
from models import db, Poster
from utils.tag_generator import generate_tags_for_poster
from utils.qr_generator import generate_qr_code
from config import Config

def import_excel_data(excel_file_path):
    """Import poster data from Excel file"""
    try:
        # Read Excel file
        df = pd.read_excel(excel_file_path)
        
        print(f"Found {len(df)} posters in Excel file")
        print(f"Columns: {df.columns.tolist()}")
        
        # Clear existing posters
        Poster.query.delete()
        
        imported_count = 0
        
        for index, row in df.iterrows():
            try:
                # Create poster object
                poster = Poster(
                    poster_number=int(row['Poster Number']),
                    session=int(row['Poster Session ']),
                    first_name=str(row['First Name']).strip(),
                    last_name=str(row['Last Name']).strip(),
                    institution=str(row['Institution Name']).strip(),
                    title=str(row['Title']).strip(),
                    category=""  # Will be set by get_category_name method
                )
                
                # Generate tags
                tags = generate_tags_for_poster(poster)
                poster.tags = json.dumps(tags)
                
                # Generate QR code
                qr_data = f"https://your-domain.com/poster/{poster.poster_number}"
                poster.qr_code_data = generate_qr_code(qr_data)
                
                # Add to database
                db.session.add(poster)
                imported_count += 1
                
                if imported_count % 50 == 0:
                    print(f"Imported {imported_count} posters...")
                    
            except Exception as e:
                print(f"Error importing row {index}: {e}")
                continue
        
        # Commit all changes
        db.session.commit()
        print(f"Successfully imported {imported_count} posters")
        
        return imported_count
        
    except Exception as e:
        print(f"Error importing data: {e}")
        db.session.rollback()
        return 0

def check_data_integrity():
    """Check if data was imported correctly"""
    total_posters = Poster.query.count()
    print(f"Total posters in database: {total_posters}")
    
    # Check category distribution
    categories = {}
    for poster in Poster.query.all():
        category = poster.get_category_name()
        categories[category] = categories.get(category, 0) + 1
    
    print("Category distribution:")
    for category, count in categories.items():
        print(f"  {category}: {count}")
    
    # Check session distribution
    session_counts = db.session.query(Poster.session, db.func.count(Poster.id)).group_by(Poster.session).all()
    print("Session distribution:")
    for session, count in session_counts:
        print(f"  Session {session}: {count}")
    
    return total_posters

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Import data
        excel_file = "2025 SPSCon Poster Assignments_Student View.xlsx"
        count = import_excel_data(excel_file)
        
        if count > 0:
            check_data_integrity()
        else:
            print("No data imported. Check the Excel file path and format.")


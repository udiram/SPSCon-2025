from models import db, User, Poster, Favorite, Visit, PresenterStatus
from app import create_app

def init_db():
    """Initialize database tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("Database tables created successfully")
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Created tables: {tables}")
            
            return True
        except Exception as e:
            print(f"Error creating database: {e}")
            return False

def check_db_status():
    """Check database status and table counts"""
    app = create_app()
    
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("Database Status:")
            print(f"Tables: {tables}")
            
            if 'user' in tables:
                user_count = User.query.count()
                print(f"Users: {user_count}")
            
            if 'poster' in tables:
                poster_count = Poster.query.count()
                print(f"Posters: {poster_count}")
            
            if 'favorite' in tables:
                favorite_count = Favorite.query.count()
                print(f"Favorites: {favorite_count}")
            
            if 'visit' in tables:
                visit_count = Visit.query.count()
                print(f"Visits: {visit_count}")
            
            if 'presenter_status' in tables:
                status_count = PresenterStatus.query.count()
                print(f"Presenter Statuses: {status_count}")
            
            return True
        except Exception as e:
            print(f"Error checking database: {e}")
            return False

if __name__ == "__main__":
    print("Initializing database...")
    success = init_db()
    
    if success:
        print("\nChecking database status...")
        check_db_status()
    else:
        print("Database initialization failed")


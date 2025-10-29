import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///spscon.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # External APIs
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    # Conference information
    CONFERENCE_NAME = "SPSCon 2025"
    SESSION_I_TIME = "Friday, October 31, 10:30 AM – 12:00 PM"
    SESSION_II_TIME = "Saturday, November 1, 11:30 AM – 1:00 PM"
    SETUP_TIME = "Thursday, October 30, 6:15 PM – 7:00 PM"
    LOCATION = "Exhibit Hall"
    
    # Poster categories
    CATEGORIES = {
        1: "Supporting Our Phase Shifts",
        2: "Careers and Corporate Internships", 
        3: "Sigma Pi Sigma Chapter Activities",
        4: "Research"
    }
    
    # Category ranges
    CATEGORY_RANGES = {
        1: (1, 5),      # Supporting Our Phase Shifts
        2: (6, 13),     # Careers and Corporate Internships
        3: (14, 20),    # Sigma Pi Sigma Chapter Activities
        4: (21, 355)    # Research
    }


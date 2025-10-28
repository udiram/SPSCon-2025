from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    visits = db.relationship('Visit', backref='user', lazy=True, cascade='all, delete-orphan')
    presenter_statuses = db.relationship('PresenterStatus', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        if not self.first_name or not self.last_name:
            return self.username  # Fallback to username if names are missing
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.username}>'

class Poster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poster_number = db.Column(db.Integer, unique=True, nullable=False)
    session = db.Column(db.Integer, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    institution = db.Column(db.String(200), nullable=False)
    title = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.Text)  # JSON string of tags
    qr_code_data = db.Column(db.Text)  # Base64 encoded QR code
    presenter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Assigned presenter
    
    # Relationships
    favorites = db.relationship('Favorite', backref='poster', lazy=True, cascade='all, delete-orphan')
    visits = db.relationship('Visit', backref='poster', lazy=True, cascade='all, delete-orphan')
    presenter_statuses = db.relationship('PresenterStatus', backref='poster', lazy=True, cascade='all, delete-orphan')
    presenter = db.relationship('User', backref='presented_posters', foreign_keys=[presenter_id])
    
    def get_category_name(self):
        """Get the category name based on poster number"""
        for cat_id, (start, end) in Config.CATEGORY_RANGES.items():
            if start <= self.poster_number <= end:
                return Config.CATEGORIES[cat_id]
        return "Unknown"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def can_user_manage(self, user):
        """Check if a user can manage this poster (name match or assigned presenter)"""
        if not user:
            return False
        
        # Check if user is assigned presenter
        if self.presenter_id == user.id:
            return True
        
        # Check if first and last name match exactly (handle None values)
        if not user.first_name or not user.last_name:
            return False
            
        return (self.first_name.lower().strip() == user.first_name.lower().strip() and 
                self.last_name.lower().strip() == user.last_name.lower().strip())
    
    def __repr__(self):
        return f'<Poster {self.poster_number}: {self.title[:50]}...>'

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('poster.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure unique user-poster combination
    __table_args__ = (db.UniqueConstraint('user_id', 'poster_id', name='unique_user_poster_favorite'),)
    
    def __repr__(self):
        return f'<Favorite {self.user_id}-{self.poster_id}>'

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('poster.id'), nullable=False)
    visited_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Visit {self.user_id}-{self.poster_id}>'

class PresenterStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poster_id = db.Column(db.Integer, db.ForeignKey('poster.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one status per poster per user
    __table_args__ = (db.UniqueConstraint('poster_id', 'user_id', name='unique_poster_user_status'),)
    
    def __repr__(self):
        return f'<PresenterStatus {self.poster_id}-{self.user_id}: {self.is_available}>'

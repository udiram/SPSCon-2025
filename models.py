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
    password_hash = db.Column(db.String(255), nullable=False)
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

# -----------------------------
# AI Recommendation Models
# -----------------------------

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    # Flexible JSON blobs to store evolving preferences and interests
    preferences_json = db.Column(db.Text)  # JSON string
    interests_json = db.Column(db.Text)    # JSON string
    research_areas = db.Column(db.Text)    # comma-separated or JSON
    academic_background = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('profile', uselist=False))

    def __repr__(self):
        return f'<UserProfile user_id={self.user_id}>'


class UserQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    query_text = db.Column(db.Text, nullable=False)
    extracted_interests = db.Column(db.Text)  # JSON string
    context = db.Column(db.Text)              # JSON string for extra metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='queries')

    def __repr__(self):
        return f'<UserQuery id={self.id} user_id={self.user_id}>'


class RecommendationCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    query_hash = db.Column(db.String(64), index=True)  # sha256
    recommendations_json = db.Column(db.Text)  # JSON string containing posters/users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='recommendation_caches')

    def __repr__(self):
        return f'<RecommendationCache id={self.id} user_id={self.user_id}>'


class UserSettings(db.Model):
    """User preferences and settings"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Appearance
    dark_mode = db.Column(db.Boolean, default=False)
    compact_view = db.Column(db.Boolean, default=False)
    font_size = db.Column(db.String(20), default='medium')  # small, medium, large
    high_contrast = db.Column(db.Boolean, default=False)
    reduce_animations = db.Column(db.Boolean, default=False)
    
    # Notifications
    email_notifications = db.Column(db.Boolean, default=True)
    
    # Privacy
    profile_visible = db.Column(db.Boolean, default=True)
    show_activity = db.Column(db.Boolean, default=True)
    
    # Recommendations
    exclude_visited_recommendations = db.Column(db.Boolean, default=True)
    recommendations_count = db.Column(db.Integer, default=20)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('settings', uselist=False))
    
    def __repr__(self):
        return f'<UserSettings user_id={self.user_id}>'
    
    def to_dict(self):
        """Convert settings to dictionary"""
        return {
            'dark_mode': self.dark_mode,
            'compact_view': self.compact_view,
            'font_size': self.font_size,
            'high_contrast': self.high_contrast,
            'reduce_animations': self.reduce_animations,
            'email_notifications': self.email_notifications,
            'profile_visible': self.profile_visible,
            'show_activity': self.show_activity,
            'exclude_visited_recommendations': self.exclude_visited_recommendations,
            'recommendations_count': self.recommendations_count
        }


class ChangeRequest(db.Model):
    """Model for user change requests to admins"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(50), nullable=False)  # 'email', 'username', 'name', 'other'
    field_name = db.Column(db.String(100), nullable=False)  # What field to change
    current_value = db.Column(db.Text)  # Current value
    proposed_value = db.Column(db.Text, nullable=False)  # Requested new value
    reason = db.Column(db.Text, nullable=False)  # Why they want the change
    status = db.Column(db.String(20), default='pending')  # pending, approved, denied
    admin_notes = db.Column(db.Text)  # Notes from admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='change_requests')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_requests')
    
    def __repr__(self):
        return f'<ChangeRequest {self.id}: {self.request_type} - {self.status}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'user_email': self.user.email if self.user else None,
            'request_type': self.request_type,
            'field_name': self.field_name,
            'current_value': self.current_value,
            'proposed_value': self.proposed_value,
            'reason': self.reason,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reviewed_by': self.reviewed_by,
            'reviewer_username': self.reviewer.username if self.reviewer else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }

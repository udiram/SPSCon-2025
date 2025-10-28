from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Poster, Favorite, Visit, PresenterStatus
from config import Config
import json
from datetime import datetime
import csv
import io
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Add custom Jinja2 filters
    @app.template_filter('from_json')
    def from_json_filter(value):
        if value is None:
            return []
        try:
            import json
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Routes
    @app.route('/health')
    def health_check():
        """Health check endpoint for Railway"""
        return jsonify({
            'status': 'healthy',
            'service': 'SPSCon 2025',
            'timestamp': datetime.utcnow().isoformat(),
            'environment': os.environ.get('FLASK_ENV', 'development')
        })
    
    @app.route('/')
    def index():
        # Get statistics for dashboard (available to everyone)
        total_posters = Poster.query.count()
        total_users = User.query.count()
        total_visits = Visit.query.count()
        
        # Get category distribution
        categories = {}
        for poster in Poster.query.all():
            category = poster.get_category_name()
            categories[category] = categories.get(category, 0) + 1
        
        # Get institution distribution (top 10 for chart)
        institutions = db.session.query(Poster.institution, db.func.count(Poster.id)).group_by(Poster.institution).order_by(db.func.count(Poster.id).desc()).limit(10).all()
        institutions = [(row[0], row[1]) for row in institutions]
        
        # Get total unique institutions count
        total_institutions = db.session.query(Poster.institution).distinct().count()
        
        return render_template('index.html', 
                             total_posters=total_posters,
                             total_users=total_users,
                             total_visits=total_visits,
                             categories=categories,
                             institutions=institutions,
                             total_institutions=total_institutions)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form['email']
            username = request.form['username']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            password = request.form['password']
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                flash('Email already registered')
                return render_template('register.html')
            
            if User.query.filter_by(username=username).first():
                flash('Username already taken')
                return render_template('register.html')
            
            # Create new user
            user = User(email=email, username=username, first_name=first_name, last_name=last_name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/search')
    def search():
        query = request.args.get('q', '')
        category = request.args.get('category', '')
        session_filter = request.args.get('session', '')
        institution = request.args.get('institution', '')
        available_only = request.args.get('available', '') == 'true'
        
        # Build query
        posters_query = Poster.query
        
        if query:
            posters_query = posters_query.filter(
                db.or_(
                    Poster.title.contains(query),
                    Poster.first_name.contains(query),
                    Poster.last_name.contains(query),
                    Poster.institution.contains(query),
                    Poster.tags.contains(query)
                )
            )
        
        if category:
            # Filter by category based on poster number ranges
            if category == 'Supporting Our Phase Shifts':
                posters_query = posters_query.filter(Poster.poster_number.between(1, 5))
            elif category == 'Careers and Corporate Internships':
                posters_query = posters_query.filter(Poster.poster_number.between(6, 13))
            elif category == 'Sigma Pi Sigma Chapter Activities':
                posters_query = posters_query.filter(Poster.poster_number.between(14, 20))
            elif category == 'Research':
                posters_query = posters_query.filter(Poster.poster_number.between(21, 355))
        
        if session_filter:
            posters_query = posters_query.filter(Poster.session == int(session_filter))
        
        if institution:
            posters_query = posters_query.filter(Poster.institution.contains(institution))
        
        # Get unique institutions for filter dropdown
        institutions = db.session.query(Poster.institution).distinct().order_by(Poster.institution).all()
        institutions = [inst[0] for inst in institutions]
        
        posters = posters_query.order_by(Poster.poster_number).all()
        
        # Filter by availability if requested
        if available_only:
            available_poster_ids = [ps.poster_id for ps in PresenterStatus.query.filter_by(is_available=True).all()]
            posters = [p for p in posters if p.id in available_poster_ids]
        
        return render_template('search_results.html', 
                             posters=posters,
                             query=query,
                             category=category,
                             session_filter=session_filter,
                             institution=institution,
                             available_only=available_only,
                             institutions=institutions)

    @app.route('/institutions')
    def institutions_list():
        """List all unique institutions with poster counts."""
        institution_counts = db.session.query(
            Poster.institution, db.func.count(Poster.id)
        ).group_by(Poster.institution).order_by(Poster.institution.asc()).all()
        # Normalize to list of tuples
        institutions = [(row[0], row[1]) for row in institution_counts]
        return render_template('institutions.html', institutions=institutions)

    @app.route('/institutions/<path:institution_name>')
    def institutions_detail(institution_name):
        """Redirect to search filtered by institution when clicking an institution."""
        # Let the existing search page handle rendering and filtering
        return redirect(url_for('search', institution=institution_name))
    
    @app.route('/poster/<int:poster_id>')
    def poster_detail(poster_id):
        poster = db.session.get(Poster, poster_id)
        if not poster:
            from flask import abort
            abort(404)
        
        # Check if user has favorited this poster (only if logged in)
        is_favorited = False
        if current_user.is_authenticated:
            is_favorited = Favorite.query.filter_by(user_id=current_user.id, poster_id=poster.id).first() is not None
        
        # Check if user has visited this poster (only if logged in)
        has_visited = False
        if current_user.is_authenticated:
            has_visited = Visit.query.filter_by(user_id=current_user.id, poster_id=poster.id).first() is not None
        
        # Get presenter availability status
        presenter_status = PresenterStatus.query.filter_by(poster_id=poster.id).first()
        is_available = presenter_status.is_available if presenter_status else False
        
        # Check if user can manage this poster (only if logged in)
        can_manage = False
        if current_user.is_authenticated:
            can_manage = poster.can_user_manage(current_user)
        
        # Get similar posters
        from utils.similarity import get_similar_posters
        all_posters = Poster.query.all()
        similar_posters = get_similar_posters(poster, all_posters, limit=5)
        
        return render_template('poster_detail.html',
                             poster=poster,
                             is_favorited=is_favorited,
                             has_visited=has_visited,
                             is_available=is_available,
                             can_manage=can_manage,
                             similar_posters=similar_posters)
    
    @app.route('/visited')
    def visited():
        if current_user.is_authenticated:
            # Logged in user - get from database
            user_visits = Visit.query.filter_by(user_id=current_user.id).all()
            posters = [visit.poster for visit in user_visits]
        else:
            # Anonymous user - get from local storage (will be handled by frontend)
            posters = []
        
        return render_template('visited.html', posters=posters)

    @app.route('/favorites')
    def favorites():
        if current_user.is_authenticated:
            # Logged in user - get from database
            user_favorites = Favorite.query.filter_by(user_id=current_user.id).all()
            posters = [fav.poster for fav in user_favorites]
        else:
            # Anonymous user - get from local storage (will be handled by frontend)
            posters = []
        
        return render_template('favorites.html', posters=posters)
    
    @app.route('/analytics')
    @login_required
    def analytics():
        # Get visit statistics
        total_visits = Visit.query.count()
        unique_visitors = db.session.query(Visit.user_id).distinct().count()
        
        # Most visited posters
        most_visited = db.session.query(Visit.poster_id, db.func.count(Visit.id).label('visit_count')).group_by(Visit.poster_id).order_by(db.func.count(Visit.id).desc()).limit(10).all()
        
        most_visited_posters = []
        for poster_id, visit_count in most_visited:
            poster = db.session.get(Poster, poster_id)
            if poster:
                most_visited_posters.append((poster, visit_count))
        
        # Institution engagement
        institution_engagement = db.session.query(Poster.institution, db.func.count(Visit.id).label('visits')).join(Visit).group_by(Poster.institution).order_by(db.func.count(Visit.id).desc()).limit(10).all()
        institution_engagement = [(row[0], row[1]) for row in institution_engagement]
        
        return render_template('analytics.html',
                             total_visits=total_visits,
                             unique_visitors=unique_visitors,
                             most_visited_posters=most_visited_posters,
                             institution_engagement=institution_engagement)
    
    # API Routes
    @app.route('/api/favorite/<int:poster_id>', methods=['POST'])
    def toggle_favorite(poster_id):
        """Toggle favorite status for a poster"""
        poster = db.session.get(Poster, poster_id)
        if not poster:
            from flask import abort
            abort(404)
        
        if current_user.is_authenticated:
            # Logged in user - use database
            favorite = Favorite.query.filter_by(user_id=current_user.id, poster_id=poster_id).first()
            
            if favorite:
                # Remove from favorites
                db.session.delete(favorite)
                db.session.commit()
                return jsonify({'status': 'removed', 'message': 'Removed from favorites', 'use_local_storage': False})
            else:
                # Add to favorites
                favorite = Favorite(user_id=current_user.id, poster_id=poster_id)
                db.session.add(favorite)
                db.session.commit()
                return jsonify({'status': 'added', 'message': 'Added to favorites', 'use_local_storage': False})
        else:
            # Anonymous user - return status for local storage
            return jsonify({'status': 'local_storage', 'message': 'Use local storage for anonymous users', 'use_local_storage': True})

    @app.route('/api/visit/<int:poster_id>', methods=['POST'])
    def mark_visited(poster_id):
        """Mark a poster as visited"""
        poster = db.session.get(Poster, poster_id)
        if not poster:
            from flask import abort
            abort(404)
        
        if current_user.is_authenticated:
            # Logged in user - use database
            visit = Visit.query.filter_by(user_id=current_user.id, poster_id=poster_id).first()
            
            if not visit:
                visit = Visit(user_id=current_user.id, poster_id=poster_id)
                db.session.add(visit)
                db.session.commit()
                return jsonify({'status': 'success', 'message': 'Marked as visited', 'use_local_storage': False})
            else:
                return jsonify({'status': 'already_visited', 'message': 'Already marked as visited', 'use_local_storage': False})
        else:
            # Anonymous user - return status for local storage
            return jsonify({'status': 'local_storage', 'message': 'Use local storage for anonymous users', 'use_local_storage': True})

    @app.route('/api/anonymous-data')
    def get_anonymous_data():
        """Get anonymous user's local storage data"""
        return jsonify({
            'favorites': request.args.get('favorites', '[]'),
            'visited': request.args.get('visited', '[]'),
            'message': 'Anonymous user data from local storage'
        })

    @app.route('/api/posters-by-ids', methods=['POST'])
    def get_posters_by_ids():
        """Get poster details by IDs for local storage users"""
        data = request.get_json()
        poster_ids = data.get('poster_ids', [])
        
        if not poster_ids:
            return jsonify([])
        
        posters = Poster.query.filter(Poster.id.in_(poster_ids)).all()
        
        # Convert to JSON-serializable format
        posters_data = []
        for poster in posters:
            posters_data.append({
                'id': poster.id,
                'poster_number': poster.poster_number,
                'session': poster.session,
                'first_name': poster.first_name,
                'last_name': poster.last_name,
                'institution': poster.institution,
                'title': poster.title,
                'category': poster.get_category_name(),
                'tags': poster.tags
            })
        
        return jsonify(posters_data)

    @app.route('/api/presenter-status/<int:poster_id>', methods=['POST'])
    @login_required
    def toggle_presenter_status(poster_id):
        """Toggle presenter availability status"""
        poster = db.session.get(Poster, poster_id)
        if not poster:
            from flask import abort
            abort(404)
        
        # Check if user can manage this poster
        if not poster.can_user_manage(current_user):
            return jsonify({'status': 'error', 'message': 'You are not authorized to manage this poster'}), 403
        
        status = PresenterStatus.query.filter_by(poster_id=poster_id, user_id=current_user.id).first()
        
        if status:
            # Toggle existing status
            status.is_available = not status.is_available
            status.last_updated = datetime.utcnow()
        else:
            # Create new status
            status = PresenterStatus(
                poster_id=poster_id,
                user_id=current_user.id,
                is_available=True,
                last_updated=datetime.utcnow()
            )
            db.session.add(status)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'is_available': status.is_available,
            'message': f"Status updated: {'Available' if status.is_available else 'Not available'}"
        })

    @app.route('/api/presenter-status/<int:poster_id>')
    @login_required
    def get_presenter_status(poster_id):
        """Get presenter availability status"""
        status = PresenterStatus.query.filter_by(poster_id=poster_id).first()
        
        if status:
            return jsonify({
                'is_available': status.is_available,
                'last_updated': status.last_updated.isoformat(),
                'user_id': status.user_id
            })
        else:
            return jsonify({
                'is_available': False,
                'last_updated': None,
                'user_id': None
            })

    @app.route('/api/export/csv')
    @login_required
    def export_csv():
        """Export search results to CSV"""
        # Get search parameters
        query = request.args.get('q', '')
        category = request.args.get('category', '')
        session_filter = request.args.get('session', '')
        institution = request.args.get('institution', '')
        
        # Build query (same logic as search route)
        posters_query = Poster.query
        
        if query:
            posters_query = posters_query.filter(
                db.or_(
                    Poster.title.contains(query),
                    Poster.first_name.contains(query),
                    Poster.last_name.contains(query),
                    Poster.institution.contains(query),
                    Poster.tags.contains(query)
                )
            )
        
        if category:
            if category == 'Supporting Our Phase Shifts':
                posters_query = posters_query.filter(Poster.poster_number.between(1, 5))
            elif category == 'Careers and Corporate Internships':
                posters_query = posters_query.filter(Poster.poster_number.between(6, 13))
            elif category == 'Sigma Pi Sigma Chapter Activities':
                posters_query = posters_query.filter(Poster.poster_number.between(14, 20))
            elif category == 'Research':
                posters_query = posters_query.filter(Poster.poster_number.between(21, 355))
        
        if session_filter:
            posters_query = posters_query.filter(Poster.session == int(session_filter))
        
        if institution:
            posters_query = posters_query.filter(Poster.institution.contains(institution))
        
        posters = posters_query.order_by(Poster.poster_number).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Poster Number', 'Session', 'First Name', 'Last Name', 'Institution', 'Title', 'Category'])
        
        # Write data
        for poster in posters:
            writer.writerow([
                poster.poster_number,
                poster.session,
                poster.first_name,
                poster.last_name,
                poster.institution,
                poster.title,
                poster.get_category_name()
            ])
        
        # Prepare response
        output.seek(0)
        csv_data = output.getvalue()
        output.close()
        
        return csv_data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=spscon_posters_{datetime.now().strftime("%Y%m%d")}.csv'
        }

    # Admin Routes
    @app.route('/admin')
    @login_required
    def admin_panel():
        """Admin panel for managing presenter assignments"""
        # Simple admin check - you can make this more sophisticated
        if current_user.username != 'admin':
            from flask import abort
            abort(403)
        
        # Get all posters with their assignments
        posters = Poster.query.order_by(Poster.poster_number).all()
        
        # Get all users for assignment dropdown
        users = User.query.order_by(User.username).all()
        
        return render_template('admin.html', posters=posters, users=users)
    
    @app.route('/admin/assign-presenter', methods=['POST'])
    @login_required
    def assign_presenter():
        """Assign a presenter to a poster"""
        if current_user.username != 'admin':
            from flask import abort
            abort(403)
        
        poster_id = request.json.get('poster_id')
        user_id = request.json.get('user_id')
        
        poster = db.session.get(Poster, poster_id)
        if not poster:
            return jsonify({'status': 'error', 'message': 'Poster not found'}), 404
        
        if user_id:
            user = db.session.get(User, user_id)
            if not user:
                return jsonify({'status': 'error', 'message': 'User not found'}), 404
            poster.presenter_id = user.id
        else:
            poster.presenter_id = None
        
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': f'Presenter {"assigned" if user_id else "unassigned"} successfully',
            'presenter_name': user.username if user_id else None
        })
    
    @app.route('/admin/my-posters')
    @login_required
    def my_posters():
        """Show posters that the current user can manage"""
        # Find posters where user can manage (name match or assigned)
        manageable_posters = []
        for poster in Poster.query.all():
            if poster.can_user_manage(current_user):
                manageable_posters.append(poster)
        
        return render_template('my_posters.html', posters=manageable_posters)
    
    @app.route('/admin/auto-assign', methods=['POST'])
    @login_required
    def auto_assign_presenters():
        """Auto-assign presenters based on name matching"""
        if current_user.username != 'admin':
            from flask import abort
            abort(403)
        
        assigned_count = 0
        
        for poster in Poster.query.all():
            if poster.presenter_id:  # Skip already assigned
                continue
                
            # Try to find matching user by first and last name (only if user has names)
            matching_user = User.query.filter(
                db.and_(
                    User.first_name.isnot(None),
                    User.last_name.isnot(None),
                    User.first_name.ilike(f"%{poster.first_name.lower()}%"),
                    User.last_name.ilike(f"%{poster.last_name.lower()}%")
                )
            ).first()
            
            if matching_user:
                poster.presenter_id = matching_user.id
                assigned_count += 1
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Auto-assigned {assigned_count} posters',
            'assigned_count': assigned_count
        })
    
    @app.route('/admin/unassign-all', methods=['POST'])
    @login_required
    def unassign_all_presenters():
        """Unassign all presenters from all posters"""
        if current_user.username != 'admin':
            from flask import abort
            abort(403)
        
        Poster.query.update({'presenter_id': None})
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'All posters unassigned successfully'
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Only create tables if not in production (Railway handles this via deploy.py)
    if os.environ.get('FLASK_ENV') != 'production':
        with app.app_context():
            db.create_all()
    
    # Get configuration from environment
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 Starting SPSCon 2025 Flask App")
    print(f"   Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"   Debug: {debug}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    
    app.run(debug=debug, host=host, port=port)

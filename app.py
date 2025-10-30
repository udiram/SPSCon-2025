from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Poster, Favorite, Visit, PresenterStatus, UserProfile, UserQuery, RecommendationCache, UserSettings, ChangeRequest
from config import Config
from functools import wraps
import json
from datetime import datetime
import csv
import io
import os

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

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
    
    # Context processor for navbar counts
    @app.context_processor
    def inject_navbar_counts():
        """Inject favorites and visited counts into all templates"""
        favorites_count = 0
        visited_count = 0
        
        try:
            if current_user.is_authenticated:
                favorites_count = Favorite.query.filter_by(user_id=current_user.id).count()
                visited_count = Visit.query.filter_by(user_id=current_user.id).count()
        except Exception as e:
            # Database might not be ready yet, return zeros
            print(f"Warning: Could not load navbar counts: {e}")
        
        return {
            'favorites_count': favorites_count,
            'visited_count': visited_count
        }
    
    # Helper functions
    def get_poster_visit_counts():
        """Get visit counts for all posters"""
        visit_counts = db.session.query(
            Visit.poster_id, 
            db.func.count(Visit.id).label('visit_count')
        ).group_by(Visit.poster_id).all()
        return {poster_id: count for poster_id, count in visit_counts}
    
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
        visit_counts = get_poster_visit_counts()
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
                             visit_counts=visit_counts,
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
        
        # Get visitor counts
        visit_counts = get_poster_visit_counts()
        
        return render_template('search_results.html', 
                             posters=posters,
                             query=query,
                             category=category,
                             session_filter=session_filter,
                             institution=institution,
                             available_only=available_only,
                             institutions=institutions,
                             visit_counts=visit_counts)

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
        
        # Get visitor counts
        visit_counts = get_poster_visit_counts()
        visit_count = visit_counts.get(poster_id, 0)
        
        return render_template('poster_detail.html',
                             poster=poster,
                             is_favorited=is_favorited,
                             has_visited=has_visited,
                             is_available=is_available,
                             can_manage=can_manage,
                             similar_posters=similar_posters,
                             visit_counts=visit_counts,
                             visit_count=visit_count)
    
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
    def analytics():
        # Get visit statistics
        total_visits = Visit.query.count()
        unique_visitors = db.session.query(Visit.user_id).distinct().count()
        
        # Most visited posters (top 10)
        most_visited = db.session.query(
            Visit.poster_id, 
            db.func.count(Visit.id).label('visit_count')
        ).group_by(Visit.poster_id).order_by(
            db.func.count(Visit.id).desc()
        ).limit(10).all()
        
        most_visited_posters = []
        for poster_id, visit_count in most_visited:
            poster = db.session.get(Poster, poster_id)
            if poster:
                most_visited_posters.append((poster, visit_count))
        
        # Institution engagement (top 10)
        institution_engagement = db.session.query(
            Poster.institution, 
            db.func.count(Visit.id).label('visits')
        ).join(Visit).group_by(
            Poster.institution
        ).order_by(
            db.func.count(Visit.id).desc()
        ).limit(10).all()
        institution_engagement = [(row[0], row[1]) for row in institution_engagement]
        
        # Category breakdown
        category_engagement = {}
        for poster in Poster.query.all():
            cat_name = poster.get_category_name()
            visit_count = Visit.query.filter_by(poster_id=poster.id).count()
            if cat_name not in category_engagement:
                category_engagement[cat_name] = 0
            category_engagement[cat_name] += visit_count
        
        # Session breakdown
        session_visits = db.session.query(
            Poster.session,
            db.func.count(Visit.id).label('visits')
        ).join(Visit).group_by(Poster.session).all()
        session_breakdown = {session: visits for session, visits in session_visits}
        
        # Recent activity (last 20 visits)
        recent_visits = Visit.query.order_by(Visit.visited_at.desc()).limit(20).all()
        recent_activity = []
        for visit in recent_visits:
            poster = db.session.get(Poster, visit.poster_id)
            user = db.session.get(User, visit.user_id) if visit.user_id else None
            if poster:
                recent_activity.append({
                    'poster': poster,
                    'user': user,
                    'timestamp': visit.visited_at
                })
        
        # Visit trends (last 7 days, group by day)
        from datetime import timedelta
        today = datetime.utcnow().date()
        visit_trends = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())
            count = Visit.query.filter(
                Visit.visited_at >= day_start,
                Visit.visited_at <= day_end
            ).count()
            visit_trends.append({
                'date': day.strftime('%m/%d'),
                'count': count
            })
        
        return render_template('analytics.html',
                             total_visits=total_visits,
                             unique_visitors=unique_visitors,
                             most_visited_posters=most_visited_posters,
                             institution_engagement=institution_engagement,
                             category_engagement=category_engagement,
                             session_breakdown=session_breakdown,
                             recent_activity=recent_activity,
                             visit_trends=visit_trends)
    
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
        """Toggle visited status for a poster"""
        poster = db.session.get(Poster, poster_id)
        if not poster:
            from flask import abort
            abort(404)
        
        if current_user.is_authenticated:
            # Logged in user - use database
            visit = Visit.query.filter_by(user_id=current_user.id, poster_id=poster_id).first()
            
            if not visit:
                # Add visit
                visit = Visit(user_id=current_user.id, poster_id=poster_id)
                db.session.add(visit)
                db.session.commit()
                return jsonify({'status': 'added', 'message': 'Marked as visited', 'use_local_storage': False})
            else:
                # Remove visit (toggle off)
                db.session.delete(visit)
                db.session.commit()
                return jsonify({'status': 'removed', 'message': 'Removed from visited', 'use_local_storage': False})
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

    @app.route('/api/export/favorites')
    def export_favorites():
        """Export favorites for anonymous users"""
        try:
            poster_ids = request.args.get('ids', '')
            if not poster_ids:
                return jsonify({'error': 'No poster IDs provided'}), 400
            
            # Parse comma-separated IDs
            try:
                poster_ids = [int(pid.strip()) for pid in poster_ids.split(',')]
            except ValueError:
                return jsonify({'error': 'Invalid poster IDs'}), 400
            
            # Get posters
            posters = Poster.query.filter(Poster.id.in_(poster_ids)).all()
            
            # Create CSV content
            csv_content = "Poster Number,Title,Author,Institution,Session,Category\n"
            for poster in posters:
                csv_content += f'"{poster.poster_number}","{poster.title}","{poster.first_name} {poster.last_name}","{poster.institution}","{poster.session}","{poster.category}"\n'
            
            # Return CSV response
            response = make_response(csv_content)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename="spscon-favorites-{datetime.now().strftime("%Y%m%d")}.csv"'
            return response
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/export/visited')
    def export_visited():
        """Export visited posters for anonymous users"""
        try:
            poster_ids = request.args.get('ids', '')
            if not poster_ids:
                return jsonify({'error': 'No poster IDs provided'}), 400
            
            # Parse comma-separated IDs
            try:
                poster_ids = [int(pid.strip()) for pid in poster_ids.split(',')]
            except ValueError:
                return jsonify({'error': 'Invalid poster IDs'}), 400
            
            # Get posters
            posters = Poster.query.filter(Poster.id.in_(poster_ids)).all()
            
            # Create CSV content
            csv_content = "Poster Number,Title,Author,Institution,Session,Category\n"
            for poster in posters:
                csv_content += f'"{poster.poster_number}","{poster.title}","{poster.first_name} {poster.last_name}","{poster.institution}","{poster.session}","{poster.category}"\n'
            
            # Return CSV response
            response = make_response(csv_content)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename="spscon-visited-{datetime.now().strftime("%Y%m%d")}.csv"'
            return response
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

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

    # Recommendation Routes
    @app.route('/recommendations')
    def recommendations():
        """Main recommendations page"""
        return render_template('recommendations.html')
    
    @app.route('/api/recommend/query', methods=['POST'])
    def recommend_from_query():
        """Process natural language query and return recommendations"""
        if not current_user.is_authenticated:
            return jsonify({'status': 'error', 'message': 'Please log in to use recommendations'}), 401
        
        data = request.get_json()
        query_text = data.get('query', '').strip()
        
        if not query_text:
            return jsonify({'status': 'error', 'message': 'Query is required'}), 400
        
        try:
            from utils.groq_client import GroqClient
            from utils.recommendation_engine import ProfileBuilder, RecommendationGenerator, UserSimilarityCalculator
            
            groq_client = GroqClient()
            profile_builder = ProfileBuilder(current_user)
            
            # Update profile with query insights
            profile = profile_builder.update_profile_from_query(query_text, groq_client)
            
            # Generate recommendations
            all_posters = Poster.query.all()
            rec_generator = RecommendationGenerator(groq_client)
            poster_recommendations = rec_generator.generate_poster_recommendations(
                profile, 
                all_posters,
                limit=20,
                exclude_visited=True
            )
            
            # Format poster recommendations
            formatted_posters = []
            for rec in poster_recommendations:
                poster = rec['poster']
                # Parse tags
                tags = []
                if poster.tags:
                    try:
                        tags = json.loads(poster.tags) if isinstance(poster.tags, str) else poster.tags
                    except:
                        tags = []
                
                formatted_posters.append({
                    'id': poster.id,
                    'poster_number': poster.poster_number,
                    'title': poster.title,
                    'author': f"{poster.first_name} {poster.last_name}",
                    'institution': poster.institution,
                    'category': poster.get_category_name(),
                    'session': poster.session,
                    'tags': tags,
                    'score': round(rec['score'], 3),
                    'reasons': rec['reasons'],
                    'url': url_for('poster_detail', poster_id=poster.id)
                })
            
            # Get user recommendations
            all_users = User.query.filter(User.id != current_user.id).all()
            user_calculator = UserSimilarityCalculator()
            user_recommendations = user_calculator.calculate_similarities(
                current_user,
                profile,
                all_users,
                limit=10
            )
            
            # Format user recommendations
            formatted_users = []
            for rec in user_recommendations:
                user = rec['user']
                formatted_users.append({
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.get_full_name(),
                    'score': round(rec['score'], 3),
                    'shared_posters': rec['shared_posters'],
                    'shared_categories': rec['categories']
                })
            
            return jsonify({
                'status': 'success',
                'posters': formatted_posters,
                'users': formatted_users,
                'profile_updated': True
            })
            
        except Exception as e:
            print(f"Recommendation error: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/recommend/posters')
    @login_required
    def get_poster_recommendations():
        """Get poster recommendations based on current profile"""
        try:
            from utils.groq_client import GroqClient
            from utils.recommendation_engine import ProfileBuilder, RecommendationGenerator
            
            groq_client = GroqClient()
            profile_builder = ProfileBuilder(current_user)
            profile = profile_builder.get_or_build_profile()
            
            all_posters = Poster.query.all()
            rec_generator = RecommendationGenerator(groq_client)
            recommendations = rec_generator.generate_poster_recommendations(
                profile,
                all_posters,
                limit=20,
                exclude_visited=True
            )
            
            formatted = []
            for rec in recommendations:
                poster = rec['poster']
                # Parse tags
                tags = []
                if poster.tags:
                    try:
                        tags = json.loads(poster.tags) if isinstance(poster.tags, str) else poster.tags
                    except:
                        tags = []
                
                formatted.append({
                    'id': poster.id,
                    'poster_number': poster.poster_number,
                    'title': poster.title,
                    'author': f"{poster.first_name} {poster.last_name}",
                    'institution': poster.institution,
                    'category': poster.get_category_name(),
                    'session': poster.session,
                    'tags': tags,
                    'score': round(rec['score'], 3),
                    'reasons': rec['reasons'],
                    'url': url_for('poster_detail', poster_id=poster.id)
                })
            
            return jsonify({
                'status': 'success',
                'posters': formatted
            })
            
        except Exception as e:
            print(f"Recommendation error: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/recommend/users')
    @login_required
    def get_user_recommendations():
        """Get similar user recommendations"""
        try:
            from utils.groq_client import GroqClient
            from utils.recommendation_engine import ProfileBuilder, UserSimilarityCalculator
            
            groq_client = GroqClient()
            profile_builder = ProfileBuilder(current_user)
            profile = profile_builder.get_or_build_profile()
            
            all_users = User.query.filter(User.id != current_user.id).all()
            user_calculator = UserSimilarityCalculator()
            recommendations = user_calculator.calculate_similarities(
                current_user,
                profile,
                all_users,
                limit=10
            )
            
            formatted = []
            for rec in recommendations:
                user = rec['user']
                formatted.append({
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.get_full_name(),
                    'score': round(rec['score'], 3),
                    'shared_posters': rec['shared_posters'],
                    'shared_categories': rec['categories']
                })
            
            return jsonify({
                'status': 'success',
                'users': formatted
            })
            
        except Exception as e:
            print(f"User recommendation error: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/profile')
    @login_required
    def get_profile():
        """Get current user profile summary"""
        try:
            from utils.recommendation_engine import ProfileBuilder
            
            profile_builder = ProfileBuilder(current_user)
            profile = profile_builder.get_or_build_profile()
            
            # Return summary without sensitive details
            return jsonify({
                'status': 'success',
                'profile': {
                    'interests': profile.get('interests', [])[:10],
                    'categories': profile.get('categories', []),
                    'top_tags': profile.get('top_tags', [])[:10],
                    'favorite_count': profile.get('favorite_count', 0),
                    'visit_count': profile.get('visit_count', 0),
                    'experience_level': profile.get('experience_level')
                }
            })
            
        except Exception as e:
            print(f"Profile error: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # Settings Routes
    @app.route('/settings')
    @login_required
    def settings_page():
        """User settings page"""
        return render_template('settings.html')
    
    @app.route('/api/settings', methods=['GET'])
    @login_required
    def get_settings():
        """Get current user settings"""
        try:
            user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
            
            if not user_settings:
                # Create default settings
                user_settings = UserSettings(user_id=current_user.id)
                db.session.add(user_settings)
                db.session.commit()
            
            return jsonify({
                'status': 'success',
                'settings': user_settings.to_dict()
            })
        except Exception as e:
            print(f"Get settings error: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/settings', methods=['POST'])
    @login_required
    def update_settings():
        """Update user settings"""
        try:
            data = request.get_json()
            
            user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
            
            if not user_settings:
                user_settings = UserSettings(user_id=current_user.id)
                db.session.add(user_settings)
            
            # Update settings
            if 'dark_mode' in data:
                user_settings.dark_mode = data['dark_mode']
            if 'compact_view' in data:
                user_settings.compact_view = data['compact_view']
            if 'font_size' in data:
                user_settings.font_size = data['font_size']
            if 'high_contrast' in data:
                user_settings.high_contrast = data['high_contrast']
            if 'reduce_animations' in data:
                user_settings.reduce_animations = data['reduce_animations']
            if 'email_notifications' in data:
                user_settings.email_notifications = data['email_notifications']
            if 'profile_visible' in data:
                user_settings.profile_visible = data['profile_visible']
            if 'show_activity' in data:
                user_settings.show_activity = data['show_activity']
            if 'exclude_visited_recommendations' in data:
                user_settings.exclude_visited_recommendations = data['exclude_visited_recommendations']
            if 'recommendations_count' in data:
                user_settings.recommendations_count = data['recommendations_count']
            
            user_settings.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Settings updated successfully',
                'settings': user_settings.to_dict()
            })
        except Exception as e:
            print(f"Update settings error: {e}")
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # Change Request APIs
    @app.route('/api/change-request', methods=['POST'])
    @login_required
    def submit_change_request():
        """Submit a change request"""
        try:
            data = request.get_json()
            
            change_request = ChangeRequest(
                user_id=current_user.id,
                request_type=data.get('request_type'),
                field_name=data.get('field_name'),
                current_value=data.get('current_value'),
                proposed_value=data.get('proposed_value'),
                reason=data.get('reason'),
                status='pending'
            )
            
            db.session.add(change_request)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Change request submitted successfully',
                'request_id': change_request.id
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/change-requests', methods=['GET'])
    @login_required
    def get_user_change_requests():
        """Get current user's change requests"""
        try:
            requests = ChangeRequest.query.filter_by(user_id=current_user.id).order_by(
                ChangeRequest.created_at.desc()
            ).all()
            
            return jsonify({
                'status': 'success',
                'requests': [req.to_dict() for req in requests]
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/admin/change-requests', methods=['GET'])
    @admin_required
    def get_all_change_requests():
        """Get all change requests (admin only)"""
        
        try:
            status_filter = request.args.get('status', 'pending')
            query = ChangeRequest.query
            
            if status_filter != 'all':
                query = query.filter_by(status=status_filter)
            
            requests = query.order_by(ChangeRequest.created_at.desc()).all()
            
            return jsonify({
                'status': 'success',
                'requests': [req.to_dict() for req in requests]
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/admin/change-request/<int:request_id>/approve', methods=['POST'])
    @admin_required
    def approve_change_request(request_id):
        """Approve a change request and apply the changes (admin only)"""
        
        try:
            change_req = db.session.get(ChangeRequest, request_id)
            if not change_req:
                return jsonify({'status': 'error', 'message': 'Request not found'}), 404
            
            # Get the user whose data needs to be changed
            user = db.session.get(User, change_req.user_id)
            if not user:
                return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
            # Apply the change
            field_name = change_req.field_name
            new_value = change_req.proposed_value
            
            if hasattr(user, field_name):
                setattr(user, field_name, new_value)
            else:
                return jsonify({'status': 'error', 'message': f'Invalid field: {field_name}'}), 400
            
            # Update request status
            change_req.status = 'approved'
            change_req.reviewed_by = current_user.id
            change_req.reviewed_at = datetime.utcnow()
            
            # Get admin notes from request body if provided
            data = request.get_json() or {}
            if 'admin_notes' in data:
                change_req.admin_notes = data['admin_notes']
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Change request approved and applied',
                'request': change_req.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/admin/change-request/<int:request_id>/deny', methods=['POST'])
    @admin_required
    def deny_change_request(request_id):
        """Deny a change request (admin only)"""
        
        try:
            change_req = db.session.get(ChangeRequest, request_id)
            if not change_req:
                return jsonify({'status': 'error', 'message': 'Request not found'}), 404
            
            # Update request status
            change_req.status = 'denied'
            change_req.reviewed_by = current_user.id
            change_req.reviewed_at = datetime.utcnow()
            
            # Get admin notes from request body
            data = request.get_json() or {}
            if 'admin_notes' in data:
                change_req.admin_notes = data['admin_notes']
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Change request denied',
                'request': change_req.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # Admin Routes
    @app.route('/admin')
    @admin_required
    def admin_panel():
        """Admin panel for managing presenter assignments"""
        
        # Get all posters with their assignments
        posters = Poster.query.order_by(Poster.poster_number).all()
        
        # Get all users for assignment dropdown
        users = User.query.order_by(User.username).all()
        
        return render_template('admin.html', posters=posters, users=users)
    
    @app.route('/admin/assign-presenter', methods=['POST'])
    @admin_required
    def assign_presenter():
        """Assign a presenter to a poster"""
        
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
    @admin_required
    def auto_assign_presenters():
        """Auto-assign presenters based on name matching"""
        
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
    @admin_required
    def unassign_all_presenters():
        """Unassign all presenters from all posters"""
        
        Poster.query.update({'presenter_id': None})
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'All posters unassigned successfully'
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Only create tables if not in production (Railway handles this via quick_init.py)
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
    
    # Start Flask server first - healthcheck must pass!
    # Admin creation happens on first request via before_first_request
    app.run(debug=debug, host=host, port=port)

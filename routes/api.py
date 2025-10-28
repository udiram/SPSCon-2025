from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Favorite, Visit, PresenterStatus, Poster
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/favorite/<int:poster_id>', methods=['POST'])
@login_required
def toggle_favorite(poster_id):
    """Toggle favorite status for a poster"""
    poster = Poster.query.get_or_404(poster_id)
    
    favorite = Favorite.query.filter_by(user_id=current_user.id, poster_id=poster_id).first()
    
    if favorite:
        # Remove from favorites
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'status': 'removed', 'message': 'Removed from favorites'})
    else:
        # Add to favorites
        favorite = Favorite(user_id=current_user.id, poster_id=poster_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'status': 'added', 'message': 'Added to favorites'})

@api_bp.route('/visit/<int:poster_id>', methods=['POST'])
@login_required
def mark_visited(poster_id):
    """Mark a poster as visited"""
    poster = Poster.query.get_or_404(poster_id)
    
    # Check if already visited
    visit = Visit.query.filter_by(user_id=current_user.id, poster_id=poster_id).first()
    
    if not visit:
        visit = Visit(user_id=current_user.id, poster_id=poster_id)
        db.session.add(visit)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Marked as visited'})
    else:
        return jsonify({'status': 'already_visited', 'message': 'Already marked as visited'})

@api_bp.route('/presenter-status/<int:poster_id>', methods=['POST'])
@login_required
def toggle_presenter_status(poster_id):
    """Toggle presenter availability status"""
    poster = Poster.query.get_or_404(poster_id)
    
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

@api_bp.route('/presenter-status/<int:poster_id>')
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

@api_bp.route('/export/csv')
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


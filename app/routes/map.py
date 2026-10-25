"""
ResQAI Live Incident Map Blueprint.
Serves interactive Leaflet disaster mapping interface and privacy-controlled spatial API.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from app.services.map_service import get_map_incidents, get_map_summary_stats, CATEGORY_COLORS

map_bp = Blueprint('map', __name__)

@map_bp.route('/map')
def index():
    """Render interactive emergency incident map view with category & status filters."""
    stats = get_map_summary_stats()
    categories = list(CATEGORY_COLORS.keys())
    return render_template(
        'map/index.html',
        stats=stats,
        categories=categories,
        category_colors=CATEGORY_COLORS
    )

@map_bp.route('/api/map/incidents')
def map_incidents_api():
    """
    Public and Responder JSON endpoint for Leaflet markers.
    Applies automatic privacy masking based on user authentication and role.
    """
    category = request.args.get('category', 'all')
    status = request.args.get('status', 'all')
    
    incidents = get_map_incidents(category=category, status=status, user=current_user)
    return jsonify({
        'status': 'success',
        'count': len(incidents),
        'incidents': incidents
    })

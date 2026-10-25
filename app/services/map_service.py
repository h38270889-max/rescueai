"""
ResQAI Interactive Map Service.
Handles spatial querying, Leaflet marker preparation, category/urgency color coding,
and role-based privacy protection (coordinate approximation and PII masking for public viewers).
"""

from app.models.incident import EmergencyReport

# Color mapping by emergency category
CATEGORY_COLORS = {
    'Medical Emergency': '#e63946',
    'Fire Outbreak': '#f77f00',
    'Flood / Waterlogging': '#0077b6',
    'Earthquake': '#8d5b4c',
    'Road Accident': '#7209b7',
    'Cyclone / Severe Storm': '#023e8a',
    'Landslide': '#936639',
    'Building Collapse': '#5a189a',
    'Hazardous Material / Gas Leak': '#d90429',
    'General Emergency': '#495057'
}

# Urgency pin styles
URGENCY_COLORS = {
    'Critical': '#d90429',
    'High': '#f77f00',
    'Medium': '#0077b6',
    'Low': '#2b9348'
}


def get_map_incidents(category=None, status=None, user=None):
    """
    Query incidents with valid geographic coordinates and format them for Leaflet rendering.
    Enforces privacy protection for non-responders:
      - Ordinary users & public: GPS coordinates rounded to 2 decimal places (~1.1 km precision)
        and personal phone/names masked to prevent doxxing or vigilantism.
      - Responders & Admins: Exact GPS coordinates, reporter phone number, and internal notes.
    """
    query = EmergencyReport.query.filter(
        EmergencyReport.latitude.isnot(None),
        EmergencyReport.longitude.isnot(None)
    )

    if category and category != 'all':
        query = query.filter(EmergencyReport.category == category)

    if status and status != 'all':
        query = query.filter(EmergencyReport.status == status)

    incidents = query.order_by(EmergencyReport.created_at.desc()).all()

    is_privileged = user is not None and (user.is_responder or user.is_admin)

    features = []
    for inc in incidents:
        # Privacy filtering for public / citizen role
        if is_privileged:
            lat = inc.latitude
            lon = inc.longitude
            reporter_name = inc.contact_name or 'Anonymous Submitter'
            reporter_phone = inc.contact_phone or 'Not Provided'
            is_approx = False
        else:
            # Round coordinates to 2 decimal places for approximate privacy preservation
            lat = round(inc.latitude, 2)
            lon = round(inc.longitude, 2)
            reporter_name = 'Confidential (Protected Citizen)'
            reporter_phone = 'Hidden for privacy'
            is_approx = True

        marker = {
            'id': inc.id,
            'incident_id': inc.incident_id,
            'category': inc.category,
            'priority': inc.ai_suggested_priority,
            'status': inc.status,
            'description': inc.translated_description or inc.description,
            'original_language': inc.original_language,
            'latitude': lat,
            'longitude': lon,
            'is_approximate': is_approx,
            'location_address': inc.location_address or 'Location Coordinates Provided',
            'affected_count': inc.affected_count,
            'contact_name': reporter_name,
            'contact_phone': reporter_phone,
            'created_at': inc.created_at.strftime('%Y-%m-%d %H:%M UTC') if inc.created_at else None,
            'category_color': CATEGORY_COLORS.get(inc.category, '#495057'),
            'priority_color': URGENCY_COLORS.get(inc.ai_suggested_priority, '#0077b6'),
            'badge_class': inc.badge_class,
            'priority_badge_class': inc.priority_badge_class,
            'is_potential_duplicate': inc.is_potential_duplicate,
            'has_image': bool(inc.image_filename)
        }
        features.append(marker)

    return features


def get_map_summary_stats():
    """Aggregate high-level metrics for the map sidebar."""
    from extensions import db
    from sqlalchemy import func

    total_mapped = EmergencyReport.query.filter(
        EmergencyReport.latitude.isnot(None),
        EmergencyReport.longitude.isnot(None)
    ).count()

    active_count = EmergencyReport.query.filter(
        EmergencyReport.latitude.isnot(None),
        EmergencyReport.longitude.isnot(None),
        EmergencyReport.status.in_(['Submitted', 'Under Review', 'Assigned', 'In Progress'])
    ).count()

    critical_count = EmergencyReport.query.filter(
        EmergencyReport.latitude.isnot(None),
        EmergencyReport.longitude.isnot(None),
        EmergencyReport.ai_suggested_priority == 'Critical',
        EmergencyReport.status != 'Resolved'
    ).count()

    return {
        'total_mapped': total_mapped,
        'active_incidents': active_count,
        'critical_active': critical_count
    }

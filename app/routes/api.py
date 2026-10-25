from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_login import current_user
from extensions import db, csrf
from app.models.incident import EmergencyReport, IncidentStatusHistory
from app.models.notification import PushSubscription
from app.models.audit import AuditLog
from app.services.ai_service import classify_and_triage
from app.services.translation_service import translate_emergency_message

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Exclude JSON API from CSRF token checks to support offline IndexedDB sync and WebPush subscriptions
@csrf.exempt
@api_bp.route('/sync/report', methods=['POST'])
def sync_offline_report():
    """
    Offline report synchronization endpoint with Idempotency Key validation.
    Prevents duplicate incident creation during network retries or flapping connections.
    """
    data = request.get_json(silent=True) or {}
    idempotency_key = data.get('idempotency_key')
    
    if not idempotency_key:
        return jsonify({'error': 'idempotency_key is required for offline sync.'}), 400

    # 1. Idempotency Check: prevent duplicate submission
    existing = EmergencyReport.query.filter_by(idempotency_key=idempotency_key).first()
    if existing:
        return jsonify({
            'status': 'synced',
            'is_duplicate': True,
            'incident_id': existing.incident_id,
            'message': 'Report already received and safely stored on server.'
        }), 200

    description = data.get('description', '').strip()
    if not description:
        return jsonify({'error': 'Incident description cannot be empty.'}), 400

    category = data.get('category', 'other')
    lang = data.get('original_language', 'en')

    # 2. AI Triage & Translation
    triage = classify_and_triage(description, language=lang)
    translation = translate_emergency_message(description, source_lang=lang, target_lang='en')

    # 3. Create Report Record
    report = EmergencyReport(
        idempotency_key=idempotency_key,
        user_id=current_user.id if current_user.is_authenticated else None,
        category=category,
        description=description,
        original_language=lang,
        translated_description=translation.get('translated_text'),
        translation_confidence=translation.get('confidence'),
        translation_service=translation.get('service'),
        contact_name=data.get('contact_name'),
        contact_phone=data.get('contact_phone'),
        location_address=data.get('location_address'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        affected_count=int(data.get('affected_count', 1)),
        status='Submitted',
        ai_suggested_category=triage.get('category'),
        ai_suggested_priority=triage.get('urgency', 'Medium'),
        ai_classification_explanation=triage.get('explanation'),
        is_high_risk=triage.get('is_high_risk', False)
    )
    db.session.add(report)
    db.session.flush()

    history = IncidentStatusHistory(
        incident_id=report.id,
        old_status=None,
        new_status='Submitted',
        changed_by_user_id=current_user.id if current_user.is_authenticated else None,
        notes='Synchronized from client offline IndexedDB queue.'
    )
    db.session.add(history)

    AuditLog.log(
        action='OFFLINE_REPORT_SYNCED',
        user_id=current_user.id if current_user.is_authenticated else None,
        target_type='incident',
        target_id=report.id,
        ip_address=request.remote_addr,
        details=f"Offline report synced with idempotency key: {idempotency_key[:8]}..."
    )
    db.session.commit()

    return jsonify({
        'status': 'synced',
        'is_duplicate': False,
        'incident_id': report.incident_id,
        'priority': report.ai_suggested_priority,
        'message': f"Offline emergency report successfully uploaded as {report.incident_id}."
    }), 201


@csrf.exempt
@api_bp.route('/push/subscribe', methods=['POST'])
def push_subscribe():
    """Register browser Web Push subscription."""
    data = request.get_json(silent=True) or {}
    endpoint = data.get('endpoint')
    keys = data.get('keys', {})
    p256dh = keys.get('p256dh')
    auth = keys.get('auth')

    if not endpoint or not p256dh or not auth:
        return jsonify({'error': 'Invalid subscription payload.'}), 400

    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if not existing:
        sub = PushSubscription(
            user_id=current_user.id if current_user.is_authenticated else None,
            endpoint=endpoint,
            p256dh_key=p256dh,
            auth_key=auth
        )
        db.session.add(sub)
        db.session.commit()

    return jsonify({'success': True, 'message': 'WebPush subscription registered.'})


@csrf.exempt
@api_bp.route('/offline-sync', methods=['POST'])
def offline_sync_batch():
    """Batch endpoint for offline reports from IndexedDB."""
    data = request.get_json(silent=True) or {}
    reports = data.get('reports', [])
    results = []

    for item in reports:
        idemp = item.get('idempotency_key')
        if not idemp:
            continue
        existing = EmergencyReport.query.filter_by(idempotency_key=idemp).first()
        if existing:
            results.append({
                'idempotency_key': idemp,
                'status': 'already_synced',
                'incident_id': existing.incident_id
            })
            continue

        desc = item.get('description', '').strip()
        cat = item.get('category', 'other')
        lang = item.get('original_language', 'en')
        triage = classify_and_triage(desc, language=lang)
        translation = translate_emergency_message(desc, source_lang=lang, target_lang='en')

        rep = EmergencyReport(
            idempotency_key=idemp,
            user_id=current_user.id if current_user.is_authenticated else None,
            category=cat,
            description=desc,
            original_language=lang,
            translated_description=translation.get('translated_text'),
            latitude=item.get('latitude'),
            longitude=item.get('longitude'),
            affected_count=int(item.get('affected_count', 1)),
            status='Submitted',
            ai_suggested_category=triage.get('category'),
            ai_suggested_priority=triage.get('urgency', 'Medium'),
            is_high_risk=triage.get('is_high_risk', False)
        )
        db.session.add(rep)
        db.session.flush()

        results.append({
            'idempotency_key': idemp,
            'status': 'synced',
            'incident_id': rep.incident_id
        })

    db.session.commit()
    return jsonify({'status': 'success', 'results': results}), 200


@api_bp.route('/ping', methods=['GET'])
def ping():
    """Connectivity check endpoint for online/offline synchronization listeners."""
    return jsonify({
        'status': 'online',
        'service': 'ResQAI Emergency Core',
        'server_time': datetime.now(timezone.utc).isoformat()
    })

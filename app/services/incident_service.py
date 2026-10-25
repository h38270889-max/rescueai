"""
ResQAI Incident Orchestration Service.
Coordinates AI classification, multilingual translation, duplicate detection,
idempotent deduplication, status history logging, and one-tap SOS beacon creation.
"""

from extensions import db
from app.models.incident import EmergencyReport, IncidentStatusHistory
from app.models.audit import AuditLog
from app.services.ai_service import classify_and_triage
from app.services.translation_service import translate_emergency_message
from app.services.duplicate_service import check_for_duplicates


def submit_emergency_incident(
    description,
    category=None,
    original_language='en',
    contact_name=None,
    contact_phone=None,
    location_address=None,
    latitude=None,
    longitude=None,
    affected_count=1,
    image_filename=None,
    user_id=None,
    idempotency_key=None,
    client_ip=None
):
    """
    Primary pipeline for ingesting an emergency report:
    1. Idempotency deduplication check.
    2. AI classification & urgency scoring.
    3. Multilingual translation to English for central dispatch.
    4. Database persistence and status history log.
    5. Screen against existing incidents for potential duplicate matches.
    """
    # 1. Idempotency check
    if idempotency_key:
        existing = EmergencyReport.query.filter_by(idempotency_key=idempotency_key).first()
        if existing:
            return existing, existing.is_potential_duplicate, None, None

    # 2. AI Triage & Urgency Classification
    triage = classify_and_triage(description, language=original_language)
    final_category = category or triage.get('category', 'General Emergency')
    priority = triage.get('urgency', 'Medium')
    is_high_risk = triage.get('is_high_risk', False)
    explanation = triage.get('explanation', '')

    # 3. Translation for unified responder coordination
    translation = translate_emergency_message(description, source_lang=original_language, target_lang='en')

    # 4. Create database entity
    report = EmergencyReport(
        user_id=user_id,
        category=final_category,
        description=description,
        original_language=original_language,
        translated_description=translation.get('translated_text'),
        translation_confidence=translation.get('confidence'),
        translation_service=translation.get('service'),
        contact_name=contact_name,
        contact_phone=contact_phone,
        location_address=location_address,
        latitude=latitude,
        longitude=longitude,
        affected_count=affected_count or 1,
        image_filename=image_filename,
        idempotency_key=idempotency_key,
        status='Submitted',
        ai_suggested_category=triage.get('category'),
        ai_suggested_priority=priority,
        ai_classification_explanation=explanation,
        is_high_risk=is_high_risk
    )
    db.session.add(report)
    db.session.flush()

    # Initial Status History
    history = IncidentStatusHistory(
        incident_id=report.id,
        old_status=None,
        new_status='Submitted',
        changed_by_user_id=user_id,
        notes='Emergency report filed via system portal.'
    )
    db.session.add(history)

    # 5. Screen for potential duplicate reports
    is_dup, match_cand, match_rec = check_for_duplicates(report)

    # 6. Audit Log
    AuditLog.log(
        action='INCIDENT_SUBMITTED',
        user_id=user_id,
        target_type='incident',
        target_id=report.id,
        ip_address=client_ip,
        details=f"Incident {report.incident_id} filed in {original_language}. Priority: {priority}. Duplicate flagged: {is_dup}"
    )

    db.session.commit()
    return report, is_dup, match_cand, match_rec


def trigger_one_tap_sos(latitude, longitude, user=None, contact_phone=None, contact_name=None, client_ip=None, language='en'):
    """
    Instantaneous one-tap SOS emergency beacon.
    Bypasses long questionnaires, automatically classifies as Critical,
    and flags for priority emergency dispatch.
    """
    sos_description = "URGENT DISTRESS BEACON: One-Tap SOS triggered with GPS coordinates. Submitter requires immediate emergency response."

    user_id = user.id if user and user.is_authenticated else None
    name = contact_name or (user.full_name if user and user.is_authenticated else 'Emergency Submitter')
    phone = contact_phone or (user.phone if user and user.is_authenticated else None)

    report = EmergencyReport(
        user_id=user_id,
        category='Medical Emergency',
        description=sos_description,
        original_language=language,
        translated_description=sos_description,
        contact_name=name,
        contact_phone=phone,
        location_address=f"GPS Fix: {latitude:.4f}, {longitude:.4f}" if latitude and longitude else "Coordinates Pending",
        latitude=latitude,
        longitude=longitude,
        affected_count=1,
        status='Submitted',
        ai_suggested_category='Medical Emergency',
        ai_suggested_priority='Critical',
        ai_classification_explanation="Instantaneous One-Tap SOS Distress Beacon triggered. Immediate life-safety intervention requested.",
        is_high_risk=True
    )
    db.session.add(report)
    db.session.flush()

    # Status History
    history = IncidentStatusHistory(
        incident_id=report.id,
        old_status=None,
        new_status='Submitted',
        changed_by_user_id=user_id,
        notes='Immediate One-Tap SOS Distress Beacon recorded.'
    )
    db.session.add(history)

    # Screen duplicate
    is_dup, match_cand, match_rec = check_for_duplicates(report)

    # Audit log
    AuditLog.log(
        action='ONE_TAP_SOS_TRIGGERED',
        user_id=user_id,
        target_type='incident',
        target_id=report.id,
        ip_address=client_ip,
        details=f"One-Tap SOS Incident {report.incident_id} triggered at lat={latitude}, lon={longitude}."
    )

    db.session.commit()
    return report

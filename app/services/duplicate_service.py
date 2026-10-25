"""
ResQAI Duplicate Incident Detection Service.
Uses explainable TF-IDF cosine text similarity combined with geospatial Haversine distance
and temporal windows to flag potential duplicate disaster reports for human administrator review.
"""

import math
import re
from datetime import datetime, timedelta, timezone
from flask import current_app
from extensions import db
from app.models.incident import EmergencyReport, PotentialDuplicateMatch
from app.models.audit import AuditLog

# Common stop words for text normalization
STOP_WORDS = {
    'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'in', 'to', 'for',
    'of', 'with', 'by', 'from', 'my', 'we', 'our', 'i', 'am', 'are', 'was', 'were',
    'हे', 'आहे', 'आणि', 'व', 'का', 'के', 'में', 'पर', 'से', 'को', 'और', 'है', 'था'
}

def tokenize_and_clean(text):
    """Normalize text into lowercase alphanumeric tokens, filtering stop words."""
    if not text:
        return []
    words = re.findall(r'\b\w+\b', text.lower())
    return [w for w in words if len(w) > 1 and w not in STOP_WORDS]

def compute_tf_idf_cosine_similarity(text1, text2):
    """
    Compute explainable TF-IDF Cosine Similarity between two incident texts.
    No heavy external libraries required — pure Python, fast and robust.
    """
    tokens1 = tokenize_and_clean(text1)
    tokens2 = tokenize_and_clean(text2)

    if not tokens1 or not tokens2:
        return 0.0

    all_tokens = list(set(tokens1 + tokens2))
    if not all_tokens:
        return 0.0

    # Term frequency (TF)
    tf1 = {t: tokens1.count(t) / len(tokens1) for t in all_tokens}
    tf2 = {t: tokens2.count(t) / len(tokens2) for t in all_tokens}

    # Inverse document frequency (IDF) over the 2-doc corpus
    idf = {}
    for t in all_tokens:
        doc_count = (1 if t in tokens1 else 0) + (1 if t in tokens2 else 0)
        idf[t] = math.log((2 + 1) / (doc_count + 1)) + 1

    # TF-IDF vectors
    vec1 = [tf1[t] * idf[t] for t in all_tokens]
    vec2 = [tf2[t] * idf[t] for t in all_tokens]

    # Cosine Similarity: dot(v1, v2) / (||v1|| * ||v2||)
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return round(dot_product / (mag1 * mag2), 3)

def haversine_distance_km(lat1, lon1, lat2, lon2):
    """Calculate Great Circle distance in kilometers between two GPS coordinates."""
    if None in (lat1, lon1, lat2, lon2):
        return None

    r = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r * c, 2)

def check_for_duplicates(report):
    """
    Screen an emergency report against recent incidents.
    If similarity exceeds threshold, flag it and create a PotentialDuplicateMatch record.
    Returns:
        tuple: (is_duplicate_flagged, top_match_report, match_record)
    """
    time_window_hours = current_app.config.get('DUPLICATE_TIME_WINDOW_HOURS', 24)
    threshold = current_app.config.get('DUPLICATE_SIMILARITY_THRESHOLD', 0.55)
    distance_threshold_km = current_app.config.get('DUPLICATE_DISTANCE_KM_THRESHOLD', 5.0)

    cutoff_time = (report.created_at or datetime.now(timezone.utc)) - timedelta(hours=time_window_hours)

    # Query recent incidents excluding the current report itself
    candidates = EmergencyReport.query.filter(
        EmergencyReport.id != report.id,
        EmergencyReport.created_at >= cutoff_time
    ).all()

    top_score = 0.0
    top_candidate = None
    top_distance = None
    top_time_diff = None
    match_reason = None

    for cand in candidates:
        # 1. Text Similarity (original or translated)
        text_a = f"{report.description} {report.translated_description or ''}"
        text_b = f"{cand.description} {cand.translated_description or ''}"
        text_sim = compute_tf_idf_cosine_similarity(text_a, text_b)

        # 2. Category Match
        cat_sim = 1.0 if report.category == cand.category else 0.0

        # 3. Geospatial Proximity
        dist = haversine_distance_km(report.latitude, report.longitude, cand.latitude, cand.longitude)
        if dist is not None:
            if dist <= 1.0:
                dist_sim = 1.0
            elif dist <= distance_threshold_km:
                dist_sim = max(0.0, 1.0 - (dist / distance_threshold_km))
            else:
                dist_sim = 0.0
        else:
            dist_sim = 0.5  # Neutral when coordinates not provided

        # Composite Weighted Score
        composite = (text_sim * 0.55) + (cat_sim * 0.25) + (dist_sim * 0.20)

        if composite > top_score:
            top_score = composite
            top_candidate = cand
            top_distance = dist
            time_diff = abs((report.created_at - cand.created_at).total_seconds()) / 3600.0 if report.created_at and cand.created_at else 0.0
            top_time_diff = round(time_diff, 1)
            match_reason = f"Text Sim: {int(text_sim*100)}% | Category: {cand.category} | Proximity: {dist}km" if dist is not None else f"Text Sim: {int(text_sim*100)}% | Category: {cand.category}"

    if top_score >= threshold and top_candidate:
        # Flag the report
        report.is_potential_duplicate = True
        report.potential_duplicate_of_id = top_candidate.id
        report.duplicate_similarity_score = round(top_score, 2)
        report.duplicate_match_reason = match_reason
        report.duplicate_review_status = 'flagged'

        # Record pairwise match
        match = PotentialDuplicateMatch(
            incident_a_id=top_candidate.id,
            incident_b_id=report.id,
            similarity_score=round(top_score, 2),
            distance_km=top_distance,
            time_diff_hours=top_time_diff,
            match_reason=match_reason,
            status='pending'
        )
        db.session.add(match)
        db.session.commit()
        return (True, top_candidate, match)

    return (False, None, None)

def review_duplicate_match(match_id, decision, reviewer_user_id, notes=None):
    """
    Administrator confirmation or rejection of a suspected duplicate incident.
    decision: 'confirmed_duplicate' | 'rejected_distinct'
    """
    match = PotentialDuplicateMatch.query.get_or_404(match_id)
    match.status = decision
    match.reviewed_by_user_id = reviewer_user_id
    match.review_notes = notes
    match.reviewed_at = datetime.now(timezone.utc)

    report_b = match.incident_b
    if report_b:
        report_b.duplicate_review_status = decision
        if decision == 'rejected_distinct':
            report_b.is_potential_duplicate = False

    AuditLog.log(
        action='DUPLICATE_REVIEW_DECISION',
        user_id=reviewer_user_id,
        target_type='duplicate_match',
        target_id=match.id,
        details=f"Decision: {decision} for incident {match.incident_b_id} matching {match.incident_a_id}. Notes: {notes}"
    )

    db.session.commit()
    return match

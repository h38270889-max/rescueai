"""
Unit and integration tests for ResQAI Duplicate Incident Screener.
Tests TF-IDF cosine similarity, geospatial Haversine distance,
duplicate threshold matching, and administrative review decisions.
"""

from datetime import datetime, timezone
from extensions import db
from app.models.incident import EmergencyReport, PotentialDuplicateMatch
from app.services.duplicate_service import (
    compute_tf_idf_cosine_similarity,
    haversine_distance_km,
    check_for_duplicates,
    review_duplicate_match
)

def test_tf_idf_cosine_similarity():
    text1 = "Major building fire on the third floor with heavy smoke"
    text2 = "Building fire on third floor with heavy smoke and residents trapped"
    text3 = "Flooded road with water overflowing from river bank"

    sim_similar = compute_tf_idf_cosine_similarity(text1, text2)
    sim_different = compute_tf_idf_cosine_similarity(text1, text3)

    assert sim_similar > 0.50
    assert sim_different < 0.20

def test_haversine_distance():
    # Mumbai CST to Churchgate (~2.1 km)
    dist = haversine_distance_km(18.9401, 72.8354, 18.9322, 72.8264)
    assert 1.0 < dist < 3.0

    # Same location
    dist_zero = haversine_distance_km(19.0760, 72.8777, 19.0760, 72.8777)
    assert dist_zero == 0.0

def test_duplicate_incident_detection_and_review(app, test_users):
    with app.app_context():
        admin_id = test_users['admin_id']
        citizen1_id = test_users['citizen1_id']
        citizen2_id = test_users['citizen2_id']

        # Report 1
        rep1 = EmergencyReport(
            user_id=citizen1_id,
            category="Fire Outbreak",
            description="Electrical transformer fire at SV Road market near subway",
            latitude=19.1197,
            longitude=72.8464,
            status="In Progress"
        )
        db.session.add(rep1)
        db.session.commit()

        # Report 2 (reported nearby with similar description)
        rep2 = EmergencyReport(
            user_id=citizen2_id,
            category="Fire Outbreak",
            description="Massive electrical transformer explosion and fire on SV Road near subway entrance",
            latitude=19.1200,
            longitude=72.8468,
            status="Submitted"
        )
        db.session.add(rep2)
        db.session.commit()

        # Run duplicate check
        is_dup, match_cand, match_rec = check_for_duplicates(rep2)
        assert is_dup is True
        assert match_cand.id == rep1.id
        assert match_rec is not None
        assert match_rec.similarity_score >= 0.55
        assert rep2.is_potential_duplicate is True

        # Administrator confirms duplicate
        reviewed_match = review_duplicate_match(
            match_id=match_rec.id,
            decision='confirmed_duplicate',
            reviewer_user_id=admin_id,
            notes='Verified by fire dispatch unit.'
        )
        assert reviewed_match.status == 'confirmed_duplicate'
        assert rep2.duplicate_review_status == 'confirmed_duplicate'

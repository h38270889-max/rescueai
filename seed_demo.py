"""
ResQAI Demo Data Seeding Script.
Populates local development database with realistic users, multilingual incidents,
triage classifications, status histories, emergency alerts, and notifications.
"""

import os
from datetime import datetime, timedelta, timezone
from app import create_app
from extensions import db
from app.models.user import User
from app.models.incident import EmergencyReport, IncidentStatusHistory, PotentialDuplicateMatch
from app.models.alert import EmergencyAlert
from app.models.notification import UserNotification
from app.models.family import FamilyContact, FamilyCheckIn
from app.models.audit import AuditLog
from app.services.classification_rules import classify_message_rule_based
from app.services.translation_service import translate_emergency_message

def seed_database():
    app = create_app('development')
    with app.app_context():
        print("Initializing ResQAI database tables...")
        db.drop_all()
        db.create_all()

        now = datetime.now(timezone.utc)

        print("Seeding demo user accounts...")
        # 1. Admin Account
        admin = User(
            full_name="Emergency Operations Commander (Admin)",
            email="admin@resqai.org",
            phone="+91 98200 11111",
            role="admin",
            preferred_language="en",
            region="Mumbai Metro",
            consent_emergency_notifications=True
        )
        admin.set_password("Admin@12345")
        db.session.add(admin)

        # 2. Responder Accounts
        responder_1 = User(
            full_name="Rajesh Kadam (NDRF Disaster Response)",
            email="responder.rajesh@resqai.org",
            phone="+91 98200 22222",
            role="responder",
            preferred_language="mr",
            region="Mumbai Metro",
            consent_emergency_notifications=True
        )
        responder_1.set_password("Responder@123")
        db.session.add(responder_1)

        responder_2 = User(
            full_name="Dr. Priya Sharma (Emergency Medical Officer)",
            email="responder.priya@resqai.org",
            phone="+91 98200 33333",
            role="responder",
            preferred_language="hi",
            region="Pune Region",
            consent_emergency_notifications=True
        )
        responder_2.set_password("Responder@123")
        db.session.add(responder_2)

        # 3. Citizen User Accounts
        citizen_1 = User(
            full_name="Aarav Patel",
            email="user.aarav@example.com",
            phone="+91 98200 44444",
            role="user",
            preferred_language="hi",
            region="Mumbai Metro",
            consent_emergency_notifications=True
        )
        citizen_1.set_password("User@123")
        db.session.add(citizen_1)

        citizen_2 = User(
            full_name="Sneha Deshmukh",
            email="user.sneha@example.com",
            phone="+91 98200 55555",
            role="user",
            preferred_language="mr",
            region="Pune Region",
            consent_emergency_notifications=True
        )
        citizen_2.set_password("User@123")
        db.session.add(citizen_2)

        citizen_3 = User(
            full_name="Tariq Ahmed",
            email="user.tariq@example.com",
            phone="+91 98200 66666",
            role="user",
            preferred_language="ur",
            region="Delhi NCR",
            consent_emergency_notifications=True
        )
        citizen_3.set_password("User@123")
        db.session.add(citizen_3)

        citizen_4 = User(
            full_name="Maria Garcia",
            email="user.maria@example.com",
            phone="+91 98200 77777",
            role="user",
            preferred_language="es",
            region="Goa Coastal",
            consent_emergency_notifications=True
        )
        citizen_4.set_password("User@123")
        db.session.add(citizen_4)

        db.session.commit()

        print("Seeding multilingual incident reports with AI triage...")
        incidents_data = [
            {
                'user': citizen_1,
                'category': 'medical',
                'desc': 'My elderly grandfather is having severe chest pain, breathing difficulties and is semi-unconscious. Please send an ambulance immediately.',
                'lang': 'en',
                'contact_name': 'Aarav Patel',
                'contact_phone': '+91 98200 44444',
                'address': 'B-304, Green Palms Apt, Andheri East, Mumbai',
                'lat': 19.1136,
                'lng': 72.8697,
                'affected': 1,
                'status': 'In Progress',
                'responder': responder_2,
                'notes': 'Ambulance 108 dispatched from Cooper Hospital. ETA 8 minutes.'
            },
            {
                'user': citizen_2,
                'category': 'flood',
                'desc': 'आमच्या सोसायटीत तळमजल्यावर ४ फूट पाणी भरले आहे. १० कुटुंबे आणि लहान मुले वरच्या मजल्यावर अडकली आहेत. वीज गेली आहे, बोटीची गरज आहे.',
                'lang': 'mr',
                'contact_name': 'Sneha Deshmukh',
                'contact_phone': '+91 98200 55555',
                'address': 'Kothrud Riverside Society, Karve Road, Pune',
                'lat': 18.5074,
                'lng': 73.8077,
                'affected': 28,
                'status': 'Assigned',
                'responder': responder_1,
                'notes': 'NDRF rescue inflatable boat deployed from Pune base station.'
            },
            {
                'user': citizen_1,
                'category': 'fire',
                'desc': 'इमारत की तीसरी मंजिल पर भीषण आग लगी है और सीढ़ियों में घना काला धुआं भरा है। लोग बालकनी में फंसे हैं।',
                'lang': 'hi',
                'contact_name': 'Ramesh Kumar',
                'contact_phone': '+91 98111 22233',
                'address': 'Plot 12, Industrial Area, Kurla West, Mumbai',
                'lat': 19.0688,
                'lng': 72.8807,
                'affected': 15,
                'status': 'Under Review',
                'responder': None,
                'notes': None
            },
            {
                'user': citizen_3,
                'category': 'earthquake',
                'desc': 'زلزلے کے بعد پرانی عمارت کی چھت کا ایک حصہ گر گیا ہے۔ ملبے کے نیچے دو مزدور پھنسے ہوئے ہیں اور مدد کے لیے پکار رہے ہیں۔',
                'lang': 'ur',
                'contact_name': 'Tariq Ahmed',
                'contact_phone': '+91 98200 66666',
                'address': 'Gali 4, Chandni Chowk, Old Delhi',
                'lat': 28.6506,
                'lng': 77.2303,
                'affected': 2,
                'status': 'Submitted',
                'responder': None,
                'notes': None
            },
            {
                'user': citizen_4,
                'category': 'road_accident',
                'desc': 'Colisión frontal múltiple entre dos vehículos en la autopista costera. Dos personas lesionadas conscientes pero atrapadas con cinturón.',
                'lang': 'es',
                'contact_name': 'Maria Garcia',
                'contact_phone': '+91 98200 77777',
                'address': 'NH-66 Highway, Near Candolim Junction, Goa',
                'lat': 15.5186,
                'lng': 73.7667,
                'affected': 3,
                'status': 'Resolved',
                'responder': responder_1,
                'notes': 'Police and Highway Patrol safely extricated all occupants and transferred them to District Hospital.'
            },
            {
                'user': citizen_2,
                'category': 'shelter_request',
                'desc': 'Heavy rain and landslide damaged 6 homes in our hamlet. 24 villagers need emergency dry shelter, drinking water and blankets tonight.',
                'lang': 'en',
                'contact_name': 'Gram Panchayat Sarpanch',
                'contact_phone': '+91 98333 44455',
                'address': 'Bhor Hills Valley Village, Pune Outskirts',
                'lat': 18.1500,
                'lng': 73.8500,
                'affected': 24,
                'status': 'In Progress',
                'responder': responder_1,
                'notes': 'Zilla Parishad School opened as designated emergency relief shelter. Relief supplies in transit.'
            }
        ]

        created_incidents = []
        for idx, inc in enumerate(incidents_data):
            triage = classify_message_rule_based(inc['desc'])
            trans = translate_emergency_message(inc['desc'], source_lang=inc['lang'], target_lang='en')

            report = EmergencyReport(
                user_id=inc['user'].id,
                category=inc['category'],
                description=inc['desc'],
                original_language=inc['lang'],
                translated_description=trans.get('translated_text'),
                translation_confidence=trans.get('confidence'),
                translation_service=trans.get('service'),
                contact_name=inc['contact_name'],
                contact_phone=inc['contact_phone'],
                location_address=inc['address'],
                latitude=inc['lat'],
                longitude=inc['lng'],
                affected_count=inc['affected'],
                status=inc['status'],
                ai_suggested_category=triage.get('category'),
                ai_suggested_priority=triage.get('urgency', 'High'),
                ai_classification_explanation=triage.get('explanation'),
                is_high_risk=triage.get('is_high_risk', False),
                assigned_responder_id=inc['responder'].id if inc['responder'] else None,
                responder_notes=inc['notes'],
                created_at=now - timedelta(hours=(idx * 4) + 1)
            )
            db.session.add(report)
            db.session.flush()

            # Status history
            hist1 = IncidentStatusHistory(
                incident_id=report.id,
                old_status=None,
                new_status='Submitted',
                changed_by_user_id=inc['user'].id,
                notes='Initial emergency report submitted.',
                created_at=report.created_at
            )
            db.session.add(hist1)

            if inc['status'] != 'Submitted':
                hist2 = IncidentStatusHistory(
                    incident_id=report.id,
                    old_status='Submitted',
                    new_status=inc['status'],
                    changed_by_user_id=admin.id,
                    notes=inc['notes'] or f"Triage updated to {inc['status']}",
                    created_at=report.created_at + timedelta(minutes=15)
                )
                db.session.add(hist2)

            created_incidents.append(report)

        print("Seeding emergency broadcast alerts and notifications...")
        alert1 = EmergencyAlert(
            created_by_user_id=admin.id,
            category='flood',
            title='Flash Flood & High Tide Warning — Coastal Konkan & Mumbai Metro',
            message='IMD reports extreme precipitation (>150mm) coinciding with a 4.5m high tide at 14:30. Low-lying areas must move to upper floors. Do not drive through submerged underpasses. Emergency helpline: 112 / NDRF 1078.',
            urgency='Critical',
            target_audience='region',
            target_region='Mumbai Metro',
            is_active=True,
            created_at=now - timedelta(hours=2)
        )
        db.session.add(alert1)

        alert2 = EmergencyAlert(
            created_by_user_id=admin.id,
            category='other',
            title='Severe Weather & Wind Advisory — State-Wide Precautionary Protocol',
            message='Gusty winds up to 65 km/h expected across the region tonight. Citizens are advised to secure loose outdoor objects, stay clear of tin sheds and electric transformers, and keep mobile devices fully charged.',
            urgency='High',
            target_audience='all',
            is_active=True,
            created_at=now - timedelta(hours=8)
        )
        db.session.add(alert2)
        db.session.flush()

        # Seed in-app notifications for users
        all_seeded_users = [admin, responder_1, responder_2, citizen_1, citizen_2, citizen_3, citizen_4]
        for u in all_seeded_users:
            # Regional alert notification if in Mumbai
            if 'Mumbai' in (u.region or ''):
                n1 = UserNotification(
                    user_id=u.id,
                    alert_id=alert1.id,
                    title=f"🚨 [CRITICAL ALERT] {alert1.title}",
                    message=alert1.message,
                    delivery_channel='in_app',
                    delivery_status='delivered',
                    created_at=alert1.created_at
                )
                db.session.add(n1)

            # Global alert notification
            n2 = UserNotification(
                user_id=u.id,
                alert_id=alert2.id,
                title=f"⚠️ [HIGH ALERT] {alert2.title}",
                message=alert2.message,
                delivery_channel='in_app',
                delivery_status='delivered',
                created_at=alert2.created_at
            )
            db.session.add(n2)

        # Seed Family Contacts and Safety Check-ins
        print("Seeding family safety contacts and voluntary check-ins...")
        fc1 = FamilyContact(
            user_id=citizen_1.id,
            name="Meera Patel",
            contact_method="email",
            contact_value="user.sneha@example.com",
            relationship="Sister",
            status="active"
        )
        fc2 = FamilyContact(
            user_id=citizen_1.id,
            name="Suresh Patel",
            contact_method="phone",
            contact_value="+91 98200 88888",
            relationship="Father",
            status="active"
        )
        db.session.add_all([fc1, fc2])

        checkin1 = FamilyCheckIn(
            user_id=citizen_1.id,
            status="safe",
            message="Reached Dadar relief shelter safely. Food and water available. Battery at 65%.",
            share_location=True,
            latitude=19.0178,
            longitude=72.8478,
            location_name="Dadar Central Relief Center",
            created_at=now - timedelta(hours=3)
        )
        db.session.add(checkin1)

        # Seed Synthetic Duplicate Incident Match for Admin Review
        print("Seeding synthetic duplicate incidents for admin review...")
        orig_inc = EmergencyReport(
            user_id=citizen_1.id,
            category="Fire Outbreak",
            description="Dense smoke and fire pouring from second floor electrical room at Silver Towers building.",
            original_language="en",
            translated_description="Dense smoke and fire pouring from second floor electrical room at Silver Towers building.",
            location_address="Silver Towers, SV Road, Andheri West, Mumbai",
            latitude=19.1197,
            longitude=72.8464,
            affected_count=15,
            status="In Progress",
            ai_suggested_category="Fire Outbreak",
            ai_suggested_priority="Critical",
            is_high_risk=True,
            created_at=now - timedelta(minutes=45)
        )
        db.session.add(orig_inc)
        db.session.flush()

        dup_inc = EmergencyReport(
            user_id=citizen_2.id,
            category="Fire Outbreak",
            description="Massive building fire at Silver Towers 2nd floor, thick black smoke blocking hallway. People trapped.",
            original_language="en",
            translated_description="Massive building fire at Silver Towers 2nd floor, thick black smoke blocking hallway. People trapped.",
            location_address="Silver Towers Wing B, SV Road, Andheri West",
            latitude=19.1198,
            longitude=72.8465,
            affected_count=20,
            status="Submitted",
            ai_suggested_category="Fire Outbreak",
            ai_suggested_priority="Critical",
            is_high_risk=True,
            is_potential_duplicate=True,
            potential_duplicate_of_id=orig_inc.id,
            duplicate_similarity_score=0.82,
            duplicate_match_reason="Text Sim: 76% | Category: Fire Outbreak | Proximity: 0.02km",
            duplicate_review_status="flagged",
            created_at=now - timedelta(minutes=30)
        )
        db.session.add(dup_inc)
        db.session.flush()

        dup_match = PotentialDuplicateMatch(
            incident_a_id=orig_inc.id,
            incident_b_id=dup_inc.id,
            similarity_score=0.82,
            distance_km=0.02,
            time_diff_hours=0.25,
            match_reason="High text overlap on Silver Towers electrical fire + geospatial co-location (<30 meters).",
            status="pending",
            created_at=now - timedelta(minutes=30)
        )
        db.session.add(dup_match)

        # Audit Log
        AuditLog.log('SYSTEM_SEED', admin.id, 'system', None, details="Development database seeded with realistic records.")
        db.session.commit()

        print("\n========================================================================")
        print("  ResQAI DEVELOPMENT DATABASE SEEDED SUCCESSFULLY!                     ")
        print("========================================================================")
        print("  DEMO ACCOUNTS (DEVELOPMENT / LOCAL DEMONSTRATION ONLY):                ")
        print("  ----------------------------------------------------------------------")
        print("  1. ADMINISTRATOR:")
        print("     Email:    admin@resqai.org")
        print("     Password: Admin@12345")
        print("     Role:     Administrator (Full access, broadcasts, analytics, users)")
        print("")
        print("  2. FIELD RESPONDER 1 (NDRF / Disaster Team):")
        print("     Email:    responder.rajesh@resqai.org")
        print("     Password: Responder@123")
        print("     Role:     Responder (Assigned incidents, triage updates, GPS)")
        print("")
        print("  3. FIELD RESPONDER 2 (Medical Officer):")
        print("     Email:    responder.priya@resqai.org")
        print("     Password: Responder@123")
        print("     Role:     Responder (Medical incidents triage)")
        print("")
        print("  4. CITIZEN TEST ACCOUNTS (Password for all: User@123):")
        print("     - user.aarav@example.com   (Hindi, Mumbai Metro)")
        print("     - user.sneha@example.com   (Marathi, Pune Region)")
        print("     - user.tariq@example.com   (Urdu, Delhi NCR)")
        print("     - user.maria@example.com   (Spanish, Goa Coastal)")
        print("========================================================================\n")

if __name__ == '__main__':
    seed_database()

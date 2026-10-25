# ResQAI: Viva Demonstration & Examination Guide

**Project Title:** ResQAI — AI-Powered Multilingual Emergency Triage and Offline Disaster Support System  
**Course:** Diploma in Computer Engineering — Final Year Capstone Project  
**Author / Presenter:** Engineering Candidate  

---

## 1. Quick Start Commands (Windows PowerShell)

Open PowerShell in the project directory (`c:\Users\Jay\Desktop\video`):

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Reset and seed development database with demo data
python seed_demo.py

# 3. Run all automated tests (56 tests)
python -m pytest -v

# 4. Launch web application server
python run.py
```

The application will be live at: **`http://127.0.0.1:5000`**

---

## 2. Pre-Seeded Demonstration Accounts

| Role | Email | Password | Key Permissions & Demonstrable Features |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@resqai.org` | `Admin@12345` | Global command center, duplicate incident review console, broadcast emergency alert creation, user role management, system analytics, CSV exports. |
| **Field Responder 1** | `responder.rajesh@resqai.org` | `Responder@123` | Responder operational desk, assigned incident triage, status transitions (`In Progress` &rarr; `Resolved`), full GPS access. |
| **Field Responder 2** | `responder.priya@resqai.org` | `Responder@123` | Medical incident triage, responder notes, field communication. |
| **Citizen (Hindi)** | `user.aarav@example.com` | `User@123` | Report emergency, AI chatbot in Hindi, One-Tap SOS, family safety check-ins. |
| **Citizen (Marathi)** | `user.sneha@example.com` | `User@123` | Marathi incident submission, regional alerts, trusted contact circle. |
| **Citizen (Urdu)** | `user.tariq@example.com` | `User@123` | RTL layout demonstration, Urdu voice / text emergency triage. |

---

## 3. Step-by-Step Viva Demonstration Workflow

### Scenario 1: One-Tap SOS & Instant Triage (30 Seconds)
1. Navigate to `http://127.0.0.1:5000`.
2. Click the red **SOS** button in the navigation bar.
3. Show the examiner:
   - The browser automatically fetches live GPS coordinates (`pos.coords.latitude, pos.coords.longitude`).
   - Click **Transmit SOS Beacon**.
   - Show how the report is instantly marked as **Critical Priority** with an incident tracking code like `INC-20261025-XXXX`.
   - Point out that official national helpline **112** is prominently advised.

### Scenario 2: Multilingual AI Emergency Assistant & Voice Interaction (1 Minute)
1. Go to **AI Assistant** (`/chatbot`).
2. Switch language dropdown to **हिन्दी (Hindi)**.
3. Click the **Microphone** icon (Web Speech API) or type:  
   `"इमारत में आग लगी है और सीढ़ियों में धुआं भरा है"`
4. Send the message.
5. Show the examiner:
   - AI detects **Fire Outbreak** and flags priority as **Critical / High**.
   - Shows actionable life safety instructions in Hindi.
   - Click the **Speaker** icon on the response bubble: Web Speech Synthesis reads the Hindi instructions aloud cleanly!

### Scenario 3: Offline PWA & IndexedDB Queue (1 Minute)
1. Open Chrome DevTools (`F12`), switch to the **Application** tab &rarr; **Service Workers** (show registered `service-worker.js`).
2. Switch DevTools **Network** tab to **Offline** mode.
3. Notice the top red banner appears: *"Offline Mode Active — cellular/internet connection unavailable"*.
4. Navigate to **Emergency Handbook** (`/offline-guide`): it loads instantly from cache even though offline!
5. Fill out an emergency report while offline:
   - Category: `Flood / Waterlogging`
   - Description: `Offline test: river water entered colony`
   - Submit the form.
6. Show in DevTools &rarr; **IndexedDB** &rarr; `ResQAIOfflineDB` &rarr; `reports`: the report is stored with an `idempotency_key` (UUID v4).
7. Switch network back to **Online**:
   - The telemetry pill turns green.
   - The report automatically synchronizes with the server, deduplicating via the idempotency key!

### Scenario 4: Live Spatial Map & Role-Based Privacy Controls (1 Minute)
1. Log out or open an Incognito window (unauthenticated public user).
2. Visit `/map`.
3. Click on any incident marker pin:
   - GPS coordinates are generalized to 2 decimal places ($\approx 1.1 \text{ km}$) for citizen privacy.
   - Reporter phone number is masked as `Hidden for privacy`.
4. Now log in as `responder.rajesh@resqai.org`.
5. Re-open `/map`:
   - Exact floating-point GPS coordinates are revealed.
   - Submitter phone number and callback contact are accessible for dispatch.

### Scenario 5: Duplicate Incident Review Console (1 Minute)
1. Log in as `admin@resqai.org` (password `Admin@12345`).
2. Click **User Profile** dropdown &rarr; **Duplicate Incidents** (`/admin/duplicates`).
3. Show the pending match pair (`Pairing #1`):
   - Report A (Silver Towers electrical fire) vs. Report B (Building fire at Silver Towers reported 15 minutes later).
   - Display the explainable algorithm metrics: **Similarity Score: 82%**, **Haversine Distance: 0.02 km (20 meters)**, **Time Delta: 0.25 hrs**.
   - Click **Confirm Duplicate**: Report B is merged and marked as duplicate, preventing duplicate fire truck dispatches!

### Scenario 6: Family Safety Center (1 Minute)
1. Log in as `user.aarav@example.com` (password `User@123`).
2. Visit **Family Safety** (`/family`).
3. Show the Trusted Contacts list (e.g. `Meera Patel`, `Suresh Patel`).
4. Click **I AM SAFE** &rarr; optionally attach GPS location &rarr; Click **Broadcast Status Now**.
5. Log out and log in as `user.sneha@example.com`: show the bell icon with an unread notification:  
   *🟢 Family Update: Aarav Patel is SAFE at Dadar Central Relief Center!*

---

## 4. Top 10 Viva Questions & Recommended Answers

### Q1: Why did you choose SQLite instead of MongoDB or PostgreSQL for this project?
**Answer:**  
"SQLite requires zero configuration and runs as an in-process, file-backed ACID database, making it ideal for self-contained academic demonstrations, automated test suites, and edge deployments on disaster-relief command laptops. Furthermore, all our models use standard SQLAlchemy ORM constructs with explicit foreign keys and cascade rules. In production, changing a single line in `config.py` (`DATABASE_URL = 'postgresql://...'`) instantly migrates the platform to enterprise PostgreSQL or MySQL without altering application code."

### Q2: How does your AI triage work if the internet is completely severed during a cyclone or earthquake?
**Answer:**  
"ResQAI employs a pluggable architecture with deterministic local fallback (`app/services/classification_rules.py`). When an external LLM API (OpenAI or Gemini) fails or is unreachable, the system automatically falls back to an offline regex and keyword scoring matrix covering 10 disaster categories across 14 languages. This guarantees zero-downtime triage and verified safety advice with sub-millisecond latency even on zero internet connectivity."

### Q3: What is an Idempotency Key, and why is it critical for emergency disaster systems?
**Answer:**  
"In disaster zones, cellular connections flap erratically. A user might click 'Submit Report', the phone sends the packet, but the acknowledgment packet drops. Without idempotency, the browser's retry logic would create multiple duplicate incident tickets. In ResQAI, the client generates a unique UUID v4 idempotency key inside IndexedDB. If the server receives the same key twice, it recognizes the existing incident, acknowledges it safely, and prevents duplicate record insertion (`unique=True` database constraint)."

### Q4: Explain the mathematical formula used for Duplicate Incident Detection.
**Answer:**  
"Our duplicate detection algorithm uses two mathematical models:
1. **TF-IDF Cosine Similarity:** Computes term frequency and inverse document frequency vectors between descriptions, measuring the angle cosine between vectors ($\text{similarity} = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|}$).
2. **Haversine Distance Formula:** Calculates the great-circle surface distance in kilometers between two latitude/longitude points on Earth ($R = 6371 \text{ km}$) accounting for planetary curvature:
$$d = 2R \arcsin\left(\sqrt{\sin^2(\Delta \phi / 2) + \cos(\phi_1)\cos(\phi_2)\sin^2(\Delta \lambda / 2)}\right)$$
We combine these into a composite weighted score: $55\%$ text similarity, $25\%$ category match, and $20\%$ spatial proximity. Matches above 0.55 are flagged for admin review."

### Q5: How do you prevent vigilantism or privacy violations on the public incident map?
**Answer:**  
"Public users and ordinary citizens only receive generalized coordinates rounded to 2 decimal places (roughly a 1.1 km radius area) and all submitter names and phone numbers are redacted to 'Protected Citizen'. Only authenticated field responders and administrators with official roles receive raw floating-point GPS coordinates and caller callback phone numbers (`app/services/map_service.py`)."

### Q6: How does ResQAI handle Right-to-Left (RTL) scripts like Urdu and Arabic?
**Answer:**  
"The application dynamically detects the script direction via `is_rtl_language()` and injects `dir="rtl"` into the HTML `<html>` tag along with language-specific CSS overrides (`app/static/css/style.css`). This mirrors padding, form alignments, and message bubble tails automatically for Urdu and Arabic speakers."

### Q7: What security protections prevent ordinary users from promoting themselves to Administrator?
**Answer:**  
"First, the registration form (`RegisterForm`) has no role field—every registered account is hardcoded on the server to `role='user'`. Second, admin routes are strictly guarded by two layers: the `@login_required` decorator and our custom `@admin_required` decorator (`app/utils/decorators.py`), which inspects `current_user.role == 'admin'` and throws a 403 Forbidden error if breached. Our automated test suite specifically verifies these boundaries in `test_role_permissions.py`."

### Q8: How is password security implemented?
**Answer:**  
"Passwords are never stored in plaintext. We utilize Werkzeug's `generate_password_hash` which implements Scrypt / PBKDF2 with unique cryptographic salt per user. Passwords cannot be reversed even if the database file is compromised. Single-use password reset tokens expire after 60 minutes and are invalidated immediately upon consumption."

### Q9: Why does ResQAI include an explicit disclaimer stating it does not replace 112?
**Answer:**  
"As an ethical software engineering principle for life-critical systems, an AI web platform must never falsely claim to replace official government emergency dispatchers. ResQAI serves as an auxiliary decision-support, localized triage, and family communication platform. Every page, chatbot response, and emergency report header prominently surfaces official national helplines: **112** (Pan-India), **101** (Fire), **108/102** (Ambulance), and **1078** (NDRF)."

### Q10: How do you know the application is reliable and free from breaking regressions?
**Answer:**  
"We have implemented an automated test suite comprising **56 comprehensive test cases** using `pytest`. The test suite covers AI classification, multilingual script detection, Web Speech voice configs, family check-in dispatching, TF-IDF duplicate scoring, GPS privacy masking, offline idempotency replay, and RBAC authorization. All 56 tests execute cleanly with a 100% pass rate."

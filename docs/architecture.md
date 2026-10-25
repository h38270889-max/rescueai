# ResQAI: System Architecture & Engineering Specification

**Project Title:** ResQAI — AI-Powered Multilingual Emergency Triage and Offline Disaster Support System  
**Academic Target:** Diploma in Computer Engineering — Final-Year Project  
**Implementation Language:** Python 3.12+ (Tested on Python 3.14 on Windows)  
**Framework:** Flask 3.1, Flask-SQLAlchemy 3.1, Flask-Login, Flask-WTF, Werkzeug  
**Database:** SQLite (development / local viva) with strict ANSI SQL-compliant SQLAlchemy models for PostgreSQL / MySQL migration  

---

## 1. High-Level Architectural Overview

ResQAI implements a multi-tier, modular micro-modular monolith architecture engineered for high fault tolerance and zero-downtime during natural disasters and infrastructure disruptions.

```
                             +----------------------------------------+
                             |       Client Layer (Browser / PWA)      |
                             | HTML5, Bootstrap 5, Leaflet.js, WebAPI |
                             +-------------------+--------------------+
                                                 |
                                       HTTPS / Service Worker
                                                 |
         +---------------------------------------+---------------------------------------+
         | (Online)                                                                      | (Offline)
         v                                                                               v
+------------------+                                                           +-------------------+
| Reverse Proxy /  |                                                           |  IndexedDB Store  |
| Flask WSGI Core  |                                                           | (Client Queue +   |
+--------+---------+                                                           |  Survival Cache)  |
         |                                                                     +---------+---------+
         |                                                                               |
         +-------------------------------------------------------------------------------+ (Auto-Sync)
         |
         v
+------------------------------------------------------------------------------------------------+
|                               Flask Application Orchestration Layer                             |
|                                                                                                |
|  [Auth BP]     [Incidents BP]    [Chatbot BP]      [Alerts BP]     [Map BP]      [Family BP]   |
|  [Admin BP]    [Responder BP]    [API Sync BP]     [Main BP]       [Dashboard]                 |
+-------------------+---------------------+--------------------+--------------------+--------+
                    |                     |                    |                    |
                    v                     v                    v                    v
         +--------------------+  +------------------+  +---------------+  +------------------+
         | AI Triage Engine   |  | Multilingual Svc |  | Duplicate Svc |  | Map & Privacy Svc|
         | (OpenAI / Gemini / |  | (14 Languages +  |  | (TF-IDF Text  |  | (Role-Based GPS  |
         |  Local Fallback)   |  |  Unicode Script) |  |  + Haversine) |  |   Masking)       |
         +----------+---------+  +--------+---------+  +-------+-------+  +--------+---------+
                    |                     |                    |                   |
                    +---------------------+--------------------+-------------------+
                                                 |
                                                 v
                                    +--------------------------+
                                    | Data Persistence Layer   |
                                    | SQLite / PostgreSQL      |
                                    | 8 Relational Models      |
                                    +--------------------------+
```

---

## 2. Core Subsystems

### 2.1 Pluggable AI Emergency Triage Subsystem (`app/services/ai_service.py`)
- **Primary Interface:** Pluggable adapter supporting OpenAI (`gpt-4o-mini`), Google Gemini (`gemini-2.5-flash`), or Local Rule Engine.
- **Strict Ethical Boundaries:** Never diagnoses medical diseases, never prescribes medications, never hallucinates arrival times.
- **Zero-Downtime Deterministic Fallback (`app/services/classification_rules.py`):**
  - Evaluates multilingual keywords across 10 disaster categories (`Medical Emergency`, `Fire Outbreak`, `Flood / Waterlogging`, `Earthquake`, `Road Accident`, `Landslide`, `Cyclone`, `Building Collapse`, `Hazardous Material`, `General Emergency`).
  - Assigns urgency (`Critical`, `High`, `Medium`, `Low`) based on life-threat indicators.
  - Automatically appends pan-India official hotlines (**112**, **101**, **108**, **1078**).

### 2.2 Multilingual Natural Language Processing (`app/services/translation_service.py`)
- **Supported Languages (14):** English (`en`), Hindi (`hi`), Marathi (`mr`), Urdu (`ur`), Bengali (`bn`), Tamil (`ta`), Telugu (`te`), Gujarati (`gu`), Kannada (`kn`), Malayalam (`ml`), Punjabi (`pa`), Spanish (`es`), Arabic (`ar`), French (`fr`).
- **Unicode Script Analysis:** Zero-dependency algorithm inspecting character ranges to automatically detect Devanagari, Gurmukhi, Dravidian, Arabic/Urdu, and Latin alphabets.
- **RTL Support:** Dynamic CSS layout direction injection (`dir="rtl"`) for Urdu and Arabic interfaces.
- **Preservation Policy:** Original citizen text is *always* preserved in the database; translated text is provided alongside to assist English-speaking command centers without discarding victim nuances.

### 2.3 Duplicate Incident Detection Subsystem (`app/services/duplicate_service.py`)
- **Objective:** Prevent responder dispatch fragmentation caused by multiple citizens reporting the same fire, building collapse, or road collision.
- **Pure-Python TF-IDF Vectorization:**
  $$\text{TF}(t, d) = \frac{f_{t,d}}{|d|}, \quad \text{IDF}(t, D) = \ln\left(\frac{|D| + 1}{\text{DF}(t) + 1}\right) + 1$$
  $$\text{Cosine Similarity} = \frac{\vec{v}_1 \cdot \vec{v}_2}{\|\vec{v}_1\| \|\vec{v}_2\|}$$
- **Haversine Geospatial Distance Formula:**
  $$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
  Where $R = 6371.0 \text{ km}$.
- **Composite Score:**
  $$\text{Score} = (0.55 \times \text{TextSim}) + (0.25 \times \text{CategoryMatch}) + (0.20 \times \text{GeospatialProximity})$$
  Incidents exceeding $\text{Score} \ge 0.55$ within a 24-hour temporal window are flagged as `potential_duplicate` and logged in `potential_duplicate_matches` for human administrator verification.

### 2.4 Offline PWA & Idempotent Synchronization (`app/static/js/indexeddb.js`)
- **Service Worker (`service-worker.js`):** Cache-first strategy for static assets and the comprehensive offline emergency handbook; network-first with offline fallback for navigational pages.
- **Client Storage (`ResQAIOfflineDB`):** IndexedDB stores queued emergency reports with client-generated UUID v4 idempotency keys.
- **Server Deduplication:** `EmergencyReport.idempotency_key` unique index prevents duplicate incident generation if network reconnects with multiple retry requests.

### 2.5 Geospatial Mapping & Privacy Safeguards (`app/services/map_service.py`)
- **Interactive Leaflet.js Canvas:** Renders OpenStreetMap tiles with color-coded category markers and urgency pulsing circles.
- **Role-Based Privacy Masking:**
  - *Public Citizens & Guests:* GPS coordinates are generalized to 2 decimal places ($\approx 1.1 \text{ km}$ precision), and contact phone numbers/names are masked as `Protected Citizen` to prevent vigilantism or doxxing.
  - *Authorized Responders & Admins:* View exact floating-point GPS coordinates, live phone numbers, and operational notes.

### 2.6 Family Safety Center (`app/services/family_service.py`)
- Allows users to maintain a trusted circle of relatives or friends.
- Enables voluntary, one-tap safety broadcasts: `I AM SAFE`, `EVACUATING`, `NEED ASSISTANCE`.
- Automatically routes in-app notifications to registered family contacts without burdening cellular voice networks.

---

## 3. Security Architecture & RBAC

- **Password Security:** Scrypt / PBKDF2 password hashing via Werkzeug (`generate_password_hash`, `check_password_hash`). Plaintext passwords never exist in memory or database.
- **CSRF Protection:** Flask-WTF CSRF tokens on all state-altering POST/PUT forms. Clean API exemptions for IndexedDB offline sync and WebPush subscriptions.
- **Role-Based Access Control (RBAC):**
  - `user`: Submit incidents, chat with assistant, view personal reports, manage family safety contacts.
  - `responder`: Access responder operational desk, claim incidents, update status, view exact GPS fixes.
  - `admin`: Full platform governance, user role promotion, system-wide emergency alerts, duplicate reviews, CSV audit exports.
- **Single-Use Expiring Tokens:** Password reset tokens expire after 60 minutes and become invalid immediately upon first use.

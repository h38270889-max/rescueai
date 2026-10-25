# ResQAI: AI-Powered Multilingual Emergency Triage and Offline Disaster Support System

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-26%20Passed%20(100%25)-brightgreen.svg)](docs/testing-report.md)
[![PWA](https://img.shields.io/badge/PWA-Offline%20Ready-orange.svg)](docs/project-overview.md)

**Diploma in Computer Engineering — Final Year Capstone Project**

---

## 🚨 Problem Statement & Solution

During natural disasters (floods, earthquakes, building fires, cyclones) and medical crises:
- **Telecommunication towers degrade**, leaving victims without internet or cellular connectivity.
- **Emergency call centers (112 / 100 / 108) experience acute call congestion.**
- **Language barriers prevent non-native speakers** from accurately communicating their injuries or location.

**ResQAI** is a full-stack, production-grade emergency web application that solves these challenges through:
1. **Multilingual Intake Across 14 Languages:** Natural communication in Hindi, Marathi, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam, Punjabi, Urdu, Spanish, French, Arabic, and English, with full Right-to-Left (RTL) layout support.
2. **Pluggable AI & Zero-Downtime Rule Fallback:** Triage powered by Google Gemini when online, backed by an instant deterministic rule-based emergency triage engine that operates locally with zero internet dependency.
3. **Offline-First PWA & IndexedDB Queue:** Citizens can file emergency reports during network outages. Reports are stored in client-side IndexedDB and synchronized automatically when connectivity returns, using UUID **Idempotency Keys** to prevent duplicate incident creation.
4. **Targeted Multi-Channel Broadcasts:** Emergency coordinators can dispatch regional or category-specific broadcast alerts with audited delivery tracking.
5. **Dedicated Field Responder Desk:** Responders receive prioritized queues, GPS coordinates, translations, and live operational status tracking.

---

## 🛠️ Technology Stack

- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5.3, Bootstrap Icons, Chart.js, Jinja2 Templates.
- **Backend:** Python 3.12/3.14, Flask 3.1.0, Flask-SQLAlchemy, Flask-Login, Flask-WTF with CSRF Protection, Werkzeug Password Hashing.
- **Database:** SQLite (local zero-configuration development), designed for seamless migration to PostgreSQL or MySQL.
- **AI & Triage:** Pluggable Google Gemini API + Zero-Latency Deterministic Rule Engine for 10 emergency categories.
- **Offline / PWA:** Service Worker Cache API, Web App Manifest, IndexedDB with idempotency deduplication.
- **Testing:** Automated test suite with 26 unit & integration tests using `pytest`.

---

## 🚀 Quick Start Guide

### 1. Set Up Virtual Environment & Dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Seed the Development Database
Populate realistic demo accounts, multilingual reports, alerts, and notifications:
```powershell
python seed_demo.py
```

### 3. Run the Application
```powershell
python run.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 🔑 Pre-Configured Demo Accounts (For Viva / Evaluation)

| Role | Email | Password | Access Details |
|---|---|---|---|
| **Administrator** | `admin@resqai.org` | `Admin@12345` | Command & Control, Emergency Alerts, User Roles, Analytics, CSV Export |
| **Field Responder 1** | `responder.rajesh@resqai.org` | `Responder@123` | NDRF Rescue Lead: Incident dispatch, claim cases, GPS coordinates |
| **Field Responder 2** | `responder.priya@resqai.org` | `Responder@123` | Emergency Medical Officer: Trauma triage and hospital coordination |
| **Citizen 1 (Hindi)** | `user.aarav@example.com` | `User@123` | Emergency report in Hindi, status tracking |
| **Citizen 2 (Marathi)** | `user.sneha@example.com` | `User@123` | Flood rescue request in Marathi |
| **Citizen 3 (Urdu)** | `user.tariq@example.com` | `User@123` | Earthquake report in Urdu with Right-to-Left (RTL) layout |
| **Citizen 4 (Spanish)** | `user.maria@example.com` | `User@123` | Road accident report in Spanish |

---

## 🧪 Running Automated Unit Tests

Run the full 26-test automated test suite:
```powershell
python -m pytest -v
```

All 26 tests will execute against an isolated in-memory test database, validating:
- Account registration & duplicate email rejection
- Login with password hashing & logout
- Role-based permissions (Citizen, Responder, Admin isolation)
- Cross-user privacy boundaries (User A cannot open User B's report)
- Emergency incident creation & unique incident ID generation
- AI category classification & urgency priority calculation
- Deterministic fallback chatbot functionality without API key
- Multilingual interface switching & translation preservation
- Emergency broadcast alerting & audience targeting
- Offline report queueing & idempotency deduplication (prevents duplicate tickets upon reconnect)
- Administrator CSV export

---

## 📁 Project Structure

```
video/ (Project Root)
├── config.py                 # Development, Testing & Production Configurations
├── extensions.py             # SQLAlchemy, LoginManager & CSRF Initialization
├── requirements.txt          # Pinned Dependencies
├── run.py                    # Application Entrypoint
├── seed_demo.py              # Realistic Database Seeding Script
├── .env.example              # Environment Configuration Template
├── .gitignore                # Git Exclusions
├── README.md                 # Primary Project Documentation
├── app/
│   ├── __init__.py           # Application Factory & Blueprint Registration
│   ├── models/               # SQLAlchemy Relational Models (User, Incident, Alert, etc.)
│   ├── routes/               # Modular Flask Blueprints (Main, Auth, Incidents, Admin, etc.)
│   ├── services/             # AI Triage, Deterministic Rules, Multilingual Translations
│   ├── forms/                # Secure Flask-WTF Forms with CSRF Protection
│   ├── utils/                # Decorators, Geolocation Helpers, Template Processors
│   ├── translations/         # 14 Localized JSON Catalogs (hi, mr, bn, ur, ar, etc.)
│   ├── static/
│   │   ├── css/style.css     # Responsive Disaster Response Design System
│   │   ├── js/app.js         # Telemetry, Geolocation & PWA Client Engine
│   │   ├── js/chat.js        # AI Assistant Chat Interface
│   │   ├── js/indexeddb.js   # Offline Queue & Idempotency Key Sync
│   │   ├── manifest.json     # PWA Web App Manifest
│   │   └── service-worker.js # Cache-First Offline Asset & Handbook Service Worker
│   └── templates/            # Jinja2 Layouts (Admin, Responder, Chat, Reporting, Auth)
├── tests/                    # Pytest Suite (26 Automated Test Cases)
└── docs/                     # Project Overview, Database Design, Setup Guide, Limitations
```

---

## 📚 Detailed Documentation

- [Project Overview & Architecture](docs/project-overview.md)
- [Database Schema & ERD](docs/database-design.md)
- [Setup & Demonstration Guide](docs/setup-guide.md)
- [Automated Testing Report](docs/testing-report.md)
- [System Limitations & Ethical Boundaries](docs/limitations.md)

---

## ⚠️ Important Safety & Legal Disclaimer

ResQAI is an auxiliary emergency assistance platform designed to assist communities and relief responders during crises. **It does NOT claim to replace government emergency services or telecommunication dispatchers.** In any acute, life-threatening emergency, always dial **112 (Pan-India)** or your local national emergency telephone number immediately.

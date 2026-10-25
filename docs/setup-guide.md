# ResQAI: Local Setup & Demonstration Guide

---

## 1. Prerequisites

- **Python:** 3.12, 3.13, or 3.14 (Verified and tested on Python 3.14)
- **Pip:** 24.0 or newer
- **Web Browser:** Modern browser supporting Service Workers and IndexedDB (Google Chrome, Microsoft Edge, Mozilla Firefox, or Safari)

---

## 2. Installation Steps

### Step 1: Clone or Navigate to Project Directory
```powershell
cd c:\Users\Jay\Desktop\video
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (Optional)
Copy `.env.example` to `.env` if you wish to configure optional external services (such as Google Gemini API for cloud LLM triage, or SMTP email parameters):
```powershell
cp .env.example .env
```
> **Note on AI Fallback:** Setting `GEMINI_API_KEY` is completely optional. If left blank, ResQAI operates in full **Deterministic Offline Fallback Mode**, providing immediate, zero-latency emergency triage and safety guidance for all 10 emergency categories and 14 languages!

### Step 5: Seed the Development Database
Run the automated demo seeder to create database tables and populate realistic test data:
```powershell
python seed_demo.py
```

### Step 6: Launch the Web Application
```powershell
python run.py
```
The server will start at: **`http://127.0.0.1:5000`**

---

## 3. Demo Accounts for Viva / Project Demonstration

The database seeder creates pre-configured accounts for evaluating all access tiers:

| Role | Email Address | Password | Jurisdiction / Region | Capabilities |
|---|---|---|---|---|
| **Administrator** | `admin@resqai.org` | `Admin@12345` | Mumbai Metro | Full Command & Control, Emergency Broadcasts, User Roles, Analytics, CSV Export |
| **Field Responder 1** | `responder.rajesh@resqai.org` | `Responder@123` | Mumbai Metro | NDRF Rescue Lead: Incident dispatch, claim unassigned cases, GPS navigation, field notes |
| **Field Responder 2** | `responder.priya@resqai.org` | `Responder@123` | Pune Region | Emergency Medical Officer: Medical triage, hospital routing |
| **Citizen 1 (Hindi)** | `user.aarav@example.com` | `User@123` | Mumbai Metro | Emergency reporting in Hindi, tracking status |
| **Citizen 2 (Marathi)** | `user.sneha@example.com` | `User@123` | Pune Region | Flood rescue request in Marathi, notifications |
| **Citizen 3 (Urdu)** | `user.tariq@example.com` | `User@123` | Delhi NCR | Earthquake collapse report in Urdu (RTL interface) |
| **Citizen 4 (Spanish)** | `user.maria@example.com` | `User@123` | Goa Coastal | Road accident report in Spanish |

---

## 4. How to Test Offline Capabilities (PWA & IndexedDB)

1. Open `http://127.0.0.1:5000` in Google Chrome or Microsoft Edge.
2. Open Chrome DevTools (`F12` or `Ctrl + Shift + I`).
3. Click the **Network** tab in DevTools.
4. Change the throttling dropdown from **"No throttling"** to **"Offline"**.
5. Observe the UI:
   - The status pill in the navbar instantly changes to **`Offline Mode`**.
   - The yellow sticky warning banner appears at the top of the screen.
6. Navigate to **Report Emergency** (`/incidents/report`). Fill in the form and click **Submit Emergency Report**:
   - The browser will intercept the submission.
   - An alert confirms the report was saved in **IndexedDB** with an Idempotency Key!
7. Switch DevTools Network back to **"No throttling"** (Online):
   - The application automatically synchronizes the queued report with the backend server.
   - The report appears in the live database without creating duplicates!

---

## 5. Running Automated Unit Tests

Execute the complete 26-test suite using pytest:
```powershell
python -m pytest -v
```
All 26 tests will execute against an isolated in-memory test database, validating authentication, permissions, triage rules, chat fallbacks, broadcast notifications, and offline sync deduplication.

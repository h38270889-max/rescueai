# ResQAI: System Limitations, Technical Realities & Ethical Boundaries

---

## 1. Platform Auxiliary Status & Official Emergency Services

**Primary Rule:** ResQAI is an auxiliary emergency assistance and coordination platform. It is designed to assist communities and relief responders during crises. **It does NOT claim to replace official government emergency dispatchers or telecommunication lifelines.**

- In any acute, life-threatening situation, individuals should always dial **112 (Pan-India)** or their local emergency telephone number immediately.
- ResQAI does not operate emergency vehicles, police squads, or fire suppression units directly; it channels structured, prioritized information to trained human coordinators.

---

## 2. Physical & Network Infrastructure Constraints

1. **Physical Transmission Limits:**
   - While ResQAI's Progressive Web App (PWA) architecture caches the app shell and stores draft emergency reports inside client-side IndexedDB, **no web software can physically transmit radio signals through air without a working hardware network path.**
   - An offline-queued report remains stored on the user's device until the device reconnects to a cellular tower, WiFi router, satellite hotspot, or emergency mesh network.
   - ResQAI makes this transparent to users through persistent UI banners and sync status badges.

2. **GPS Accuracy & Battery Depletion:**
   - Browser geolocation accuracy depends entirely on device hardware and satellite visibility. Cloud cover, collapsed concrete buildings, and subterranean basements degrade GPS triangulation.
   - Prolonged device usage during power blackouts depletes battery reserves. ResQAI provides a lightweight offline survival guide to minimize screen-on time.

---

## 3. Artificial Intelligence & Decision Boundaries

1. **No Autonomous Rescue Prioritization:**
   - ResQAI Assistant's urgency classifications (`Critical`, `High`, `Medium`, `Low`) are **decision-support recommendations** intended to help human responders triage overloaded queues.
   - The AI does not have the authority to cancel, deprioritize, or deny rescue assistance autonomously.

2. **Strict Medical & Diagnostic Boundaries:**
   - The AI assistant is strictly programmed to provide immediate basic first aid protocols (e.g., direct pressure on bleeding, recovery position, burn cooling).
   - It is strictly forbidden from diagnosing medical conditions or recommending pharmaceutical prescriptions.

3. **No Hallucinated Commitments:**
   - The AI assistant will never fabricate or promise rescue team arrival times, hospital bed availability, or dispatch guarantees unless verified and confirmed by an authorized human coordinator.

---

## 4. Emergency Broadcast & Audience Coverage Realities

- A web application cannot automatically blast unsolicited SMS or push notifications to arbitrary unknown cellular phone numbers in a geographic disaster zone.
- Real-world nationwide broadcasts require integration with national Public Warning Systems (such as the Common Alerting Protocol - CAP, cell broadcast technology, or telecom operator coordination).
- ResQAI broadcasts reach **registered, consented platform users** within targeted geographic regions or hazard categories.

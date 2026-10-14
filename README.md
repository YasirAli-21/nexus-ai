
# 🛡️ NEXUS AI

### AI-Powered Operations & Incident Intelligence Platform

**An intelligent, human-controlled platform for anomaly detection, incident investigation, and safe remediation workflows.**

[![CI](https://github.com/YasirAli-21/nexus-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/YasirAli-21/nexus-ai/actions/workflows/ci.yml)

## 🌐 Live Interactive Demo

### [🚀 Explore NEXUS AI Live](https://nexus-ai-4ng.pages.dev/)

Explore the interactive dashboard, synthetic incidents, severity analytics, and AI investigation previews.

> **Demo Notice:** The public demo uses synthetic data and is read-only. The actual FastAPI backend, administrator workflows, and telemetry ingestion are not exposed publicly.

NEXUS AI combines machine learning, live telemetry monitoring, evidence-based incident analysis, and a security operations dashboard to support operational decision-making.

Instead of automatically modifying infrastructure, NEXUS AI keeps remediation decisions under human control.

---

## 🚀 Key Features

### 1. AI-Powered Anomaly Detection

- Isolation Forest-based anomaly detection
- Rule-based critical thresholds
- Hybrid ML and threshold detection
- Three-observation confirmation for ML-only anomalies
- Duplicate suppression using cooldown logic
- Automatic incident generation

### 2. Live Telemetry Monitoring

- FastAPI telemetry ingestion endpoints
- CPU and memory monitoring
- API response latency monitoring
- Request count and error rate monitoring
- Persistent telemetry history using SQLite
- Incident generation based on detection criteria

### 3. Incident Intelligence

- Centralized incident management
- Severity classifications
- Evidence collection
- Incident timelines
- Root cause assessments
- Investigation confidence levels

### 4. AI Investigation Engine

- On-demand incident investigation
- Evidence-based root cause assessment
- Key findings generation
- Recommended response actions
- Saved investigation reports
- Deterministic investigation mode without API costs
- Optional LLM investigation support

> AI-generated findings are advisory and do not automatically execute remediation.

### 5. Human-in-the-Loop Remediation

- Human approval and rejection
- Safe remediation simulation
- Prevention of repeated approval decisions
- Prevention of repeated simulations
- Persistent workflow audit trail
- No real production infrastructure modifications

### 6. Security Operations Dashboard

- Professional React dashboard
- Dark security operations interface
- Incident severity analytics
- Incident queue with search and filtering
- Evidence correlation
- Incident timeline visualization
- AI Investigation Center
- Human Approval Center
- Automatic 15-second incident refresh

### 7. Authentication & Security

- Administrator login and logout
- Signed HttpOnly session cookies
- Protected incident APIs
- Protected telemetry endpoints
- Origin validation for state-changing requests
- Temporary lockout after repeated incorrect passwords
- Automated authentication security tests

---

## 🏗️ System Architecture

NEXUS AI follows a modular architecture that separates anomaly detection, incident management, AI investigation, and human-controlled remediation.

```text
                    NEXUS AI SYSTEM ARCHITECTURE

                  +---------------------------+
                  |   Operational Telemetry   |
                  | CPU, Memory, Latency,     |
                  | Requests, Error Rate      |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |   FastAPI Ingestion API   |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |  Hybrid Detection Engine  |
                  +-------------+-------------+
                                |
                   +------------+------------+
                   |                         |
                   v                         v
          +------------------+     +------------------+
          | Isolation Forest |     | Threshold Rules  |
          | ML Anomaly Model |     | Critical Metrics |
          +--------+---------+     +--------+---------+
                   |                        |
                   +------------+-----------+
                                |
                                v
                  +---------------------------+
                  | Confirmation & Cooldown   |
                  | Duplicate Suppression     |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |    Incident Management    |
                  | Evidence + Event Timeline |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |      SQLite Database      |
                  +-------------+-------------+
                                |
                  +-------------+-------------+
                  |                           |
                  v                           v
       +-----------------------+  +-----------------------+
       | AI Investigation      |  | React SOC Dashboard   |
       | Root Cause Analysis   |  | Incident Monitoring   |
       | Findings & Actions    |  | Evidence & Timeline   |
       +-----------+-----------+  +-----------+-----------+
                   |                          |
                   +-------------+------------+
                                 |
                                 v
                   +--------------------------+
                   | Human Approval / Reject  |
                   +------------+-------------+
                                |
                                v
                   +--------------------------+
                   | Safe Remediation         |
                   | Simulation Only          |
                   +------------+-------------+
                                |
                                v
                   +--------------------------+
                   | Workflow Audit Trail     |
                   | Persisted in SQLite      |
                   +--------------------------+
```

### Architecture Explanation

**1. Telemetry Ingestion:** Operational metrics are submitted through the FastAPI REST interface.

**2. Hybrid Detection:** Isolation Forest detects unusual patterns while threshold rules identify critical conditions.

**3. Confirmation & Cooldown:** ML-only anomalies require repeated observations before incident creation. Cooldown logic suppresses duplicate incidents.

**4. Incident Management:** Confirmed anomalies produce persistent incident records, evidence, and event timelines.

**5. AI Investigation:** The investigation engine reviews stored evidence and produces probable root causes, findings, and recommendations.

**6. React Dashboard:** Administrators inspect incidents, investigation results, workflow status, and audit trails.

**7. Human Approval:** Remediation actions require administrator review and approval.

**8. Safe Simulation:** Approved incidents can undergo a simulated remediation workflow. No production infrastructure is modified.

---

## 🧰 Technology Stack

| Component | Technologies |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Frontend | React, Vite, JavaScript |
| Machine Learning | scikit-learn, Isolation Forest |
| Data Processing | Pandas, NumPy |
| Database | SQLite, SQLAlchemy |
| AI Investigation | Deterministic investigator, optional LLM |
| Authentication | Session middleware, HttpOnly cookies |
| Testing | Python unittest, FastAPI TestClient |
| CI/CD | GitHub Actions |
| Public Demo | HTML, CSS, JavaScript, Cloudflare Pages |
| Version Control | Git, GitHub |

---

## 📁 Project Structure

```text
nexus-ai/
|
+-- .github/
|   +-- workflows/
|       +-- ci.yml
|
+-- ai/
+-- backend/
|   +-- app/
|       +-- api/
|       +-- core/
|       +-- models/
|       +-- services/
|
+-- config/
+-- data/
|   +-- synthetic/
|
+-- demo/
|   +-- index.html
|
+-- docs/
|   +-- screenshots/
|
+-- frontend/
|   +-- src/
|
+-- ml/
+-- scripts/
+-- tests/
|   +-- test_api_integration.py
|   +-- test_api_smoke.py
|   +-- test_auth_security.py
|
+-- requirements.txt
+-- .gitignore
+-- README.md
```

Sensitive credentials, local databases, virtual environments, and backups are excluded from version control.

---

## 📸 Platform Screenshots

### Security Operations Dashboard

![NEXUS AI Dashboard](docs/screenshots/dashboard.png)

### AI Investigation Center

![AI Investigation](docs/screenshots/ai-investigation.png)

### Human-Controlled Remediation

![Remediation Workflow](docs/screenshots/remediation.png)

### Administrator Login

![NEXUS AI Login](docs/screenshots/login.png)

---

## ⚙️ Installation & Local Setup

### Prerequisites

- Python 3.10
- Node.js and npm
- Git

### 1. Clone Repository

```bash
git clone https://github.com/YasirAli-21/nexus-ai.git
cd nexus-ai
```

### 2. Create Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure Authentication

Create a `.env` file in the project root:

```dotenv
NEXUS_AUTH_ENABLED=true
NEXUS_ADMIN_PASSWORD=REPLACE_WITH_A_STRONG_RANDOM_PASSWORD
NEXUS_SESSION_SECRET=REPLACE_WITH_A_LONG_RANDOM_SECRET
NEXUS_COOKIE_SECURE=false
```

The administrator password must contain at least 12 characters. The session secret must contain at least 32 characters.

`NEXUS_COOKIE_SECURE=false` is intended only for local HTTP development. Secure HTTPS environments require appropriate secure-cookie configuration.

**Never commit `.env`, passwords, or API keys.**

### 5. Start FastAPI Backend

From the project root:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001
```

Backend health endpoint:

http://127.0.0.1:8001/health

### 6. Start React Dashboard

Open a separate terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the admin dashboard:

http://127.0.0.1:5173

Sign in using the administrator password configured in `.env`.

---

## 🔍 End-to-End Workflow

1. Operational telemetry is submitted through FastAPI.
2. Isolation Forest evaluates metrics against learned normal patterns.
3. Rule-based thresholds check for critical conditions.
4. Confirmation and cooldown logic determine whether an incident should be generated.
5. The incident and its supporting evidence are saved in SQLite.
6. An administrator opens the incident in the React dashboard.
7. The AI investigation engine generates findings and recommendations.
8. An administrator approves or rejects the remediation proposal.
9. Approved cases may undergo safe remediation simulation.
10. Audit events and workflow results are preserved.

### Example: E-Commerce Checkout Failure

Imagine an online shopping platform where checkout latency suddenly increases.

NEXUS AI monitors latency, error rate, CPU, memory, and request volume.

If critical thresholds are crossed, it records an incident.

The investigation engine analyzes evidence and suggests possible causes, such as service saturation or downstream dependency delays.

An administrator reviews these findings and decides whether to approve a safe remediation simulation.

**The current system does not automatically repair production infrastructure.**

---

## 🧪 Automated Testing

### Backend Integration Tests

```bash
python -m unittest discover -s tests -p "test_api_integration.py" -v
```

### Authentication Security Tests

```bash
python -m unittest discover -s tests -p "test_auth_security.py" -v
```

### React Production Build

```bash
cd frontend
npm run build
```

The GitHub Actions CI workflow automatically executes integration tests, security tests, and the frontend production build on pushes and pull requests targeting `main`.

The smoke-test suite requires a running backend and is not included in the current CI workflow.

---

## 🔐 Security Considerations

NEXUS AI includes several development-stage security protections, but the admin application is not production-hardened.

Before public production deployment, additional improvements are necessary:

- HTTPS and secure-cookie configuration
- Centralized, persistent login rate limiting
- Stronger session revocation mechanisms
- Production authentication and authorization
- Secret management
- Proxy and origin configuration
- Security monitoring and load testing

The current login limiter is process-local.

The remediation engine intentionally supports simulation only.

### Public Demo Safety

The publicly deployed recruiter demo is separate from the authenticated backend.

It uses hardcoded, illustrative synthetic incident examples and does not connect to private administrator APIs or the live SQLite database.

---

## 🌍 Public Deployment

**Platform:** Cloudflare Pages

**Live URL:**

https://nexus-ai-4ng.pages.dev/

The deployed application is a standalone interactive portfolio demonstration.

It supports:

- Synthetic incident monitoring
- Severity analytics
- Incident search
- Severity filters
- Investigation previews
- Responsive desktop and mobile layouts

Administrative actions and real telemetry ingestion are not exposed.

---

## 🗺️ Future Improvements

- Docker-based deployment
- Kubernetes integration
- Additional telemetry collectors
- Advanced anomaly detection models
- Expanded AI investigation capabilities
- Multi-user role-based access control
- Production authentication infrastructure
- Distributed rate limiting
- Improved incident reporting
- Real-time streaming integrations
- Research-based model evaluation

---

## 👨‍💻 Author

**Yasir Ali**

Information Technology Graduate | AI/ML & Software Development

GitHub: [YasirAli-21](https://github.com/YasirAli-21)

---

## 📌 Project Status

**Functional Portfolio MVP**

NEXUS AI includes:

- Hybrid operational anomaly detection
- Persistent incident management
- Evidence-based AI investigation
- Human-controlled remediation simulation
- Administrator authentication
- Automated backend and security testing
- GitHub Actions CI/CD
- Public read-only recruiter demonstration

The project demonstrates AI-assisted operational intelligence while maintaining human control over remediation decisions.

It is a development and portfolio platform, not a production-ready autonomous remediation system.

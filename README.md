# TrustShield AI

TrustShield AI is a transparent, privacy-first decision-support web platform designed to help everyday users assess suspicious messages, links, and news claims. It explains the indicators behind each assessment and provides practical, actionable safety guidance without making unfounded guarantees.

> **Important Advisory:** TrustShield AI is an educational decision-support advisory tool. It does **not** claim or provide guarantees that any message is safe, true, fraudulent, or false. Critical financial, medical, or legal matters must always be verified directly through recognized official institutions.

---

## Architecture Overview

TrustShield AI is built as a lightweight, decoupled full-stack application with transient in-memory processing and zero persistent database dependencies:

```
TrustShield AI / Hack-Trust
├── .github/
│   └── workflows/
│       └── ci.yml             # Automated CI workflow (backend checks + frontend tests/build)
├── frontend/                  # React 18 + Vite + Tailwind CSS + Lucide Icons + Vitest
│   ├── src/
│   │   ├── components/        # Accessible UI components (Form, Results, Evidence, Modals)
│   │   ├── context/           # LanguageContext (English & Hindi)
│   │   ├── i18n/              # Complete bilingual dictionary (translations.js)
│   │   ├── utils/             # Client-side validation & SSRF restrictions
│   │   └── __tests__/         # Vitest unit & component test suites
│   ├── package.json
│   └── vite.config.js
├── backend/                   # Python 3.10+ with FastAPI & Uvicorn
│   ├── app/
│   │   ├── analyzers/         # Transparent rule analyzers (Message, URL, Claim)
│   │   ├── providers/         # Pluggable adapters (Safe Browsing, Fact Check Tools)
│   │   ├── config.py          # Environment settings loader
│   │   ├── schemas.py         # Pydantic v2 data contracts & input validators
│   │   └── main.py            # FastAPI application, security headers, rate limiting
│   ├── requirements.txt       # Production & test dependencies
│   ├── .env.example           # Environment template
│   ├── run_all_checks.py      # Master backend test suite runner (8 suites)
│   ├── test_http_e2e.py       # FastAPI HTTP endpoint & middleware tests
│   ├── test_url_security.py   # Authority credentials & URL security tests
│   └── test_fact_check.py     # Claim relevance & Jaccard similarity tests
├── Dockerfile                 # Multi-stage build with non-root user & healthcheck
├── docker-compose.yml         # Container configuration with health monitoring
└── README.md
```

---

## Feature Status Table

| Feature Area | Status | Description |
| :--- | :--- | :--- |
| **Suspicious Message Analysis** | **Implemented & Active** | Analyzes false urgency cues, bank/utility/lottery impersonation, OTP/credential solicitation, and suspicious contacts in English and Hindi. |
| **Safe URL Assessment** | **Implemented & Active** | Enforces strict SSRF defense (blocking loopback, private RFC1918 ranges, cloud metadata), detects Punycode spoofing, IP hostnames, high-risk TLDs, and brand mimicry. Strictly rejects embedded authority credentials (`user:password@`). |
| **Server-Side Fetching Invariant** | **Implemented & Active** | Server-side web scraping and target URL fetching are **deliberately disabled** to eliminate SSRF exploit vectors and remote code execution hazards. |
| **Transparent Indicator Scoring** | **Implemented & Active** | Replaced arbitrary percentage scores with transparent indicator counts (`Critical`, `Warning`, `Info`) and clear categorical levels (`LOW`, `MEDIUM`, `HIGH`). A low score never implies verification or guaranteed safety. |
| **News Claim Verification** | **Implemented & Active** | Lexical Jaccard relevance matching prevents blind attribution. Candidate fact-checks below 0.25 similarity are rejected as `NO_MATCH`; 0.25–0.55 are labeled `POSSIBLE_MATCH` requiring review; >=0.55 are presented as `VERIFIED_MATCH` with publisher credit. |
| **External Provider Opt-In** | **Implemented & Active** | External reputation queries (Google Safe Browsing & Google Fact Check) require explicit user opt-in before submission. When unselected, analysis runs 100% locally with `CONSENT_WITHHELD` status. |
| **Bilingual Support (EN / HI)** | **Implemented & Active** | Complete interface, forms, error alerts, severity badges, modal disclosures, and analysis outputs in both English and Hindi. |
| **Privacy & Zero Storage** | **Implemented & Active** | Zero database persistence. All inputs are analyzed strictly in transient RAM. User text, URLs, and exception bodies are never logged. |
| **Abuse Mitigation** | **Implemented & Active** | Pseudonymous SHA-256 IP hashing with periodic memory-bounded eviction (60 requests/minute per client) and strict HTTP security headers (`nosniff`, `DENY`, `no-store`). HSTS conditionally applied when TLS is active. |
| **Google Safe Browsing API** | **Configurable (Optional)** | If `SAFE_BROWSING_API_KEY` is provided and user consents, queries Google threat lists. If absent, reports honest `NOT_CONFIGURED` status and relies on local heuristics. |
| **Google Fact Check API** | **Configurable (Optional)** | If `FACT_CHECK_API_KEY` is provided and user consents, queries Google Fact Check Tools API. If absent, reports honest `NOT_CONFIGURED` status. |
| **User Accounts / Profiles** | **Out of Scope (MVP)** | Intentionally excluded to guarantee user anonymity and prevent data collection. |
| **Database Storage** | **Out of Scope (MVP)** | No database configured. Submissions exist only for the lifespan of the request. |

---

## Prerequisites

Ensure you have the following installed on your machine:
- **Python**: v3.10, v3.11, or v3.12
- **Node.js**: v20.0.0 or higher (v22+ LTS recommended) with `npm`
- **Docker & Docker Compose** (optional, for containerized execution)

---

## Local Setup & Run Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Virat2218/Hack-Trust.git
cd Hack-Trust
```

### 2. Backend Setup & Run (FastAPI)
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. (Optional) Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   *Note: All external API keys are strictly optional. TrustShield AI operates fully with local heuristics when keys are omitted.*
5. Start the backend development server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be live at `http://127.0.0.1:8000`. You can inspect OpenAPI docs at `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup & Run (React + Vite)
In a second terminal window from the repository root:
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open `http://localhost:5173` in your browser. The Vite development proxy forwards all `/api/*` calls to the FastAPI backend on port 8000.

---

## Docker Deployment

TrustShield AI includes a multi-stage Dockerfile that builds the React frontend, packages the FastAPI backend, runs as an unprivileged non-root user (`appuser`, UID 1000), and includes an automated healthcheck.

### Using Docker Compose (Recommended)
```bash
# Build and run the containerized app
docker compose up --build

# Run in background
docker compose up -d

# Check container health status
docker compose ps
```
The application will be accessible at `http://localhost:8000`.

### Using Standalone Docker
```bash
# Build the production image
docker build -t trustshield-ai .

# Run the container
docker run -p 8000:8000 --name trustshield trustshield-ai
```

---

## Automated Verification & Testing

TrustShield AI includes comprehensive automated testing across both backend and frontend.

### 1. Backend Verification Test Suite
Run the master runner from the project root:
```bash
PYTHONPATH=backend python backend/run_all_checks.py
```
*(Or specify your virtualenv python: `PYTHONPATH=backend backend/venv/bin/python backend/run_all_checks.py`)*

This runs **8 verification suites**:
1. `backend/test_backend.py` — Analyzer heuristics (Message, URL, Claim).
2. `backend/test_api.py` — HTTP endpoints and schema responses.
3. `backend/test_providers.py` — 13 SSRF attack vector blocks and honest unconfigured provider fallbacks.
4. `backend/test_bilingual.py` — 100% Hindi field coverage across all output models.
5. `backend/test_edge_cases.py` — URL casing, Devanagari punctuation (danda), and benign low-risk content.
6. `backend/test_fact_check.py` — Jaccard lexical relevance scoring and claim match gating.
7. `backend/test_url_security.py` — Rejection of authority credentials (`user:pass@`), unsupported schemes, and malformed URLs.
8. `backend/test_http_e2e.py` — End-to-end FastAPI HTTP client tests, middleware security headers, rate limiting (429 Retry-After), and mocked external providers.

### 2. Frontend Test Suite & Production Build
```bash
cd frontend

# Run Vitest component and logic tests
npm test

# Verify production Vite compilation
npm run build
```

### 3. Continuous Integration
All pull requests and pushes to `main` are automatically verified via GitHub Actions (`.github/workflows/ci.yml`), running both the 8 backend suites and the frontend test/build jobs in parallel without requiring repository secrets.

---

## Environment Configuration Options

Environment variables can be set in `backend/.env` or passed via Docker Compose:

```ini
# Server configuration
PORT=8000
HOST=127.0.0.1

# Optional: Google Safe Browsing API v4 Key (for external URL reputation checks)
SAFE_BROWSING_API_KEY=

# Optional: Google Fact Check Tools API Key (for external claim verification checks)
FACT_CHECK_API_KEY=

# Optional: Comma-separated list of additional allowed CORS origins (e.g. https://trustshield.example.com)
ALLOWED_ORIGINS=
```

---

## Privacy & Security Guarantees

1. **Transient Memory Only:**
   User submissions exist strictly in volatile RAM for the duration of the HTTP request and are discarded immediately upon sending the response.
2. **Zero Database Persistence:**
   No SQL, NoSQL, or persistent disk storage is attached.
3. **Privacy-Preserving Logs:**
   Standard logging records only `METHOD /path -> Status Code (Duration ms)`. Request bodies, user text, target URLs, and exception messages are strictly excluded from logs.
4. **Server-Side Fetching Invariant:**
   TrustShield AI evaluates domain structures and queries documented reputation APIs; it intentionally does **not** fetch, scrape, or execute remote HTML/JS from submitted links, eliminating SSRF and remote code execution hazards.
5. **Rate Limiting with Pseudonymous Hashing:**
   Requests are throttled to 60 requests per minute using a 16-character SHA-256 hash of the client IP. Inactive records are automatically pruned every 5 minutes to prevent unbounded memory growth.
6. **Hardened HTTP Headers:**
   Every response includes `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Cache-Control: no-store`. `Strict-Transport-Security` is applied when TLS is active.

---

## Known Technical Limitations & Disclosures

1. **Decision Support, Not Proof:** Linguistic and heuristic signals cannot prove that a message is genuine or that a news event occurred. Critical decisions must be corroborated with primary official sources.
2. **Shortened URLs:** Because server-side fetching is disabled for security, shortened URLs (`bit.ly`, `tinyurl.com`) are flagged with a `WARNING` signal advising caution rather than being automatically followed.
3. **Blocklist Latency:** Brand-new phishing domains registered minutes before inspection may not yet appear on Google Safe Browsing blocklists.
4. **Machine Translation:** Hindi translations are model-assisted for accessibility and have not undergone certified human court-grade linguistic review.
5. **In-Memory Rate Limiting Scope:** The built-in rate limiter operates in-memory for single-process deployments. Horizontally scaled multi-server deployments would require a distributed key-value store (e.g., Redis).

# TrustShield AI

TrustShield AI is a transparent, privacy-first decision-support web platform designed to help everyday users assess suspicious messages, links, and news claims. It explains the indicators behind each assessment and provides practical, actionable safety guidance.

> **Important Advisory:** TrustShield AI is an educational and analytical advisory tool. It does **not** provide guarantees that any message is safe or that any news claim is true or false. Critical financial, medical, or legal matters must always be verified directly through recognized official channels.

---

## Architecture Overview

TrustShield AI is built as a lightweight, decoupled full-stack application with zero persistent database dependencies:

```
Trust-Shield-Ai/
├── frontend/                 # React 18 + Vite + Tailwind CSS + Lucide Icons
│   ├── src/
│   │   ├── components/      # UI Shell, Input Forms, Results Card, Modals
│   │   ├── context/         # LanguageContext (English & Hindi)
│   │   ├── i18n/            # Localization dictionary (translations.js)
│   │   └── utils/           # Client-side validation & SSRF restrictions
│   └── package.json
├── backend/                  # Python 3.10+ with FastAPI
│   ├── app/
│   │   ├── analyzers/       # Explainable heuristic analyzers (Message, URL, Claim)
│   │   ├── providers/       # Pluggable adapters (Safe Browsing, Fact Check)
│   │   ├── config.py        # Environment settings loader
│   │   ├── schemas.py       # Pydantic v2 data contracts
│   │   └── main.py          # FastAPI application, CORS, rate limiting
│   ├── requirements.txt
│   ├── .env.example
│   └── run_all_checks.py    # Master test suite runner
└── README.md
```

---

## Feature Status

| Feature Area | Status | Description |
| :--- | :--- | :--- |
| **Suspicious Message Analysis** | **Implemented & Active** | Detects false urgency cues, bank/utility/lottery impersonation, OTP/credential solicitation, and suspicious contacts in English and Hindi. |
| **Safe URL Assessment** | **Implemented & Active** | Enforces strict SSRF defense (blocking loopback, private ranges, cloud metadata), detects Punycode spoofing, IP hostnames, high-risk TLDs, and brand mimicry. |
| **News Claim Examination** | **Implemented & Active** | Analyzes viral sensationalism, unverified medical miracle cures, fake government schemes, and authority appeals without primary citations. |
| **Bilingual Support (EN / HI)** | **Implemented & Active** | Complete interface, forms, error alerts, severity badges, and analysis outputs in both English and Hindi. |
| **Transient Zero-Storage Privacy** | **Implemented & Active** | Zero database persistence. In-memory processing only. Zero logging of user-submitted text or URLs. |
| **Abuse Mitigation** | **Implemented & Active** | In-memory sliding-window rate limiter (60 requests/minute per IP) and HTTP security headers (`nosniff`, `DENY`). |
| **Google Safe Browsing API** | **Configurable (Optional)** | If `SAFE_BROWSING_API_KEY` is provided in `.env`, checks Google threat lists. If absent, reports honest `NOT_CONFIGURED` status and relies on local heuristics. |
| **Google Fact Check API** | **Configurable (Optional)** | If `FACT_CHECK_API_KEY` is provided in `.env`, queries verified fact-checking records. If absent, reports honest `NOT_CONFIGURED` status. |
| **User Accounts / Profiles** | **Out of Scope (MVP)** | Intentionally excluded to guarantee user anonymity and prevent data collection. |
| **Database Storage** | **Out of Scope (MVP)** | No database configured. Submissions are purged from memory immediately after analysis. |

---

## Prerequisites

Ensure you have the following installed on your machine:
- **Node.js**: v18.0.0 or higher (v20+ recommended)
- **Python**: v3.10 or higher
- **Git** (optional, for version management)

---

## Quickstart Setup & Run Guide

### Step 1: Clone or Open the Workspace
Navigate to the project root directory:
```bash
cd /Users/alok/Trust-Shield-Ai
```

### Step 2: Set Up & Start the Backend (FastAPI)
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. (Optional) Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   *Note: All external API keys are strictly optional. TrustShield AI runs fully without them.*
5. Start the backend development server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be live at `http://127.0.0.1:8000`. You can inspect the interactive OpenAPI documentation at `http://127.0.0.1:8000/docs`.

### Step 3: Set Up & Start the Frontend (React + Vite)
In a new terminal window:
1. Navigate to the `frontend/` directory:
   ```bash
   cd /Users/alok/Trust-Shield-Ai/frontend
   ```
2. Install frontend packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open `http://localhost:5173` in your web browser.

---

## Environment Configuration

The backend reads settings from `backend/.env`. A placeholder file `backend/.env.example` is provided:

```ini
PORT=8000
HOST=127.0.0.1

# Optional: Google Safe Browsing API v4 Key (for external URL reputation)
SAFE_BROWSING_API_KEY=

# Optional: Google Fact Check Tools API Key (for external claim verification)
FACT_CHECK_API_KEY=
```

### Adding Optional API Keys
- **Google Safe Browsing:** Obtain a free API key from the [Google Cloud Console](https://console.cloud.google.com/) for the *Safe Browsing APIs*. Paste it into `SAFE_BROWSING_API_KEY`.
- **Google Fact Check Tools API:** Obtain an API key from Google Cloud for the *Fact Check Tools API*. Paste it into `FACT_CHECK_API_KEY`.

If either key is omitted or left empty, TrustShield AI automatically falls back to local heuristic engines and displays an honest `Not Configured (Optional key not set)` badge in the Evidence section—it will never simulate or fabricate third-party results.

---

## Privacy & Security Guarantees

1. **Transient Memory Only:**
   - User submissions (messages, links, news claims) exist only in volatile RAM for the duration of the HTTP request and are discarded immediately upon sending the response.
2. **Zero Storage & Zero Analytics:**
   - No relational or NoSQL database is attached. No tracking cookies or analytics pixels are included.
3. **No User Content in Logs:**
   - Backend logging middleware records solely `METHOD /path -> Status Code (Duration ms)`. Request bodies and user parameters are strictly omitted from terminal stdout and log files.
4. **Strict SSRF Defense:**
   - The backend actively inspects hostnames and DNS resolutions to block requests to loopback addresses (`127.0.0.1`, `localhost`), link-local metadata endpoints (`169.254.169.254`), private RFC1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and internal TLDs (`.local`, `.internal`).
5. **No Arbitrary Remote Execution:**
   - TrustShield AI analyzes domain structures and queries documented reputation APIs; it intentionally does **not** fetch, render, or execute remote HTML/JS from untrusted links.
6. **In-Memory Rate Limiting:**
   - Requests are throttled to 60 requests per minute per IP address to safeguard the service from denial-of-service hammering.

---

## Running Verification Tests

You can run the comprehensive automated test suite at any time from the workspace root:

```bash
PYTHONPATH=backend backend/venv/bin/python backend/run_all_checks.py
```

This master runner executes 5 focused test suites:
1. `backend/test_backend.py` — Verifies rule pattern matching and calibrated risk scoring.
2. `backend/test_api.py` — Verifies FastAPI endpoint responses and schema validations.
3. `backend/test_providers.py` — Verifies 13 SSRF attack vector blocks and honest unconfigured provider fallbacks.
4. `backend/test_bilingual.py` — Verifies 100% Hindi field coverage across all output models.
5. `backend/test_edge_cases.py` — Verifies URL case insensitivity, Devanagari punctuation (danda), and benign low-risk content.

To verify frontend compilation:
```bash
cd frontend && npm run build
```

---

## Known Technical Limitations & Disclosures

1. **Heuristic Scope:** Heuristic rules assess common urgency cues, impersonation patterns, and structural anomalies. Sophisticated targeted attacks or brand-new terminology may not trigger existing rules.
2. **HTTPS vs. Trust:** A valid HTTPS certificate proves encrypted communication; it does not guarantee that the site operator is legitimate.
3. **Translation Disclosure:** Hindi translations are model-assisted for accessibility and have not undergone certified professional human linguistic review.
4. **Rate Limiting Scope:** The current rate limiter operates in-memory for single-process deployments. Clustered deployments across multiple servers would require an external key-value store (e.g. Redis).


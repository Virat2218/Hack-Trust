import os
import time
import hashlib
import logging
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.schemas import (
    MessageAnalyzeRequest,
    UrlAnalyzeRequest,
    ClaimAnalyzeRequest,
    AnalysisResult,
    HealthResponse
)
from app.analyzers.message_analyzer import analyze_message_text
from app.analyzers.url_analyzer import analyze_url_target
from app.analyzers.claim_analyzer import analyze_claim_text
from app.config import settings

# Configure privacy-preserving logging (NO logging of request bodies or user content)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("trustshield")

app = FastAPI(
    title="TrustShield AI API",
    description="Privacy-preserving decision-support API for assessing suspicious messages, URLs, and news claims.",
    version="1.0.0"
)

# CORS configuration with configurable origins from environment
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
env_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
origins = list(set(default_origins + env_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Bounded, privacy-preserving in-memory rate limiter
# Uses a pseudonymous 16-character SHA-256 hash of the client IP to avoid storing raw IPs
# Implements automatic eviction to prevent unbounded memory growth
RATE_LIMIT_WINDOW = 60 # seconds
MAX_REQUESTS_PER_WINDOW = 60
_request_counts = {}
_last_cleanup = time.time()
CLEANUP_INTERVAL = 300 # prune expired entries every 5 minutes

def _get_anonymized_ip_hash(client_ip: str) -> str:
    # 16-character pseudonymous hash
    return hashlib.sha256(f"ts_salt_{client_ip}".encode("utf-8")).hexdigest()[:16]

def _evict_expired_clients(now: float):
    global _last_cleanup, _request_counts
    if now - _last_cleanup > CLEANUP_INTERVAL or len(_request_counts) > 2000:
        expired_keys = [
            k for k, timestamps in _request_counts.items()
            if not timestamps or now - timestamps[-1] > RATE_LIMIT_WINDOW
        ]
        for k in expired_keys:
            del _request_counts[k]
        _last_cleanup = now

@app.middleware("http")
async def security_and_privacy_middleware(request: Request, call_next):
    # 1. Privacy-preserving rate limiting with pseudonymous hashing & memory bounds
    client_ip = request.client.host if request.client else "unknown"
    client_hash = _get_anonymized_ip_hash(client_ip)
    now = time.time()
    
    _evict_expired_clients(now)
    
    timestamps = _request_counts.get(client_hash, [])
    # Filter to active window
    active_timestamps = [ts for ts in timestamps if now - ts < RATE_LIMIT_WINDOW]
    
    if len(active_timestamps) >= MAX_REQUESTS_PER_WINDOW:
        logger.warning("Rate limit exceeded for incoming analysis request.")
        return Response(
            content='{"detail":"Too many analysis requests. Please wait a moment before trying again."}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json",
            headers={"Retry-After": "60"}
        )
    
    active_timestamps.append(now)
    _request_counts[client_hash] = active_timestamps

    # 2. Process request & calculate execution time
    start_time = time.time()
    response: Response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    # 3. Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

    # Strict-Transport-Security ONLY applied when TLS is active or indicated by reverse proxy
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    if is_https:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Log only method, path, and status code (strictly zero request body or user parameters)
    logger.info(f"{request.method} {request.url.path} -> Status {response.status_code} ({duration_ms}ms)")
    return response

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        providers={
            "local_heuristics": True,
            "safe_browsing": bool(settings.safe_browsing_api_key),
            "fact_check": bool(settings.fact_check_api_key)
        }
    )

@app.post("/api/analyze/message", response_model=AnalysisResult)
async def analyze_message_endpoint(payload: MessageAnalyzeRequest):
    try:
        result = analyze_message_text(payload.text, payload.language or "en")
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Internal error analyzing message [type={type(e).__name__}]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal analysis error while evaluating message."
        )

@app.post("/api/analyze/url", response_model=AnalysisResult)
async def analyze_url_endpoint(payload: UrlAnalyzeRequest):
    try:
        result = analyze_url_target(
            payload.url,
            payload.language or "en",
            payload.allow_external_lookup
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Internal error analyzing URL [type={type(e).__name__}]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal analysis error while evaluating URL."
        )

@app.post("/api/analyze/claim", response_model=AnalysisResult)
async def analyze_claim_endpoint(payload: ClaimAnalyzeRequest):
    try:
        result = analyze_claim_text(
            payload.text,
            payload.language or "en",
            payload.allow_external_lookup
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Internal error analyzing claim [type={type(e).__name__}]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal analysis error while evaluating news claim."
        )

# Production static frontend mounting (if frontend/dist exists)
FRONTEND_DIST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
    "dist"
)
if os.path.isdir(FRONTEND_DIST_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="static_frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)

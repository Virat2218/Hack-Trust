import os
import time
import logging
from collections import defaultdict
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

# CORS configuration for decoupled local or remote development
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# In-memory transient rate limiter to guard against local denial-of-service abuse
RATE_LIMIT_WINDOW = 60 # seconds
MAX_REQUESTS_PER_WINDOW = 60
_request_counts = defaultdict(list)

@app.middleware("http")
async def security_and_privacy_middleware(request: Request, call_next):
    # 1. Rate limiting check (using transient in-memory timestamps)
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Prune old timestamps
    _request_counts[client_ip] = [ts for ts in _request_counts[client_ip] if now - ts < RATE_LIMIT_WINDOW]
    
    if len(_request_counts[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        logger.warning(f"Rate limit exceeded for client {client_ip}")
        return Response(
            content='{"detail":"Too many analysis requests. Please wait a moment before trying again."}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json"
        )
    
    _request_counts[client_ip].append(now)

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
    except Exception as e:
        logger.error(f"Error analyzing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal analysis error while evaluating message."
        )

@app.post("/api/analyze/url", response_model=AnalysisResult)
async def analyze_url_endpoint(payload: UrlAnalyzeRequest):
    try:
        result = analyze_url_target(payload.url, payload.language or "en")
        return result
    except Exception as e:
        logger.error(f"Error analyzing URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal analysis error while evaluating URL."
        )

@app.post("/api/analyze/claim", response_model=AnalysisResult)
async def analyze_claim_endpoint(payload: ClaimAnalyzeRequest):
    try:
        result = analyze_claim_text(payload.text, payload.language or "en")
        return result
    except Exception as e:
        logger.error(f"Error analyzing claim: {str(e)}")
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

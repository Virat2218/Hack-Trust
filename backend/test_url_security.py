import asyncio
from fastapi import HTTPException
from app.main import (
    app,
    analyze_url_endpoint,
    analyze_message_endpoint,
    analyze_claim_endpoint
)
from app.schemas import UrlAnalyzeRequest, MessageAnalyzeRequest, ClaimAnalyzeRequest
from app.analyzers.url_analyzer import validate_and_parse_url, analyze_url_target

def test_url_credentials_rejected():
    credential_cases = [
        "http://admin:secret123@evil.com/login",
        "https://user:password@bank.com",
        "user:pass@legit-looking.xyz",
        "http://victim@attacker.com"
    ]
    for bad_url in credential_cases:
        try:
            validate_and_parse_url(bad_url)
            assert False, f"Expected credentials rejection for {bad_url}, but passed."
        except ValueError as e:
            assert "credentials" in str(e).lower(), f"Expected credential error message, got: {e}"
    print("✓ All URLs with authority credentials strictly rejected with ValueError.")

def test_unsupported_schemes_rejected():
    scheme_cases = [
        "javascript:alert(document.cookie)",
        "file:///etc/passwd",
        "ftp://ftp.example.com/file.txt",
        "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
        "gopher://gopher.example.com",
    ]
    for bad_scheme in scheme_cases:
        try:
            validate_and_parse_url(bad_scheme)
            assert False, f"Expected scheme rejection for {bad_scheme}, but passed."
        except ValueError as e:
            assert "unsupported" in str(e).lower() or "accepts only http and https" in str(e).lower(), f"Unexpected error: {e}"
    print("✓ All unsupported protocol schemes strictly rejected.")

def test_malformed_urls_rejected():
    malformed_cases = [
        "http://",
        "https://",
        "http://.com",
        "http://..evil.com",
        "https://evil..com",
        "http://has spaces.com/test",
        "http://has\x00nullbyte.com"
    ]
    for bad_url in malformed_cases:
        try:
            validate_and_parse_url(bad_url)
            assert False, f"Expected malformed rejection for '{bad_url}', but passed."
        except ValueError:
            pass
    print("✓ All malformed / syntax-violating URLs strictly rejected.")

def test_valid_http_https_accepted():
    valid_cases = [
        ("https://example.com", "example.com", "https"),
        ("http://example.com/path?query=1", "example.com", "http"),
        ("subdomain.trusted-service.org", "subdomain.trusted-service.org", "https"),
        ("https://sbi-rewards.portal.xyz", "sbi-rewards.portal.xyz", "https"),
    ]
    for raw, expected_host, expected_scheme in valid_cases:
        normalized, host, scheme = validate_and_parse_url(raw)
        assert host == expected_host
        assert scheme == expected_scheme
    print("✓ Valid HTTP and HTTPS URLs accepted and normalized.")

async def test_api_endpoint_url_security_rejections():
    # 1. Credential URL should raise HTTP 400
    try:
        req = UrlAnalyzeRequest(url="http://admin:secret@phishing.com")
        await analyze_url_endpoint(req)
        assert False, "Expected 400 HTTPException for credentials"
    except HTTPException as he:
        assert he.status_code == 400
        assert "credentials" in he.detail.lower()

    # 2. Unsupported scheme should raise HTTP 400
    try:
        req = UrlAnalyzeRequest(url="file:///etc/shadow")
        await analyze_url_endpoint(req)
        assert False, "Expected 400 HTTPException for file:// scheme"
    except HTTPException as he:
        assert he.status_code == 400
        assert "unsupported" in he.detail.lower()

    # 3. Legitimate SSRF target is analyzed with high risk rather than crashing
    req_ssrf = UrlAnalyzeRequest(url="http://169.254.169.254/latest/meta-data")
    res_ssrf = await analyze_url_endpoint(req_ssrf)
    assert res_ssrf.risk_level == "HIGH"
    assert any(s.id == "ssrf_blocked" for s in res_ssrf.signals)
    print("✓ API endpoint URL security checks and HTTP 400 rejections verified.")

if __name__ == "__main__":
    test_url_credentials_rejected()
    test_unsupported_schemes_rejected()
    test_malformed_urls_rejected()
    test_valid_http_https_accepted()
    asyncio.run(test_api_endpoint_url_security_rejections())
    print("All Phase 7 URL Handling & Security tests passed successfully!")

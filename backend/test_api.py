import asyncio
from app.main import (
    health_check,
    analyze_message_endpoint,
    analyze_url_endpoint,
    analyze_claim_endpoint
)
from app.schemas import (
    MessageAnalyzeRequest,
    UrlAnalyzeRequest,
    ClaimAnalyzeRequest
)

async def run_tests():
    # 1. Test health endpoint
    health = await health_check()
    assert health.status == "healthy"
    assert health.providers["local_heuristics"] is True
    print("✓ Health endpoint OK")

    # 2. Test message endpoint
    msg_req = MessageAnalyzeRequest(
        text="URGENT: Your SBI bank account will be blocked tonight! Click http://sbi-kyc-verify.top to update PAN card immediately."
    )
    msg_res = await analyze_message_endpoint(msg_req)
    assert msg_res.risk_level == "HIGH"
    assert len(msg_res.signals) >= 3
    print("✓ Message endpoint OK")

    # 3. Test URL endpoint with SSRF target
    url_req = UrlAnalyzeRequest(url="http://127.0.0.1:8000/admin")
    url_res = await analyze_url_endpoint(url_req)
    assert url_res.risk_level == "HIGH"
    assert any(s.id == "ssrf_blocked" for s in url_res.signals)
    print("✓ URL SSRF protection endpoint OK")

    # 4. Test claim endpoint
    claim_req = ClaimAnalyzeRequest(
        text="Drinking boiled garlic water is 100% cure for cancer! Doctors secretly admitted this. Share before deleted!"
    )
    claim_res = await analyze_claim_endpoint(claim_req)
    assert claim_res.risk_level == "HIGH"
    assert any(s.category == "UNVERIFIED_SOURCE" for s in claim_res.signals)
    print("✓ News claim endpoint OK")

if __name__ == "__main__":
    asyncio.run(run_tests())
    print("All backend API endpoints verified successfully!")

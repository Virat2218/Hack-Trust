import sys
from app.schemas import AnalysisResult
from app.analyzers.message_analyzer import analyze_message_text
from app.analyzers.url_analyzer import analyze_url_target
from app.analyzers.claim_analyzer import analyze_claim_text

def test_message_analyzer():
    # Test scam message
    scam_msg = "URGENT: Your SBI bank account will be blocked tonight! Click http://sbi-kyc-verify.top to update PAN card immediately."
    res = analyze_message_text(scam_msg, "en")
    assert isinstance(res, AnalysisResult)
    assert res.risk_level == "HIGH", f"Expected HIGH, got {res.risk_level}"
    assert len(res.signals) >= 3, f"Expected at least 3 signals, got {len(res.signals)}"
    assert res.critical_signals_count >= 1

    # Test benign message
    benign_msg = "Hey Alok, are we still meeting for lunch tomorrow at 1 PM?"
    res2 = analyze_message_text(benign_msg, "en")
    assert res2.risk_level == "LOW"
    print("✓ Message Analyzer tests passed.")

def test_url_analyzer():
    # Test SSRF block
    res_ssrf = analyze_url_target("http://127.0.0.1:8080/admin")
    assert res_ssrf.risk_level == "HIGH"
    assert any(s.id == "ssrf_blocked" for s in res_ssrf.signals)

    # Test high risk TLD & punycode
    res_punycode = analyze_url_target("http://xn--80ak6aa92e.com")
    assert any(s.id == "punycode_detected" for s in res_punycode.signals)

    # Test brand mimicry
    res_mimic = analyze_url_target("https://sbi-login.fake-verify.xyz/update")
    assert res_mimic.risk_level == "HIGH"
    print("✓ URL Analyzer tests passed.")

def test_claim_analyzer():
    # Test sensational medical claim
    miracle_claim = "Drinking boiled garlic water is 100% cure for cancer! Doctors secretly admitted this. Share before deleted!"
    res = analyze_claim_text(miracle_claim, "en")
    assert res.risk_level == "HIGH"
    assert any(s.category == "UNVERIFIED_SOURCE" for s in res.signals)

    # Test normal claim
    normal_claim = "The local municipality announced road repairs scheduled for next Monday."
    res2 = analyze_claim_text(normal_claim, "en")
    assert res2.risk_level == "LOW"
    print("✓ Claim Analyzer tests passed.")

if __name__ == "__main__":
    test_message_analyzer()
    test_url_analyzer()
    test_claim_analyzer()
    print("All backend analysis tests passed successfully!")


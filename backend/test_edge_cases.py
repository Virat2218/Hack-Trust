import time
import socket
from app.analyzers.message_analyzer import analyze_message_text
from app.analyzers.url_analyzer import analyze_url_target
from app.analyzers.claim_analyzer import analyze_claim_text
from app.schemas import AnalysisResult

def test_hindi_message_detection():
    # Hindi electricity cutoff message
    hi_msg = "तुरंत बिजली बिल भरें अन्यथा आज रात बिजली काट दी जाएगी। कॉल करें 9876543210 पर।"
    res = analyze_message_text(hi_msg, "hi")
    assert res.risk_level in ["MEDIUM", "HIGH"]
    assert any("Hindi" in s.label or "बिजली" in s.label_hi for s in res.signals)
    print("✓ Hindi message heuristic detection passed.")

def test_url_normalization_and_casing():
    # Uppercase URL with trailing path
    raw = "  HTTPS://SBI-REWARDS.PORTAL.XYZ/Update/  "
    res = analyze_url_target(raw, "en")
    assert res.risk_level == "HIGH"
    assert any(s.id == "high_risk_tld" for s in res.signals)
    assert any("brand_mimic" in s.id for s in res.signals)
    print("✓ URL normalization & case insensitivity passed.")

def test_hindi_claim_detection():
    # Hindi health claim
    hi_claim = "चमत्कारी इलाज: लहसुन का पानी पीने से 100% कैंसर ठीक होता है। सबको भेजें!"
    res = analyze_claim_text(hi_claim, "hi")
    assert res.risk_level == "HIGH"
    assert any("Hindi" in s.label or "चमत्कारी" in s.label_hi for s in res.signals)
    print("✓ Hindi viral claim detection passed.")

def test_financial_fraud_patterns():
    # UPI collect scam
    upi_msg = "Congratulation! Refund of Rs 4999 approved. Enter your UPI PIN to receive money in bank account."
    res_upi = analyze_message_text(upi_msg, "en")
    assert res_upi.risk_level in ["MEDIUM", "HIGH"]
    assert any("UPI" in s.label for s in res_upi.signals)

    # Job task scam
    job_msg = "Earn 3000-5000 daily by liking YouTube videos and rating hotels. Contact Telegram @job_hr."
    res_job = analyze_message_text(job_msg, "en")
    assert res_job.risk_level in ["MEDIUM", "HIGH"]
    assert any("Job Scam" in s.label for s in res_job.signals)

    # Courier delivery scam
    courier_msg = "Your parcel delivery failed because address is missing. Update address immediately."
    res_courier = analyze_message_text(courier_msg, "en")
    assert res_courier.risk_level in ["MEDIUM", "HIGH"]
    assert any("Parcel" in s.label for s in res_courier.signals)
    print("✓ Financial, Job & Courier scam patterns passed.")

def test_edge_case_benign_content():
    # Standard benign message
    benign = "Hello Team, please find attached the meeting minutes from our morning discussion."
    res = analyze_message_text(benign, "en")
    assert res.risk_level == "LOW"
    assert res.critical_signals_count == 0
    print("✓ Benign content low risk score verified.")

if __name__ == "__main__":
    test_hindi_message_detection()
    test_financial_fraud_patterns()
    test_url_normalization_and_casing()
    test_hindi_claim_detection()
    test_edge_case_benign_content()
    print("All Phase 9 edge case verification checks passed!")


from app.analyzers.message_analyzer import analyze_message_text
from app.analyzers.url_analyzer import analyze_url_target
from app.analyzers.claim_analyzer import analyze_claim_text

def test_bilingual_coverage():
    # 1. Message Analyzer Hindi coverage
    msg_res = analyze_message_text("URGENT: SBI bank account blocked tonight! Update KYC immediately.", "hi")
    assert msg_res.summary_hi, "Missing Hindi summary in message analyzer"
    assert len(msg_res.uncertainty_notes_hi) > 0, "Missing Hindi uncertainty notes"
    assert len(msg_res.recommended_actions_hi) > 0, "Missing Hindi actions"
    for s in msg_res.signals:
        assert s.label_hi, f"Signal {s.id} missing label_hi"
        assert s.description_hi, f"Signal {s.id} missing description_hi"
    print("✓ Message analyzer bilingual fields verified.")

    # 2. URL Analyzer Hindi coverage
    url_res = analyze_url_target("https://sbi-login.fake-portal.xyz/verify", "hi")
    assert url_res.summary_hi, "Missing Hindi summary in URL analyzer"
    assert len(url_res.uncertainty_notes_hi) > 0
    assert len(url_res.recommended_actions_hi) > 0
    for s in url_res.signals:
        assert s.label_hi, f"Signal {s.id} missing label_hi"
        assert s.description_hi, f"Signal {s.id} missing description_hi"
    print("✓ URL analyzer bilingual fields verified.")

    # 3. Claim Analyzer Hindi coverage
    claim_res = analyze_claim_text("Drinking boiled garlic cures 100% of cancer! Forward to everyone!", "hi")
    assert claim_res.summary_hi, "Missing Hindi summary in Claim analyzer"
    assert len(claim_res.uncertainty_notes_hi) > 0
    assert len(claim_res.recommended_actions_hi) > 0
    for s in claim_res.signals:
        assert s.label_hi, f"Signal {s.id} missing label_hi"
        assert s.description_hi, f"Signal {s.id} missing description_hi"
    print("✓ Claim analyzer bilingual fields verified.")

if __name__ == "__main__":
    test_bilingual_coverage()
    print("All bilingual backend checks passed successfully!")


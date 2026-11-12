import io
import logging
from unittest.mock import patch, MagicMock
from app.providers.fact_check import compute_claim_relevance, FactCheckProvider

def test_claim_relevance_calculation():
    # Identical claims
    score_exact = compute_claim_relevance(
        "Drinking boiled garlic water cures cancer",
        "Drinking boiled garlic water cures 100% of cancer"
    )
    assert score_exact >= 0.6, f"Expected high overlap, got {score_exact}"

    # Completely unrelated claims
    score_unrelated = compute_claim_relevance(
        "Garlic water cures cancer",
        "NASA announces Artemis moon launch date for next November"
    )
    assert score_unrelated == 0.0, f"Expected 0.0, got {score_unrelated}"
    print("✓ Claim relevance similarity scores verified.")

def test_unrelated_provider_result_rejected_as_no_match():
    # If API returns an unrelated claim, relevance filter must reject it as NO_MATCH
    provider = FactCheckProvider(api_key="mock_key")
    mock_api_data = {
        "claims": [
            {
                "text": "The moon is made of green cheese, claims scientist",
                "claimReview": [
                    {
                        "publisher": {"name": "Snopes"},
                        "textualRating": "False",
                        "url": "https://snopes.com/fact-check/moon-cheese"
                    }
                ]
            }
        ]
    }

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_api_data
        mock_get.return_value = mock_resp

        res = provider.check("Free electricity scheme for all students in Delhi")
        assert res.provider_status.status == "NO_MATCH", f"Expected NO_MATCH, got {res.provider_status.status}"
        assert len(res.signals) == 0, "Should not attach fact-check signal for unrelated claim"
        print("✓ Unrelated provider result successfully rejected as NO_MATCH.")

def test_high_similarity_reported_as_matching_record_not_verified():
    provider = FactCheckProvider(api_key="mock_key")
    mock_api_data = {
        "claims": [
            {
                "text": "Drinking boiled garlic water cures 100% of cancer cases",
                "claimReview": [
                    {
                        "publisher": {"name": "BOOM Live"},
                        "textualRating": "False",
                        "url": "https://boomlive.in/fact-check/garlic-cancer",
                        "reviewDate": "2024-05-10"
                    }
                ]
            }
        ]
    }

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_api_data
        mock_get.return_value = mock_resp

        res = provider.check("Drinking boiled garlic water cures cancer")
        # Must report MATCH_FOUND, not claim claim itself is "verified"
        assert res.provider_status.status == "MATCH_FOUND"
        assert len(res.signals) == 1
        assert "BOOM Live" in res.signals[0].label
        assert "Matching Fact-Check Record" in res.signals[0].label
        assert res.matched_data["match_confidence"] == "STRONG_OVERLAP"
        print("✓ High-overlap result correctly labeled as MATCH_FOUND with publisher attribution.")

def test_misleading_high_overlap_and_negation():
    # Verify that opposite polarity statements still reflect token similarity
    # but the system makes clear text similarity does not prove identical meaning
    claim_a = "Drinking boiled garlic water cures cancer"
    claim_b = "Drinking boiled garlic water does NOT cure cancer"
    score = compute_claim_relevance(claim_a, claim_b)
    assert score >= 0.6, f"Expected high topic overlap, got {score}"

    provider = FactCheckProvider(api_key="mock_key")
    mock_api_data = {
        "claims": [
            {
                "text": claim_b,
                "claimReview": [
                    {
                        "publisher": {"name": "Health Feedback"},
                        "textualRating": "False",
                        "url": "https://healthfeedback.org/garlic"
                    }
                ]
            }
        ]
    }
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_api_data
        mock_get.return_value = mock_resp

        res = provider.check(claim_a)
        assert res.provider_status.status == "MATCH_FOUND"
        # The signal description explicitly states text similarity is not proof
        assert "text similarity does not prove claims are identical" in res.signals[0].description
        print("✓ Negation and contradictory wording boundaries verified.")

def test_provider_error_does_not_leak_api_key_in_logs():
    secret_key = "AIzaSySecretFakeApiKey123456789"
    provider = FactCheckProvider(api_key=secret_key)

    # Attach string stream to logger
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    fc_logger = logging.getLogger("trustshield.providers.factcheck")
    fc_logger.addHandler(handler)

    try:
        with patch("requests.get") as mock_get:
            # Simulate a network error that internally includes the full URL and key in error message
            mock_get.side_effect = Exception(
                f"HTTPSConnectionPool(host='factchecktools.googleapis.com', port=443): "
                f"Failed to connect to /v1alpha1/claims:search?key={secret_key}&query=test"
            )

            res = provider.check("Some test claim about viral rumors")
            assert res.provider_status.status == "ERROR"

            # Verify that the secret key does NOT appear in the captured logs
            log_output = log_stream.getvalue()
            assert secret_key not in log_output, "SECURITY BREACH: Secret API key leaked into provider logs!"
            # Verify details message returned to user doesn't contain key
            assert secret_key not in (res.provider_status.details or "")
            print("✓ Provider error logging strictly protects secret API keys from log exposure.")
    finally:
        fc_logger.removeHandler(handler)

if __name__ == "__main__":
    test_claim_relevance_calculation()
    test_unrelated_provider_result_rejected_as_no_match()
    test_high_similarity_reported_as_matching_record_not_verified()
    test_misleading_high_overlap_and_negation()
    test_provider_error_does_not_leak_api_key_in_logs()
    print("All Phase 3 & 4 Fact-Check Verification and Credential Protection tests passed successfully!")

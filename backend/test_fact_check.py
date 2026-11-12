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

def test_exact_match_accepted_as_verified_match():
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
        assert res.provider_status.status == "VERIFIED_MATCH"
        assert len(res.signals) == 1
        assert "BOOM Live" in res.signals[0].label
        assert res.matched_data["match_confidence"] == "EXACT"
        print("✓ Exact match correctly identified as VERIFIED_MATCH with publisher credit.")

if __name__ == "__main__":
    test_claim_relevance_calculation()
    test_unrelated_provider_result_rejected_as_no_match()
    test_exact_match_accepted_as_verified_match()
    print("All Phase 5 News Claim Verification tests passed successfully!")


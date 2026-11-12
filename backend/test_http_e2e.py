import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app, _request_counts
from app.providers.safe_browsing import SafeBrowsingProvider
from app.providers.fact_check import FactCheckProvider

class TestTrustShieldHttpE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        # Clear rate limit store between tests
        _request_counts.clear()

    # 1. Health & Security Headers
    def test_health_endpoint_and_security_headers(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["providers"]["local_heuristics"])

        # Validate security headers
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")
        self.assertEqual(response.headers.get("referrer-policy"), "strict-origin-when-cross-origin")
        self.assertIn("no-store", response.headers.get("cache-control", ""))

    # 2. Message Analysis
    def test_message_analysis_scam_high_risk(self):
        payload = {
            "text": "URGENT: Your SBI bank account will be deactivated in 24 hours. Update KYC immediately at http://sbi-fake.top",
            "language": "en"
        }
        response = self.client.post("/api/analyze/message", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["risk_level"], "HIGH")
        self.assertGreaterEqual(data["critical_signals_count"], 1)
        self.assertNotIn("risk_score", data)
        self.assertIn("summary", data)
        self.assertIn("summary_hi", data)
        self.assertIn("uncertainty_notes", data)
        self.assertIn("recommended_actions", data)

    def test_message_analysis_benign_low_risk(self):
        payload = {
            "text": "Hi team, please find attached the meeting minutes from this morning's architectural sync.",
            "language": "en"
        }
        response = self.client.post("/api/analyze/message", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["risk_level"], "LOW")
        self.assertEqual(data["critical_signals_count"], 0)

    def test_message_validation_rejects_empty_and_short(self):
        # Blank / whitespace only
        response = self.client.post("/api/analyze/message", json={"text": "       ", "language": "en"})
        self.assertEqual(response.status_code, 422)

        # Under 10 characters
        response = self.client.post("/api/analyze/message", json={"text": "Hello", "language": "en"})
        self.assertEqual(response.status_code, 422)

    # 3. URL Analysis & Security Boundaries
    def test_url_analysis_benign(self):
        payload = {"url": "https://example.com", "language": "en", "allow_external_lookup": False}
        response = self.client.post("/api/analyze/url", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["risk_level"], "LOW")
        self.assertEqual(data["critical_signals_count"], 0)
        # Verify privacy status
        sb_evidence = [e for e in data["evidence"] if "Safe Browsing" in e["source_name"]]
        self.assertTrue(len(sb_evidence) > 0)
        self.assertEqual(sb_evidence[0]["status"], "CONSENT_WITHHELD")

    def test_url_ssrf_protection_high_risk(self):
        # SSRF destination is analyzed locally, blocked from egress, and flagged HIGH
        payload = {"url": "http://169.254.169.254/latest/meta-data", "language": "en"}
        response = self.client.post("/api/analyze/url", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["risk_level"], "HIGH")
        self.assertTrue(any(s["id"] == "ssrf_blocked" for s in data["signals"]))

    def test_url_credentials_rejection_http_400(self):
        payload = {"url": "http://admin:secret@phishing.example.com/login"}
        response = self.client.post("/api/analyze/url", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("credentials", response.json()["detail"].lower())

    def test_url_unsupported_scheme_http_400(self):
        bad_schemes = [
            "javascript:alert(1)",
            "file:///etc/passwd",
            "ftp://files.example.com",
            "data:text/html,test"
        ]
        for url in bad_schemes:
            response = self.client.post("/api/analyze/url", json={"url": url})
            self.assertEqual(response.status_code, 400)
            self.assertIn("unsupported", response.json()["detail"].lower())

    def test_url_malformed_http_400(self):
        malformed = ["http://", "https://", "http://..invalid.com"]
        for url in malformed:
            response = self.client.post("/api/analyze/url", json={"url": url})
            self.assertEqual(response.status_code, 400)

    # 4. Mocked External Providers
    @patch.object(SafeBrowsingProvider, "is_configured", return_value=True)
    @patch("requests.post")
    def test_safe_browsing_threat_match_mocked(self, mock_post, mock_cfg):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "matches": [{
                    "threatType": "SOCIAL_ENGINEERING",
                    "platformType": "ANY_PLATFORM",
                    "threatEntryType": "URL",
                    "threat": {"url": "https://threat-site.com"}
                }]
            }
        )

        payload = {"url": "https://threat-site.com", "allow_external_lookup": True}
        response = self.client.post("/api/analyze/url", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["risk_level"], "HIGH")
        self.assertTrue(any(s["id"] == "safe_browsing_threat_match" for s in data["signals"]))
        sb_evidence = [e for e in data["evidence"] if "Safe Browsing" in e["source_name"]][0]
        self.assertEqual(sb_evidence["status"], "ACTIVE")

    @patch.object(SafeBrowsingProvider, "is_configured", return_value=True)
    @patch("requests.post")
    def test_safe_browsing_provider_error_graceful_fallback(self, mock_post, mock_cfg):
        mock_post.return_value = MagicMock(status_code=503)

        payload = {"url": "https://example.com", "allow_external_lookup": True}
        response = self.client.post("/api/analyze/url", json=payload)
        self.assertEqual(response.status_code, 200) # Backend continues with local heuristics
        data = response.json()
        sb_evidence = [e for e in data["evidence"] if "Safe Browsing" in e["source_name"]][0]
        self.assertEqual(sb_evidence["status"], "ERROR")

    @patch.object(FactCheckProvider, "is_configured", return_value=True)
    @patch("requests.get")
    def test_fact_check_exact_match_mocked(self, mock_get, mock_cfg):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "claims": [{
                    "text": "Drinking boiled garlic water cures cancer 100 percent",
                    "claimant": "Social media rumors",
                    "claimDate": "2024-01-15T00:00:00Z",
                    "claimReview": [{
                        "publisher": {"name": "Health Feedback", "site": "healthfeedback.org"},
                        "url": "https://healthfeedback.org/garlic-cancer",
                        "title": "Garlic water does not cure cancer",
                        "reviewDate": "2024-01-16T00:00:00Z",
                        "textualRating": "False"
                    }]
                }]
            }
        )

        payload = {
            "text": "Drinking boiled garlic water cures cancer 100 percent guaranteed!",
            "allow_external_lookup": True
        }
        response = self.client.post("/api/analyze/claim", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        fc_evidence = [e for e in data["evidence"] if "Fact Check" in e["source_name"]][0]
        self.assertEqual(fc_evidence["status"], "MATCH_FOUND")
        self.assertEqual(fc_evidence["match_confidence"], "STRONG_OVERLAP")
        self.assertEqual(fc_evidence["publisher"], "Health Feedback")
        self.assertEqual(fc_evidence["textual_rating"], "False")

    @patch.object(FactCheckProvider, "is_configured", return_value=True)
    @patch("requests.get")
    def test_fact_check_unrelated_result_rejected_as_no_match(self, mock_get, mock_cfg):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "claims": [{
                    "text": "NASA confirms moon made of green Swiss cheese",
                    "claimReview": [{
                        "publisher": {"name": "Snopes"},
                        "url": "https://snopes.com/moon-cheese",
                        "textualRating": "False"
                    }]
                }]
            }
        )

        # Submitted claim is completely unrelated to moon cheese
        payload = {
            "text": "Government announces free smartphone scheme for all students in 2026",
            "allow_external_lookup": True
        }
        response = self.client.post("/api/analyze/claim", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        fc_evidence = [e for e in data["evidence"] if "Fact Check" in e["source_name"]][0]
        self.assertEqual(fc_evidence["status"], "NO_MATCH")
        self.assertEqual(fc_evidence["match_confidence"], "NONE")

    # 5. Rate Limiting
    def test_rate_limiting_enforcement(self):
        # Fire 60 allowed requests
        for _ in range(60):
            res = self.client.get("/api/health")
            self.assertEqual(res.status_code, 200)

        # 61st request should be rate-limited
        blocked_res = self.client.get("/api/health")
        self.assertEqual(blocked_res.status_code, 429)
        self.assertEqual(blocked_res.headers.get("retry-after"), "60")
        self.assertIn("Too many analysis requests", blocked_res.json()["detail"])

if __name__ == "__main__":
    unittest.main()


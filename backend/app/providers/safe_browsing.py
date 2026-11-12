import requests
import logging
from typing import Optional
from app.providers.base import BaseProvider, ProviderCheckResponse
from app.schemas import ProviderStatus, AnalysisSignal
from app.config import settings

logger = logging.getLogger("trustshield.providers.safebrowsing")

class SafeBrowsingProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = (api_key or settings.safe_browsing_api_key or "").strip()

    @property
    def name(self) -> str:
        return "Google Safe Browsing API v4"

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def check(self, target_url: str, **kwargs) -> ProviderCheckResponse:
        if not self.is_configured():
            return ProviderCheckResponse(
                provider_status=ProviderStatus(
                    name=self.name,
                    configured=False,
                    status="NOT_CONFIGURED",
                    details="API key not set in environment (SAFE_BROWSING_API_KEY). Using local heuristics."
                )
            )

        endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={self._api_key}"
        payload = {
            "client": {
                "clientId": "trustshield-ai",
                "clientVersion": "1.0.0"
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION"
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": target_url}]
            }
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=3.0
            )

            if response.status_code != 200:
                logger.warning(f"Safe Browsing API returned HTTP {response.status_code}")
                return ProviderCheckResponse(
                    provider_status=ProviderStatus(
                        name=self.name,
                        configured=True,
                        status="ERROR",
                        details=f"Provider returned HTTP {response.status_code}. Analysis fell back to local heuristics."
                    )
                )

            data = response.json()
            matches = data.get("matches", [])

            if matches:
                # Matches detected on blocklist
                threat_types = list({m.get("threatType", "UNKNOWN") for m in matches})
                signals = [
                    AnalysisSignal(
                        id="safe_browsing_threat_match",
                        category="DOMAIN_ANOMALY",
                        label=f"Flagged by Google Safe Browsing ({', '.join(threat_types)})",
                        label_hi=f"गूगल सेफ ब्राउज़िंग द्वारा चेतावनी ({', '.join(threat_types)})",
                        description=f"Destination URL is flagged on public blocklists for active security threats: {', '.join(threat_types)}.",
                        description_hi=f"यह लिंक सक्रिय सुरक्षा खतरों के लिए सार्वजनिक सुरक्षा सूचियों में दर्ज है: {', '.join(threat_types)}।",
                        severity="CRITICAL"
                    )
                ]
                return ProviderCheckResponse(
                    provider_status=ProviderStatus(
                        name=self.name,
                        configured=True,
                        status="ACTIVE",
                        details=f"Threat match confirmed: {', '.join(threat_types)}"
                    ),
                    signals=signals,
                    additional_score=75,
                    matched_data={"matches": matches}
                )

            # URL is not currently listed as a known threat
            return ProviderCheckResponse(
                provider_status=ProviderStatus(
                    name=self.name,
                    configured=True,
                    status="ACTIVE",
                    details="No threat matches listed in public blocklists at this time."
                ),
                additional_score=0
            )

        except requests.exceptions.Timeout:
            logger.warning("Safe Browsing API request timed out (3s threshold).")
            return ProviderCheckResponse(
                provider_status=ProviderStatus(
                    name=self.name,
                    configured=True,
                    status="ERROR",
                    details="Provider lookup timed out after 3.0 seconds. Local heuristics were used."
                )
            )
        except Exception as e:
            logger.error(f"Error querying Safe Browsing API: {str(e)}")
            return ProviderCheckResponse(
                provider_status=ProviderStatus(
                    name=self.name,
                    configured=True,
                    status="ERROR",
                    details="Network error reaching reputation provider. Local heuristics were used."
                )
            )


import requests
import logging
from typing import Optional
from app.providers.base import BaseProvider, ProviderCheckResponse
from app.schemas import ProviderStatus, AnalysisSignal
from app.config import settings

logger = logging.getLogger("trustshield.providers.factcheck")

class FactCheckProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = (api_key or settings.fact_check_api_key or "").strip()

    @property
    def name(self) -> str:
        return "Google Fact Check Tools API"

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def check(self, claim_text: str, **kwargs) -> ProviderCheckResponse:
        if not self.is_configured():
            return ProviderCheckResponse(
                provider_status=ProviderStatus(
                    name=self.name,
                    configured=False,
                    status="NOT_CONFIGURED",
                    details="API key not set in environment (FACT_CHECK_API_KEY). Using local claim heuristics."
                )
            )

        # Truncate query to 150 chars for query safety
        sanitized_query = claim_text.strip()[:150]
        endpoint = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {
            "query": sanitized_query,
            "key": self._api_key,
            "languageCode": kwargs.get("language", "en")
        }

        try:
            response = requests.get(
                endpoint,
                params=params,
                timeout=3.0
            )

            if response.status_code != 200:
                logger.warning(f"Fact Check API returned HTTP {response.status_code}")
                return ProviderCheckResponse(
                    provider_status=ProviderStatus(
                        name=self.name,
                        configured=True,
                        status="ERROR",
                        details=f"Provider returned HTTP {response.status_code}. Analysis fell back to local heuristics."
                    )
                )

            data = response.json()
            claims = data.get("claims", [])

            if claims:
                top_claim = claims[0]
                reviews = top_claim.get("claimReview", [])
                signals = []

                if reviews:
                    review = reviews[0]
                    publisher = review.get("publisher", {}).get("name", "Recognized Fact-Checker")
                    rating = review.get("textualRating", "Unverified")
                    review_url = review.get("url", "")

                    signals.append(AnalysisSignal(
                        id="fact_check_matched",
                        category="UNVERIFIED_SOURCE",
                        label=f"Fact Check Found: Rated '{rating}' by {publisher}",
                        label_hi=f"तथ्य-जांच रिपोर्ट: {publisher} द्वारा '{rating}' रेटेड",
                        description=f"A matching claim has been independently investigated by {publisher} with conclusion: '{rating}'. Review available at: {review_url}",
                        description_hi=f"इस दावे की {publisher} द्वारा स्वतंत्र जांच की गई है। निष्कर्ष: '{rating}'।",
                        severity="CRITICAL" if any(w in rating.lower() for w in ["false", "fake", "hoax", "misleading", "incorrect", "गलत", "झूठ"]) else "WARNING"
                    ))

                return ProviderCheckResponse(
                    provider_status=ProviderStatus(
                        name=self.name,
                        configured=True,
                        status="ACTIVE",
                        details=f"Found {len(claims)} relevant fact-check review(s)."
                    ),
                    signals=signals,
                    additional_score=45 if signals else 0,
                    matched_data={"claims_count": len(claims)}
                )

            # No indexed reviews found
            return ProviderCheckResponse(
                provider_status=ProviderStatus(
                    name=self.name,
                    configured=True,
                    status="ACTIVE",
                    details="No indexed fact-checks matched this exact phrasing."
                ),
                additional_score=0
            )

        except requests.exceptions.Timeout:
            logger.warning("Fact Check API request timed out (3s threshold).")
            return ProviderCheckResponse(
                provider_status=ProviderStatus(
                    name=self.name,
                    configured=True,
                    status="ERROR",
                    details="Provider lookup timed out after 3.0 seconds. Local heuristics were used."
                )
            )
        except Exception as e:
            logger.error(f"Error querying Fact Check API: {str(e)}")
            return ProviderCheckResponse(
                provider_status=ProviderStatus(
                    name=self.name,
                    configured=True,
                    status="ERROR",
                    details="Network error reaching fact-check provider. Local heuristics were used."
                )
            )


import re
import requests
import logging
from typing import Optional, Tuple, Dict, Any, List
from app.providers.base import BaseProvider, ProviderCheckResponse
from app.schemas import ProviderStatus, AnalysisSignal, EvidenceItem
from app.config import settings

logger = logging.getLogger("trustshield.providers.factcheck")

STOPWORDS = {
    "the", "a", "an", "is", "in", "it", "of", "and", "or", "to", "for", "on",
    "that", "this", "by", "with", "as", "at", "from", "are", "was", "were",
    "be", "been", "have", "has", "had", "do", "does", "did", "you", "your",
    "we", "our", "they", "their", "he", "she", "his", "her", "will", "would",
    "का", "के", "की", "में", "से", "को", "पर", "है", "हैं", "था", "थी", "थे"
}

def compute_claim_relevance(submitted: str, candidate: str) -> float:
    """
    Computes token-level Jaccard similarity between the submitted claim
    and a candidate claim headline retrieved from a fact-checking index.
    Returns a score between 0.0 (no overlap) and 1.0 (identical tokens).
    """
    tokens_sub = set(re.findall(r"\w+", submitted.lower())) - STOPWORDS
    tokens_cand = set(re.findall(r"\w+", candidate.lower())) - STOPWORDS

    if not tokens_sub or not tokens_cand:
        return 0.0

    intersection = tokens_sub.intersection(tokens_cand)
    union = tokens_sub.union(tokens_cand)

    return len(intersection) / len(union) if union else 0.0

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

            if not claims:
                return ProviderCheckResponse(
                    provider_status=ProviderStatus(
                        name=self.name,
                        configured=True,
                        status="NO_MATCH",
                        details="No indexed fact-checks matched this statement. The lack of a published review does not verify or disprove the claim."
                    ),
                    additional_score=0,
                    matched_data={"match_confidence": "NONE"}
                )

            # Evaluate relevance across all returned claims
            best_claim = None
            best_score = -1.0
            for c in claims:
                c_text = c.get("text", "")
                score = compute_claim_relevance(claim_text, c_text)
                if score > best_score:
                    best_score = score
                    best_claim = c

            # If no claim met minimum relevance threshold (0.25)
            if best_score < 0.25 or not best_claim:
                return ProviderCheckResponse(
                    provider_status=ProviderStatus(
                        name=self.name,
                        configured=True,
                        status="NO_MATCH",
                        details="Retrieved database results did not meet relevance threshold for this statement. No reliable match found."
                    ),
                    additional_score=0,
                    matched_data={"match_confidence": "NONE"}
                )

            reviews = best_claim.get("claimReview", [])
            if not reviews:
                return ProviderCheckResponse(
                    provider_status=ProviderStatus(
                        name=self.name,
                        configured=True,
                        status="NO_MATCH",
                        details="Found matching claim entry but no investigative review was attached."
                    ),
                    additional_score=0,
                    matched_data={"match_confidence": "NONE"}
                )

            review = reviews[0]
            publisher = review.get("publisher", {}).get("name", "Recognized Fact-Checker")
            rating = review.get("textualRating", "Unverified")
            review_url = review.get("url", "")
            review_date = review.get("reviewDate", "")
            candidate_text = best_claim.get("text", "")

            # Strong verified match (score >= 0.55)
            if best_score >= 0.55:
                signals = [
                    AnalysisSignal(
                        id="fact_check_verified_match",
                        category="UNVERIFIED_SOURCE",
                        label=f"Verified Fact-Check: Rated '{rating}' by {publisher}",
                        label_hi=f"सत्यापित तथ्य-जांच रिपोर्ट: {publisher} द्वारा '{rating}' रेटेड",
                        description=f"A matching claim ('{candidate_text[:120]}...') was investigated by {publisher} with conclusion: '{rating}'. Review: {review_url}",
                        description_hi=f"इस दावे ('{candidate_text[:120]}...') की {publisher} द्वारा स्वतंत्र जांच की गई है। निष्कर्ष: '{rating}'।",
                        severity="CRITICAL" if any(w in rating.lower() for w in ["false", "fake", "hoax", "misleading", "incorrect", "गलत", "झूठ"]) else "WARNING"
                    )
                ]
                return ProviderCheckResponse(
                    provider_status=ProviderStatus(
                        name=self.name,
                        configured=True,
                        status="VERIFIED_MATCH",
                        details=f"High-confidence match ({round(best_score*100)}% lexical overlap) with claim investigated by {publisher}."
                    ),
                    signals=signals,
                    additional_score=45,
                    matched_data={
                        "publisher": publisher,
                        "rating": rating,
                        "review_url": review_url,
                        "review_date": review_date,
                        "reviewed_claim": candidate_text,
                        "match_confidence": "EXACT"
                    }
                )

            # Moderate / possible match (0.25 <= best_score < 0.55)
            # Must be clearly labeled as requiring user review, NOT presented as verified
            signals = [
                AnalysisSignal(
                    id="fact_check_possible_match",
                    category="UNVERIFIED_SOURCE",
                    label=f"Possible Related Fact-Check: '{rating}' by {publisher} (Requires Review)",
                    label_hi=f"संभावित संबंधित तथ्य-जांच: '{rating}' by {publisher} (समीक्षा आवश्यक)",
                    description=f"Found a potentially related claim investigated by {publisher}: '{candidate_text[:120]}...'. Check the review link to determine if it addresses your specific question.",
                    description_hi=f"{publisher} द्वारा जांची गई एक संभावित संबंधित रिपोर्ट मिली: '{candidate_text[:120]}...'। पुष्टि के लिए लिंक देखें।",
                    severity="WARNING"
                )
            ]
            return ProviderCheckResponse(
                provider_status=ProviderStatus(
                    name=self.name,
                    configured=True,
                    status="POSSIBLE_MATCH",
                    details=f"Partial match found ({round(best_score*100)}% overlap). Requires manual verification by the user."
                ),
                signals=signals,
                additional_score=20,
                matched_data={
                    "publisher": publisher,
                    "rating": rating,
                    "review_url": review_url,
                    "review_date": review_date,
                    "reviewed_claim": candidate_text,
                    "match_confidence": "POSSIBLE"
                }
            )

        except requests.exceptions.Timeout:
            logger.warning("Fact Check API request timed out (3s threshold).")
            return ProviderCheckResponse(
                provider_status=ProviderStatus(
                    name=self.name,
                    configured=True,
                    status="TIMEOUT",
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

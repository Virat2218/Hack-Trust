from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
SignalSeverity = Literal["INFO", "WARNING", "CRITICAL"]
SignalCategory = Literal[
    "URGENCY",
    "IMPERSONATION",
    "CREDENTIAL_HARVEST",
    "FINANCIAL",
    "DOMAIN_ANOMALY",
    "UNVERIFIED_SOURCE"
]
ProviderExecutionStatus = Literal[
    "ACTIVE",
    "NOT_CONFIGURED",
    "CONSENT_WITHHELD",
    "NO_MATCH",
    "POSSIBLE_MATCH",
    "MATCH_FOUND",
    "VERIFIED_MATCH",
    "TIMEOUT",
    "ERROR",
    "SKIPPED"
]

class AnalysisSignal(BaseModel):
    id: str
    category: SignalCategory
    label: str
    label_hi: str
    description: str
    description_hi: str
    severity: SignalSeverity

class ProviderStatus(BaseModel):
    name: str
    configured: bool
    status: ProviderExecutionStatus
    details: Optional[str] = None

class EvidenceItem(BaseModel):
    source_name: str
    status: ProviderExecutionStatus
    checked_target: str
    details: str
    details_hi: Optional[str] = None
    reviewed_claim: Optional[str] = None
    publisher: Optional[str] = None
    review_url: Optional[str] = None
    review_date: Optional[str] = None
    textual_rating: Optional[str] = None
    match_confidence: Optional[Literal["STRONG_OVERLAP", "POSSIBLE_OVERLAP", "NONE", "EXACT", "POSSIBLE"]] = None

class AnalysisResult(BaseModel):
    analysis_type: Literal["MESSAGE", "URL", "CLAIM"]
    risk_level: RiskLevel
    # Transparent indicator counts
    critical_signals_count: int = 0
    warning_signals_count: int = 0
    info_signals_count: int = 0
    summary: str
    summary_hi: str
    signals: List[AnalysisSignal] = []
    evidence: List[EvidenceItem] = []
    provider_statuses: List[ProviderStatus] = []
    uncertainty_notes: List[str] = []
    uncertainty_notes_hi: List[str] = []
    recommended_actions: List[str] = []
    recommended_actions_hi: List[str] = []
    timestamp: str

# Request Schemas
class MessageAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=4000)
    language: Optional[str] = "en"

    @field_validator("text")
    @classmethod
    def validate_message_text(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 10:
            raise ValueError("Message must contain at least 10 non-whitespace characters.")
        return trimmed

class UrlAnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=3, max_length=1000)
    language: Optional[str] = "en"
    allow_external_lookup: bool = Field(
        default=False,
        description="Explicit user consent to query external reputation provider (Google Safe Browsing)."
    )

    @field_validator("url")
    @classmethod
    def validate_url_string(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 3:
            raise ValueError("URL must contain at least 3 characters.")
        return trimmed

class ClaimAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=1000)
    language: Optional[str] = "en"
    allow_external_lookup: bool = Field(
        default=False,
        description="Explicit user consent to query external fact-checking provider (Google Fact Check Tools)."
    )

    @field_validator("text")
    @classmethod
    def validate_claim_text(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 10:
            raise ValueError("Claim must contain at least 10 non-whitespace characters.")
        return trimmed

class HealthResponse(BaseModel):
    status: str
    version: str
    providers: dict

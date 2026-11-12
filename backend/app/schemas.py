from typing import List, Optional, Literal
from pydantic import BaseModel, Field

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
ProviderExecutionStatus = Literal["ACTIVE", "NOT_CONFIGURED", "ERROR", "SKIPPED"]

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

class AnalysisResult(BaseModel):
    analysis_type: Literal["MESSAGE", "URL", "CLAIM"]
    risk_level: RiskLevel
    risk_score: int = Field(ge=0, le=100)
    summary: str
    summary_hi: str
    signals: List[AnalysisSignal] = []
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

class UrlAnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=3, max_length=1000)
    language: Optional[str] = "en"

class ClaimAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=1000)
    language: Optional[str] = "en"

class HealthResponse(BaseModel):
    status: str
    version: str
    providers: dict


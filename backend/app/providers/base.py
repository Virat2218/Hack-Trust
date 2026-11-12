from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.schemas import ProviderStatus, AnalysisSignal

class ProviderCheckResponse(BaseModel):
    provider_status: ProviderStatus
    signals: List[AnalysisSignal] = []
    additional_score: int = 0
    matched_data: Optional[Dict[str, Any]] = None

class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def check(self, target: str, **kwargs) -> ProviderCheckResponse:
        pass


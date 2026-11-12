import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    port: int = int(os.getenv("PORT", 8000))
    host: str = os.getenv("HOST", "127.0.0.1")
    safe_browsing_api_key: str = os.getenv("SAFE_BROWSING_API_KEY", "").strip()
    fact_check_api_key: str = os.getenv("FACT_CHECK_API_KEY", "").strip()
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "").strip()

settings = Settings()


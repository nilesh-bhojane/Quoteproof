import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load backend/.env
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)


class Settings:
    PROJECT_NAME: str = "QuoteProof AI API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Environment variables from backend/.env
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str

    # Firebase
    FIREBASE_PROJECT_ID: str
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None  # Only for local dev

    # OpenRouter
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"  # Default model

    # HubSpot OAuth
    HUBSPOT_CLIENT_ID: str
    HUBSPOT_CLIENT_SECRET: str
    HUBSPOT_REDIRECT_URI: str

    # App
    ENVIRONMENT: str = "development"
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000"

    # GCP
    GOOGLE_CLOUD_PROJECT: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    def get_firebase_credentials(self) -> dict:
        """
        Get Firebase credentials from file (local) or Secret Manager (production).
        """
        # Local development - use file
        if self.ENVIRONMENT == "development" and self.FIREBASE_CREDENTIALS_PATH:
            import json
            with open(self.FIREBASE_CREDENTIALS_PATH) as f:
                return json.load(f)

        # Production - use Secret Manager
        from src.core.secrets import get_secret_manager
        sm = get_secret_manager()
        return sm.get_json_secret("firebase-credentials")

    def get_cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()

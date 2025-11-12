"""Secret Manager integration for production secrets."""

import os
import json
from typing import Optional
from google.cloud import secretmanager
from functools import lru_cache


class SecretManager:
    """Handle secret retrieval from Google Cloud Secret Manager."""

    def __init__(self, project_id: Optional[str] = None):
        """Initialize Secret Manager client."""
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")

        self.client = secretmanager.SecretManagerServiceClient()

    @lru_cache(maxsize=32)
    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """
        Retrieve a secret from Secret Manager.

        Uses LRU cache to avoid repeated API calls.

        Args:
            secret_id: Name of the secret
            version: Version to retrieve (default: latest)

        Returns:
            Secret value as string
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"

        try:
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            raise RuntimeError(f"Failed to access secret {secret_id}: {e}")

    def get_json_secret(self, secret_id: str) -> dict:
        """Retrieve a secret and parse as JSON."""
        secret_value = self.get_secret(secret_id)
        return json.loads(secret_value)


# Singleton instance
_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    """Get or create Secret Manager singleton."""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager

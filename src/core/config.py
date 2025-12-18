# src/core/config.py
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    def __init__(self):
        # OpenAI Key
        self.OPENAI_API_KEY: str = self._get_required_env("OPENAI_API_KEY")
        
        # Database Keys
        self.QDRANT_URL: str = self._get_required_env("QDRANT_URL")
        self.QDRANT_API_KEY: str = self._get_required_env("QDRANT_API_KEY")
        self.NEON_DB_URL: str = self._get_required_env("NEON_DB_URL")
        self.API_KEY: str = self._get_required_env("API_KEY")

    def _get_required_env(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable '{key}' is not set.")
        return value

settings = Settings()
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Groq API key: fallback order groq_API -> GROQ_API_KEY -> None
    groq_api: str | None = None
    groq_api_key: str | None = None

    # Groq Model (default matches tested active model for the key)
    groq_model: str = "qwen/qwen3.8-27b"

    # Server config
    host: str = "127.0.0.1"
    port: int = 8000
    environment: str = "development"

    # Answer constraints
    min_answer_length: int = 2
    max_answer_length: int = 5000

    # API limits & timeouts
    groq_timeout_seconds: float = 35.0
    groq_max_retries: int = 2

    @property
    def api_key(self) -> str:
        """Get the Groq API key with case-insensitive fallback."""
        key = self.groq_api or self.groq_api_key or os.getenv("groq_API") or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError(
                "Groq API key not found. Please set 'groq_API' or 'GROQ_API_KEY' in your .env file."
            )
        return key.strip()


settings = Settings()

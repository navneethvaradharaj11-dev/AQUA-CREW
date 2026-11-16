"""
Application Configuration using pydantic-settings
"""
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    # Application details
    API_TITLE: str = "AQUA CREW Core API"
    API_DESCRIPTION: str = "Autonomous Water Leakage Detection and Fleet Management API"
    API_VERSION: str = "0.1.0"
    API_ENV: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"  # 'text' or 'json'

    # CORS configuration
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.strip().startswith("["):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Database configuration
    DATABASE_URL: str = "sqlite:///./aqua_crew_dev.db"

    # Simulation engine parameters
    SIMULATION_TICK_INTERVAL_MS: int = 1000
    SIMULATION_AUTO_START: bool = True

    # WebSocket settings
    WS_HEARTBEAT_INTERVAL_SECONDS: int = 15
    MAX_WS_CONNECTIONS: int = 100
    MAX_WS_PER_IP: int = 10

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: int = 120
    RATE_LIMIT_AUTH: int = 10

    # Zero-Trust Identity, Authentication & JWT Configuration (Task 13.6)
    JWT_SECRET_KEY: str = "aqua-crew-dev-insecure-secret-key-32-chars-min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "aqua-crew-auth"
    JWT_AUDIENCE: str = "aqua-crew-api"
    REQUIRE_AUTH: bool = False
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15

    # Advanced AI & LLM Provider Configuration (Task 13)
    AI_PROVIDER: str = "DETERMINISTIC"  # DETERMINISTIC, NVIDIA_NIM, OPENAI
    AI_BASE_URL: Union[str, None] = None
    AI_MODEL: str = "meta/llama-3.1-70b-instruct"
    AI_API_KEY: Union[str, None] = None
    AI_TIMEOUT: float = 30.0
    AI_MAX_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.2

    # Hardware & IoT Integration Readiness (Task 18)
    HARDWARE_ACTUATION_ENABLED: bool = False
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_BROKER_KEEPALIVE: int = 60
    MQTT_BROKER_USERNAME: Union[str, None] = None
    MQTT_BROKER_PASSWORD: Union[str, None] = None
    MQTT_CLIENT_ID: str = "aquacrew-backend-service"
    MQTT_USE_TLS: bool = False
    MQTT_TLS_CA_CERT: Union[str, None] = None
    MQTT_SIMULATION_MODE: bool = True
    IOT_TELEMETRY_RETENTION_DAYS: int = 30
    IOT_MAX_PAYLOAD_SIZE_BYTES: int = 65536
    IOT_RATE_LIMIT_PER_DEVICE_PER_MIN: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AQUA_",
        extra="ignore",
    )

    def validate_production_security(self) -> None:
        """
        Validates that production environment variables meet strict zero-trust criteria.
        Refuses to start in production with default secrets, SQLite, disabled auth, or wildcard CORS.
        """
        if self.API_ENV.lower() in ("production", "prod"):
            if self.JWT_SECRET_KEY == "aqua-crew-dev-insecure-secret-key-32-chars-min" or len(self.JWT_SECRET_KEY) < 32:
                raise RuntimeError("Production security error: Insecure or default JWT_SECRET_KEY detected in production.")
            if self.DATABASE_URL.startswith("sqlite"):
                raise RuntimeError("Production security error: SQLite database is prohibited in production.")
            if not self.REQUIRE_AUTH:
                raise RuntimeError("Production security error: REQUIRE_AUTH must be true in production.")
            if "*" in self.CORS_ORIGINS:
                raise RuntimeError("Production security error: Wildcard '*' CORS origin is strictly prohibited in production.")


settings = Settings()


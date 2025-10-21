from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/admin_db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Cerbos
    CERBOS_HOST: str = "localhost"
    CERBOS_PORT: int = 3592

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # API
    API_V1_PREFIX: str = "/api/v1"
    ADMIN_API_PORT: int = 8001

    # Legacy System
    LEGACY_DB_URL: str = ""
    LEGACY_SYNC_INTERVAL: int = 300  # seconds

    # Legacy MariaDB
    LEGACY_MARIADB_HOST: str = "10.253.215.60"
    LEGACY_MARIADB_PORT: int = 3333
    LEGACY_MARIADB_USER: str = "user"
    LEGACY_MARIADB_PASSWORD: str = "password"
    LEGACY_MARIADB_DATABASE: str = "legal_db"

    # Legacy Oracle
    LEGACY_ORACLE_HOST: str = "10.253.215.54"
    LEGACY_ORACLE_PORT: int = 1521
    LEGACY_ORACLE_USER: str = "user"
    LEGACY_ORACLE_PASSWORD: str = "password"
    LEGACY_ORACLE_SERVICE: str = "ORCL"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:10002"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "documents"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6335  # ex-gpt Qdrant port (maps to qdrant:6333 inside Docker)
    QDRANT_COLLECTION: str = "130825-512-v2"  # Main collection (must match ex-gpt-api)
    QDRANT_API_KEY: str = ""  # Optional

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8010",
        "https://ui.datastreams.co.kr:20443",
        "http://ui.datastreams.co.kr:20443",
        "https://ui.datastreams.co.kr",
        "http://ui.datastreams.co.kr"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

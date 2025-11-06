from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union, Optional


class Settings(BaseSettings):
    # Database (Admin Tool)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/admin_db"

    # User UI Health Check
    USER_UI_URL: str = "http://host.docker.internal:18180/exGenBotDS/testOld"
    USER_DB_URL: Optional[str] = None  # Optional: User UI Database

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

    # Internal Mail System Oracle DB (사내메일 연동용)
    MAIL_ORACLE_HOST: str = "172.16.164.32"
    MAIL_ORACLE_PORT: int = 1669
    MAIL_ORACLE_USER: str = "exgpt_user"
    MAIL_ORACLE_PASSWORD: str = "your_password_here"
    MAIL_ORACLE_SERVICE: str = "ANKHCG"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:10002"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "documents"

    # Qdrant
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333  # ex-gpt-qdrant-1 internal port (via exgpt_net)
    QDRANT_COLLECTION: str = "130825-512-v3"  # Main collection (must match ex-gpt-api)
    QDRANT_API_KEY: str = "QFy9YlRTm0Y1yo6D"  # API key

    # vLLM (AI Service)
    VLLM_API_URL: str = "http://localhost:8000/v1"  # vLLM OpenAI-compatible API
    VLLM_MODEL_NAME: str = "Qwen/Qwen3-32B-Instruct"  # Chat model
    EMBEDDING_API_URL: str = "http://localhost:8001/v1"  # Embedding model API

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

    # Chat Proxy Settings
    DS_API_URL: str = "http://host.docker.internal:18180/exGenBotDS"
    DS_API_KEY: str = "z3JE1M8huXmNux6y"
    CHAT_TIMEOUT: float = 120.0
    CHAT_DEFAULT_TEMPERATURE: float = 0.0
    CHAT_MODEL_NAME: str = "ex-GPT"
    TITLE_GEN_PREFIX: str = "title_gen_"
    DEFAULT_USER: str = "anonymous"
    CHAT_TITLE_MAX_LENGTH: int = 50

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_BACKEND_STORE_URI: str = "postgresql://postgres:password@localhost:5432/mlflow_db"
    MLFLOW_ARTIFACT_ROOT: str = "./mlartifacts"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

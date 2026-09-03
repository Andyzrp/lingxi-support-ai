from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 项目基础配置
    PROJECT_NAME: str = "灵犀智能客服"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "lingxi_secret_key_change_in_production"
    API_V1_STR: str = "/api/v1"

    # 上传文件目录（容器内默认挂载到 /app/uploads）
    UPLOAD_DIR: str = "./uploads"

    # PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Qdrant
    QDRANT_HOST: str = "10.99.216.94"
    QDRANT_PORT: int = 6333

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # 大模型配置
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_MODEL: str = "deepseek-v3.2-chat-private"
    LLM_MODEL_STRONG: str = "deepseek-v3.2-private"

    # Embedding模型
    EMBEDDING_HOST: str = "10.99.216.94"
    EMBEDDING_PORT: int = 8001

    @property
    def EMBEDDING_URL(self) -> str:
        return f"http://{self.EMBEDDING_HOST}:{self.EMBEDDING_PORT}"

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # 会话配置
    SESSION_TIMEOUT: int = 300
    EVAL_PUSH_DELAY: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()
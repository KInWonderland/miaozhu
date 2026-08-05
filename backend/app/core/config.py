from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Database (SQLite, stored in data/)
    DATABASE_URL: str = "sqlite+aiosqlite:///data/miaozhu.db"

    # CORS
    CORS_ORIGINS: str = '["http://localhost:5173"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    # Scheduler
    SCHEDULER_POLL_INTERVAL: int = 5       # 轮询间隔（秒）
    SCHEDULER_MAX_CONCURRENT_LLM: int = 5  # 最大并发 LLM 调用数
    SCHEDULER_MAX_CONCURRENT_EXPORT: int = 4  # 最大并发导出数

    # LLM (OpenAI-compatible)
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"

    # Export data directory
    EXPORT_DATA_DIR: str = "data/exports"

    # Session login. These values are supplied through the deployment
    # environment, never hard-coded into an image or source file.
    AUTH_USERNAME: str = ""
    AUTH_PASSWORD: str = ""
    SESSION_SECRET: str = ""
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 7
    # Keep this false for local HTTP development. HTTPS production deployments
    # must set it to true so browsers never send a session over plain HTTP.
    SESSION_HTTPS_ONLY: bool = False

    def validate_auth_configuration(self) -> None:
        missing = [
            name
            for name, value in (
                ("AUTH_USERNAME", self.AUTH_USERNAME),
                ("AUTH_PASSWORD", self.AUTH_PASSWORD),
                ("SESSION_SECRET", self.SESSION_SECRET),
            )
            if not value.strip()
        ]
        if missing:
            raise RuntimeError(
                "登录功能尚未配置，请在环境变量中设置：" + ", ".join(missing)
            )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

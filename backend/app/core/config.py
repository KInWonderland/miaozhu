import logging
import os
from pathlib import Path
from threading import RLock
from typing import List
import json

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


logger = logging.getLogger(__name__)

# Allow a deployment to provide an alternate file, while keeping the existing
# `backend/.env` behaviour for local development and containers.
ENV_FILE = Path(os.environ.get("MIAOZHU_ENV_FILE", ".env"))


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

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Prefer the file so editing it can update container configuration too.

        Docker Compose's ``env_file`` copies values into the process environment
        at container creation.  The default Pydantic source order would keep
        those stale process values ahead of a subsequently edited ``.env``.
        """
        return init_settings, dotenv_settings, env_settings, file_secret_settings


class ReloadableSettings:
    """A lazy settings proxy that reloads a changed dotenv file atomically."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._current: Settings | None = None
        self._fingerprint: tuple[int, int, int] | None = None

    @staticmethod
    def _file_fingerprint() -> tuple[int, int, int] | None:
        try:
            stat = ENV_FILE.stat()
        except FileNotFoundError:
            return None
        return stat.st_ino, stat.st_size, stat.st_mtime_ns

    def get(self) -> Settings:
        """Return the latest valid settings, retaining the last valid version.

        An editor may briefly leave a file incomplete while saving it.  In that
        case, running work continues with the last valid configuration and an
        error is logged until the file is fixed.
        """
        fingerprint = self._file_fingerprint()
        with self._lock:
            if self._current is not None and fingerprint == self._fingerprint:
                return self._current

            try:
                updated = Settings()
            except Exception:
                if self._current is None:
                    raise
                logger.exception(
                    "Ignoring invalid configuration reload from %s; retaining the last valid settings",
                    ENV_FILE,
                )
                self._fingerprint = fingerprint
                return self._current

            self._current = updated
            self._fingerprint = fingerprint
            logger.info("Configuration loaded from %s", ENV_FILE)
            return updated

    def __getattr__(self, name: str):
        return getattr(self.get(), name)


settings = ReloadableSettings()

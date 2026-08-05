import asyncio
import logging
import logging.handlers
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware


def _setup_logging():
    """Configure logging to both console and file."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (gunicorn captures this)
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    # File handler — write to logs/app.log next to the running app
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    fh = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)


_setup_logging()
logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import applications, auth, dashboard, generation, exports, sse
from app.middleware import SessionAuthenticationMiddleware
from app.services.generation.scheduler import run_scheduler
from app.services.export.scheduler import run_export_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 自动建表（替代 Alembic 迁移）
    await init_db()
    logger.info("Database initialized")

    # 启动后台调度器
    scheduler_task = asyncio.create_task(run_scheduler())
    export_scheduler_task = asyncio.create_task(run_export_scheduler())
    logger.info("Generation scheduler task created")
    logger.info("Export scheduler task created")
    yield
    # 关闭时取消调度器
    scheduler_task.cancel()
    export_scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    logger.info("Generation scheduler stopped")


def create_app() -> FastAPI:
    settings.validate_auth_configuration()

    app = FastAPI(
        title="秒著 API",
        description="AI 辅助生成软件著作权申请材料",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware is added inside-out: CORS wraps SessionMiddleware, which wraps
    # the authentication guard. This lets preflight requests receive CORS
    # headers while allowing the guard to read the decoded signed session.
    app.add_middleware(SessionAuthenticationMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        same_site="lax",
        https_only=settings.SESSION_HTTPS_ONLY,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    prefix = "/api/v1"
    app.include_router(auth.router, prefix=prefix)
    app.include_router(applications.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    app.include_router(generation.router, prefix=prefix)
    app.include_router(exports.router, prefix=prefix)
    app.include_router(sse.router, prefix=prefix)

    # Unified error response with code field
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "detail": exc.detail},
        )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()

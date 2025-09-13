"""
Main Web Service for CodeBuddy2API
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the routers
from src.codebuddy_router import router as codebuddy_router
from src.codebuddy_auth_router import router as codebuddy_auth_router
from src.settings_router import router as settings_router
from src.frontend_router import router as frontend_router
from src.health_router import router as health_router

from config import get_server_host, get_server_port, get_log_level

# 配置日志
logging.basicConfig(
    level=getattr(logging, get_log_level().upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting CodeBuddy2API Service")
    yield
    logger.info("CodeBuddy2API Service stopped")


# 创建FastAPI应用
app = FastAPI(
    title="CodeBuddy2API",
    description="CodeBuddy API proxy with OpenAI-compatible interface",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端路由
app.include_router(
    frontend_router,
    tags=["Frontend"]
)

# 挂载CodeBuddy认证路由
app.include_router(
    codebuddy_auth_router,
    prefix="/codebuddy",
    tags=["CodeBuddy OAuth2 Authentication"]
)

# 挂载CodeBuddy API路由
app.include_router(
    codebuddy_router,
    prefix="/codebuddy",
    tags=["CodeBuddy Compatible API"]
)

# 挂载设置路由
app.include_router(
    settings_router,
    prefix="/api",
    tags=["Settings Management"]
)

# 挂载健康检查路由
app.include_router(
    health_router,
    prefix="/api",
    tags=["Health Check"]
)


@app.get("/")
async def root():
    """根路径信息"""
    return {
        "service": "CodeBuddy2API",
        "version": "1.0.0",
        "description": "CodeBuddy API proxy with OpenAI-compatible interface",
        "endpoints": {
            "models": "/codebuddy/v1/models",
            "chat": "/codebuddy/v1/chat/completions",
            "credentials": "/codebuddy/v1/credentials",
            "auth_start": "/codebuddy/auth/start",
            "auth_poll": "/codebuddy/auth/poll",
            "auth_callback": "/codebuddy/auth/callback",
            "get_settings": "/api/settings",
            "save_settings": "/api/settings"
        }
    }


if __name__ == "__main__":
    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    
    port = get_server_port()
    host = get_server_host()
    
    logger.info("=" * 60)
    logger.info("Starting CodeBuddy2API")
    logger.info("=" * 60)
    logger.info(f"Main Service: http://{host}:{port}")
    logger.info("=" * 60)
    logger.info("Web Interface:")
    logger.info(f"   Admin Panel: http://{host}:{port}/")
    logger.info("=" * 60)
    logger.info("API Endpoints:")
    logger.info(f"   Models: GET http://{host}:{port}/codebuddy/v1/models")
    logger.info(f"   Chat: POST http://{host}:{port}/codebuddy/v1/chat/completions")
    logger.info(f"   Credentials: GET http://{host}:{port}/codebuddy/v1/credentials")
    logger.info("=" * 60)
    logger.info("Authentication:")
    logger.info("   Set CODEBUDDY_PASSWORD environment variable")
    logger.info("   Use Bearer token in Authorization header")
    logger.info("=" * 60)

    config = Config()
    config.bind = [f"{host}:{port}"]
    config.accesslog = None
    config.errorlog = "-"
    config.loglevel = "INFO"
    config.use_colors = True

    asyncio.run(serve(app, config))
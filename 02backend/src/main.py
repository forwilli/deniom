"""
FastAPI 应用工厂
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core import settings, database
from .features.projects.router import router as projects_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    database.init_db()
    print(f"✅ {settings.APP_NAME} 启动成功！")
    yield
    print(f"👋 {settings.APP_NAME} 正在关闭...")

def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册健康检查端点
    @app.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok"}

    # 注册功能模块路由
    app.include_router(projects_router, prefix=settings.API_V1_STR, tags=["Projects"])

    return app 
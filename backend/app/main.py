"""FastAPI 应用入口"""
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.core.database import init_db
from app.core.logger import setup_logging, get_logger, LOG_DIR
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router

settings = get_settings()
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    await init_db()
    logger.info("Database initialized")
    logger.info(f"API docs: http://{settings.backend_host}:{settings.backend_port}/docs")
    logger.info(f"Logs directory: {LOG_DIR}")
    yield
    logger.info("Server shutdown")


app = FastAPI(
    title="RAG 企业级知识库问答系统",
    description="基于 LangChain + 阿里云百炼的电商商品知识库问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({elapsed:.3f}s)"
    )
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# 注册路由
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(knowledge_router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "rag-kb-api"}

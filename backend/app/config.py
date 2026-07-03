"""应用配置管理"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # 阿里云百炼
    dashscope_api_key: str = ""
    llm_model: str = "qwen-plus"
    embedding_model: str = "text-embedding-v3"

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # JWT
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 服务
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Chroma
    chroma_persist_dir: str = "./data/chroma"

    # 上传
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 50

    # 算法
    algorithm: str = "HS256"

    # 压力测试
    stress_test_mock_llm: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()

"""测试 config.py — 应用配置管理"""
import pytest
from app.config import Settings, get_settings


class TestSettings:
    """配置类测试"""

    def test_default_values(self):
        """默认值应该正确设置"""
        settings = Settings()
        assert settings.llm_model == "qwen-plus"
        assert settings.embedding_model == "text-embedding-v3"
        assert settings.access_token_expire_minutes == 30
        assert settings.refresh_token_expire_days == 7
        assert settings.backend_port == 8000
        assert settings.max_upload_size_mb == 50
        assert settings.algorithm == "HS256"

    def test_default_chroma_dir(self):
        """Chroma 持久化目录默认值"""
        settings = Settings()
        assert settings.chroma_persist_dir == "./data/chroma"

    def test_default_upload_dir(self):
        """上传目录默认值"""
        settings = Settings()
        assert settings.upload_dir == "./data/uploads"

    def test_default_database_url(self):
        """数据库 URL 默认值"""
        settings = Settings()
        assert "sqlite" in settings.database_url
        assert "aiosqlite" in settings.database_url

    def test_get_settings_singleton(self):
        """get_settings() 应该返回单例（lru_cache）"""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_settings_model_config_has_env_file(self):
        """Settings 应该配置了 .env 文件读取"""
        settings = Settings()
        assert settings.model_config.get("env_file") == ".env"


class TestSettingsOverride:
    """配置覆盖测试"""

    def test_override_via_constructor(self):
        """通过构造函数覆盖默认值"""
        settings = Settings(llm_model="qwen-max", backend_port=9999)
        assert settings.llm_model == "qwen-max"
        assert settings.backend_port == 9999

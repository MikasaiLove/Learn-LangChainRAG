"""pytest 配置文件 — 共享 fixtures"""
import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环（session 级别）"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

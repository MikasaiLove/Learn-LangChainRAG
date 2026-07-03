"""应用日志配置"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
MAX_BYTES = 10 * 1024 * 1024  # 10MB per file
BACKUP_COUNT = 5  # Keep 5 old log files


def setup_logging() -> logging.Logger:
    """配置日志：同时输出到文件和终端"""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("rag-kb")
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 格式
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件 handler（自动轮转）
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # 终端 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "rag-kb") -> logging.Logger:
    """获取 logger 实例"""
    return logging.getLogger(name)

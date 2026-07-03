"""
LangChainRAG 压力测试 — Locust 入口
=====================================

运行方式:
  # Phase 1: Health Check 基准吞吐
  set LOCUST_PHASE=health
  locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 2m --host http://localhost:8000 --csv reports/phase1

  # Phase 2: 认证 + 会话列表
  set LOCUST_PHASE=auth
  locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 3m --host http://localhost:8000 --csv reports/phase2

  # Phase 3: 知识库管理
  set LOCUST_PHASE=kb
  locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 2m --host http://localhost:8000 --csv reports/phase3

  # Phase 4: RAG 对话 (Mock LLM)
  set LOCUST_PHASE=chat
  locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m --host http://localhost:8000 --csv reports/phase4

  # Phase 5: 真实 LLM (少量 VU)
  set LOCUST_PHASE=chat_real
  locust -f locustfile.py --headless --users 5 --spawn-rate 2 --run-time 2m --host http://localhost:8000 --csv reports/phase5

  # Web UI 模式（手动选择）
  locust -f locustfile.py --host http://localhost:8000

环境变量:
  LOCUST_PHASE = health | auth | kb | chat | chat_real
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import metrics  # noqa: F401

phase = os.getenv("LOCUST_PHASE", "").lower()

if phase == "health":
    from scenarios.health import HealthCheckUser  # noqa: F401
elif phase == "auth":
    from scenarios.auth import AuthUser  # noqa: F401
elif phase == "kb":
    from scenarios.kb_admin import KBAdminUser  # noqa: F401
elif phase == "chat":
    from scenarios.chat_heavy import ChatHeavyUser  # noqa: F401
elif phase == "chat_real":
    from scenarios.chat_real import ChatRealLLMUser  # noqa: F401
else:
    # Web UI mode — import all
    from scenarios.health import HealthCheckUser        # noqa: F401
    from scenarios.auth import AuthUser                 # noqa: F401
    from scenarios.kb_admin import KBAdminUser          # noqa: F401
    from scenarios.chat_heavy import ChatHeavyUser      # noqa: F401
    from scenarios.chat_real import ChatRealLLMUser     # noqa: F401

"""Phase 4: RAG Chat Heavy — 发送消息 + 重新生成 (Mock LLM)"""

import json
import os
from locust import HttpUser, task, between, tag
from helpers.auth_helper import get_auth_headers, get_token
from helpers.sse_client import stream_send_message


class ChatHeavyUser(HttpUser):
    """模拟 RAG 对话操作 — 发消息 + 重新生成"""

    wait_time = between(3, 10)  # 模拟用户思考时间

    def on_start(self):
        """初始化：登录 + 加载预创建会话"""
        self.username = f"testuser_{self._get_vu_index():03d}"
        self.host_url = self.host
        self.session_ids = self._load_sessions()
        self.current_session_idx = 0

    def _get_vu_index(self):
        try:
            runner = self.environment.runner
            if runner:
                return (runner.user_count % 100) + 1
        except Exception:
            pass
        return 1

    def _load_sessions(self):
        try:
            cred_file = os.path.join(os.path.dirname(__file__), "..", "test_data.json")
            with open(cred_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("sessions", {}).get(self.username, [])
        except Exception:
            return []

    def _get_session_id(self):
        """轮转使用 3 个预创建会话"""
        if not self.session_ids:
            return None
        sid = self.session_ids[self.current_session_idx % len(self.session_ids)]
        self.current_session_idx += 1
        return sid

    @task(5)
    @tag("chat_heavy")
    def send_message(self):
        """发送聊天消息 — SSE 流式 (Mock LLM)"""
        session_id = self._get_session_id()
        if not session_id:
            return

        token = get_token(self.client, self.host_url, self.username)
        if not token:
            return

        headers = {"Authorization": f"Bearer {token}"}
        questions = [
            "这个产品有什么特点？",
            "价格是多少？",
            "跟竞品比起来怎么样？",
            "有什么优惠活动吗？",
            "售后政策是什么？",
        ]
        question = questions[self.current_session_idx % len(questions)]

        # 使用自定义 SSE 客户端（记录 TTFT 等指标）
        stream_send_message(
            self.client,
            f"{self.host_url}/api/chat/sessions/{session_id}/send",
            headers,
            {"content": question},
            {"request_type": "SSE", "name": "POST /api/chat/sessions/{id}/send"},
        )

    @task(1)
    @tag("chat_heavy")
    def regenerate(self):
        """重新生成最后一条回答"""
        session_id = self._get_session_id()
        if not session_id:
            return

        token = get_token(self.client, self.host_url, self.username)
        if not token:
            return

        headers = {"Authorization": f"Bearer {token}"}
        stream_send_message(
            self.client,
            f"{self.host_url}/api/chat/sessions/{session_id}/regenerate",
            headers,
            {},
            {"request_type": "SSE", "name": "POST /api/chat/sessions/{id}/regenerate"},
        )

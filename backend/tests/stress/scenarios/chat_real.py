"""Phase 5: Real LLM — 限流验证 (少量 VU)"""

from locust import HttpUser, task, between, tag
from helpers.auth_helper import get_auth_headers
from helpers.sse_client import stream_send_message


class ChatRealLLMUser(HttpUser):
    """少量 VU 验证真实 DashScope API 稳定性"""

    wait_time = between(5, 10)

    def on_start(self):
        self.username = "testuser_001"
        self.host_url = self.host

        # 登录
        resp = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "123456"},
        )
        if resp.status_code == 200:
            self.token = resp.json()["access_token"]
            self.session_id = self._create_session()
        else:
            self.token = None
            self.session_id = None

    def _create_session(self):
        """创建新会话"""
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = self.client.post(
            "/api/chat/sessions",
            json={"title": "真实LLM压测"},
            headers=headers,
        )
        if resp.status_code == 200:
            return resp.json().get("id")
        return None

    @task
    @tag("chat_real")
    def send_real_message(self):
        """发送真实 LLM 调用（⚠️ 花钱！）"""
        if not self.token or not self.session_id:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        stream_send_message(
            self.client,
            f"{self.host_url}/api/chat/sessions/{self.session_id}/send",
            headers,
            {"content": "简单介绍一下你的商品"},
            {"request_type": "SSE_REAL", "name": "POST /api/chat/sessions/{id}/send (REAL LLM)"},
        )

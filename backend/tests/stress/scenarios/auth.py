"""Phase 2: Auth — 登录、会话列表、消息获取"""

import json
import os
from locust import HttpUser, task, between, tag
from helpers.auth_helper import get_auth_headers


class AuthUser(HttpUser):
    """模拟认证相关操作：登录 + 会话列表 + 消息获取"""

    wait_time = between(1, 3)

    def on_start(self):
        """每个 VU 启动时登录一次"""
        self.username = f"testuser_{self._get_vu_index():03d}"
        self.host_url = self.host
        self.session_ids = self._load_sessions()

    def _get_vu_index(self):
        """根据 worker 分配固定用户名"""
        try:
            runner = self.environment.runner
            if runner:
                return (runner.user_count % 100) + 1
        except Exception:
            pass
        return 1

    def _load_sessions(self):
        """从 test_data.json 加载预创建的会话 ID"""
        try:
            cred_file = os.path.join(os.path.dirname(__file__), "..", "test_data.json")
            with open(cred_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("sessions", {}).get(self.username, [])
        except Exception:
            return []

    @task(3)
    @tag("auth")
    def login(self):
        """登录请求 — 测试 bcrypt 瓶颈"""
        with self.client.post(
            "/api/auth/login",
            json={"username": self.username, "password": "Test@123456"},
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                # 缓存 token（避免每次都重新 login）
                from helpers.auth_helper import TOKEN_CACHE
                TOKEN_CACHE[self.username] = {
                    "access_token": data["access_token"],
                    "refresh_token": data["refresh_token"],
                    "expires_at": __import__("time").time() + 25 * 60,
                }
            elif resp.status_code == 401:
                # 用户不存在也正常，用默认凭据
                pass
            else:
                resp.failure(f"Login failed: {resp.status_code}")

    @task(5)
    @tag("auth")
    def list_sessions(self):
        """获取会话列表 — 测试 SQLite 读 + JWT 解码"""
        headers = get_auth_headers(self.client, self.host_url, self.username)
        if not headers:
            return

        with self.client.get(
            "/api/chat/sessions?page=1&size=20",
            headers=headers,
            catch_response=True,
        ) as resp:
            if resp.status_code == 401:
                # Token 过期，重新登录
                from helpers.auth_helper import TOKEN_CACHE
                TOKEN_CACHE.pop(self.username, None)
            elif resp.status_code != 200:
                resp.failure(f"List sessions failed: {resp.status_code}")

    @task(2)
    @tag("auth")
    def get_messages(self):
        """获取历史消息 — 测试 JOIN 查询"""
        if not self.session_ids:
            return

        headers = get_auth_headers(self.client, self.host_url, self.username)
        if not headers:
            return

        session_id = self.session_ids[0]
        with self.client.get(
            f"/api/chat/sessions/{session_id}/messages?page=1&size=50",
            headers=headers,
            catch_response=True,
        ) as resp:
            if resp.status_code not in (200, 401):
                resp.failure(f"Get messages failed: {resp.status_code}")

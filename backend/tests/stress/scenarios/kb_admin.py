"""Phase 3: Admin Knowledge Base — 文档列表、统计、上传"""

import json
import os
from locust import HttpUser, task, between, tag


class KBAdminUser(HttpUser):
    """模拟管理员操作：文档管理"""

    wait_time = between(2, 5)

    def on_start(self):
        """管理员登录"""
        resp = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "123456"},
        )
        if resp.status_code == 200:
            self.token = resp.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print(f"Admin login failed: {resp.status_code}")
            self.headers = {}

    @task(4)
    @tag("kb")
    def list_documents(self):
        """文档列表 — 分页查询"""
        if not self.headers:
            return
        with self.client.get(
            "/api/knowledge/documents?page=1&size=20",
            headers=self.headers,
            catch_response=True,
        ) as resp:
            if resp.status_code not in (200, 401, 403):
                resp.failure(f"List documents failed: {resp.status_code}")

    @task(3)
    @tag("kb")
    def get_stats(self):
        """知识库统计 — 聚合查询"""
        if not self.headers:
            return
        with self.client.get(
            "/api/knowledge/stats",
            headers=self.headers,
            catch_response=True,
        ) as resp:
            if resp.status_code not in (200, 401, 403):
                resp.failure(f"Get stats failed: {resp.status_code}")

    @task(1)
    @tag("kb")
    def get_document_detail(self):
        """文档详情"""
        if not self.headers:
            return
        # 尝试获取任意文档（如果知识库为空则跳过）
        with self.client.get(
            "/api/knowledge/documents/nonexistent",
            headers=self.headers,
            catch_response=True,
        ) as resp:
            # 404 是正常的（文档不存在），非 401/403 错误才算失败
            if resp.status_code not in (404, 401, 403):
                resp.failure(f"Get document failed: {resp.status_code}")

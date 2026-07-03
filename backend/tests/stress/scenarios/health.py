"""Phase 1: Health Check — 基准吞吐测试"""

from locust import HttpUser, task, between, tag


class HealthCheckUser(HttpUser):
    """模拟无认证的 Health check 请求洪流"""
    wait_time = between(0.1, 0.5)  # 高频请求

    @task
    @tag("health")
    def health_check(self):
        with self.client.get("/health", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Health check returned {resp.status_code}")

"""Locust 认证辅助 — Token 缓存与自动刷新"""

import json
import os
import time
import httpx

TOKEN_CACHE = {}          # username -> {access_token, refresh_token, expires_at}
CREDENTIALS = {}          # 从 test_data.json 加载的用户凭据
CREDENTIALS_LOADED = False


def load_credentials():
    """加载 test_data.json 中的用户凭据"""
    global CREDENTIALS, CREDENTIALS_LOADED
    if CREDENTIALS_LOADED:
        return

    cred_file = os.path.join(os.path.dirname(__file__), "..", "test_data.json")
    if os.path.exists(cred_file):
        with open(cred_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for u in data["users"]:
                CREDENTIALS[u["username"]] = u
    CREDENTIALS_LOADED = True


def login(client: httpx.Client, host: str, username: str, password: str) -> dict | None:
    """登录并返回 token 信息"""
    try:
        resp = client.post(
            f"{host}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            body = resp.json()
            return {
                "access_token": body["access_token"],
                "refresh_token": body["refresh_token"],
                "expires_at": time.time() + 25 * 60,  # 25分钟（access token 30分钟）
            }
        print(f"Login failed for {username}: {resp.status_code} {resp.text}")
        return None
    except Exception as e:
        print(f"Login exception for {username}: {e}")
        return None


def get_token(client: httpx.Client, host: str, username: str) -> str | None:
    """获取有效 token，必要时登录或刷新"""
    load_credentials()

    # 检查缓存
    cached = TOKEN_CACHE.get(username)
    if cached and time.time() < cached["expires_at"]:
        return cached["access_token"]

    # 获取凭据
    cred = CREDENTIALS.get(username)
    if not cred:
        # 使用默认 admin
        cred = {"username": username, "password": "123456"}

    # 登录
    result = login(client, host, cred["username"], cred["password"])
    if result:
        TOKEN_CACHE[username] = result
        return result["access_token"]

    return None


def get_auth_headers(client: httpx.Client, host: str, username: str) -> dict:
    """获取带有 Authorization 的 headers"""
    token = get_token(client, host, username)
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

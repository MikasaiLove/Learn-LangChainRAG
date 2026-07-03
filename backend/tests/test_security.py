"""测试 core/security.py — JWT 和密码安全"""
import pytest
import time
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestPasswordHashing:
    """密码哈希和验证测试"""

    def test_hash_and_verify_correct_password(self):
        """正常情况：正确密码应该验证通过"""
        password = "test123456"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password_fails(self):
        """错误密码应该验证失败"""
        password = "correct_password"
        hashed = hash_password(password)
        assert verify_password("wrong_password", hashed) is False

    def test_hash_produces_different_salt_each_time(self):
        """每次哈希应该产生不同的结果（随机盐）"""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_hash_output_is_string(self):
        """哈希结果应该是字符串"""
        hashed = hash_password("hello123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_empty_password_handling(self):
        """边界情况：空密码也能处理"""
        hashed = hash_password("")
        assert isinstance(hashed, str)
        assert verify_password("", hashed) is True

    def test_long_password_handling(self):
        """边界情况：长密码（小于72字节）正常处理"""
        long_pw = "a" * 60  # 60 chars, well within bcrypt 72-byte limit
        hashed = hash_password(long_pw)
        assert verify_password(long_pw, hashed) is True

    def test_special_chars_password(self):
        """特殊字符密码正确处理"""
        password = "p@ss!中文#テスト$%^&*()"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """JWT Token 创建和验证测试"""

    def test_create_and_decode_access_token(self):
        """正常情况：创建的 Access Token 能被正确解码"""
        token = create_access_token("user-123", "user")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["role"] == "user"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload

    def test_create_and_decode_refresh_token(self):
        """正常情况：创建的 Refresh Token 能被正确解码"""
        token = create_refresh_token("user-456", "admin")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["role"] == "admin"
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload

    def test_decode_invalid_token_returns_none(self):
        """无效 Token 应该返回 None"""
        result = decode_token("this.is.not.a.valid.jwt.token")
        assert result is None

    def test_decode_empty_string_returns_none(self):
        """空字符串应该返回 None"""
        result = decode_token("")
        assert result is None

    def test_access_token_has_short_expiry(self):
        """Access Token 过期时间应该较短（默认30分钟）"""
        token = create_access_token("user-789", "user")
        payload = decode_token(token)
        now = int(time.time())
        # Access token should expire within ~31 minutes
        assert payload["exp"] > now
        assert payload["exp"] <= now + 31 * 60

    def test_refresh_token_has_long_expiry(self):
        """Refresh Token 过期时间应该较长（默认7天）"""
        token = create_refresh_token("user-abc", "user")
        payload = decode_token(token)
        now = int(time.time())
        # Refresh token should expire within ~7 days + buffer
        assert payload["exp"] > now
        assert payload["exp"] <= now + 7 * 24 * 3600 + 60

    def test_tokens_have_unique_jti(self):
        """每次创建的 Token 应有唯一的 jti"""
        token1 = create_access_token("user-1", "user")
        token2 = create_access_token("user-1", "user")
        payload1 = decode_token(token1)
        payload2 = decode_token(token2)
        assert payload1["jti"] != payload2["jti"]

    def test_tokens_different_types(self):
        """Access Token 和 Refresh Token 应有不同的 type"""
        access = create_access_token("user-x", "user")
        refresh = create_refresh_token("user-x", "user")
        assert decode_token(access)["type"] == "access"
        assert decode_token(refresh)["type"] == "refresh"

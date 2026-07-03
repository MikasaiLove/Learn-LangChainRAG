"""认证业务逻辑"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.document import RevokedToken
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


async def register_user(db: AsyncSession, username: str, password: str) -> tuple[User | None, str | None]:
    """注册新用户，返回 (用户, 错误消息)"""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        return None, "用户名已存在"

    user = User(
        username=username,
        password_hash=hash_password(password),
        role="user",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user, None


async def login_user(db: AsyncSession, username: str, password: str) -> tuple[User | None, str | None]:
    """用户登录，返回 (用户, 错误消息)"""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        return None, "用户名或密码错误"
    if not verify_password(password, user.password_hash):
        return None, "用户名或密码错误"
    return user, None


def create_tokens(user: User) -> dict:
    """为用户创建双Token"""
    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id, user.role),
    }


async def revoke_token(db: AsyncSession, token: str):
    """将 Refresh Token 加入黑名单"""
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        return

    from datetime import datetime, timezone
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        expire_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
        if expire_dt > datetime.now(timezone.utc):
            revoked = RevokedToken(jti=jti, expires_at=expire_dt)
            db.add(revoked)
            await db.flush()


async def is_token_revoked(db: AsyncSession, jti: str) -> bool:
    """检查 Token 是否已被撤销"""
    result = await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
    return result.scalar_one_or_none() is not None


async def change_user_password(db: AsyncSession, user: User, old_password: str, new_password: str) -> str | None:
    """修改密码，返回错误消息或 None"""
    if not verify_password(old_password, user.password_hash):
        return "旧密码不正确"
    user.password_hash = hash_password(new_password)
    await db.flush()
    return None


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """根据ID获取用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

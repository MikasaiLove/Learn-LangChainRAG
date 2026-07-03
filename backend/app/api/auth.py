"""认证 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserRegister, UserLogin, ChangePassword,
    AuthResponse, TokenResponse, RefreshTokenRequest,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=AuthResponse)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    user, error = await auth_service.register_user(db, body.username, body.password)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    tokens = auth_service.create_tokens(user)
    return AuthResponse(
        user=UserResponse(**user.to_dict()),
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    user, error = await auth_service.login_user(db, body.username, body.password)
    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)

    tokens = auth_service.create_tokens(user)
    return AuthResponse(
        user=UserResponse(**user.to_dict()),
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post("/logout")
async def logout(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """用户登出，撤销 Refresh Token"""
    await auth_service.revoke_token(db, body.refresh_token)
    return {"message": "已成功登出"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """刷新 Token"""
    from app.core.security import decode_token as decode

    payload = decode(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh Token 无效或已过期")

    from app.services.auth_service import is_token_revoked
    if await is_token_revoked(db, payload.get("jti", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh Token 已被撤销")

    # 撤销旧的 refresh token
    await auth_service.revoke_token(db, body.refresh_token)

    # 获取用户信息
    user = await auth_service.get_user_by_id(db, payload.get("sub", ""))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    tokens = auth_service.create_tokens(user)
    return TokenResponse(**tokens)


@router.put("/password")
async def change_password(
    body: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    error = await auth_service.change_user_password(db, current_user, body.old_password, body.new_password)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return {"message": "密码修改成功"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(**current_user.to_dict())

"""对话 API 路由"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import CreateSessionRequest, SendMessageRequest
from app.services import chat_service

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.get("/sessions")
async def list_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的会话列表"""
    return await chat_service.get_sessions(db, current_user.id, page, size)


@router.post("/sessions")
async def create_session(
    body: CreateSessionRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新会话"""
    session = await chat_service.create_session(db, current_user.id, body.title if body else None)
    return session.to_dict()


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除会话"""
    success = await chat_service.delete_session(db, session_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已删除"}


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话消息"""
    return await chat_service.get_messages(db, session_id, current_user.id, page, size)


@router.post("/sessions/{session_id}/send")
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送消息（SSE 流式响应）"""
    # 验证会话归属
    session = await chat_service.get_session_by_id(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="会话不存在")

    async def event_stream():
        try:
            async for event in chat_service.stream_chat(db, session_id, body.content):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions/{session_id}/regenerate")
async def regenerate_message(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新生成最后一条回答"""
    session = await chat_service.get_session_by_id(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="会话不存在")

    async def event_stream():
        try:
            async for event in chat_service.regenerate_last(db, session_id):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

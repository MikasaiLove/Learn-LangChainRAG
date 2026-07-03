"""对话业务逻辑"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from app.models.session import Session
from app.models.message import Message


async def get_sessions(db: AsyncSession, user_id: str, page: int = 1, size: int = 20) -> dict:
    """获取用户的会话列表"""
    total_result = await db.execute(
        select(func.count(Session.id)).where(Session.user_id == user_id)
    )
    total = total_result.scalar() or 0

    query = (
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(Session.updated_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "items": [s.to_dict() for s in sessions],
        "total": total,
    }


async def create_session(db: AsyncSession, user_id: str, title: str | None = None) -> Session:
    """创建新会话"""
    session = Session(
        user_id=user_id,
        title=title or "新对话",
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session_id: str, user_id: str) -> bool:
    """删除会话（验证归属）"""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return False

    # 级联删除消息
    await db.execute(delete(Message).where(Message.session_id == session_id))
    await db.delete(session)
    await db.flush()
    return True


async def get_session_by_id(db: AsyncSession, session_id: str) -> Session | None:
    """按 ID 获取会话"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


async def get_messages(
    db: AsyncSession, session_id: str, user_id: str, page: int = 1, size: int = 50
) -> dict:
    """获取会话消息（验证归属）"""
    # 验证归属
    session = await get_session_by_id(db, session_id)
    if not session or session.user_id != user_id:
        return {"items": [], "total": 0}

    total_result = await db.execute(
        select(func.count(Message.id)).where(Message.session_id == session_id)
    )
    total = total_result.scalar() or 0

    query = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    return {
        "items": [m.to_dict() for m in messages],
        "total": total,
    }


async def save_user_message(db: AsyncSession, session_id: str, content: str) -> Message:
    """保存用户消息"""
    msg = Message(session_id=session_id, role="user", content=content)
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg


async def save_assistant_message(
    db: AsyncSession, session_id: str, content: str, citations: list | None = None, tokens: dict | None = None
) -> Message:
    """保存助手消息"""
    from app.core.logger import get_logger
    _log = get_logger(__name__)
    _log.info(f"Saving assistant message, tokens={tokens}")
    msg = Message(
        session_id=session_id,
        role="assistant",
        content=content,
        citations=citations or [],
        tokens=tokens,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    _log.info(f"Saved message {msg.id}, tokens from DB={msg.tokens}")
    return msg


async def get_last_assistant_message(db: AsyncSession, session_id: str) -> Message | None:
    """获取会话最后一条助手消息"""
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id, Message.role == "assistant")
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_chat_history(db: AsyncSession, session_id: str, limit: int = 10) -> list:
    """获取最近的对话历史（用于 RAG 上下文）"""
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit * 2)  # user + assistant pairs
    )
    messages = result.scalars().all()
    messages.reverse()
    return [msg.to_dict() for msg in messages]


async def update_session_title(db: AsyncSession, session_id: str, first_message: str):
    """根据第一条消息自动生成会话标题"""
    title = first_message[:30] + ("..." if len(first_message) > 30 else "")
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        session.title = title
        await db.flush()


async def stream_chat(db: AsyncSession, session_id: str, user_content: str):
    """流式对话（核心）"""
    from app.rag.pipeline import get_rag_pipeline

    # 1. 保存用户消息
    user_msg = await save_user_message(db, session_id, user_content)

    # 2. 获取对话历史
    history = await get_chat_history(db, session_id)

    # 3. 检查是否是第一条消息，更新标题
    if len(history) <= 1:
        await update_session_title(db, session_id, user_content)

    # 4. 执行 RAG 管道
    pipeline = get_rag_pipeline()
    full_response = ""
    citations = []

    async for event in pipeline.stream_query(user_content, history):
        event_type = event.get("type")
        if event_type == "token":
            full_response += event.get("content", "")
            yield event
        elif event_type == "citations":
            citations = event.get("data", [])
            yield event
        elif event_type == "done":
            # 5. 保存助手消息（含 tokens）
            assistant_msg = await save_assistant_message(
                db, session_id, full_response, citations, event.get("tokens")
            )
            # 更新会话活跃时间
            session = await get_session_by_id(db, session_id)
            if session:
                session.updated_at = datetime.now(timezone.utc)
                await db.flush()
            yield {
                "type": "done",
                "message_id": assistant_msg.id,
                "citations": citations,
                "tokens": event.get("tokens"),
            }
        elif event_type == "error":
            yield event


async def regenerate_last(db: AsyncSession, session_id: str):
    """重新生成最后一条回答"""
    from app.rag.pipeline import get_rag_pipeline

    # 获取最后一条用户消息
    history = await get_chat_history(db, session_id)
    last_user_msg = None
    for msg in reversed(history):
        if msg["role"] == "user":
            last_user_msg = msg
            break

    if not last_user_msg:
        yield {"type": "error", "message": "没有可重新生成的消息"}
        return

    # 删除最后一条助手消息
    last_assistant = await get_last_assistant_message(db, session_id)
    if last_assistant:
        await db.delete(last_assistant)
        await db.flush()

    # 重新执行 RAG（去掉最后一条用户消息后的历史）
    history_before = [m for m in history if m["id"] != last_user_msg["id"]]

    pipeline = get_rag_pipeline()
    full_response = ""
    citations = []

    async for event in pipeline.stream_query(last_user_msg["content"], history_before):
        event_type = event.get("type")
        if event_type == "token":
            full_response += event.get("content", "")
            yield event
        elif event_type == "citations":
            citations = event.get("data", [])
            yield event
        elif event_type == "done":
            assistant_msg = await save_assistant_message(
                db, session_id, full_response, citations, event.get("tokens")
            )
            yield {
                "type": "done",
                "message_id": assistant_msg.id,
                "citations": citations,
                "tokens": event.get("tokens"),
            }
        elif event_type == "error":
            yield event

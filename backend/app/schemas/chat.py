"""对话相关的 Pydantic 模型"""
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200, description="会话标题（可选，默认自动生成）")


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, description="消息内容")


class SessionResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str | None = None
    updated_at: str | None = None


class CitationItem(BaseModel):
    doc_id: str
    doc_name: str
    chunk_text: str
    score: float


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: list[dict] = []
    created_at: str | None = None


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    total: int


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int

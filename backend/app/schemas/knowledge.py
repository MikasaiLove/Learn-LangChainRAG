"""知识库相关的 Pydantic 模型"""
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    char_count: int
    chunk_count: int
    uploaded_by: str
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    char_count: int
    chunk_count: int


class KnowledgeStatsResponse(BaseModel):
    document_count: int
    total_chunks: int
    total_chars: int

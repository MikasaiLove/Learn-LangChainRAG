"""知识库管理业务逻辑"""
import os
import uuid
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.document import Document
from app.config import get_settings

settings = get_settings()


async def get_documents(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    status: str | None = None,
    search: str | None = None,
) -> dict:
    """获取文档列表（分页、筛选、搜索）"""
    query = select(Document)
    count_query = select(func.count(Document.id))

    if status:
        query = query.where(Document.status == status)
        count_query = count_query.where(Document.status == status)

    if search:
        search_filter = Document.filename.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # 总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    query = query.order_by(Document.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    documents = result.scalars().all()

    return {
        "items": [doc.to_dict() for doc in documents],
        "total": total,
    }


async def upload_document(db: AsyncSession, file: UploadFile, user_id: str) -> dict:
    """上传文档"""
    # 校验文件类型
    allowed_types = {"pdf", "docx", "txt", "md", "csv", "html"}
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}，支持: {', '.join(allowed_types)}")

    # 校验文件大小
    content = await file.read()
    file_size = len(content)
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 ({settings.max_upload_size_mb}MB)")

    # 保存文件
    os.makedirs(settings.upload_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(settings.upload_dir, stored_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # 创建文档记录
    doc = Document(
        filename=filename,
        file_type=ext,
        file_size=file_size,
        status="pending",
        uploaded_by=user_id,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    # 同步处理文档（小文件），大文件可走 Celery
    try:
        await _process_document(db, doc, file_path)
    except Exception as e:
        from app.core.logger import get_logger
        _log = get_logger(__name__)
        _log.error(f"Document processing failed: {filename} | error: {e}", exc_info=True)
        doc.status = "fail"
        doc.error_message = str(e)
        await db.flush()

    return doc.to_dict()


async def get_document_by_id(db: AsyncSession, doc_id: str) -> Document | None:
    """按 ID 获取文档"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    return result.scalar_one_or_none()


async def delete_document(db: AsyncSession, doc_id: str) -> bool:
    """删除文档及其向量数据"""
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        return False

    # 删除向量数据
    from app.services.document_processor import delete_document_vectors
    await delete_document_vectors(doc_id)

    # 删除本地文件
    try:
        settings_obj = get_settings()
        for f in os.listdir(settings_obj.upload_dir):
            if doc_id[:8] in f or (doc.filename and doc.filename in f):
                os.remove(os.path.join(settings_obj.upload_dir, f))
    except Exception:
        pass

    await db.delete(doc)
    await db.flush()
    return True


async def get_stats(db: AsyncSession) -> dict:
    """获取知识库统计"""
    result = await db.execute(
        select(
            func.count(Document.id).label("count"),
            func.sum(Document.chunk_count).label("total_chunks"),
            func.sum(Document.char_count).label("total_chars"),
        ).where(Document.status == "done")
    )
    row = result.one()

    # 文档总数（含所有状态）
    total_result = await db.execute(select(func.count(Document.id)))
    total_docs = total_result.scalar() or 0

    return {
        "document_count": total_docs,
        "indexed_count": row.count or 0,
        "total_chunks": row.total_chunks or 0,
        "total_chars": row.total_chars or 0,
    }


async def _process_document(db: AsyncSession, doc: Document, file_path: str):
    """内部：处理文档（解析 + 分块 + 向量化）"""
    from app.services.document_processor import process_document
    doc.status = "processing"
    await db.flush()

    char_count, chunk_count = await process_document(doc, file_path)

    doc.status = "done"
    doc.char_count = char_count
    doc.chunk_count = chunk_count
    doc.updated_at = datetime.now(timezone.utc)
    await db.flush()

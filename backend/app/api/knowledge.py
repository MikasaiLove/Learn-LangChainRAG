"""知识库管理 API 路由（仅 admin）"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_admin_user
from app.models.user import User
from app.services import kb_service

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])


@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """获取文档列表（分页）"""
    return await kb_service.get_documents(db, page, size, status, search)


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """上传文档"""
    return await kb_service.upload_document(db, file, admin.id)


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """获取文档详情"""
    doc = await kb_service.get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc.to_dict()


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """删除文档（级联删除向量）"""
    success = await kb_service.delete_document(db, doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"message": "文档已删除"}


@router.get("/documents/{doc_id}/status")
async def get_document_status(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """查看文档处理状态"""
    doc = await kb_service.get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {
        "id": doc.id,
        "status": doc.status,
        "char_count": doc.char_count,
        "chunk_count": doc.chunk_count,
    }


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """获取知识库统计"""
    return await kb_service.get_stats(db)

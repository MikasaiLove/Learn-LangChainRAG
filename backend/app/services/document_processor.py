"""文档解析、分块、向量化"""
import os
import asyncio
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
)
from langchain_core.documents import Document as LCDocument
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from app.config import get_settings

settings = get_settings()


def load_document(file_path: str, file_type: str) -> list:
    """根据文件类型选择加载器"""
    loaders = {
        "pdf": PyMuPDFLoader,
        "docx": Docx2txtLoader,
        "txt": TextLoader,
        "csv": CSVLoader,
    }

    if file_type in loaders:
        if file_type in ("txt", "csv"):
            loader = loaders[file_type](file_path, encoding="utf-8")
        else:
            loader = loaders[file_type](file_path)
        return loader.load()

    # md / html 等纯文本格式直接读取
    if file_type in ("md", "html"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return [LCDocument(page_content=content, metadata={"source": file_path})]

    raise ValueError(f"不支持的文件类型: {file_type}")


def chunk_documents(docs: list, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
    """智能分块"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ", ""],
        length_function=len,
    )
    return splitter.split_documents(docs)


def get_embeddings():
    """获取百炼 Embedding 模型"""
    return DashScopeEmbeddings(
        model=settings.embedding_model,
        dashscope_api_key=settings.dashscope_api_key,
    )


def get_vector_store():
    """获取 Chroma 向量存储"""
    return Chroma(
        persist_directory=settings.chroma_persist_dir,
        embedding_function=get_embeddings(),
        collection_name="knowledge_base",
    )


async def process_document(doc, file_path: str) -> tuple[int, int]:
    """处理文档：加载 -> 分块 -> 向量化 -> 存入 Chroma"""
    # 1. 加载文档
    raw_docs = load_document(file_path, doc.file_type)
    if not raw_docs:
        raise ValueError("文档内容为空")

    # 2. 分块
    chunks = chunk_documents(raw_docs)
    if not chunks:
        raise ValueError("分块结果为空")

    # 3. 添加元数据
    for i, chunk in enumerate(chunks):
        chunk.metadata["doc_id"] = doc.id
        chunk.metadata["doc_name"] = doc.filename
        chunk.metadata["chunk_index"] = i

    # 4. 计算总字符数
    total_chars = sum(len(chunk.page_content) for chunk in chunks)

    # 5. 存入 Chroma（同步方法，用 asyncio.to_thread 包装）
    vector_store = get_vector_store()
    await asyncio.to_thread(
        vector_store.add_documents,
        chunks,
        ids=[f"{doc.id}_{i}" for i in range(len(chunks))],
    )

    return total_chars, len(chunks)


async def delete_document_vectors(doc_id: str):
    """删除文档对应的向量数据"""
    try:
        vector_store = get_vector_store()
        # 按 metadata 过滤删除
        results = vector_store.get(where={"doc_id": doc_id})
        if results and results.get("ids"):
            vector_store.delete(ids=results["ids"])
    except Exception:
        pass  # 向量库删除失败不阻塞主流程

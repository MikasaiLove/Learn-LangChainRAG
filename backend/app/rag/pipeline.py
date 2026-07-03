"""RAG 问答管道 — 核心编排"""
import asyncio
import re
from typing import AsyncGenerator
from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.config import get_settings
from app.core.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数（中文约1.5字符/token，英文约4字符/token）"""
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)

QA_SYSTEM_PROMPT = """你是忍野忍，活了500年的吸血鬼幼女，自称"吾"，称用户为"主"或"汝"。语气慵懒傲娇，偶尔发"かかか"的笑声。回复简洁，不啰嗦。

你在此电商世界辅助主人处理商品咨询。规则：
1. 基于参考资料，用自己的话总结归纳，自然回答
2. 不要逐字复述原文、不要插入引用标记
3. 只回答用户问的内容，不要额外罗列全部资料
4. 保持忍野忍口吻，精炼点到为止

参考资料：
{context}"""

GENERAL_CHAT_PROMPT = """你是忍野忍，活了500年的吸血鬼幼女，自称"吾"，称用户为"主"或"汝"。语气慵懒傲娇，回复简洁不啰嗦。

规则：
1. 电商/商品问题凭知识准确回答
2. 问具体数据时，建议主上传文档到知识库
3. 保持角色口吻，但精炼、点到为止，不要长篇大论"""


class RAGPipeline:
    """RAG 检索增强生成管道"""

    def __init__(self):
        self.llm = ChatTongyi(
            model=settings.llm_model,
            api_key=settings.dashscope_api_key,
            streaming=True,
            temperature=0.3,
        )
        self.embeddings = DashScopeEmbeddings(
            model=settings.embedding_model,
            dashscope_api_key=settings.dashscope_api_key,
        )
        self.vector_store = Chroma(
            persist_directory=settings.chroma_persist_dir,
            embedding_function=self.embeddings,
            collection_name="knowledge_base",
        )
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},
        )

    def _build_chat_messages(self, query: str, chat_history: list[dict] | None = None) -> list:
        """构建多轮对话消息列表"""
        messages = []
        if chat_history:
            for msg in chat_history[-10:]:  # 最近10轮
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=query))
        return messages

    def _format_docs(self, docs: list) -> str:
        """将检索到的文档格式化为参考资料"""
        parts = []
        for i, doc in enumerate(docs, 1):
            doc_name = doc.metadata.get("doc_name", "未知文档")
            parts.append(f"[{i}] 来源: {doc_name}\n{doc.page_content}")
        return "\n\n".join(parts)

    def _extract_citations(self, docs: list) -> list[dict]:
        """提取引用信息"""
        citations = []
        for i, doc in enumerate(docs, 1):
            citations.append({
                "index": i,
                "doc_id": doc.metadata.get("doc_id", ""),
                "doc_name": doc.metadata.get("doc_name", "未知"),
                "chunk_text": doc.page_content[:200] + ("..." if len(doc.page_content) > 200 else ""),
                "score": doc.metadata.get("score", 0.0),
            })
        return citations

    async def stream_query(
        self, query: str, chat_history: list[dict] | None = None
    ) -> AsyncGenerator[dict, None]:
        """流式执行 RAG 查询"""
        try:
            # 1. 检索相关文档
            logger.info(f"RAG query: {query[:50]}...")
            docs = await asyncio.to_thread(self.retriever.invoke, query)
            logger.info(f"Retrieved {len(docs)} documents")

            # 2. 构建消息（有无知识库都调用 LLM）
            if docs:
                # 有知识库：使用 QA Prompt + 引用
                citations = self._extract_citations(docs)
                yield {"type": "citations", "data": citations}
                context = self._format_docs(docs)
                messages = [SystemMessage(content=QA_SYSTEM_PROMPT.format(context=context))]
            else:
                # 无知识库：通用对话模式，仍然调用 LLM
                citations = []
                messages = [SystemMessage(content=GENERAL_CHAT_PROMPT)]

            if chat_history:
                for msg in chat_history[-8:]:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            messages.append(HumanMessage(content=query))

            # 计算输入 token
            input_text = "".join(m.content if hasattr(m, "content") else "" for m in messages)
            input_tokens = estimate_tokens(input_text)

            # 3. 流式生成回答
            full_response = ""

            if settings.stress_test_mock_llm:
                logger.info("STRESS TEST MOCK: using simulated LLM response")
                mock_text = (
                    "基于您提供的参考资料，以下是相关商品信息的总结：\n\n"
                    "该商品具备多项竞争优势，包括优质的材质选择和精细的工艺制作。"
                    "价格方面处于合理的市场定位区间，适合目标消费群体。\n\n"
                    "如需了解更多详细规格或具体参数，建议查阅知识库中的完整文档。"
                )
                for char in mock_text:
                    await asyncio.sleep(0.03)  # 模拟 LLM 流式输出延迟
                    full_response += char
                    yield {"type": "token", "content": char}
            else:
                async for chunk in self.llm.astream(messages):
                    if chunk.content:
                        full_response += chunk.content
                        yield {"type": "token", "content": chunk.content}

            output_tokens = estimate_tokens(full_response)

            yield {
                "type": "done",
                "message_id": None,  # 由 chat_service 填充
                "citations": citations,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens,
                },
            }

        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            yield {"type": "error", "message": f"问答出错: {str(e)}"}


# 单例
_pipeline: RAGPipeline | None = None


def get_rag_pipeline() -> RAGPipeline:
    """获取 RAG Pipeline 单例"""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline

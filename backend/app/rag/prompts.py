"""Prompt 模板"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 多轮对话问题改写
CONDENSE_QUESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "结合对话历史，将用户问题改写为一个独立、完整的检索查询。直接输出改写后的问题，不要加任何解释。"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

# QA 带引用 Prompt
QA_WITH_CITATIONS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是电商商品知识库助手。严格根据以下参考资料回答问题。
如果资料中没有相关信息，请明确说明"知识库中暂无该商品的相关信息，建议联系客服获取更多帮助"。
在回答中用 [1] [2] [3] 标注引用的资料编号。
保持热情友好的客服语气，回答条理清晰。

参考资料：
{context}"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

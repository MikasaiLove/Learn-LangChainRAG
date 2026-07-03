"""测试 rag/prompts.py — Prompt 模板"""
import pytest
from app.rag.prompts import CONDENSE_QUESTION_PROMPT, QA_WITH_CITATIONS_PROMPT
from langchain_core.prompts import ChatPromptTemplate


class TestCondenseQuestionPrompt:
    """多轮对话问题改写 Prompt 测试"""

    def test_is_chat_prompt_template(self):
        """应该是 ChatPromptTemplate 实例"""
        assert isinstance(CONDENSE_QUESTION_PROMPT, ChatPromptTemplate)

    def test_contains_chat_history_placeholder(self):
        """应该包含 chat_history 占位符"""
        # ChatPromptTemplate 的 messages 中应该有 MessagesPlaceholder
        messages = CONDENSE_QUESTION_PROMPT.messages
        has_history = any(
            hasattr(msg, "variable_name") and msg.variable_name == "chat_history"
            for msg in messages
        )
        assert has_history, "CONDENSE_QUESTION_PROMPT 应该包含 chat_history 占位符"

    def test_contains_input_variable(self):
        """应该包含 {input} 变量"""
        messages = CONDENSE_QUESTION_PROMPT.messages
        human_msg = messages[-1]
        assert hasattr(human_msg, "prompt")
        template = human_msg.prompt.template if hasattr(human_msg.prompt, "template") else str(human_msg.prompt)
        assert "input" in str(template)


class TestQAWithCitationsPrompt:
    """带引用 QA Prompt 测试"""

    def test_is_chat_prompt_template(self):
        """应该是 ChatPromptTemplate 实例"""
        assert isinstance(QA_WITH_CITATIONS_PROMPT, ChatPromptTemplate)

    def test_contains_citation_instruction(self):
        """应该包含引用标注的指示"""
        system_msg = QA_WITH_CITATIONS_PROMPT.messages[0]
        template = system_msg.prompt.template if hasattr(system_msg.prompt, "template") else str(system_msg)
        assert "[1]" in str(template) or "[2]" in str(template), "应该指示用 [1] [2] 标注引用"

    def test_contains_context_variable(self):
        """应该包含 {context} 变量"""
        system_msg = QA_WITH_CITATIONS_PROMPT.messages[0]
        template = system_msg.prompt.template if hasattr(system_msg.prompt, "template") else str(system_msg)
        assert "context" in str(template)

    def test_contains_chat_history_placeholder(self):
        """应该包含 chat_history 占位符"""
        messages = QA_WITH_CITATIONS_PROMPT.messages
        has_history = any(
            hasattr(msg, "variable_name") and msg.variable_name == "chat_history"
            for msg in messages
        )
        assert has_history, "QA_WITH_CITATIONS_PROMPT 应该包含 chat_history 占位符"

    def test_contains_input_variable(self):
        """应该包含 {input} 变量"""
        messages = QA_WITH_CITATIONS_PROMPT.messages
        last_msg = messages[-1]
        assert "input" in str(last_msg)

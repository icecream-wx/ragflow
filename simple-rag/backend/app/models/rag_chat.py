"""
RAG 对话模型：多轮记忆 + 拼提示词 + LLM 流式输出
"""
from typing import List, Dict, AsyncIterator
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.logger import app_logger
from app.core.llm_config import get_llm_config
from app.services.rag_pipeline import run_rag_retrieve

SYSTEM_PROMPT_BASE = """你是一个基于知识库的智能助手。请根据对话历史和当前问题作答。
若下方提供了「参考内容」，请优先依据参考内容回答；若参考内容与问题无关或为空，可基于通用知识回答并说明。
回答需准确、简洁、友好。"""


def _build_system_message(context: str) -> SystemMessage:
    if context and context.strip():
        content = f"""{SYSTEM_PROMPT_BASE}

{context}

请结合以上参考内容回答用户问题。"""
    else:
        content = SYSTEM_PROMPT_BASE
    return SystemMessage(content=content)


def _history_to_messages(history: List[Dict[str, str]], max_turns: int = 10) -> List[BaseMessage]:
    messages = []
    flat = list(history)
    if len(flat) > max_turns * 2:
        flat = flat[-max_turns * 2:]
    for h in flat:
        role = h.get("role", "")
        content = (h.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def create_llm_instance():
    config = get_llm_config()
    base_url = config.get_base_url()
    if base_url:
        return ChatOpenAI(
            model=config.get_model_name(),
            api_key=config.get_api_key(),
            base_url=base_url,
            temperature=0.7,
            streaming=True
        )
    return ChatOpenAI(
        model=config.get_model_name(),
        api_key=config.get_api_key(),
        temperature=0.7,
        streaming=True
    )


async def generate_rag_response(
    message: str,
    history: List[Dict[str, str]],
    use_rag: bool = True
) -> AsyncIterator[str]:
    """生成带 RAG 与多轮记忆的流式响应。"""
    try:
        llm = create_llm_instance()

        context = ""
        if use_rag:
            try:
                context = run_rag_retrieve(message)
            except Exception as e:
                app_logger.warning(f"RAG 检索异常: {e}")

        system_msg = _build_system_message(context)
        all_messages: List[BaseMessage] = [system_msg]
        all_messages.extend(_history_to_messages(history))
        all_messages.append(HumanMessage(content=message))

        app_logger.info(f"生成回答: use_rag={use_rag}, 历史轮数≈{len(history)//2}")

        async for chunk in llm.astream(all_messages):
            content_to_yield = None
            if hasattr(chunk, "content") and chunk.content:
                content_to_yield = chunk.content
            elif isinstance(chunk, str) and chunk:
                content_to_yield = chunk
            if content_to_yield:
                yield content_to_yield

    except Exception as e:
        app_logger.error(f"生成 RAG 响应失败: {e}", exc_info=True)
        yield f"抱歉，回答时出错: {str(e)}"

"""
聊天 API：多轮对话与记忆，RAG 检索增强（SSE 流式响应）
"""
import json
from typing import Dict, List, Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.response import ResponseModel
from app.core.logger import app_logger
from app.models.rag_chat import generate_rag_response

router = APIRouter()


class MessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_rag: bool = True


sessions: Dict[str, List[Dict[str, str]]] = {}


def _get_or_create_history(session_id: str) -> List[Dict[str, str]]:
    if session_id not in sessions:
        sessions[session_id] = []
    return sessions[session_id]


@router.post("/send")
async def send_message(message_req: MessageRequest):
    """发送用户消息并写入会话历史"""
    try:
        session_id = message_req.session_id or "default"
        history = _get_or_create_history(session_id)
        history.append({"role": "user", "content": message_req.message})
        return ResponseModel.success(data={"session_id": session_id}, message="发送成功")
    except Exception as e:
        app_logger.error(f"发送消息失败: {e}", exc_info=True)
        return ResponseModel.error(message=f"发送失败: {str(e)}", code=500)


@router.get("/chat")
async def chat_with_ai(
    session_id: Optional[str] = None,
    use_rag: bool = True
):
    """与 AI 多轮对话（SSE 流式），带 RAG 与记忆"""
    try:
        session_id = session_id or "default"
        history = sessions.get(session_id, [])
        if not history:
            return ResponseModel.error(message="暂无用户消息", code=404)

        last_user = None
        for msg in reversed(history):
            if msg.get("role") == "user":
                last_user = msg.get("content")
                break
        if not last_user:
            return ResponseModel.error(message="未找到用户消息", code=404)

        async def generate_stream():
            full_response = ""
            try:
                async for chunk in generate_rag_response(
                    message=last_user,
                    history=history[:-1],
                    use_rag=use_rag
                ):
                    if chunk:
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"

                if not full_response:
                    full_response = "抱歉，暂时无法回答，请稍后再试。"
                    yield f"data: {json.dumps({'type': 'content', 'data': full_response}, ensure_ascii=False)}\n\n"

                _get_or_create_history(session_id).append({"role": "assistant", "content": full_response})
                yield f"data: {json.dumps({'type': 'done', 'data': {'session_id': session_id}}, ensure_ascii=False)}\n\n"
            except Exception as e:
                app_logger.error(f"流式响应错误: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        app_logger.error(f"对话失败: {e}", exc_info=True)
        return ResponseModel.error(message=f"对话失败: {str(e)}", code=500)


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        history = sessions.get(session_id, [])
        return ResponseModel.success(data=history, message="获取成功")
    except Exception as e:
        app_logger.error(f"获取历史失败: {e}", exc_info=True)
        return ResponseModel.error(message=f"获取失败: {str(e)}", code=500)


@router.get("/sessions")
async def get_chat_sessions():
    try:
        session_list = []
        for sid, history in sessions.items():
            last_msg = ""
            for msg in reversed(history):
                if msg.get("role") == "user":
                    last_msg = (msg.get("content") or "")[:50]
                    break
            session_list.append({
                "session_id": sid,
                "title": last_msg or "新对话",
                "last_message": last_msg,
                "message_count": len(history)
            })
        return ResponseModel.success(data=session_list, message="获取成功")
    except Exception as e:
        app_logger.error(f"获取会话列表失败: {e}", exc_info=True)
        return ResponseModel.error(message=f"获取失败: {str(e)}", code=500)


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    try:
        if session_id in sessions:
            del sessions[session_id]
            return ResponseModel.success(data=None, message="删除成功")
        return ResponseModel.error(message="会话不存在", code=404)
    except Exception as e:
        app_logger.error(f"删除会话失败: {e}", exc_info=True)
        return ResponseModel.error(message=f"删除失败: {str(e)}", code=500)

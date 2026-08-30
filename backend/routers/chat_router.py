"""
/ api/chat/stream - 对话SSE接口
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from models.response import APIResponse
from models.schemas import ChatRequest
from db import get_db
from models.schema import GuaCase, ChatMessage
from services.analysis_engine import AnalysisEngine
from middleware.risk_control import filter_language
import json

router = APIRouter(prefix="/api/chat", tags=["对话"])
engine = AnalysisEngine()


@router.post("/stream")
async def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):
    """SSE流式多轮对话"""
    history_list = []
    case_id = req.case_id

    # 如果是有case_id的对话，加载历史记录
    if case_id:
        case = db.query(GuaCase).filter(GuaCase.case_id == case_id).first()
        if not case:
            return APIResponse.err(404, "卦例不存在")
        history = db.query(ChatMessage).filter(
            ChatMessage.case_id == case_id,
            ChatMessage.role == "assistant"
        ).order_by(ChatMessage.created_at).all()
        history_list = [{"role": "assistant", "content": m.content} for m in history[-5:]]
        # 保存用户消息
        user_msg = ChatMessage(case_id=case_id, role="user", content=req.message)
        db.add(user_msg)
        db.commit()

    async def event_stream():
        # 构建上下文：如果有卦盘信息则带入
        context_info = {}
        if case_id:
            context_info = {'case_id': case_id}
        elif req.question:
            context_info = {'question': req.question, 'category': req.category, 'gua_disk': req.gua_disk}
        
        async for event in engine.stream_chat(
            case_id=case_id,
            history=history_list,
            message=req.message,
            context=context_info
        ):
            yield event
        yield "event: complete\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

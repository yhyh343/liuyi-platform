"""
/ api/gua/analyze 和 / api/gua/analyze/stream - 解卦接口
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from models.response import APIResponse
from models.schemas import AnalyzeRequest
from db import get_db
from models.schema import GuaCase, ChatMessage
from rag.rag_service import RAGService
from services.analysis_engine import AnalysisEngine
from middleware.risk_control import filter_language
import json

router = APIRouter(prefix="/api/gua", tags=["解卦"])
engine = AnalysisEngine()


@router.post("/analyze")
async def analyze_gua(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """标准解卦接口"""
    case = db.query(GuaCase).filter(GuaCase.case_id == req.case_id).first()
    if not case:
        return APIResponse.err(404, "卦例不存在")

    rag_svc = RAGService(db)
    rag_contexts = rag_svc.search(case.question, top_k=5)
    rag_text = "\n".join([f"[{r['source']}] {r['title']}: {r['content']}" for r in rag_contexts])

    result = await engine.analyze_gua(
        gua_disk=case.gua_disk,
        rag_context=rag_text,
        question=case.question,
        category=case.category
    )

    for k, v in result.items():
        if isinstance(v, str):
            result[k] = filter_language(v)

    case.analysis_result = result
    case.confidence = result.get("confidence", 0.5)
    case.risk_level = result.get("risk_level", "中")
    case.reference_strength = result.get("reference_strength", 0.5)
    db.commit()

    chat_msg = ChatMessage(case_id=case.case_id, role="assistant", content=json.dumps(result, ensure_ascii=False))
    db.add(chat_msg)
    db.commit()

    return APIResponse.ok(data=result)


@router.post("/analyze/stream")
async def analyze_gua_stream(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """SSE流式解卦接口"""
    case = db.query(GuaCase).filter(GuaCase.case_id == req.case_id).first()
    if not case:
        return APIResponse.err(404, "卦例不存在")

    rag_svc = RAGService(db)
    rag_contexts = rag_svc.search(case.question, top_k=5)
    rag_text = "\n".join([f"[{r['source']}] {r['title']}: {r['content']}" for r in rag_contexts])

    async def event_stream():
        async for event in engine.stream_analyze(
            gua_disk=case.gua_disk,
            rag_context=rag_text,
            question=case.question,
            category=case.category
        ):
            yield event
        yield "event: complete\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

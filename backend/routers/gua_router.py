"""
/ api/gua/create - 起卦创建接口
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models.response import APIResponse
from models.schemas import CreateGuaRequest, CalibrateResponse
from db import get_db
from services.calibration_service import calibrate_question
from services.divination_service import create_gua_case
from models.schema import GuaCase, User
from middleware.risk_control import check_blocked, filter_language
from rag.rag_service import RAGService
from config import settings
import json

router = APIRouter(prefix="/api/gua", tags=["卦例"])


@router.post("/create")
async def create_gua(req: CreateGuaRequest, db: Session = Depends(get_db)):
    """创建卦例：校准→风控→起卦→保存"""
    # 1. 风控拦截
    risk_check = check_blocked(req.question)
    if risk_check["blocked"]:
        return APIResponse.err(4001, risk_check["reason"])

    # 2. 问题校准
    calibrate_result = calibrate_question(req.question, req.category)
    if calibrate_result["need_refine"]:
        return APIResponse.ok(
            data=CalibrateResponse(**calibrate_result).model_dump(),
            message="问题需要细化"
        )

    # 3. 起卦
    gua_result = create_gua_case(
        method=req.method,
        params=req.params,
        question=req.question,
        category=req.category,
        calibrate_info=calibrate_result
    )

    # 4. 保存卦例
    user_id = None
    if req.user_id:
        user = db.query(User).filter(User.id == uuid.UUID(req.user_id)).first()
        if user:
            user_id = user.id

    case = GuaCase(
        case_id=gua_result["case_id"],
        user_id=user_id,
        question=req.question,
        category=req.category,
        method=req.method,
        gua_disk=gua_result["gua_disk"],
        analysis_result=None
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    return APIResponse.ok(data={
        "case_id": gua_result["case_id"],
        "gua_disk": gua_result["gua_disk"],
        "calibrate_info": calibrate_result
    })

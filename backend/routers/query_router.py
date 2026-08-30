"""
/ api/gua/list - 卦例列表查询
/ api/auth - 用户注册登录
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.response import APIResponse
from models.schemas import ListGuaRequest, RegisterRequest, LoginRequest
from db import get_db
from models.schema import GuaCase, User
from utils.auth import hash_password, verify_password, create_access_token
from config import settings
import uuid

router = APIRouter(prefix="/api/gua", tags=["查询"])


@router.get("/list")
async def list_gua(user_id: str = None, category: str = None, page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    """卦例列表查询"""
    query = db.query(GuaCase)
    if user_id:
        query = query.filter(GuaCase.user_id == uuid.UUID(user_id))
    if category:
        query = query.filter(GuaCase.category == category)

    total = query.count()
    cases = query.order_by(desc(GuaCase.created_at)).offset(
        (page - 1) * size
    ).limit(size).all()

    return APIResponse.ok(data={
        "total": total,
        "page": page,
        "size": size,
        "items": [{
            "case_id": c.case_id,
            "question": c.question,
            "category": c.category,
            "gua_name": c.gua_disk.get("gua_name", "") if c.gua_disk else "",
            "trend": c.gua_disk.get("trend", "") if c.gua_disk else "",
            "created_at": c.created_at.isoformat() if c.created_at else None
        } for c in cases]
    })


auth_router = APIRouter(prefix="/api/auth", tags=["认证"])


@auth_router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    existing = db.query(User).filter(
        (User.username == req.username) | (User.email == req.email)
    ).first()
    if existing:
        return APIResponse.err(400, "用户名或邮箱已存在")

    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return APIResponse.ok(data={"user_id": str(user.id), "username": user.username})


@auth_router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        return APIResponse.err(401, "用户名或密码错误")
    if not user.is_active:
        return APIResponse.err(403, "账号已被禁用")

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return APIResponse.ok(data={
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user.id)
    })

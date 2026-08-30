"""
Pydantic 请求/响应 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid


# 请求Schema
class CreateGuaRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    category: str = Field(..., pattern="^(工作事业|财运投资|感情婚姻|考试学业|出行旅行|健康疾病)$")
    method: str = Field(..., pattern="^(coin|time|number)$")
    params: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None


class AnalyzeRequest(BaseModel):
    case_id: str = Field(..., min_length=1, max_length=32)


class ChatRequest(BaseModel):
    case_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=500)
    question: Optional[str] = None
    category: Optional[str] = None
    gua_disk: Optional[Dict[str, Any]] = None


class ListGuaRequest(BaseModel):
    user_id: Optional[str] = None
    category: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=50)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


# 响应Schema
class CalibrateResponse(BaseModel):
    is_valid: bool
    need_refine: bool
    refine_suggestions: List[str]
    has_specific_event: bool
    has_time_range: bool
    has_decision_goal: bool
    clarity_score: float


class GuaCreateResponse(BaseModel):
    case_id: Optional[str] = None
    gua_disk: Dict[str, Any]
    calibrate_info: Dict[str, Any]


class ChatMessageSchema(BaseModel):
    role: str
    content: str
    created_at: Optional[str] = None

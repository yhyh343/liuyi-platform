"""
统一响应格式
"""
from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool
    code: int
    message: str
    data: Optional[Any] = None

    @classmethod
    def ok(cls, data=None, message="success"):
        return cls(success=True, code=200, message=message, data=data)

    @classmethod
    def err(cls, code: int, message: str):
        return cls(success=False, code=code, message=message)

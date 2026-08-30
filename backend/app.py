"""
FastAPI 主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routers import gua_router, analyze_router, chat_router, query_router
from routers.query_router import auth_router
from db import engine, Base
from models.schema import User, GuaCase, ChatMessage, KnowledgeCase, RiskLog

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI六爻在线问卦平台",
    description="传统六爻民俗文化参考平台",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gua_router.router)
app.include_router(analyze_router.router)
app.include_router(chat_router.router)
app.include_router(query_router.router)
app.include_router(auth_router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "liuyi-platform"}

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

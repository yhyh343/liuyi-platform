"""
全局配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@127.0.0.1:7897/liuyi"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # JWT
    SECRET_KEY: str = "liuyi-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # 风控
    SIMILARITY_THRESHOLD_REPEAT: float = 0.88
    RAG_SIMILARITY_THRESHOLD: float = 0.75
    RAG_TOP_K: int = 5
    
    # 合规词库
    ABSOLUTE_WORDS: list[str] = [
        "一定", "必定", "绝对", "命中注定", "精准", "必然",
        "注定", "肯定", "毫无疑问", "天定", "铁定", "肯定能"
    ]
    
    # 拦截类目
    BLOCKED_CATEGORIES: list[str] = [
        "生死祸福", "疾病诊疗", "赌博彩票", "违法违规", 
        "封建宿命", "情感操控"
    ]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

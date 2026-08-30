"""
RAG 知识库服务
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.schema import KnowledgeCase
from config import settings


class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self._use_mock = not settings.OPENAI_API_KEY or not settings.EMBEDDING_MODEL

    def embed_text(self, text: str) -> List[float]:
        """生成文本嵌入向量（mock模式返回零向量）"""
        if self._use_mock:
            return [0.0] * 1536
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception:
            return [0.0] * 1536

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相关知识库条目"""
        if self._use_mock:
            return []
        try:
            query_embedding = self.embed_text(query)
            # Simple cosine similarity search
            cases = self.db.query(KnowledgeCase).all()
            results = []
            for case in cases:
                if case.embedding:
                    # Simple dot product as similarity
                    sim = sum(a * b for a, b in zip(query_embedding, case.embedding))
                    results.append({
                        "source": case.source,
                        "title": case.title,
                        "content": case.content,
                        "similarity": sim
                    })
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
        except Exception:
            return []

# -*- coding: utf-8 -*-
import json
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session
from models.schema import KnowledgeCase
from config import settings
import openai


class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self._use_mock = not settings.OPENAI_API_KEY
        if not self._use_mock:
            self.client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )

    def embed_text(self, text: str) -> List[float]:
        if self._use_mock:
            import hashlib
            h = hashlib.sha256(text.encode()).digest()
            vec = list(h[:1536])
            return [v / 127.0 - 1.0 for v in vec]
        response = self.client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    def add_knowledge(self, title: str, content: str, category: str, source: str, quality_score: float = 0.0):
        embedding = self.embed_text(title + ': ' + content)
        emb_str = json.dumps(embedding)
        case = KnowledgeCase(
            title=title,
            content=content,
            category=category,
            source=source,
            quality_score=quality_score,
            embedding=emb_str
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def search(self, query: str, category: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.embed_text(query)
        query_vec = np.array(query_embedding, dtype=np.float32)
        cases = self.db.query(KnowledgeCase)
        if category:
            cases = cases.filter(KnowledgeCase.category == category)
        cases = cases.all()
        results = []
        for case in cases:
            if not case.embedding:
                continue
            try:
                case_emb = json.loads(case.embedding)
            except (json.JSONDecodeError, TypeError):
                continue
            case_vec = np.array(case_emb, dtype=np.float32)
            similarity = float(np.dot(query_vec, case_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(case_vec) + 1e-8
            ))
            if similarity >= settings.RAG_SIMILARITY_THRESHOLD:
                results.append({
                    'id': str(case.id),
                    'title': case.title,
                    'content': case.content,
                    'category': case.category,
                    'source': case.source,
                    'similarity': round(similarity, 4),
                    'quality_score': case.quality_score
                })
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]

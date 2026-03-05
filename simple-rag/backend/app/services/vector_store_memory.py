"""
内存向量存储：FAISS 仅存内存，不落盘（进程重启后数据清空）
"""
import uuid
from typing import List, Dict, Optional

from app.core.logger import app_logger
from app.services.embedding_service import get_embeddings


def _to_safe_metadata(m: Dict) -> Dict:
    return {k: (v if isinstance(v, (str, int, float, bool)) else str(v)) for k, v in (m or {}).items()}


def _docs_to_result(docs_with_scores: List, score_higher_better: bool = True) -> List[Dict]:
    out = []
    for doc, score in docs_with_scores:
        content = getattr(doc, "page_content", None) or (doc if isinstance(doc, str) else "")
        meta = getattr(doc, "metadata", None) or {}
        s = float(score) if score is not None else 0.0
        if not score_higher_better and s > 0:
            s = 1.0 / (1.0 + s)
        out.append({"content": content, "metadata": meta, "score": s})
    return out


class InMemoryVectorStore:
    """内存向量存储：FAISS 在内存中，不落盘。"""

    def __init__(self, collection_name: str = "rag_knowledge"):
        self.collection_name = collection_name
        self._embeddings = get_embeddings()
        self._store = None
        app_logger.info(f"内存向量库已创建: collection={collection_name}")

    def clear(self):
        self._store = None

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        if not texts:
            return []
        ids = ids or [str(uuid.uuid4()) for _ in texts]
        metadatas = metadatas or [{} for _ in texts]
        safe_metas = [_to_safe_metadata(m) for m in metadatas]
        from langchain_community.vectorstores import FAISS
        if self._store is None:
            self._store = FAISS.from_texts(texts, self._embeddings, metadatas=safe_metas)
        else:
            self._store.add_texts(texts, metadatas=safe_metas, ids=ids)
        app_logger.info(f"内存向量库写入 {len(texts)} 条")
        return ids

    def similarity_search(self, query: str, k: int = 10) -> List[Dict]:
        if not query or not query.strip():
            return []
        if self._store is None:
            return []
        docs_with_scores = self._store.similarity_search_with_score(query, k=k)
        return _docs_to_result(docs_with_scores, score_higher_better=False)

    def count(self) -> int:
        if self._store is None:
            return 0
        try:
            return len(self._store.docstore._dict)
        except Exception:
            return 0


_memory_store: Optional[InMemoryVectorStore] = None


def get_memory_vector_store(collection_name: str = "rag_knowledge") -> InMemoryVectorStore:
    global _memory_store
    if _memory_store is None:
        _memory_store = InMemoryVectorStore(collection_name=collection_name)
    return _memory_store

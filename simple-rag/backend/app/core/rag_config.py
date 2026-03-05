"""
RAG 流水线配置：召回数量、重排数量、分片等
"""
import os
from typing import Optional
from dotenv import load_dotenv
from app.core.logger import app_logger

load_dotenv()


class RAGConfig:
    """RAG 检索与重排配置"""

    def __init__(self):
        self.top_k_recall = int(os.getenv("RAG_TOP_K_RECALL", "10"))
        self.top_n_rerank = int(os.getenv("RAG_TOP_N_RERANK", "3"))
        self.chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "500"))
        self.chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))

        self._validate()
        app_logger.info(
            f"RAG 配置: top_k_recall={self.top_k_recall}, "
            f"top_n_rerank={self.top_n_rerank}, chunk_size={self.chunk_size}"
        )

    def _validate(self):
        if self.top_k_recall < 1:
            self.top_k_recall = 10
        if self.top_n_rerank < 1 or self.top_n_rerank > self.top_k_recall:
            self.top_n_rerank = min(3, self.top_k_recall)


_rag_config: Optional[RAGConfig] = None


def get_rag_config() -> RAGConfig:
    global _rag_config
    if _rag_config is None:
        _rag_config = RAGConfig()
    return _rag_config

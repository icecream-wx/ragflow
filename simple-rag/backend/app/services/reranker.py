"""
重排服务：按向量相似度 score 取 top_n
"""
from typing import List, Dict
from app.core.logger import app_logger


def rerank_chunks(
    chunks: List[Dict],
    query: str,
    top_n: int = 3
) -> List[Dict]:
    """对召回的片段按 score 排序，取 top_n 条。"""
    if not chunks:
        return []
    sorted_chunks = sorted(chunks, key=lambda x: x.get("score") or 0, reverse=True)
    result = sorted_chunks[:top_n]
    app_logger.info(f"重排完成: 召回 {len(chunks)} 条 -> top_n {len(result)}")
    return result

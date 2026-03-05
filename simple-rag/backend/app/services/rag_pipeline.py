"""
RAG 流水线：用户提问 -> 向量库召回 top_k -> 重排 top_n -> 拼成参考内容
知识库数据由「本地上传」时解析、分片、向量化写入内存向量库。
"""
from app.core.logger import app_logger
from app.core.rag_config import get_rag_config
from app.services.vector_store_memory import get_memory_vector_store
from app.services.reranker import rerank_chunks
from app.utils.text_utils import build_context_from_chunks


def run_rag_retrieve(query: str) -> str:
    """执行 RAG 检索：内存向量库召回 -> 重排 -> 拼成参考内容。"""
    cfg = get_rag_config()
    store = get_memory_vector_store()
    recalled = store.similarity_search(query, k=cfg.top_k_recall)
    if not recalled:
        app_logger.info("向量库未召回到相关片段（可能知识库为空或与问题无关）")
        return ""
    top_chunks = rerank_chunks(recalled, query, top_n=cfg.top_n_rerank)
    context = build_context_from_chunks(top_chunks, prefix="参考内容")
    return context

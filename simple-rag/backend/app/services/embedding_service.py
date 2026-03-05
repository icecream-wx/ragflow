"""
嵌入服务：文本向量化，供向量检索与存储使用
支持本地 sentence-transformers 或外部 OpenAI 兼容嵌入 API
"""
import os
from typing import List
from dotenv import load_dotenv
from app.core.logger import app_logger

load_dotenv()


def _load_embeddings():
    embedding_type = (os.getenv("EMBEDDING_TYPE") or "local").strip().lower()
    if embedding_type == "openai":
        return _load_openai_embeddings()
    return _load_local_embeddings()


def _load_openai_embeddings():
    api_key = (os.getenv("EMBEDDING_API_KEY") or os.getenv("LLM_API_KEY") or "").strip()
    base_url = (os.getenv("EMBEDDING_BASE_URL") or "").strip() or None
    model = (os.getenv("EMBEDDING_MODEL") or "text-embedding-3-small").strip()
    if not api_key:
        raise ValueError("API 嵌入模式下需设置 EMBEDDING_API_KEY（或 LLM_API_KEY）")
    from langchain_openai import OpenAIEmbeddings
    emb = OpenAIEmbeddings(
        openai_api_key=api_key,
        openai_api_base=base_url,
        model=model,
    )
    app_logger.info(f"嵌入 API 已启用: model={model}, base_url={base_url or 'default'}")
    return emb


def _load_local_embeddings():
    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    device = os.getenv("EMBEDDING_DEVICE", "cpu")
    try:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings as HFEmbeddings
            emb = HFEmbeddings(model_name=model_name, model_kwargs={"device": device})
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            emb = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": device}
            )
        app_logger.info(f"本地嵌入模型加载成功: {model_name}")
        return emb
    except ImportError as e:
        raise ImportError(
            "本地嵌入需要安装 sentence-transformers。请使用 API 嵌入（.env 中 EMBEDDING_TYPE=openai）"
            "或安装: poetry install --extras local-embedding"
        ) from e
    except Exception as e:
        app_logger.error(f"嵌入模型加载失败: {e}")
        raise


_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = _load_embeddings()
    return _embeddings


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    return get_embeddings().embed_documents(texts)


def embed_query(query: str) -> List[float]:
    if not query or not query.strip():
        return []
    return get_embeddings().embed_query(query)

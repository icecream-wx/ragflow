"""
文本处理：分片、拼接等
"""
from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: List[str] = None
) -> List[str]:
    """
    将长文本按固定大小分片，支持重叠以避免截断语义。
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    separators = separators or ["\n\n", "\n", "。", ".", " ", ""]
    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        segment = text[start:end]
        best_sep_pos = -1
        for sep in separators:
            if not sep:
                best_sep_pos = end - start
                break
            pos = segment.rfind(sep)
            if pos != -1:
                best_sep_pos = pos
                break

        if best_sep_pos <= 0:
            best_sep_pos = chunk_size

        chunk = text[start : start + best_sep_pos].strip()
        if chunk:
            chunks.append(chunk)

        start += best_sep_pos - chunk_overlap
        if start < 0:
            start = 0

    return chunks


def build_context_from_chunks(chunks: List[dict], prefix: str = "参考内容") -> str:
    """将检索/重排后的片段拼成送入 LLM 的上下文字符串。"""
    if not chunks:
        return ""

    parts = [f"【{prefix}】"]
    for i, item in enumerate(chunks, 1):
        content = item.get("content") or item.get("text") or str(item)
        if isinstance(content, dict):
            content = content.get("content") or content.get("text") or ""
        parts.append(f"[{i}]\n{content.strip()}")
    return "\n\n".join(parts)

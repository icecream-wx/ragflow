"""
知识分块策略：本项目支持的分块策略定义与说明。
"""
from typing import List, Dict, Any

# 策略 id -> 分隔符列表（按优先级，先尝试段落再句子再词再字符）
CHUNK_STRATEGY_SEPARATORS: Dict[str, List[str]] = {
    "recursive": ["\n\n", "\n", "。", "！", "？", ".", " ", ""],
    "paragraph": ["\n\n", "\n", ""],
    "sentence": ["。", "！", "？", "\n", ".", "! ", "? ", " ", ""],
    "fixed": [""],
}

# 策略 id -> 展示名称与描述（供 API / 前端列举）
CHUNK_STRATEGIES: List[Dict[str, Any]] = [
    {
        "id": "recursive",
        "name": "递归分段（推荐）",
        "description": "优先按段落、换行、句号分片，兼顾中英文，适合通用文档。",
    },
    {
        "id": "paragraph",
        "name": "段落优先",
        "description": "优先按双换行、单换行分片，适合以段落为主的长文。",
    },
    {
        "id": "sentence",
        "name": "句子优先",
        "description": "优先按句号、问号、感叹号分片，适合问答、对话类文本。",
    },
    {
        "id": "fixed",
        "name": "固定长度",
        "description": "严格按字符数切分，不寻找分隔符，适合无标点或代码类文本。",
    },
]


def get_supported_strategy_ids() -> List[str]:
    """返回当前支持的分块策略 id 列表。"""
    return list(CHUNK_STRATEGY_SEPARATORS.keys())


def get_separators_for_strategy(strategy_id: str) -> List[str]:
    """根据策略 id 返回分隔符列表，无效时退回 recursive。"""
    if strategy_id in CHUNK_STRATEGY_SEPARATORS:
        return CHUNK_STRATEGY_SEPARATORS[strategy_id]
    return CHUNK_STRATEGY_SEPARATORS["recursive"]

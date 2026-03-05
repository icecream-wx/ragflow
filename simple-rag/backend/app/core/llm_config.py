"""
LLM 配置模块
"""
import os
from typing import Optional
from dotenv import load_dotenv
from app.core.logger import app_logger

load_dotenv()


class LLMConfig:
    """AI 模型配置类"""

    def __init__(self):
        self.model_type = os.getenv("LLM_MODEL_TYPE", "openai").lower()
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model_name = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")
        self.base_url = (os.getenv("LLM_BASE_URL") or "").strip() or None

        if not self.model_name:
            self.model_name = "gpt-3.5-turbo"

        self._validate()
        app_logger.info(f"LLM 配置: type={self.model_type}, model={self.model_name}")

    def _validate(self):
        if not self.api_key:
            app_logger.warning("API 密钥未设置，部分功能可能不可用")

    def get_api_key(self) -> str:
        return self.api_key

    def get_model_name(self) -> str:
        return self.model_name

    def get_base_url(self) -> Optional[str]:
        return self.base_url if self.base_url else None


_llm_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    global _llm_config
    if _llm_config is None:
        _llm_config = LLMConfig()
    return _llm_config

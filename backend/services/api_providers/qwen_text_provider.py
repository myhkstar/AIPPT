"""
通义千问文本生成提供商
"""
import logging
from .base import BaseTextProvider, ProviderError, ProviderAPIError
from .qwen_provider import QwenProvider

logger = logging.getLogger(__name__)

class QwenTextProvider(BaseTextProvider):
    """通义千问文本生成提供商"""
    
    def __init__(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.qwen = QwenProvider(api_key, base_url)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        try:
            return self.qwen.generate_text(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Qwen text generation failed: {str(e)}")
            raise ProviderAPIError(f"Qwen text generation failed: {str(e)}") from e
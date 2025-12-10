"""
百度文心一言文本生成提供商
"""
import logging
from .base import BaseTextProvider, ProviderError, ProviderAPIError, ProviderConfigError
from .baidu_provider import BaiduProvider

logger = logging.getLogger(__name__)

class BaiduTextProvider(BaseTextProvider):
    """百度文心一言文本生成提供商"""
    
    def __init__(self, api_key: str, base_url: str = "https://aip.baidubce.com", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        secret_key = kwargs.get('secret_key', '')
        if not secret_key:
            raise ProviderConfigError("Baidu provider requires secret_key parameter")
        self.baidu = BaiduProvider(api_key, secret_key, base_url)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        try:
            return self.baidu.generate_text(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Baidu text generation failed: {str(e)}")
            raise ProviderAPIError(f"Baidu text generation failed: {str(e)}") from e
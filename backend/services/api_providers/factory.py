"""
API Provider Factory
"""
import logging
from typing import Dict, Type, Optional, List

from .base import BaseTextProvider, BaseImageProvider, ProviderConfigError

logger = logging.getLogger(__name__)

# 尝试导入各个提供商，如果失败则跳过
try:
    from .google_provider import GoogleTextProvider, GoogleImageProvider
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    GoogleTextProvider = None
    GoogleImageProvider = None

try:
    from .openai_provider import OpenAITextProvider, OpenAIImageProvider
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAITextProvider = None
    OpenAIImageProvider = None

try:
    from .jimeng_provider import JimengImageProvider
    JIMENG_AVAILABLE = True
except ImportError:
    JIMENG_AVAILABLE = False
    JimengImageProvider = None

try:
    from .qwen_text_provider import QwenTextProvider
    from .qwen_image_provider import QwenImageProvider
    QWEN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Qwen providers not available: {e}")
    QWEN_AVAILABLE = False
    QwenTextProvider = None
    QwenImageProvider = None

try:
    from .baidu_text_provider import BaiduTextProvider
    from .baidu_image_provider import BaiduImageProvider
    BAIDU_AVAILABLE = True
except ImportError:
    BAIDU_AVAILABLE = False
    BaiduTextProvider = None
    BaiduImageProvider = None

try:
    from .openai_compatible_provider import OpenAICompatibleTextProvider, OpenAICompatibleImageProvider
    OPENAI_COMPATIBLE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenAI Compatible providers not available: {e}")
    OPENAI_COMPATIBLE_AVAILABLE = False
    OpenAICompatibleTextProvider = None
    OpenAICompatibleImageProvider = None

logger = logging.getLogger(__name__)

# Provider registry - 只注册可用的提供商
TEXT_PROVIDERS: Dict[str, Type[BaseTextProvider]] = {}
IMAGE_PROVIDERS: Dict[str, Type[BaseImageProvider]] = {}

# 动态注册可用的提供商
if GOOGLE_AVAILABLE:
    TEXT_PROVIDERS['google'] = GoogleTextProvider
    IMAGE_PROVIDERS['google'] = GoogleImageProvider

if OPENAI_AVAILABLE:
    TEXT_PROVIDERS['openai'] = OpenAITextProvider
    IMAGE_PROVIDERS['openai'] = OpenAIImageProvider

if JIMENG_AVAILABLE:
    IMAGE_PROVIDERS['jimeng'] = JimengImageProvider

if QWEN_AVAILABLE:
    TEXT_PROVIDERS['qwen'] = QwenTextProvider
    IMAGE_PROVIDERS['qwen'] = QwenImageProvider

if BAIDU_AVAILABLE:
    TEXT_PROVIDERS['baidu'] = BaiduTextProvider
    IMAGE_PROVIDERS['baidu'] = BaiduImageProvider

if OPENAI_COMPATIBLE_AVAILABLE:
    TEXT_PROVIDERS['openai_compatible'] = OpenAICompatibleTextProvider
    IMAGE_PROVIDERS['openai_compatible'] = OpenAICompatibleImageProvider


class ProviderFactory:
    """Factory for creating API providers"""
    
    @staticmethod
    def create_text_provider(provider_type: str, api_key: str, 
                           base_url: Optional[str] = None, **kwargs) -> BaseTextProvider:
        """Create a text provider instance"""
        if not api_key:
            raise ProviderConfigError(f"API key is required for {provider_type}")
        
        if provider_type not in TEXT_PROVIDERS:
            raise ProviderConfigError(f"Unknown text provider: {provider_type}")
        
        provider_class = TEXT_PROVIDERS[provider_type]
        
        try:
            # Handle secretKey -> secret_key mapping for Baidu
            if 'secretKey' in kwargs:
                kwargs['secret_key'] = kwargs.pop('secretKey')
            
            # Handle enableThinking -> enable_thinking mapping for OpenAI Compatible
            if 'enableThinking' in kwargs:
                kwargs['enable_thinking'] = kwargs.pop('enableThinking')
            
            return provider_class(api_key=api_key, base_url=base_url, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create text provider {provider_type}: {str(e)}")
            raise ProviderConfigError(f"Failed to initialize {provider_type}: {str(e)}") from e
    
    @staticmethod
    def create_image_provider(provider_type: str, api_key: str,
                            base_url: Optional[str] = None, **kwargs) -> BaseImageProvider:
        """Create an image provider instance"""
        if not api_key:
            raise ProviderConfigError(f"API key is required for {provider_type}")
        
        if provider_type not in IMAGE_PROVIDERS:
            raise ProviderConfigError(f"Unknown image provider: {provider_type}")
        
        provider_class = IMAGE_PROVIDERS[provider_type]
        
        try:
            # Handle secretKey -> secret_key mapping for Baidu
            if 'secretKey' in kwargs:
                kwargs['secret_key'] = kwargs.pop('secretKey')
            
            return provider_class(api_key=api_key, base_url=base_url, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create image provider {provider_type}: {str(e)}")
            raise ProviderConfigError(f"Failed to initialize {provider_type}: {str(e)}") from e
    
    @staticmethod
    def get_available_text_providers() -> list:
        """Get list of available text providers"""
        return list(TEXT_PROVIDERS.keys())
    
    @staticmethod
    def get_available_image_providers() -> list:
        """Get list of available image providers"""
        return list(IMAGE_PROVIDERS.keys())
    
    @staticmethod
    def validate_provider_config(provider_type: str, config: dict, is_image: bool = False) -> bool:
        """Validate provider configuration"""
        providers = IMAGE_PROVIDERS if is_image else TEXT_PROVIDERS
        
        if provider_type not in providers:
            return False
        
        # Basic validation - API key is required
        if not config.get('api_key'):
            return False
        
        return True
    
    @staticmethod
    def get_provider_models(provider_type: str) -> Dict[str, List[str]]:
        """Get supported models for a specific provider"""
        models = {"text": [], "image": []}
        
        # 预定义的模型列表
        predefined_models = {
            "google": {
                "text": ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
                "image": ["gemini-3-pro-image-preview", "imagen-3.0-generate-001", "imagen-2.0"]
            },
            "openai": {
                "text": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "image": ["dall-e-3", "dall-e-2"]
            },
            "anthropic": {
                "text": ["claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-opus-20240229"],
                "image": []
            },
            "qwen": {
                "text": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long", "qwen2.5-72b-instruct", "qwen2.5-32b-instruct"],
                "image": ["qwen-vl-plus", "qwen-vl-max"]
            },
            "baidu": {
                "text": ["ernie-4.0-8k", "ernie-3.5-8k", "ernie-turbo-8k", "ernie-speed-8k", "ernie-lite-8k"],
                "image": ["stable-diffusion-xl", "stable-diffusion-v1.5"]
            },
            "openai_compatible": {
                "text": ["deepseek-v3.2", "deepseek-chat", "glm-4-plus", "glm-4-0520", "moonshot-v1-8k", "moonshot-v1-32k"],
                "image": ["flux-pro-1.1", "flux-dev", "flux-schnell", "stable-diffusion-3-large"]
            },
            "jimeng": {
                "text": [],
                "image": ["jimeng-v1", "jimeng-pro"]
            }
        }
        
        if provider_type in predefined_models:
            models = predefined_models[provider_type]
        
        return models
"""
Base classes for API providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union
from PIL import Image


class BaseTextProvider(ABC):
    """Base class for text generation providers"""
    
    def __init__(self, api_key: str, base_url: str = None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported models for this provider"""
        return []


class BaseImageProvider(ABC):
    """Base class for image generation providers"""
    
    def __init__(self, api_key: str, base_url: str = None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
    
    @abstractmethod
    def generate_image(self, prompt: str, ref_image: Optional[Image.Image] = None, 
                      additional_ref_images: Optional[List[Union[str, Image.Image]]] = None,
                      **kwargs) -> Optional[Image.Image]:
        """Generate image from prompt"""
        pass
    
    @abstractmethod
    def edit_image(self, prompt: str, current_image: Image.Image,
                  original_description: str = None,
                  additional_ref_images: Optional[List[Union[str, Image.Image]]] = None,
                  **kwargs) -> Optional[Image.Image]:
        """Edit existing image with instruction"""
        pass
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported models for this provider"""
        return []


class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class ProviderConfigError(ProviderError):
    """Configuration error for providers"""
    pass


class ProviderAPIError(ProviderError):
    """API error for providers"""
    pass
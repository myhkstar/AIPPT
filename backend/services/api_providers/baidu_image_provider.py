"""
百度文心一格图像生成提供商
"""
import logging
import requests
from PIL import Image
from io import BytesIO
from typing import List, Optional, Union
from .base import BaseImageProvider, ProviderError, ProviderAPIError, ProviderConfigError
from .baidu_provider import BaiduProvider

logger = logging.getLogger(__name__)

class BaiduImageProvider(BaseImageProvider):
    """百度文心一格图像生成提供商"""
    
    def __init__(self, api_key: str, base_url: str = "https://aip.baidubce.com", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        secret_key = kwargs.get('secret_key', '')
        if not secret_key:
            raise ProviderConfigError("Baidu provider requires secret_key parameter")
        self.baidu = BaiduProvider(api_key, secret_key, base_url)
    
    def generate_image(self, prompt: str, ref_image: Optional[Image.Image] = None, 
                      additional_ref_images: Optional[List[Union[str, Image.Image]]] = None,
                      **kwargs) -> Optional[Image.Image]:
        """生成图像"""
        try:
            # 调用百度图像生成
            image_url = self.baidu.generate_image(prompt, **kwargs)
            
            # 下载图像
            if image_url.startswith('data:image'):
                # 处理base64图像
                import base64
                header, data = image_url.split(',', 1)
                image_data = base64.b64decode(data)
                return Image.open(BytesIO(image_data))
            else:
                # 下载URL图像
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
                
        except Exception as e:
            logger.error(f"Baidu image generation failed: {str(e)}")
            raise ProviderAPIError(f"Baidu image generation failed: {str(e)}") from e
    
    def edit_image(self, prompt: str, current_image: Image.Image,
                  original_description: str = None,
                  additional_ref_images: Optional[List[Union[str, Image.Image]]] = None,
                  **kwargs) -> Optional[Image.Image]:
        """编辑图像"""
        try:
            # 调用百度图像编辑
            image_url = self.baidu.edit_image(prompt, current_image, **kwargs)
            
            # 下载编辑后的图像
            if image_url.startswith('data:image'):
                import base64
                header, data = image_url.split(',', 1)
                image_data = base64.b64decode(data)
                return Image.open(BytesIO(image_data))
            else:
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
                
        except Exception as e:
            logger.error(f"Baidu image edit failed: {str(e)}")
            raise ProviderAPIError(f"Baidu image edit failed: {str(e)}") from e
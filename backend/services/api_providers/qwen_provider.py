"""
阿里云通义千问 API 提供商
支持文本生成和图像生成
"""
import os
import logging
from typing import Dict, Any, Optional, List
from PIL import Image
import requests
from openai import OpenAI

from .base import BaseTextProvider, BaseImageProvider, ProviderError, ProviderAPIError

logger = logging.getLogger(__name__)

class QwenProvider:
    """阿里云通义千问 API 提供商 - 共享基础功能"""
    
    def __init__(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def generate_text(
        self,
        prompt: str,
        model: str = "qwen-max",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """生成文本内容"""
        try:
            logger.info(f"Qwen text generation request: model={model}, prompt_length={len(prompt)}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for creating PPT content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ProviderAPIError("Qwen API returned empty content")
            
            logger.info(f"Qwen text generation successful: response_length={len(content)}")
            return content.strip()
            
        except Exception as e:
            logger.error(f"Qwen text generation error: {str(e)}")
            raise ProviderAPIError(f"Qwen API error: {str(e)}") from e

    def generate_image(
        self,
        prompt: str,
        model: str = "qwen-vl-plus",
        size: str = "1024x1024",
        quality: str = "standard",
        **kwargs
    ) -> str:
        """生成图像
        
        注意：通义千问的图像生成需要使用专门的API，这里提供基础框架
        实际使用时可能需要调用阿里云的图像生成服务
        """
        try:
            logger.info(f"Qwen image generation request: model={model}, prompt_length={len(prompt)}")
            
            # 通义千问图像生成的具体实现
            # 这里需要根据阿里云的实际API进行调整
            response = self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
                **kwargs
            )
            
            if not response.data or len(response.data) == 0:
                raise ProviderAPIError("Qwen image API returned no images")
            
            image_url = response.data[0].url
            if not image_url:
                raise ProviderAPIError("Qwen image API returned empty URL")
            
            logger.info(f"Qwen image generation successful: url={image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"Qwen image generation error: {str(e)}")
            raise ProviderAPIError(f"Qwen API error: {str(e)}") from e
    
    def edit_image(
        self,
        prompt: str,
        current_image: Image.Image,
        model: str = "qwen-vl-plus",
        **kwargs
    ) -> str:
        """编辑图像"""
        try:
            logger.info(f"Qwen image edit request: model={model}, prompt_length={len(prompt)}")
            
            # 将PIL图像转换为base64或临时文件
            # 具体实现取决于阿里云API的要求
            
            # 这里是示例实现，需要根据实际API调整
            response = self.client.images.edit(
                image=current_image,
                prompt=prompt,
                model=model,
                **kwargs
            )
            
            if not response.data or len(response.data) == 0:
                raise ProviderAPIError("Qwen image edit API returned no images")
            
            image_url = response.data[0].url
            logger.info(f"Qwen image edit successful: url={image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"Qwen image edit error: {str(e)}")
            raise ProviderAPIError(f"Qwen API error: {str(e)}") from e

    def get_models(self) -> Dict[str, List[str]]:
        """获取支持的模型列表"""
        return {
            "text": [
                "qwen-max",
                "qwen-plus", 
                "qwen-turbo",
                "qwen-long",
                "qwen2.5-72b-instruct",
                "qwen2.5-32b-instruct",
                "qwen2.5-14b-instruct",
                "qwen2.5-7b-instruct"
            ],
            "image": [
                "qwen-vl-plus",
                "qwen-vl-max"
            ]
        }
    
    def validate_config(self) -> bool:
        """验证API配置"""
        try:
            # 测试文本生成
            response = self.client.chat.completions.create(
                model="qwen-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Qwen config validation failed: {str(e)}")
            return False
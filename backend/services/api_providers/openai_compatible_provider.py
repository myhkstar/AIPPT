"""
OpenAI兼容API提供商
支持所有使用OpenAI兼容接口的模型，如DeepSeek、阿里云百炼等
"""
import logging
from typing import Dict, Any, Optional, List
from PIL import Image
import requests
from openai import OpenAI

from .base import BaseTextProvider, BaseImageProvider, ProviderError, ProviderAPIError

logger = logging.getLogger(__name__)

class OpenAICompatibleTextProvider(BaseTextProvider):
    """OpenAI兼容文本生成提供商"""
    
    def __init__(self, api_key: str, base_url: str, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = kwargs.get('model', 'gpt-3.5-turbo')
        self.max_tokens = kwargs.get('max_tokens', 4000)
        self.temperature = kwargs.get('temperature', 0.7)
        self.enable_thinking = kwargs.get('enable_thinking', False)  # 支持思考模式（如DeepSeek）
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本内容"""
        try:
            model = kwargs.get('model', self.model)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)
            temperature = kwargs.get('temperature', self.temperature)
            enable_thinking = kwargs.get('enable_thinking', self.enable_thinking)
            
            logger.info(f"OpenAI Compatible text generation: model={model}, prompt_length={len(prompt)}")
            
            # 构建请求参数
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant for creating PPT content."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **{k: v for k, v in kwargs.items() if k not in ['model', 'max_tokens', 'temperature', 'enable_thinking']}
            }
            
            # 如果支持思考模式（如DeepSeek），添加extra_body参数
            if enable_thinking:
                request_params["extra_body"] = {"enable_thinking": True}
            
            response = self.client.chat.completions.create(**request_params)
            
            content = response.choices[0].message.content
            if not content:
                raise ProviderAPIError("OpenAI Compatible API returned empty content")
            
            logger.info(f"OpenAI Compatible text generation successful: response_length={len(content)}")
            return content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI Compatible text generation error: {str(e)}")
            raise ProviderAPIError(f"OpenAI Compatible API error: {str(e)}") from e


class OpenAICompatibleImageProvider(BaseImageProvider):
    """OpenAI兼容图像生成提供商"""
    
    def __init__(self, api_key: str, base_url: str, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = kwargs.get('model', 'dall-e-3')
    
    def generate_image(self, prompt: str, ref_image: Optional[Image.Image] = None, 
                      additional_ref_images: Optional[List] = None, **kwargs) -> Optional[Image.Image]:
        """生成图像"""
        try:
            model = kwargs.get('model', self.model)
            size = kwargs.get('size', '1024x1024')
            quality = kwargs.get('quality', 'standard')
            
            logger.info(f"OpenAI Compatible image generation: model={model}, prompt_length={len(prompt)}")
            
            response = self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
                **{k: v for k, v in kwargs.items() if k not in ['model', 'size', 'quality']}
            )
            
            if not response.data or len(response.data) == 0:
                raise ProviderAPIError("OpenAI Compatible image API returned no images")
            
            image_url = response.data[0].url
            if not image_url:
                raise ProviderAPIError("OpenAI Compatible image API returned empty URL")
            
            # 下载图像
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            
            from io import BytesIO
            image = Image.open(BytesIO(img_response.content))
            
            logger.info(f"OpenAI Compatible image generation successful")
            return image
            
        except Exception as e:
            logger.error(f"OpenAI Compatible image generation error: {str(e)}")
            raise ProviderAPIError(f"OpenAI Compatible API error: {str(e)}") from e
    
    def edit_image(self, prompt: str, current_image: Image.Image,
                  original_description: str = None, additional_ref_images: Optional[List] = None,
                  **kwargs) -> Optional[Image.Image]:
        """编辑图像"""
        try:
            model = kwargs.get('model', self.model)
            
            logger.info(f"OpenAI Compatible image edit: model={model}, prompt_length={len(prompt)}")
            
            # 将PIL图像转换为临时文件
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                current_image.save(tmp_file.name, 'PNG')
                
                with open(tmp_file.name, 'rb') as image_file:
                    response = self.client.images.edit(
                        image=image_file,
                        prompt=prompt,
                        model=model,
                        **{k: v for k, v in kwargs.items() if k not in ['model']}
                    )
                
                # 清理临时文件
                os.unlink(tmp_file.name)
            
            if not response.data or len(response.data) == 0:
                raise ProviderAPIError("OpenAI Compatible image edit API returned no images")
            
            image_url = response.data[0].url
            
            # 下载编辑后的图像
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            
            from io import BytesIO
            edited_image = Image.open(BytesIO(img_response.content))
            
            logger.info(f"OpenAI Compatible image edit successful")
            return edited_image
            
        except Exception as e:
            logger.error(f"OpenAI Compatible image edit error: {str(e)}")
            raise ProviderAPIError(f"OpenAI Compatible API error: {str(e)}") from e
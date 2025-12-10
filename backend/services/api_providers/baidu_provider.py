"""
百度文心一言 API 提供商
支持文本生成和图像生成
"""
import os
import logging
import json
import requests
from typing import Dict, Any, Optional, List
from PIL import Image
import base64
import io

from .base import BaseTextProvider, BaseImageProvider, ProviderError, ProviderAPIError

logger = logging.getLogger(__name__)

class BaiduProvider:
    """百度文心一言 API 提供商 - 共享基础功能"""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str = "https://aip.baidubce.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.secret_key = secret_key
        self.access_token = None
    
    def _get_access_token(self) -> str:
        """获取访问令牌"""
        if self.access_token:
            return self.access_token
            
        try:
            url = f"{self.base_url}/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key
            }
            
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            self.access_token = result.get("access_token")
            
            if not self.access_token:
                raise ProviderAPIError("Failed to get Baidu access token")
            
            return self.access_token
            
        except Exception as e:
            logger.error(f"Baidu access token error: {str(e)}")
            raise ProviderAPIError(f"Baidu auth error: {str(e)}") from e
    
    def generate_text(
        self,
        prompt: str,
        model: str = "ernie-4.0-8k",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """生成文本内容"""
        try:
            logger.info(f"Baidu text generation request: model={model}, prompt_length={len(prompt)}")
            
            access_token = self._get_access_token()
            
            # 根据模型选择对应的API端点
            model_endpoints = {
                "ernie-4.0-8k": "completions_pro",
                "ernie-3.5-8k": "completions",
                "ernie-turbo-8k": "eb-instant",
                "ernie-speed-8k": "ernie_speed",
                "ernie-lite-8k": "ernie-lite-8k"
            }
            
            endpoint = model_endpoints.get(model, "completions_pro")
            url = f"{self.base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{endpoint}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_output_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
            
            response = requests.post(
                url,
                headers=headers,
                params={"access_token": access_token},
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error_code" in result:
                raise ProviderAPIError(f"Baidu API error: {result.get('error_msg', 'Unknown error')}")
            
            content = result.get("result")
            if not content:
                raise ProviderAPIError("Baidu API returned empty content")
            
            logger.info(f"Baidu text generation successful: response_length={len(content)}")
            return content.strip()
            
        except Exception as e:
            logger.error(f"Baidu text generation error: {str(e)}")
            raise ProviderAPIError(f"Baidu API error: {str(e)}") from e

    def generate_image(
        self,
        prompt: str,
        model: str = "stable-diffusion-xl",
        size: str = "1024x1024",
        quality: str = "standard",
        **kwargs
    ) -> str:
        """生成图像"""
        try:
            logger.info(f"Baidu image generation request: model={model}, prompt_length={len(prompt)}")
            
            access_token = self._get_access_token()
            
            # 文心一格图像生成API
            url = f"{self.base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/{model}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # 解析尺寸
            width, height = size.split('x')
            
            data = {
                "prompt": prompt,
                "width": int(width),
                "height": int(height),
                "image_num": 1,
                **kwargs
            }
            
            response = requests.post(
                url,
                headers=headers,
                params={"access_token": access_token},
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error_code" in result:
                raise ProviderAPIError(f"Baidu image API error: {result.get('error_msg', 'Unknown error')}")
            
            images = result.get("data", [])
            if not images:
                raise ProviderAPIError("Baidu image API returned no images")
            
            # 返回第一张图片的base64数据或URL
            image_data = images[0]
            if "b64_image" in image_data:
                # 如果返回base64，需要转换为URL或保存为文件
                return f"data:image/png;base64,{image_data['b64_image']}"
            elif "url" in image_data:
                return image_data["url"]
            else:
                raise ProviderAPIError("Baidu image API returned invalid image data")
            
        except Exception as e:
            logger.error(f"Baidu image generation error: {str(e)}")
            raise ProviderAPIError(f"Baidu API error: {str(e)}") from e
    
    def edit_image(
        self,
        prompt: str,
        current_image: Image.Image,
        model: str = "stable-diffusion-xl",
        **kwargs
    ) -> str:
        """编辑图像"""
        try:
            logger.info(f"Baidu image edit request: model={model}, prompt_length={len(prompt)}")
            
            # 将PIL图像转换为base64
            buffer = io.BytesIO()
            current_image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            access_token = self._get_access_token()
            
            url = f"{self.base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/image2image/{model}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "prompt": prompt,
                "image": image_base64,
                "image_num": 1,
                **kwargs
            }
            
            response = requests.post(
                url,
                headers=headers,
                params={"access_token": access_token},
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error_code" in result:
                raise ProviderAPIError(f"Baidu image edit API error: {result.get('error_msg', 'Unknown error')}")
            
            images = result.get("data", [])
            if not images:
                raise ProviderAPIError("Baidu image edit API returned no images")
            
            image_data = images[0]
            if "b64_image" in image_data:
                return f"data:image/png;base64,{image_data['b64_image']}"
            elif "url" in image_data:
                return image_data["url"]
            else:
                raise ProviderAPIError("Baidu image edit API returned invalid image data")
            
        except Exception as e:
            logger.error(f"Baidu image edit error: {str(e)}")
            raise ProviderAPIError(f"Baidu API error: {str(e)}") from e

    def get_models(self) -> Dict[str, List[str]]:
        """获取支持的模型列表"""
        return {
            "text": [
                "ernie-4.0-8k",
                "ernie-3.5-8k", 
                "ernie-turbo-8k",
                "ernie-speed-8k",
                "ernie-lite-8k"
            ],
            "image": [
                "stable-diffusion-xl",
                "stable-diffusion-v1.5"
            ]
        }
    
    def validate_config(self) -> bool:
        """验证API配置"""
        try:
            # 测试获取访问令牌
            access_token = self._get_access_token()
            return bool(access_token)
        except Exception as e:
            logger.error(f"Baidu config validation failed: {str(e)}")
            return False
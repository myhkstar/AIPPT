import type { TextApiConfig, ImageApiConfig } from '@/types/api-config';

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * 验证文本API配置
 */
export const validateTextApiConfig = (config: Partial<TextApiConfig>): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  // 必填字段验证
  if (!config.name?.trim()) {
    errors.push('API名称不能为空');
  }

  if (!config.apiKey?.trim()) {
    errors.push('API密钥不能为空');
  }

  if (!config.provider) {
    errors.push('必须选择API提供商');
  }

  if (!config.model?.trim()) {
    errors.push('模型名称不能为空');
  }

  // 参数范围验证
  if (config.maxTokens !== undefined) {
    if (config.maxTokens < 1 || config.maxTokens > 100000) {
      errors.push('最大Token数应在1-100000之间');
    }
  }

  if (config.temperature !== undefined) {
    if (config.temperature < 0 || config.temperature > 2) {
      errors.push('温度值应在0-2之间');
    }
  }

  // 提供商特定验证
  switch (config.provider) {
    case 'google':
      if (config.apiKey && !config.apiKey.startsWith('AI')) {
        warnings.push('Google API密钥通常以"AI"开头，请确认密钥正确');
      }
      break;
    case 'openai':
      if (config.apiKey && !config.apiKey.startsWith('sk-')) {
        warnings.push('OpenAI API密钥通常以"sk-"开头，请确认密钥正确');
      }
      break;
    case 'anthropic':
      if (config.apiKey && !config.apiKey.startsWith('sk-ant-')) {
        warnings.push('Anthropic API密钥通常以"sk-ant-"开头，请确认密钥正确');
      }
      break;
    case 'qwen':
      if (config.baseUrl && !config.baseUrl.includes('dashscope.aliyuncs.com')) {
        warnings.push('通义千问API的Base URL应为阿里云DashScope地址');
      }
      if (config.apiKey && !config.apiKey.startsWith('sk-')) {
        warnings.push('通义千问API密钥通常以"sk-"开头，请确认密钥正确');
      }
      break;
    case 'baidu':
      if (!config.secretKey?.trim()) {
        errors.push('百度API需要同时提供API Key和Secret Key');
      }
      if (config.baseUrl && !config.baseUrl.includes('baidubce.com')) {
        warnings.push('百度API的Base URL应为百度云地址');
      }
      break;
  }

  // URL格式验证
  if (config.baseUrl && config.baseUrl.trim()) {
    try {
      new URL(config.baseUrl);
    } catch {
      errors.push('Base URL格式不正确');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

/**
 * 验证图像API配置
 */
export const validateImageApiConfig = (config: Partial<ImageApiConfig>): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  // 必填字段验证
  if (!config.name?.trim()) {
    errors.push('API名称不能为空');
  }

  if (!config.apiKey?.trim()) {
    errors.push('API密钥不能为空');
  }

  if (!config.provider) {
    errors.push('必须选择API提供商');
  }

  // 宽高比验证
  if (config.aspectRatio && !['16:9', '4:3', '1:1', '3:4', '9:16'].includes(config.aspectRatio)) {
    warnings.push('建议使用标准宽高比：16:9, 4:3, 1:1, 3:4, 9:16');
  }

  // 分辨率验证
  if (config.resolution) {
    const resolutionPattern = /^\d+x\d+$|^(2K|4K|HD|FHD)$/i;
    if (!resolutionPattern.test(config.resolution)) {
      warnings.push('分辨率格式应为"1024x576"或"2K"等标准格式');
    }
  }

  // 提供商特定验证
  switch (config.provider) {
    case 'google':
      if (config.apiKey && !config.apiKey.startsWith('AI')) {
        warnings.push('Google API密钥通常以"AI"开头，请确认密钥正确');
      }
      break;
    case 'dalle':
      if (config.apiKey && !config.apiKey.startsWith('sk-')) {
        warnings.push('DALL-E API密钥通常以"sk-"开头，请确认密钥正确');
      }
      break;
    case 'jimeng':
      if (config.baseUrl && !config.baseUrl.includes('jimeng')) {
        warnings.push('即梦AI的Base URL应包含"jimeng"');
      }
      break;
    case 'qwen':
      if (config.baseUrl && !config.baseUrl.includes('dashscope.aliyuncs.com')) {
        warnings.push('通义千问API的Base URL应为阿里云DashScope地址');
      }
      if (config.apiKey && !config.apiKey.startsWith('sk-')) {
        warnings.push('通义千问API密钥通常以"sk-"开头，请确认密钥正确');
      }
      break;
    case 'baidu':
      if (!config.secretKey?.trim()) {
        errors.push('百度API需要同时提供API Key和Secret Key');
      }
      if (config.baseUrl && !config.baseUrl.includes('baidubce.com')) {
        warnings.push('百度API的Base URL应为百度云地址');
      }
      break;
  }

  // URL格式验证
  if (config.baseUrl && config.baseUrl.trim()) {
    try {
      new URL(config.baseUrl);
    } catch {
      errors.push('Base URL格式不正确');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

/**
 * 获取API配置建议
 */
export const getApiConfigSuggestions = (provider: string, type: 'text' | 'image') => {
  const suggestions: Record<string, Record<string, any>> = {
    text: {
      google: {
        model: 'gemini-2.5-flash',
        maxTokens: 8192,
        temperature: 0.7,
        tips: '推荐使用gemini-2.5-flash模型，性能和成本平衡较好'
      },
      openai: {
        model: 'gpt-4',
        maxTokens: 4096,
        temperature: 0.7,
        tips: 'GPT-4质量更高但成本较高，可考虑使用gpt-3.5-turbo降低成本'
      },
      anthropic: {
        model: 'claude-3-sonnet-20240229',
        maxTokens: 4096,
        temperature: 0.7,
        tips: 'Claude在长文本处理和推理方面表现优秀'
      },
      qwen: {
        model: 'qwen-max',
        maxTokens: 4000,
        temperature: 0.7,
        tips: '通义千问支持中文对话，适合中文PPT生成'
      },
      baidu: {
        model: 'ernie-4.0-8k',
        maxTokens: 4000,
        temperature: 0.7,
        tips: '文心一言在中文理解方面表现优秀，需要API Key和Secret Key'
      },
      openai_compatible: {
        model: 'deepseek-v3.2',
        maxTokens: 4000,
        temperature: 0.7,
        tips: '支持DeepSeek、智谱AI、月之暗面等OpenAI兼容API，需要提供Base URL'
      }
    },
    image: {
      google: {
        model: 'gemini-3-pro-image-preview',
        aspectRatio: '16:9',
        resolution: '2K',
        tips: 'Google图像生成支持参考图片，适合PPT风格一致性'
      },
      jimeng: {
        model: 'jimeng-v1',
        aspectRatio: '16:9',
        resolution: '1024x576',
        style: 'realistic',
        tips: '即梦AI在中文理解和本土化场景方面表现较好'
      },
      dalle: {
        model: 'dall-e-3',
        resolution: '1792x1024',
        tips: 'DALL-E 3生成质量高，但不支持参考图片'
      },
      qwen: {
        model: 'qwen-vl-plus',
        aspectRatio: '16:9',
        resolution: '1024x1024',
        tips: '通义千问图像生成支持中文提示词，适合中文场景'
      },
      baidu: {
        model: 'stable-diffusion-xl',
        aspectRatio: '16:9',
        resolution: '1024x1024',
        tips: '文心一格支持多种风格，需要API Key和Secret Key'
      },
      openai_compatible: {
        model: 'flux-pro-1.1',
        aspectRatio: '16:9',
        resolution: '1024x1024',
        tips: '支持Flux、Stable Diffusion等OpenAI兼容图像API，需要提供Base URL'
      }
    }
  };

  return suggestions[type]?.[provider] || {};
};

/**
 * 验证OpenAI兼容API配置
 */
export const validateOpenAICompatibleConfig = (config: Partial<TextApiConfig | ImageApiConfig>): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!config.baseUrl?.trim()) {
    errors.push('OpenAI兼容API需要提供Base URL');
  }

  if (config.baseUrl && config.baseUrl.trim()) {
    try {
      new URL(config.baseUrl);
    } catch {
      errors.push('Base URL格式不正确');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};
// API配置相关类型定义

export interface BaseApiConfig {
  id: string;
  name: string;
  type: 'text' | 'image';
  enabled: boolean;
}

export interface TextApiConfig extends BaseApiConfig {
  type: 'text';
  provider: 'google' | 'openai' | 'anthropic' | 'qwen' | 'baidu' | 'openai_compatible' | 'custom';
  apiKey: string;
  baseUrl?: string;
  model: string;
  maxTokens?: number;
  temperature?: number;
  secretKey?: string; // 百度需要的secret key
  enableThinking?: boolean; // 支持思考模式（如DeepSeek）
}

export interface ImageApiConfig extends BaseApiConfig {
  type: 'image';
  provider: 'google' | 'jimeng' | 'midjourney' | 'dalle' | 'stable-diffusion' | 'qwen' | 'baidu' | 'openai_compatible' | 'custom';
  apiKey: string;
  baseUrl?: string;
  model?: string;
  aspectRatio?: string;
  resolution?: string;
  style?: string;
  secretKey?: string; // 百度需要的secret key
}

export type ApiConfig = TextApiConfig | ImageApiConfig;

export interface ApiConfigState {
  textApis: TextApiConfig[];
  imageApis: ImageApiConfig[];
  defaultTextApi: string | null;
  defaultImageApi: string | null;
}

// 预设的API配置模板
export const API_TEMPLATES = {
  text: {
    google: {
      name: 'Google Gemini',
      provider: 'google' as const,
      baseUrl: 'https://generativelanguage.googleapis.com',
      model: 'gemini-2.5-flash',
      maxTokens: 8192,
      temperature: 0.7,
    },
    openai: {
      name: 'OpenAI GPT',
      provider: 'openai' as const,
      baseUrl: 'https://api.openai.com/v1',
      model: 'gpt-4',
      maxTokens: 4096,
      temperature: 0.7,
    },
    anthropic: {
      name: 'Anthropic Claude',
      provider: 'anthropic' as const,
      baseUrl: 'https://api.anthropic.com',
      model: 'claude-3-sonnet-20240229',
      maxTokens: 4096,
      temperature: 0.7,
    },
    qwen: {
      name: '通义千问',
      provider: 'qwen' as const,
      baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      model: 'qwen-max',
      maxTokens: 4000,
      temperature: 0.7,
    },
    baidu: {
      name: '百度文心一言',
      provider: 'baidu' as const,
      baseUrl: 'https://aip.baidubce.com',
      model: 'ernie-4.0-8k',
      maxTokens: 4000,
      temperature: 0.7,
    },
    deepseek: {
      name: 'DeepSeek',
      provider: 'openai_compatible' as const,
      baseUrl: 'https://api.deepseek.com/v1',
      model: 'deepseek-v3.2',
      maxTokens: 4000,
      temperature: 0.7,
      enableThinking: true,
    },
    alibaba_bailian: {
      name: '阿里云百炼',
      provider: 'openai_compatible' as const,
      baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      model: 'qwen-max',
      maxTokens: 4000,
      temperature: 0.7,
    },
  },
  image: {
    google: {
      name: 'Google Gemini Image',
      provider: 'google' as const,
      model: 'gemini-3-pro-image-preview',
      aspectRatio: '16:9',
      resolution: '2K',
    },
    jimeng: {
      name: '即梦AI',
      provider: 'jimeng' as const,
      baseUrl: 'https://api.jimeng.ai',
      model: 'jimeng-v1',
      aspectRatio: '16:9',
      resolution: '1024x576',
      style: 'realistic',
    },
    dalle: {
      name: 'DALL-E 3',
      provider: 'dalle' as const,
      baseUrl: 'https://api.openai.com/v1',
      model: 'dall-e-3',
      resolution: '1792x1024',
    },
    midjourney: {
      name: 'Midjourney',
      provider: 'midjourney' as const,
      baseUrl: 'https://api.midjourney.com',
      aspectRatio: '16:9',
      resolution: 'high',
      style: 'v6',
    },
    'stable-diffusion': {
      name: 'Stable Diffusion',
      provider: 'stable-diffusion' as const,
      baseUrl: 'https://api.stability.ai',
      model: 'stable-diffusion-xl-1024-v1-0',
      resolution: '1024x576',
    },
    qwen: {
      name: '通义千问图像',
      provider: 'qwen' as const,
      baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      model: 'qwen-vl-plus',
      aspectRatio: '16:9',
      resolution: '1024x1024',
    },
    baidu: {
      name: '文心一格',
      provider: 'baidu' as const,
      baseUrl: 'https://aip.baidubce.com',
      model: 'stable-diffusion-xl',
      aspectRatio: '16:9',
      resolution: '1024x1024',
    },
    flux: {
      name: 'Flux (OpenAI兼容)',
      provider: 'openai_compatible' as const,
      baseUrl: 'https://api.bfl.ml/v1',
      model: 'flux-pro-1.1',
      aspectRatio: '16:9',
      resolution: '1024x1024',
    },
  },
} as const;
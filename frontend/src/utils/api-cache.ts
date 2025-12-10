/**
 * API配置缓存管理
 * 避免每次请求都重新构建配置对象
 */

import { useApiConfigStore } from '@/store/useApiConfigStore';

// 缓存配置对象
let cachedApiConfig: any = null;
let lastConfigHash: string = '';

/**
 * 计算配置的哈希值
 */
const calculateConfigHash = (textApi: any, imageApi: any): string => {
  const configStr = JSON.stringify({
    text: textApi ? {
      provider: textApi.provider,
      apiKey: textApi.apiKey?.slice(-4), // 只用最后4位计算哈希
      secretKey: textApi.secretKey?.slice(-4), // 百度API的secretKey
      enableThinking: textApi.enableThinking, // OpenAI兼容API的思考模式
      model: textApi.model,
    } : null,
    image: imageApi ? {
      provider: imageApi.provider,
      apiKey: imageApi.apiKey?.slice(-4),
      secretKey: imageApi.secretKey?.slice(-4), // 百度API的secretKey
      model: imageApi.model,
    } : null,
  });
  
  // 简单哈希函数
  let hash = 0;
  for (let i = 0; i < configStr.length; i++) {
    const char = configStr.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // 转换为32位整数
  }
  return hash.toString();
};

/**
 * 获取缓存的API配置
 */
export const getCachedApiConfig = () => {
  const store = useApiConfigStore.getState();
  const defaultTextApi = store.getDefaultTextApi();
  const defaultImageApi = store.getDefaultImageApi();
  
  const currentHash = calculateConfigHash(defaultTextApi, defaultImageApi);
  
  // 如果配置没有变化，返回缓存的配置
  if (currentHash === lastConfigHash && cachedApiConfig) {
    return cachedApiConfig;
  }
  
  // 重新构建配置
  const apiConfig: any = {};
  
  if (defaultTextApi && defaultTextApi.enabled && defaultTextApi.apiKey) {
    apiConfig.text_api = {
      provider: defaultTextApi.provider,
      api_key: defaultTextApi.apiKey,
      base_url: defaultTextApi.baseUrl,
      model: defaultTextApi.model,
      max_tokens: defaultTextApi.maxTokens,
      temperature: defaultTextApi.temperature,
      ...(defaultTextApi.secretKey && { secretKey: defaultTextApi.secretKey }),
      ...(defaultTextApi.enableThinking && { enableThinking: defaultTextApi.enableThinking }),
      enabled: true,
    };
  }
  
  if (defaultImageApi && defaultImageApi.enabled && defaultImageApi.apiKey) {
    apiConfig.image_api = {
      provider: defaultImageApi.provider,
      api_key: defaultImageApi.apiKey,
      base_url: defaultImageApi.baseUrl,
      model: defaultImageApi.model,
      aspect_ratio: defaultImageApi.aspectRatio,
      resolution: defaultImageApi.resolution,
      style: defaultImageApi.style,
      ...(defaultImageApi.secretKey && { secretKey: defaultImageApi.secretKey }),
      enabled: true,
    };
  }
  
  // 更新缓存
  cachedApiConfig = Object.keys(apiConfig).length > 0 ? { api_config: apiConfig } : {};
  lastConfigHash = currentHash;
  
  return cachedApiConfig;
};

/**
 * 清除配置缓存
 */
export const clearApiConfigCache = () => {
  cachedApiConfig = null;
  lastConfigHash = '';
};

/**
 * 预热配置缓存
 */
export const warmupApiConfigCache = () => {
  getCachedApiConfig();
};
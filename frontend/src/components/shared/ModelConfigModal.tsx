import React, { useState, useEffect } from 'react';
import { Save, RotateCcw, Info } from 'lucide-react';
import { useApiConfigStore } from '@/store/useApiConfigStore';
import { apiClient } from '@/api/client';
import { Button } from './Button';
import { Input } from './Input';
import { Modal } from './Modal';

interface ModelConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ModelPresets {
  [provider: string]: {
    text: string[];
    image: string[];
  };
}

// 动态获取的模型列表将存储在组件状态中

export const ModelConfigModal: React.FC<ModelConfigModalProps> = ({ isOpen, onClose }) => {
  const { textApis, imageApis, updateTextApi, updateImageApi } = useApiConfigStore();
  const [localConfigs, setLocalConfigs] = useState<Record<string, string>>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [modelPresets, setModelPresets] = useState<ModelPresets>({});
  const [loadingModels, setLoadingModels] = useState<Record<string, boolean>>({});

  // 初始化本地配置
  useEffect(() => {
    if (isOpen) {
      const configs: Record<string, string> = {};
      [...textApis, ...imageApis].forEach(api => {
        configs[api.id] = api.model || '';
      });
      setLocalConfigs(configs);
      setHasChanges(false);
    }
  }, [isOpen, textApis, imageApis]);

  const handleModelChange = (apiId: string, model: string) => {
    setLocalConfigs(prev => ({ ...prev, [apiId]: model }));
    setHasChanges(true);
  };

  const handleSave = () => {
    // 保存所有更改
    [...textApis, ...imageApis].forEach(api => {
      const newModel = localConfigs[api.id];
      if (newModel !== api.model) {
        if (api.type === 'text') {
          updateTextApi(api.id, { model: newModel });
        } else {
          updateImageApi(api.id, { model: newModel });
        }
      }
    });
    setHasChanges(false);
    onClose();
  };

  const handleReset = () => {
    const configs: Record<string, string> = {};
    [...textApis, ...imageApis].forEach(api => {
      configs[api.id] = api.model || '';
    });
    setLocalConfigs(configs);
    setHasChanges(false);
  };

  // 动态获取模型列表
  const fetchProviderModels = async (provider: string) => {
    if (modelPresets[provider] || loadingModels[provider]) {
      return; // 已经加载过或正在加载
    }

    setLoadingModels(prev => ({ ...prev, [provider]: true }));
    
    try {
      const response = await apiClient.get(`/api/config/providers/${provider}/models`);
      if (response.data?.success && response.data?.data?.models) {
        setModelPresets(prev => ({
          ...prev,
          [provider]: response.data.data.models
        }));
      }
    } catch (error) {
      console.error(`Failed to fetch models for ${provider}:`, error);
      // 使用默认的空列表
      setModelPresets(prev => ({
        ...prev,
        [provider]: { text: [], image: [] }
      }));
    } finally {
      setLoadingModels(prev => ({ ...prev, [provider]: false }));
    }
  };

  const getModelSuggestions = (provider: string, type: 'text' | 'image'): string[] => {
    // 如果还没有加载过这个提供商的模型，触发加载
    if (!modelPresets[provider] && !loadingModels[provider]) {
      fetchProviderModels(provider);
    }
    
    return modelPresets[provider]?.[type] || [];
  };

  const renderApiModelConfig = (api: any) => {
    const suggestions = getModelSuggestions(api.provider, api.type);
    const currentModel = localConfigs[api.id] || '';

    return (
      <div key={api.id} className="border rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h3 className="font-medium">{api.name}</h3>
            <span className="text-xs px-2 py-1 bg-gray-100 rounded">
              {api.provider}
            </span>
            <span className={`text-xs px-2 py-1 rounded ${
              api.type === 'text' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
            }`}>
              {api.type === 'text' ? '文本' : '图像'}
            </span>
          </div>
          {!api.enabled && (
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">已禁用</span>
          )}
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            模型名称
          </label>
          <Input
            value={currentModel}
            onChange={(e) => handleModelChange(api.id, e.target.value)}
            placeholder={`输入${api.type === 'text' ? '文本' : '图像'}模型名称`}
            disabled={!api.enabled}
          />
          
          {(suggestions.length > 0 || loadingModels[api.provider]) && (
            <div className="space-y-2">
              <div className="flex items-center space-x-1 text-sm text-gray-600">
                <Info size={14} />
                <span>推荐模型：</span>
                {loadingModels[api.provider] && (
                  <span className="text-xs text-gray-500">加载中...</span>
                )}
              </div>
              <div className="flex flex-wrap gap-1">
                {loadingModels[api.provider] ? (
                  <div className="text-xs text-gray-500 px-2 py-1">正在获取模型列表...</div>
                ) : (
                  suggestions.map((model) => (
                    <button
                      key={model}
                      onClick={() => handleModelChange(api.id, model)}
                      disabled={!api.enabled}
                      className={`text-xs px-2 py-1 rounded border transition-colors ${
                        currentModel === model
                          ? 'bg-blue-100 border-blue-300 text-blue-700'
                          : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                      } ${!api.enabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      {model}
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const allApis = [...textApis, ...imageApis].sort((a, b) => {
    // 先按类型排序（文本在前），再按名称排序
    if (a.type !== b.type) {
      return a.type === 'text' ? -1 : 1;
    }
    return a.name.localeCompare(b.name);
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="模型配置" size="lg">
      <div className="space-y-6">
        {/* 说明 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-700">
              <p className="font-medium mb-1">模型配置说明</p>
              <ul className="list-disc list-inside space-y-1 text-blue-600">
                <li>为每个API配置具体使用的模型名称</li>
                <li>点击推荐模型可快速选择</li>
                <li>不同提供商支持的模型名称可能不同</li>
                <li>已禁用的API不会在生成时使用</li>
              </ul>
            </div>
          </div>
        </div>

        {/* API模型配置列表 */}
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {allApis.length > 0 ? (
            allApis.map(renderApiModelConfig)
          ) : (
            <div className="text-center py-8 text-gray-500">
              暂无API配置，请先在API配置中添加
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex justify-between items-center pt-4 border-t">
          <Button
            variant="ghost"
            onClick={handleReset}
            disabled={!hasChanges}
            icon={<RotateCcw size={16} />}
          >
            重置更改
          </Button>
          
          <div className="flex space-x-3">
            <Button variant="ghost" onClick={onClose}>
              取消
            </Button>
            <Button
              onClick={handleSave}
              disabled={!hasChanges}
              icon={<Save size={16} />}
            >
              保存配置
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
import React, { useState } from 'react';
import { Button } from './Button';
import { useApiConfigStore } from '@/store/useApiConfigStore';
import { apiClient } from '@/api/client';

export const ApiConfigTest: React.FC = () => {
  const { textApis, imageApis, addTextApi, addImageApi } = useApiConfigStore();
  const [testResults, setTestResults] = useState<string[]>([]);

  const addTestResult = (message: string) => {
    setTestResults(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const testAddTextApi = () => {
    addTestResult('测试添加文本API...');
    addTextApi({
      name: '测试Google API',
      provider: 'google',
      baseUrl: 'https://generativelanguage.googleapis.com',
      model: 'gemini-2.5-flash',
      apiKey: 'test-key-123',
      enabled: true,
    });
    addTestResult('文本API添加完成');
  };

  const testAddImageApi = () => {
    addTestResult('测试添加图像API...');
    addImageApi({
      name: '测试Google图像API',
      provider: 'google',
      model: 'gemini-3-pro-image-preview',
      apiKey: 'test-key-456',
      enabled: true,
    });
    addTestResult('图像API添加完成');
  };

  const testFetchModels = async () => {
    addTestResult('测试获取模型列表...');
    try {
      const response = await apiClient.get('/api/config/providers/google/models');
      if (response.data?.success) {
        addTestResult(`获取模型成功: ${JSON.stringify(response.data.data.models)}`);
      } else {
        addTestResult(`获取模型失败: ${response.data?.message || '未知错误'}`);
      }
    } catch (error) {
      addTestResult(`获取模型出错: ${error}`);
    }
  };

  const clearResults = () => {
    setTestResults([]);
  };

  return (
    <div className="p-6 border rounded-lg space-y-4">
      <h3 className="text-lg font-semibold">API配置测试</h3>
      
      <div className="space-y-2">
        <div className="text-sm text-gray-600">
          当前配置: {textApis.length} 个文本API, {imageApis.length} 个图像API
        </div>
        
        <div className="flex space-x-2">
          <Button onClick={testAddTextApi} size="sm">
            测试添加文本API
          </Button>
          <Button onClick={testAddImageApi} size="sm">
            测试添加图像API
          </Button>
          <Button onClick={testFetchModels} size="sm">
            测试获取模型
          </Button>
          <Button onClick={clearResults} variant="ghost" size="sm">
            清空日志
          </Button>
        </div>
      </div>

      <div className="bg-gray-50 p-3 rounded max-h-40 overflow-y-auto">
        <div className="text-sm font-medium mb-2">测试日志:</div>
        {testResults.length === 0 ? (
          <div className="text-gray-500 text-sm">暂无测试日志</div>
        ) : (
          <div className="space-y-1">
            {testResults.map((result, index) => (
              <div key={index} className="text-xs font-mono text-gray-700">
                {result}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-blue-50 p-3 rounded">
        <div className="text-sm font-medium mb-2">当前API配置:</div>
        <div className="text-xs space-y-1">
          <div>文本APIs: {textApis.map(api => `${api.name}(${api.provider})`).join(', ') || '无'}</div>
          <div>图像APIs: {imageApis.map(api => `${api.name}(${api.provider})`).join(', ') || '无'}</div>
        </div>
      </div>
    </div>
  );
};
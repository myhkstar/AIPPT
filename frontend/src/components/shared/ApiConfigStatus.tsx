import React, { useState, useMemo } from 'react';
import { CheckCircle, AlertCircle, XCircle, Loader } from 'lucide-react';
import { useApiConfigStore } from '@/store/useApiConfigStore';
import { StepByStepApiWizard } from './StepByStepApiWizard';
import { ApiConfigModal } from './ApiConfigModal';

interface ApiConfigStatusProps {
  className?: string;
  showText?: boolean;
  clickable?: boolean;
}

export const ApiConfigStatus: React.FC<ApiConfigStatusProps> = ({ 
  className = '', 
  showText = true,
  clickable = true
}) => {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // 直接从store获取状态，确保响应式更新
  const { textApis, imageApis, defaultTextApi, defaultImageApi } = useApiConfigStore();
  
  // 计算配置状态
  const status = useMemo(() => {
    const defaultText = textApis.find(api => api.id === defaultTextApi);
    const defaultImage = imageApis.find(api => api.id === defaultImageApi);
    
    const hasText = !!(defaultText && defaultText.enabled && defaultText.apiKey);
    const hasImage = !!(defaultImage && defaultImage.enabled && defaultImage.apiKey);
    
    return {
      hasText,
      hasImage,
      hasAny: hasText || hasImage,
      isComplete: hasText && hasImage,
      status: hasText && hasImage ? 'complete' : 
              hasText || hasImage ? 'partial' : 'none'
    };
  }, [textApis, imageApis, defaultTextApi, defaultImageApi]);
  
  const getStatusIcon = () => {
    switch (status.status) {
      case 'complete':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'partial':
        return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      case 'none':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Loader className="w-4 h-4 text-gray-400 animate-spin" />;
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case 'complete':
        return '已完整配置';
      case 'partial':
        return status.hasText ? '仅文本API' : '仅图像API';
      case 'none':
        return '点击配置API';
      default:
        return '检查中...';
    }
  };

  const getStatusColor = () => {
    switch (status.status) {
      case 'complete':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'partial':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'none':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const handleClick = () => {
    if (!clickable) return;
    
    // 如果没有任何API配置，打开向导；否则打开配置模态框
    if (!status.hasAny) {
      setIsWizardOpen(true);
    } else {
      setIsModalOpen(true);
    }
  };

  const baseClasses = `flex items-center space-x-2 px-3 py-1 rounded-full border ${getStatusColor()} ${className}`;
  const clickableClasses = clickable ? 'cursor-pointer hover:opacity-80 transition-opacity' : '';

  return (
    <>
      <div 
        className={`${baseClasses} ${clickableClasses}`}
        onClick={handleClick}
        title={clickable ? '点击配置API' : undefined}
      >
        {getStatusIcon()}
        {showText && (
          <span className="text-sm font-medium">
            {getStatusText()}
          </span>
        )}
      </div>

      {/* 快速配置向导 */}
      <StepByStepApiWizard
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
      />

      {/* API配置模态框 */}
      <ApiConfigModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};
import React, { useState, useMemo } from 'react';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import { Button } from './Button';
import { useProjectStore } from '@/store/useProjectStore';
import { useToast } from './Toast';

interface BatchRetryButtonProps {
  className?: string;
}

export const BatchRetryButton: React.FC<BatchRetryButtonProps> = ({ className = '' }) => {
  const [isRetrying, setIsRetrying] = useState(false);
  const { currentProject, generatePageImage } = useProjectStore();
  const { show } = useToast();

  // 获取失败的页面
  const failedPages = useMemo(() => {
    if (!currentProject) return [];
    return currentProject.pages.filter(page => 
      page.status === 'FAILED' ||
      (page.status === 'COMPLETED' && !page.generated_image_url)
    );
  }, [currentProject]);

  // 获取正在生成的页面
  const generatingPages = useMemo(() => {
    if (!currentProject) return [];
    return currentProject.pages.filter(page => 
      page.status === 'GENERATING'
    );
  }, [currentProject]);

  const handleBatchRetry = async () => {
    if (failedPages.length === 0) return;
    
    setIsRetrying(true);
    try {
      // 批量重新生成失败的页面
      const retryPromises = failedPages.map(async (page) => {
        if (!page.id) return;
        try {
          await generatePageImage(page.id, true); // 强制重新生成
        } catch (error) {
          console.error(`重新生成页面 ${page.id} 失败:`, error);
        }
      });

      await Promise.all(retryPromises);
      
      show({ 
        message: `已开始重新生成 ${failedPages.length} 个失败的页面`, 
        type: 'success' 
      });
    } catch (error: any) {
      show({ 
        message: `批量重试失败: ${error.message || '未知错误'}`, 
        type: 'error' 
      });
    } finally {
      setIsRetrying(false);
    }
  };

  // 如果没有失败的页面，不显示按钮
  if (failedPages.length === 0) return null;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex items-center gap-1 text-sm text-orange-600 bg-orange-50 px-2 py-1 rounded">
        <AlertTriangle size={14} />
        <span>{failedPages.length} 个失败</span>
      </div>
      
      <Button
        variant="secondary"
        size="sm"
        icon={<RefreshCw size={14} className={isRetrying ? 'animate-spin' : ''} />}
        onClick={handleBatchRetry}
        disabled={isRetrying || generatingPages.length > 0}
        className="text-orange-600 border-orange-200 hover:bg-orange-50"
      >
        {isRetrying ? '重试中...' : '批量重试'}
      </Button>
    </div>
  );
};

export default BatchRetryButton;
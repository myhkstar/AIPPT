import React, { useState, useMemo } from 'react';
import { RefreshCw, CheckSquare, Square, AlertTriangle, XCircle } from 'lucide-react';
import { Button } from './Button';
import { Modal } from './Modal';
import { useProjectStore } from '@/store/useProjectStore';
import { useToast } from './Toast';
import type { Page } from '@/types';

interface BatchSelectModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const BatchSelectModal: React.FC<BatchSelectModalProps> = ({ isOpen, onClose }) => {
  const [selectedPageIds, setSelectedPageIds] = useState<Set<string>>(new Set());
  const [isRetrying, setIsRetrying] = useState(false);
  const { currentProject, generatePageImage } = useProjectStore();
  const { show } = useToast();

  // 获取可重试的页面（失败或未生成的）
  const retryablePages = useMemo(() => {
    if (!currentProject) return [];
    return currentProject.pages.filter(page => 
      page.status === 'FAILED' ||
      (page.status === 'COMPLETED' && !page.generated_image_url)
    );
  }, [currentProject]);

  // 自动选择所有失败的页面
  const selectAllFailed = () => {
    const failedIds = retryablePages
      .filter(page => page.status === 'FAILED')
      .map(page => page.id!)
      .filter(Boolean);
    setSelectedPageIds(new Set(failedIds));
  };

  // 选择所有可重试的页面
  const selectAll = () => {
    const allIds = retryablePages.map(page => page.id!).filter(Boolean);
    setSelectedPageIds(new Set(allIds));
  };

  // 清空选择
  const clearSelection = () => {
    setSelectedPageIds(new Set());
  };

  // 切换页面选择状态
  const togglePageSelection = (pageId: string) => {
    const newSelection = new Set(selectedPageIds);
    if (newSelection.has(pageId)) {
      newSelection.delete(pageId);
    } else {
      newSelection.add(pageId);
    }
    setSelectedPageIds(newSelection);
  };

  // 批量重试选中的页面
  const handleBatchRetry = async () => {
    if (selectedPageIds.size === 0) return;
    
    setIsRetrying(true);
    try {
      const retryPromises = Array.from(selectedPageIds).map(async (pageId) => {
        try {
          await generatePageImage(pageId, true);
        } catch (error) {
          console.error(`重新生成页面 ${pageId} 失败:`, error);
        }
      });

      await Promise.all(retryPromises);
      
      show({ 
        message: `已开始重新生成 ${selectedPageIds.size} 个页面`, 
        type: 'success' 
      });
      
      onClose();
      setSelectedPageIds(new Set());
    } catch (error: any) {
      show({ 
        message: `批量重试失败: ${error.message || '未知错误'}`, 
        type: 'error' 
      });
    } finally {
      setIsRetrying(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'FAILED':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'GENERATING':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
    }
  };

  const getStatusText = (page: Page) => {
    if (page.status === 'FAILED') {
      return '生成失败';
    }
    if (page.status === 'COMPLETED' && !page.generated_image_url) {
      return '图片缺失';
    }
    return page.status;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="批量重新生成" size="lg">
      <div className="space-y-4">
        {retryablePages.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckSquare className="w-12 h-12 mx-auto mb-3 text-green-500" />
            <p>所有页面都已成功生成图片</p>
          </div>
        ) : (
          <>
            {/* 批量操作按钮 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={selectAllFailed}
                  className="text-red-600 hover:bg-red-50"
                >
                  选择失败项
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={selectAll}
                  className="text-blue-600 hover:bg-blue-50"
                >
                  全选
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearSelection}
                  className="text-gray-600 hover:bg-gray-50"
                >
                  清空
                </Button>
              </div>
              <div className="text-sm text-gray-500">
                已选择 {selectedPageIds.size} / {retryablePages.length} 个
              </div>
            </div>

            {/* 页面列表 */}
            <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-lg">
              {retryablePages.map((page, index) => (
                <div
                  key={page.id}
                  className={`flex items-center gap-3 p-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 cursor-pointer ${
                    selectedPageIds.has(page.id!) ? 'bg-blue-50 border-blue-200' : ''
                  }`}
                  onClick={() => page.id && togglePageSelection(page.id)}
                >
                  <div className="flex-shrink-0">
                    {selectedPageIds.has(page.id!) ? (
                      <CheckSquare className="w-5 h-5 text-blue-600" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                  
                  <div className="flex-shrink-0 w-16 h-12 bg-gray-100 rounded border flex items-center justify-center text-sm text-gray-500">
                    {index + 1}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 truncate">
                      {page.outline_content.title}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusIcon(page.status)}
                      <span className="text-sm text-gray-500">
                        {getStatusText(page)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* 操作按钮 */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
              <Button variant="ghost" onClick={onClose}>
                取消
              </Button>
              <Button
                variant="primary"
                icon={<RefreshCw size={16} className={isRetrying ? 'animate-spin' : ''} />}
                onClick={handleBatchRetry}
                disabled={selectedPageIds.size === 0 || isRetrying}
              >
                {isRetrying ? '重试中...' : `重新生成 (${selectedPageIds.size})`}
              </Button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};

export default BatchSelectModal;
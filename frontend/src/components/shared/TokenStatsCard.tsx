import React, { useState } from 'react';
import { BarChart3, TrendingUp, DollarSign, Zap, ChevronDown, ChevronUp, Trash2 } from 'lucide-react';
import { useTokenStatsStore } from '@/store/useTokenStatsStore';
import { Button } from './Button';

interface TokenStatsCardProps {
  className?: string;
  compact?: boolean;
}

export const TokenStatsCard: React.FC<TokenStatsCardProps> = ({ 
  className = '',
  compact = false 
}) => {
  const [expanded, setExpanded] = useState(false);
  const { getTodayStats, getMonthlyStats, totalTokensUsed, totalCost, resetStats } = useTokenStatsStore();
  
  const todayStats = getTodayStats();
  const monthlyStats = getMonthlyStats();

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const formatCost = (cost: number) => {
    return '$' + cost.toFixed(4);
  };

  if (compact) {
    return (
      <div className={`flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg text-sm ${className}`}>
        <Zap size={14} className="text-yellow-500" />
        <span className="text-gray-600">今日: {formatNumber(todayStats.totalTokens)} tokens</span>
        <span className="text-gray-400">|</span>
        <span className="text-gray-600">{formatCost(todayStats.estimatedCost)}</span>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      <div 
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Token 消耗统计</h3>
            <p className="text-sm text-gray-500">今日: {formatNumber(todayStats.totalTokens)} tokens</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">{formatCost(todayStats.estimatedCost)}</span>
          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-gray-100">
          {/* 今日统计 */}
          <div className="pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">今日统计</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-blue-50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp size={14} className="text-blue-600" />
                  <span className="text-xs text-blue-600">文本生成</span>
                </div>
                <div className="text-lg font-semibold text-blue-900">
                  {formatNumber(todayStats.textTokens)}
                </div>
              </div>
              <div className="bg-purple-50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Zap size={14} className="text-purple-600" />
                  <span className="text-xs text-purple-600">图像生成</span>
                </div>
                <div className="text-lg font-semibold text-purple-900">
                  {formatNumber(todayStats.imageTokens)}
                </div>
              </div>
            </div>
          </div>

          {/* 本月统计 */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">本月统计 (30天)</h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500 mb-1">总 Tokens</div>
                <div className="text-lg font-semibold text-gray-900">
                  {formatNumber(monthlyStats.tokens)}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500 mb-1">请求次数</div>
                <div className="text-lg font-semibold text-gray-900">
                  {monthlyStats.requests}
                </div>
              </div>
              <div className="bg-green-50 rounded-lg p-3 text-center">
                <div className="flex items-center justify-center gap-1 text-xs text-green-600 mb-1">
                  <DollarSign size={12} />
                  <span>预估费用</span>
                </div>
                <div className="text-lg font-semibold text-green-700">
                  {formatCost(monthlyStats.cost)}
                </div>
              </div>
            </div>
          </div>

          {/* 累计统计 */}
          <div className="flex items-center justify-between pt-3 border-t border-gray-100">
            <div className="text-sm text-gray-600">
              累计: <span className="font-medium">{formatNumber(totalTokensUsed)}</span> tokens
              <span className="mx-2">·</span>
              <span className="font-medium text-green-600">{formatCost(totalCost)}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              icon={<Trash2 size={14} />}
              onClick={(e) => {
                e.stopPropagation();
                if (confirm('确定要清空所有统计数据吗？')) {
                  resetStats();
                }
              }}
              className="text-gray-400 hover:text-red-500"
            >
              清空
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TokenStatsCard;

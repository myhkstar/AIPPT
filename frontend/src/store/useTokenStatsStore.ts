import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface TokenUsageRecord {
  id: string;
  timestamp: number;
  type: 'text' | 'image';
  provider: string;
  model: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  cost?: number;
  projectId?: string;
}

interface DailyStats {
  date: string;
  textTokens: number;
  imageTokens: number;
  totalTokens: number;
  requestCount: number;
  estimatedCost: number;
}

interface TokenStatsState {
  records: TokenUsageRecord[];
  dailyStats: DailyStats[];
  totalTokensUsed: number;
  totalCost: number;
}

interface TokenStatsStore extends TokenStatsState {
  addRecord: (record: Omit<TokenUsageRecord, 'id' | 'timestamp'>) => void;
  getStatsForPeriod: (days: number) => DailyStats[];
  getTodayStats: () => DailyStats;
  getMonthlyStats: () => { tokens: number; cost: number; requests: number };
  clearOldRecords: (daysToKeep: number) => void;
  resetStats: () => void;
}

const generateId = () => Math.random().toString(36).substr(2, 9);

const getDateString = (date: Date) => date.toISOString().split('T')[0];

// Token 价格估算（每1000 tokens）
const TOKEN_PRICES: Record<string, { input: number; output: number }> = {
  'gemini-2.5-flash': { input: 0.00015, output: 0.0006 },
  'gemini-2.5-pro': { input: 0.00125, output: 0.005 },
  'gpt-4': { input: 0.03, output: 0.06 },
  'gpt-3.5-turbo': { input: 0.0005, output: 0.0015 },
  'claude-3-sonnet': { input: 0.003, output: 0.015 },
  'default': { input: 0.001, output: 0.002 },
};

const estimateCost = (model: string, inputTokens: number, outputTokens: number): number => {
  const prices = TOKEN_PRICES[model] || TOKEN_PRICES['default'];
  return (inputTokens / 1000) * prices.input + (outputTokens / 1000) * prices.output;
};

export const useTokenStatsStore = create<TokenStatsStore>()(
  persist(
    (set, get) => ({
      records: [],
      dailyStats: [],
      totalTokensUsed: 0,
      totalCost: 0,

      addRecord: (record) => {
        const newRecord: TokenUsageRecord = {
          ...record,
          id: generateId(),
          timestamp: Date.now(),
          cost: record.cost ?? estimateCost(record.model, record.inputTokens, record.outputTokens),
        };

        const today = getDateString(new Date());
        
        set((state) => {
          // 更新记录
          const newRecords = [...state.records, newRecord];
          
          // 更新每日统计
          let dailyStats = [...state.dailyStats];
          const todayIndex = dailyStats.findIndex(s => s.date === today);
          
          if (todayIndex >= 0) {
            dailyStats[todayIndex] = {
              ...dailyStats[todayIndex],
              textTokens: dailyStats[todayIndex].textTokens + (record.type === 'text' ? record.totalTokens : 0),
              imageTokens: dailyStats[todayIndex].imageTokens + (record.type === 'image' ? record.totalTokens : 0),
              totalTokens: dailyStats[todayIndex].totalTokens + record.totalTokens,
              requestCount: dailyStats[todayIndex].requestCount + 1,
              estimatedCost: dailyStats[todayIndex].estimatedCost + (newRecord.cost || 0),
            };
          } else {
            dailyStats.push({
              date: today,
              textTokens: record.type === 'text' ? record.totalTokens : 0,
              imageTokens: record.type === 'image' ? record.totalTokens : 0,
              totalTokens: record.totalTokens,
              requestCount: 1,
              estimatedCost: newRecord.cost || 0,
            });
          }

          return {
            records: newRecords,
            dailyStats,
            totalTokensUsed: state.totalTokensUsed + record.totalTokens,
            totalCost: state.totalCost + (newRecord.cost || 0),
          };
        });
      },

      getStatsForPeriod: (days) => {
        const { dailyStats } = get();
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - days);
        const cutoffStr = getDateString(cutoff);
        
        return dailyStats.filter(s => s.date >= cutoffStr).sort((a, b) => a.date.localeCompare(b.date));
      },

      getTodayStats: () => {
        const { dailyStats } = get();
        const today = getDateString(new Date());
        return dailyStats.find(s => s.date === today) || {
          date: today,
          textTokens: 0,
          imageTokens: 0,
          totalTokens: 0,
          requestCount: 0,
          estimatedCost: 0,
        };
      },

      getMonthlyStats: () => {
        const stats = get().getStatsForPeriod(30);
        return stats.reduce((acc, s) => ({
          tokens: acc.tokens + s.totalTokens,
          cost: acc.cost + s.estimatedCost,
          requests: acc.requests + s.requestCount,
        }), { tokens: 0, cost: 0, requests: 0 });
      },

      clearOldRecords: (daysToKeep) => {
        const cutoff = Date.now() - daysToKeep * 24 * 60 * 60 * 1000;
        const cutoffDate = getDateString(new Date(cutoff));
        
        set((state) => ({
          records: state.records.filter(r => r.timestamp >= cutoff),
          dailyStats: state.dailyStats.filter(s => s.date >= cutoffDate),
        }));
      },

      resetStats: () => {
        set({
          records: [],
          dailyStats: [],
          totalTokensUsed: 0,
          totalCost: 0,
        });
      },
    }),
    {
      name: 'token-stats-storage',
      version: 1,
    }
  )
);

import React, { useState, useCallback } from 'react';
import { ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { Button } from './Button';

// PPT用途选项
const PURPOSE_OPTIONS = [
  { value: 'presentation', label: '演讲汇报', icon: '🎤' },
  { value: 'teaching', label: '教学培训', icon: '📚' },
  { value: 'proposal', label: '方案提案', icon: '💡' },
  { value: 'report', label: '工作总结', icon: '📊' },
  { value: 'product', label: '产品介绍', icon: '🚀' },
  { value: 'marketing', label: '营销推广', icon: '📢' },
  { value: 'other', label: '其他', icon: '📝' },
] as const;

// 受众选项
const AUDIENCE_OPTIONS = [
  { value: 'internal', label: '内部团队', icon: '👥' },
  { value: 'leadership', label: '领导层', icon: '👔' },
  { value: 'client', label: '客户', icon: '🤝' },
  { value: 'student', label: '学生', icon: '🎓' },
  { value: 'public', label: '公众', icon: '🌍' },
  { value: 'other', label: '其他', icon: '👤' },
] as const;

// 风格选项
const STYLE_OPTIONS = [
  { value: 'professional', label: '专业商务', icon: '💼' },
  { value: 'creative', label: '创意活泼', icon: '🎨' },
  { value: 'minimalist', label: '简约清新', icon: '✨' },
  { value: 'tech', label: '科技感', icon: '🔮' },
  { value: 'elegant', label: '优雅大气', icon: '🌸' },
  { value: 'cartoon', label: '卡通可爱', icon: '🎪' },
] as const;

// 页数选项
const PAGE_COUNT_OPTIONS = [
  { value: '5', label: '5页' },
  { value: '10', label: '10页' },
  { value: '15', label: '15页' },
  { value: '20', label: '20页' },
  { value: 'custom', label: '自定义' },
  { value: 'auto', label: '自动' },
] as const;

// 语言选项
const LANGUAGE_OPTIONS = [
  { value: 'zh', label: '中文', icon: '🇨🇳' },
  { value: 'en', label: 'English', icon: '🇺🇸' },
  { value: 'bilingual', label: '中英双语', icon: '🌐' },
] as const;

export interface StructuredRequirementsData {
  topic: string;
  purpose: string;
  audience: string;
  style: string;
  pageCount: string;
  language: string;
  keyPoints: string;
  additionalNotes: string;
}

interface StructuredRequirementsProps {
  onGenerate: (data: StructuredRequirementsData, prompt: string) => void;
  isLoading?: boolean;
}

const OptionButton: React.FC<{
  selected: boolean;
  onClick: () => void;
  icon?: string;
  label: string;
}> = ({ selected, onClick, icon, label }) => (
  <button
    type="button"
    onClick={onClick}
    className={`px-3 py-2 rounded-lg border-2 transition-all text-sm flex items-center gap-1.5 ${
      selected
        ? 'border-banana-500 bg-banana-50 text-banana-700'
        : 'border-gray-200 hover:border-banana-300 text-gray-600'
    }`}
  >
    {icon && <span>{icon}</span>}
    <span>{label}</span>
  </button>
);

const generatePrompt = (data: StructuredRequirementsData): string => {
  const parts: string[] = [];
  parts.push(`主题：${data.topic}`);
  
  const purpose = PURPOSE_OPTIONS.find(item => item.value === data.purpose);
  if (purpose) parts.push(`用途：${purpose.label}`);
  
  const audience = AUDIENCE_OPTIONS.find(item => item.value === data.audience);
  if (audience) parts.push(`受众：${audience.label}`);
  
  const style = STYLE_OPTIONS.find(item => item.value === data.style);
  if (style) parts.push(`风格：${style.label}`);
  
  if (data.pageCount !== 'auto') {
    parts.push(`页数：约${data.pageCount}页`);
  }
  
  const lang = LANGUAGE_OPTIONS.find(item => item.value === data.language);
  if (lang && data.language !== 'zh') {
    parts.push(`语言：${lang.label}`);
  }
  
  if (data.keyPoints.trim()) {
    parts.push(`要点：${data.keyPoints}`);
  }
  
  if (data.additionalNotes.trim()) {
    parts.push(`补充：${data.additionalNotes}`);
  }
  
  return parts.join('\n');
};

export const StructuredRequirements: React.FC<StructuredRequirementsProps> = ({
  onGenerate,
  isLoading = false,
}) => {
  const [data, setData] = useState<StructuredRequirementsData>({
    topic: '',
    purpose: 'presentation',
    audience: 'internal',
    style: 'professional',
    pageCount: '10',
    language: 'zh',
    keyPoints: '',
    additionalNotes: '',
  });
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [customPageCount, setCustomPageCount] = useState('');

  const updateField = useCallback(<K extends keyof StructuredRequirementsData>(
    field: K,
    value: StructuredRequirementsData[K]
  ) => {
    setData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleSubmit = useCallback(() => {
    if (!data.topic.trim()) return;
    const prompt = generatePrompt(data);
    onGenerate(data, prompt);
  }, [data, onGenerate]);

  const isValid = data.topic.trim().length > 0;

  return (
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          PPT主题 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.topic}
          onChange={(e) => updateField('topic', e.target.value)}
          placeholder="例如：2024年度工作总结、新产品发布会、Python入门教程..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-banana-500 focus:border-transparent text-base"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">PPT用途</label>
        <div className="flex flex-wrap gap-2">
          {PURPOSE_OPTIONS.map((opt) => (
            <OptionButton
              key={opt.value}
              selected={data.purpose === opt.value}
              onClick={() => updateField('purpose', opt.value)}
              icon={opt.icon}
              label={opt.label}
            />
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">目标受众</label>
        <div className="flex flex-wrap gap-2">
          {AUDIENCE_OPTIONS.map((opt) => (
            <OptionButton
              key={opt.value}
              selected={data.audience === opt.value}
              onClick={() => updateField('audience', opt.value)}
              icon={opt.icon}
              label={opt.label}
            />
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">视觉风格</label>
        <div className="flex flex-wrap gap-2">
          {STYLE_OPTIONS.map((opt) => (
            <OptionButton
              key={opt.value}
              selected={data.style === opt.value}
              onClick={() => updateField('style', opt.value)}
              icon={opt.icon}
              label={opt.label}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">预计页数</label>
          <div className="flex gap-2">
            <select
              value={data.pageCount === 'custom' || !PAGE_COUNT_OPTIONS.some(o => o.value === data.pageCount) ? 'custom' : data.pageCount}
              onChange={(e) => {
                const val = e.target.value;
                if (val === 'custom') {
                  updateField('pageCount', 'custom');
                } else {
                  updateField('pageCount', val);
                  setCustomPageCount('');
                }
              }}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-banana-500 focus:border-transparent"
            >
              {PAGE_COUNT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            {(data.pageCount === 'custom' || (!PAGE_COUNT_OPTIONS.some(o => o.value === data.pageCount) && data.pageCount !== 'auto')) && (
              <input
                type="number"
                min="1"
                max="100"
                value={customPageCount || (data.pageCount !== 'custom' ? data.pageCount : '')}
                onChange={(e) => {
                  const val = e.target.value;
                  setCustomPageCount(val);
                  if (val && parseInt(val) > 0) {
                    updateField('pageCount', val);
                  }
                }}
                placeholder="页数"
                className="w-20 px-2 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-banana-500 focus:border-transparent text-center"
              />
            )}
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">语言</label>
          <div className="flex gap-2">
            {LANGUAGE_OPTIONS.map((opt) => (
              <OptionButton
                key={opt.value}
                selected={data.language === opt.value}
                onClick={() => updateField('language', opt.value)}
                icon={opt.icon}
                label={opt.label}
              />
            ))}
          </div>
        </div>
      </div>

      <div>
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          <span>高级选项</span>
        </button>
        
        {showAdvanced && (
          <div className="mt-3 space-y-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">核心要点（可选）</label>
              <textarea
                value={data.keyPoints}
                onChange={(e) => updateField('keyPoints', e.target.value)}
                placeholder="列出PPT需要涵盖的核心要点，每行一个..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-banana-500 focus:border-transparent text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">补充说明（可选）</label>
              <textarea
                value={data.additionalNotes}
                onChange={(e) => updateField('additionalNotes', e.target.value)}
                placeholder="其他特殊要求或说明..."
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-banana-500 focus:border-transparent text-sm"
              />
            </div>
          </div>
        )}
      </div>

      <Button
        variant="primary"
        size="lg"
        icon={<Sparkles size={20} />}
        onClick={handleSubmit}
        disabled={!isValid || isLoading}
        className="w-full"
      >
        {isLoading ? '生成中...' : '生成PPT大纲'}
      </Button>
    </div>
  );
};

export default StructuredRequirements;

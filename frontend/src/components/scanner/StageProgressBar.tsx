import React from 'react';
import { useTranslation } from 'react-i18next';
import { CheckCircle2, Loader2, Sparkles, Sliders, Eye, FileCheck } from 'lucide-react';

interface StageProgressBarProps {
  status: string;
  progressPercentage: number;
  stageMessage: string;
}

export const StageProgressBar: React.FC<StageProgressBarProps> = ({
  status,
  progressPercentage,
  stageMessage,
}) => {
  const { t } = useTranslation();

  const STAGES = [
    { key: 'PREPROCESSING', label: t('stage.preprocessing'), icon: Sliders, desc: 'Panel Deskew & QR Markers' },
    { key: 'GEMINI_ANALYSIS', label: t('stage.gemini_analysis'), icon: Sparkles, desc: 'Declarations Vision Read' },
    { key: 'RULES_ENGINE', label: t('stage.rules_engine'), icon: FileCheck, desc: '2011 Rules & USP Audit' },
    { key: 'VISUAL_AUDIT', label: t('stage.visual_audit'), icon: Eye, desc: 'Table-I Font & Contrast' },
  ];
  const getStageIndex = (s: string) => {
    switch (s) {
      case 'PREPROCESSING': return 0;
      case 'GEMINI_ANALYSIS':
      case 'VISION_ANALYSIS':
      case 'OCR_RUNNING': return 1;
      case 'RULES_ENGINE':
      case 'EXTRACTING': return 2;
      case 'VISUAL_AUDIT':
      case 'EVALUATING':
      case 'ANALYZING': return 3;
      case 'COMPLETED': return 4;
      default: return 0;
    }
  };

  const currentIndex = getStageIndex(status);

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
          <h3 className="font-bold text-slate-900 text-sm">{t('scan.btn_scanning')}</h3>
        </div>
        <div className="text-sm font-mono font-bold text-blue-600">
          {progressPercentage}%
        </div>
      </div>

      {/* Progress Bar Track */}
      <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
        <div
          className="bg-gradient-to-r from-blue-600 to-indigo-600 h-2.5 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${Math.max(5, progressPercentage)}%` }}
        />
      </div>

      {/* Live Stage Message */}
      <div className="text-xs text-slate-600 font-mono bg-slate-50 p-2.5 rounded border border-slate-200 flex items-center justify-between">
        <span>{stageMessage || 'Initializing VisionX Multimodal Compliance Inspection...'}</span>
        <span className="text-[10px] text-slate-400">VisionX Inspection Engine</span>
      </div>

      {/* Visual Pipeline Steps */}
      <div className="grid grid-cols-4 gap-2 pt-2">
        {STAGES.map((stg, idx) => {
          const Icon = stg.icon;
          const isDone = currentIndex > idx || status === 'COMPLETED';
          const isCurrent = currentIndex === idx && status !== 'COMPLETED';

          return (
            <div
              key={stg.key}
              className={`p-2 rounded-lg border text-center transition-all ${
                isDone
                  ? 'bg-emerald-50/60 border-emerald-200 text-emerald-800'
                  : isCurrent
                  ? 'bg-blue-50 border-blue-300 text-blue-900 ring-2 ring-blue-500/20 shadow-sm'
                  : 'bg-slate-50 border-slate-200 text-slate-400'
              }`}
            >
              <div className="flex justify-center mb-1">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : isCurrent ? (
                  <Icon className="w-4 h-4 text-blue-600 animate-pulse" />
                ) : (
                  <Icon className="w-4 h-4 text-slate-400" />
                )}
              </div>
              <div className="text-[11px] font-semibold truncate">{stg.label}</div>
              <div className="text-[9px] text-slate-500 truncate">{stg.desc}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

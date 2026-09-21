import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { RuleResultItem, OCRToken, ExtractedFieldItem } from '../../types';
import { Eye, EyeOff, ZoomIn, ZoomOut, RotateCcw, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface AnnotatedImageViewerProps {
  imageUrl: string;
  imageUrls?: string[];
  activePanelIndex: number;
  onPanelChange: (index: number) => void;
  ruleResults: RuleResultItem[];
  rawTokens: OCRToken[];
  extractedData: Record<string, ExtractedFieldItem | any>;
  selectedRuleId: string | null;
  onSelectRule: (ruleId: string | null) => void;
}

export const AnnotatedImageViewer: React.FC<AnnotatedImageViewerProps> = ({
  imageUrl,
  imageUrls,
  activePanelIndex,
  onPanelChange,
  ruleResults,
  rawTokens,
  extractedData,
  selectedRuleId,
  onSelectRule,
}) => {
  const { t } = useTranslation();
  const [zoom, setZoom] = useState<number>(1);
  const [overlayMode, setOverlayMode] = useState<'rules' | 'tokens' | 'both'>('rules');
  const [hoveredBox, setHoveredBox] = useState<any | null>(null);

  const images = imageUrls && imageUrls.length > 0 ? imageUrls : [imageUrl];
  const currentImageUrl = images[activePanelIndex] || imageUrl;

  // Filter boxes for rules that have bounding box coordinates and match current panel
  const ruleBoxes = ruleResults
    .filter((r) => r.bbox && r.bbox.width > 0 && (r.image_index ?? 0) === activePanelIndex)
    .map((r) => ({
      id: r.rule_id,
      type: 'rule' as const,
      status: r.status,
      title: r.title,
      text: r.extracted_value || r.title,
      confidence: r.confidence,
      bbox: r.bbox!,
      image_index: r.image_index ?? 0,
    }));

  const tokenBoxes = rawTokens
    .filter((t) => (t.image_index ?? 0) === activePanelIndex)
    .map((t, idx) => ({
      id: `token_${idx}`,
      type: 'token' as const,
      status: t.needs_review ? 'NEEDS_REVIEW' : 'PASS',
      title: t.engine,
      text: t.text,
      confidence: t.confidence,
      bbox: t.bbox,
      image_index: t.image_index ?? 0,
    }));

  const activeBoxes = overlayMode === 'rules' ? ruleBoxes : overlayMode === 'tokens' ? tokenBoxes : [...ruleBoxes, ...tokenBoxes];

  const getStatusColor = (status: string, isSelected: boolean) => {
    if (status === 'PASS') {
      return {
        border: isSelected ? '#15803d' : '#22c55e',
        fill: isSelected ? 'rgba(34, 197, 94, 0.45)' : 'rgba(34, 197, 94, 0.22)',
        badge: 'bg-emerald-600',
      };
    }
    if (status === 'FAIL') {
      return {
        border: isSelected ? '#b91c1c' : '#ef4444',
        fill: isSelected ? 'rgba(239, 68, 68, 0.45)' : 'rgba(239, 68, 68, 0.22)',
        badge: 'bg-rose-600',
      };
    }
    return {
      border: isSelected ? '#b45309' : '#f59e0b',
      fill: isSelected ? 'rgba(245, 158, 11, 0.45)' : 'rgba(245, 158, 11, 0.22)',
      badge: 'bg-amber-600',
    };
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full">
      {/* Viewer Header Controls */}
      <div className="p-3 bg-slate-900 text-white flex flex-wrap items-center justify-between gap-2 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-xs tracking-wide uppercase text-slate-300">
            Interactive Label Inspector
          </span>
          {images.length > 1 && (
            <div className="flex items-center bg-slate-800 rounded p-0.5 space-x-1">
              {images.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => onPanelChange(idx)}
                  className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                    activePanelIndex === idx
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Panel {idx + 1}
                </button>
              ))}
            </div>
          )}
          <span className="text-[11px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
            {activeBoxes.length} Regions Mapped
          </span>
        </div>

        {/* View toggles & zoom */}
        <div className="flex items-center space-x-2">
          {/* Overlay switch */}
          <div className="flex items-center bg-slate-800 rounded p-0.5 text-xs">
            <button
              onClick={() => setOverlayMode('rules')}
              className={`px-2 py-0.5 rounded text-[11px] transition ${
                overlayMode === 'rules' ? 'bg-blue-600 text-white font-medium' : 'text-slate-400 hover:text-white'
              }`}
            >
              Rules
            </button>
            <button
              onClick={() => setOverlayMode('tokens')}
              className={`px-2 py-0.5 rounded text-[11px] transition ${
                overlayMode === 'tokens' ? 'bg-blue-600 text-white font-medium' : 'text-slate-400 hover:text-white'
              }`}
            >
              OCR Tokens
            </button>
            <button
              onClick={() => setOverlayMode('both')}
              className={`px-2 py-0.5 rounded text-[11px] transition ${
                overlayMode === 'both' ? 'bg-blue-600 text-white font-medium' : 'text-slate-400 hover:text-white'
              }`}
            >
              Both
            </button>
          </div>

          {/* Zoom controls */}
          <button
            onClick={() => setZoom((z) => Math.max(0.75, z - 0.25))}
            className="p-1 hover:bg-slate-800 text-slate-300 rounded cursor-pointer"
            title={t('viewer.zoom_out')}
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-[11px] font-mono text-slate-400 w-9 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.min(2.5, z + 0.25))}
            className="p-1 hover:bg-slate-800 text-slate-300 rounded cursor-pointer"
            title={t('viewer.zoom_in')}
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(1)}
            className="p-1 hover:bg-slate-800 text-slate-300 rounded cursor-pointer"
            title={t('viewer.reset_zoom')}
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Canvas Viewport */}
      <div className="relative flex-1 bg-slate-950 overflow-auto flex items-center justify-center p-4 min-h-[420px]">
        <div
          className="relative inline-block transition-transform duration-150 ease-out origin-center"
          style={{ transform: `scale(${zoom})` }}
        >
          {/* Label Image */}
          <img
            src={currentImageUrl}
            alt="Packaged Product Label"
            className="max-h-[540px] w-auto rounded shadow-2xl block select-none"
          />

          {/* SVG Overlay for Bounding Boxes */}
          <svg className="absolute inset-0 w-full h-full pointer-events-auto">
            {activeBoxes.map((box) => {
              const isSelected = selectedRuleId === box.id;
              const isHovered = hoveredBox?.id === box.id;
              const colors = getStatusColor(box.status, isSelected || isHovered);

              return (
                <g
                  key={box.id}
                  className="cursor-pointer transition-all"
                  onClick={() => onSelectRule(box.type === 'rule' ? (isSelected ? null : box.id) : null)}
                  onMouseEnter={() => setHoveredBox(box)}
                  onMouseLeave={() => setHoveredBox(null)}
                >
                  <rect
                    x={`${box.bbox.x}%`}
                    y={`${box.bbox.y}%`}
                    width={`${box.bbox.width}%`}
                    height={`${box.bbox.height}%`}
                    fill={colors.fill}
                    stroke={colors.border}
                    strokeWidth={isSelected ? 3 : 1.5}
                    strokeDasharray={box.status === 'NEEDS_REVIEW' ? '4 2' : 'none'}
                    rx="3"
                  />
                  {/* Status Indicator Pip */}
                  <circle
                    cx={`${box.bbox.x}%`}
                    cy={`${box.bbox.y}%`}
                    r={isSelected ? 5 : 3.5}
                    fill={colors.border}
                  />
                </g>
              );
            })}
          </svg>

          {/* Dynamic Hover Tooltip */}
          {hoveredBox && (
            <div
              className="absolute z-30 pointer-events-none bg-slate-900/95 text-white text-xs rounded-md px-2.5 py-1.5 shadow-xl border border-slate-700 backdrop-blur-sm max-w-xs -translate-y-full mb-2"
              style={{
                left: `${hoveredBox.bbox.x}%`,
                top: `${hoveredBox.bbox.y}%`,
              }}
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="font-bold text-[11px] text-slate-200">{hoveredBox.title}</span>
                <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                  {Math.round(hoveredBox.confidence * 100)}% conf
                </span>
              </div>
              <p className="text-[10px] text-slate-300 italic line-clamp-2">
                "{hoveredBox.text}"
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Legend Footer */}
      <div className="p-2.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
        <div className="flex items-center space-x-4">
          <span className="font-semibold text-slate-700 text-[11px]">Legend:</span>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
            <span className="text-[11px]">Compliant Declaration</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500 inline-block" />
            <span className="text-[11px]">Rule Violation</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" />
            <span className="text-[11px]">Needs Review / Scale Required</span>
          </div>
        </div>
        <div className="text-[11px] text-slate-400">
          Click any bounding box to highlight rule
        </div>
      </div>
    </div>
  );
};

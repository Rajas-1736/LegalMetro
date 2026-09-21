import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { RuleResultItem } from '../../types';
import { CheckCircle2, XCircle, AlertTriangle, FileText, ChevronRight, Scale, Download, Mail } from 'lucide-react';
import { api } from '../../api/client';

interface RuleChecklistPanelProps {
  scanId?: string;
  productName?: string;
  category?: string;
  inspectorName?: string;
  createdAt?: string;
  ruleResults: RuleResultItem[];
  overallVerdict: string;
  complianceScore: number;
  selectedRuleId: string | null;
  onSelectRule: (ruleId: string | null) => void;
  onViewReport: () => void;
}

export const RuleChecklistPanel: React.FC<RuleChecklistPanelProps> = ({
  scanId,
  productName,
  category,
  inspectorName,
  createdAt,
  ruleResults,
  overallVerdict,
  complianceScore,
  selectedRuleId,
  onSelectRule,
  onViewReport,
}) => {
  const { t } = useTranslation();
  const [hasDownloadedPdf, setHasDownloadedPdf] = useState<boolean>(false);

  const handleDownloadPdf = () => {
    if (scanId) {
      window.open(api.reports.getPdfDownloadUrl(scanId), '_blank');
      setHasDownloadedPdf(true);
    }
  };

  const handleOpenGmail = () => {
    const prod = productName || 'Packaged Commodity';
    const verdict = overallVerdict || 'INSPECTION COMPLETE';
    const score = complianceScore !== undefined ? `${complianceScore}%` : 'N/A';
    const dateStr = createdAt ? new Date(createdAt).toLocaleDateString() : new Date().toLocaleDateString();

    const subject = `VisionX Statutory Inspection Report: ${prod} [${verdict}]`;
    const body = `Respected Official,\n\nPlease find attached the statutory compliance inspection report for "${prod}" generated via VisionX (Legal Metrology Compliance Enforcement System).\n\n--- INSPECTION SUMMARY ---\n• Product Name: ${prod}\n• Category: ${category || 'Packaged Goods'}\n• Final Verdict: ${verdict}\n• Compliance Score: ${score}\n• Inspection Case ID: ${scanId || 'N/A'}\n• Date of Inspection: ${dateStr}\n• Inspecting Officer: ${inspectorName || 'Legal Metrology Enforcement Officer'}\n---------------------------\n\n(Note: The official inspection PDF report has been downloaded to this device and can be attached to this email.)\n\nRegards,\nLegal Metrology Enforcement Directorate\nMinistry of Consumer Affairs, Government of India`;

    const isMobile = /Android|iPhone|iPad|iPod|Opera Mini|IEMobile|WPDesktop/i.test(navigator.userAgent);

    if (isMobile) {
      // Launch native email client / Gmail on mobile via RFC-compliant mailto
      const mailtoUri = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body.replace(/\n/g, '\r\n'))}`;
      const link = document.createElement('a');
      link.href = mailtoUri;
      link.rel = 'noopener noreferrer';
      document.body.appendChild(link);
      link.click();
      setTimeout(() => {
        try { document.body.removeChild(link); } catch (_) {}
      }, 150);
    } else {
      const gmailWebUrl = `https://mail.google.com/mail/?view=cm&fs=1&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      window.open(gmailWebUrl, '_blank', 'noopener,noreferrer');
    }
  };
  const getVerdictStyle = (verdict: string) => {
    switch (verdict) {
      case 'COMPLIANT':
        return 'bg-emerald-50 text-emerald-800 border-emerald-300';
      case 'NON_COMPLIANT':
        return 'bg-rose-50 text-rose-800 border-rose-300';
      case 'FLAGGED_FOR_REVIEW':
      case 'NEEDS_MANUAL_INSPECTION':
        return 'bg-amber-50 text-amber-800 border-amber-300';
      default:
        return 'bg-slate-50 text-slate-800 border-slate-300';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PASS':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />;
      case 'FAIL':
        return <XCircle className="w-4 h-4 text-rose-600 shrink-0" />;
      case 'NEEDS_REVIEW':
        return <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />;
      default:
        return null;
    }
  };

  const isCompliant = overallVerdict === 'COMPLIANT';
  const isViolation = overallVerdict === 'NON_COMPLIANT';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col h-full overflow-hidden animate-in fade-in duration-300">
      
      {/* Top Verdict & Score Card */}
      <div className="p-4 border-b border-slate-200 bg-slate-50 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            {t('checklist.title')}
          </span>
          <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-blue-100 text-blue-800">
            {t('common.score')}: {complianceScore}%
          </span>
        </div>

        <div className={`p-3.5 rounded-xl border flex items-center justify-between shadow-sm transition-all ${getVerdictStyle(overallVerdict)}`}>
          <div className="flex items-center space-x-3">
            {isCompliant ? (
              <div className="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-md shadow-emerald-600/30 animate-in zoom-in-90 duration-300">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            ) : isViolation ? (
              <div className="w-9 h-9 rounded-xl bg-rose-600 text-white flex items-center justify-center shadow-md shadow-rose-600/30 animate-in zoom-in-90 duration-300">
                <XCircle className="w-5 h-5" />
              </div>
            ) : (
              <div className="w-9 h-9 rounded-xl bg-amber-500 text-white flex items-center justify-center shadow-md shadow-amber-500/30">
                <AlertTriangle className="w-5 h-5" />
              </div>
            )}
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-wider opacity-80">{t('checklist.overall_verdict')}</div>
              <div className="text-base font-extrabold tracking-tight">
                {overallVerdict === 'COMPLIANT'
                  ? t('status.compliant')
                  : overallVerdict === 'NON_COMPLIANT'
                  ? t('status.non_compliant')
                  : t('status.needs_review')}
              </div>
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs font-bold">
              {ruleResults.filter((r) => r.status === 'PASS').length}/{ruleResults.length} {t('status.pass')}
            </span>
          </div>
        </div>
      </div>

      {/* Checklist items */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 divide-y divide-slate-100">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1 pt-1">
          Mandatory Declarations (2011 Rules)
        </div>

        {ruleResults.map((rule) => {
          const isSelected = selectedRuleId === rule.rule_id;
          const hasBox = !!rule.bbox;
          const isFail = rule.status === 'FAIL';

          return (
            <div
              key={rule.rule_id}
              onClick={() => onSelectRule(isSelected ? null : rule.rule_id)}
              className={`p-2.5 rounded-lg border transition cursor-pointer ${
                isSelected
                  ? 'bg-blue-50/80 border-blue-400 shadow-sm ring-1 ring-blue-400'
                  : isFail
                  ? 'bg-rose-50/40 border-rose-200/90 hover:bg-rose-50/70 hover:border-rose-300'
                  : 'bg-white border-slate-200/80 hover:bg-slate-50 hover:border-slate-300'
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <div className="flex items-center space-x-1.5 min-w-0">
                  {getStatusIcon(rule.status)}
                  <h4 className="font-semibold text-xs text-slate-900 truncate">
                    {rule.title}
                  </h4>
                </div>

                <div className="flex items-center space-x-1 shrink-0">
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                    rule.status === 'PASS'
                      ? 'bg-emerald-100 text-emerald-800'
                      : rule.status === 'FAIL'
                      ? 'bg-rose-100 text-rose-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}>
                    {rule.status === 'PASS'
                      ? t('status.pass')
                      : rule.status === 'FAIL'
                      ? t('status.fail')
                      : t('status.warning')}
                  </span>
                  {rule.image_index !== undefined && rule.image_index > 0 && (
                    <span className="text-[9px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded border border-blue-200 font-medium">
                      Panel {rule.image_index + 1}
                    </span>
                  )}
                  {rule.cross_referenced && (
                    <span className="text-[9px] bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded border border-indigo-200 font-medium">
                      Cross-Ref
                    </span>
                  )}
                  {hasBox && (
                    <span className="text-[9px] bg-slate-100 text-slate-600 px-1 py-0.5 rounded border border-slate-200">
                      BBox
                    </span>
                  )}
                </div>
              </div>

              {/* Clause Reference */}
              <div className="text-[10px] font-mono text-slate-500 mb-1.5">
                {rule.clause_reference}
              </div>

              {/* Declared Text / Extraction */}
              {rule.extracted_value && (
                <div className="text-xs bg-slate-50 p-1.5 rounded text-slate-700 font-mono mb-1.5 border border-slate-100 line-clamp-2">
                  <span className="text-slate-400 select-none">Found: </span>
                  "{rule.extracted_value}"
                </div>
              )}

              {/* Inspector Remarks */}
              <p className="text-[11px] text-slate-600 leading-snug">
                {rule.remarks}
              </p>
            </div>
          );
        })}
      </div>

      {/* Action Footer */}
      <div className="p-3 bg-slate-50 border-t border-slate-200 space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={handleDownloadPdf}
            className="flex items-center justify-center space-x-1.5 bg-slate-800 hover:bg-slate-900 text-white py-2.5 px-3 rounded-lg font-semibold text-xs shadow transition active:scale-[0.99] cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </button>
          
          <button
            type="button"
            onClick={onViewReport}
            className="flex items-center justify-center space-x-1.5 bg-blue-600 hover:bg-blue-700 text-white py-2.5 px-3 rounded-lg font-semibold text-xs shadow transition active:scale-[0.99] cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>{t('checklist.btn_view_report')}</span>
          </button>
        </div>

        {hasDownloadedPdf && (
          <button
            type="button"
            onClick={handleOpenGmail}
            style={{ backgroundColor: '#ea4335', color: '#ffffff' }}
            className="w-full flex items-center justify-center space-x-2 text-white py-2.5 px-4 rounded-lg font-bold text-xs shadow-md transition active:scale-[0.99] cursor-pointer"
            title="Open Gmail with official inspection summary"
          >
            <Mail className="w-4 h-4 shrink-0" style={{ stroke: '#ffffff' }} />
            <span style={{ color: '#ffffff' }}>Mail Report via Gmail</span>
          </button>
        )}
      </div>
    </div>
  );
};

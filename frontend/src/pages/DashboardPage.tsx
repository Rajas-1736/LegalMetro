import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import { DashboardStats } from '../types';
import { 
  ShieldCheck, AlertTriangle, TrendingUp, Users, CheckCircle2, 
  XCircle, Clock, FileCheck, ArrowRight 
} from 'lucide-react';
import { 
  AreaChart, Area, BarChart, Bar, Cell, XAxis, YAxis, 
  CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';

interface DashboardPageProps {
  onViewScan: (scanId: string) => void;
  onNewScan: () => void;
}

const AnimatedCounter: React.FC<{ value: string }> = ({ value }) => {
  const [displayValue, setDisplayValue] = useState<string>('0');

  useEffect(() => {
    const match = value.match(/^([^0-9]*)([0-9,]+(?:\.[0-9]+)?)(.*)$/);
    if (!match) {
      setDisplayValue(value);
      return;
    }

    const prefix = match[1] || '';
    const cleanNumStr = match[2].replace(/,/g, '');
    const targetNum = parseFloat(cleanNumStr);
    const suffix = match[3] || '';

    if (isNaN(targetNum)) {
      setDisplayValue(value);
      return;
    }

    const start = 0;
    const duration = 850;
    const startTime = performance.now();

    const updateCounter = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Smooth quintic ease-out curve for premium SaaS feel
      const easeOut = 1 - Math.pow(1 - progress, 4);
      const current = Math.round(start + (targetNum - start) * easeOut);

      setDisplayValue(`${prefix}${current.toLocaleString()}${suffix}`);

      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      } else {
        setDisplayValue(value);
      }
    };

    requestAnimationFrame(updateCounter);
  }, [value]);

  return <span>{displayValue}</span>;
};

export const DashboardPage: React.FC<DashboardPageProps> = ({ onViewScan, onNewScan }) => {
  const { t } = useTranslation();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const getLocalizedRuleTitle = (ruleId: string, defaultTitle: string) => {
    const key = `rules_def.${ruleId}.title`;
    const translated = t(key);
    if (translated !== key) return translated;
    if (defaultTitle.includes("Background Color Contrast")) return t('rules_def.RULE_9_CONTRAST.title', { defaultValue: defaultTitle });
    if (defaultTitle.includes("Second Schedule") || defaultTitle.includes("Shrinkflation")) return t('rules_def.RULE_5_SHRINKFLATION.title', { defaultValue: defaultTitle });
    if (defaultTitle.includes("Maximum Retail Price") || defaultTitle.includes("MRP")) return t('rules_def.RULE_6_1_E.title', { defaultValue: defaultTitle });
    if (defaultTitle.includes("Unit Sale Price") || defaultTitle.includes("USP")) return t('rules_def.RULE_6_1_E_USP.title', { defaultValue: defaultTitle });
    if (defaultTitle.includes("Month and Year") || defaultTitle.includes("Date")) return t('rules_def.RULE_6_1_D.title', { defaultValue: defaultTitle });
    if (defaultTitle.includes("Net Quantity")) return t('rules_def.RULE_6_1_C.title', { defaultValue: defaultTitle });
    if (defaultTitle.includes("Consumer Care")) return t('rules_def.RULE_6_1_F.title', { defaultValue: defaultTitle });
    if (defaultTitle.includes("Manufacturer") || defaultTitle.includes("Packer")) return t('rules_def.RULE_6_1_A.title', { defaultValue: defaultTitle });
    return defaultTitle;
  };

  const getLocalizedRuleClause = (ruleId: string, defaultClause: string) => {
    const key = `rules_def.${ruleId}.clause`;
    const translated = t(key);
    if (translated !== key) return translated;
    if (defaultClause.includes("9(1)(b)")) return t('rules_def.RULE_9_CONTRAST.clause', { defaultValue: defaultClause });
    if (defaultClause.includes("Rule 5")) return t('rules_def.RULE_5_SHRINKFLATION.clause', { defaultValue: defaultClause });
    if (defaultClause.includes("Second Proviso")) return t('rules_def.RULE_6_1_E_USP.clause', { defaultValue: defaultClause });
    if (defaultClause.includes("6(1)(e)")) return t('rules_def.RULE_6_1_E.clause', { defaultValue: defaultClause });
    if (defaultClause.includes("6(1)(d)")) return t('rules_def.RULE_6_1_D.clause', { defaultValue: defaultClause });
    return defaultClause;
  };

  const getLocalizedCategory = (category: string) => {
    const norm = category.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    const key = `category.${norm}`;
    const translated = t(key);
    return translated !== key ? translated : category;
  };

  const getLocalizedMetricLabel = (label: string) => {
    const norm = label.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    const key = `dashboard.metric_${norm}`;
    const translated = t(key);
    return translated !== key ? translated : label;
  };

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const data = await api.dashboard.getStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to load dashboard stats', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-3">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-semibold text-slate-500 font-mono">{t('common.loading')}</span>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      
      {/* Top Banner - Soft Shadow, Confident Authority */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-md shadow-slate-900/10 flex flex-col md:flex-row md:items-center justify-between gap-4 border border-slate-800 animate-enter-up">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="bg-blue-500/20 text-blue-400 text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded border border-blue-500/30 font-semibold">
              {t('nav.badge_enforcement')}
            </span>
            <span className="text-slate-400 text-xs">• {t('dashboard.live_analytics', 'Live Enforcement Analytics')}</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight">
            {t('dashboard.title')}
          </h1>
          <p className="text-xs text-slate-400 max-w-2xl">
            {t('dashboard.subtitle')}
          </p>
        </div>

        <button
          onClick={onNewScan}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl text-xs shadow-md shadow-blue-600/30 hover:shadow-lg hover:shadow-blue-500/40 hover:scale-[1.02] active:scale-[0.98] transition-all duration-150 flex items-center space-x-2 self-start cursor-pointer"
        >
          <span>{t('dashboard.new_scan')}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards - Staggered entrance, animated counter & hover lift */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.metrics.map((m, idx) => {
          const delayClass = 
            idx === 0 ? 'animation-delay-75' :
            idx === 1 ? 'animation-delay-150' :
            idx === 2 ? 'animation-delay-225' : 'animation-delay-300';

          return (
            <div 
              key={idx} 
              className={`bg-white p-5 rounded-2xl border border-slate-200/90 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 space-y-2 group animate-enter-up ${delayClass}`}
            >
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider group-hover:text-slate-700 transition">
                {getLocalizedMetricLabel(m.label)}
              </div>
              <div className="text-2xl font-black text-slate-900 font-mono tracking-tight">
                <AnimatedCounter value={m.value} />
              </div>
              {m.change && (
                <div className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
                  <span className={m.trend === 'up' ? 'text-emerald-600 font-bold' : m.trend === 'down' ? 'text-rose-600 font-bold' : 'text-amber-600 font-bold'}>
                    {m.change}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Main Charts Row - Animated draw-in with subtle styling */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-enter-up animation-delay-225">
        
        {/* 7-Day Trend Chart */}
        <div className="lg:col-span-7 bg-white p-5 rounded-2xl border border-slate-200/90 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">{t('dashboard.chart_trend_title')}</h3>
              <p className="text-xs text-slate-500">{t('dashboard.chart_trend_subtitle', 'Daily breakdown of conducted inspections and identified infractions')}</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.violation_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCompliant" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#15803d" stopOpacity={0.08}/>
                    <stop offset="95%" stopColor="#15803d" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorViolations" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#be123c" stopOpacity={0.08}/>
                    <stop offset="95%" stopColor="#be123c" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip contentStyle={{ fontSize: '12px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Area 
                  type="monotone" 
                  dataKey="compliant" 
                  name={t('dashboard.chart_compliant_packages')} 
                  stroke="#15803d" 
                  fillOpacity={1} 
                  fill="url(#colorCompliant)" 
                  strokeWidth={1.5} 
                  isAnimationActive={true}
                  animationDuration={1200}
                  animationEasing="ease-out"
                />
                <Area 
                  type="monotone" 
                  dataKey="violations" 
                  name={t('dashboard.chart_infractions')} 
                  stroke="#be123c" 
                  fillOpacity={1} 
                  fill="url(#colorViolations)" 
                  strokeWidth={1.5} 
                  isAnimationActive={true}
                  animationDuration={1200}
                  animationEasing="ease-out"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Violations by Category Bar Chart */}
        <div className="lg:col-span-5 bg-white p-5 rounded-2xl border border-slate-200/90 shadow-sm space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">{t('dashboard.chart_rules_title')}</h3>
              <p className="text-xs text-slate-500">{t('dashboard.chart_rules_subtitle', 'Percentage of compliant packages across consumer sectors')}</p>
            </div>
            <div className="hidden sm:flex items-center gap-2 text-[10px] text-slate-400 font-medium">
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[#15803d]" /> ≥85%</span>
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[#2563eb]" /> 70-84%</span>
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[#c2410c]" /> &lt;70%</span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.category_breakdown} margin={{ top: 10, right: 10, left: -20, bottom: 0 }} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} stroke="#94a3b8" unit="%" />
                <YAxis type="category" dataKey="category" tick={{ fontSize: 10 }} width={90} stroke="#94a3b8" tickFormatter={(val) => getLocalizedCategory(val)} />
                <Tooltip formatter={(value) => `${value}%`} contentStyle={{ fontSize: '12px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }} />
                <Bar 
                  dataKey="compliance_rate" 
                  name={t('dashboard.chart_rule_rate')} 
                  radius={[0, 4, 4, 0]}
                  isAnimationActive={true}
                  animationDuration={1100}
                  animationEasing="ease-out"
                >
                  {stats.category_breakdown.map((entry, index) => {
                    const barColor = entry.compliance_rate >= 85 
                    ? '#15803d' 
                    : entry.compliance_rate >= 70 
                    ? '#2563eb' 
                    : '#c2410c';
                    return <Cell key={`cell-${index}`} fill={barColor} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Bottom Section: Top Violations & Inspector Leaderboard */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-enter-up animation-delay-300">
        
        {/* Top Violations */}
        <div className="lg:col-span-6 bg-white p-5 rounded-2xl border border-slate-200/90 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-slate-900">{t('dashboard.top_infractions_title', 'Most Prevalent Legal Metrology Infractions')}</h3>
          <p className="text-xs text-slate-500">{t('dashboard.top_infractions_subtitle', 'Top mandatory rule violations detected during surveillance scans')}</p>

          <div className="space-y-3 pt-2">
            {stats.top_violation_types.map((v) => (
              <div key={v.rule_id} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-800">{getLocalizedRuleTitle(v.rule_id, v.title)}</span>
                  <span className="text-[#be123c] font-mono">{v.count} {t('dashboard.violations', 'violations')} ({v.percentage}%)</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-[#be123c] h-2 rounded-full" style={{ width: `${Math.min(100, v.percentage * 2)}%` }} />
                </div>
                <div className="text-[10px] text-slate-400 font-mono">{getLocalizedRuleClause(v.rule_id, v.clause)}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Active Inspectors */}
        <div className="lg:col-span-6 bg-white p-5 rounded-2xl border border-slate-200/90 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-slate-900">{t('dashboard.officer_log_title', 'Enforcement Officer Surveillance Log')}</h3>
          <p className="text-xs text-slate-500">{t('dashboard.officer_log_subtitle', 'Officer inspection quota and violation identification records')}</p>

          <div className="divide-y divide-slate-100">
            {stats.inspector_stats.map((insp, idx) => (
              <div key={idx} className="py-3 flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-slate-900">{insp.inspector_name}</div>
                  <div className="text-[10px] text-slate-400 font-mono">{t('dashboard.badge_label', 'Badge:')} {insp.badge_number}</div>
                </div>
                <div className="text-right">
                  <span className="text-xs font-bold text-blue-600 font-mono">{insp.inspections_count} {t('dashboard.scans', 'Scans')}</span>
                  <div className="text-[10px] text-[#be123c] font-semibold">{insp.violations_detected} {t('dashboard.infractions_flagged', 'Infractions Flagged')}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Recent Scans Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden space-y-3 p-5 animate-enter-up animation-delay-375">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">{t('dashboard.recent_table_title')}</h3>
            <p className="text-xs text-slate-500">{t('dashboard.recent_table_subtitle')}</p>
          </div>
        </div>

        <div className="overflow-x-auto w-full">
          <table className="w-full text-left text-xs border-collapse min-w-[620px]">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 uppercase font-bold text-[10px] tracking-wider">
              <tr>
                <th className="p-3">{t('dashboard.col_product')}</th>
                <th className="p-3">{t('common.category')}</th>
                <th className="p-3">{t('dashboard.col_inspector', 'Inspecting Officer')}</th>
                <th className="p-3">{t('common.status')}</th>
                <th className="p-3">{t('common.score')}</th>
                <th className="p-3 text-right">{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {stats.recent_scans.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/70 transition">
                  <td className="p-3 font-bold text-slate-900">{s.product_name}</td>
                  <td className="p-3 text-slate-600">{getLocalizedCategory(s.category)}</td>
                  <td className="p-3 text-slate-600">{s.inspector_name}</td>
                  <td className="p-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                      s.verdict === 'COMPLIANT'
                        ? 'bg-emerald-50 text-[#15803d] border-emerald-200'
                        : s.verdict === 'NON_COMPLIANT'
                        ? 'bg-rose-50 text-[#be123c] border-rose-200'
                        : 'bg-amber-50 text-[#b45309] border-amber-200'
                    }`}>
                      {s.verdict === 'COMPLIANT'
                        ? t('status.compliant')
                        : s.verdict === 'NON_COMPLIANT'
                        ? t('status.non_compliant')
                        : t('status.needs_review')}
                    </span>
                  </td>
                  <td className="p-3 font-mono font-bold text-slate-700">{s.compliance_score}%</td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => onViewScan(s.id)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-semibold cursor-pointer"
                    >
                      {t('common.view_report')} →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};

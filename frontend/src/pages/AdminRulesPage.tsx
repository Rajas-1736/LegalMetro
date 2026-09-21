import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import { RuleConfig } from '../types';
import { Sliders, ShieldCheck, Edit3, Save, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

export const AdminRulesPage: React.FC = () => {
  const { t } = useTranslation();
  const [rules, setRules] = useState<RuleConfig[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [editingRule, setEditingRule] = useState<RuleConfig | null>(null);
  const [saving, setSaving] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const data = await api.admin.getRules();
      setRules(data);
    } catch (err) {
      console.error('Failed to load rules', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleToggleActive = async (rule: RuleConfig) => {
    try {
      const updated = await api.admin.updateRule(rule.rule_id, {
        is_active: !rule.is_active,
      });
      setRules((prev) => prev.map((r) => (r.rule_id === rule.rule_id ? updated : r)));
      setSuccessMsg(t('rules.msg_status_updated', { ruleId: rule.rule_id, defaultValue: `Rule ${rule.rule_id} status updated.` }));
      setTimeout(() => setSuccessMsg(null), 2500);
    } catch (err) {
      console.error('Failed to toggle rule', err);
    }
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRule) return;

    setSaving(true);
    try {
      const updated = await api.admin.updateRule(editingRule.rule_id, {
        title: editingRule.title,
        description: editingRule.description,
        severity: editingRule.severity,
      });
      setRules((prev) => prev.map((r) => (r.rule_id === editingRule.rule_id ? updated : r)));
      setEditingRule(null);
      setSuccessMsg(t('rules.msg_rule_updated', { ruleId: editingRule.rule_id, defaultValue: `Rule ${editingRule.rule_id} successfully updated and applied live to the Rule Engine.` }));
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      console.error('Failed to update rule', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Sliders className="w-5 h-5 text-blue-600" />
            <span>{t('rules.live_config_title', 'Legal Metrology Rules 2011 • Live Configuration')}</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {t('rules.live_config_subtitle', 'Judges Panel Feature: Live-configurable statutory rules taking immediate effect in the compliance evaluation engine without redeploying code.')}
          </p>
        </div>

        <button
          onClick={fetchRules}
          className="p-2 border rounded-lg hover:bg-slate-50 text-slate-600 self-start"
          title={t('rules.refresh', 'Refresh Rules')}
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-lg text-emerald-800 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Rules Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400">{t('rules.loading', 'Loading statutory rule definitions...')}</div>
        ) : (
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-xs border-collapse min-w-[640px]">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 uppercase font-bold text-[10px] tracking-wider">
              <tr>
                <th className="p-3.5 w-16">{t('rules.col_active', 'Active')}</th>
                <th className="p-3.5 w-1/4">{t('rules.col_rule_id', 'Rule ID & Legal Clause')}</th>
                <th className="p-3.5">{t('rules.col_title_desc', 'Title & Enforcement Description')}</th>
                <th className="p-3.5 w-36">{t('rules.col_severity', 'Severity')}</th>
                <th className="p-3.5 text-right w-24">{t('rules.col_actions', 'Actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rules.map((rule) => (
                <tr key={rule.id} className={`hover:bg-slate-50/70 transition ${!rule.is_active ? 'opacity-50' : ''}`}>
                  
                  {/* Toggle Active Checkbox */}
                  <td className="p-3.5">
                    <input
                      type="checkbox"
                      checked={rule.is_active}
                      onChange={() => handleToggleActive(rule)}
                      className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 cursor-pointer"
                    />
                  </td>

                  {/* Rule ID & Citation */}
                  <td className="p-3.5">
                    <div className="font-mono font-bold text-blue-900">{rule.rule_id}</div>
                    <div className="text-[10px] text-slate-500 font-mono mt-0.5">{rule.clause_reference}</div>
                  </td>

                  {/* Title & Description */}
                  <td className="p-3.5">
                    <div className="font-bold text-slate-900">{rule.title}</div>
                    <div className="text-[11px] text-slate-500 leading-snug mt-0.5 line-clamp-2">{rule.description}</div>
                  </td>

                  {/* Severity Badge */}
                  <td className="p-3.5">
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      rule.severity === 'MANDATORY_VIOLATION'
                        ? 'bg-rose-100 text-rose-800'
                        : rule.severity === 'WARNING'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-slate-100 text-slate-800'
                    }`}>
                      {rule.severity === 'MANDATORY_VIOLATION'
                        ? t('status.mandatory_violation', 'MANDATORY VIOLATION')
                        : rule.severity === 'WARNING'
                        ? t('status.warning', 'WARNING')
                        : rule.severity === 'INFORMATIVE'
                        ? t('status.informative', 'INFORMATIVE')
                        : rule.severity.replace('_', ' ')}
                    </span>
                  </td>

                  {/* Action Edit */}
                  <td className="p-3.5 text-right">
                    <button
                      onClick={() => setEditingRule(rule)}
                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition font-semibold"
                      title={t('rules.btn_edit', 'Edit Parameters')}
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </div>

      {/* Edit Rule Modal */}
      {editingRule && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-sm text-slate-900">
                {t('rules.edit_rule_title', { ruleId: editingRule.rule_id, defaultValue: `Edit Statutory Rule: ${editingRule.rule_id}` })}
              </h3>
              <button
                onClick={() => setEditingRule(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('rules.field_rule_title', 'Rule Title')}
                </label>
                <input
                  type="text"
                  required
                  value={editingRule.title}
                  onChange={(e) => setEditingRule({ ...editingRule, title: e.target.value })}
                  className="w-full text-xs p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('rules.field_severity', 'Enforcement Severity Level')}
                </label>
                <select
                  value={editingRule.severity}
                  onChange={(e) => setEditingRule({ ...editingRule, severity: e.target.value })}
                  className="w-full text-xs p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                >
                  <option value="MANDATORY_VIOLATION">{t('rules.severity_mandatory_desc', 'MANDATORY VIOLATION (Strict Liability)')}</option>
                  <option value="WARNING">{t('rules.severity_warning_desc', 'WARNING (Minor Non-Compliance)')}</option>
                  <option value="INFORMATIVE">{t('rules.severity_informative_desc', 'INFORMATIVE (Advisory Only)')}</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('rules.field_desc', 'Legal Description / Inspector Guidance')}
                </label>
                <textarea
                  rows={3}
                  required
                  value={editingRule.description}
                  onChange={(e) => setEditingRule({ ...editingRule, description: e.target.value })}
                  className="w-full text-xs p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setEditingRule(null)}
                  className="px-3 py-1.5 rounded-lg border text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  {t('rules.btn_cancel', 'Cancel')}
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow transition disabled:opacity-50"
                >
                  {saving ? t('rules.btn_updating', 'Updating...') : t('rules.btn_save_live', 'Save & Apply Live')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

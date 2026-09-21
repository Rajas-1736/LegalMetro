import React from 'react';
import { useTranslation } from 'react-i18next';
import { LayoutDashboard, ScanLine, PackageSearch, FileText, Sliders, ShieldAlert, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, isOpen = false, onClose }) => {
  const { user, canManageRules, canScanAndReport } = useAuth();
  const { t } = useTranslation();

  const navItems = [
    { id: 'dashboard', label: t('nav.dashboard'), icon: LayoutDashboard },
    { id: 'scan', label: t('nav.scan'), icon: ScanLine, disabled: !canScanAndReport },
    { id: 'repository', label: t('nav.repository'), icon: PackageSearch },
    { id: 'reports', label: t('nav.reports'), icon: FileText },
    { id: 'rules', label: t('nav.rules'), icon: Sliders, adminOnly: true },
  ];

  const handleItemClick = (id: string) => {
    setActiveTab(id);
    if (onClose) {
      onClose();
    }
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 md:hidden transition-opacity"
          aria-hidden="true"
        />
      )}

      {/* Sidebar / Mobile Drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4 transition-transform duration-300 ease-in-out md:static md:w-64 md:translate-x-0 md:min-h-[calc(100vh-4rem)] md:shrink-0 ${
          isOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="space-y-6">
          {/* Mobile Drawer Close Header */}
          <div className="flex items-center justify-between pb-2 border-b border-slate-800 md:hidden">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
              {t('nav.menu_title')}
            </span>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
              aria-label="Close navigation drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        
        {/* Navigation list */}
        <div className="space-y-1">
          <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {t('nav.menu_title')}
          </div>
          {navItems.map((item) => {
            if (item.adminOnly && !canManageRules) return null;
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => !item.disabled && handleItemClick(item.id)}
                disabled={item.disabled}
                className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20 font-semibold'
                    : item.disabled
                    ? 'text-slate-600 cursor-not-allowed'
                    : 'text-slate-300 hover:bg-slate-800/70 hover:text-white'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
                {item.disabled && (
                  <span className="ml-auto text-[10px] bg-slate-800 text-slate-500 px-1.5 py-0.5 rounded">
                    {t('common.view_only')}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Legal Authority Callout */}
        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-800 text-xs text-slate-400 space-y-1.5">
          <div className="flex items-center space-x-1.5 text-slate-300 font-semibold text-xs">
            <ShieldAlert className="w-3.5 h-3.5 text-blue-400" />
            <span>{t('nav.enforcement_standard')}</span>
          </div>
          <p className="text-[11px] leading-relaxed">
            {t('nav.enforcement_standard_desc')}
          </p>
        </div>
      </div>

      {/* Footer officer info */}
      <div className="pt-4 border-t border-slate-800 text-center">
        <div className="text-[11px] text-slate-500 font-mono">
          {t('nav.badge')}: {user?.badge_number || 'LM-OFFICIAL'}
        </div>
        <div className="text-[10px] text-slate-500 mt-0.5">
          {t('nav.system_footer')}
        </div>
      </div>
    </aside>
    </>
  );
};

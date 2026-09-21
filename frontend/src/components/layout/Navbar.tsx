import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck, LogOut, Menu } from 'lucide-react';
import { LanguageSwitcher } from '../common/LanguageSwitcher';

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  const handleLogout = () => {
    const confirmed = window.confirm(
      t('nav.sign_out_confirm')
    );
    if (confirmed) {
      logout();
    }
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-40 shadow-sm w-full">
      <div className="w-full max-w-7xl mx-auto px-2.5 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center justify-between gap-1.5 sm:gap-4">
        
        {/* Brand & Government Affiliation + Mobile Toggle */}
        <div className="flex items-center space-x-1.5 sm:space-x-2.5 shrink-0">
          {user && onToggleSidebar && (
            <button
              type="button"
              onClick={onToggleSidebar}
              className="p-1.5 -ml-1 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg md:hidden transition cursor-pointer"
              aria-label="Toggle navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}

          <div className="bg-gradient-to-br from-blue-600 to-indigo-700 p-1.5 sm:p-2 rounded-xl flex items-center justify-center text-white shadow-md shadow-blue-600/30 shrink-0">
            <ShieldCheck className="w-4 h-4 sm:w-6 sm:h-6" />
          </div>
          <div className="shrink-0">
            <div className="flex items-center space-x-1.5 sm:space-x-2">
              <span className="font-extrabold text-base sm:text-lg tracking-tight text-white select-none">
                {t('nav.title')}
              </span>
              <span className="hidden md:inline-block bg-blue-500/20 text-blue-400 text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded border border-blue-500/30">
                {t('nav.badge_enforcement')}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              {t('nav.ministry_subtitle')}
            </p>
          </div>
        </div>

        {/* Right Action Area: Language Switcher, Authenticated Officer Profile & Sign Out */}
        <div className="flex items-center space-x-1.5 sm:space-x-3 shrink-0">
          <LanguageSwitcher variant="dark" />

          {user && (
            <div className="flex items-center space-x-1.5 sm:space-x-3">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-semibold text-slate-200">{user.full_name}</div>
                <div className="text-[10px] text-slate-400 font-mono">{user.badge_number || user.designation}</div>
              </div>

              <span className={`inline-flex items-center px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-md text-[9px] sm:text-[10px] font-bold tracking-wider uppercase border ${
                user.role === 'admin'
                  ? 'bg-blue-600 text-white border-blue-500 shadow-sm'
                  : user.role === 'inspector'
                  ? 'bg-blue-500/20 text-blue-300 border-blue-500/40'
                  : 'bg-slate-800 text-slate-300 border-slate-700'
              }`}>
                {user.role}
              </span>

              {/* Secure Log Out Button */}
              <button
                onClick={handleLogout}
                title={t('nav.sign_out')}
                className="flex items-center gap-1.5 p-1.5 sm:px-3 sm:py-1.5 text-xs text-slate-300 hover:text-rose-200 hover:bg-rose-950/40 border border-slate-700 hover:border-rose-800/60 rounded-lg transition font-medium shadow-sm cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{t('nav.sign_out')}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Languages, ChevronDown, Check } from 'lucide-react';
import { SUPPORTED_LANGUAGES } from '../../i18n';

interface LanguageSwitcherProps {
  variant?: 'dark' | 'light';
  className?: string;
}

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({
  variant = 'dark',
  className = '',
}) => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentLanguage =
    SUPPORTED_LANGUAGES.find((lang) => lang.code === (i18n.language || 'en').slice(0, 2)) ||
    SUPPORTED_LANGUAGES[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (code: string) => {
    i18n.changeLanguage(code);
    setIsOpen(false);
  };

  const isDark = variant === 'dark';

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
        title="Change UI Language / भाषा बदला"
        className={`flex items-center gap-1 sm:gap-2 px-1.5 sm:px-2.5 py-1 sm:py-1.5 rounded-lg text-xs font-medium transition-all shadow-xs border cursor-pointer ${
          isDark
            ? 'bg-slate-800/90 text-slate-200 border-slate-700 hover:bg-slate-700/90 hover:text-white focus:ring-2 focus:ring-blue-500/50'
            : 'bg-white/95 text-slate-700 border-slate-200 hover:bg-slate-50 hover:text-slate-900 shadow-sm focus:ring-2 focus:ring-blue-500/40 backdrop-blur-sm'
        }`}
      >
        <Languages className={`w-3.5 h-3.5 shrink-0 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
        <span className="font-medium tracking-tight hidden sm:inline">{currentLanguage.nativeName}</span>
        <span className="font-bold tracking-tight sm:hidden text-[11px] uppercase">{currentLanguage.code}</span>
        <ChevronDown className={`w-3 h-3 shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''} ${isDark ? 'text-slate-400' : 'text-slate-500'}`} />
      </button>

      {isOpen && (
        <div
          className={`absolute right-0 mt-1.5 w-44 rounded-xl shadow-xl border py-1.5 z-50 animate-in fade-in zoom-in-95 duration-100 ${
            isDark
              ? 'bg-slate-900 border-slate-800 text-slate-200 divide-y divide-slate-800/60'
              : 'bg-white border-slate-200 text-slate-800 divide-y divide-slate-100'
          }`}
        >
          <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-400">
            UI Language
          </div>
          <div className="py-1">
            {SUPPORTED_LANGUAGES.map((lang) => {
              const isSelected = (i18n.language || 'en').startsWith(lang.code);
              return (
                <button
                  key={lang.code}
                  onClick={() => handleSelect(lang.code)}
                  className={`w-full flex items-center justify-between px-3 py-2 text-xs text-left transition-colors cursor-pointer ${
                    isSelected
                      ? isDark
                        ? 'bg-blue-600/20 text-blue-400 font-semibold'
                        : 'bg-blue-50 text-blue-700 font-semibold'
                      : isDark
                      ? 'hover:bg-slate-800 text-slate-300 hover:text-white'
                      : 'hover:bg-slate-50 text-slate-700 hover:text-slate-900'
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="text-xs">{lang.nativeName}</span>
                    <span className={`text-[10px] ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                      {lang.name}
                    </span>
                  </div>
                  {isSelected && (
                    <Check className={`w-3.5 h-3.5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

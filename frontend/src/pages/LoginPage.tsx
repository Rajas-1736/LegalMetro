import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { PackagingScannerGraphic } from '../components/auth/PackagingScannerGraphic';
import { LanguageSwitcher } from '../components/common/LanguageSwitcher';
import { 
  ShieldCheck, Lock, Mail, AlertCircle, ArrowRight, 
  CheckCircle2, ChevronDown, ChevronUp, ScanLine, Eye, EyeOff,
  Scale, FileCheck, Award, Loader2
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showDemoHelper, setShowDemoHelper] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemoCredentials = (targetEmail: string, targetPass: string) => {
    setEmail(targetEmail);
    setPassword(targetPass);
    setError('');
  };

  return (
    <div className="min-h-screen w-full bg-slate-50 text-slate-900 selection:bg-blue-600 selection:text-white relative overflow-x-hidden font-sans flex items-center justify-center">
      
      {/* Top Floating Language Switcher */}
      <div className="absolute top-4 right-4 sm:right-8 z-30">
        <LanguageSwitcher variant="light" />
      </div>

      {/* Full-Bleed Ambient Background Mesh & Subtle Technical Grid */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div 
          className="absolute inset-0 opacity-40"
          style={{
            backgroundImage: `radial-gradient(#94a3b8 1px, transparent 1px)`,
            backgroundSize: '28px 28px'
          }}
        />
        {/* Soft drifting gradient blobs */}
        <div className="absolute -top-24 -left-24 w-[550px] h-[550px] bg-gradient-to-br from-blue-500/8 via-indigo-500/4 to-transparent rounded-full blur-3xl animate-float-slow" />
        <div className="absolute top-1/3 -right-24 w-[450px] h-[450px] bg-gradient-to-bl from-slate-400/8 via-blue-400/5 to-transparent rounded-full blur-3xl" />
        <div className="absolute -bottom-24 left-1/3 w-[600px] h-[600px] bg-gradient-to-tr from-slate-300/10 via-blue-500/5 to-transparent rounded-full blur-3xl" />
      </div>

      {/* Main Responsive Layout: Clean Floating Split without Center Line */}
      <div className="w-full max-w-[1400px] mx-auto px-6 py-8 sm:px-10 lg:px-12 flex flex-col lg:flex-row items-center justify-between gap-8 lg:gap-14 animate-enter-up">
        
        {/* LEFT PANEL: Showcase, Animated Packaging Scanner & Statutory Typography */}
        <div className="w-full lg:w-7/12 flex flex-col justify-between space-y-5 lg:space-y-6">
          
          {/* Top Statutory Header Badge */}
          <div className="space-y-1.5">
            <div className="inline-flex items-center space-x-2.5 px-3 py-1 rounded-full bg-white/90 border border-slate-200 shadow-xs backdrop-blur-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_#10b981]" />
              <span className="text-[10px] font-mono tracking-wider text-slate-600 uppercase font-semibold">
                {t('auth.gov_header_badge')}
              </span>
            </div>
            <div className="text-[11px] text-slate-500 font-medium pl-1">
              {t('auth.gov_division')}
            </div>
          </div>

          {/* Hero Branding & Bold Display Headline */}
          <div className="space-y-4 max-w-2xl">
            
            {/* Brand Mark */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-600/25 ring-4 ring-blue-50">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900">VisionX</span>
                  <span className="bg-blue-50 text-blue-700 text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-md border border-blue-200 font-bold">
                    Enforcement v1.0
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 font-medium">
                  {t('auth.brand_tagline')}
                </p>
              </div>
            </div>

            {/* Display Headline with Deliberate Accent Highlight */}
            <div className="space-y-2">
              <h1 className="text-2xl sm:text-3xl lg:text-[38px] font-black tracking-tight text-slate-900 leading-[1.18]">
                {t('auth.headline_main')}{' '}
                <span className="text-blue-600 relative inline-block">
                  {t('auth.headline_highlight')}
                  <span className="absolute bottom-1 left-0 right-0 h-2 bg-blue-100/90 -z-10 rounded-full" />
                </span>
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-xl font-normal">
                {t('auth.subhead')}
              </p>
            </div>

            {/* Custom Interactive Packaging Scanner Illustration */}
            <div className="py-1">
              <PackagingScannerGraphic />
            </div>

            {/* Staggered PDP Audit Checklist Ribbon */}
            <div className="bg-white border border-slate-200/90 rounded-xl p-3.5 shadow-sm space-y-2.5 backdrop-blur-sm">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <div className="flex items-center space-x-2 text-[11px] font-mono font-semibold text-slate-700">
                  <ScanLine className="w-3.5 h-3.5 text-blue-600" />
                  <span>ACTIVE COMPLIANCE SURVEILLANCE ENGINE</span>
                </div>
                <span className="inline-flex items-center gap-1 text-[9px] bg-emerald-50 text-emerald-700 border border-emerald-200/80 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Live Verification</span>
                </span>
              </div>

              {/* 4 Core Statutory Rules with pulsing checkmarks */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-xs">
                
                <div className="flex items-center space-x-1.5 bg-slate-50 p-2 rounded-lg border border-slate-100">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 animate-pulse-glow" />
                  <span className="text-slate-700 text-[10px] font-medium truncate">Rule 6(1)(a) Factory</span>
                </div>

                <div className="flex items-center space-x-1.5 bg-slate-50 p-2 rounded-lg border border-slate-100">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 animate-pulse-glow" />
                  <span className="text-slate-700 text-[10px] font-medium truncate">Rule 6(1)(e) MRP</span>
                </div>

                <div className="flex items-center space-x-1.5 bg-slate-50 p-2 rounded-lg border border-slate-100">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 animate-pulse-glow" />
                  <span className="text-slate-700 text-[10px] font-medium truncate">Rule 13 SI Units</span>
                </div>

                <div className="flex items-center space-x-1.5 bg-slate-50 p-2 rounded-lg border border-slate-100">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 animate-pulse-glow" />
                  <span className="text-slate-700 text-[10px] font-medium truncate">Schedule II Pack</span>
                </div>

              </div>
            </div>

            {/* Statutory Pillars */}
            <div className="flex flex-wrap gap-4 text-xs text-slate-600 font-medium">
              <div className="flex items-center space-x-1.5">
                <FileCheck className="w-3.5 h-3.5 text-blue-600" />
                <span className="text-[11px]">Court-Admissible Evidence</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Scale className="w-3.5 h-3.5 text-blue-600" />
                <span className="text-[11px]">Policy-as-Code Engine</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Award className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-[11px]">Tamper-Proof Audit Records</span>
              </div>
            </div>

          </div>

          {/* Footer Authority */}
          <div className="pt-3 border-t border-slate-200/80 text-[10px] text-slate-400 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1">
            <span>Official Government Enforcement Terminal</span>
            <span className="font-mono">Security Level: RESTRICTED</span>
          </div>

        </div>

        {/* RIGHT PANEL: Floating Authentication Card (Linear/Stripe Style Elevation) */}
        <div className="w-full lg:w-5/12 flex items-center justify-center">
          
          <div className="w-full max-w-md bg-white border border-slate-200/90 rounded-3xl p-7 sm:p-9 shadow-[0_20px_60px_rgba(15,23,42,0.08)] space-y-6">
            
            {/* Card Header */}
            <div className="space-y-1 text-left">
              <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center justify-between">
                <span>{t('auth.signin_title')}</span>
                <span className="text-[10px] font-mono bg-blue-50 text-blue-700 px-2.5 py-0.5 rounded-full border border-blue-200 font-semibold">
                  SSL Secured
                </span>
              </h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                {t('auth.signin_subtitle')}
              </p>
            </div>

            {/* Error Notice */}
            {error && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2.5 animate-in fade-in duration-200">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                <span className="font-medium">{error}</span>
              </div>
            )}

            {/* Login Form */}
            <form className="space-y-4" onSubmit={handleSubmit}>
              
              {/* Email Field */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700">
                  {t('auth.email_label')}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t('auth.email_placeholder')}
                    className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50/70 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 focus:bg-white transition shadow-xs"
                  />
                </div>
              </div>

              {/* Password Field */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700">
                  {t('auth.password_label')}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={t('auth.password_placeholder')}
                    className="w-full pl-10 pr-10 py-2.5 bg-slate-50/70 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 focus:bg-white transition shadow-xs"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 transition cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Submit Action with Hover Lift & Loading Spinner */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs sm:text-sm shadow-md shadow-blue-600/25 hover:shadow-lg hover:shadow-blue-600/30 hover:scale-[1.01] active:scale-[0.99] transition-all duration-150 disabled:opacity-60 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>{t('auth.btn_authenticating')}</span>
                  </>
                ) : (
                  <>
                    <span>{t('auth.btn_signin')}</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* Collapsible Secondary Demo Accounts Helper */}
            <div className="pt-2">
              <button
                type="button"
                onClick={() => setShowDemoHelper(!showDemoHelper)}
                className="w-full flex items-center justify-between text-xs text-slate-500 hover:text-slate-800 py-2 px-1 border-t border-slate-200/80 transition group cursor-pointer"
              >
                <span className="flex items-center gap-2 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                  <span>{t('auth.demo_helper_title')}</span>
                </span>
                {showDemoHelper ? (
                  <ChevronUp className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600" />
                )}
              </button>

              {showDemoHelper && (
                <div className="mt-2.5 space-y-2 p-3 bg-slate-50/90 rounded-2xl border border-slate-200 animate-in fade-in duration-200 text-xs">
                  <p className="text-[11px] text-slate-500 font-medium">
                    {t('auth.demo_helper_subtitle')}
                  </p>

                  {/* Senior Inspector */}
                  <button
                    type="button"
                    onClick={() => fillDemoCredentials('inspector@visionx.gov.in', 'inspector123')}
                    className="w-full p-2.5 rounded-xl border border-slate-200 hover:border-blue-300 bg-white hover:bg-blue-50/40 hover:shadow-xs text-left transition-all duration-150 flex items-center justify-between group cursor-pointer"
                  >
                    <div>
                      <div className="font-bold text-slate-900 text-xs group-hover:text-blue-700 transition">
                        {t('auth.role_inspector')}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">inspector@visionx.gov.in</div>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                      inspector123
                    </span>
                  </button>

                  {/* Director / Admin */}
                  <button
                    type="button"
                    onClick={() => fillDemoCredentials('admin@visionx.gov.in', 'admin123')}
                    className="w-full p-2.5 rounded-xl border border-slate-200 hover:border-blue-300 bg-white hover:bg-blue-50/40 hover:shadow-xs text-left transition-all duration-150 flex items-center justify-between group cursor-pointer"
                  >
                    <div>
                      <div className="font-bold text-slate-900 text-xs group-hover:text-blue-700 transition">
                        {t('auth.role_admin')}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">admin@visionx.gov.in</div>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                      admin123
                    </span>
                  </button>

                  {/* Observer / Viewer */}
                  <button
                    type="button"
                    onClick={() => fillDemoCredentials('viewer@visionx.gov.in', 'viewer123')}
                    className="w-full p-2.5 rounded-xl border border-slate-200 hover:border-blue-300 bg-white hover:bg-blue-50/40 hover:shadow-xs text-left transition-all duration-150 flex items-center justify-between group cursor-pointer"
                  >
                    <div>
                      <div className="font-bold text-slate-900 text-xs group-hover:text-blue-700 transition">
                        {t('auth.role_viewer')}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">viewer@visionx.gov.in</div>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                      viewer123
                    </span>
                  </button>
                </div>
              )}
            </div>

            {/* Legal Security Disclaimer */}
            <p className="text-center text-[10px] text-slate-400 leading-relaxed border-t border-slate-100 pt-4 font-medium">
              {t('auth.legal_notice')}
            </p>

          </div>

        </div>

      </div>

    </div>
  );
};

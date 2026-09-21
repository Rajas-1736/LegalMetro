import React from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, QrCode, Sparkles, Check } from 'lucide-react';

export const PackagingScannerGraphic: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className="relative w-full max-w-lg mx-auto select-none">
      
      {/* Decorative ambient glow behind the package */}
      <div className="absolute -inset-2 bg-gradient-to-tr from-blue-500/10 via-indigo-500/5 to-emerald-500/10 rounded-3xl blur-2xl -z-10" />

      {/* Main Package / Label Container */}
      <div className="relative bg-white rounded-2xl border border-slate-200/90 shadow-[0_12px_36px_rgba(15,23,42,0.06)] overflow-hidden transition-all duration-300">
        
        {/* Top Package Seal Bar */}
        <div className="h-2.5 bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-600 w-full" />

        <div className="p-5 sm:p-6 space-y-4">
          
          {/* Label Header with Commodity & Brand */}
          <div className="flex items-start justify-between border-b border-slate-100 pb-3.5">
            <div className="space-y-0.5">
              <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-semibold">
                Principal Display Panel (PDP)
              </span>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                {t('graphic.product_name')}
              </h3>
              <p className="text-[11px] text-slate-500">Premium Grade • Ready-to-Eat Snack</p>
            </div>

            {/* Official Inspection Tag */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-blue-50 border border-blue-200/80 text-blue-700 text-[10px] font-mono font-semibold">
              <Sparkles className="w-3 h-3 text-blue-600" />
              <span>AI Vision Scan</span>
            </div>
          </div>

          {/* Mandatory Declarations Grid */}
          <div className="grid grid-cols-12 gap-3 text-xs">
            
            {/* Net Quantity with Detected Bounding Box */}
            <div className="col-span-6 relative p-2.5 rounded-lg bg-slate-50/90 border border-slate-200/80">
              {/* Target detection brackets */}
              <div className="absolute top-1 left-1 w-2 h-2 border-t-2 border-l-2 border-blue-600" />
              <div className="absolute top-1 right-1 w-2 h-2 border-t-2 border-r-2 border-blue-600" />
              <div className="absolute bottom-1 left-1 w-2 h-2 border-b-2 border-l-2 border-blue-600" />
              <div className="absolute bottom-1 right-1 w-2 h-2 border-b-2 border-r-2 border-blue-600" />

              <div className="text-[10px] text-slate-500 font-medium flex items-center justify-between">
                <span>{t('graphic.rule_13_unit')}</span>
                <span className="text-[9px] text-emerald-600 font-mono font-bold flex items-center gap-0.5">
                  <Check className="w-2.5 h-2.5" /> SI Unit OK
                </span>
              </div>
              <div className="text-sm font-extrabold text-slate-900 font-mono mt-0.5">
                {t('graphic.net_qty')}
              </div>
            </div>

            {/* Maximum Retail Price (MRP) with Detected Bounding Box */}
            <div className="col-span-6 relative p-2.5 rounded-lg bg-slate-50/90 border border-slate-200/80">
              {/* Target detection brackets */}
              <div className="absolute top-1 left-1 w-2 h-2 border-t-2 border-blue-600" />
              <div className="absolute top-1 right-1 w-2 h-2 border-t-2 border-r-2 border-blue-600" />
              <div className="absolute bottom-1 left-1 w-2 h-2 border-b-2 border-l-2 border-blue-600" />
              <div className="absolute bottom-1 right-1 w-2 h-2 border-b-2 border-r-2 border-blue-600" />

              <div className="text-[10px] text-slate-500 font-medium flex items-center justify-between">
                <span>{t('graphic.rule_6_1_e_usp')}</span>
                <span className="text-[9px] text-emerald-600 font-mono font-bold flex items-center gap-0.5">
                  <Check className="w-2.5 h-2.5" /> USP Valid
                </span>
              </div>
              <div className="text-sm font-extrabold text-slate-900 font-mono mt-0.5">
                {t('graphic.mrp')}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">
                (USP: ₹ 0.85 / g)
              </div>
            </div>

            {/* Manufacturer Details */}
            <div className="col-span-12 p-2.5 rounded-lg bg-slate-50/90 border border-slate-200/80 space-y-1">
              <div className="text-[10px] text-slate-500 font-medium flex items-center justify-between">
                <span>{t('graphic.rule_6_1_a_mfg')}</span>
                <span className="text-[9px] text-emerald-600 font-mono font-bold flex items-center gap-0.5">
                  <Check className="w-2.5 h-2.5" /> Complete Address
                </span>
              </div>
              <p className="text-[11px] text-slate-800 font-medium leading-tight">
                Mfd & Packed by: Apex Nutrition Ltd, Plot 42, GIDC Industrial Estate, Pune, MH - 411019
              </p>
            </div>

            {/* Barcode & Consumer Care Row */}
            <div className="col-span-8 flex items-center space-x-3 p-2 rounded-lg bg-slate-50/60 border border-slate-200/60">
              {/* Simulated barcode */}
              <div className="flex items-center space-x-[2px] h-8 px-1 bg-white rounded border border-slate-200">
                <div className="w-[2px] h-6 bg-slate-900" />
                <div className="w-[1px] h-6 bg-slate-900" />
                <div className="w-[3px] h-6 bg-slate-900" />
                <div className="w-[1px] h-6 bg-slate-900" />
                <div className="w-[2px] h-6 bg-slate-900" />
                <div className="w-[4px] h-6 bg-slate-900" />
                <div className="w-[1px] h-6 bg-slate-900" />
                <div className="w-[2px] h-6 bg-slate-900" />
                <div className="w-[3px] h-6 bg-slate-900" />
                <div className="w-[1px] h-6 bg-slate-900" />
              </div>
              <div className="text-[10px] space-y-0.5 font-mono">
                <div className="text-slate-700 font-semibold">8901234567890</div>
                <div className="text-slate-400">Batch: B409 • Exp: 08/2027</div>
              </div>
            </div>

            <div className="col-span-4 flex items-center justify-center p-2 rounded-lg bg-slate-50/60 border border-slate-200/60 text-center">
              <div className="flex flex-col items-center">
                <QrCode className="w-5 h-5 text-blue-600 mb-0.5" />
                <span className="text-[9px] text-slate-500 font-mono font-medium">QR Portal OK</span>
              </div>
            </div>

          </div>

        </div>

        {/* Dynamic Sweeping Optical Scan Line */}
        <div className="absolute inset-x-0 pointer-events-none animate-scan-beam z-20">
          {/* Laser glowing bar */}
          <div className="h-[2px] bg-blue-600 shadow-[0_0_12px_#2563eb,0_0_4px_#3b82f6]" />
          {/* Trailing beam illumination */}
          <div className="h-10 bg-gradient-to-b from-blue-500/15 via-blue-500/5 to-transparent pointer-events-none" />
          {/* Leading reticle dots */}
          <div className="absolute -top-1 left-2 w-2 h-2 rounded-full bg-blue-600 shadow-[0_0_6px_#2563eb]" />
          <div className="absolute -top-1 right-2 w-2 h-2 rounded-full bg-blue-600 shadow-[0_0_6px_#2563eb]" />
        </div>

      </div>

      {/* Floating Metrology Seal Tag (Modern Layered Depth) */}
      <div className="absolute -bottom-4 -right-2 sm:-right-4 bg-white/95 backdrop-blur-sm border border-slate-200 rounded-xl px-3.5 py-2 shadow-lg shadow-slate-900/5 flex items-center space-x-2.5 z-30 animate-float-slow">
        <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm shadow-emerald-600/30">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div>
          <div className="text-[11px] font-bold text-slate-900 leading-tight">
            {t('graphic.pcr_verified')}
          </div>
          <div className="text-[9px] font-mono text-emerald-600 font-semibold">
            {t('graphic.statutory_conformity')}
          </div>
        </div>
      </div>

    </div>
  );
};

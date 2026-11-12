import React from 'react';
import { ShieldCheck, Lock, Globe } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const Footer = () => {
  const { t } = useLanguage();

  return (
    <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 py-8 px-4 sm:px-6 lg:px-8 mt-16 text-xs">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-sky-400" aria-hidden="true" />
          <span className="font-semibold text-slate-200">TrustShield AI</span>
          <span className="text-slate-600">|</span>
          <span>{t.footer.version}</span>
        </div>

        <p className="text-center sm:text-left max-w-xl text-slate-400">
          {t.footer.disclaimer}
        </p>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700">
            <Lock className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />
            <span>{t.footer.privacyNote}</span>
          </div>
        </div>

      </div>
    </footer>
  );
};

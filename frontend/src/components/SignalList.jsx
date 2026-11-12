import React from 'react';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const SignalList = ({ signals = [] }) => {
  const { lang, t } = useLanguage();

  if (!signals || signals.length === 0) {
    return (
      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-sm text-slate-600">
        {t.results.noSignals}
      </div>
    );
  }

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" aria-hidden="true" />
            <span>{t.results.severityLevels.CRITICAL}</span>
          </span>
        );
      case 'WARNING':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" aria-hidden="true" />
            <span>{t.results.severityLevels.WARNING}</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
            <Info className="w-3.5 h-3.5 text-slate-500 shrink-0" aria-hidden="true" />
            <span>{t.results.severityLevels.INFO}</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-3">
      {signals.map((sig, idx) => {
        const label = lang === 'hi' && sig.label_hi ? sig.label_hi : sig.label;
        const description = lang === 'hi' && sig.description_hi ? sig.description_hi : sig.description;

        return (
          <div
            key={sig.id || idx}
            className="p-3.5 rounded-lg border border-slate-200 bg-white hover:border-slate-300 transition-colors"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
              <h4 className="font-semibold text-sm text-slate-900">{label}</h4>
              {getSeverityBadge(sig.severity)}
            </div>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {description}
            </p>
          </div>
        );
      })}
    </div>
  );
};

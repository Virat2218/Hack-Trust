import React from 'react';
import { Server, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const EvidenceCard = ({ providers = [] }) => {
  const { lang, t } = useLanguage();

  return (
    <div className="bg-slate-50 rounded-lg border border-slate-200 p-4">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center space-x-1.5">
        <Server className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
        <span>{t.results.evidenceHeader}</span>
      </h4>

      <div className="space-y-2.5">
        {providers.map((p, idx) => {
          const isConfigured = p.configured;
          const isActive = p.status === 'ACTIVE';

          return (
            <div
              key={idx}
              className="flex flex-col sm:flex-row sm:items-center justify-between text-xs p-2.5 rounded bg-white border border-slate-200 gap-1.5"
            >
              <div className="flex items-center space-x-2">
                {isActive ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" aria-hidden="true" />
                ) : isConfigured ? (
                  <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" aria-hidden="true" />
                ) : (
                  <HelpCircle className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
                )}
                <span className="font-medium text-slate-800">{p.name}</span>
              </div>

              <div className="text-right sm:text-right text-slate-500">
                {isActive ? (
                  <span className="text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    {lang === 'hi' ? 'सक्रिय (स्थानीय नियम)' : 'Active (Local Heuristics)'}
                  </span>
                ) : (
                  <span className="text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                    {lang === 'hi' ? 'कॉन्फ़िगर नहीं किया गया (वैकल्पिक)' : 'Not Configured (Optional Key Missing)'}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};


import React from 'react';
import { Loader2 } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const LoadingState = () => {
  const { t } = useLanguage();

  return (
    <div
      className="bg-white rounded-xl border border-slate-200 p-8 text-center shadow-xs"
      role="status"
      aria-live="polite"
    >
      <Loader2 className="w-8 h-8 text-sky-600 animate-spin mx-auto mb-3" aria-hidden="true" />
      <h3 className="text-base font-semibold text-slate-800 mb-1">
        {t.states.loadingTitle}
      </h3>
      <p className="text-sm text-slate-500 max-w-sm mx-auto">
        {t.states.loadingSubtitle}
      </p>
      <div className="mt-4 max-w-xs mx-auto h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className="h-full bg-sky-600 rounded-full animate-pulse w-3/4"></div>
      </div>
    </div>
  );
};


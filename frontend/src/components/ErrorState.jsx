import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const ErrorState = ({ message, onRetry }) => {
  const { t } = useLanguage();

  return (
    <div
      className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center text-rose-900 shadow-xs"
      role="alert"
    >
      <div className="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 mx-auto mb-2">
        <AlertCircle className="w-6 h-6" aria-hidden="true" />
      </div>
      <h3 className="text-base font-semibold text-rose-900 mb-1">
        {t.states.errorTitle}
      </h3>
      <p className="text-sm text-rose-700 max-w-md mx-auto mb-4">
        {message || t.states.errorRetry}
      </p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center space-x-1.5 px-4 py-2 bg-rose-700 text-white rounded-lg text-sm font-medium hover:bg-rose-800 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 shadow-xs"
        >
          <RotateCcw className="w-4 h-4" aria-hidden="true" />
          <span>{t.states.retryButton}</span>
        </button>
      )}
    </div>
  );
};

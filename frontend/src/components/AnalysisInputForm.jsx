import React from 'react';
import { ShieldCheck, RotateCcw, ArrowRight, Loader2, AlertCircle, Cloud } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const AnalysisInputForm = ({
  activeTab,
  value,
  onChange,
  onSubmit,
  onReset,
  loading,
  validationError,
  allowExternal,
  onToggleExternal,
}) => {
  const { lang, t } = useLanguage();

  const getLimits = () => {
    switch (activeTab) {
      case 'url':
        return { max: 1000, label: t.inputs.urlLabel, placeholder: t.inputs.urlPlaceholder };
      case 'claim':
        return { max: 1000, label: t.inputs.claimLabel, placeholder: t.inputs.claimPlaceholder };
      default:
        return { max: 4000, label: t.inputs.messageLabel, placeholder: t.inputs.messagePlaceholder };
    }
  };

  const { max, label, placeholder } = getLimits();
  const currentLen = (value || '').length;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!loading) {
      onSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
      
      {/* Header with Title and Reset */}
      <div className="flex items-center justify-between mb-3">
        <label htmlFor="analysis-input-field" className="text-sm font-semibold text-slate-800">
          {label}
        </label>

        {value && (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800 focus:outline-none focus-visible:ring-1 focus-visible:ring-sky-500"
          >
            <RotateCcw className="w-3 h-3" aria-hidden="true" />
            <span>{t.nav.newAnalysis}</span>
          </button>
        )}
      </div>

      {/* Input Area */}
      {activeTab === 'url' ? (
        <input
          id="analysis-input-field"
          type="url"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={loading}
          className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-sm font-mono text-slate-900 bg-white placeholder-slate-400 disabled:bg-slate-50"
        />
      ) : (
        <textarea
          id="analysis-input-field"
          rows={5}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={loading}
          className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-sm text-slate-900 bg-white placeholder-slate-400 disabled:bg-slate-50 leading-relaxed"
        />
      )}

      {/* Inline Validation Error */}
      {validationError && (
        <div className="mt-2.5 flex items-center space-x-1.5 text-xs text-rose-600" role="alert">
          <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
          <span>{validationError}</span>
        </div>
      )}

      {/* Privacy Opt-in for URL and Claim Analysis */}
      {(activeTab === 'url' || activeTab === 'claim') && (
        <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
          <label className="flex items-start space-x-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={allowExternal}
              onChange={(e) => onToggleExternal(e.target.checked)}
              disabled={loading}
              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500 cursor-pointer disabled:cursor-not-allowed"
            />
            <div className="text-xs text-slate-700">
              <span className="font-semibold flex items-center gap-1 text-slate-800">
                <Cloud className="w-3.5 h-3.5 text-sky-600 inline" aria-hidden="true" />
                {t.inputs.externalOptInLabel}
              </span>
              <p className="text-slate-500 mt-0.5 leading-relaxed">
                {t.inputs.externalOptInDesc}
              </p>
            </div>
          </label>
        </div>
      )}

      {/* Controls: Privacy Reassurance, Char Count, Submit Button */}
      <div className="mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100">
        
        <div className="flex items-center space-x-1.5 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" aria-hidden="true" />
          <span>{t.inputs.privacyNotice}</span>
        </div>

        <div className="flex items-center justify-between sm:justify-end space-x-4">
          <span className={`text-xs font-mono ${currentLen > max ? 'text-rose-600 font-bold' : 'text-slate-400'}`}>
            {currentLen} / {max} {t.inputs.chars}
          </span>

          <button
            type="submit"
            disabled={loading || currentLen === 0}
            className={`inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 ${
              loading || currentLen === 0
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                : 'bg-sky-600 hover:bg-sky-700 text-white shadow-xs'
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                <span>{t.inputs.analyzingButton}</span>
              </>
            ) : (
              <>
                <span>{t.inputs.analyzeButton}</span>
                <ArrowRight className="w-4 h-4" aria-hidden="true" />
              </>
            )}
          </button>
        </div>

      </div>

    </form>
  );
};

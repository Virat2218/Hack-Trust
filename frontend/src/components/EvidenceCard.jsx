import React from 'react';
import { Server, CheckCircle2, AlertCircle, HelpCircle, ExternalLink, ShieldOff } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const EvidenceCard = ({ evidence = [], providers = [] }) => {
  const { lang, t } = useLanguage();

  // Combine or prioritize structured evidence over simple provider status
  const items = (evidence && evidence.length > 0) ? evidence : providers;

  if (!items || items.length === 0) {
    return null;
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <span className="text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            {t.results.evidenceStatus.ACTIVE}
          </span>
        );
      case 'CONSENT_WITHHELD':
        return (
          <span className="text-slate-600 font-medium bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            {t.results.evidenceStatus.CONSENT_WITHHELD}
          </span>
        );
      case 'VERIFIED_MATCH':
        return (
          <span className="text-rose-800 font-bold bg-rose-50 px-2 py-0.5 rounded border border-rose-300">
            {t.results.evidenceStatus.VERIFIED_MATCH}
          </span>
        );
      case 'POSSIBLE_MATCH':
        return (
          <span className="text-amber-800 font-semibold bg-amber-50 px-2 py-0.5 rounded border border-amber-300">
            {t.results.evidenceStatus.POSSIBLE_MATCH}
          </span>
        );
      case 'NO_MATCH':
        return (
          <span className="text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            {t.results.evidenceStatus.NO_MATCH}
          </span>
        );
      case 'TIMEOUT':
        return (
          <span className="text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
            {t.results.evidenceStatus.TIMEOUT}
          </span>
        );
      case 'ERROR':
        return (
          <span className="text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
            {t.results.evidenceStatus.ERROR}
          </span>
        );
      default:
        return (
          <span className="text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            {t.results.evidenceStatus.NOT_CONFIGURED}
          </span>
        );
    }
  };

  const getStatusIcon = (status) => {
    if (status === 'ACTIVE' || status === 'VERIFIED_MATCH') {
      return <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" aria-hidden="true" />;
    }
    if (status === 'CONSENT_WITHHELD') {
      return <ShieldOff className="w-4 h-4 text-slate-500 shrink-0" aria-hidden="true" />;
    }
    if (status === 'POSSIBLE_MATCH' || status === 'TIMEOUT' || status === 'ERROR') {
      return <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" aria-hidden="true" />;
    }
    return <HelpCircle className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />;
  };

  return (
    <div className="bg-slate-50 rounded-lg border border-slate-200 p-4">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center space-x-1.5">
        <Server className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
        <span>{t.results.evidenceHeader}</span>
      </h4>

      <div className="space-y-2.5">
        {items.map((item, idx) => {
          const sourceName = item.source_name || item.name;
          const status = item.status;
          const details = (lang === 'hi' && item.details_hi) ? item.details_hi : (item.details || '');
          const publisher = item.publisher;
          const reviewUrl = item.review_url;
          const rating = item.textual_rating;

          return (
            <div
              key={idx}
              className="flex flex-col text-xs p-3 rounded bg-white border border-slate-200 gap-1.5"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(status)}
                  <span className="font-semibold text-slate-800">{sourceName}</span>
                </div>
                <div>{getStatusBadge(status)}</div>
              </div>

              {details && (
                <p className="text-slate-600 text-xs mt-1 leading-relaxed pl-6">
                  {details}
                </p>
              )}

              {/* Verified Fact-Check Citation Details if present */}
              {publisher && (
                <div className="mt-1 pl-6 pt-1.5 border-t border-slate-100 space-y-1 text-slate-700">
                  {item.reviewed_claim && (
                    <div className="text-slate-600 italic">
                      <span className="font-medium text-slate-700 not-italic">Reviewed Claim:</span> "{item.reviewed_claim}"
                    </div>
                  )}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium text-slate-900">{publisher}</span>
                      {rating && (
                        <span className="px-1.5 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 text-xs font-semibold">
                          Rating: {rating}
                        </span>
                      )}
                      {item.review_date && (
                        <span className="text-slate-400 text-xs">({item.review_date.slice(0, 10)})</span>
                      )}
                    </div>

                    {reviewUrl && (
                      <a
                        href={reviewUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center space-x-1 text-sky-600 hover:text-sky-800 font-medium"
                      >
                        <span>Read Original Investigation</span>
                        <ExternalLink className="w-3 h-3 ml-0.5" aria-hidden="true" />
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

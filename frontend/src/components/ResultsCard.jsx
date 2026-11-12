import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, Copy, Check, RotateCcw } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { SignalList } from './SignalList';
import { EvidenceCard } from './EvidenceCard';
import { UncertaintyNotice } from './UncertaintyNotice';
import { ActionGuide } from './ActionGuide';

export const ResultsCard = ({ result, onReset }) => {
  const { lang, t } = useLanguage();
  const [copied, setCopied] = useState(false);

  if (!result) return null;

  const {
    risk_level = 'LOW',
    critical_signals_count = 0,
    warning_signals_count = 0,
    info_signals_count = 0,
    summary,
    summary_hi,
    signals = [],
    evidence = [],
    provider_statuses = [],
    uncertainty_notes = [],
    uncertainty_notes_hi = [],
    recommended_actions = [],
    recommended_actions_hi = [],
    timestamp
  } = result;

  const displaySummary = (lang === 'hi' && summary_hi) ? summary_hi : summary;

  // Visual risk styling
  const getRiskDetails = () => {
    switch (risk_level) {
      case 'HIGH':
        return {
          badgeBg: 'bg-rose-100 text-rose-800 border-rose-300',
          badgeText: t.results.riskLevels.HIGH.badge,
          label: t.results.riskLevels.HIGH.label,
          icon: ShieldAlert,
          iconColor: 'text-rose-600',
          cardBorder: 'border-rose-200',
          bannerBg: 'bg-rose-50/70',
        };
      case 'MEDIUM':
        return {
          badgeBg: 'bg-amber-100 text-amber-800 border-amber-300',
          badgeText: t.results.riskLevels.MEDIUM.badge,
          label: t.results.riskLevels.MEDIUM.label,
          icon: AlertTriangle,
          iconColor: 'text-amber-600',
          cardBorder: 'border-amber-200',
          bannerBg: 'bg-amber-50/70',
        };
      default:
        return {
          badgeBg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          badgeText: t.results.riskLevels.LOW.badge,
          label: t.results.riskLevels.LOW.label,
          icon: ShieldCheck,
          iconColor: 'text-emerald-600',
          cardBorder: 'border-emerald-200',
          bannerBg: 'bg-emerald-50/70',
        };
    }
  };

  const riskDetails = getRiskDetails();
  const RiskIcon = riskDetails.icon;

  const handleCopySummary = () => {
    const textToCopy = `[TrustShield AI Assessment]\nRisk Assessment: ${riskDetails.label}\nSignals Detected: ${critical_signals_count} Critical, ${warning_signals_count} Warning\n\nSummary:\n${displaySummary}\n\nKey Signals:\n${signals.map(s => `- ${s.label}: ${s.description}`).join('\n')}\n\nRecommended Actions:\n${recommended_actions.map(a => `- ${a}`).join('\n')}\n\nNotice: Decision-support tool only. Verify critical matters through official channels.`;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  return (
    <div className={`bg-white rounded-xl border ${riskDetails.cardBorder} p-6 shadow-sm space-y-6`}>
      
      {/* Risk Level Header Banner */}
      <div className={`p-5 rounded-lg border ${riskDetails.cardBorder} ${riskDetails.bannerBg}`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-lg bg-white border ${riskDetails.cardBorder} flex items-center justify-center shrink-0`}>
              <RiskIcon className={`w-6 h-6 ${riskDetails.iconColor}`} aria-hidden="true" />
            </div>
            <div>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${riskDetails.badgeBg}`}>
                {riskDetails.badgeText}
              </span>
              <h3 className="text-base sm:text-lg font-bold text-slate-900 mt-0.5">
                {riskDetails.label}
              </h3>
            </div>
          </div>

          <div className="text-left sm:text-right">
            <span className="text-xs uppercase tracking-wider text-slate-500 font-medium">
              {t.results.signalsCountLabel}
            </span>
            <div className="text-sm font-semibold text-slate-800 mt-0.5">
              {signals.length === 0 ? (
                <span className="text-slate-500 font-normal">{lang === 'hi' ? '0 संकेत मिले' : '0 Indicators'}</span>
              ) : (
                <div className="flex items-center gap-1.5 justify-start sm:justify-end">
                  {critical_signals_count > 0 && (
                    <span className="px-1.5 py-0.5 rounded text-xs bg-rose-100 text-rose-800 font-bold border border-rose-200">
                      {critical_signals_count} {lang === 'hi' ? 'गंभीर' : 'Critical'}
                    </span>
                  )}
                  {warning_signals_count > 0 && (
                    <span className="px-1.5 py-0.5 rounded text-xs bg-amber-100 text-amber-900 font-medium border border-amber-200">
                      {warning_signals_count} {lang === 'hi' ? 'चेतावनी' : 'Warning'}
                    </span>
                  )}
                  {info_signals_count > 0 && (
                    <span className="px-1.5 py-0.5 rounded text-xs bg-slate-100 text-slate-700 border border-slate-200 font-normal">
                      {info_signals_count} {lang === 'hi' ? 'सूचना' : 'Info'}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        <p className="text-sm text-slate-700 leading-relaxed pt-1 border-t border-slate-200/60">
          {displaySummary}
        </p>
      </div>

      {/* Contributing Signals */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
          {t.results.signalsHeader} ({signals.length})
        </h4>
        <SignalList signals={signals} />
      </div>

      {/* Action Guide & Recommended Next Steps */}
      <ActionGuide actions={recommended_actions} actions_hi={recommended_actions_hi} />

      {/* Evidence & Provider Status */}
      <EvidenceCard evidence={evidence} providers={provider_statuses} />

      {/* Uncertainty & Limitations */}
      <UncertaintyNotice notes={uncertainty_notes} notes_hi={uncertainty_notes_hi} />

      {/* Actions & Reset */}
      <div className="pt-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="text-xs text-slate-500 italic text-center sm:text-left">
          {t.results.disclaimerNote}
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <button
            type="button"
            onClick={handleCopySummary}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center space-x-1.5 px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
                <span className="text-emerald-700">{t.results.copiedSummary}</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
                <span>{t.results.copySummary}</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onReset}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center space-x-1.5 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-medium hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 shadow-xs"
          >
            <RotateCcw className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{t.results.newAnalysis}</span>
          </button>
        </div>
      </div>

    </div>
  );
};

import React from 'react';
import { CheckSquare } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const ActionGuide = ({ actions = [], actions_hi = [] }) => {
  const { lang, t } = useLanguage();
  const activeActions = (lang === 'hi' && actions_hi && actions_hi.length > 0) ? actions_hi : actions;

  if (!activeActions || activeActions.length === 0) return null;

  return (
    <div className="bg-sky-50/60 border border-sky-200/80 rounded-lg p-4">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-sky-950 mb-2 flex items-center space-x-1.5">
        <CheckSquare className="w-3.5 h-3.5 text-sky-700" aria-hidden="true" />
        <span>{t.results.actionsHeader}</span>
      </h4>
      <ol className="list-decimal list-inside space-y-1.5 text-xs text-sky-950 leading-relaxed font-medium">
        {activeActions.map((action, idx) => (
          <li key={idx} className="pl-1">
            <span>{action}</span>
          </li>
        ))}
      </ol>
    </div>
  );
};


import React from 'react';
import { HelpCircle } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const UncertaintyNotice = ({ notes = [], notes_hi = [] }) => {
  const { lang, t } = useLanguage();
  const activeNotes = (lang === 'hi' && notes_hi && notes_hi.length > 0) ? notes_hi : notes;

  if (!activeNotes || activeNotes.length === 0) return null;

  return (
    <div className="bg-amber-50/70 border border-amber-200/80 rounded-lg p-4">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-900 mb-2 flex items-center space-x-1.5">
        <HelpCircle className="w-3.5 h-3.5 text-amber-700" aria-hidden="true" />
        <span>{t.results.uncertaintyHeader}</span>
      </h4>
      <ul className="list-disc list-inside space-y-1.5 text-xs text-amber-900/90 leading-relaxed">
        {activeNotes.map((note, idx) => (
          <li key={idx} className="pl-1">
            <span>{note}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};


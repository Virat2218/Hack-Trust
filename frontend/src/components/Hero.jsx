import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Info } from 'lucide-react';

export const Hero = () => {
  const { t } = useLanguage();

  return (
    <section className="bg-gradient-to-b from-slate-900 to-slate-800 text-white py-8 px-4 sm:px-6 lg:px-8 border-b border-slate-700">
      <div className="max-w-4xl mx-auto text-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-950/80 border border-sky-800/80 text-sky-300 text-xs font-medium mb-3">
          <Info className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{t.hero.tagline}</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
          {t.hero.title}
        </h1>
        <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
          {t.hero.subtitle}
        </p>
      </div>
    </section>
  );
};

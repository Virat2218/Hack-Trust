import React from 'react';
import { ShieldCheck, Globe, Lock } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const Navbar = ({ onOpenPrivacy, privacyButtonRef }) => {
  const { lang, setLang, t } = useLanguage();

  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-30 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand identity */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-sky-600/20 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <ShieldCheck className="w-6 h-6 text-sky-400" aria-hidden="true" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-lg tracking-tight text-white">{t.brand.name}</span>
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
                {t.brand.badge}
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden md:block">
              {t.brand.tagline}
            </p>
          </div>
        </div>

        {/* Controls: Privacy Link & Language Switcher */}
        <div className="flex items-center space-x-3">
          <button
            ref={privacyButtonRef}
            type="button"
            onClick={onOpenPrivacy}
            className="inline-flex items-center text-xs font-medium text-slate-300 hover:text-white px-3 py-1.5 rounded-md hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
            aria-label={t.nav.privacyLink}
          >
            <Lock className="w-3.5 h-3.5 mr-1.5 text-sky-400" aria-hidden="true" />
            <span>{t.nav.privacyLink}</span>
          </button>

          {/* Language Toggle with Accessible aria-pressed states */}
          <div className="flex items-center bg-slate-800 rounded-md p-1 border border-slate-700" role="group" aria-label="Language selection">
            <Globe className="w-3.5 h-3.5 text-slate-400 ml-1.5 mr-1" aria-hidden="true" />
            <button
              type="button"
              onClick={() => setLang('en')}
              className={`px-2 py-0.5 text-xs font-medium rounded transition-colors ${
                lang === 'en'
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              aria-pressed={lang === 'en'}
              aria-label="Switch to English"
            >
              EN
            </button>
            <button
              type="button"
              onClick={() => setLang('hi')}
              className={`px-2 py-0.5 text-xs font-medium rounded transition-colors ${
                lang === 'hi'
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              aria-pressed={lang === 'hi'}
              aria-label="Switch to Hindi (हिंदी)"
            >
              हिंदी
            </button>
          </div>
        </div>

      </div>
    </header>
  );
};

import React, { useEffect, useRef } from 'react';
import { X, ShieldCheck, Database, ExternalLink, AlertTriangle, Languages, Cloud, HardDrive } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const PrivacyModal = ({ isOpen, onClose }) => {
  const { t } = useLanguage();
  const modalRef = useRef(null);
  const closeButtonRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;

    const timer = setTimeout(() => {
      closeButtonRef.current?.focus();
    }, 50);

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }

      if (e.key === 'Tab' && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="privacy-modal-title"
      ref={modalRef}
    >
      <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 relative max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-sky-50 text-sky-700">
              <ShieldCheck className="w-5 h-5" aria-hidden="true" />
            </div>
            <h2 id="privacy-modal-title" className="text-lg font-semibold text-slate-900">
              {t.privacyModal.title}
            </h2>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded-md hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
            aria-label={t.privacyModal.close}
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        <div className="mt-4 space-y-3.5 text-sm text-slate-700">
          {/* Section 1: Zero Storage */}
          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex space-x-3 items-start">
            <Database className="w-5 h-5 text-slate-700 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <h3 className="font-semibold text-slate-900">{t.privacyModal.section1Title}</h3>
              <p className="mt-1 text-slate-600 leading-relaxed text-xs sm:text-sm">{t.privacyModal.section1Body}</p>
            </div>
          </div>

          {/* Section 2: Decision Support */}
          <div className="p-3.5 bg-amber-50/80 rounded-lg border border-amber-200 flex space-x-3 items-start">
            <AlertTriangle className="w-5 h-5 text-amber-800 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <h3 className="font-semibold text-amber-950">{t.privacyModal.section2Title}</h3>
              <p className="mt-1 text-amber-900 leading-relaxed text-xs sm:text-sm">{t.privacyModal.section2Body}</p>
            </div>
          </div>

          {/* Section 3: Safe URL Validation */}
          <div className="p-3.5 bg-sky-50/70 rounded-lg border border-sky-200 flex space-x-3 items-start">
            <ExternalLink className="w-5 h-5 text-sky-700 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <h3 className="font-semibold text-sky-950">{t.privacyModal.section3Title}</h3>
              <p className="mt-1 text-sky-900 leading-relaxed text-xs sm:text-sm">{t.privacyModal.section3Body}</p>
            </div>
          </div>

          {/* Section 4: Translation Transparency */}
          <div className="p-3.5 bg-slate-100/80 rounded-lg border border-slate-200 flex space-x-3 items-start">
            <Languages className="w-5 h-5 text-slate-700 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <h3 className="font-semibold text-slate-900">{t.privacyModal.section4Title}</h3>
              <p className="mt-1 text-slate-600 leading-relaxed text-xs sm:text-sm">{t.privacyModal.section4Body}</p>
            </div>
          </div>

          {/* Section 5: Local vs. External Provider Data Flow */}
          <div className="p-3.5 bg-indigo-50/70 rounded-lg border border-indigo-200 flex space-x-3 items-start">
            <Cloud className="w-5 h-5 text-indigo-700 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <h3 className="font-semibold text-indigo-950">{t.privacyModal.section5Title}</h3>
              <p className="mt-1 text-indigo-900 leading-relaxed text-xs sm:text-sm">{t.privacyModal.section5Body}</p>
            </div>
          </div>

          {/* Section 6: Browser-Stored Data */}
          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex space-x-3 items-start">
            <HardDrive className="w-5 h-5 text-slate-700 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <h3 className="font-semibold text-slate-900">{t.privacyModal.section6Title}</h3>
              <p className="mt-1 text-slate-600 leading-relaxed text-xs sm:text-sm">{t.privacyModal.section6Body}</p>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 shadow-xs"
          >
            {t.privacyModal.acknowledge}
          </button>
        </div>
      </div>
    </div>
  );
};

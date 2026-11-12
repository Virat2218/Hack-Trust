import React from 'react';
import { ShieldAlert, FileText, Link, HelpCircle } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const EmptyState = ({ activeTab, onSelectExample }) => {
  const { t, lang } = useLanguage();

  const examples = {
    message: [
      {
        label: lang === 'hi' ? 'उदाहरण: बिजली बिल निलंबन' : 'Example: Urgent Electricity Bill Disconnection',
        text: 'URGENT: Your electricity power will be disconnected tonight at 9:30 PM because your previous month bill was not updated. Immediately contact our electricity officer at 9876543210 to update KYC now.'
      },
      {
        label: lang === 'hi' ? 'उदाहरण: बैंक खाता ब्लॉक सूचना' : 'Example: Bank Account KYC Suspension',
        text: 'Dear Customer, your SBI account has been suspended due to pending PAN card verification. Click http://sbi-kyc-verify-portal.top to update your details within 24 hours to avoid permanent account block.'
      }
    ],
    url: [
      {
        label: lang === 'hi' ? 'उदाहरण: संदिग्ध शॉर्टनर लिंक' : 'Example: Suspicious Shortened Link',
        text: 'http://bit.ly/claim-free-government-subsidy-2026'
      },
      {
        label: lang === 'hi' ? 'उदाहरण: भ्रामक बैंकिंग डोमेन' : 'Example: Lookalike Domain Name',
        text: 'https://hdfc-bank-rewards-login-update.online/auth'
      }
    ],
    claim: [
      {
        label: lang === 'hi' ? 'उदाहरण: वायरल स्वास्थ्य दावा' : 'Example: Viral Health Remedy Claim',
        text: 'Drinking boiled garlic water every morning is scientifically proven by doctors to cure 100% of viral infections within 48 hours. Forward to everyone you care about!'
      },
      {
        label: lang === 'hi' ? 'उदाहरण: वायरल सरकारी योजना' : 'Example: Free Phone Scheme Forward',
        text: 'Government has launched new scheme giving free smartphones to all students who register their Aadhaar number on this forwarded portal today only.'
      }
    ]
  };

  const currentExamples = examples[activeTab] || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-8 text-center shadow-xs">
      <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 flex items-center justify-center text-slate-500 mb-3">
        <HelpCircle className="w-6 h-6 text-slate-500" aria-hidden="true" />
      </div>
      <h3 className="text-base font-semibold text-slate-800 mb-1">
        {t.states.emptyPromptTitle}
      </h3>
      <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
        {t.states.emptyPromptDesc}
      </p>

      {/* Suggested Examples */}
      {currentExamples.length > 0 && (
        <div className="border-t border-slate-100 pt-5 max-w-lg mx-auto text-left">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 text-center">
            {lang === 'hi' ? 'परीक्षण के लिए उदाहरण चुनें (Clickable Examples):' : 'Try an example to see how signals are explained:'}
          </p>
          <div className="space-y-2">
            {currentExamples.map((item, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectExample(item.text)}
                className="w-full text-left p-2.5 rounded-lg border border-slate-200 hover:border-sky-400 hover:bg-sky-50/50 text-xs text-slate-700 transition flex items-start space-x-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
              >
                <span className="font-semibold text-sky-700 shrink-0">▸</span>
                <span className="line-clamp-2">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};


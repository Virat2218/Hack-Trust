import React, { useState, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { PrivacyModal } from './components/PrivacyModal';
import { EmptyState } from './components/EmptyState';
import { LoadingState } from './components/LoadingState';
import { ErrorState } from './components/ErrorState';
import { Footer } from './components/Footer';
import { AnalysisInputForm } from './components/AnalysisInputForm';
import { ResultsCard } from './components/ResultsCard';
import { useLanguage } from './context/LanguageContext';
import { validateMessageInput, validateUrlInput, validateClaimInput } from './utils/validation';
import { MessageSquare, Link, Newspaper } from 'lucide-react';

export const AppContent = () => {
  const { t, lang } = useLanguage();
  const [activeTab, setActiveTab] = useState('message'); // 'message' | 'url' | 'claim'
  const [isPrivacyOpen, setIsPrivacyOpen] = useState(false);
  const privacyTriggerRef = useRef(null);

  // Form states
  const [inputValue, setInputValue] = useState('');
  const [validationError, setValidationError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState(null);
  const [result, setResult] = useState(null);

  // Tab definitions
  const tabs = [
    { id: 'message', label: t.nav.messageTab, icon: MessageSquare },
    { id: 'url', label: t.nav.urlTab, icon: Link },
    { id: 'claim', label: t.nav.claimTab, icon: Newspaper },
  ];

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setInputValue('');
    setValidationError(null);
    setServerError(null);
    setResult(null);
  };

  const handleReset = () => {
    setInputValue('');
    setValidationError(null);
    setServerError(null);
    setResult(null);
  };

  const handleSelectExample = (text) => {
    setInputValue(text);
    setValidationError(null);
    setServerError(null);
  };

  // Keyboard navigation for accessible tabs (ArrowLeft / ArrowRight)
  const handleTabKeyDown = (e, currentIndex) => {
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % tabs.length;
      handleTabChange(tabs[nextIndex].id);
      document.getElementById(`tab-${tabs[nextIndex].id}`)?.focus();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + tabs.length) % tabs.length;
      handleTabChange(tabs[prevIndex].id);
      document.getElementById(`tab-${tabs[prevIndex].id}`)?.focus();
    }
  };

  const handleAnalyze = async () => {
    setValidationError(null);
    setServerError(null);

    // 1. Client-side input validation
    let isValid = false;
    let sanitized = inputValue;

    if (activeTab === 'message') {
      const v = validateMessageInput(inputValue, t);
      if (!v.valid) {
        setValidationError(v.error);
        return;
      }
      isValid = true;
    } else if (activeTab === 'url') {
      const v = validateUrlInput(inputValue, t);
      if (!v.valid) {
        setValidationError(v.error);
        return;
      }
      isValid = true;
      sanitized = v.sanitizedUrl || inputValue;
    } else if (activeTab === 'claim') {
      const v = validateClaimInput(inputValue, t);
      if (!v.valid) {
        setValidationError(v.error);
        return;
      }
      isValid = true;
    }

    if (!isValid) return;

    // 2. Execute analysis request
    setLoading(true);
    try {
      const endpoint = `/api/analyze/${activeTab}`;
      const payload = activeTab === 'url' ? { url: sanitized, language: lang } : { text: sanitized, language: lang };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Analysis service responded with status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setServerError(
        lang === 'hi'
          ? `बैकएंड विश्लेषण सेवा से संपर्क नहीं हो सका (${err.message})। कृपया सुनिश्चित करें कि बैकएंड पोर्ट 8000 पर चल रहा है।`
          : `Unable to connect to analysis backend (${err.message}). Ensure the backend is active on port 8000.`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Skip to Main Content Link for Keyboard and Screen Reader Accessibility */}
      <a href="#main-content" className="skip-link">
        {lang === 'hi' ? 'मुख्य सामग्री पर जाएं' : 'Skip to main content'}
      </a>

      <Navbar
        onOpenPrivacy={() => setIsPrivacyOpen(true)}
        privacyButtonRef={privacyTriggerRef}
      />
      <Hero />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8" id="main-content">
        
        {/* Navigation Tabs with Keyboard Arrow Navigation */}
        <div className="flex border-b border-slate-200 mb-6" role="tablist" aria-label="Analysis Types">
          {tabs.map((tab, idx) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                role="tab"
                id={`tab-${tab.id}`}
                tabIndex={isActive ? 0 : -1}
                aria-selected={isActive}
                aria-controls={`panel-${tab.id}`}
                onClick={() => handleTabChange(tab.id)}
                onKeyDown={(e) => handleTabKeyDown(e, idx)}
                className={`flex-1 sm:flex-initial inline-flex items-center justify-center space-x-2 py-3 px-4 border-b-2 font-medium text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 ${
                  isActive
                    ? 'border-sky-600 text-sky-700 bg-white rounded-t-lg border-t border-l border-r border-b-transparent shadow-xs'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-600' : 'text-slate-400'}`} aria-hidden="true" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Panel */}
        <div
          role="tabpanel"
          id={`panel-${activeTab}`}
          aria-labelledby={`tab-${activeTab}`}
          className="space-y-6"
        >
          {/* Input Form */}
          <AnalysisInputForm
            activeTab={activeTab}
            value={inputValue}
            onChange={(val) => {
              setInputValue(val);
              if (validationError) setValidationError(null);
            }}
            onSubmit={handleAnalyze}
            onReset={handleReset}
            loading={loading}
            validationError={validationError}
          />

          {/* Results / Status Area */}
          {loading && <LoadingState />}
          {serverError && <ErrorState message={serverError} onRetry={handleAnalyze} />}
          {!loading && !serverError && result && (
            <ResultsCard result={result} onReset={handleReset} />
          )}
          {!loading && !serverError && !result && (
            <EmptyState activeTab={activeTab} onSelectExample={handleSelectExample} />
          )}

        </div>

      </main>

      <PrivacyModal
        isOpen={isPrivacyOpen}
        onClose={() => {
          setIsPrivacyOpen(false);
          privacyTriggerRef.current?.focus();
        }}
      />
      <Footer />
    </div>
  );
};

export default function App() {
  return <AppContent />;
}

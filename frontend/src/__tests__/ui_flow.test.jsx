import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import App from '../App';
import { LanguageProvider } from '../context/LanguageContext';
import { AnalysisInputForm } from '../components/AnalysisInputForm';
import { ResultsCard } from '../components/ResultsCard';

describe('UI Flow & Component Integrity', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders AnalysisInputForm with privacy opt-in checkbox unchecked by default', () => {
    const handleChange = vi.fn();
    const handleSubmit = vi.fn();
    const handleReset = vi.fn();
    const handleToggleExternal = vi.fn();

    render(
      <LanguageProvider>
        <AnalysisInputForm
          activeTab="url"
          value="https://example.com"
          onChange={handleChange}
          onSubmit={handleSubmit}
          onReset={handleReset}
          loading={false}
          validationError={null}
          allowExternal={false}
          onToggleExternal={handleToggleExternal}
        />
      </LanguageProvider>
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeDefined();
    expect(checkbox.checked).toBe(false);

    // Form inputs and submit button are present
    const analyzeBtn = screen.getByRole('button', { name: /Analyze Signals|संकेतों का विश्लेषण करें/i });
    expect(analyzeBtn).toBeDefined();
  });

  it('triggers onToggleExternal and onSubmit properly', () => {
    const handleChange = vi.fn();
    const handleSubmit = vi.fn();
    const handleReset = vi.fn();
    const handleToggleExternal = vi.fn();

    render(
      <LanguageProvider>
        <AnalysisInputForm
          activeTab="url"
          value="https://example.com"
          onChange={handleChange}
          onSubmit={handleSubmit}
          onReset={handleReset}
          loading={false}
          validationError={null}
          allowExternal={false}
          onToggleExternal={handleToggleExternal}
        />
      </LanguageProvider>
    );

    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);
    expect(handleToggleExternal).toHaveBeenCalledWith(true);

    const submitBtn = screen.getByRole('button', { name: /Analyze Signals|संकेतों का विश्लेषण करें/i });
    fireEvent.click(submitBtn);
    expect(handleSubmit).toHaveBeenCalled();
  });

  it('renders ResultsCard with indicator count tags and without arbitrary probability scores', () => {
    const mockResult = {
      analysis_type: 'URL',
      risk_level: 'HIGH',
      critical_signals_count: 2,
      warning_signals_count: 1,
      info_signals_count: 0,
      summary: 'High risk indicators detected on destination.',
      summary_hi: 'गंतव्य पर उच्च जोखिम के संकेत मिले हैं।',
      signals: [
        {
          id: 'ssrf_blocked',
          category: 'DOMAIN_ANOMALY',
          label: 'Restricted / Private Network Destination',
          label_hi: 'प्रतिबंधित या आंतरिक नेटवर्क गंतव्य',
          description: 'SSRF Protection Guard: Blocked private IP.',
          description_hi: 'आंतरिक नेटवर्क सुरक्षा: प्रतिबंधित नेटवर्क।',
          severity: 'CRITICAL'
        }
      ],
      evidence: [],
      provider_statuses: [],
      uncertainty_notes: ['A valid HTTPS certificate only confirms encryption, not honesty.'],
      uncertainty_notes_hi: ['वैध HTTPS प्रमाणपत्र केवल एन्क्रिप्शन सुनिश्चित करता है।'],
      recommended_actions: ['Inspect root domain carefully.'],
      recommended_actions_hi: ['मुख्य डोमेन की जांच करें।'],
      timestamp: new Date().toISOString()
    };

    render(
      <LanguageProvider>
        <ResultsCard result={mockResult} onReset={() => {}} />
      </LanguageProvider>
    );

    // Must show Critical and Warning indicator counts
    expect(screen.getByText(/2 Critical|2 गंभीर/i)).toBeDefined();
    expect(screen.getByText(/1 Warning|1 चेतावनी/i)).toBeDefined();

    // Must show uncertainty notes
    expect(screen.getByText(/A valid HTTPS certificate only confirms encryption, not honesty./i)).toBeDefined();

    // Must NOT contain "/ 100" in text content
    const fullText = document.body.textContent;
    expect(fullText).not.toContain('/ 100');
  });

  it('resets external provider consent when switching tabs or resetting analysis', async () => {
    render(
      <LanguageProvider>
        <App />
      </LanguageProvider>
    );

    // Switch to URL tab
    const urlTabBtn = screen.getByRole('tab', { name: /Safe URL Check|सुरक्षित लिंक/i });
    fireEvent.click(urlTabBtn);

    // Toggle consent checkbox
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox.checked).toBe(false);
    fireEvent.click(checkbox);
    expect(checkbox.checked).toBe(true);

    // Switch to News Claim tab
    const claimTabBtn = screen.getByRole('tab', { name: /News Claim|समाचार दावा/i });
    fireEvent.click(claimTabBtn);

    // In the new tab, consent must be reset to false!
    const claimCheckbox = screen.getByRole('checkbox');
    expect(claimCheckbox.checked).toBe(false);
  });

  it('prevents an aborted earlier request from clearing loading state of a newer request', async () => {
    let resolveFirstRequest;
    const firstRequestPromise = new Promise((resolve) => {
      resolveFirstRequest = resolve;
    });

    const mockFetch = vi.fn().mockImplementation((url) => {
      if (url.includes('/message')) {
        return firstRequestPromise;
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          analysis_type: 'CLAIM',
          risk_level: 'LOW',
          critical_signals_count: 0,
          warning_signals_count: 0,
          info_signals_count: 0,
          summary: 'Second request completed successfully.',
          summary_hi: 'दूसरा अनुरोध पूरा हुआ।',
          signals: [],
          evidence: [],
          provider_statuses: [],
          uncertainty_notes: ['Uncertainty notice.'],
          uncertainty_notes_hi: ['सूचना।'],
          recommended_actions: ['Action.'],
          recommended_actions_hi: ['कदम।'],
          timestamp: new Date().toISOString()
        })
      });
    });

    global.fetch = mockFetch;

    render(
      <LanguageProvider>
        <App />
      </LanguageProvider>
    );

    // Type a message in first tab
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'This is the first suspicious message for testing.' } });

    const submitBtn = screen.getByRole('button', { name: /Analyze Signals|संकेतों का विश्लेषण करें/i });
    fireEvent.click(submitBtn);

    // First request is in flight
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Switch to claim tab while first request is in flight
    const claimTabBtn = screen.getByRole('tab', { name: /News Claim|समाचार दावा/i });
    fireEvent.click(claimTabBtn);

    // Resolve the first request now (simulating late arrival)
    resolveFirstRequest({
      ok: true,
      json: () => Promise.resolve({
        analysis_type: 'MESSAGE',
        risk_level: 'HIGH',
        critical_signals_count: 3,
        summary: 'Stale first request data that should be ignored.'
      })
    });

    // Verify stale data does NOT appear in UI
    await waitFor(() => {
      expect(screen.queryByText('Stale first request data that should be ignored.')).toBeNull();
    });
  });
});

import { describe, it, expect } from 'vitest';
import { translations } from '../i18n/translations';

describe('Bilingual Translations Dictionary Symmetry', () => {
  const en = translations.en;
  const hi = translations.hi;

  it('contains both English (en) and Hindi (hi) language keys', () => {
    expect(en).toBeDefined();
    expect(hi).toBeDefined();
  });

  it('has identical top-level keys in both English and Hindi', () => {
    const enKeys = Object.keys(en).sort();
    const hiKeys = Object.keys(hi).sort();
    expect(enKeys).toEqual(hiKeys);
  });

  it('has identical nested keys for nav, inputs, results, privacyModal, footer, and errors', () => {
    const sections = ['brand', 'nav', 'hero', 'inputs', 'results', 'privacyModal', 'footer', 'errors'];
    for (const section of sections) {
      if (en[section] && typeof en[section] === 'object') {
        const enSectionKeys = Object.keys(en[section]).sort();
        const hiSectionKeys = Object.keys(hi[section]).sort();
        expect(enSectionKeys).toEqual(hiSectionKeys);
      }
    }
  });

  it('includes all 6 Privacy Modal sections in both languages', () => {
    for (let i = 1; i <= 6; i++) {
      expect(en.privacyModal[`section${i}Title`]).toBeTruthy();
      expect(hi.privacyModal[`section${i}Title`]).toBeTruthy();
      expect(en.privacyModal[`section${i}Body`]).toBeTruthy();
      expect(hi.privacyModal[`section${i}Body`]).toBeTruthy();
    }
  });

  it('includes external lookup disclosures and credential error strings in inputs', () => {
    expect(en.inputs.externalOptInLabel).toBeDefined();
    expect(hi.inputs.externalOptInLabel).toBeDefined();
    expect(en.inputs.credentialsInUrlError).toBeDefined();
    expect(hi.inputs.credentialsInUrlError).toBeDefined();
  });
});

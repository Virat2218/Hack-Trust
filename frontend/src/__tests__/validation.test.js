import { describe, it, expect } from 'vitest';
import {
  validateMessageInput,
  validateUrlInput,
  validateClaimInput,
  isPrivateOrRestrictedHost
} from '../utils/validation';
import { translations } from '../i18n/translations';

const t = translations.en;

describe('Frontend Form Validation Suite', () => {
  describe('Message Validation', () => {
    it('rejects empty or whitespace-only messages', () => {
      const res = validateMessageInput('   ', t);
      expect(res.valid).toBe(false);
      expect(res.error).toBe(t.inputs.minMessageError);
    });

    it('rejects messages shorter than 10 characters', () => {
      const res = validateMessageInput('Too short', t);
      expect(res.valid).toBe(false);
      expect(res.error).toBe(t.inputs.minMessageError);
    });

    it('accepts valid messages with 10+ characters', () => {
      const res = validateMessageInput('Your SBI bank account has been deactivated. Update KYC immediately.', t);
      expect(res.valid).toBe(true);
      expect(res.error).toBeNull();
    });
  });

  describe('URL Validation & Security Boundaries', () => {
    it('rejects empty URL input', () => {
      const res = validateUrlInput('', t);
      expect(res.valid).toBe(false);
      expect(res.error).toBe(t.inputs.invalidUrlError);
    });

    it('strictly rejects URLs containing embedded authority credentials', () => {
      const credentialCases = [
        'http://admin:secret123@evil.com/login',
        'https://user:password@bank-portal.xyz',
        'user:pass@test.com'
      ];
      for (const url of credentialCases) {
        const res = validateUrlInput(url, t);
        expect(res.valid).toBe(false);
        expect(res.error).toBe(t.inputs.credentialsInUrlError);
      }
    });

    it('rejects private and loopback destinations (SSRF guard)', () => {
      const ssrfCases = [
        'http://localhost:8000',
        'http://127.0.0.1/admin',
        'http://169.254.169.254/latest/meta-data',
        'http://192.168.1.1/router'
      ];
      for (const url of ssrfCases) {
        const res = validateUrlInput(url, t);
        expect(res.valid).toBe(false);
        expect(res.error).toBe(t.inputs.ssrfBlockedUrlError);
      }
    });

    it('accepts and normalizes valid domains and URLs', () => {
      const validCases = [
        'https://example.com',
        'http://subdomain.bank.com/login',
        'google.com'
      ];
      for (const url of validCases) {
        const res = validateUrlInput(url, t);
        expect(res.valid).toBe(true);
        expect(res.error).toBeNull();
      }
    });
  });

  describe('News Claim Validation', () => {
    it('rejects claims shorter than 10 characters', () => {
      const res = validateClaimInput('Rumor', t);
      expect(res.valid).toBe(false);
      expect(res.error).toBe(t.inputs.minClaimError);
    });

    it('accepts detailed claims', () => {
      const res = validateClaimInput('New government scheme distributes free laptops to all students in 2026.', t);
      expect(res.valid).toBe(true);
      expect(res.error).toBeNull();
    });
  });

  describe('isPrivateOrRestrictedHost SSRF Filter', () => {
    it('identifies private IPv4 addresses correctly', () => {
      expect(isPrivateOrRestrictedHost('127.0.0.1')).toBe(true);
      expect(isPrivateOrRestrictedHost('10.50.0.1')).toBe(true);
      expect(isPrivateOrRestrictedHost('172.20.0.1')).toBe(true);
      expect(isPrivateOrRestrictedHost('192.168.0.1')).toBe(true);
      expect(isPrivateOrRestrictedHost('169.254.169.254')).toBe(true);
    });

    it('permits public hosts', () => {
      expect(isPrivateOrRestrictedHost('example.com')).toBe(false);
      expect(isPrivateOrRestrictedHost('google.com')).toBe(false);
      expect(isPrivateOrRestrictedHost('8.8.8.8')).toBe(false);
    });
  });
});

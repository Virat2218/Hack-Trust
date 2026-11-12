/**
 * Client-side input validation helpers for TrustShield AI.
 * Strict SSRF protection and length boundaries.
 */

const BLOCKED_HOSTS = [
  'localhost',
  '127.0.0.1',
  '0.0.0.0',
  '169.254.169.254', // Cloud metadata
  '[::1]',
  'metadata.google.internal'
];

export const isPrivateOrRestrictedHost = (hostname) => {
  if (!hostname) return true;
  const host = hostname.toLowerCase().trim();

  // Exact matches
  if (BLOCKED_HOSTS.includes(host)) return true;

  // Local domains
  if (host.endsWith('.local') || host.endsWith('.internal') || host.endsWith('.localhost')) {
    return true;
  }

  // IPv4 Private Range checks (Class A: 10.0.0.0/8, Class B: 172.16-31.0.0, Class C: 192.168.0.0/16)
  const ipv4Match = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (ipv4Match) {
    const p1 = parseInt(ipv4Match[1], 10);
    const p2 = parseInt(ipv4Match[2], 10);
    if (p1 === 127) return true; // Loopback
    if (p1 === 10) return true;  // Private Class A
    if (p1 === 172 && p2 >= 16 && p2 <= 31) return true; // Private Class B
    if (p1 === 192 && p2 === 168) return true; // Private Class C
    if (p1 === 169 && p2 === 254) return true; // Link-local
    if (p1 === 0) return true; // Any local
  }

  return false;
};

export const validateMessageInput = (text, t) => {
  const trimmed = (text || '').trim();
  if (trimmed.length < 10) {
    return { valid: false, error: t.inputs.minMessageError };
  }
  if (trimmed.length > 4000) {
    return { valid: false, error: t.inputs.maxMessageError };
  }
  return { valid: true, error: null };
};

export const validateUrlInput = (rawUrl, t) => {
  const trimmed = (rawUrl || '').trim();
  if (!trimmed) {
    return { valid: false, error: t.inputs.invalidUrlError };
  }

  let parsed;
  try {
    // If user forgot scheme, allow prepending https:// for parsing check
    const withScheme = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
    parsed = new URL(withScheme);
  } catch (err) {
    return { valid: false, error: t.inputs.invalidUrlError };
  }

  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    return { valid: false, error: t.inputs.invalidUrlError };
  }

  if (isPrivateOrRestrictedHost(parsed.hostname)) {
    return { valid: false, error: t.inputs.ssrfBlockedUrlError };
  }

  return { valid: true, error: null, sanitizedUrl: parsed.href };
};

export const validateClaimInput = (text, t) => {
  const trimmed = (text || '').trim();
  if (trimmed.length < 10) {
    return { valid: false, error: t.inputs.minClaimError };
  }
  if (trimmed.length > 1000) {
    return { valid: false, error: t.inputs.maxClaimError };
  }
  return { valid: true, error: null };
};


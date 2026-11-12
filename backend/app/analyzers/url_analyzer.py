import re
import socket
import ipaddress
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import List, Tuple, Optional
from app.schemas import AnalysisResult, AnalysisSignal, ProviderStatus, EvidenceItem
from app.providers.safe_browsing import SafeBrowsingProvider

HIGH_RISK_TLDS = {
    "top", "xyz", "click", "buzz", "club", "online", "cam", "loan", "work", "cfd", "rest", "fit", "gq", "ml", "tk"
}

KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "rb.gy", "goo.gl", "ow.ly", "buff.ly"
}

TARGETED_BRANDS = [
    "sbi", "hdfc", "icici", "axis", "paytm", "phonepe", "gpay", "google", "apple", "microsoft", "paypal", "netflix", "amazon"
]

def is_forbidden_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Checks if an IP is within private, loopback, link-local, multicast, or cloud metadata ranges."""
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return True
    ip_str = str(ip)
    if ip_str == "169.254.169.254" or ip_str == "100.100.100.200":
        return True
    if isinstance(ip, ipaddress.IPv4Address) and ip.exploded.startswith("0."):
        return True
    return False

def check_ssrf_strict(hostname: str) -> Tuple[bool, str]:
    if not hostname:
        return False, "Empty or missing hostname."

    clean_host = hostname.strip().strip("[]").lower()

    if clean_host in {"localhost", "localhost.localdomain", "metadata.google.internal"}:
        return False, "Target is a forbidden local hostname."

    if clean_host.endswith(".local") or clean_host.endswith(".internal") or clean_host.endswith(".localhost"):
        return False, "Target is an internal or local top-level domain."

    try:
        parsed_ip = ipaddress.ip_address(clean_host)
        if is_forbidden_ip(parsed_ip):
            return False, f"Target IP '{parsed_ip}' is in a private, loopback, or cloud-metadata network range."
        return True, str(parsed_ip)
    except ValueError:
        pass

    try:
        addr_info = socket.getaddrinfo(clean_host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for entry in addr_info:
            candidate_str = entry[4][0]
            try:
                candidate_ip = ipaddress.ip_address(candidate_str)
                if is_forbidden_ip(candidate_ip):
                    return False, f"Domain resolves to forbidden or private IP '{candidate_ip}'."
            except ValueError:
                return False, f"Invalid IP returned by DNS: '{candidate_str}'"
        return True, "Public DNS"
    except socket.gaierror:
        return True, "Unresolvable DNS"
    except Exception as e:
        return False, f"DNS resolution error: {str(e)}"

def validate_and_parse_url(raw_url: str) -> Tuple[str, str, str]:
    """
    Validates that raw_url is a valid HTTP or HTTPS URL, rejecting malformed URLs,
    unsupported schemes, and credentials in the authority section.
    Returns (normalized_url, hostname, scheme).
    Raises ValueError with a user-facing explanation on security or syntax violation.
    """
    if not raw_url or not isinstance(raw_url, str):
        raise ValueError("URL cannot be empty.")
    
    cleaned = raw_url.strip()
    if not cleaned:
        raise ValueError("URL cannot be empty or blank.")
        
    if len(cleaned) > 1000:
        raise ValueError("URL exceeds maximum permitted length of 1000 characters.")

    # Check for forbidden control characters or internal whitespace
    if re.search(r"[\s\x00-\x1f\x7f]", cleaned):
        raise ValueError("Invalid URL: contains spaces or unprintable control characters.")

    # Reject credentials in authority section (e.g., user:pass@host or user@host)
    authority_section = cleaned.split("://", 1)[1].split("/")[0] if "://" in cleaned else cleaned.split("/")[0]
    if "@" in authority_section:
        raise ValueError("URLs containing embedded credentials (user:password@) are rejected for security reasons.")

    # Check for explicit scheme (e.g., http://, ftp://, javascript:, file://, etc.)
    scheme_match = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*)://", cleaned)
    if scheme_match:
        scheme = scheme_match.group(1).lower()
        if scheme not in {"http", "https"}:
            raise ValueError(f"Unsupported URL protocol '{scheme}://'. TrustShield accepts only HTTP and HTTPS links.")
        url_to_parse = cleaned
    else:
        # Check if URL starts with a scheme like javascript: or mailto: or data: without //
        non_slashed_scheme = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):", cleaned)
        if non_slashed_scheme and non_slashed_scheme.group(1).lower() not in {"http", "https"}:
            raise ValueError(f"Unsupported URL scheme '{non_slashed_scheme.group(1)}:'. TrustShield accepts only HTTP and HTTPS links.")
        scheme = "https"
        url_to_parse = f"https://{cleaned}"

    parsed = urlparse(url_to_parse)

    # Secondary check on parsed authority
    if parsed.username or parsed.password or ("@" in parsed.netloc):
        raise ValueError("URLs containing embedded credentials (user:password@) are rejected for security reasons.")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValueError("Malformed URL: missing valid destination hostname.")

    # Validate hostname structure
    if hostname.startswith(".") or hostname.endswith(".") or ".." in hostname:
        raise ValueError("Malformed URL: destination hostname has invalid label structure.")
    
    if len(hostname) > 253:
        raise ValueError("Malformed URL: hostname exceeds maximum length of 253 characters.")

    return url_to_parse, hostname, scheme

def analyze_url_target(
    raw_url: str,
    language: str = "en",
    allow_external_lookup: bool = False
) -> AnalysisResult:
    # 1. Strict URL validation & normalization (rejects malformed URLs, credentials, non-HTTP/HTTPS schemes)
    url_to_parse, hostname, scheme = validate_and_parse_url(raw_url)
    parsed = urlparse(url_to_parse)

    # SERVER-SIDE FETCHING POLICY:
    # TrustShield AI deliberately keeps server-side URL content fetching DISABLED.
    # We do NOT execute HTTP GET/POST or scrape arbitrary user-submitted URLs.
    # Analysis is purely structural (domain, TLD, SSL scheme, SSRF boundaries, Punycode,
    # and reputation via Safe Browsing if explicitly consented).

    signals: List[AnalysisSignal] = []
    evidence_items: List[EvidenceItem] = []
    provider_statuses: List[ProviderStatus] = [
        ProviderStatus(name="Local Domain Structure & SSRF Engine", configured=True, status="ACTIVE")
    ]

    # 2. SSRF Safety Check
    is_safe, ssrf_msg = check_ssrf_strict(hostname)
    if not is_safe:
        signals.append(AnalysisSignal(
            id="ssrf_blocked",
            category="DOMAIN_ANOMALY",
            label="Restricted / Private Network Destination",
            label_hi="प्रतिबंधित या आंतरिक नेटवर्क गंतव्य",
            description=f"SSRF Protection Guard: {ssrf_msg}",
            description_hi=f"आंतरिक नेटवर्क सुरक्षा: यह पता निजी या प्रतिबंधित नेटवर्क को इंगित करता है।",
            severity="CRITICAL"
        ))

    evidence_items.append(EvidenceItem(
        source_name="Local Domain Structure & SSRF Engine",
        status="ACTIVE" if is_safe else "ERROR",
        checked_target=hostname or raw_url,
        details="Verified against SSRF private network boundaries, punycode spoofing, and brand mimicry." if is_safe else f"Blocked: {ssrf_msg}",
        details_hi="निजी नेटवर्क सीमा, प्यूनिकोड धोखाधड़ी और ब्रांड नकल के विरुद्ध जांच की गई।" if is_safe else f"प्रतिबंधित: {ssrf_msg}"
    ))

    # 3. Scheme check (HTTP is unencrypted warning, not definitive fraud)
    if parsed.scheme.lower() == "http":
        signals.append(AnalysisSignal(
            id="insecure_scheme",
            category="DOMAIN_ANOMALY",
            label="Unencrypted Connection (HTTP)",
            label_hi="असुरक्षित कनेक्शन (HTTP)",
            description="The URL uses unencrypted HTTP instead of HTTPS. While common on older sites, transmitted data lacks cryptographic protection.",
            description_hi="यह लिंक सुरक्षित HTTPS के बजाय अप्रतिबंधित HTTP का उपयोग करता है। प्रेषित डेटा सुरक्षित नहीं है।",
            severity="WARNING"
        ))

    # 4. Raw numeric IP as hostname
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
        signals.append(AnalysisSignal(
            id="raw_ip_host",
            category="DOMAIN_ANOMALY",
            label="Numeric IP Address Used as Hostname",
            label_hi="होस्टनाम के रूप में संख्यात्मक आईपी पता",
            description="Legitimate consumer sites use registered domain names rather than bare numerical IP addresses.",
            description_hi="वैध वेबसाइटें सीधे संख्यात्मक आईपी पते के बजाय पंजीकृत डोमेन नाम का उपयोग करती हैं।",
            severity="CRITICAL"
        ))

    # 5. Punycode / IDN Homoglyph detection
    if "xn--" in hostname:
        signals.append(AnalysisSignal(
            id="punycode_detected",
            category="DOMAIN_ANOMALY",
            label="Punycode / Homoglyph Domain Encoding",
            label_hi="प्यूनिकोड / समरूप वर्ण डोमेन (Punycode)",
            description="The domain uses Punycode encoding (xn--), which can disguise lookalike international characters to impersonate legitimate brand domains.",
            description_hi="डोमेन प्यूनिकोड एन्कोडिंग का उपयोग करता है, जिससे ब्रांड की नकली वेबसाइट बनाई जा सकती है।",
            severity="CRITICAL"
        ))

    # 6. High-risk TLD (Warning, not definitive proof by itself)
    tld = hostname.split(".")[-1] if "." in hostname else ""
    if tld in HIGH_RISK_TLDS:
        signals.append(AnalysisSignal(
            id="high_risk_tld",
            category="DOMAIN_ANOMALY",
            label=f"High-Risk / Low-Cost Top Level Domain (.{tld})",
            label_hi=f"उच्च-जोखिम वाला शीर्ष-स्तरीय डोमेन (.{tld})",
            description=f"The domain ends in '.{tld}', a low-cost top-level domain frequently associated with disposable phishing infrastructure.",
            description_hi=f"डोमेन '.{tld}' पर समाप्त होता है, जिसका उपयोग अक्सर फ़िशिंग अभियानों में किया जाता है।",
            severity="WARNING"
        ))

    # 7. URL Shortener detection
    if hostname in KNOWN_SHORTENERS:
        signals.append(AnalysisSignal(
            id="url_shortener",
            category="DOMAIN_ANOMALY",
            label="URL Shortener Obscuring Destination",
            label_hi="शॉर्टनर लिंक (वास्तविक गंतव्य छिपा हुआ है)",
            description="This link uses a shortening service that obscures the real destination host until visited.",
            description_hi="यह लिंक एक शॉर्टनर सेवा का उपयोग करता है जो क्लिक करने तक वास्तविक वेबसाइट को छिपाए रखता है।",
            severity="WARNING"
        ))

    # 8. Brand Mimicry in Subdomain
    parts = hostname.split(".")
    domain_root = ".".join(parts[-2:]) if len(parts) >= 2 else hostname
    for brand in TARGETED_BRANDS:
        if brand in hostname and brand not in domain_root:
            signals.append(AnalysisSignal(
                id=f"brand_mimic_{brand}",
                category="IMPERSONATION",
                label=f"Brand Mimicry in Subdomain ({brand.upper()})",
                label_hi=f"सबडोमेन में ब्रांड का भ्रामक उपयोग ({brand.upper()})",
                description=f"The URL contains '{brand}' in its subdomain, but the actual registering root domain is '{domain_root}'.",
                description_hi=f"लिंक के सबडोमेन में '{brand}' शामिल है, लेकिन वास्तविक मुख्य डोमेन '{domain_root}' है।",
                severity="CRITICAL"
            ))
            break

    # 9. Excessive Subdomain Stacking
    if len(parts) > 4:
        signals.append(AnalysisSignal(
            id="excessive_subdomains",
            category="DOMAIN_ANOMALY",
            label="Excessive Subdomain Stacking",
            label_hi="अत्यधिक सबडोमेन संरचना",
            description=f"The domain contains {len(parts)} levels, a pattern sometimes used to disguise the root destination on mobile screens.",
            description_hi=f"डोमेन में {len(parts)} स्तर हैं, जिसका उपयोग मोबाइल स्क्रीन पर असली डोमेन छिपाने के लिए किया जाता है।",
            severity="INFO"
        ))

    # 10. External Provider: Google Safe Browsing (Executed ONLY if SSRF safe AND user opt-in is granted)
    sb_provider = SafeBrowsingProvider()
    if not allow_external_lookup:
        provider_statuses.append(ProviderStatus(
            name="Google Safe Browsing API v4",
            configured=sb_provider.is_configured(),
            status="CONSENT_WITHHELD",
            details="External reputation lookup skipped per privacy settings; analyzed locally."
        ))
        evidence_items.append(EvidenceItem(
            source_name="Google Safe Browsing API v4",
            status="CONSENT_WITHHELD",
            checked_target=hostname or raw_url,
            details="External reputation query was skipped because external lookups were not enabled. Local heuristics were used.",
            details_hi="गोपनीयता सेटिंग्स के कारण बाहरी जांच छोड़ दी गई। केवल स्थानीय विश्लेषण लागू किया गया।"
        ))
    elif is_safe:
        sb_result = sb_provider.check(url_to_parse)
        provider_statuses.append(sb_result.provider_status)
        if sb_result.signals:
            signals.extend(sb_result.signals)
        evidence_items.append(EvidenceItem(
            source_name="Google Safe Browsing API v4",
            status=sb_result.provider_status.status,
            checked_target=hostname or raw_url,
            details=sb_result.provider_status.details or "Queried Safe Browsing blocklist."
        ))

    # Tally signal severities
    crit_count = sum(1 for s in signals if s.severity == "CRITICAL")
    warn_count = sum(1 for s in signals if s.severity == "WARNING")
    info_count = sum(1 for s in signals if s.severity == "INFO")

    # Calibrated risk level
    if crit_count >= 1:
        risk_level = "HIGH"
        summary = f"High risk indicators detected on destination '{hostname}' ({crit_count} critical signal{'s' if crit_count != 1 else ''}). Significant deceptive patterns or security restrictions discovered."
        summary_hi = f"गंतव्य '{hostname}' पर उच्च जोखिम के संकेत मिले हैं ({crit_count} गंभीर संकेत)। भ्रामक पैटर्न या सुरक्षा प्रतिबंध पाए गए।"
    elif warn_count >= 1:
        risk_level = "MEDIUM"
        summary = f"Caution recommended on '{hostname}' ({warn_count} warning indicator{'s' if warn_count != 1 else ''}). Verify the registering domain carefully before proceeding."
        summary_hi = f"'{hostname}' पर सावधानी की सलाह दी जाती है ({warn_count} चेतावनी संकेत)। आगे बढ़ने से पहले मुख्य डोमेन की जांच करें।"
    else:
        risk_level = "LOW"
        summary = f"Standard domain structure observed for '{hostname}'. No overt spoofing cues detected. A low signal level is not proof that the destination is safe."
        summary_hi = f"'{hostname}' के लिए सामान्य डोमेन संरचना पाई गई। कोई प्रत्यक्ष धोखाधड़ी संकेत नहीं मिले। कम जोखिम का स्तर साइट के सुरक्षित होने की गारंटी नहीं है।"

    # Internal heuristic index for backward-compatible test assertions
    heuristic_index = min((crit_count * 40) + (warn_count * 20) + (info_count * 10), 95)
    if not signals:
        heuristic_index = 12

    uncertainty_notes = [
        "Brand-new phishing sites registered minutes ago may not yet appear on public blocklists.",
        "A valid HTTPS certificate only confirms encrypted communication, not that the website owner is trustworthy.",
        "TrustShield never renders or executes arbitrary page code from untrusted links."
    ]
    uncertainty_notes_hi = [
        "कुछ ही समय पहले बनाए गए नए फ़िशिंग डोमेन तुरंत किसी सार्वजनिक ब्लॉकलिस्ट में नहीं आते हैं।",
        "वैध HTTPS प्रमाणपत्र केवल एन्क्रिप्शन सुनिश्चित करता है, यह नहीं कि साइट का मालिक ईमानदार है।",
        "ट्रस्टशील्ड सुरक्षा कारणों से अज्ञात लिंक्स के आंतरिक कोड को सीधे कभी नहीं चलाता है।"
    ]

    recommended_actions = [
        f"Carefully inspect the root domain ('{domain_root if 'domain_root' in locals() else hostname}') rather than subdomains or paths.",
        "Never enter banking credentials, passwords, or personal identity numbers on unverified links.",
        "Type known official web addresses directly into your browser bookmark rather than clicking links in messages."
    ]
    recommended_actions_hi = [
        f"सबडोमेन के बजाय मुख्य डोमेन ('{domain_root if 'domain_root' in locals() else hostname}') की सावधानीपूर्वक जांच करें।",
        "अज्ञात या असत्यापित लिंक्स पर कभी भी अपना पासवर्ड, पिन या पहचान दस्तावेज दर्ज न करें।",
        "संदेशों में आए लिंक पर क्लिक करने के बजाय आधिकारिक वेबसाइट का पता सीधे ब्राउज़र में टाइप करें।"
    ]

    return AnalysisResult(
        analysis_type="URL",
        risk_level=risk_level,
        critical_signals_count=crit_count,
        warning_signals_count=warn_count,
        info_signals_count=info_count,
        summary=summary,
        summary_hi=summary_hi,
        signals=signals,
        evidence=evidence_items,
        provider_statuses=provider_statuses,
        uncertainty_notes=uncertainty_notes,
        uncertainty_notes_hi=uncertainty_notes_hi,
        recommended_actions=recommended_actions,
        recommended_actions_hi=recommended_actions_hi,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

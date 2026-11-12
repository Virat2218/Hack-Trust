import re
import socket
import ipaddress
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import List, Tuple
from app.schemas import AnalysisResult, AnalysisSignal, ProviderStatus
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
    # Cloud metadata (AWS, GCP, Azure, OpenStack)
    if ip_str == "169.254.169.254" or ip_str == "100.100.100.200":
        return True
    # 0.0.0.0/8
    if isinstance(ip, ipaddress.IPv4Address) and ip.exploded.startswith("0."):
        return True
    return False

def check_ssrf_strict(hostname: str) -> Tuple[bool, str]:
    """
    Validates hostname against SSRF bypass techniques:
    Decimal, octal, hex, IPv6 bracketed, and standard DNS resolution.
    """
    if not hostname:
        return False, "Empty or missing hostname."

    clean_host = hostname.strip().strip("[]").lower()

    # Block well-known internal hostnames directly
    if clean_host in {"localhost", "localhost.localdomain", "metadata.google.internal"}:
        return False, "Target is a forbidden local hostname."

    if clean_host.endswith(".local") or clean_host.endswith(".internal") or clean_host.endswith(".localhost"):
        return False, "Target is an internal or local top-level domain."

    # Try parsing direct IP (handles standard decimal dotted-quad, single integer, etc.)
    try:
        parsed_ip = ipaddress.ip_address(clean_host)
        if is_forbidden_ip(parsed_ip):
            return False, f"Target IP '{parsed_ip}' is in a private, loopback, or cloud-metadata network range."
        return True, str(parsed_ip)
    except ValueError:
        pass

    # Try resolving via DNS safely
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
        # Domain does not currently resolve via DNS
        return True, "Unresolvable DNS"
    except Exception as e:
        return False, f"DNS resolution error: {str(e)}"

def analyze_url_target(raw_url: str, language: str = "en") -> AnalysisResult:
    signals: List[AnalysisSignal] = []
    score_accumulator = 0
    provider_statuses: List[ProviderStatus] = [
        ProviderStatus(name="Local Domain Structure & SSRF Engine", configured=True, status="ACTIVE")
    ]

    # Prepend scheme if omitted
    url_to_parse = raw_url.strip()
    if not re.match(r"^https?://", url_to_parse, re.IGNORECASE):
        url_to_parse = "https://" + url_to_parse

    parsed = urlparse(url_to_parse)
    hostname = (parsed.hostname or "").lower()

    # 1. SSRF Safety Check
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
        score_accumulator += 85

    # 2. Scheme checks
    if parsed.scheme.lower() == "http":
        signals.append(AnalysisSignal(
            id="insecure_scheme",
            category="DOMAIN_ANOMALY",
            label="Unencrypted Connection (HTTP)",
            label_hi="असुरक्षित कनेक्शन (HTTP)",
            description="The URL uses unencrypted HTTP instead of HTTPS, leaving transmitted credentials vulnerable to interception.",
            description_hi="यह लिंक सुरक्षित HTTPS के बजाय अप्रतिबंधित HTTP का उपयोग करता है, जिससे डेटा चोरी हो सकता है।",
            severity="WARNING"
        ))
        score_accumulator += 15

    # 3. Userinfo / At-sign deception
    if "@" in raw_url:
        signals.append(AnalysisSignal(
            id="userinfo_at_sign",
            category="DOMAIN_ANOMALY",
            label="URL Authentication Deception (@ Symbol)",
            label_hi="भ्रामक URL संरचना (@ प्रतीक का उपयोग)",
            description="The URL uses '@' syntax to mislead users into believing they are visiting the domain listed before the '@'.",
            description_hi="यह लिंक '@' प्रतीक का उपयोग करके भ्रमित करता है ताकि वास्तविक डोमेन छिप सके।",
            severity="CRITICAL"
        ))
        score_accumulator += 40

    # 4. Raw IP as hostname
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
        score_accumulator += 35

    # 5. Punycode / IDN Homoglyph detection
    if "xn--" in hostname:
        signals.append(AnalysisSignal(
            id="punycode_detected",
            category="DOMAIN_ANOMALY",
            label="Punycode / Homoglyph Domain Encoding",
            label_hi="प्यूनिकोड / समरूप वर्ण डोमेन (Punycode)",
            description="The domain uses Punycode encoding (xn--), which can be used to impersonate famous brands with lookalike foreign characters.",
            description_hi="डोमेन प्यूनिकोड एन्कोडिंग का उपयोग करता है, जिसका उपयोग अक्सर ब्रांडों की नकली वेबसाइट बनाने के लिए किया जाता है।",
            severity="CRITICAL"
        ))
        score_accumulator += 35

    # 6. High-risk TLD
    tld = hostname.split(".")[-1] if "." in hostname else ""
    if tld in HIGH_RISK_TLDS:
        signals.append(AnalysisSignal(
            id="high_risk_tld",
            category="DOMAIN_ANOMALY",
            label=f"High-Risk / Low-Cost Top Level Domain (.{tld})",
            label_hi=f"उच्च-जोखिम वाला शीर्ष-स्तरीय डोमेन (.{tld})",
            description=f"The domain ends in '.{tld}', a top-level domain frequently utilized in automated phishing campaigns.",
            description_hi=f"डोमेन '.{tld}' पर समाप्त होता है, जिसका उपयोग अक्सर फ़िशिंग अभियानों में किया जाता है।",
            severity="WARNING"
        ))
        score_accumulator += 25

    # 7. URL Shortener detection
    if hostname in KNOWN_SHORTENERS:
        signals.append(AnalysisSignal(
            id="url_shortener",
            category="DOMAIN_ANOMALY",
            label="URL Shortener Obscuring Destination",
            label_hi="शॉर्टनर लिंक (वास्तविक गंतव्य छिपा हुआ है)",
            description="This link uses a shortening service that hides the real destination domain until clicked.",
            description_hi="यह लिंक एक शॉर्टनर सेवा का उपयोग करता है जो क्लिक करने तक वास्तविक वेबसाइट को छिपाए रखता है।",
            severity="WARNING"
        ))
        score_accumulator += 20

    # 8. Brand Mimicry in Subdomain / Path
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
            score_accumulator += 40
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
        score_accumulator += 10

    # 10. External Provider: Google Safe Browsing (Executed only if URL passed SSRF validation)
    if is_safe:
        sb_provider = SafeBrowsingProvider()
        sb_result = sb_provider.check(url_to_parse)
        provider_statuses.append(sb_result.provider_status)
        if sb_result.signals:
            signals.extend(sb_result.signals)
            score_accumulator += sb_result.additional_score

    # Calculate final score
    risk_score = min(score_accumulator, 95)
    if not signals:
        risk_score = 12

    if risk_score >= 60:
        risk_level = "HIGH"
        summary = f"High risk indicators detected on destination '{hostname}'. Suspicious domain structure or deceptive patterns found."
        summary_hi = f"गंतव्य '{hostname}' पर उच्च जोखिम के संकेत मिले हैं। संदिग्ध डोमेन संरचना या भ्रामक पैटर्न पाए गए।"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
        summary = f"Notable caution indicators found on '{hostname}'. Verify the root domain carefully before visiting."
        summary_hi = f"'{hostname}' पर कुछ सावधानी के संकेत मिले हैं। वेबसाइट खोलने से पहले मुख्य डोमेन की अच्छी तरह जांच करें।"
    else:
        risk_level = "LOW"
        summary = f"Standard domain structure observed for '{hostname}'. No overt spoofing cues detected."
        summary_hi = f"'{hostname}' के लिए सामान्य डोमेन संरचना पाई गई। कोई प्रत्यक्ष धोखाधड़ी संकेत नहीं मिले।"

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
        risk_score=risk_score,
        summary=summary,
        summary_hi=summary_hi,
        signals=signals,
        provider_statuses=provider_statuses,
        uncertainty_notes=uncertainty_notes,
        uncertainty_notes_hi=uncertainty_notes_hi,
        recommended_actions=recommended_actions,
        recommended_actions_hi=recommended_actions_hi,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

import re
from datetime import datetime, timezone
from typing import List
from app.schemas import AnalysisResult, AnalysisSignal, ProviderStatus, EvidenceItem

# Curated regex heuristic patterns for message scam detection
URGENCY_PATTERNS = [
    (r"\b(within\s+\d+\s*(hours?|hrs?|mins?|minutes?)|immediately|urgent(ly)?|tonight\s+at|before\s+it'?s\s+too\s+late|action\s+required|suspended\s+today)\b", "Urgency Pressure Detected", "अत्यधिक जल्दबाजी का दबाव", "Message induces panic by demanding immediate compliance within an artificial deadline.", "संदेश कृत्रिम समय सीमा के भीतर तत्काल कार्रवाई की मांग करके डर पैदा करता है।", "CRITICAL"),
    (r"(तुरंत|तत्काल|24\s*घंटे|आज\s*रात|बंद\s*हो\s*जाएगा|निलंबित)", "Urgency Threat (Hindi)", "जल्दबाजी या निलंबन की धमकी", "Language pressures immediate response under threat of disconnection or block.", "भाषा सेवा बंद करने या खाता ब्लॉक करने की धमकी देकर तुरंत कार्रवाई का दबाव डालती है।", "CRITICAL"),
]

IMPERSONATION_PATTERNS = [
    (r"\b(electricity\s*(bill|power|officer)|power\s+will\s+be\s+disconnected|ur\s+power\s+will\s+be\s+cut)\b", "Utility / Electricity Department Impersonation", "बिजली विभाग का प्रतिरूपण", "Claims to represent a public utility threatening power cutoff over an alleged unpaid bill.", "कथित बकाया बिल को लेकर बिजली काटने की धमकी देते हुए बिजली विभाग का प्रतिरूपण करता है।", "CRITICAL"),
    (r"\b(sbi|hdfc|icici|axis|punjab\s+national|rbi|bank\s+account|bank\s+officer|debit\s+card|credit\s+card)\b", "Banking Institution Reference", "बैंक संस्थान का संदर्भ", "References a banking institution or debit/credit card services without official verification.", "बिना आधिकारिक सत्यापन के बैंक या कार्ड सेवाओं का उल्लेख करता है।", "WARNING"),
    (r"\b(kyc\s*(update|suspended|pending|expired)|pan\s*(card)?\s*(link|update|pending)|aadhaar\s*(link|update))\b", "Mandatory KYC / PAN Suspension Threat", "केवाईसी / पैन निलंबन की धमकी", "Claims user must immediately update KYC or PAN records to prevent financial service suspension.", "दावा करता है कि सेवाओं के निलंबन को रोकने के लिए उपयोगकर्ता को तुरंत केवाईसी या पैन अपडेट करना होगा।", "CRITICAL"),
    (r"\b(lottery|won\s+\d+|cash\s+prize|lucky\s+draw|congratulations\s+you\s+have\s+won|crore|lakh)\b", "Lottery / Prize Bait", "लॉटरी या नकद पुरस्कार का प्रलोभन", "Unsolicited notification claiming unexpected lottery or prize winnings.", "अप्रत्याशित लॉटरी या नकद पुरस्कार जीतने का दावा करने वाला अवांछित संदेश।", "CRITICAL"),
    (r"(बिजली\s*बिल|बैंक\s*खाता|केवाईसी|लॉटरी|इनाम|पैन\s*कार्ड)", "Official Institution Impersonation (Hindi)", "आधिकारिक संस्था का प्रतिरूपण", "Pretends to represent an electricity board, bank, or prize distribution authority.", "बिजली बोर्ड, बैंक या पुरस्कार वितरण प्राधिकरण का प्रतिरूपण करता है।", "CRITICAL"),
]

CREDENTIAL_HARVEST_PATTERNS = [
    (r"\b(otp|one\s+time\s+password|pin|upi\s*pin|cvv|netbanking\s*password|login\s*credentials?)\b", "Credential / Sensitive Authentication Request", "संवेदनशील पासवर्ड / ओटीपी का अनुरोध", "Requests or discusses sharing of confidential authentication tokens like OTP, PIN, or CVV.", "ओटीपी, पिन या सीवीवी जैसे गोपनीय प्रमाणीकरण कोड साझा करने का अनुरोध करता है।", "CRITICAL"),
    (r"\b(click\s+(here|http|link)|visit\s+http|download\s+apk|install\s+(app|apk))\b", "Suspicious Action / Link or APK Prompt", "संदिग्ध लिंक या ऐप डाउनलोड का निर्देश", "Directs recipient to click an unverified external link or install an application (APK).", "प्राप्तकर्ता को किसी असत्यापित लिंक पर क्लिक करने या बाहरी ऐप (APK) डाउनलोड करने का निर्देश देता है।", "WARNING"),
    (r"(ओटीपी|पिन|पासवर्ड|लिंक\s*पर\s*क्लिक|डाउनलोड)", "Credential Request (Hindi)", "संवेदनशील डेटा का अनुरोध", "Prompts recipient to disclose authentication details or click links.", "प्रमाणीकरण विवरण साझा करने या लिंक खोलने का अनुरोध करता है।", "CRITICAL"),
]

SUSPICIOUS_CONTACT_PATTERNS = [
    (r"\b(call\s+our\s+officer\s+at\s*\d{10}|contact\s+\d{10}|helpline\s*\d{10})\b", "Unverified Direct Mobile Number as Official Helpline", "व्यक्तिगत मोबाइल नंबर को आधिकारिक हेल्पलाइन बताना", "Gives a standard personal 10-digit mobile number as an official helpline or officer desk.", "आधिकारिक कस्टमर केयर के रूप में एक सामान्य 10 अंकों का व्यक्तिगत मोबाइल नंबर प्रदान करता है।", "WARNING"),
    (r"\b(https?://\S+(\.top|\.xyz|\.click|\.online|\.buzz|\.club|\.info|\.cc|\.tk|\.ga|\.ml))\b", "Suspicious / Cheap TLD Link in Message", "संदिग्ध या उच्च-जोखिम डोमेन लिंक", "Message includes a link on a top-level domain frequently associated with automated scam campaigns.", "संदिग्ध शीर्ष-स्तरीय डोमेन का लिंक शामिल है जो अक्सर फ़िशिंग अभियानों में उपयोग किया जाता है।", "CRITICAL"),
]

def analyze_message_text(text: str, language: str = "en") -> AnalysisResult:
    signals: List[AnalysisSignal] = []
    lowered = text.lower()

    all_groups = [
        ("URGENCY", URGENCY_PATTERNS),
        ("IMPERSONATION", IMPERSONATION_PATTERNS),
        ("CREDENTIAL_HARVEST", CREDENTIAL_HARVEST_PATTERNS),
        ("FINANCIAL", SUSPICIOUS_CONTACT_PATTERNS),
    ]

    seen_ids = set()
    for cat, pattern_list in all_groups:
        for idx, (regex, lbl, lbl_hi, desc, desc_hi, severity) in enumerate(pattern_list):
            if re.search(regex, lowered, re.IGNORECASE):
                sig_id = f"{cat.lower()}_{idx}"
                if sig_id not in seen_ids:
                    seen_ids.add(sig_id)
                    signals.append(AnalysisSignal(
                        id=sig_id,
                        category=cat,
                        label=lbl,
                        label_hi=lbl_hi,
                        description=desc,
                        description_hi=desc_hi,
                        severity=severity,
                    ))

    # Check for presence of URL inside message
    url_match = re.search(r"https?://\S+", text)
    if url_match and not any(s.category == "FINANCIAL" and "TLD" in s.label for s in signals):
        signals.append(AnalysisSignal(
            id="url_present",
            category="CREDENTIAL_HARVEST",
            label="External Web Link Present in SMS/Text",
            label_hi="संदेश में बाहरी वेब लिंक मौजूद है",
            description="Official institutions rarely send raw SMS links requesting immediate action.",
            description_hi="आधिकारिक संस्थान तत्काल कार्रवाई की मांग करने वाले लिंक शायद ही कभी एसएमएस में भेजते हैं।",
            severity="WARNING"
        ))

    # Tally signal severities
    crit_count = sum(1 for s in signals if s.severity == "CRITICAL")
    warn_count = sum(1 for s in signals if s.severity == "WARNING")
    info_count = sum(1 for s in signals if s.severity == "INFO")

    # Calibrated risk determination based on transparent signal triggers
    if crit_count >= 2 or (crit_count >= 1 and warn_count >= 1):
        risk_level = "HIGH"
        summary = f"High risk scam indicators detected ({crit_count} critical, {warn_count} warning). The message exhibits aggressive urgency, impersonation, or credential requests."
        summary_hi = f"धोखाधड़ी के उच्च जोखिम संकेत मिले हैं ({crit_count} गंभीर, {warn_count} चेतावनी)। संदेश में जल्दबाजी, संस्थान के प्रतिरूपण या डेटा के अनुरोध के स्पष्ट संकेत हैं।"
    elif crit_count == 1 or warn_count >= 1:
        risk_level = "MEDIUM"
        summary = f"Caution recommended ({crit_count} critical, {warn_count} warning signal{'s' if warn_count != 1 else ''}). Notable suspicious indicators discovered."
        summary_hi = f"सावधानी बरतने की आवश्यकता है ({crit_count} गंभीर, {warn_count} चेतावनी संकेत)। कुछ संदिग्ध संकेत पाए गए हैं।"
    else:
        risk_level = "LOW"
        summary = "Few or no scam indicators detected in this content. A low signal level is not proof that the message is safe or authentic."
        summary_hi = "धोखाधड़ी के कोई स्पष्ट संकेत नहीं मिले हैं। कम जोखिम का स्तर यह साबित नहीं करता कि संदेश सुरक्षित या प्रामाणिक है।"

    # Internal heuristic index for backward-compatible test assertions
    heuristic_index = min((crit_count * 35) + (warn_count * 18) + (info_count * 8), 95)
    if not signals:
        heuristic_index = 10

    evidence_items = [
        EvidenceItem(
            source_name="Local Heuristic Rule Engine",
            status="ACTIVE",
            checked_target="Message Text Content",
            details=f"Evaluated against urgency, impersonation, credential harvesting, and suspicious contact rules ({len(signals)} matching signals discovered).",
            details_hi=f"जल्दबाजी, प्रतिरूपण, क्रेडेंशियल चोरी और संदिग्ध संपर्क नियमों के विरुद्ध मूल्यांकन किया गया ({len(signals)} संकेत मिले)।"
        )
    ]

    uncertainty_notes = [
        "This heuristic analysis inspects message patterns only; it cannot verify personal account balances or official records.",
        "Scammers continuously evolve their phrasing to bypass keyword checks.",
        "A 'Low Risk' result is an analytical indicator, not a legal or security guarantee."
    ]
    uncertainty_notes_hi = [
        "यह विश्लेषण केवल संदेश के पैटर्न की जांच करता है; यह आपके बैंक खाते या सरकारी रिकॉर्ड को सत्यापित नहीं कर सकता।",
        "धोखेबाज सुरक्षा जांच से बचने के लिए लगातार नए शब्दों का उपयोग करते हैं।",
        "'कम जोखिम' एक विश्लेषणात्मक संकेत है, कोई कानूनी या सुरक्षा गारंटी नहीं।"
    ]

    recommended_actions = [
        "Never share an OTP, PIN, password, or UPI secret with anyone calling or texting you.",
        "Do not click on unverified links or download files (APKs) sent via SMS or messaging apps.",
        "If the message mentions a bank, utility, or government service, call their verified official number found on their official website or on your physical card/bill."
    ]
    recommended_actions_hi = [
        "कॉल या मैसेज करने वाले किसी भी व्यक्ति के साथ ओटीपी, पिन, पासवर्ड या यूपीआई पिन कभी साझा न करें।",
        "संदिग्ध लिंक पर क्लिक न करें और न ही कोई अज्ञात ऐप (APK) डाउनलोड करें।",
        "यदि संदेश बैंक या बिजली विभाग का है, तो उनके आधिकारिक बिल या बैंक कार्ड के पीछे दिए गए हेल्पलाइन नंबर पर ही संपर्क करें।"
    ]

    return AnalysisResult(
        analysis_type="MESSAGE",
        risk_level=risk_level,
        critical_signals_count=crit_count,
        warning_signals_count=warn_count,
        info_signals_count=info_count,
        summary=summary,
        summary_hi=summary_hi,
        signals=signals,
        evidence=evidence_items,
        provider_statuses=[
            ProviderStatus(name="Local Heuristic Rule Engine", configured=True, status="ACTIVE"),
        ],
        uncertainty_notes=uncertainty_notes,
        uncertainty_notes_hi=uncertainty_notes_hi,
        recommended_actions=recommended_actions,
        recommended_actions_hi=recommended_actions_hi,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

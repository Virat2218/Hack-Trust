import re
from datetime import datetime, timezone
from typing import List
from app.schemas import AnalysisResult, AnalysisSignal, ProviderStatus
from app.providers.fact_check import FactCheckProvider

VIRAL_SENSATIONAL_PATTERNS = [
    (r"\b(100%\s*(cure|effective|guaranteed)|miracle\s+cure|cure\s+for\s+cancer|doctors\s+(don'?t\s+want\s+you\s+to\s+know|secretly\s+admit)|scientists\s+stunned)\b", "Extreme Health Miracle / Unverified Medical Claim", "अतिशयोक्तिपूर्ण स्वास्थ्य या चमत्कारी इलाज का दावा", "Claims an absolute, unverified medical miracle or cure while alleging suppression by medical professionals.", "बिना वैज्ञानिक प्रमाण के 100% इलाज या चमत्कारी परिणाम का दावा करता है।", "CRITICAL"),
    (r"\b(forward\s+to\s+(everyone|all\s+groups|your\s+family)|share\s+before\s+deleted|viral\s+video\s+proves|breaking\s+news\s+shock)\b", "Viral Forwarding Pressure", "वायरल करने और आगे भेजने का दबाव", "Uses artificial urgency prompting recipients to spread the message to others without verification.", "संदेश बिना पुष्टि किए अन्य लोगों को तुरंत शेयर करने का अनुचित दबाव डालता है।", "WARNING"),
    (r"\b(free\s*(recharge|smartphones?|laptops?|tablets?|electric\s*scooters?)|subsidy\s+of\s+rs|pm\s+yojana\s+giving\s+\d+|scheme\s+giving\s+free)\b", "Unverified Government Free Scheme / Subsidy Bait", "फर्जी सरकारी योजना या मुफ्त उपहार का दावा", "Claims government or public authorities are distributing free electronic goods or cash subsidies via forwarded links.", "दावा करता है कि सरकार मुफ्त मोबाइल, लैपटॉप या पैसे बांट रही है।", "CRITICAL"),
    (r"\b(secret\s+truth|media\s+won'?t\s+tell\s+you|banned\s+in\s+india|censored\s+news)\b", "Conspiracy / Suppression Framing", "सच्चाई छिपाने या षड्यंत्र का दावा", "Presents content under the guise of censored or hidden secrets to discourage mainstream cross-checking.", "पारंपरिक समाचार स्रोतों से पुष्टि रोकने के लिए षड्यंत्रकारी भाषा का उपयोग करता है।", "WARNING"),
    (r"(चमत्कारी\s*इलाज|100%\s*(इलाज|कैंसर|ठीक|गारंटी)|कैंसर\s*का\s*इलाज)", "Miracle Cure Claim (Hindi)", "चमत्कारी या 100% इलाज का दावा", "Claims an absolute medical miracle or cure without scientific basis.", "बिना वैज्ञानिक प्रमाण के 100% इलाज या चमत्कारी परिणाम का दावा करता है।", "CRITICAL"),
    (r"(सबको\s*(भेजें|शेयर\s*करें)|आगे\s*भेजें|ग्रुप\s*में\s*भेजें|शेयर\s*करें|डिलीट\s*होने\s*से\s*पहले)", "Viral Forwarding Pressure (Hindi)", "वायरल करने और आगे भेजने का दबाव", "Prompts recipients to forward the message immediately without independent verification.", "संदेश बिना पुष्टि किए अन्य लोगों को तुरंत शेयर करने का अनुचित दबाव डालता है।", "WARNING"),
    (r"(मुफ्त\s*(रिचार्ज|मोबाइल|लैपटॉप)|योजना\s*के\s*तहत\s*पैसे|सरकारी\s*योजना\s*में\s*मुफ्त)", "Fake Government Scheme Bait (Hindi)", "फर्जी सरकारी योजना या मुफ्त उपहार का दावा", "Promotes unverified government schemes or giveaways via forwarded messages.", "दावा करता है कि सरकार मुफ्त मोबाइल, लैपटॉप या पैसे बांट रही है।", "CRITICAL"),
]

VAGUE_AUTHORITY_PATTERNS = [
    (r"\b(nasa\s+has\s+confirmed|who\s+secretly\s+warned|unesco\s+declared|oxford\s+university\s+study\s+proves)\b", "Vague / Questionable Authority Appeal", "संदिग्ध या अप्रमाणित संस्थागत संदर्भ", "Appeals to prestigious global institutions (NASA, WHO, UNESCO) without citing a verifiable publication date or study link.", "बिना किसी शोध पत्र या लिंक के यूनेस्को, नासा या डब्ल्यूएचओ जैसी संस्थाओं के नाम का दुरुपयोग करता है।", "WARNING"),
    (r"(नासा\s*ने\s*कहा|यूनेस्को\s*ने\s*घोषित\s*किया|डॉक्टरों\s*का\s*मानना)", "Unverified Authority Appeal (Hindi)", "संस्था का नाम लेकर भ्रामक दावा", "Mentions respected bodies without verifiable press releases.", "बिना किसी प्रेस विज्ञप्ति के प्रतिष्ठित संस्थाओं का नाम लेता है।", "WARNING"),
]

def analyze_claim_text(text: str, language: str = "en") -> AnalysisResult:
    signals: List[AnalysisSignal] = []
    lowered = text.lower()
    score_accumulator = 0

    all_groups = [
        ("UNVERIFIED_SOURCE", VIRAL_SENSATIONAL_PATTERNS),
        ("UNVERIFIED_SOURCE", VAGUE_AUTHORITY_PATTERNS),
    ]

    seen = set()
    for cat, pattern_list in all_groups:
        for idx, (regex, lbl, lbl_hi, desc, desc_hi, severity) in enumerate(pattern_list):
            if re.search(regex, lowered, re.IGNORECASE):
                sig_id = f"claim_{idx}"
                if sig_id not in seen:
                    seen.add(sig_id)
                    signals.append(AnalysisSignal(
                        id=sig_id,
                        category=cat,
                        label=lbl,
                        label_hi=lbl_hi,
                        description=desc,
                        description_hi=desc_hi,
                        severity=severity,
                    ))
                    if severity == "CRITICAL":
                        score_accumulator += 40
                    elif severity == "WARNING":
                        score_accumulator += 25
                    else:
                        score_accumulator += 10

    # Provider statuses: Local Heuristics + Fact Check API
    provider_statuses = [
        ProviderStatus(name="Local Viral & Claim Indicator Engine", configured=True, status="ACTIVE")
    ]

    # External Fact Check Provider
    fc_provider = FactCheckProvider()
    fc_result = fc_provider.check(text, language=language)
    provider_statuses.append(fc_result.provider_status)
    if fc_result.signals:
        signals.extend(fc_result.signals)
        score_accumulator += fc_result.additional_score

    risk_score = min(score_accumulator, 95)
    if not signals:
        risk_score = 15

    if risk_score >= 60:
        risk_level = "HIGH"
        summary = "Multiple high-risk viral misinformation indicators detected (unverified miracle cures, false government schemes, or sensational pressure)."
        summary_hi = "वायरल भ्रामक सूचना के कई उच्च संकेत मिले हैं (असत्यापित चमत्कारी इलाज, फर्जी सरकारी योजनाएं या सनसनीखेज दबाव)।"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
        summary = "Notable unverified claim indicators found. The statement lacks primary publisher citations or institutional verification."
        summary_hi = "कुछ असत्यापित संकेत पाए गए हैं। इस कथन में प्राथमिक प्रकाशक या आधिकारिक संदर्भ का अभाव है।"
    else:
        risk_level = "LOW"
        summary = "Standard assertion phrasing. No blatant sensationalist or viral forwarding cues detected."
        summary_hi = "सामान्य कथन भाषा पाई गई। कोई स्पष्ट सनसनीखेज या भ्रामक संकेत नहीं मिले।"

    uncertainty_notes = [
        "TrustShield AI evaluates linguistic indicators and claim patterns; it cannot arbitrate factual historical truth.",
        "A lack of sensationalism signals does not automatically confirm that an unverified claim is factual.",
        "Legitimate scientific discoveries and government notices are published directly on official agency portals (.gov.in, .gov, or peer-reviewed journals)."
    ]
    uncertainty_notes_hi = [
        "ट्रस्टशील्ड AI केवल भाषा के संकेतों और पैटर्न का मूल्यांकन करता है; यह किसी ऐतिहासिक या वैज्ञानिक तथ्य का अंतिम निर्णायक नहीं है।",
        "सनसनीखेज भाषा न होने का अर्थ यह नहीं है कि कोई दावा पूरी तरह सत्य है।",
        "वैध वैज्ञानिक खोजें और सरकारी घोषणाएं आधिकारिक पोर्टल्स (.gov.in, .gov) या प्रतिष्ठित पत्रिकाओं पर प्रकाशित की जाती हैं।"
    ]

    recommended_actions = [
        "Search the exact claim or headline in Google News to see if established, reputable news outlets have reported it.",
        "Check recognized independent fact-checking databases (such as PIB Fact Check, AltNews, BOOM Live, or Snopes).",
        "Do not forward or amplify health advice or viral scheme messages to family or group chats until verified with primary sources."
    ]
    recommended_actions_hi = [
        "सटीक हेडलाइन को गूगल न्यूज़ पर खोजें और देखें कि क्या किसी स्थापित समाचार संगठन ने इसकी रिपोर्टिंग की है।",
        "मान्यता प्राप्त फैक्ट-चेकिंग वेबसाइटों (जैसे पीआईबी फैक्ट चेक, बूम लाइव आदि) पर जांच करें।",
        "जब तक प्राथमिक स्रोतों से पुष्टि न हो जाए, तब तक स्वास्थ्य संबंधी सलाह या मुफ्त योजना के संदेशों को दूसरों को न भेजें।"
    ]

    return AnalysisResult(
        analysis_type="CLAIM",
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

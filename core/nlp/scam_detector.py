import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import re
import json
from datetime import datetime
from config import (SCAM_KEYWORDS, LANGUAGE_KEYWORDS, LANGUAGE_NAMES,
                    SCAM_PATTERNS, SCAM_KEYWORD_THRESHOLD, LOG_PATH)

class ScamDetector:
    def __init__(self):
        self.detected_keywords = []
        self.alert_log         = []
        self.scam_patterns     = SCAM_PATTERNS

    def detect_language(self, text: str) -> str:
        """
        Simple language detection based on script and keyword presence.
        Returns language code: 'en', 'hi', 'kn', 'ta'
        """
        # Check for native scripts first (most reliable)
        kannada_chars = sum(1 for c in text if '\u0C80' <= c <= '\u0CFF')
        hindi_chars   = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        tamil_chars   = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')

        if kannada_chars > 2:
            return "kn"
        if hindi_chars > 2:
            return "hi"
        if tamil_chars > 2:
            return "ta"

        # Check transliterated keywords
        text_lower = text.lower()
        kn_hits = sum(1 for kw in LANGUAGE_KEYWORDS["kn"]
                      if kw.lower() in text_lower and all(ord(c) < 128 for c in kw))
        hi_hits = sum(1 for kw in LANGUAGE_KEYWORDS["hi"]
                      if kw.lower() in text_lower and all(ord(c) < 128 for c in kw))
        ta_hits = sum(1 for kw in LANGUAGE_KEYWORDS["ta"]
                      if kw.lower() in text_lower and all(ord(c) < 128 for c in kw))

        if kn_hits > hi_hits and kn_hits > ta_hits:
            return "kn"
        if hi_hits > kn_hits and hi_hits > ta_hits:
            return "hi"
        if ta_hits > 0:
            return "ta"

        return "en"

    def analyze_text(self, text: str) -> dict:
        text_lower      = text.lower()
        found_keywords  = []
        found_patterns  = []

        # Detect language
        lang      = self.detect_language(text)
        lang_name = LANGUAGE_NAMES.get(lang, "Unknown")

        # Check ALL language keywords (scammers mix languages)
        for keyword in SCAM_KEYWORDS:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)

        # Regex patterns
        for pattern in self.scam_patterns:
            match = re.search(pattern, text_lower)
            if match:
                found_patterns.append(match.group())

        # Score
        keyword_score = len(found_keywords)
        pattern_score = len(found_patterns) * 1.5
        total_score   = keyword_score + pattern_score

        # Risk level
        if total_score == 0:
            risk = "SAFE"
        elif total_score < SCAM_KEYWORD_THRESHOLD:
            risk = "SUSPICIOUS"
        else:
            risk = "DANGER"

        result = {
            "timestamp"      : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text_analyzed"  : text,
            "language"       : lang,
            "language_name"  : lang_name,
            "found_keywords" : found_keywords,
            "found_patterns" : found_patterns,
            "total_score"    : total_score,
            "risk_level"     : risk,
            "alert"          : risk == "DANGER",
        }

        if risk != "SAFE":
            self._log_alert(result)

        return result

    def _log_alert(self, result: dict):
        try:
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps(result) + "\n")
        except Exception as e:
            print(f"Logging error: {e}")

    def get_risk_summary(self, results: list) -> str:
        if not results:
            return "No analysis done yet."
        danger_count    = sum(1 for r in results if r["risk_level"] == "DANGER")
        suspicious_count = sum(1 for r in results if r["risk_level"] == "SUSPICIOUS")
        langs_detected  = set(r.get("language_name", "Unknown") for r in results)
        return (f"Session Summary: {danger_count} DANGER alerts, "
                f"{suspicious_count} SUSPICIOUS flags. "
                f"Languages detected: {', '.join(langs_detected)}")


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    detector = ScamDetector()

    test_cases = [
        # English
        ("en", "Hello, how are you doing today?"),
        ("en", "You are under digital arrest. Do not tell anyone."),
        # Hindi
        ("hi", "Aap digital giraftari mein hain. Kisi ko mat batao. Abhi paisa transfer karo."),
        ("hi", "यह CBI अधिकारी बोल रहा हूँ। आपका खाता freeze हो गया है।"),
        # Kannada
        ("kn", "Nimma hesaru digital badhavane case nalli ide. Yaarigu helabedi."),
        ("kn", "ನಿಮ್ಮ ಖಾತೆ ಫ್ರೀಜ್ ಆಗಿದೆ. ತಕ್ಷಣ ಹಣ ವರ್ಗಾಯಿಸಿ."),
        # Tamil
        ("ta", "Ungal peyar case la irukku. Yarukkum sollathe. Ipave transfer pannu."),
        # Mixed language (common in real scams)
        ("mixed", "This is CBI officer. Aapka digital arrest ho gaya hai. Yaarigu helabedi."),
    ]

    print("=" * 65)
    print("   SENTINEL-GUARD — Multilingual Scam Detector Test")
    print("=" * 65)

    results = []
    for expected_lang, text in test_cases:
        result = detector.analyze_text(text)
        results.append(result)
        risk   = result["risk_level"]
        icon   = "🚨" if risk=="DANGER" else "⚠️" if risk=="SUSPICIOUS" else "✅"
        lang   = result["language_name"]

        print(f"\n[Expected: {expected_lang.upper()}] Detected: {lang}")
        print(f"  Text  : {text[:65]}{'...' if len(text)>65 else ''}")
        print(f"  {icon} Risk  : {risk} | Score: {result['total_score']}")
        if result["found_keywords"]:
            print(f"  🔑 Keywords: {result['found_keywords'][:3]}")

    print("\n" + "=" * 65)
    print(detector.get_risk_summary(results))

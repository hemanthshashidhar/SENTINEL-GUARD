import json
import re
from datetime import datetime
from config import SCAM_KEYWORDS, SCAM_KEYWORD_THRESHOLD, LOG_PATH

class ScamDetector:
    def __init__(self):
        self.detected_keywords = []
        self.alert_log = []
        self.scam_patterns = [
            r"don.t (tell|inform|contact)",
            r"keep (video|camera) on",
            r"(transfer|send).{0,20}(money|amount|funds)",
            r"(arrest|warrant|FIR).{0,20}(your name|registered)",
            r"(CBI|ED|RBI|cyber cell).{0,20}(officer|investigation)",
            r"do not (hang|disconnect|cut)",
        ]

    def analyze_text(self, text: str) -> dict:
        text_lower = text.lower()
        found_keywords = []
        found_patterns = []

        # Keyword matching
        for keyword in SCAM_KEYWORDS:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)

        # Regex pattern matching
        for pattern in self.scam_patterns:
            match = re.search(pattern, text_lower)
            if match:
                found_patterns.append(match.group())

        # Score calculation
        keyword_score = len(found_keywords)
        pattern_score = len(found_patterns) * 1.5  # patterns weigh more
        total_score = keyword_score + pattern_score

        # Risk level
        if total_score == 0:
            risk = "SAFE"
            risk_color = "green"
        elif total_score < SCAM_KEYWORD_THRESHOLD:
            risk = "SUSPICIOUS"
            risk_color = "orange"
        else:
            risk = "DANGER"
            risk_color = "red"

        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text_analyzed": text,
            "found_keywords": found_keywords,
            "found_patterns": found_patterns,
            "total_score": total_score,
            "risk_level": risk,
            "risk_color": risk_color,
            "alert": risk == "DANGER"
        }

        # Log if suspicious or dangerous
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
        danger_count = sum(1 for r in results if r["risk_level"] == "DANGER")
        suspicious_count = sum(1 for r in results if r["risk_level"] == "SUSPICIOUS")
        return f"Session Summary: {danger_count} DANGER alerts, {suspicious_count} SUSPICIOUS flags detected."


# ── Quick test ──────────────────────────────────────────────
if __name__ == "__main__":
    detector = ScamDetector()

    test_cases = [
        "Hello, how are you doing today?",
        "This is CBI officer speaking, FIR has been registered against you.",
        "You are under digital arrest. Do not tell anyone. Keep your video on. Transfer money immediately to clear your name.",
        "Your account is frozen due to money laundering case. ED office has issued arrest warrant."
    ]

    print("=" * 60)
    print("       SENTINEL-GUARD — NLP Scam Detector Test")
    print("=" * 60)

    results = []
    for i, text in enumerate(test_cases, 1):
        result = detector.analyze_text(text)
        results.append(result)
        print(f"\nTest {i}: '{text[:50]}...' " if len(text) > 50 else f"\nTest {i}: '{text}'")
        print(f"  Risk Level  : {result['risk_level']}")
        print(f"  Score       : {result['total_score']}")
        print(f"  Keywords    : {result['found_keywords']}")
        print(f"  Patterns    : {result['found_patterns']}")
        print(f"  ALERT       : {'🚨 YES' if result['alert'] else '✅ NO'}")

    print("\n" + "=" * 60)
    print(detector.get_risk_summary(results))

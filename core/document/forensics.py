import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import re
import json
import pytesseract
from PIL import Image
from datetime import datetime
from config import SCAM_KEYWORDS, LOG_PATH

class DocumentForensics:
    def __init__(self):
        self.suspicious_indicators = []

        # Official document formatting rules
        self.official_seals = [
            "government of india", "ministry of home affairs",
            "central bureau of investigation", "enforcement directorate",
            "supreme court of india", "high court", "district court",
            "reserve bank of india", "income tax department"
        ]

        self.forgery_redflags = [
            r"whatsapp",
            r"gmail\.com",
            r"yahoo\.com",
            r"pay.{0,10}(upi|paytm|gpay|phonepe)",
            r"transfer.{0,20}(within|immediately|urgent|now)",
            r"do not (share|show|tell)",
            r"(call|contact).{0,20}(immediately|urgently|now)",
            r"fine.{0,10}(rs|₹|inr).{0,10}\d+",
        ]

        # Fonts/formatting anomalies we check via text analysis
        self.format_checks = {
            "has_case_number": r"(case|FIR|complaint).{0,10}(no|number|#)\.?\s*\d+",
            "has_date": r"\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}",
            "has_official_address": r"(new delhi|mumbai|kolkata|chennai).{0,30}(110|400|700|600)\d{3}",
            "has_signature_line": r"(signature|signed by|authorized by|seal of)",
            "has_proper_header": r"(government|ministry|court|bureau|department)",
        }

    def extract_text_from_image(self, image_path: str) -> str:
        """OCR extraction from document image."""
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text
        except Exception as e:
            return f"OCR Error: {e}"

    def analyze_document(self, text: str, source: str = "unknown") -> dict:
        """Full forensic analysis of document text."""
        text_lower = text.lower()
        findings = []
        red_flags = []
        format_scores = {}
        scam_keywords_found = []

        # 1. Check for scam keywords
        for keyword in SCAM_KEYWORDS:
            if keyword.lower() in text_lower:
                scam_keywords_found.append(keyword)

        # 2. Check forgery red flags
        for pattern in self.forgery_redflags:
            match = re.search(pattern, text_lower)
            if match:
                red_flags.append(f"Suspicious phrase: '{match.group()}'")

        # 3. Format legitimacy checks
        for check_name, pattern in self.format_checks.items():
            match = re.search(pattern, text_lower)
            format_scores[check_name] = bool(match)

        # 4. Check if claims to be official but has red flags
        claims_official = any(seal in text_lower for seal in self.official_seals)
        legitimacy_score = sum(format_scores.values())  # 0-5

        # 5. Verdict
        if red_flags or scam_keywords_found:
            if claims_official:
                verdict = "FORGED"
                confidence = 90 if len(red_flags) > 1 else 70
            else:
                verdict = "SUSPICIOUS"
                confidence = 60
        elif legitimacy_score >= 4:
            verdict = "LIKELY LEGITIMATE"
            confidence = 75
        else:
            verdict = "UNVERIFIED"
            confidence = 50

        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "verdict": verdict,
            "confidence": confidence,
            "claims_official": claims_official,
            "legitimacy_score": f"{legitimacy_score}/5",
            "scam_keywords_found": scam_keywords_found,
            "red_flags": red_flags,
            "format_checks": format_scores,
            "alert": verdict in ["FORGED", "SUSPICIOUS"]
        }

        if result["alert"]:
            self._log_alert(result)

        return result

    def _log_alert(self, result: dict):
        try:
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps(result) + "\n")
        except Exception as e:
            print(f"Logging error: {e}")

    def print_report(self, result: dict):
        print("\n" + "=" * 60)
        print("       SENTINEL-GUARD — Document Forensics Report")
        print("=" * 60)
        print(f"  Verdict         : {result['verdict']}  (Confidence: {result['confidence']}%)")
        print(f"  Claims Official : {result['claims_official']}")
        print(f"  Legitimacy Score: {result['legitimacy_score']}")
        print(f"  Scam Keywords   : {result['scam_keywords_found']}")
        print(f"  Red Flags       : {result['red_flags']}")
        print(f"  Format Checks   :")
        for check, passed in result['format_checks'].items():
            icon = "✅" if passed else "❌"
            print(f"    {icon} {check.replace('_', ' ').title()}")
        print(f"\n  ALERT           : {'🚨 DOCUMENT IS FORGED/SUSPICIOUS' if result['alert'] else '✅ No alert'}")
        print("=" * 60)


# ── Quick test ──────────────────────────────────────────────
if __name__ == "__main__":
    forensics = DocumentForensics()

    print("=" * 60)
    print("       SENTINEL-GUARD — Document Forensics Test")
    print("=" * 60)

    # Simulated fake FIR document text (what scammers send on WhatsApp)
    fake_fir = """
    GOVERNMENT OF INDIA
    Central Bureau of Investigation
    FIR No: CBI/2024/MH/4521

    This is to inform you that your name has appeared in a money
    laundering case. An arrest warrant has been issued.

    You must transfer Rs. 50,000 immediately via GPay or PhonePe
    to avoid arrest. Do not share this document with anyone.

    Contact officer immediately on WhatsApp: 9876543210
    Payment must be done within 2 hours.

    Signed by: Officer Sharma
    Date: 15/03/2024
    """

    # Simulated real government notice
    real_notice = """
    GOVERNMENT OF INDIA
    Ministry of Home Affairs
    New Delhi - 110001

    Case No: MHA/2024/1234
    Date: 15/03/2024

    This notice is issued regarding compliance requirements.
    Please appear before the designated authority on the date mentioned.

    Authorized by: Joint Secretary
    Signature: [Official Seal of Ministry of Home Affairs]
    """

    print("\n[TEST 1] Analyzing fake scam FIR...")
    result1 = forensics.analyze_document(fake_fir, source="WhatsApp_document")
    forensics.print_report(result1)

    print("\n[TEST 2] Analyzing legitimate government notice...")
    result2 = forensics.analyze_document(real_notice, source="official_notice")
    forensics.print_report(result2)

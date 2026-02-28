import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import re
import json
from datetime import datetime
from config import LOG_PATH

class CallerAnalyzer:
    def __init__(self):
        self.agency_patterns = {
            "CBI": {
                "valid_prefixes": ["011"],
                "hq_location"  : "New Delhi (011)",
                "fact"         : "CBI HQ is in New Delhi. They only call from 011-XXXXXXXX landlines. Never from mobile or WhatsApp.",
            },
            "ED": {
                "valid_prefixes": ["011", "022"],
                "hq_location"  : "New Delhi / Mumbai",
                "fact"         : "ED offices use government landlines only. Never WhatsApp or mobile numbers.",
            },
            "RBI": {
                "valid_prefixes": ["022"],
                "hq_location"  : "Mumbai (022)",
                "fact"         : "RBI never contacts individuals directly about legal cases.",
            },
            "TRAI": {
                "valid_prefixes": ["011"],
                "hq_location"  : "New Delhi (011)",
                "fact"         : "TRAI uses 011 landlines only. Never demands payment over call.",
            },
            "Income Tax": {
                "valid_prefixes": ["011", "022", "080", "033", "044"],
                "hq_location"  : "Major city landlines only",
                "fact"         : "Income Tax dept sends notices via post/email. Never demands payment over call.",
            },
            "Cyber Police": {
                "valid_prefixes": ["1930"],
                "hq_location"  : "National Cyber Crime Helpline: 1930",
                "fact"         : "Cyber police helpline is 1930. They never call you first.",
            },
            "Supreme Court": {
                "valid_prefixes": ["011"],
                "hq_location"  : "New Delhi (011)",
                "fact"         : "Supreme Court communicates via official notices only. Never phone calls.",
            },
            "Customs": {
                "valid_prefixes": ["011", "022", "080"],
                "hq_location"  : "Port city landlines",
                "fact"         : "Customs dept sends written notices. Never demands payment over phone.",
            },
        }

        self.std_codes = {
            "011" : "New Delhi",
            "022" : "Mumbai",
            "080" : "Bengaluru",
            "033" : "Kolkata",
            "044" : "Chennai",
            "040" : "Hyderabad",
            "020" : "Pune",
            "0172": "Chandigarh",
            "0484": "Kochi",
        }

        self.known_scam_series = [
            "9958", "8800", "7011", "9999",
            "7678", "8527", "9315", "8076",
        ]

    # ── Number cleaning ──────────────────────────────────────
    def clean_number(self, number: str) -> str:
        n = re.sub(r"[\s\-\(\)\.]", "", number.strip())
        if n.startswith("0091"):
            n = "+91" + n[4:]
        elif n.startswith("91") and len(n) == 12 and not n.startswith("+"):
            n = "+91" + n[2:]
        return n

    # ── Number classification ────────────────────────────────
    def classify_number(self, number: str) -> dict:
        n = self.clean_number(number)

        # Toll-free / helpline
        if n in ["1930", "1800"] or n.startswith("1930") or n.startswith("1800"):
            label = "Cyber Crime Helpline (LEGITIMATE)" if "1930" in n else "Toll-Free"
            return {"type": "toll-free", "country": "India",
                    "location": label, "raw": n}

        # International
        if n.startswith("+1"):
            return {"type": "international", "country": "USA/Canada", "raw": n}
        if n.startswith("+44"):
            return {"type": "international", "country": "UK", "raw": n}
        if n.startswith("+92"):
            return {"type": "international", "country": "Pakistan", "raw": n}
        if n.startswith("+") and not n.startswith("+91"):
            return {"type": "international", "country": "Foreign", "raw": n}

        # Indian number
        local = n.replace("+91", "") if n.startswith("+91") else n

        # Indian mobile
        if re.match(r"^[6-9]\d{9}$", local):
            series  = local[:4]
            carrier = self._guess_carrier(local)
            circle  = self._guess_circle(local)
            scam    = series in self.known_scam_series
            return {
                "type"          : "mobile",
                "country"       : "India",
                "carrier"       : carrier,
                "circle"        : circle,
                "known_scam_series": scam,
                "raw"           : n,
            }

        # Indian landline — try STD codes longest first
        for code in ["0172", "0484", "011", "022", "080",
                     "033", "044", "040", "020"]:
            if local.startswith(code):
                location = self.std_codes.get(code, "Unknown")
                return {
                    "type"    : "landline",
                    "country" : "India",
                    "std_code": code,
                    "location": location,
                    "raw"     : n,
                }

        return {"type": "unknown", "country": "Unknown", "raw": n}

    def _guess_carrier(self, number: str) -> str:
        p = number[:4]
        mapping = {
            "9876": "Airtel", "9845": "Airtel", "9886": "Airtel",
            "9900": "Airtel", "9342": "Airtel", "9980": "Jio",
            "7019": "Jio",    "6364": "Jio",    "9448": "Vodafone",
            "9449": "Vodafone","9611": "BSNL",  "9480": "BSNL",
            "9958": "⚠️ Reported scam series",
            "8527": "⚠️ Reported scam series",
        }
        return mapping.get(p, "Unknown carrier")

    def _guess_circle(self, number: str) -> str:
        p = number[:2]
        mapping = {
            "98": "Delhi/NCR", "99": "Mumbai/MH",
            "96": "Karnataka", "97": "Tamil Nadu",
            "93": "West Bengal","94": "Gujarat",
            "70": "Rajasthan", "63": "Karnataka",
            "80": "Karnataka", "81": "Andhra Pradesh",
        }
        return mapping.get(p, "Unknown circle")

    # ── Main analysis ────────────────────────────────────────
    def analyze_caller(self, number: str, claimed_agency: str = None) -> dict:
        num_info   = self.classify_number(number)
        red_flags  = []
        risk_score = 0
        agency_info = None

        # 1. International number claiming to be Indian govt
        if num_info["type"] == "international" and claimed_agency:
            red_flags.append(
                f"CRITICAL: Caller claims to be Indian government but is calling "
                f"from {num_info['country']}. Indian agencies NEVER call internationally."
            )
            risk_score += 70

        # 2. Mobile number claiming to be govt agency
        if num_info["type"] == "mobile" and claimed_agency:
            red_flags.append(
                f"CRITICAL: Government agencies NEVER call from mobile numbers. "
                f"This is a {num_info.get('carrier','unknown')} mobile number."
            )
            risk_score += 50

        # 3. Known scam number series
        if num_info.get("known_scam_series"):
            red_flags.append(
                f"Number series {number[:6]}XXXX has been reported in "
                f"multiple scam complaints to cyber police."
            )
            risk_score += 30

        # 4. Agency-specific checks
        if claimed_agency:
            agency_key = None
            for key in self.agency_patterns:
                if key.lower() in claimed_agency.lower():
                    agency_key = key
                    break

            if agency_key:
                agency_info = self.agency_patterns[agency_key]

                if num_info["type"] == "landline":
                    std = num_info.get("std_code", "")
                    if std not in agency_info["valid_prefixes"]:
                        loc = num_info.get("location", "unknown location")
                        red_flags.append(
                            f"{agency_key} is located in {agency_info['hq_location']}. "
                            f"This number is from {loc} — location mismatch."
                        )
                        risk_score += 25

                if num_info["type"] == "toll-free" and "1930" in num_info.get("location",""):
                    risk_score = 0
                    red_flags  = []

        # 5. Unknown number type with govt claim
        if num_info["type"] == "unknown" and claimed_agency:
            red_flags.append("Could not verify number format. Treat with caution.")
            risk_score += 15

        risk_score = min(100, risk_score)

        # Verdict
        if "1930" in str(num_info.get("location", "")):
            verdict = "LEGITIMATE — Cyber Crime Helpline"
        elif risk_score >= 60:
            verdict = "SCAM LIKELY"
        elif risk_score >= 25:
            verdict = "SUSPICIOUS"
        elif num_info["type"] == "landline" and not red_flags:
            verdict = "POSSIBLY LEGITIMATE"
        else:
            verdict = "UNVERIFIED"

        result = {
            "timestamp"     : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "number"        : self.clean_number(number),
            "number_type"   : num_info,
            "claimed_agency": claimed_agency,
            "agency_fact"   : agency_info["fact"] if agency_info else None,
            "red_flags"     : red_flags,
            "risk_score"    : risk_score,
            "verdict"       : verdict,
            "alert"         : verdict in ["SCAM LIKELY", "SUSPICIOUS"],
        }

        if result["alert"]:
            self._log_alert(result)

        return result

    def _log_alert(self, result: dict):
        try:
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps({
                    k: v for k, v in result.items()
                    if k != "number_type"
                }) + "\n")
        except Exception as e:
            print(f"Log error: {e}")


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    analyzer = CallerAnalyzer()

    test_cases = [
        ("+91 9876543210", "CBI officer"),
        ("+91 9958123456", "ED office"),
        ("+1 4155552671",  "RBI investigation"),
        ("011-23384666",   "CBI"),
        ("+91 8527001234", "Supreme Court"),
        ("1930",           "Cyber Police"),
        ("+92 3001234567", "Income Tax"),
        ("080-22868000",   "Income Tax"),
    ]

    print("=" * 65)
    print("   SENTINEL-GUARD — Caller ID Analyzer Test")
    print("=" * 65)

    for number, agency in test_cases:
        result  = analyzer.analyze_caller(number, agency)
        verdict = result["verdict"]
        risk    = result["risk_score"]
        ntype   = result["number_type"]["type"]
        icon    = "🚨" if "SCAM" in verdict else "⚠️" if "SUSPICIOUS" in verdict else "✅"

        print(f"\n{icon} [{verdict}]")
        print(f"   Number  : {number} → Type: {ntype.upper()}")
        print(f"   Agency  : {agency} | Risk: {risk}/100")
        if result["red_flags"]:
            print(f"   🚩 {result['red_flags'][0][:75]}")
        if result["agency_fact"]:
            print(f"   ℹ️  {result['agency_fact'][:75]}")

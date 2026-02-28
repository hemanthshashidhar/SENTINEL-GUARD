# SENTINEL-GUARD Configuration

# ── English scam keywords ────────────────────────────────────
SCAM_KEYWORDS_EN = [
    "digital arrest", "cyber crime", "money laundering",
    "FIR registered", "do not tell anyone", "keep video on",
    "RBI investigation", "ED office", "CBI case",
    "arrest warrant", "your account is frozen", "immediate action",
    "transfer money", "verification fee", "legal notice",
    "narcotics", "don't disconnect", "stay on call",
    "CBI officer", "ED officer", "cyber cell officer",
    "officer speaking", "FIR registered", "transfer funds",
    "clear your name", "don't move", "stay on video",
    "you are arrested", "court order", "Supreme Court notice",
    "income tax raid", "customs department", "drug trafficking",
]

# ── Hindi scam keywords (transliterated + Devanagari) ────────
SCAM_KEYWORDS_HI = [
    # Transliterated
    "digital giraftari", "cyber crime vibhag", "hawala case",
    "FIR darj", "kisi ko mat batao", "video band mat karo",
    "RBI jaanch", "ED ka notice", "CBI adhikari",
    "giraftari warrant", "khata band ho gaya", "turant karwai",
    "paisa transfer karo", "verification shulk", "kanuni notice",
    "nasha", "call mat kaato", "online giraftari",
    "CBI officer bol raha hoon", "aapka naam case mein hai",
    "jail ho sakti hai", "abhi transfer karo", "court ka aadesh",
    "income tax vibhag", "customs adhikari",
    # Devanagari script
    "सीबीआई अधिकारी बोल रहा", "खाता फ्रीज", "डिजिटल गिरफ्तारी",
    "पैसे ट्रांसफर", "किसी को मत बताओ", "वीडियो बंद मत करो",
    "डिजिटल गिरफ्तारी", "साइबर क्राइम", "मनी लॉन्ड्रिंग",
    "एफआईआर दर्ज", "किसी को मत बताओ", "वीडियो बंद मत करो",
    "गिरफ्तारी वारंट", "पैसे ट्रांसफर करो", "कोर्ट का आदेश",
    "सीबीआई अधिकारी", "ईडी का नोटिस",
]

# ── Kannada scam keywords (transliterated + Kannada script) ──
SCAM_KEYWORDS_KN = [
    # Transliterated
    "digital badhavane", "cyber crime vibhaga", "havala prakarana",
    "FIR daakhalu maadidaare", "yaarigu helabedi", "video off maadabedi",
    "RBI tanikhee", "ED notice", "CBI adhikari maatanaadutha ide",
    "badhavane warrant", "nimma khate freeze aagide", "turant krama",
    "paisa transfer maadi", "verification shulka", "court aadesha",
    "nimma hesaru case nalli ide", "jail aagabahudu", "ibba transfer maadi",
    "income tax daadu", "customs adhikari", "call kattu maadabedi",
    "online badhavane", "nimma aadhar link aagide",
    # Kannada script
    "ಡಿಜಿಟಲ್ ಬಂಧನ", "ಸೈಬರ್ ಕ್ರೈಮ್", "ಮನಿ ಲಾಂಡರಿಂಗ್",
    "ಎಫ್ಐಆರ್ ದಾಖಲು", "ಯಾರಿಗೂ ಹೇಳಬೇಡಿ", "ವಿಡಿಯೋ ಬಂದ್ ಮಾಡಬೇಡಿ",
    "ಬಂಧನ ವಾರೆಂಟ್", "ಹಣ ವರ್ಗಾಯಿಸಿ", "ನ್ಯಾಯಾಲಯದ ಆದೇಶ",
    "ಸಿಬಿಐ ಅಧಿಕಾರಿ", "ಜೈಲು ಆಗಬಹುದು", "ತಕ್ಷಣ ಕ್ರಮ",
]

# ── Tamil scam keywords (transliterated + Tamil script) ──────
SCAM_KEYWORDS_TA = [
    # Transliterated
    "digital kavalai", "cyber crime thurai", "panam thulaiyal",
    "FIR podalanadu", "yarukkum sollathe", "video off pannaathe",
    "RBI vidan", "ED aanai", "CBI adigari pesugiren",
    "kaivalai aanai", "ungal account freeze aagividhu",
    "undan peyar case la irukku", "jail aagalaam", "ipave transfer pannu",
    "income tax thurai", "customs adigari", "call vetkathe",
    # Tamil script
    "டிஜிட்டல் கைது", "சைபர் க்ரைம்", "பண மோசடி",
    "எஃப்ஐஆர் பதிவு", "யாருக்கும் சொல்லாதே", "வீடியோ நிறுத்தாதே",
    "கைது வாரண்ட்", "பணம் அனுப்புங்கள்", "நீதிமன்ற உத்தரவு",
    "சிபிஐ அதிகாரி", "சிறை போகலாம்",
]

# ── Combined for backward compatibility ──────────────────────
SCAM_KEYWORDS = SCAM_KEYWORDS_EN + SCAM_KEYWORDS_HI + SCAM_KEYWORDS_KN + SCAM_KEYWORDS_TA

# ── Language map ─────────────────────────────────────────────
LANGUAGE_KEYWORDS = {
    "en": SCAM_KEYWORDS_EN,
    "hi": SCAM_KEYWORDS_HI,
    "kn": SCAM_KEYWORDS_KN,
    "ta": SCAM_KEYWORDS_TA,
}

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "unknown": "Unknown",
}

# ── Scam regex patterns (English + Hindi transliterated) ─────
SCAM_PATTERNS = [
    # English
    r"don.t (tell|inform|contact)",
    r"keep (video|camera) on",
    r"(transfer|send).{0,20}(money|amount|funds|rupees|paisa)",
    r"(arrest|warrant|FIR).{0,20}(your name|registered|darj)",
    r"(CBI|ED|RBI|cyber cell).{0,20}(officer|investigation|adhikari)",
    r"do not (hang|disconnect|cut|kaato)",
    r"(jail|prison).{0,15}(ho sakti|aagabahudu|aagalaam|jayil)",
    # Hindi transliterated
    r"kisi ko mat bata",
    r"paisa.{0,10}transfer",
    r"giraftari.{0,20}(warrant|hogi)",
    # Kannada transliterated
    r"yaarigu.{0,10}helabedi",
    r"paisa.{0,10}(transfer|kodi)",
    r"badhavane.{0,20}warrant",
]

# ── Alert thresholds ─────────────────────────────────────────
SCAM_KEYWORD_THRESHOLD  = 2
VOICE_ANOMALY_THRESHOLD = 0.6
VIDEO_DEEPFAKE_THRESHOLD = 0.5

# ── Paths ────────────────────────────────────────────────────
LOG_PATH    = "logs/alerts.json"
ASSETS_PATH = "assets/"

# ── App ──────────────────────────────────────────────────────
APP_NAME = "SENTINEL-GUARD"
VERSION  = "1.0.0"
SUPPORTED_LANGUAGES = ["English", "Hindi", "Kannada", "Tamil"]

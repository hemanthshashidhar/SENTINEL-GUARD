# SENTINEL-GUARD Configuration

# Scam keywords and phrases (digital arrest patterns)
SCAM_KEYWORDS = [
    "CBI officer", "ED officer", "cyber cell officer",
    "officer speaking", "FIR registered", "transfer funds",
    "clear your name", "don't move", "stay on video",
    "digital arrest", "cyber crime", "money laundering",
    "FIR registered", "do not tell anyone", "keep video on",
    "RBI investigation", "ED office", "CBI case",
    "arrest warrant", "your account is frozen", "immediate action",
    "transfer money", "verification fee", "legal notice",
    "narcotics", "don't disconnect", "stay on call"
]

# Alert thresholds
SCAM_KEYWORD_THRESHOLD = 2      # how many keywords before alert
VOICE_ANOMALY_THRESHOLD = 0.6   # confidence score for AI voice detection
VIDEO_DEEPFAKE_THRESHOLD = 0.5  # confidence for deepfake frame

# Paths
LOG_PATH = "logs/alerts.json"
ASSETS_PATH = "assets/"

# App settings
APP_NAME = "SENTINEL-GUARD"
VERSION = "1.0.0"

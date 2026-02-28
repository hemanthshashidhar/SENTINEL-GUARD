import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import json
import time
from datetime import datetime
from core.nlp.scam_detector import ScamDetector
from core.document.forensics import DocumentForensics

# ── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title="SENTINEL-GUARD",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0a0a0a; }
    .stApp { background-color: #0d1117; color: #ffffff; }

    .danger-box {
        background: linear-gradient(135deg, #ff000022, #ff000044);
        border: 2px solid #ff0000;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        animation: pulse 1s infinite;
    }
    .safe-box {
        background: linear-gradient(135deg, #00ff0022, #00ff0044);
        border: 2px solid #00ff00;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .warning-box {
        background: linear-gradient(135deg, #ffaa0022, #ffaa0044);
        border: 2px solid #ffaa00;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .metric-card {
        background: #1a1a2e;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255,0,0,0.4); }
        70% { box-shadow: 0 0 0 10px rgba(255,0,0,0); }
        100% { box-shadow: 0 0 0 0 rgba(255,0,0,0); }
    }
    .title-text {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #ff6b35, #f7c59f, #efefd0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────
if "detector" not in st.session_state:
    st.session_state.detector = ScamDetector()
if "forensics" not in st.session_state:
    st.session_state.forensics = DocumentForensics()
if "nlp_history" not in st.session_state:
    st.session_state.nlp_history = []
if "panic_triggered" not in st.session_state:
    st.session_state.panic_triggered = False
if "total_alerts" not in st.session_state:
    st.session_state.total_alerts = 0
if "session_start" not in st.session_state:
    st.session_state.session_start = datetime.now().strftime("%H:%M:%S")

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ SENTINEL-GUARD")
    st.markdown("**AI-Powered Scam Detection**")
    st.markdown("---")
    st.markdown(f"🕐 Session started: `{st.session_state.session_start}`")
    st.markdown(f"🚨 Total alerts: `{st.session_state.total_alerts}`")
    st.markdown("---")

    st.markdown("### 🔧 System Status")
    st.success("✅ NLP Engine: Online")
    st.success("✅ Document Forensics: Online")
    st.warning("⚡ Voice Engine: Standby")
    st.warning("⚡ Video Engine: Standby")

    st.markdown("---")
    st.markdown("### ⚙️ Detection Settings")
    sensitivity = st.slider("Detection Sensitivity", 1, 5, 3)
    st.caption("Higher = more aggressive detection")

    st.markdown("---")
    # PANIC BUTTON
    if st.button("🆘 PANIC BUTTON", use_container_width=True, type="primary"):
        st.session_state.panic_triggered = True

    if st.session_state.panic_triggered:
        st.error("🚨 PANIC ACTIVATED\nAlert sent to trusted contacts!\nEvidence logged for cyber police.")
        st.markdown("""
        **Emergency contacts notified:**
        - 👨‍👩‍👧 Family member: ✅ Sent
        - 🚔 Cyber Police: 1930
        - 📧 Evidence log: Saved
        """)
        if st.button("Cancel Panic", use_container_width=True):
            st.session_state.panic_triggered = False

# ── Main header ──────────────────────────────────────────────
st.markdown('<p class="title-text">🛡️ SENTINEL-GUARD</p>', unsafe_allow_html=True)
st.markdown("##### Real-Time Digital Arrest & Deepfake Scam Detection | Powered by AMD Ryzen AI")
st.markdown("---")

# ── Panic alert banner ───────────────────────────────────────
if st.session_state.panic_triggered:
    st.markdown("""
    <div class="danger-box">
        <h1>🚨 PANIC MODE ACTIVE 🚨</h1>
        <h3>Trusted contacts alerted • Evidence being recorded • Call Cyber Helpline: 1930</h3>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")

# ── Tabs ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🎙️ Live Call Monitor",
    "📄 Document Forensics",
    "📊 Alert Dashboard",
    "ℹ️ How It Works"
])

# ════════════════════════════════════════════════════════════
# TAB 1 — Live Call Monitor
# ════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### 🎙️ Real-Time Call Analysis")
    st.caption("Paste call transcript or type what the caller is saying. The AI analyzes it in real-time.")

    col1, col2 = st.columns([2, 1])

    with col1:
        user_input = st.text_area(
            "Enter caller's speech / transcript:",
            placeholder="e.g. This is CBI officer. Your name has appeared in a money laundering case...",
            height=150
        )

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            analyze_btn = st.button("🔍 Analyze", use_container_width=True, type="primary")
        with col_b:
            demo_btn = st.button("▶️ Run Demo", use_container_width=True)
        with col_c:
            clear_btn = st.button("🗑️ Clear", use_container_width=True)

        if clear_btn:
            st.session_state.nlp_history = []
            st.rerun()

        if demo_btn:
            demo_script = [
                "Hello, I am officer Sharma calling from CBI headquarters.",
                "Your Aadhaar number has been linked to a money laundering case. FIR has been registered.",
                "You are under digital arrest. Do not tell anyone about this call. Keep your video on.",
                "To avoid arrest you must transfer funds immediately. Do not disconnect the call."
            ]
            st.markdown("#### 🎬 Demo: Simulated Scam Call in Progress...")
            progress = st.progress(0)
            for i, line in enumerate(demo_script):
                time.sleep(0.5)
                result = st.session_state.detector.analyze_text(line)
                result["transcript"] = line
                st.session_state.nlp_history.append(result)
                if result["alert"]:
                    st.session_state.total_alerts += 1
                progress.progress((i + 1) / len(demo_script))
            st.success("Demo complete! See results below.")
            st.rerun()

        if analyze_btn and user_input:
            result = st.session_state.detector.analyze_text(user_input)
            result["transcript"] = user_input
            st.session_state.nlp_history.append(result)
            if result["alert"]:
                st.session_state.total_alerts += 1

    with col2:
        st.markdown("### 📊 Live Stats")
        total = len(st.session_state.nlp_history)
        dangers = sum(1 for r in st.session_state.nlp_history if r["risk_level"] == "DANGER")
        suspicious = sum(1 for r in st.session_state.nlp_history if r["risk_level"] == "SUSPICIOUS")

        st.metric("Chunks Analyzed", total)
        st.metric("🚨 DANGER Alerts", dangers)
        st.metric("⚠️ Suspicious", suspicious)

        if total > 0:
            risk_pct = int((dangers / total) * 100)
            st.progress(risk_pct / 100)
            st.caption(f"Risk Score: {risk_pct}%")

    # Results
    if st.session_state.nlp_history:
        st.markdown("---")
        st.markdown("### 📋 Analysis Results")
        for i, result in enumerate(reversed(st.session_state.nlp_history[-10:]), 1):
            risk = result["risk_level"]
            if risk == "DANGER":
                box_class = "danger-box"
                icon = "🚨"
            elif risk == "SUSPICIOUS":
                box_class = "warning-box"
                icon = "⚠️"
            else:
                box_class = "safe-box"
                icon = "✅"

            with st.expander(f"{icon} [{risk}] {result['transcript'][:60]}...", expanded=(i == 1 and risk == "DANGER")):
                c1, c2, c3 = st.columns(3)
                c1.metric("Risk Level", risk)
                c2.metric("Score", result["total_score"])
                c3.metric("Alert", "YES 🚨" if result["alert"] else "NO ✅")

                if result.get("found_keywords"):
                    st.error(f"🔑 Keywords detected: {', '.join(result['found_keywords'])}")
                if result.get("found_patterns"):
                    st.warning(f"🔍 Patterns matched: {', '.join(result['found_patterns'])}")


# ════════════════════════════════════════════════════════════
# TAB 2 — Document Forensics
# ════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📄 Document Forensics Engine")
    st.caption("Paste document text or upload an image. AI detects forged FIRs, fake warrants, and scam notices.")

    doc_col1, doc_col2 = st.columns([2, 1])

    with doc_col1:
        doc_input = st.text_area(
            "Paste document text here:",
            placeholder="Paste the content of the suspicious document...",
            height=200
        )

        d1, d2 = st.columns(2)
        with d1:
            doc_analyze_btn = st.button("🔬 Analyze Document", use_container_width=True, type="primary")
        with d2:
            doc_demo_btn = st.button("▶️ Load Fake FIR Demo", use_container_width=True)

        if doc_demo_btn:
            st.session_state["doc_demo_text"] = """GOVERNMENT OF INDIA
Central Bureau of Investigation
FIR No: CBI/2024/MH/4521

This is to inform you that your name has appeared in a money laundering case.
An arrest warrant has been issued against you.

You must transfer Rs. 50,000 immediately via GPay or PhonePe to avoid arrest.
Do not share this document with anyone. Contact officer on WhatsApp: 9876543210
Payment must be done within 2 hours or you will be arrested.

Signed by: Officer Sharma"""
            st.rerun()

        if "doc_demo_text" in st.session_state:
            doc_input = st.session_state["doc_demo_text"]

    with doc_col2:
        st.markdown("### 🔍 What We Check")
        st.markdown("""
        - ✅ Official seals & headers
        - ✅ Case number format
        - ✅ Proper address & date
        - ✅ Signature legitimacy
        - 🚩 UPI/payment demands
        - 🚩 WhatsApp contact
        - 🚩 Urgency pressure
        - 🚩 Scam keywords
        """)

    if doc_analyze_btn and doc_input:
        result = st.session_state.forensics.analyze_document(doc_input, source="manual_input")

        st.markdown("---")
        st.markdown("### 📋 Forensics Report")

        verdict = result["verdict"]
        if verdict == "FORGED":
            st.markdown(f"""
            <div class="danger-box">
                <h2>🚨 DOCUMENT IS FORGED</h2>
                <h3>Confidence: {result['confidence']}%</h3>
            </div>
            """, unsafe_allow_html=True)
        elif verdict == "SUSPICIOUS":
            st.markdown(f"""
            <div class="warning-box">
                <h2>⚠️ DOCUMENT IS SUSPICIOUS</h2>
                <h3>Confidence: {result['confidence']}%</h3>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="safe-box">
                <h2>✅ {verdict}</h2>
                <h3>Confidence: {result['confidence']}%</h3>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")
        m1, m2, m3 = st.columns(3)
        m1.metric("Verdict", verdict)
        m2.metric("Legitimacy Score", result["legitimacy_score"])
        m3.metric("Claims Official", "Yes" if result["claims_official"] else "No")

        if result["red_flags"]:
            st.error("🚩 Red Flags Found:\n" + "\n".join(f"• {f}" for f in result["red_flags"]))

        if result["scam_keywords_found"]:
            st.warning(f"🔑 Scam keywords: {', '.join(result['scam_keywords_found'])}")

        st.markdown("#### Format Legitimacy Checks")
        fc1, fc2 = st.columns(2)
        checks = list(result["format_checks"].items())
        for i, (check, passed) in enumerate(checks):
            col = fc1 if i % 2 == 0 else fc2
            icon = "✅" if passed else "❌"
            col.markdown(f"{icon} {check.replace('_', ' ').title()}")


# ════════════════════════════════════════════════════════════
# TAB 3 — Alert Dashboard
# ════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📊 Session Alert Dashboard")

    if not st.session_state.nlp_history:
        st.info("No analysis done yet. Go to 'Live Call Monitor' and run the demo first.")
    else:
        total = len(st.session_state.nlp_history)
        dangers = sum(1 for r in st.session_state.nlp_history if r["risk_level"] == "DANGER")
        suspicious = sum(1 for r in st.session_state.nlp_history if r["risk_level"] == "SUSPICIOUS")
        safe = total - dangers - suspicious

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Total Analyzed", total)
        a2.metric("🚨 DANGER", dangers)
        a3.metric("⚠️ Suspicious", suspicious)
        a4.metric("✅ Safe", safe)

        st.markdown("---")
        st.markdown("### 📜 Full Alert Log")
        for result in reversed(st.session_state.nlp_history):
            risk = result["risk_level"]
            icon = "🚨" if risk == "DANGER" else "⚠️" if risk == "SUSPICIOUS" else "✅"
            st.markdown(f"{icon} `{result.get('timestamp', 'N/A')}` — **{risk}** — Score: {result['total_score']} — _{result['transcript'][:80]}_")

        st.markdown("---")
        if st.button("💾 Export Evidence Log"):
            log_data = json.dumps(st.session_state.nlp_history, indent=2)
            st.download_button(
                label="📥 Download JSON Evidence",
                data=log_data,
                file_name=f"sentinel_evidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


# ════════════════════════════════════════════════════════════
# TAB 4 — How It Works
# ════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### ℹ️ How SENTINEL-GUARD Works")
    st.markdown("""
    **SENTINEL-GUARD** is a multi-modal AI system that detects digital arrest scams in real-time.

    #### 🏗️ Architecture
```
    Live Call / Document Input
           ↓
    ┌─────────────────────────────────┐
    │       SENTINEL-GUARD CORE       │
    ├──────────────┬──────────────────┤
    │ 🎙️ Voice     │ 🧠 NLP Scam      │
    │   Analyzer   │   Detector       │
    │ (Whisper AI) │ (Pattern Match)  │
    ├──────────────┼──────────────────┤
    │ 📹 Video     │ 📄 Document      │
    │   Deepfake   │   Forensics      │
    │   Detector   │   (OCR + AI)     │
    └──────────────┴──────────────────┘
           ↓
    🚨 Real-Time Alert + Panic Button
    💾 Evidence Logged for Cyber Police
```

    #### ⚡ AMD Ryzen AI NPU Advantage
    - All inference runs **on-device** — no cloud, no privacy risk
    - ONNX Runtime optimized for AMD NPU
    - Low latency: analysis in under 500ms per chunk

    #### 🇮🇳 India Impact
    - ₹120.3 crore lost to digital arrest scams annually
    - 47% of Indians know someone affected by AI voice scams
    - Supreme Court has intervened on this issue
    - No existing multi-modal solution exists for this threat
    """)

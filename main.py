import sys
import os
import subprocess
import threading
import time
import webbrowser

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗  ║
║   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝  ║
║   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗    ║
║   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝    ║
║   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗  ║
║   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝  ║
║                                                              ║
║          ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗           ║
║         ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗          ║
║         ██║  ███╗██║   ██║███████║██████╔╝██║  ██║          ║
║         ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║          ║
║         ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝          ║
║          ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝           ║
║                                                              ║
║     AI-Powered Digital Arrest & Deepfake Detection          ║
║     Powered by AMD Ryzen AI NPU  |  Version 1.0.0           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_dependencies():
    print("[*] Checking dependencies...")
    required = [
        "streamlit",
        "faster_whisper",
        "cv2",
        "transformers",
        "pytesseract",
        "sounddevice",
        "numpy",
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"[!] Missing packages: {', '.join(missing)}")
        print("[!] Run: pip install -r requirements.txt")
        return False

    print("[✓] All dependencies found.")
    return True

def run_engine_tests():
    print("\n[*] Running engine self-tests...")

    # Test NLP
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from core.nlp.scam_detector import ScamDetector
        d = ScamDetector()
        r = d.analyze_text("You are under digital arrest. Do not tell anyone.")
        assert r["risk_level"] == "DANGER"
        print("[✓] NLP Scam Detector     — ONLINE")
    except Exception as e:
        print(f"[✗] NLP Scam Detector     — FAILED: {e}")

    # Test Document Forensics
    try:
        from core.document.forensics import DocumentForensics
        f = DocumentForensics()
        r = f.analyze_document("Transfer money via GPay. Do not share. WhatsApp: 9876543210")
        assert r["alert"] == True
        print("[✓] Document Forensics    — ONLINE")
    except Exception as e:
        print(f"[✗] Document Forensics    — FAILED: {e}")

    # Test Video
    try:
        from core.video.deepfake import DeepfakeDetector
        print("[✓] Video Deepfake Engine — ONLINE")
    except Exception as e:
        print(f"[✗] Video Deepfake Engine — FAILED: {e}")

    # Test Voice
    try:
        from faster_whisper import WhisperModel
        print("[✓] Voice/Whisper Engine  — ONLINE")
    except Exception as e:
        print(f"[✗] Voice/Whisper Engine  — FAILED: {e}")

def ensure_logs():
    os.makedirs("logs", exist_ok=True)
    log_path = "logs/alerts.json"
    if not os.path.exists(log_path):
        open(log_path, "w").close()
    print("[✓] Log directory ready.")

def launch_dashboard():
    print("\n[*] Launching SENTINEL-GUARD dashboard...")
    print("[*] Opening browser at http://localhost:8501")
    print("[*] Press Ctrl+C to stop.\n")

    # Open browser after short delay
    def open_browser():
        time.sleep(3)
        webbrowser.open("http://localhost:8501")

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Launch streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "ui/dashboard.py",
        "--server.port=8501",
        "--server.headless=false",
        "--browser.gatherUsageStats=false",
        "--theme.base=dark",
        "--theme.primaryColor=#3b82f6",
        "--theme.backgroundColor=#030712",
        "--theme.secondaryBackgroundColor=#0d1b2a",
        "--theme.textColor=#e2e8f0",
    ])

def launch_video_only():
    print("\n[*] Launching Video Deepfake Detector only...")
    print("[*] Press Q in the window to quit.\n")
    subprocess.run([sys.executable, "-m", "core.video.deepfake"])

def main():
    print_banner()

    print("=" * 65)
    print("  SELECT MODE")
    print("=" * 65)
    print("  1. Launch Full Dashboard (Recommended)")
    print("  2. Launch Video Deepfake Detector only")
    print("  3. Run engine self-tests")
    print("  4. Exit")
    print("=" * 65)

    choice = input("\n  Enter choice (1-4): ").strip()

    if choice == "1":
        if not check_dependencies():
            sys.exit(1)
        ensure_logs()
        run_engine_tests()
        launch_dashboard()

    elif choice == "2":
        launch_video_only()

    elif choice == "3":
        check_dependencies()
        run_engine_tests()
        input("\nPress Enter to exit...")

    elif choice == "4":
        print("\n[✓] Goodbye.\n")
        sys.exit(0)

    else:
        print("[!] Invalid choice.")
        main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[✓] SENTINEL-GUARD stopped. Goodbye.\n")

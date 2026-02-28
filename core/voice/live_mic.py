import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import wave
import time
import tempfile
import threading
import numpy as np
import sounddevice as sd
from datetime import datetime
from faster_whisper import WhisperModel
from core.nlp.scam_detector import ScamDetector
from config import LOG_PATH

class LiveMicDetector:
    def __init__(self, callback=None):
        """
        callback: function called with result dict after each chunk analysis.
                  Used by dashboard to update UI in real-time.
        """
        print("[*] Loading Whisper model (base)...")
        self.model        = WhisperModel("base", device="cpu", compute_type="int8")
        self.detector     = ScamDetector()
        self.callback     = callback
        self.is_running   = False
        self.sample_rate  = 16000
        self.chunk_secs   = 5        # analyze every 5 seconds
        self.results      = []
        print("[✓] Live Mic Detector ready.")

    # ── Audio helpers ────────────────────────────────────────
    def _record_chunk(self) -> np.ndarray:
        frames = int(self.sample_rate * self.chunk_secs)
        audio  = sd.rec(frames, samplerate=self.sample_rate,
                        channels=1, dtype="float32")
        sd.wait()
        return audio.flatten()

    def _save_wav(self, audio: np.ndarray) -> str:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes((audio * 32767).astype(np.int16).tobytes())
        return tmp.name

    def _transcribe(self, wav_path: str) -> str:
        segments, _ = self.model.transcribe(wav_path, beam_size=5)
        return " ".join(seg.text for seg in segments).strip()

    # ── Single chunk pipeline ────────────────────────────────
    def process_chunk(self, audio: np.ndarray) -> dict:
        wav  = self._save_wav(audio)
        text = self._transcribe(wav)
        os.unlink(wav)

        if not text:
            return {
                "transcript" : "",
                "risk_level" : "SAFE",
                "total_score": 0,
                "alert"      : False,
                "found_keywords": [],
                "found_patterns": [],
                "timestamp"  : datetime.now().strftime("%H:%M:%S"),
            }

        result              = self.detector.analyze_text(text)
        result["transcript"] = text
        result["timestamp"]  = datetime.now().strftime("%H:%M:%S")
        self.results.append(result)

        # Fire callback for live UI updates
        if self.callback:
            self.callback(result)

        return result

    # ── Main loop ────────────────────────────────────────────
    def start(self):
        self.is_running = True
        print("\n[🎙️] Listening... Press Ctrl+C to stop.\n")
        try:
            while self.is_running:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Recording chunk...")
                audio  = self._record_chunk()
                result = self.process_chunk(audio)

                if not result["transcript"]:
                    print("  [~] No speech detected.\n")
                    continue

                rl = result["risk_level"]
                print(f"  Transcript : {result['transcript']}")
                print(f"  Risk Level : {rl}")
                print(f"  Score      : {result['total_score']}")
                if result["alert"]:
                    print("  ⚠️  🚨 SCAM DETECTED 🚨 ⚠️")
                print()

        except KeyboardInterrupt:
            self.is_running = False
            print("\n[✓] Monitoring stopped.")
            print(self.detector.get_risk_summary(self.results))

    def stop(self):
        self.is_running = False

    # ── Background thread version (for dashboard) ────────────
    def start_background(self):
        self.thread = threading.Thread(target=self.start, daemon=True)
        self.thread.start()


# ── Standalone test ──────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("   SENTINEL-GUARD — Live Mic Detector")
    print("=" * 60)
    print("\n1. Live microphone")
    print("2. Simulate scam call (no mic needed)")
    choice = input("\nChoice: ").strip()

    if choice == "1":
        mic = LiveMicDetector()
        mic.start()
    else:
        print("\n[*] Simulating real-time scam call detection...\n")
        mic = LiveMicDetector()

        scam_call = [
            "Hello is this you? I am calling from CBI headquarters.",
            "Your Aadhaar number is linked to a money laundering case.",
            "You are under digital arrest. Do not tell anyone.",
            "Keep your video on. Do not disconnect this call.",
            "Transfer fifty thousand rupees immediately to clear your name.",
        ]

        print("=" * 60)
        for i, line in enumerate(scam_call, 1):
            print(f"\n[Chunk {i} — {datetime.now().strftime('%H:%M:%S')}]")
            print(f"  🎙️  Transcribed: \"{line}\"")
            result = mic.detector.analyze_text(line)
            rl     = result["risk_level"]
            color  = "🔴" if rl=="DANGER" else "🟡" if rl=="SUSPICIOUS" else "🟢"
            print(f"  {color} Risk: {rl} | Score: {result['total_score']}")
            if result["found_keywords"]:
                print(f"  🔑 Keywords: {', '.join(result['found_keywords'])}")
            if result["alert"]:
                print("  🚨 ═══ SCAM ALERT TRIGGERED ═══ 🚨")
            time.sleep(0.4)

        print("\n" + "=" * 60)
        print(mic.detector.get_risk_summary(
            [mic.detector.analyze_text(l) for l in scam_call]
        ))

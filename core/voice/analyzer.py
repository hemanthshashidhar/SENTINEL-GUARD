import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import wave
import json
import threading
import tempfile
import numpy as np
import sounddevice as sd
from datetime import datetime
from faster_whisper import WhisperModel
from core.nlp.scam_detector import ScamDetector
from config import LOG_PATH

class VoiceAnalyzer:
    def __init__(self):
        print("[*] Loading Whisper model... (first time takes 1-2 mins)")
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        self.detector = ScamDetector()
        self.is_recording = False
        self.sample_rate = 16000
        self.chunk_duration = 5      # analyze every 5 seconds
        self.results = []
        print("[✓] Voice Analyzer ready.")

    def _record_chunk(self) -> np.ndarray:
        """Record a chunk of audio from microphone."""
        frames = int(self.sample_rate * self.chunk_duration)
        audio = sd.rec(frames, samplerate=self.sample_rate, channels=1, dtype='float32')
        sd.wait()
        return audio.flatten()

    def _save_temp_wav(self, audio: np.ndarray) -> str:
        """Save numpy audio array to a temp WAV file for Whisper."""
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes((audio * 32767).astype(np.int16).tobytes())
        return tmp.name

    def analyze_chunk(self, audio: np.ndarray) -> dict:
        """Transcribe audio and run scam detection."""
        wav_path = self._save_temp_wav(audio)

        # Transcribe with Whisper
        segments, _ = self.model.transcribe(wav_path, beam_size=5)
        transcript = " ".join([seg.text for seg in segments]).strip()

        os.unlink(wav_path)  # clean up temp file

        if not transcript:
            return {"transcript": "", "risk_level": "SAFE", "alert": False}

        # Run through NLP scam detector
        result = self.detector.analyze_text(transcript)
        result["transcript"] = transcript
        self.results.append(result)

        return result

    def start_live_monitoring(self):
        """Start real-time voice monitoring loop."""
        self.is_recording = True
        print("\n[🎙️] Live monitoring started. Speak or play audio...")
        print("[*] Press Ctrl+C to stop.\n")

        try:
            while self.is_recording:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Listening...")
                audio = self._record_chunk()
                result = self.analyze_chunk(audio)

                if result["transcript"]:
                    print(f"  Transcript  : {result['transcript']}")
                    print(f"  Risk Level  : {result['risk_level']}")
                    if result["alert"]:
                        print("  ⚠️  🚨 SCAM DETECTED — TRIGGERING ALERT 🚨 ⚠️")
                    print()

        except KeyboardInterrupt:
            self.is_recording = False
            print("\n[✓] Monitoring stopped.")
            print(self.detector.get_risk_summary(self.results))

    def analyze_audio_file(self, file_path: str) -> dict:
        """Analyze a pre-recorded audio file (useful for demo)."""
        print(f"[*] Analyzing file: {file_path}")
        segments, _ = self.model.transcribe(file_path, beam_size=5)
        transcript = " ".join([seg.text for seg in segments]).strip()

        if not transcript:
            return {"transcript": "", "risk_level": "SAFE", "alert": False}

        result = self.detector.analyze_text(transcript)
        result["transcript"] = transcript
        return result


# ── Quick test ──────────────────────────────────────────────
if __name__ == "__main__":
    analyzer = VoiceAnalyzer()

    print("\n" + "=" * 60)
    print("       SENTINEL-GUARD — Voice Analyzer Test")
    print("=" * 60)
    print("\nChoose test mode:")
    print("  1. Live microphone monitoring")
    print("  2. Test with simulated transcript")
    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        analyzer.start_live_monitoring()
    else:
        # Simulate what whisper would transcribe from a scam call
        print("\n[*] Simulating scam call transcript...\n")
        fake_transcripts = [
            "Hello this is officer Sharma from CBI",
            "Your name has appeared in a money laundering case FIR has been registered",
            "You are under digital arrest do not tell anyone keep your video on",
            "You must transfer funds immediately to clear your name from this case"
        ]

        for i, text in enumerate(fake_transcripts, 1):
            print(f"[Chunk {i}] Transcribed: '{text}'")
            result = analyzer.detector.analyze_text(text)
            print(f"  Risk: {result['risk_level']} | Score: {result['total_score']} | Alert: {'🚨' if result['alert'] else '✅'}")
            print()

        print(analyzer.detector.get_risk_summary(analyzer.results))

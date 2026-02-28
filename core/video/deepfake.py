import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import cv2
import time
import json
import numpy as np
from datetime import datetime
from collections import deque
from config import LOG_PATH

class DeepfakeDetector:
    def __init__(self):
        print("[*] Loading Deepfake Detector (OpenCV)...")

        # Load OpenCV's built-in face + eye detectors
        cascade_base = cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(cascade_base + "haarcascade_frontalface_default.xml")
        self.eye_cascade  = cv2.CascadeClassifier(cascade_base + "haarcascade_eye.xml")

        if self.face_cascade.empty() or self.eye_cascade.empty():
            raise RuntimeError("Could not load cascade classifiers.")

        # History buffers
        self.ear_history        = deque(maxlen=60)
        self.texture_history    = deque(maxlen=30)
        self.movement_history   = deque(maxlen=60)
        self.symmetry_history   = deque(maxlen=30)
        self.lighting_history   = deque(maxlen=30)

        # Blink tracking
        self.blink_count        = 0
        self.eyes_closed_frames = 0
        self.BLINK_THRESHOLD    = 3
        self.prev_eyes_detected = True

        # Frame tracking
        self.frame_count        = 0
        self.analysis_start     = time.time()
        self.prev_gray          = None
        self.prev_face_rect     = None

        # Risk
        self.risk_scores        = deque(maxlen=30)
        self.last_alert_time    = 0

        print("[✓] Deepfake Detector ready.")

    # ── Texture Score (Laplacian variance) ───────────────────
    def _texture_score(self, face_roi):
        """Low variance = over-smoothed = deepfake artifact."""
        try:
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            # Normalize: lower variance = higher artifact score
            score = max(0.0, 1.0 - (lap_var / 600.0))
            return round(float(score), 3)
        except:
            return 0.0

    # ── Lighting Asymmetry ───────────────────────────────────
    def _lighting_asymmetry(self, face_roi):
        """Real faces have roughly symmetric lighting. Deepfakes often don't."""
        try:
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            left_mean  = np.mean(gray[:, :w//2])
            right_mean = np.mean(gray[:, w//2:])
            asymmetry  = abs(left_mean - right_mean) / 255.0
            return round(float(asymmetry), 3)
        except:
            return 0.0

    # ── Face Symmetry ────────────────────────────────────────
    def _face_symmetry(self, face_roi):
        """Real faces are naturally symmetric. Deepfake blending breaks symmetry."""
        try:
            gray    = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            flipped = cv2.flip(gray, 1)
            diff    = cv2.absdiff(gray, flipped)
            score   = np.mean(diff) / 255.0
            # Higher diff = more asymmetric = more suspicious
            return round(float(score), 3)
        except:
            return 0.0

    # ── Optical Flow Movement ────────────────────────────────
    def _movement_score(self, gray, face_rect):
        """Measure natural micro-movements. Deepfakes are unnaturally still."""
        try:
            x, y, w, h = face_rect
            face_gray = gray[y:y+h, x:x+w]
            face_gray = cv2.resize(face_gray, (100, 100))

            if self.prev_gray is None:
                self.prev_gray = face_gray
                return 1.0

            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray, face_gray,
                None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
            self.prev_gray = face_gray
            return round(float(np.mean(magnitude)), 3)
        except:
            return 1.0

    # ── Blink Detection ──────────────────────────────────────
    def _detect_blink(self, face_roi):
        """Detect eyes using cascade. Missing eyes = possible blink."""
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 5, minSize=(20, 20))
        eyes_detected = len(eyes) >= 2

        if not eyes_detected:
            self.eyes_closed_frames += 1
        else:
            if self.eyes_closed_frames >= self.BLINK_THRESHOLD:
                self.blink_count += 1
            self.eyes_closed_frames = 0

        return eyes_detected, len(eyes)

    # ── Main Frame Analysis ──────────────────────────────────
    def analyze_frame(self, frame):
        self.frame_count += 1
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        analysis = {
            "face_detected"     : False,
            "blink_count"       : self.blink_count,
            "blink_rate"        : 0.0,
            "texture_score"     : 0.0,
            "lighting_asymmetry": 0.0,
            "face_symmetry"     : 0.0,
            "movement_score"    : 0.0,
            "risk_score"        : 0.0,
            "risk_level"        : "ANALYZING...",
            "flags"             : [],
        }

        # Detect face
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(120, 120)
        )

        if len(faces) == 0:
            frame = self._draw_no_face(frame)
            return frame, analysis

        # Use largest face
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
        face_roi  = frame[y:y+fh, x:x+fw]
        analysis["face_detected"] = True

        # Run all checks
        texture     = self._texture_score(face_roi)
        lighting    = self._lighting_asymmetry(face_roi)
        symmetry    = self._face_symmetry(face_roi)
        movement    = self._movement_score(gray, (x, y, fw, fh))
        eyes_open, eye_count = self._detect_blink(face_roi)

        self.texture_history.append(texture)
        self.lighting_history.append(lighting)
        self.symmetry_history.append(symmetry)
        self.movement_history.append(movement)

        elapsed     = max(1, time.time() - self.analysis_start)
        blink_rate  = (self.blink_count / elapsed) * 60

        analysis.update({
            "blink_rate"        : round(blink_rate, 1),
            "texture_score"     : texture,
            "lighting_asymmetry": lighting,
            "face_symmetry"     : symmetry,
            "movement_score"    : round(movement, 3),
        })

        # ── Risk Calculation ─────────────────────────────────
        risk  = 0.0
        flags = []

        # 1. Blink rate (normal 12-20/min, need 15s to judge)
        if elapsed > 15:
            if blink_rate < 4:
                risk += 30
                flags.append(f"Abnormal blink rate: {blink_rate:.1f}/min")
            elif blink_rate > 45:
                risk += 15
                flags.append(f"High blink rate: {blink_rate:.1f}/min")

        # 2. Texture smoothing
        avg_texture = np.mean(list(self.texture_history)) if self.texture_history else 0
        if avg_texture > 0.55:
            risk += 25
            flags.append(f"Face over-smoothing: {avg_texture:.2f}")

        # 3. Lighting asymmetry
        avg_lighting = np.mean(list(self.lighting_history)) if self.lighting_history else 0
        if avg_lighting > 0.25:
            risk += 20
            flags.append(f"Lighting inconsistency: {avg_lighting:.2f}")

        # 4. Face asymmetry
        avg_symmetry = np.mean(list(self.symmetry_history)) if self.symmetry_history else 0
        if avg_symmetry > 0.18:
            risk += 15
            flags.append(f"Face asymmetry detected: {avg_symmetry:.2f}")

        # 5. Unnatural stillness
        avg_movement = np.mean(list(self.movement_history)) if self.movement_history else 1
        if elapsed > 15 and avg_movement < 0.15:
            risk += 15
            flags.append(f"Unnatural stillness: {avg_movement:.3f}")

        analysis["risk_score"] = min(100, round(risk, 1))
        analysis["flags"]      = flags
        self.risk_scores.append(risk)

        # Risk level
        if risk >= 55:
            analysis["risk_level"] = "DEEPFAKE DETECTED"
        elif risk >= 30:
            analysis["risk_level"] = "SUSPICIOUS"
        elif elapsed < 15:
            analysis["risk_level"] = "ANALYZING..."
        else:
            analysis["risk_level"] = "REAL"

        # Draw everything
        frame = self._draw_overlay(frame, analysis, (x, y, fw, fh))
        return frame, analysis

    # ── Drawing ──────────────────────────────────────────────
    def _draw_overlay(self, frame, analysis, face_rect):
        h, w   = frame.shape[:2]
        risk   = analysis["risk_score"]
        level  = analysis["risk_level"]
        x, y, fw, fh = face_rect

        # Colors
        if "DEEPFAKE" in level:
            color = (0, 0, 255)
        elif "SUSPICIOUS" in level:
            color = (0, 140, 255)
        elif level == "REAL":
            color = (0, 220, 0)
        else:
            color = (200, 200, 0)

        # Face bounding box
        cv2.rectangle(frame, (x, y), (x+fw, y+fh), color, 2)
        cv2.putText(frame, level, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

        # Top bar background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 95), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Title
        cv2.putText(frame, "SENTINEL-GUARD  |  Live Deepfake Detector",
                    (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        # Status
        cv2.putText(frame, f"STATUS: {level}",
                    (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

        # Risk bar
        bx, by, bw, bh = 10, 65, 320, 18
        cv2.rectangle(frame, (bx, by), (bx+bw, by+bh), (50, 50, 50), -1)
        fill = int((risk / 100) * bw)
        cv2.rectangle(frame, (bx, by), (bx+fill, by+bh), color, -1)
        cv2.putText(frame, f"Risk: {risk:.0f}%",
                    (bx+bw+8, by+14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        # Stats bottom-left
        stats = [
            f"Blink Rate  : {analysis['blink_rate']:.1f}/min  (normal: 12-20)",
            f"Blinks      : {analysis['blink_count']}",
            f"Texture     : {analysis['texture_score']:.3f}",
            f"Lighting    : {analysis['lighting_asymmetry']:.3f}",
            f"Symmetry    : {analysis['face_symmetry']:.3f}",
            f"Movement    : {analysis['movement_score']:.3f}",
        ]
        panel_top = h - len(stats) * 22 - 15
        overlay2  = frame.copy()
        cv2.rectangle(overlay2, (0, panel_top-8), (370, h), (10,10,10), -1)
        cv2.addWeighted(overlay2, 0.6, frame, 0.4, 0, frame)
        for i, s in enumerate(stats):
            cv2.putText(frame, s, (10, panel_top + i*22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.44, (200, 200, 200), 1)

        # Flags right side
        for i, flag in enumerate(analysis["flags"]):
            cv2.putText(frame, f"! {flag}", (w-430, 110 + i*25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 80, 255), 1)

        # Alert banner
        if "DEEPFAKE" in level:
            ab = frame.copy()
            cv2.rectangle(ab, (0, h//2-35), (w, h//2+35), (0, 0, 180), -1)
            cv2.addWeighted(ab, 0.7, frame, 0.3, 0, frame)
            cv2.putText(frame, "DEEPFAKE DETECTED — DO NOT TRUST THIS CALL",
                        (w//2-340, h//2+10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        return frame

    def _draw_no_face(self, frame):
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (w, 55), (10,10,10), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        cv2.putText(frame, "SENTINEL-GUARD  |  No face detected",
                    (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100,100,100), 2)
        return frame

    def _log_alert(self, analysis):
        try:
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type"     : "deepfake_alert",
                    "risk"     : analysis["risk_score"],
                    "level"    : analysis["risk_level"],
                    "flags"    : analysis["flags"]
                }) + "\n")
        except Exception as e:
            print(f"Log error: {e}")


# ── Standalone runner ────────────────────────────────────────
if __name__ == "__main__":
    detector = DeepfakeDetector()
    cap      = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[!] Cannot open webcam.")
        exit()

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("\n[✓] Webcam live. Press Q to quit.")
    print("[*] Keep face in frame. Calibrating for 15 seconds...\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame, analysis = detector.analyze_frame(frame)

        if "DEEPFAKE" in analysis.get("risk_level", ""):
            if time.time() - detector.last_alert_time > 10:
                detector._log_alert(analysis)
                detector.last_alert_time = time.time()

        cv2.imshow("SENTINEL-GUARD | Deepfake Detector", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[✓] Session ended. Total blinks detected: {detector.blink_count}")

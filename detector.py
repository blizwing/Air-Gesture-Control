# detector.py
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import mediapipe as mp


@dataclass
class Gesture:
    type: str


class HandDetector:
    def __init__(self, camera_id: int = 0, width: int = 640, height: int = 480) -> None:
        self.cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.draw = mp.solutions.drawing_utils
        self.history: deque[Tuple[float, float, float]] = deque(maxlen=5)

    def release(self) -> None:
        self.cap.release()
        self.hands.close()


    def _detect_swipe(self) -> Optional[str]:
        if len(self.history) < 2:
            return None
        t0, x0, y0 = self.history[0]
        t1, x1, y1 = self.history[-1]
        dt = t1 - t0
        if dt == 0:
            return None
        vx = (x1 - x0) / dt
        vy = (y1 - y0) / dt
        print(f"[SWIPE DEBUG] dt={dt:.2f}s, vx={vx:.2f}, vy={vy:.2f}")

        # relaxed thresholds
        if vx > 1.0 and abs(vy) < 0.8:
            self.history.clear()
            return "swipe_right"
        if vy < -1.0 and abs(vx) < 0.8:
            self.history.clear()
            return "swipe_up"
        if vy > 1.0 and abs(vx) < 0.8:
            self.history.clear()
            return "swipe_down"
        return None

    def _select_closest_hand(self, hands) -> Optional[any]:
        best = None
        best_area = 0.0
        for lm in hands:
            xs = [p.x for p in lm.landmark]
            ys = [p.y for p in lm.landmark]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            if area > best_area:
                best_area = area
                best = lm
        return best if best_area >= 0.05 else None


    def process(self) -> Tuple[Optional[Gesture], Optional[any]]:
        ret, frame = self.cap.read()
        if not ret:
            return None, None

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        gesture: Optional[Gesture] = None

        if results.multi_hand_landmarks:
            hand = self._select_closest_hand(results.multi_hand_landmarks)
            if hand:
                self.draw.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
                wrist = hand.landmark[0]
                self.history.append((time.time(), wrist.x, wrist.y))
                print(f"[HISTORY] entries={len(self.history)}, newest=({wrist.x:.2f},{wrist.y:.2f})")

                swipe = self._detect_swipe()
                if swipe:
                    gesture = Gesture(type=swipe)

            else:
                self.history.clear()
        else:
            self.history.clear()

        return gesture, frame

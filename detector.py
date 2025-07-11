"""Hand detection and gesture recognition module."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import mediapipe as mp


@dataclass
class Gesture:
    """Represents a recognized gesture."""

    type: str
    fingers: int | None = None


class HandDetector:
    """Detects hand landmarks and recognizes gestures."""

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
        self.last_finger_time = 0.0

    def release(self) -> None:
        """Release camera resources."""
        self.cap.release()
        self.hands.close()

    def _count_fingers(self, landmarks) -> int:
        """Return number of extended fingers from landmarks."""
        tips = [4, 8, 12, 16, 20]
        pips = [2, 6, 10, 14, 18]
        fingers = 0
        # Convert normalized landmarks to simple array for readability
        lm = [(lm.x, lm.y) for lm in landmarks.landmark]
        # Determine hand orientation using wrist and MCP of index
        if lm[5][0] < lm[17][0]:
            # Right hand
            if lm[tips[0]][0] > lm[pips[0]][0]:
                fingers += 1
        else:
            # Left hand
            if lm[tips[0]][0] < lm[pips[0]][0]:
                fingers += 1
        for tip, pip in zip(tips[1:], pips[1:]):
            if lm[tip][1] < lm[pip][1]:
                fingers += 1
        return fingers

    def _detect_swipe(self) -> Optional[str]:
        """Detect swipe gestures based on wrist velocity."""
        if len(self.history) < 2:
            return None
        t0, x0, y0 = self.history[0]
        t1, x1, y1 = self.history[-1]
        dt = t1 - t0
        if dt == 0:
            return None
        vx = (x1 - x0) / dt
        vy = (y1 - y0) / dt
        if vx > 2.0 and abs(vy) < 1.0:
            self.history.clear()
            return "swipe_right"
        if vy < -2.0 and abs(vx) < 1.0:
            self.history.clear()
            return "swipe_up"
        if vy > 2.0 and abs(vx) < 1.0:
            self.history.clear()
            return "swipe_down"
        return None

    def process(self) -> Tuple[Optional[Gesture], Optional[any]]:
        """Capture frame and return detected gesture and annotated frame."""
        ret, frame = self.cap.read()
        if not ret:
            return None, None
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        gesture: Optional[Gesture] = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.draw.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                wrist = hand_landmarks.landmark[0]
                self.history.append((time.time(), wrist.x, wrist.y))
                fingers = self._count_fingers(hand_landmarks)
                if fingers:
                    now = time.time()
                    if now - self.last_finger_time > 0.5:
                        gesture = Gesture(type="fingers", fingers=fingers)
                        self.last_finger_time = now
                swipe = self._detect_swipe()
                if swipe:
                    gesture = Gesture(type=swipe)
        else:
            self.history.clear()
        return gesture, frame


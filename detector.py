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
    fingers: Optional[int] = None
    delta: Optional[float] = None


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
        self.last_finger_time = 0.0
        self.scroll_mode = False
        self._activation_time = 0.0
        self._scroll_ref_y: Optional[float] = None

    def release(self) -> None:
        self.cap.release()
        self.hands.close()

    def _count_fingers(self, landmarks) -> int:
        tips = [4, 8, 12, 16, 20]
        pips = [2, 6, 10, 14, 18]
        fingers = 0
        lm = [(lm.x, lm.y) for lm in landmarks.landmark]
        # thumb
        if lm[5][0] < lm[17][0]:
            if lm[tips[0]][0] > lm[pips[0]][0]:
                fingers += 1
        else:
            if lm[tips[0]][0] < lm[pips[0]][0]:
                fingers += 1
        # other four
        for tip, pip in zip(tips[1:], pips[1:]):
            if lm[tip][1] < lm[pip][1]:
                fingers += 1
        return fingers

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

    def _is_pointing_at_camera(self, landmarks) -> bool:
        tip = landmarks.landmark[8]
        dip = landmarks.landmark[7]
        return tip.z < dip.z - 0.02

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

                fingers = self._count_fingers(hand)
                now = time.time()

                # scroll mode
                if self.scroll_mode:
                    if fingers == 1 and self._is_pointing_at_camera(hand):
                        idx = hand.landmark[8].y
                        if self._scroll_ref_y is None:
                            self._scroll_ref_y = idx
                        delta = self._scroll_ref_y - idx
                        self._scroll_ref_y = idx
                        gesture = Gesture(type="scroll", delta=delta)
                    else:
                        self.scroll_mode = False
                        self._scroll_ref_y = None
                else:
                    # enter scroll: five-finger hold then point
                    if fingers == 5:
                        self._activation_time = now
                    elif fingers == 1 and (now - self._activation_time) < 1.5 and self._is_pointing_at_camera(hand):
                        print("[DEBUG] Entering scroll mode")
                        self.scroll_mode = True
                        self._scroll_ref_y = hand.landmark[8].y
                    # finger count gestures
                    elif fingers and (now - self.last_finger_time) > 0.5:
                        gesture = Gesture(type="fingers", fingers=fingers)
                        self.last_finger_time = now

                # only detect swipes when not in scroll mode
                if not self.scroll_mode:
                    swipe = self._detect_swipe()
                    if swipe:
                        gesture = Gesture(type=swipe)

            else:
                self.history.clear()
        else:
            self.history.clear()

        return gesture, frame

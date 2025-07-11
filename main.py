# app.py
from __future__ import annotations

import time
import tkinter as tk
from typing import Dict, Optional, Tuple

import cv2
from PIL import Image, ImageTk

from detector import HandDetector, Gesture
import actions


class App(tk.Tk):
    """Tkinter GUI application."""
    def __init__(self) -> None:
        super().__init__()
        self.title("Air Gesture Control")
        self.detector = HandDetector()
        self.enabled: Dict[str, tk.BooleanVar] = {
            "swipe_right": tk.BooleanVar(value=True),
            "swipe_up":    tk.BooleanVar(value=True),
            "swipe_down":  tk.BooleanVar(value=True),
        }
        self._build_ui()
        self.last_action: Dict[str, float] = {}
        self.delay = 66  # ~15 FPS
        self.update_frame()

    def _build_ui(self) -> None:
        self.video_label = tk.Label(self, bd=0, highlightthickness=0)
        self.video_label.pack()
        btn_frame = tk.Frame(self)
        btn_frame.pack()
        for name, var in self.enabled.items():
            cb = tk.Checkbutton(btn_frame, text=name, variable=var)
            cb.pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Hide", command=self.iconify).pack(side=tk.LEFT)


    def update_frame(self) -> None:
        gesture, frame = self.detector.process()
        if frame is not None:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)



        if gesture:
            print(f"[DEBUG] Gesture received in update_frame: {gesture}")
            self.handle_gesture(gesture)

        self.after(self.delay, self.update_frame)

    def handle_gesture(self, gesture: Gesture) -> None:
        print(f"[DEBUG] handle_gesture called with: {gesture}")
        enabled_var = self.enabled.get(gesture.type)
        print(f"[DEBUG] enabled flag for '{gesture.type}': {enabled_var.get() if enabled_var else 'N/A'}")
        if not enabled_var or not enabled_var.get():
            print("[DEBUG] gesture ignored because flag is off or missing")
            return


        # rate-limit
        now = time.time()
        if now - self.last_action.get(gesture.type, 0) < 1.0:
            print("[DEBUG] gesture ignored due to rate limiting")
            return
        self.last_action[gesture.type] = now

        # other gestures
        if gesture.type == "swipe_right":
            print("[DEBUG] swipe_right detected")
            actions.dismiss_notifications()
        elif gesture.type == "swipe_up":
            print("[DEBUG] swipe_up detected")
            actions.send_page_down()
        elif gesture.type == "swipe_down":
            print("[DEBUG] swipe_down detected")
            actions.send_page_up()
        else:
            print(f"[DEBUG] unhandled gesture type: {gesture.type}")


if __name__ == "__main__":
    app = App()
    app.protocol(
        "WM_DELETE_WINDOW",
        lambda: (
            actions.release_mod_keys(),
            app.detector.release(),
            app.destroy(),
        ),
    )
    app.mainloop()

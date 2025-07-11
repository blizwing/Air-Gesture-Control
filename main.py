"""Main application entry point with GUI."""
from __future__ import annotations

import time
import tkinter as tk
from typing import Dict

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
            "swipe_up": tk.BooleanVar(value=True),
            "swipe_down": tk.BooleanVar(value=True),
            "fingers": tk.BooleanVar(value=True),
        }
        self._build_ui()
        self.last_action: Dict[str, float] = {}
        self.delay = 66  # ~15 FPS
        self.update_frame()

    def _build_ui(self) -> None:
        self.video_label = tk.Label(self)
        self.video_label.pack()
        btn_frame = tk.Frame(self)
        btn_frame.pack()
        for name, var in self.enabled.items():
            cb = tk.Checkbutton(btn_frame, text=name, variable=var)
            cb.pack(side=tk.LEFT)

    def update_frame(self) -> None:
        gesture, frame = self.detector.process()
        if frame is not None:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        if gesture:
            self.handle_gesture(gesture)
        self.after(self.delay, self.update_frame)

    def handle_gesture(self, gesture: Gesture) -> None:
        if not self.enabled.get(gesture.type, tk.BooleanVar(value=False)).get():
            return
        now = time.time()
        if now - self.last_action.get(gesture.type, 0) < 1.0:
            return
        self.last_action[gesture.type] = now
        if gesture.type == "swipe_right":
            actions.dismiss_notifications()
        elif gesture.type == "swipe_up":
            actions.send_page_down()
        elif gesture.type == "swipe_down":
            actions.send_page_up()
        elif gesture.type == "fingers" and gesture.fingers:
            actions.toggle_taskbar_slot(gesture.fingers)


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.detector.release(), app.destroy()))
    app.mainloop()



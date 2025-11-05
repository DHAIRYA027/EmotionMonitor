import time
import threading
import csv
import os
from datetime import datetime
from pynput import keyboard, mouse
import rumps
from flask import Flask, jsonify, send_from_directory
import AppKit

UPDATE_INTERVAL = 15
DATA_LOG = "logs/activity_data.csv"

app = Flask(__name__)

# ============================
# ACTIVITY TRACKER
# ============================
class ActivityTracker:
    def __init__(self):
        self.key_count = 0
        self.mouse_movement = 0
        self.clicks = 0
        self.last_time = time.time()
        self.lock = threading.Lock()
        self.history = []
        self.emotion = "Initializing..."
        self.paused = False

        self.k_listener = keyboard.Listener(on_press=self.on_key_press)
        self.m_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)

    def start(self):
        self.k_listener.start()
        self.m_listener.start()

    def on_key_press(self, key):
        if not self.paused:
            with self.lock:
                self.key_count += 1

    def on_click(self, x, y, button, pressed):
        if pressed and not self.paused:
            with self.lock:
                self.clicks += 1

    def on_move(self, x, y):
        if not self.paused:
            with self.lock:
                self.mouse_movement += 1

    def analyze(self):
        with self.lock:
            elapsed = time.time() - self.last_time
            if elapsed < UPDATE_INTERVAL:
                return None
            self.last_time = time.time()

            kpm = max(0, int(self.key_count * (60 / elapsed)))
            mouse_activity = int(self.mouse_movement / elapsed)
            clicks = int(self.clicks)

            self.key_count = self.mouse_movement = self.clicks = 0

            emotion = self.classify_emotion(kpm)
            self.emotion = emotion

            entry = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "kpm": kpm,
                "mouse": mouse_activity,
                "clicks": clicks,
                "emotion": emotion
            }

            self.history.append(entry)
            self.history = self.history[-40:]
            return entry

    def classify_emotion(self, kpm):
        if kpm > 170:
            return "Focused"
        elif kpm > 120:
            return "Normal"
        elif kpm > 60:
            return "Tired"
        else:
            return "Stressed"


# ============================
# MENU BAR APP
# ============================
class EmotionApp(rumps.App):
    def __init__(self, tracker):
        super().__init__("Initializing...", icon=None, quit_button=None)
        self.tracker = tracker
        self.menu = ["Pause Monitoring", "Open Dashboard", None, "Quit EmotionMonitor"]
        self.icon_map = {
            "Focused": "🧠",
            "Normal": "💛",
            "Tired": "💤",
            "Stressed": "🔥",
            "Idle": "⚫",
            "Initializing...": "💤"
        }

    @rumps.clicked("Pause Monitoring")
    def pause(self, _):
        self.tracker.paused = not self.tracker.paused
        msg = "Paused" if self.tracker.paused else "Resumed"
        rumps.notification("EmotionMonitor", "Monitoring", msg)
        self.title = "⏸️ Paused" if self.tracker.paused else f"{self.icon_map.get(self.tracker.emotion)} {self.tracker.emotion}"

    @rumps.clicked("Open Dashboard")
    def open_dash(self, _):
        import webbrowser
        webbrowser.open("http://localhost:8080")

    @rumps.clicked("Quit EmotionMonitor")
    def quit_app(self, _):
        rumps.quit_application()

    def update_ui(self, emotion):
        self.title = f"{self.icon_map.get(emotion, '💤')} {emotion}"


# ============================
# BACKGROUND LOOP
# ============================
def analyzer_loop(tracker, ui):
    while True:
        entry = tracker.analyze()
        if entry and not tracker.paused:
            print(f"[{entry['timestamp']}] {entry['emotion']} | KPM={entry['kpm']} | Mouse={entry['mouse']} | Clicks={entry['clicks']}")
            ui.update_ui(entry["emotion"])
        time.sleep(UPDATE_INTERVAL)


# ============================
# FLASK ROUTES
# ============================
@app.route("/")
def serve_dashboard():
    return send_from_directory(".", "dashboard.html")

@app.route("/api/stats")
def stats():
    labels = [h["timestamp"] for h in tracker.history]
    values = [h["kpm"] for h in tracker.history]
    current = tracker.history[-1] if tracker.history else {"emotion": "--", "kpm": 0, "mouse": 0, "clicks": 0}
    return {"labels": labels, "values": values, "current": current}


# ============================
# MAIN
# ============================
if __name__ == "__main__":
    AppKit.NSApplication.sharedApplication().setActivationPolicy_(1)
    tracker = ActivityTracker()
    tracker.start()

    ui = EmotionApp(tracker)
    threading.Thread(target=lambda: app.run(host="127.0.0.1", port=8080), daemon=True).start()
    threading.Thread(target=analyzer_loop, args=(tracker, ui), daemon=True).start()
    print("[INFO] Emotion + Activity Monitor (v12 - Neon Dashboard Integrated)")
    ui.run()

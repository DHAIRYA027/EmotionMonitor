import time
import threading
import csv
import os
from datetime import datetime
from pynput import keyboard, mouse
import rumps
from flask import Flask, jsonify, render_template_string
import AppKit

# =============================
# Configuration
# =============================
UPDATE_INTERVAL = 15  # seconds
NOTIFY_INTERVAL = 480  # 8 minutes
DATA_LOG = "logs/activity_data.csv"

# =============================
# Flask Dashboard
# =============================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<title>EmotionMonitor AI Dashboard</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(120deg,#0f2027,#203a43,#2c5364); color:white; text-align:center; }
  h1 { margin-top:20px; }
  .stats { margin:20px auto; width:60%; background:#1b1b1b; border-radius:10px; padding:10px; box-shadow:0 0 10px rgba(0,0,0,0.3); }
  .stats p { font-size:18px; margin:8px 0; }
  canvas { margin-top:20px; background:#1b1b1b; border-radius:10px; padding:10px; }
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
  <h1>🧠 EmotionMonitor AI — Dashboard</h1>
  <div class="stats">
    <p><b>Current Emotion:</b> <span id="emotion">--</span></p>
    <p><b>Keystrokes/min:</b> <span id="kpm">--</span></p>
    <p><b>Mouse Movements:</b> <span id="mouse">--</span></p>
    <p><b>Clicks:</b> <span id="clicks">--</span></p>
  </div>
  <canvas id="emotionChart" width="700" height="300"></canvas>

  <script>
    const ctx = document.getElementById('emotionChart').getContext('2d');
    let chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Emotion Score (%)',
          borderColor: '#00e5ff',
          backgroundColor: 'rgba(0,229,255,0.2)',
          data: [],
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        scales: {
          x: { ticks: { color: '#fff' } },
          y: { beginAtZero: true, max: 100, ticks: { color: '#fff' } }
        },
        plugins: {
          legend: { labels: { color: '#fff' } }
        }
      }
    });

    // Define colors per emotion
    const emotionColors = {
      "Focused": {border: "#00ffcc", fill: "rgba(0,255,204,0.2)"},
      "Normal": {border: "#ffd700", fill: "rgba(255,215,0,0.2)"},
      "Tired": {border: "#ff8c00", fill: "rgba(255,140,0,0.2)"},
      "Stressed": {border: "#ff3b3b", fill: "rgba(255,59,59,0.2)"},
      "Idle": {border: "#999", fill: "rgba(153,153,153,0.2)"}
    };

    async function updateData() {
      const res = await fetch('/api/stats');
      const data = await res.json();
      chart.data.labels = data.labels;
      chart.data.datasets[0].data = data.values;
      
      // Update stats
      document.getElementById("emotion").textContent = data.current.emotion;
      document.getElementById("kpm").textContent = data.current.kpm;
      document.getElementById("mouse").textContent = data.current.mouse;
      document.getElementById("clicks").textContent = data.current.clicks;

      // Change graph color according to emotion
      const colors = emotionColors[data.current.emotion] || {border: "#00e5ff", fill: "rgba(0,229,255,0.2)"};
      chart.data.datasets[0].borderColor = colors.border;
      chart.data.datasets[0].backgroundColor = colors.fill;
      chart.update();
    }

    setInterval(updateData, 15000);
    updateData();
  </script>
</body>
</html>
"""

# =============================
# Emotion Tracking Logic
# =============================
class ActivityTracker:
    def __init__(self):
        self.key_count = 0
        self.mouse_movement = 0
        self.clicks = 0
        self.last_time = time.time()
        self.lock = threading.Lock()
        self.history = []
        self.emotion = "Initializing..."
        self.score = 0
        self.paused = False
        self.last_notify = 0

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

            kpm = round(self.key_count * (60 / elapsed))
            mouse_activity = round(self.mouse_movement / elapsed)
            clicks = self.clicks

            self.key_count = self.mouse_movement = self.clicks = 0

            # Stable weighted scoring
            base_score = min(100, int((kpm * 0.5) + (mouse_activity * 0.05) + (clicks * 0.3)))
            self.score = (self.score * 0.9) + (base_score * 0.1)

            emotion = self.classify_emotion(kpm, self.score)
            self.emotion = emotion

            entry = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "kpm": kpm,
                "mouse": mouse_activity,
                "clicks": clicks,
                "emotion": emotion,
                "score": round(self.score, 2)
            }

            self.history.append(entry)
            self.history = self.history[-40:]
            self.log_data(entry)
            return entry

    def classify_emotion(self, kpm, score):
        if kpm < 40:
            return "Idle"
        elif score > 200:
            return "Stressed"
        elif score > 100:
            return "Focused"
        elif score > 70:
            return "Normal"
        else:
            return "Tired"

    def log_data(self, entry):
        os.makedirs("logs", exist_ok=True)
        new_file = not os.path.exists(DATA_LOG)
        with open(DATA_LOG, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=entry.keys())
            if new_file:
                writer.writeheader()
            writer.writerow(entry)

# =============================
# Menubar App
# =============================
class EmotionApp(rumps.App):
    def __init__(self, tracker):
        super(EmotionApp, self).__init__("Initializing...", icon=None, quit_button=None)
        self.tracker = tracker
        self.menu = ["Pause Monitoring", "Open Dashboard", None, "Quit EmotionMonitor"]
        self.icon_map = {
            "Focused": "🧠",
            "Normal": "💛",
            "Tired": "🟠",
            "Stressed": "🔴",
            "Idle": "⚫",
            "Initializing...": "💤"
        }

    @rumps.clicked("Pause Monitoring")
    def pause_monitoring(self, _):
        self.tracker.paused = not self.tracker.paused
        self.title = "⏸️ Monitoring Paused" if self.tracker.paused else f"{self.icon_map.get(self.tracker.emotion)} {self.tracker.emotion}"
        rumps.notification("EmotionMonitor", "Monitoring", "Paused" if self.tracker.paused else "Resumed")

    @rumps.clicked("Open Dashboard")
    def open_dashboard(self, _):
        import webbrowser
        webbrowser.open("http://localhost:8080")

    @rumps.clicked("Quit EmotionMonitor")
    def quit_app(self, _):
        rumps.quit_application()

    def update_ui(self, emotion):
        self.title = f"{self.icon_map.get(emotion, '💤')} {emotion}"

# =============================
# Background Threads
# =============================
def analyzer_loop(tracker, app_ui):
    while True:
        entry = tracker.analyze()
        if entry and not tracker.paused:
            print(f"[{entry['timestamp']}] {entry['emotion']}({entry['score']}%) KPM={entry['kpm']} Mouse={entry['mouse']} Clicks={entry['clicks']}")
            app_ui.update_ui(entry["emotion"])

            if entry["emotion"] in ["Tired", "Stressed"]:
                if time.time() - tracker.last_notify > NOTIFY_INTERVAL:
                    msg = "You seem tired, take a short break 💆‍♂️" if entry["emotion"] == "Tired" else "You seem stressed, relax for a minute 🧘"
                    rumps.notification("EmotionMonitor", entry["emotion"], msg)
                    tracker.last_notify = time.time()
        time.sleep(UPDATE_INTERVAL)

# =============================
# Flask Routes
# =============================
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/stats")
def get_stats():
    labels = [h["timestamp"] for h in tracker.history]
    values = [h["score"] for h in tracker.history]
    current = tracker.history[-1] if tracker.history else {"emotion": "--", "kpm": 0, "mouse": 0, "clicks": 0}
    return jsonify({"labels": labels, "values": values, "current": current})

# =============================
# Run Everything
# =============================
if __name__ == "__main__":
    # 🧩 Hide Dock icon (menubar only)
    AppKit.NSApplication.sharedApplication().setActivationPolicy_(1)

    tracker = ActivityTracker()
    tracker.start()

    app_ui = EmotionApp(tracker)

    flask_thread = threading.Thread(target=lambda: app.run(host="127.0.0.1", port=8080))
    flask_thread.daemon = True
    flask_thread.start()

    analyzer_thread = threading.Thread(target=analyzer_loop, args=(tracker, app_ui))
    analyzer_thread.daemon = True
    analyzer_thread.start()

    print("[INFO] Starting Emotion + Activity Monitor (v10 - Smart Graph Color + Menubar Only)...")
    app_ui.run()

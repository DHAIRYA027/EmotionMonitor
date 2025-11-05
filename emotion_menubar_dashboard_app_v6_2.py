#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Emotion + Activity Monitor (macOS v6.2 Final Stable)
Thread-safe | Fixed Dashboard | Smart Fallback | 7-min Detection | Focus Mode | Notifications
"""

import time
import json
import subprocess
import threading
from datetime import datetime
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
import numpy as np
import rumps
import AppKit
import objc
from WebKit import WKWebView, WKWebViewConfiguration

# Hide Dock icon
rumps.debug_mode(False)
AppKit.NSApplication.sharedApplication().setActivationPolicy_(1)

# --- Core Configurations ---
DETECTION_INTERVAL = 420     # 7 minutes
NOTIFY_COOLDOWN = 900        # 15 minutes

# --- State ---
state = {
    "emotion": "Normal",
    "activity": "Idle",
    "last_notified": 0,
    "focus_mode": False,
    "paused": False,
    "history": deque(maxlen=15)
}

# --- Emoji Titles ---
EMOJI_TEXT = {
    "Focused": "🧠 Focused and Productive 🧠",
    "Normal": "🧠 Stable Mood 🙂",
    "Tired": "🧠 You seem tired 😴",
    "Stressed": "🧠 Feeling Stressed 😣",
}

# --- Thread-safe Main Thread Execution ---
def run_on_main_thread(func):
    AppKit.NSApp().performSelectorOnMainThread_withObject_waitUntilDone_(
        objc.selector(func, signature=b"v@:"), None, False
    )

# --- macOS Notification ---
def system_notify(title, message):
    def _notify():
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script])
        except Exception as e:
            print("[WARN] Notification failed:", e)
    run_on_main_thread(_notify)

# --- Dashboard HTML ---
def get_dashboard_html():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Emotion Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{
                background: linear-gradient(135deg, #0d1117, #161b22);
                color: #e6edf3;
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 20px;
            }}
            h1 {{ font-size: 22px; }}
            canvas {{ width: 90%; height: 70%; margin-top: 20px; }}
            #legend {{
                display: flex; justify-content: center; gap: 20px; margin-top: 15px; font-size: 15px;
            }}
        </style>
    </head>
    <body>
        <h1>🧠 Emotion + Activity Dashboard</h1>
        <p>Tracking your emotional state during this session</p>
        <div><canvas id="chart"></canvas></div>
        <div id="legend">
            <span style="color:#00FF00;">🟢 Focused</span>
            <span style="color:#1E90FF;">🔵 Normal</span>
            <span style="color:#FFA500;">🟠 Tired</span>
            <span style="color:#FF4500;">🔴 Stressed</span>
        </div>
        <script>
            async function updateChart() {{
                const res = await fetch('http://localhost:8080/api/stats');
                const data = await res.json();
                const emotions = data.history.map(item => item.emotion);
                const times = data.history.map(item => item.time);
                const colors = emotions.map(e => ({{ 
                    "Focused": "#00FF00",
                    "Normal": "#1E90FF",
                    "Tired": "#FFA500",
                    "Stressed": "#FF4500"
                }})[e]);
                const ctx = document.getElementById('chart').getContext('2d');
                if (window.chartInstance) window.chartInstance.destroy();
                window.chartInstance = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: times,
                        datasets: [{{
                            label: 'Emotion Trend',
                            data: emotions.map((e,i)=>i+1),
                            borderColor: colors[colors.length-1] || "#00FF00",
                            backgroundColor: colors.map(c => c + "33"),
                            fill: true,
                            tension: 0.4,
                            borderWidth: 3,
                            pointRadius: 5,
                            pointBackgroundColor: colors
                        }}]
                    }},
                    options: {{
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            x: {{ ticks: {{ color: '#bbb' }} }},
                            y: {{ display: false }}
                        }}
                    }}
                }});
            }}
            setInterval(updateChart, 3000);
            updateChart();
        </script>
    </body>
    </html>
    """

# --- Local Server for Dashboard Data ---
class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/stats":
            stats = {
                "emotion": state["emotion"],
                "activity": state["activity"],
                "focus_mode": state["focus_mode"],
                "paused": state["paused"],
                "history": list(state["history"]),
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(get_dashboard_html().encode("utf-8"))

def run_server():
    server = HTTPServer(("localhost", 8080), DashboardHandler)
    print("[INFO] Dashboard data server running at http://localhost:8080")
    server.serve_forever()

# --- Emotion Detection Simulation ---
def detect_emotion_activity(app):
    if state["paused"]:
        return
    emotions = ["Focused", "Normal", "Tired", "Stressed"]
    activities = ["Typing", "Browsing", "Idle"]
    e = np.random.choice(emotions)
    a = np.random.choice(activities)
    state["emotion"] = e
    state["activity"] = a
    state["history"].append({ "emotion": e, "time": datetime.now().strftime("%H:%M:%S") })

    def update_ui():
        app.title = EMOJI_TEXT.get(e, "🧠 Monitoring...")
    run_on_main_thread(update_ui)

    print(f"[INFO] Emotion: {e}, Activity: {a}")

    now = time.time()
    if not state["focus_mode"] and e in ["Tired", "Stressed"] and (now - state["last_notified"]) > NOTIFY_COOLDOWN:
        system_notify("🧘 Emotion Monitor", "You seem tired — take a short break ☕")
        state["last_notified"] = now

def analyzer_loop(app):
    while True:
        detect_emotion_activity(app)
        time.sleep(DETECTION_INTERVAL)

# --- Native Popup Dashboard (WebKit) ---
class DashboardWindow(AppKit.NSWindow):
    def __init__(self):
        screen = AppKit.NSScreen.mainScreen().frame()
        width, height = 900, 600
        rect = AppKit.NSMakeRect((screen.size.width-width)/2, (screen.size.height-height)/2, width, height)
        style = AppKit.NSTitledWindowMask | AppKit.NSClosableWindowMask | AppKit.NSResizableWindowMask
        super(DashboardWindow, self).__init__(rect, style, AppKit.NSBackingStoreBuffered, False)
        self.setTitle_("🧠 Emotion + Activity Dashboard")
        self.setLevel_(AppKit.NSFloatingWindowLevel)
        config = WKWebViewConfiguration.alloc().init()
        self.webview = WKWebView.alloc().initWithFrame_configuration_(self.contentView().frame(), config)
        self.webview.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        self.setContentView_(self.webview)
        self.center()
        self.webview.loadRequest_(objc.lookUpClass("NSURLRequest").requestWithURL_(objc.lookUpClass("NSURL").URLWithString_("http://localhost:8080")))

# --- Menubar App ---
class EmotionMenubarApp(rumps.App):
    def __init__(self):
        super(EmotionMenubarApp, self).__init__("🧠", title="Emotion Monitor", quit_button=None)
        self.dashboard = None
        self.menu = ["Open Dashboard", "Open in Browser", "Pause Monitoring", "Toggle Focus Mode", None, "Quit"]
        threading.Thread(target=run_server, daemon=True).start()
        threading.Thread(target=analyzer_loop, args=(self,), daemon=True).start()

    @rumps.clicked("Open Dashboard")
    def open_dashboard(self, _):
        def show_dashboard():
            try:
                if not self.dashboard:
                    self.dashboard = DashboardWindow()
                self.dashboard.makeKeyAndOrderFront_(None)
            except Exception as e:
                print("[WARN] WebKit load failed:", e)
                alert = AppKit.NSAlert.alloc().init()
                alert.setMessageText_("Dashboard Error")
                alert.setInformativeText_("The native dashboard couldn't load. Would you like to open it in your browser instead?")
                alert.addButtonWithTitle_("Yes")
                alert.addButtonWithTitle_("No")
                if alert.runModal() == AppKit.NSAlertFirstButtonReturn:
                    subprocess.run(["open", "http://localhost:8080"])
        run_on_main_thread(show_dashboard)

    @rumps.clicked("Open in Browser")
    def open_in_browser(self, _):
        subprocess.run(["open", "http://localhost:8080"])

    @rumps.clicked("Pause Monitoring")
    def toggle_pause(self, _):
        state["paused"] = not state["paused"]
        status = "Paused ⏸️" if state["paused"] else "Resumed ▶️"
        run_on_main_thread(lambda: setattr(self, "title", f"🧠 {status}"))
        system_notify("Emotion Monitor", f"Monitoring {status.lower()}")

    @rumps.clicked("Toggle Focus Mode")
    def toggle_focus(self, _):
        state["focus_mode"] = not state["focus_mode"]
        mode = "ON 🧘" if state["focus_mode"] else "OFF 💻"
        system_notify("Focus Mode", f"Focus Mode turned {mode}")

    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()


if __name__ == "__main__":
    print("Starting Emotion + Activity Monitor (v6.2 Final Stable)...")
    EmotionMenubarApp().run()

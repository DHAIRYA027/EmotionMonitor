# ===============================================
# Emotion + Activity Monitor v7  (Core Functional Demo)
# ===============================================
import threading, time, random, json, webbrowser, math
from datetime import datetime
from collections import deque
import rumps
import AppKit
from flask import Flask, jsonify, Response

# ------------------------------------------------
# Simulated adaptive baseline + emotion detection
# ------------------------------------------------
baseline = {"kpm": 180, "mouse": 9000, "clicks": 20}
history = deque(maxlen=40)

def simulate_metrics():
    """Simulate keystrokes/mouse/clicks."""
    return {
        "kpm": random.randint(100, 260),
        "mouse": random.randint(5000, 15000),
        "clicks": random.randint(5, 35),
    }

def detect_emotion(metrics):
    """Heuristic emotion + confidence based on deviation."""
    kpm, mouse, clicks = metrics["kpm"], metrics["mouse"], metrics["clicks"]
    emotion = "Normal"; emoji = "🙂"
    if kpm > 240 or mouse > 14000: emotion, emoji = "Stressed", "⚡️"
    elif kpm < 120 and mouse < 5000: emotion, emoji = "Tired", "🌙"
    elif 160 < kpm < 230 and 7000 < mouse < 11000: emotion, emoji = "Focused", "🧠"
    conf = 90 - abs(kpm - baseline["kpm"]) / 3
    conf = max(60, min(99, int(conf)))
    return emotion, emoji, conf

# ------------------------------------------------
# Flask dashboard
# ------------------------------------------------
app = Flask(__name__)
HTML = """
<!DOCTYPE html><html><head>
<title>Emotion Monitor</title>
<meta name='viewport' content='width=device-width,initial-scale=1'/>
<style>
body{font-family:-apple-system,Helvetica;background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);
color:white;text-align:center;margin:0;padding:0}
h1{margin-top:30px}
.card{display:inline-block;margin:10px;padding:15px 25px;background:rgba(255,255,255,0.1);
border-radius:12px}
footer{margin-top:20px;font-size:12px;opacity:0.6}
</style></head><body>
<h1>🧠 Emotion + Activity Monitor</h1>
<div id='data'></div>
<footer>Auto refresh every 3 s</footer>
<script>
async function refresh(){
 const r=await fetch('/api/stats'); const d=await r.json();
 document.getElementById('data').innerHTML =
  `<div class='card'><b>Emotion:</b> ${d.emotion} (${d.confidence}%)</div>
   <div class='card'><b>KPM:</b> ${d.kpm}</div>
   <div class='card'><b>Mouse px/min:</b> ${d.mouse}</div>
   <div class='card'><b>Clicks/min:</b> ${d.clicks}</div>`;
}
refresh(); setInterval(refresh,3000);
</script></body></html>
"""

@app.route("/")
def home(): return Response(HTML, mimetype="text/html")

@app.route("/api/stats")
def stats():
    if history: h = history[-1]
    else: h = {"emotion":"Initializing","confidence":0,"kpm":0,"mouse":0,"clicks":0}
    return jsonify(h)

def start_server():
    app.run(port=8080, debug=False, use_reloader=False)

# ------------------------------------------------
# macOS menubar app
# ------------------------------------------------
class EmotionApp(rumps.App):
    def __init__(self):
        super().__init__("🧠 Initializing...", quit_button=None)
        self.menu = ["Open Dashboard", "Pause Monitoring", None, "Quit"]
        self.paused = False
        self.last_notify = 0
        threading.Thread(target=start_server, daemon=True).start()
        time.sleep(1)
        webbrowser.open("http://localhost:8080")   # auto open first launch
        threading.Thread(target=self.loop, daemon=True).start()

    @rumps.clicked("Open Dashboard")
    def open_dash(self,_):
        webbrowser.open("http://localhost:8080")

    @rumps.clicked("Pause Monitoring")
    def pause(self,_):
        self.paused = not self.paused
        self.title = "⏸ Paused" if self.paused else "🧠 Resuming..."
        time.sleep(2); self.title="🧠 Monitoring..."

    @rumps.clicked("Quit")
    def quit_app(self,_=None): rumps.quit_application()

    def notify(self,title,msg):
        AppKit.NSUserNotificationCenter.defaultUserNotificationCenter().deliverNotification_(
            AppKit.NSUserNotification.alloc().init().autorelease())
        note = AppKit.NSUserNotification.alloc().init()
        note.setTitle_(f"🧠 {title}")
        note.setInformativeText_(msg)
        AppKit.NSUserNotificationCenter.defaultUserNotificationCenter().deliverNotification_(note)

    def loop(self):
        while True:
            if not self.paused:
                metrics = simulate_metrics()
                # adaptive baseline
                for k in baseline:
                    baseline[k] = (baseline[k]*0.9 + metrics[k]*0.1)
                emotion, emoji, conf = detect_emotion(metrics)
                data = {"time":datetime.now().isoformat(),
                        "emotion":emotion,"confidence":conf, **metrics}
                history.append(data)
                self.title = f"{emoji} {emotion}"
                # occasional notification
                now=time.time()
                if emotion in ["Tired","Stressed"] and now-self.last_notify>900:
                    self.notify(emotion, f"You seem {emotion.lower()}, take a short break.")
                    self.last_notify=now
                print(f"[INFO] {emotion} ({conf}%) | kpm={metrics['kpm']} mouse={metrics['mouse']} clicks={metrics['clicks']}")
            time.sleep(5)  # update every 5 sec for testing

if __name__ == "__main__":
    EmotionApp().run()

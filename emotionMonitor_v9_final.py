import os, time, threading, random, datetime, webbrowser, rumps
from flask import Flask, jsonify, render_template_string
from AppKit import NSApplication, NSApp, NSApplicationActivationPolicyAccessory

# --- Setup ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "session_log.txt")

flask_app = Flask(__name__)
data_lock = threading.Lock()

# --- Global state ---
stats = {
    "emotion": "Initializing",
    "confidence": 0,
    "kpm": 0,
    "mouse": 0,
    "clicks": 0,
    "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
}

emotion_colors = {
    "Focused": "#00ff66",
    "Normal": "#FFD700",
    "Tired": "#0096FF",
    "Stressed": "#FF4040"
}

# --- Dashboard HTML ---
HTML_DASHBOARD = """<!DOCTYPE html><html><head>
<title>🧠 Emotion + Activity Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background-color:#0d0d0f;color:#f5f5f5;font-family:'Inter',sans-serif;text-align:center;padding:20px;}
canvas{width:90%%!important;height:70vh!important;margin:auto;border-radius:12px;background:#111;box-shadow:0 0 15px rgba(0,0,0,0.4);}
.legend{display:flex;justify-content:center;gap:15px;margin-top:10px;}
.legend div{display:flex;align-items:center;gap:6px;font-size:14px;}
.color-box{width:16px;height:16px;border-radius:3px;}
</style></head><body>
<h2>🧠 Emotion + Activity Monitor</h2>
<div id="stats">Loading...</div>
<canvas id="chart"></canvas>
<div class="legend">
<div><span class="color-box" style="background:#00ff66"></span>Focused</div>
<div><span class="color-box" style="background:#FFD700"></span>Normal</div>
<div><span class="color-box" style="background:#0096FF"></span>Tired</div>
<div><span class="color-box" style="background:#FF4040"></span>Stressed</div>
</div>
<script>
const ctx=document.getElementById('chart').getContext('2d');
const data={labels:[],datasets:[{label:'Keystrokes/min',data:[],borderColor:'#FFD700',backgroundColor:'rgba(255,215,0,0.25)',fill:true,tension:.3}]};
const chart=new Chart(ctx,{type:'line',data:data,options:{animation:{duration:800},scales:{x:{ticks:{color:'#aaa'}},y:{ticks:{color:'#aaa'}}}}});
async function fetchData(){
try{
const r=await fetch('/api/stats');const d=await r.json();
document.getElementById('stats').innerHTML=`Emotion:<b style="color:${d.color}">${d.emotion}</b> (${d.confidence}%) | KPM:${d.kpm} | Mouse:${d.mouse} | Clicks:${d.clicks}`;
if(data.labels.length>40){data.labels.shift();data.datasets[0].data.shift();}
data.labels.push(d.timestamp);data.datasets[0].data.push(d.kpm);
data.datasets[0].borderColor=d.color;data.datasets[0].backgroundColor=d.color+'40';
chart.update();
}catch(e){document.getElementById('stats').innerText='⚠️ Waiting for live data...';}}
setInterval(fetchData,10000);fetchData();
</script></body></html>"""

@flask_app.route("/")
def dashboard():
    return render_template_string(HTML_DASHBOARD)

@flask_app.route("/api/stats")
def api_stats():
    with data_lock:
        return jsonify(stats | {"color": emotion_colors.get(stats["emotion"], "#FFFFFF")})

# --- Simulated behavior ---
def simulate():
    emotions = ["Focused", "Normal", "Tired", "Stressed"]
    e = random.choices(emotions, weights=[0.3, 0.4, 0.2, 0.1])[0]
    return e, random.randint(60, 100), random.randint(50, 300), random.randint(2000, 20000), random.randint(10, 50)

# --- Analyzer Loop ---
def analyzer_loop():
    last_notified = 0
    while True:
        e, c, k, m, cl = simulate()
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        with data_lock:
            stats.update({"emotion": e, "confidence": c, "kpm": k, "mouse": m, "clicks": cl, "timestamp": ts})

        log = f"[{ts}] {e} ({c}%) | KPM={k} | Mouse={m} | Clicks={cl}\n"
        with open(LOG_FILE, "a") as f:
            f.write(log)
        print(log.strip())

        # Notify only if Tired or Stressed every 7–8 min
        now = time.time()
        if e in ["Tired", "Stressed"] and now - last_notified >= random.randint(420, 480):
            try:
                msg_map = {
                    "Tired": ("Emotion Monitor", "😴 Feeling Tired?", "Take a short break to recharge."),
                    "Stressed": ("Emotion Monitor", "⚡ Feeling Stressed?", "Breathe deeply and relax for a moment.")
                }
                title, subtitle, message = msg_map[e]
                rumps.notification(title, subtitle, message)
                last_notified = now
            except Exception as err:
                print(f"[WARN] Notification failed: {err}")

        time.sleep(15)

# --- Menu Bar UI ---
class MenuBar(rumps.App):
    def __init__(self):
        super(MenuBar, self).__init__("🧠 Initializing")
        self.menu = ["Open Dashboard", None, "Pause Monitoring", "View Logs", None, "Quit"]
        self.paused = False
        threading.Thread(target=self.update_state, daemon=True).start()

    @rumps.clicked("Open Dashboard")
    def open_dash(self, _):
        webbrowser.open("http://localhost:8080")

    @rumps.clicked("Pause Monitoring")
    def toggle_pause(self, sender):
        self.paused = not self.paused
        sender.title = "Resume Monitoring" if self.paused else "Pause Monitoring"
        status = "Paused monitoring." if self.paused else "Resumed monitoring."
        rumps.notification("Emotion Monitor", "Status Update", status)
        print(f"[INFO] {status}")

    @rumps.clicked("View Logs")
    def view_logs(self, _):
        os.system(f"open -a TextEdit {LOG_FILE}")

    @rumps.clicked("Quit")
    def quit_app(self, _):
        print("[INFO] Exiting Emotion Monitor.")
        rumps.quit_application()

    def update_state(self):
        while True:
            if not self.paused:
                with data_lock:
                    e = stats["emotion"]
                    c = stats["confidence"]
                    self.title = f"🧠 {e} ({c}%)"
            else:
                self.title = "⏸️ Paused"
            time.sleep(5)

# --- Launch ---
if __name__ == "__main__":
    print("[INFO] Starting Emotion + Activity Monitor (v9 - Final Stable Edition)...")

    app_inst = NSApplication.sharedApplication()
    NSApp = app_inst
    app_inst.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    threading.Thread(target=lambda: flask_app.run(port=8080, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=analyzer_loop, daemon=True).start()

    MenuBar().run()


import os, time, threading, random, datetime, webbrowser, json, rumps
from flask import Flask, jsonify, render_template_string
from AppKit import NSApplication, NSApp, NSApplicationActivationPolicyAccessory

# --- Setup ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "session_log.txt")
BASELINE_FILE = os.path.join(LOG_DIR, "baseline.json")

flask_app = Flask(__name__)
data_lock = threading.Lock()

# --- Global state ---
stats = {
    "emotion": "Calibrating...",
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

is_calibrating = True
calibration_data = []
avg_kpm = 100
avg_mouse = 5000
paused_monitoring = False

# --- Load baseline ---
if os.path.exists(BASELINE_FILE):
    try:
        with open(BASELINE_FILE, "r") as f:
            baseline = json.load(f)
            avg_kpm = baseline.get("avg_kpm", avg_kpm)
            avg_mouse = baseline.get("avg_mouse", avg_mouse)
            is_calibrating = False
            print(f"[INFO] Loaded baseline: avg_kpm={avg_kpm}, avg_mouse={avg_mouse}")
    except Exception as e:
        print(f"[WARN] Failed to load baseline: {e}")

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
#pausedOverlay{
position:absolute;top:50%%;left:50%%;transform:translate(-50%%,-50%%);
font-size:1.2em;color:#ff6666;background:rgba(0,0,0,0.7);
padding:10px 20px;border-radius:10px;display:none;
}
.container{position:relative;display:inline-block;}
</style></head><body>
<h2>🧠 Emotion + Activity Monitor</h2>
<div id="stats">Loading...</div>
<div class="container">
<canvas id="chart"></canvas>
<div id="pausedOverlay">⏸ Monitoring Paused</div>
</div>
<div class="legend">
<div><span class="color-box" style="background:#00ff66"></span>Focused</div>
<div><span class="color-box" style="background:#FFD700"></span>Normal</div>
<div><span class="color-box" style="background:#0096FF"></span>Tired</div>
<div><span class="color-box" style="background:#FF4040"></span>Stressed</div>
</div>
<script>
let paused=false;
const overlay=document.getElementById('pausedOverlay');
const ctx=document.getElementById('chart').getContext('2d');
const data={labels:[],datasets:[{label:'Keystrokes/min',data:[],borderColor:'#FFD700',backgroundColor:'rgba(255,215,0,0.25)',fill:true,tension:.3}]};
const chart=new Chart(ctx,{type:'line',data:data,options:{animation:{duration:800},scales:{x:{ticks:{color:'#aaa'}},y:{ticks:{color:'#aaa'}}}}});

async function fetchData(){
try{
const r=await fetch('/api/stats');const d=await r.json();
paused=d.paused;
overlay.style.display=paused?'block':'none';
document.getElementById('stats').innerHTML=`Emotion:<b style="color:${d.color}">${d.emotion}</b> (${d.confidence}%) | KPM:${d.kpm} | Mouse:${d.mouse} | Clicks:${d.clicks}`;
if(!paused){
if(data.labels.length>40){data.labels.shift();data.datasets[0].data.shift();}
data.labels.push(d.timestamp);data.datasets[0].data.push(d.kpm);
data.datasets[0].borderColor=d.color;data.datasets[0].backgroundColor=d.color+'40';
chart.update();
}
}catch(e){document.getElementById('stats').innerText='⚠️ Waiting for live data...';}}
setInterval(fetchData,10000);fetchData();
</script></body></html>"""

@flask_app.route("/")
def dashboard():
    return render_template_string(HTML_DASHBOARD)

@flask_app.route("/api/stats")
def api_stats():
    with data_lock:
        return jsonify(stats | {"color": emotion_colors.get(stats["emotion"], "#FFD700"), "paused": paused_monitoring})

# --- Simulation ---
def simulate():
    global avg_kpm, avg_mouse, is_calibrating
    modes = [
        ("Coding", random.randint(180, 280), random.randint(4000, 8000), random.randint(30, 80)),
        ("Browsing", random.randint(30, 90), random.randint(7000, 16000), random.randint(5, 25)),
        ("Call", random.randint(5, 25), random.randint(1000, 4000), random.randint(0, 10)),
        ("Idle", random.randint(0, 10), random.randint(0, 1000), random.randint(0, 5))
    ]
    mode, kpm, mouse, clicks = random.choices(modes, weights=[0.4, 0.35, 0.15, 0.1])[0]
    if is_calibrating:
        calibration_data.append((kpm, mouse))
        if len(calibration_data) >= 12:
            avg_kpm = sum(k for k, _ in calibration_data)/len(calibration_data)
            avg_mouse = sum(m for _, m in calibration_data)/len(calibration_data)
            is_calibrating=False
            with open(BASELINE_FILE,"w") as f: json.dump({"avg_kpm":avg_kpm,"avg_mouse":avg_mouse},f)
            print(f"[CALIBRATED] Saved baseline: avg_kpm={int(avg_kpm)}, avg_mouse={int(avg_mouse)}")
        return "Calibrating...",0,kpm,mouse,clicks
    avg_kpm=(avg_kpm*0.9)+(kpm*0.1);avg_mouse=(avg_mouse*0.9)+(mouse*0.1)
    if kpm>avg_kpm*1.2 and mouse>avg_mouse*0.5: e="Focused"
    elif avg_kpm*0.5<kpm<=avg_kpm*1.2: e="Normal"
    elif kpm<avg_kpm*0.5 and mouse<avg_mouse*0.5: e="Tired"
    else: e="Stressed"
    return e,random.randint(75,98),kpm,mouse,clicks

# --- Analyzer Loop ---
def analyzer_loop():
    global paused_monitoring
    last_notified=0
    while True:
        if not paused_monitoring:
            e,c,k,m,cl=simulate()
            ts=datetime.datetime.now().strftime("%H:%M:%S")
            with data_lock: stats.update({"emotion":e,"confidence":c,"kpm":k,"mouse":m,"clicks":cl,"timestamp":ts})
            with open(LOG_FILE,"a") as f: f.write(f"[{ts}] {e}({c}%) KPM={k} Mouse={m} Clicks={cl}\n")
            now=time.time()
            if e in ["Tired","Stressed"] and now-last_notified>=random.randint(420,480):
                msg={"Tired":("😴 Take a short break","You seem tired.","Drink water or relax for a minute."),
                     "Stressed":("⚠️ Time for a break!","You seem stressed.","Stretch or rest your eyes.")}
                title,sub,msg_body=msg[e];rumps.notification(title,sub,msg_body);last_notified=now
        time.sleep(15)

# --- Menubar App ---
class MenuBar(rumps.App):
    def __init__(self):
        super(MenuBar,self).__init__("🧠 Calibrating...")
        self.menu=["Open Dashboard",None,"Pause Monitoring","Recalibrate","View Logs",None,"Quit"]
        threading.Thread(target=self.update_state,daemon=True).start()
    @rumps.clicked("Open Dashboard") 
    def dash(self,_): webbrowser.open("http://localhost:8080")
    @rumps.clicked("Pause Monitoring")
    def toggle(self,sender):
        global paused_monitoring
        paused_monitoring=not paused_monitoring
        sender.title="Resume Monitoring" if paused_monitoring else "Pause Monitoring"
        status="Paused monitoring." if paused_monitoring else "Resumed monitoring."
        print(f"[INFO] {status}");rumps.notification("Emotion Monitor","Status Update",status)
    @rumps.clicked("Recalibrate")
    def recal(self,_):
        global calibration_data,is_calibrating
        calibration_data.clear();is_calibrating=True
        if os.path.exists(BASELINE_FILE): os.remove(BASELINE_FILE)
        rumps.notification("Emotion Monitor","Calibration Reset","Recalibrating your personal baseline...")
    @rumps.clicked("View Logs")
    def logs(self,_): os.system(f"open -a TextEdit {LOG_FILE}")
    @rumps.clicked("Quit")
    def quit_app(self,_): print("[INFO] Exiting Emotion Monitor.");rumps.quit_application()
    def update_state(self):
        while True:
            with data_lock:
                if paused_monitoring: self.title="⏸️ Paused"
                elif is_calibrating: self.title="⚙️ Calibrating..."
                else: e=stats["emotion"];c=stats["confidence"];self.title=f"🧠 {e} ({c}%)"
            time.sleep(5)

# --- Launch ---
if __name__=="__main__":
    print("[INFO] Starting Emotion + Activity Monitor (v10.4 - Paused Overlay Edition)...")
    app_inst=NSApplication.sharedApplication();NSApp=app_inst
    app_inst.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    threading.Thread(target=lambda: flask_app.run(port=8080,debug=False,use_reloader=False),daemon=True).start()
    threading.Thread(target=analyzer_loop,daemon=True).start()
    MenuBar().run()

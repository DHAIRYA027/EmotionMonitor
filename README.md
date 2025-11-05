<div align="center">

# 🧠 Emotion + Activity Monitor

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Framework-black?logo=flask)
![macOS](https://img.shields.io/badge/macOS-Compatible-lightgrey?logo=apple)
![AI/ML](https://img.shields.io/badge/AI%2FML-Emotion%20Detection-orange?logo=tensorflow)
![Status](https://img.shields.io/badge/Version-v10_Final-green)

### _Smart Stress & Focus Detection for macOS_
A real-time emotion and activity tracker that monitors keyboard and mouse usage to determine focus, tiredness, or stress levels — displayed via a live dashboard and menu-bar integration.

</div>

---

## ⚙️ Overview
**Emotion + Activity Monitor** uses behavioral data (keystrokes, mouse activity) to estimate emotional state and alert users when they may need a break. It’s built for students, developers, and remote workers who spend long hours at their Mac.

---

## ✨ Features

- 🧮 **Real-time activity tracking** – keyboard + mouse event analysis  
- 🎯 **Emotion inference** – detects *Focused, Normal, Tired,* or *Stressed* states  
- 🌈 **Color-coded dashboard** – gradient graph with emotion colors  
- 🧠 **Smart notifications** – alerts every 7–8 minutes *only* when stressed or tired  
- ⏸ **Pause/Resume** – control monitoring directly from the menu bar  
- 🧍 **Menubar-only app** – runs silently without Dock icon  
- 📈 **Auto-updating dashboard** – updates every 10 seconds with live data

---

## 🧰 Tech Stack

| Component | Technology |
|------------|-------------|
| **Language** | Python 3.11+ |
| **Frontend Dashboard** | Flask + HTML5 + Chart.js |
| **Desktop Integration** | Rumps (menu bar) + AppKit (macOS native) |
| **Data Collection** | pynput (keyboard, mouse) |
| **Visualization** | Plotly / Matplotlib |
| **Notifications** | macOS System Alerts |

---

## 🖥️ Live Dashboard Preview

> Displays a dynamic graph showing recent emotional trends, activity intensity, and emotion percentages.  
> Automatically syncs with monitoring data and pauses when monitoring is stopped.

| Emotion Graph | Activity Trend | Notifications |
|----------------|----------------|----------------|
| ![Graph](docs/screenshots/3_dashboard.png) | ![Focused](docs/screenshots/1_focused.png) | ![Tired Alert](docs/screenshots/2_tired.png) |

---

## 🧮 Version Timeline

| Version | Highlights |
|----------|-------------|
| **v4** | First working menubar prototype |
| **v6.2** | Improved UI and smoother live graph |
| **v7** | Emotion-based graph coloring + emoji state indicator |
| **v9** | macOS notifications + background run |
| **v10 (Final)** | Smart cooldown, accurate detection, and pause-sync |

---

## 🚀 Setup & Run

```bash
# 1️⃣ Clone the repository
git clone https://github.com/DHAIRYA027/EmotionMonitor.git
cd EmotionMonitor

# 2️⃣ Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # on macOS/Linux

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Run the latest build
python3 emotionMonitor_v10.py
```

📍 Dashboard: [http://127.0.0.1:8080](http://127.0.0.1:8080)

---

## 🧠 Future Enhancements
- 🔊 Add ambient sound cues for stress feedback  
- 🌐 Cloud sync of emotion data history  
- 📱 Mobile companion app for session tracking  
- 🤖 Optional integration with Apple Health or smartwatch sensors  

---

<div align="center">
Made with ❤️ for productivity and balance.  
</div>

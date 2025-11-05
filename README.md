# 🧠 Emotion + Activity Monitor (macOS)

Real-time emotion, stress, and activity detection using keystrokes and mouse dynamics.  
Designed as a sleek macOS menubar app with a live dashboard and intelligent rest notifications.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![UI](https://img.shields.io/badge/UI-Dark--Mode-black)
![Model](https://img.shields.io/badge/AI-XGBoost%20%2B%20Scikit--Learn-green)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

✅ Real-time emotion & activity detection  
✅ Animated gradient dashboard (dark mode)  
✅ Intelligent break reminders (stressed/tired detection)  
✅ Focus Mode toggle in menubar  
✅ Rest timer widget with countdown  
✅ No Dock icon — true background macOS app  
✅ Lightweight, uses local XGBoost & Scikit-learn models  

---

## ⚙️ Installation

```bash
git clone https://github.com/<your-username>/emotion-monitor.git
cd emotion-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 Running the App

```bash
python3 emotion_menubar_dashboard_app_v4.py
```

Once launched, you’ll see a 🧠 icon appear in your macOS menu bar.  
Dashboard available at [http://localhost:8080](http://localhost:8080)

---

## 🌙 Dashboard Preview

You can add a screenshot here (e.g. `Screenshot 2025-11-05 at 00.30.14.png`).

---

## 📂 Folder Structure

```
emotion-monitor/
│
├── emotion_menubar_dashboard_app_v4.py
├── model/
├── venv/
├── README.md
└── requirements.txt
```

---

## 🧠 Tech Stack

- **Python 3.10+**
- **rumps** — macOS menubar integration  
- **pynput** — keystroke & mouse tracking  
- **scikit-learn**, **xgboost** — ML models  
- **joblib**, **numpy** — data handling  
- **Chart.js** — live emotion trend visualization  

---

## 🧘 Notifications

Smart notifications suggest breaks when stress or fatigue is detected.  
All messages are contextual (e.g., *“Feeling tired while coding? Time to stretch!”*).

Focus mode can be toggled to temporarily mute notifications.

---

## 📜 License

**MIT License © 2025 Dhairya Prabhakar**  
Free to use, modify, and distribute with attribution.

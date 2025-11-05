from setuptools import setup

APP = ['emotionMonitor_v9.py']
DATA_FILES = ['dashboard.html', 'app_icon.icns']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['rumps', 'pynput', 'flask'],
    'iconfile': 'app_icon.icns',
    'plist': {
        'CFBundleName': 'Emotion Monitor',
        'CFBundleDisplayName': 'Emotion Monitor',
        'CFBundleIdentifier': 'com.dhairya.emotionmonitor',
        'LSUIElement': True
    }
}

setup(
    app=APP,
    name="Emotion Monitor",
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

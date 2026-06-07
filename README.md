# FocusFlow — Deep Work Tracker

**Version 1.0**

A lightweight desktop app for tracking deep work sessions from the system tray. FocusFlow helps you log study time, stay consistent with streaks and weekly goals, and review your progress with heatmaps and weekly breakdowns.

## Screenshot

<!-- Add a screenshot here -->
![FocusFlow dashboard](docs/screenshot.png)

## Features

- **System tray integration** — run in the background; tray icon switches between dark (idle) and coral (active session)
- **Windows taskbar & title bar icons** — same icon set as the tray, updated in sync when a session starts or ends
- **Session timer** — start, pause, resume, and stop study sessions with subject and quick notes
- **Quick start** — one-click free-topic sessions with auto-generated names
- **Pause & resume** — manual pause plus auto-pause after configurable inactivity
- **Keyboard shortcuts** — `Ctrl+Shift+Q` quick start, `Ctrl+Shift+P` pause/resume, `Ctrl+Shift+D` stop
- **SQLite persistence** — local session history stored on your machine
- **Dashboard** — live timer, weekly bar chart, streak counter, and weekly goal progress
- **Recent sessions log** — table with day, subject, duration, and notes
- **Statistics page** — three-month activity heatmaps and expandable weekly day breakdown
- **Streak tracking** — consecutive study days updated automatically
- **Weekly goal** — configurable hour target with progress bar
- **Dark mode** — toggle in Settings; warm dark palette across the full UI
- **Settings** — weekly goal, inactivity timeout, and dark mode
- **Sounds & notifications** — audio cues and Windows toast on session events
- **Single-instance lock** — prevents duplicate tray icons
- **CustomTkinter UI** — warm light and dark themes with themed dialogs

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/MateoRedD/focusflow.git
cd focusflow
```

### 2. Install dependencies

Requires **Python 3.10+** on Windows.

```bash
python -m pip install -r requirements.txt
```

### 3. Run the app

```bash
python main.py
```

FocusFlow starts in the system tray. Double-click the tray icon or use **Abrir ventana** to open the dashboard.

## Tech stack

- **Python 3**
- **CustomTkinter** — modern desktop UI
- **pystray** — system tray icon and menu
- **SQLite** — local data storage
- **Pillow** — tray and window icon rendering
- **winotify** — Windows notifications
- **winsound** — session sound cues

## License

Personal project — use and modify as you like.

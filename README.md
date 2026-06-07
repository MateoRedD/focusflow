# FocusFlow — Deep Work Tracker

**Version 1.0**

A lightweight desktop app for tracking deep work sessions from the system tray. FocusFlow helps you log study time, stay consistent with streaks and weekly goals, and review your progress with heatmaps and weekly breakdowns.

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

## 📋 Requirements

- **Node.js 18 or later** — [Download from nodejs.org](https://nodejs.org/)
- **Python 3.10 or later** — required to run the app (`npm start` calls Python under the hood)
- **Windows 10/11**
- **npm** — included with Node.js

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/MateoRedD/focusflow.git
cd focusflow
```

### 2. Install Node.js (if needed)

Download and install the LTS version from **[nodejs.org](https://nodejs.org/)**.  
After installing, open a new terminal and verify:

```bash
node -v
npm -v
```

### 3. Install dependencies

This installs Node packages and Python packages (`requirements.txt`) automatically:

```bash
npm install
```

If `postinstall` fails, install Python dependencies manually:

```bash
python -m pip install -r requirements.txt
```

### 4. Run the app

```bash
npm start
```

FocusFlow starts in the system tray. Double-click the tray icon or use **Abrir ventana** to open the dashboard.

### Optional — create a Desktop shortcut

Creates a **FocusFlow** shortcut on your Desktop (no terminal window):

```bash
node create-shortcut.js
```

No npm? Use PowerShell instead:

```powershell
powershell -ExecutionPolicy Bypass -File create-shortcut.ps1
```

You can also double-click **`FocusFlow.vbs`** or **`FocusFlow.bat`** in the project folder.

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

# ⚡ Planner V8 README: Command Planner — Qt Quick & QML Edition

[![Python Version](https://img.shields.io/badge/Python-3.10%2B%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/Frontend-PySide6%20%2F%20Qt%20Quick%20(QML)-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://www.qt.io/)
[![Architecture](https://img.shields.io/badge/Architecture-MVC%20Decoupled-blueviolet?style=for-the-badge)](https://github.com/Rajratna-D/PLANNER-APP)
[![Visualization](https://img.shields.io/badge/Graphics-Native%20GPU%20QML%20Canvas-11557c?style=for-the-badge)](https://doc.qt.io/qt-6/qml-qtquick-canvas.html)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](../LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)](https://github.com/Rajratna-D/PLANNER-APP)

> **Planner V8.0** marks the most ambitious milestone in the Command Planner project. Completely redesigned from the ground up, V8 transitions the entire platform from legacy procedural Tkinter scripts to an enterprise-grade **Model-View-Controller (MVC)** architecture powered by **PySide6** (Qt for Python) and **Qt Quick / QML**.

---

## 📑 Table of Contents

- [Executive Summary: The Generational Leap](#-executive-summary-the-generational-leap)
- [System Architecture (MVC)](#-system-architecture-mvc)
- [Comprehensive Module Walkthrough (10 QML Tabs)](#-comprehensive-module-walkthrough-10-qml-tabs)
  - [1. ⬡ OverviewTab.qml](#1-⬡-overviewtabqml)
  - [2. ◈ TestsTab.qml](#2-◈-teststabqml)
  - [3. ▣ TasksTab.qml](#3-▣-taskstabqml)
  - [4. ◫ ListsTab.qml](#4-◫-liststabqml)
  - [5. ◧ AssignmentsTab.qml](#5-◧-assignmentstabqml)
  - [6. ◩ PracticalsTab.qml](#6-◩-practicalstabqml)
  - [7. ⬢ SyllabusTab.qml](#7-⬢-syllabustabqml)
  - [8. ◎ PomodoroTab.qml](#8--pomodorotabqml)
  - [9. ✎ NotesTab.qml](#9--notestabqml)
  - [10. ◐ ProductivityTab.qml](#10--productivitytabqml)
- [Reusable QML Component Primitives](#-reusable-qml-component-primitives)
- [Migration Guide: V7.x (CustomTkinter) ➔ V8.0 (PySide6 / QML)](#-migration-guide-v7x-to-v80)
- [Data Layer, Atomic Persistence & Disaster Recovery](#-data-layer-atomic-persistence--disaster-recovery)
- [Getting Started & Installation](#-getting-started--installation)
- [Directory Structure](#-directory-structure)
- [License](#-license)

---

## 🚀 Executive Summary: The Generational Leap

In versions 1 through 7, Command Planner pushed procedural Tkinter and CustomTkinter to its absolute limit (reaching 3,139 lines in V7.4.5). However, monolithic scripts faced inherent architectural barriers: GUI thread locking, Matplotlib rendering latency, and cascading UI coupling.

**Planner V8.0 fundamentally solves these challenges:**
- **Hardware-Accelerated Qt Quick / QML**: Renders via OpenGL/DirectX/Vulkan/Metal, delivering 60+ FPS fluid animations and responsive layout scaling across 4K displays.
- **Strict Decoupled MVC**: The presentation layer (`.qml`) has zero knowledge of file I/O or storage, communicating solely through typed Qt Signals, Slots, and Properties.
- **Native Canvas Visualizations**: Fully discarded Matplotlib in favor of native QML `Canvas` 2D rendering for instantaneous, pixel-perfect spider charts and activity heatmaps.
- **Atomic Data Engine**: Safe state serialization ensuring zero file corruption even during unexpected system power downs.

---

## 🏛️ System Architecture (MVC)

```
┌────────────────────────────────────────────────────────┐
│                      VIEW LAYER                        │
│          Qt Quick / QML Declarative Interface          │
│                                                        │
│  ┌─────────────────┐ ┌──────────────────────────────┐  │
│  │    Main.qml     │ │        qml/tabs/             │  │
│  │  (App Shell &   │ │  (Overview, Tasks, Tests,    │  │
│  │   Navigation)   │ │   Pomodoro, Analytics, etc.) │  │
│  └────────┬────────┘ └──────────────┬───────────────┘  │
│           │                         │                  │
│           └────────────┬────────────┘                  │
│                        │ QML Property / Signal Bridge  │
└────────────────────────┼───────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────────┐
│                   CONTROLLER LAYER                     │
│               main.py (PlannerBridge)                  │
│                                                        │
│  • Qt Signals & Slots      • Non-blocking Timers       │
│  • QML Property Exposing   • Event Dispatcher          │
│  • Audio playback threads  • Auto-save Loop            │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│                      MODEL LAYER                       │
│                   planner_backend.py                   │
│                                                        │
│  • CRUD Business Logic     • Date & Urgency Math       │
│  • JSON Schema Validation  • Rolling Backup Engine     │
│  • Streak & Score Math     • Atomic File Swapping      │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
             [ planner_data.json ] ──► [ backups/ ]
```

---

## 🔍 Comprehensive Module Walkthrough (10 QML Tabs)

### 1. ⬡ OverviewTab.qml
The high-altitude command center:
- **KPI Metrics Grid**: 6 responsive metric cards displaying real-time counts for tests, tasks, assignments, practicals, subjects, and today's Pomodoro sessions.
- **Action Dashboard**: Two-column layout featuring upcoming tests with live urgency badges, top priority tasks, and assignment deadlines.
- **Urgent Action Panels**:
  - 🔴 **Due Today & Overdue**: Highlights immediate deadlines in vibrant red cards.
  - 🟡 **Due Tomorrow**: Proactive 24-hour head-up display.
- **Miniature Spider Radar**: Native QML canvas radial chart rendering current weekly focus balance directly on the home screen.

### 2. ◈ TestsTab.qml
Academic evaluation and exam milestone tracker:
- **Date Arithmetic Engine**: Calculates exact remaining days (`TODAY`, `TOMORROW`, `X d`, `PAST`).
- **Dynamic Urgency Palette**: Real-time color shifts from Green (>7 days) down to Gold (≤7 days), Orange (≤2 days), and Red (0 days).
- **Fast Entry Bar**: Form inputs for Subject, Date (`YYYY-MM-DD`), Time (`HH:MM`), and optional syllabus notes.

### 3. ▣ TasksTab.qml
Multi-tiered task management workstation:
- **5-Tier Priority Classification**:
  - `Immediate` (Crimson Red `#FF3358`)
  - `Important` (Amber Orange `#FF9020`)
  - `2nd Priority` (Electric Blue `#3D8EFF`)
  - `3rd Priority` (Emerald Green `#2EE87A`)
  - `Someday` (Muted Slate `#5E6A90`)
- **Automated Recurrence Engine**: Automatically spawns the next occurrence (`Daily`, `Weekly`, `Monthly`) when an existing recurring item is checked off.
- **Sorting & Quick Filter Toolbar**: Filter by priority level with dedicated neon badges, or sort by Priority, Due Date, or Added Date.
- **Completed Archive**: Smooth strikethrough styling and historical count.

### 4. ◫ ListsTab.qml
Customizable project boards and checklist tracker:
- Dynamic checklist creation with custom titles (e.g., *Project Roadmaps*, *Reading Lists*).
- Real-time animated progress bars displaying completion ratio (`X / Y`).
- Item-level checkboxes with strike-through animations and one-click item removal.

### 5. ◧ AssignmentsTab.qml
Coursework and submission deadline tracker:
- Tracks Subject, Assignment Title, Due Date, and Weightage/Marks.
- Overdue notification tags and urgency calculation.
- One-click **✓ SUBMITTED** transition archiving submissions into a dedicated completed drawer.

### 6. ◩ PracticalsTab.qml
Designed specifically for lab courses and STEM curricula:
- Tracks Experiment Number, Title, Subject, and Lab Date.
- **3-Stage Milestone Workflow**:
  - `[P]` **Performed**: Lab experiment conducted.
  - `[W]` **Writeup Done**: Calculations and observations verified.
  - `[S]` **Submitted**: Journal signed off.
- Automatic completion detection when all 3 states are verified.

### 7. ⬢ SyllabusTab.qml
Comprehensive course curriculum coverage manager:
- Multi-subject creation with subject color accents.
- Responsive 2-column topic grid with interactive checkboxes.
- Real-time percentage calculation updating smooth progress bars as topics are marked complete.

### 8. ◎ PomodoroTab.qml
Deep-work focus workstation:
- **Interval Control**: Configurable Focus duration (default: 25 min), Short Break (5 min), and Long Break (15 min after 4 sessions).
- **Smooth Arc Progress**: Hardware-accelerated timer visualization displaying exact countdown minutes and seconds.
- **Task Association**: Dropdown linking current timer session directly to any pending task.
- **Sound Alerts**: Native Windows audio chime triggers upon session milestones via non-blocking background threads.
- **Session Log**: Chronological daily table tracking session type, timestamp, linked task, and duration.

### 9. ✎ NotesTab.qml
Dual-pane markdown-ready knowledge repository:
- **Left Panel**: Master note list with real-time text search across titles, subjects, and body text.
- **Right Panel**: Full-featured note editor with title input, subject category selector, and last-edited timestamp.
- Instant auto-saving and deletion safety.

### 10. ◐ ProductivityTab.qml
Enterprise-grade focus analytics suite:
- **Daily Goal Setter**: Configurable daily session target dial (default: 6 sessions).
- **Dynamic Productivity Score**: Algorithmic score calculated from daily output (0–100) with rating bands (*EXCELLENT*, *GOOD*, *AVERAGE*, *NEEDS WORK*).
- **52-Week Contribution Heatmap**: Native QML Canvas implementation mapping full-year focus activity with 4 saturation levels and month labels.
- **Native Spider Radar Chart**: 7 radial spokes (Mon–Sun) comparing this week's focus distribution against last week's baseline with glowing paths and vertex halos.
- **Peak Focus Hours**: 24-hour hourly distribution identifying peak productive periods throughout the day.
- **Week-over-Week Delta Metrics**: Comparative delta badges showing session changes (+/-).

---

## 🧩 Reusable QML Component Primitives

All UI elements are organized into modular, reusable primitives in [`qml/components/`](qml/components):

| Component | File | Description |
|---|---|---|
| **GitHub Heatmap** | `GitHubHeatmap.qml` | 52-week activity contribution grid rendered on QML Canvas |
| **Spider Chart** | `SpiderChart.qml` | 7-axis Kiviat radar chart with glowing polygons and labels |
| **Premium Card** | `PremiumCard.qml` | Elevated container with customizable accent bars & hover effects |
| **Action Button** | `ActionButton.qml` | Standardized push button with hover states and custom colors |
| **Delete Button** | `DeleteButton.qml` | Two-step confirmation button preventing accidental deletes |
| **Input Field** | `InputField.qml` | Modern input field with placeholder text and focus rings |
| **Toast Popup** | `ToastPopup.qml` | Non-blocking sliding notification banner with auto-dismiss |

---

## 📊 Migration Guide: V7.x to V8.0

| Feature | Planner V7.4.5 (Legacy) | Planner V8.0 (Modern) |
|---|---|---|
| **UI Framework** | CustomTkinter (Procedural) | **PySide6 / Qt Quick QML (Declarative)** |
| **Architecture** | Single-file monolith (3,139 lines) | **Decoupled MVC (20+ modular files)** |
| **Chart Visualization** | Matplotlib via TkAgg | **Native QML Canvas 2D API (Hardware Accelerated)** |
| **Rendering Engine** | Software-rendered Tk | **GPU Hardware Accelerated (OpenGL / DirectX / Metal)** |
| **Code Modularity** | All tabs defined in one class | **Each tab in an independent `.qml` file** |
| **UI Threading** | Risk of mainloop lag | **Separate QML scene graph rendering thread** |
| **Memory Footprint** | Heavy (Matplotlib dependencies) | **Lightweight native Qt Quick primitives** |

---

## 💾 Data Layer, Atomic Persistence & Disaster Recovery

### Schema Integrity
All user state is managed in `planner_data.json` with deterministic UUID keys:
```json
{
  "tests": [...],
  "tasks": [...],
  "lists": [...],
  "assignments": [...],
  "practicals": [...],
  "syllabus": [...],
  "pomodoro_log": [...],
  "notes": [...],
  "streak": { "last_date": "2026-09-11", "count": 7 },
  "daily_goal": 6,
  "theme": "dark",
  "subject_colors": { "CS101": "#00C8F0" }
}
```

### Reliability Guarantees
- **Atomic File Swapping**: Application writes state to `planner_data.json.tmp` before atomically replacing `planner_data.json`, preventing partial-write file corruption.
- **Rolling Archival Backups (`/backups`)**: Generates timestamped snapshots on launch (`backup_YYYYMMDD_HHMMSS.json`) and automatically prunes to keep the last 30 backups.
- **60-Second Auto-Save Daemon**: State is continuously synchronized via non-blocking `QTimer`.

---

## 🚀 Getting Started & Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or **Python 3.14**
- Git

### 1. Install Dependencies
```bash
pip install PySide6
```

*(Note: Matplotlib and CustomTkinter are no longer required in V8.0!)*

### 2. Launch Planner V8
```bash
# Navigate to the Planner V8 directory
cd "Planner V8"

# Launch the application
python main.py
```

---

## 📁 Directory Structure

```
Planner V8/
├── Planner V8 README.md      # Comprehensive V8 Documentation
├── main.py                   # PySide6 Application Bridge & Entry Point
├── planner_backend.py        # Core Business Logic & State Controller
├── planner_data.json         # Local JSON State Database
└── qml/                      # Qt Quick Declarative Interface
    ├── Main.qml              # Application Window Shell & Navigation
    ├── components/           # Reusable QML Widget Library
    │   ├── ActionButton.qml  # Custom Interactive Button
    │   ├── DeleteButton.qml  # Two-Step Safety Delete Button
    │   ├── GitHubHeatmap.qml # 52-Week Focus Contribution Heatmap
    │   ├── InputField.qml    # Styled Input Field
    │   ├── PremiumCard.qml   # Elevated Surface Card
    │   ├── SpiderChart.qml   # Kiviat Radar Polygon Canvas
    │   └── ToastPopup.qml    # Non-blocking Animated Toast Banner
    └── tabs/                 # Modular Application Tab Views
        ├── AssignmentsTab.qml# Coursework & Deadline Tracking
        ├── ListsTab.qml      # Checklist & Project Management
        ├── NotesTab.qml      # Dual-Pane Searchable Knowledge Base
        ├── OverviewTab.qml   # Command Dashboard & Urgent Alerts
        ├── PomodoroTab.qml   # Focus Timer & Audio Alert Engine
        ├── PracticalsTab.qml # 3-Stage Laboratory Experiment Tracker
        ├── ProductivityTab.qml # Heatmap, Radar & Peak Hours Analytics
        ├── SyllabusTab.qml   # Subject Coverage & Progress Bars
        ├── TasksTab.qml      # 5-Tier Priority Tasks & Recurrence
        └── TestsTab.qml      # Exam Countdown & Urgency Badges
```

---

## 📄 License

This project is licensed under the [MIT License](../LICENSE) — see the LICENSE file for details.

*Command Planner V8: Engineered for elite productivity.*

# 🪐 Planner V6 README: Command Planner — PrinceBlue Edition

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Visualization](https://img.shields.io/badge/Charts-Matplotlib%20Kiviat-11557c?style=for-the-badge)](https://matplotlib.org/)
[![Notifications](https://img.shields.io/badge/Alerts-Plyer-orange?style=for-the-badge)](https://github.com/kivy/plyer)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)](https://github.com/Rajratna-D/PLANNER-APP)

> **Planner V6** (codename *Command Planner — PrinceBlue*) is an all-in-one, high-performance desktop productivity workstation engineered for students, engineers, and power users. Built natively on Python and modern CustomTkinter widgetry, it combines rigorous academic tracking, task scheduling, a threaded Pomodoro engine, and data visualization via custom Kiviat radar charts.

---

## 📑 Table of Contents

- [Key Highlights](#-key-highlights)
- [Architecture & Design System](#-architecture--design-system)
- [Comprehensive Module Walkthrough](#-comprehensive-module-walkthrough)
  - [1. ⬡ Overview Dashboard](#1-⬡-overview-dashboard)
  - [2. ◈ Tests & Exam Schedule](#2-◈-tests--exam-schedule)
  - [3. ▣ Task Engine with Recurrence](#3-▣-task-engine-with-recurrence)
  - [4. ◫ Lists & Workflows](#4-◫-lists--workflows)
  - [5. ◧ Assignment Tracker](#5-◧-assignment-tracker)
  - [6. ◩ Practicals & Laboratory Milestones](#6-◩-practicals--laboratory-milestones)
  - [7. ⬢ Syllabus Coverage Manager](#7-⬢-syllabus-coverage-manager)
  - [8. ◎ Pomodoro Workstation](#8--pomodoro-workstation)
  - [9. ✎ Knowledge Base & Notes](#9--knowledge-base--notes)
  - [10. ◐ Focus & Productivity Analytics](#10--focus--productivity-analytics)
- [Data Layer & Reliability](#-data-layer--reliability)
- [Getting Started & Installation](#-getting-started--installation)
- [Usage & Workflows](#-usage--workflows)
- [Repository Structure](#-repository-structure)
- [Version History & Evolution](#-version-history--evolution)
- [License](#-license)

---

## ⚡ Key Highlights

- **Sleek Cyber-Dark Aesthetic**: Custom "PrinceBlue" palette featuring high-contrast neon accents (Cyan, Gold, Violet, Pink, Green, Orange) and smooth dark/light mode toggle.
- **10 Integrated Productivity Modules**: From daily tasks and recurring routines to laboratory practicals and syllabus tracking.
- **Kiviat Polygon Focus Radar**: Bespoke multi-ring radial radar charts comparing this week's focus distribution against last week's baseline with glowing paths and vertex halos.
- **Threaded Pomodoro Engine**: Non-blocking asynchronous timer thread with automatic session logging, task-linking, and native cross-platform desktop notifications.
- **Automated Rolling Backups**: Guaranteed data safety with 60-second auto-saving and rolling 30-version snapshot retention.

---

## 🎨 Architecture & Design System

### Technology Stack
| Layer | Technology | Purpose |
|---|---|---|
| **Runtime** | Python 3.10+ | Core language runtime |
| **GUI Framework** | `customtkinter` | GPU-rendered modern widgets, rounded cards, adaptive frames |
| **Data Visualization** | `matplotlib` (`TkAgg`) | Custom radar charts, hourly histograms, comparative bar charts |
| **Desktop Alerts** | `plyer` | Native OS toast & notification center integration |
| **Data Engine** | `json` + `uuid` | Structured document database with deterministic IDs |
| **Thread Management** | `threading` | Background timer daemon preventing GUI lockups |

### Visual Identity (PrinceBlue Palette)
```
Background  : #07090E  (Deep Space Void)
Panel       : #0C0F18  (Sidebar & Nav)
Cards       : #111420  (Elevated Surfaces)
Borders     : #1F2540  (Subtle Dividers)
Accents     : Cyan (#00C8F0) | Gold (#FFCC44) | Orange (#FF9020)
              Red (#FF3358)  | Green (#2EE87A)| Violet (#9D7EFF) | Pink (#FF6EB0)
```

---

## 🔍 Comprehensive Module Walkthrough

### 1. ⬡ Overview Dashboard
The central command hub that synthesizes all application activity into actionable intelligence:
- **Time-Aware Greeting**: Dynamic banner reflecting the time of day alongside current daily study streak.
- **Real-Time KPI Counters**: Instant glance at pending tests, open tasks, unsubmitted assignments, incomplete practicals, syllabus count, and today's Pomodoro count.
- **Urgency Alert Panels**:
  - 🔴 **Due Today & Overdue**: Critical action list displaying past-due items in red.
  - 🟡 **Due Tomorrow**: Proactive 24-hour head-up display.
- **Miniature Radar Chart**: Live Kiviat visualization embedded directly into the overview for rapid assessment of weekly rhythm.

### 2. ◈ Tests & Exam Schedule
Never miss an examination or evaluation:
- **Precision Countdown**: Real-time date arithmetic computing exact days remaining (`TODAY`, `TOMORROW`, `X d`, `PAST`).
- **Urgency Tiers**: Dynamic color transitions from Green (>7 days) down to Gold (≤7 days), Orange (≤2 days), and Red (0 days).
- **Metadata Support**: Track subject code, scheduled date, exam time slot, and syllabus scope/notes.

### 3. ▣ Task Engine with Recurrence
Advanced task management built for high output:
- **5-Level Priority Hierarchy**:
  - `Immediate` (Flaming Red)
  - `Important` (Amber Orange)
  - `2nd Priority` (Electric Blue)
  - `3rd Priority` (Emerald Green)
  - `Someday` (Muted Slate)
- **Automated Recurrence Engine**: Set routines to `Daily`, `Weekly`, or `Monthly`. When marked complete, the engine automatically calculates the next due date and spawns the next instance.
- **Smart Filtering & Sorting**: Sort by Priority, Due Date, or Added Date; filter by priority tier on demand.
- **Archive & History**: Collapsible completed section with strikethrough typography and historical counts.

### 4. ◫ Lists & Workflows
Ad-hoc project boards and checklists:
- Create arbitrary named lists (e.g., *Exam Revision*, *Project Deliverables*, *Shopping*).
- Live visual progress bars displaying completed ratio (`X / Y`).
- Rapid-entry input fields with instant persistence.

### 5. ◧ Assignment Tracker
Academic and coursework deadline manager:
- Monitor subject, assignment title, due date, and weightage/marks.
- Color-coded deadline warnings that flag overdue submissions instantly.
- One-click **✓ SUBMITTED** transition with dedicated submitted archive.

### 6. ◩ Practicals & Laboratory Milestones
Designed specifically for STEM and lab-heavy curricula:
- Tracks Experiment Number, Title, Subject, and Lab Date.
- **Three-Stage Milestone Lifecycle**:
  - `[P]` **Performed**: Lab work conducted in the laboratory.
  - `[W]` **Writeup Done**: Observation journal and calculations drafted.
  - `[S]` **Submitted**: Final evaluation signed off by instructor.
- Automatic completion detection once all three states are verified.

### 7. ⬢ Syllabus Coverage Manager
Comprehensive curriculum coverage tracking:
- Add multiple subjects (e.g., *Engineering Physics*, *Discrete Mathematics*).
- Break down each course into individual chapters or topics.
- Interactive two-column checklist automatically recalculates overall subject coverage percentage with a responsive colored progress bar.

### 8. ◎ Pomodoro Workstation
Stay in deep focus with zero distraction:
- **Configurable Interval System**: Default 25-minute focus session, 5-minute short break, and 15-minute long break after 4 successful sessions.
- **Task Association**: Link your active Pomodoro timer directly to any open task from the Tasks module.
- **Asynchronous Daemon**: Runs on a background thread (`threading.Thread`) without freezing UI responsiveness.
- **Desktop Push Notifications**: Native OS alerts notifying you when focus periods end or break times expire via `plyer`.
- **Session History Log**: Daily chronological log displaying session type, start timestamp, linked task, and duration.

### 9. ✎ Knowledge Base & Notes
Integrated markdown-ready scratchpad:
- **Master-Detail Dual Pane**: Categorized list on the left with live snippet previews; full editor on the right.
- **Instant Search**: Real-time filtering across titles, content, and subject tags.
- **Subject Grouping**: Assign notes to specific courses or the `General` collection.
- **Audit Metadata**: Automatic tracking of creation date and last-modified timestamps.

### 10. ◐ Focus & Productivity Analytics
Quantitative self-reflection and performance metrics powered by `matplotlib`:
- **Daily Target Dial**: Set personal goals for sessions per day (default: 6 sessions).
- **Dynamic Productivity Score**: Algorithmic score calculated from daily output (0–100) with rating bands (*EXCELLENT*, *GOOD*, *AVERAGE*, *NEEDS WORK*).
- **Dual-Week Kiviat Spider Chart**:
  - 7 radial spokes representing Monday through Sunday.
  - This week's output plotted with a vivid glowing pink fill and path glow effects.
  - Last week's output mapped as a dashed ghost polygon for direct comparative analysis.
- **Peak Focus Hours Bar Chart**: 24-hour distribution identifying your most productive times of day (from 06:00 to 24:00) with heat-mapped gradient coloring.
- **Week-over-Week Delta Engine**: Side-by-side session comparisons highlighting volume change (+/-).
- **Streak Tracker**: Consecutive day counter rewarded for completing tasks or Pomodoro sessions daily.

---

## 💾 Data Layer & Reliability

### Storage Engine
Planner V6 stores all state in a human-readable, schema-validated JSON document (`planner_data.json`):
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
  "streak": { "last_date": "2026-09-11", "count": 5 },
  "daily_goal": 6,
  "theme": "dark"
}
```

### Safety Features
- **Non-Blocking Auto-Save**: An asynchronous timer automatically writes application state to disk every 60 seconds.
- **Rolling Backups (`/backups`)**: On launch and manual invocation, timestamped snapshots (`backup_YYYYMMDD_HHMMSS.json`) are preserved.
- **Auto-Pruning**: Automatically retains the latest 30 backups to prevent storage bloat.

---

## 🚀 Getting Started & Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Rajratna-D/PLANNER-APP.git
cd PLANNER-APP
```

### 2. Install Required Dependencies
```bash
pip install customtkinter matplotlib plyer numpy
```

> **Note**: If `matplotlib` or `plyer` are omitted, Planner V6 gracefully falls back to lightweight mode while preserving all task, calendar, and notes functionality.

### 3. Launch the Application
```bash
# Launch Planner V6
python "planner v6.py"
```

---

## ⌨️ Usage & Workflows

### Theme Switching
Click the **☀ LIGHT / ☾ DARK** button in the top navigation bar to toggle between dark and light modes.

### Fast Task Creation Workflow
1. Navigate to the **▣ TASKS** tab.
2. Enter your task title, choose priority level, set due date (`YYYY-MM-DD`), and optionally choose recurrence.
3. Click **＋ ADD TASK** or press Enter.

### Pomodoro Linking
1. Open the **◎ POMODORO** tab.
2. Under *Working on:*, pick the relevant task from the dropdown.
3. Click **▶ START**. The background timer will commence with live progress bar feedback and trigger a system chime upon completion.

---

## 📁 Repository Structure

```
PLANNER-APP/
├── LICENSE                 # MIT License
├── README.md               # Planner V6 Comprehensive Documentation
├── planner v1.py           # Initial prototype
├── planner v2.py           # Early layout & basic task list
├── planner v3.py           # Added preliminary calendar & categories
├── planner v4.py           # Introduction of priority levels & exams
├── planner v5.py           # UI overhaul & initial data architecture
└── planner v6.py           # Flagship release: PrinceBlue edition, Kiviat radar, 10 tabs
```

---

## 📈 Version History & Evolution

- **V1 - V2**: Proof of concept with standard Tkinter UI and single task lists.
- **V3 - V4**: Introduction of exam scheduling, structured JSON storage, and priority tiers.
- **V5**: Transition to CustomTkinter dark theme, modular cards, and basic timer routines.
- **V6 (Current)**:
  - Complete "PrinceBlue" visual design system.
  - Matplotlib Kiviat spider radar with glowing multi-layer canvas rendering.
  - Multi-milestone practical tracking (`[P]`, `[W]`, `[S]`).
  - Automated recurring task engine (`Daily`, `Weekly`, `Monthly`).
  - Rolling 30-version disaster recovery backups and 60-second auto-saving.
  - Dual-pane searchable markdown notes.
  - Full analytics suite with peak focus hours and productivity grading.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — see the LICENSE file for details.

Developed with precision for high achievers.

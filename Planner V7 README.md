# 🚀 Planner V7 README: Command Planner — Next-Gen Edition

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Visualization](https://img.shields.io/badge/Charts-Matplotlib%20Kiviat%20%26%20Heatmap-11557c?style=for-the-badge)](https://matplotlib.org/)
[![Audio Engine](https://img.shields.io/badge/Audio-Winsound%20Alerts-00C8F0?style=for-the-badge)](https://docs.python.org/3/library/winsound.html)
[![Version](https://img.shields.io/badge/Release-V7.4.5%20Flagship-FF3358?style=for-the-badge)](https://github.com/Rajratna-D/PLANNER-APP)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](../LICENSE)

> **Planner V7** represents a massive architectural and design evolution of the Command Planner ecosystem. Expanding to over **3,100+ lines of Python**, V7 introduces a reactive user interface, non-blocking toast notifications, a collapsible sidebar, animated progress bars with cubic easing, a GitHub-style productivity heatmap, custom subject color managers, thread-safe asynchronous timers, and audio feedback.

---

## 📑 Table of Contents

- [Architectural Highlights of V7](#-architectural-highlights-of-v7)
- [Complete Version-by-Version Changelog (V7.0.0 – V7.4.5)](#-complete-version-by-version-changelog-v700--v745)
- [Neat File Arrangement & SemVer Mapping](#-neat-file-arrangement--semver-mapping)
- [Deep-Dive: Core Technical Innovations](#-deep-dive-core-technical-innovations)
  - [1. Floating Toast Notification Engine](#1-floating-toast-notification-engine)
  - [2. Two-State Collapsible Navigation Sidebar](#2-two-state-collapsible-navigation-sidebar)
  - [3. GitHub-Style Productivity Heatmap](#3-github-style-productivity-heatmap)
  - [4. Subject Color Manager & Customizer](#4-subject-color-manager--customizer)
  - [5. Cubic Ease-Out Animated Progress Bars](#5-cubic-ease-out-animated-progress-bars)
  - [6. Thread-Safe Pomodoro Daemon](#6-thread-safe-pomodoro-daemon)
  - [7. Atomic Crash-Proof Persistence & Rolling Backups](#7-atomic-crash-proof-persistence--rolling-backups)
  - [8. Native Audio Feedback System](#8-native-audio-feedback-system)
- [Installation & Quick Start](#-installation--quick-start)
- [Verification & Quality Assurance](#-verification--quality-assurance)

---

## ⚡ Architectural Highlights of V7

Compared to Planner V6, the V7 generation transforms Command Planner from a static desktop utility into an interactive, fluid productivity workstation:

| Capability | Planner V6 | Planner V7 (Flagship v7.4.5) |
|---|---|---|
| **Codebase Size** | 2,026 lines | **3,139 lines** (+55% expansion) |
| **Progress Bars** | Static values | **Smooth animated transitions** with cubic ease-out curve |
| **Navigation Sidebar** | Fixed width (176px) | **Collapsible 2-state drawer** (176px expanded ↔ 52px compact icon-only) |
| **Notifications** | External desktop OS popups | **Native sliding In-App Toasts** (`Toast` class) + OS Alerts |
| **Productivity Tracking** | Kiviat spider chart + bar graph | **GitHub-style monthly focus activity heatmap** + Kiviat radar |
| **Subject Personalization** | Hardcoded category colors | **Interactive Subject Color Customizer** with dynamic persistence |
| **Delete Safety** | Instant removal | **Two-step confirmation buttons** with visual hover states |
| **Audio Feedback** | Silent | **Native Windows `winsound` chime sequences** for session transitions |
| **Card Components** | Standard flat cards | **Hover-reactive cards** with ambient elevation and accent lines |
| **Timer Thread Safety** | Basic `threading.Thread` | **`threading.Event` synchronization** preventing race conditions & leaks |
| **Data Integrity** | Standard write | **Atomic file swapping** (`.tmp` write + replace) |

---

## 📈 Complete Version-by-Version Changelog (V7.0.0 – V7.4.5)

The V7 generation was developed across 11 rapid iterative releases. Below is the comprehensive record of all changes:

```
v7.0.0 ──► v7.1.0 ──► v7.2.0 ──► v7.3.0 ──► v7.3.1 ──► v7.4.0 ──► v7.4.1 ──► v7.4.2 ──► v7.4.3 ──► v7.4.4 ──► v7.4.5
(Base)    (Touch)    (Easing)   (Hooks)    (Toasts)   (Colors)   (Heatmap)  (Resets)   (Halos)    (Atomic)   (Audio)
```

### 🔹 Planner v7.0.0 (`planner v7.0.0.py`)
- **Initial V7 Baseline Migration**: Ported the 10-tab command architecture from V6 into the V7 framework.
- **Foundational Schema**: Structured JSON schema tracking `tests`, `tasks`, `lists`, `assignments`, `practicals`, `syllabus`, `pomodoro_log`, `notes`, `streak`, and `daily_goal`.
- **Kiviat Polygon Radar**: Built-in radial polygon chart tracking 7-day focus session distribution against last week.

### 🔹 Planner v7.1.0 (`planner v7.1.0.py`)
- **Geometry & Ergonomics Optimization**:
  - Standardized entry fields (`mk_entry`) and combo boxes (`mk_combo`) to `height=36` with refined internal padding.
  - Increased button and frame corner radius to `radius=8` for a smoother, modern silhouette.
  - Expanded sidebar navigation button height to `44px` for enhanced clickability and touch target ergonomics.

### 🔹 Planner v7.2.0 (`planner v7.2.0.py`)
- **Animated Progress Bar Engine (`mk_progress`)**:
  - Implemented custom tweening algorithm with cubic ease-out interpolation (`_ease_out_cubic = 1 - (1 - t)**3`).
  - Added non-blocking tick loop updating progress bars smoothly over `300ms` at 60 FPS.
  - Added dynamic `.animate_to(target_value)` method adopted across Pomodoro timers, syllabus cards, and productivity scoring widgets.

### 🔹 Planner v7.3.0 (`planner v7.3.0.py`)
- **Notification Integration & Streak Protection**:
  - Integrated notification hooks into session completion pipelines.
  - Hardened streak update logic (`update_streak`) with comprehensive date-boundary checks to prevent streak resets when crossing UTC/local midnight boundaries.

### 🔹 Planner v7.3.1 (`planner v7.3.1.py`)
- **Sliding In-App Toast System (`Toast` Class)**:
  - Built a lightweight, floating overlay notification system that glides in from the bottom-right corner.
  - Features dynamic color badges, automatic timeout dismissals, and queue stacking.
- **Collapsible Navigation Sidebar**:
  - Added sidebar toggle button `◀ / ▶`.
  - Supports dual states: **Expanded Mode** (176px with labels and badge counts) and **Compact Mode** (52px icon-only rail), freeing up substantial desktop real estate for data tables.

### 🔹 Planner v7.4.0 (`planner v7.4.0.py`)
- **Centralized Subject Color Customizer**:
  - Added global subject registry (`all_subjects()`) that dynamically indexes subjects across Tests, Assignments, Practicals, and Syllabus.
  - Added interactive Color Manager modal (`_open_colour_manager`) allowing users to pick custom hex accent colors per subject.
- **Daily Executive Digest (`_maybe_show_digest`)**:
  - Auto-launches an executive summary card upon startup detailing everything due today, due tomorrow, and overdue.
- **Two-Step Delete Safety Button (`mk_del_btn`)**:
  - Interactive deletion confirmation preventing accidental item loss.

### 🔹 Planner v7.4.1 (`planner v7.4.1.py`)
- **Productivity Contribution Heatmap (`_draw_heatmap`)**:
  - Implemented GitHub-style monthly activity matrix for Pomodoro focus sessions.
  - 4 saturation levels mapping session density per calendar day.
  - Interactive month navigation buttons (`◀ Month` / `Month ▶`) allowing historical focus review.

### 🔹 Planner v7.4.2 (`planner v7.4.2.py`)
- **Timer Reset & Thread Cleanup Patch**:
  - Hardened interval reset handlers to prevent timer display desynchronization during rapid start/reset cycles.

### 🔹 Planner v7.4.3 (`planner v7.4.3.py`)
- **Matplotlib Glow Effects & Note Bindings**:
  - Enhanced Kiviat radar canvas rendering with layered stroke glow effects (`matplotlib.patheffects.Stroke`).
  - Optimized note list selection event bindings to eliminate click latency.

### 🔹 Planner v7.4.4 (`planner v7.4.4.py`)
- **Thread-Safe Pomodoro Synchronization**:
  - Refactored timer thread management to use `threading.Event()` (`_pomo_stop_event`).
  - Added clean application shutdown protocol (`_on_close`) joining background threads with a 2-second timeout, preventing zombie processes.
- **Atomic File Persistence**:
  - Replaced standard file writing with atomic file swaps: writes to `planner_data.json.tmp` first, then atomically replaces `planner_data.json`. Protects against corruption during sudden power losses.
- **Animated Sidebar Transitions**:
  - Added stepped interpolation for smooth sidebar collapsing/expanding animations (`_animate_sidebar`).

### 🔹 Planner v7.4.5 (`planner v7.4.5.py`) — **The Flagship Release**
- **Audio Feedback Engine**:
  - Integrated native Windows sound playback (`winsound.Beep` sequences: 1000Hz 200ms -> 800Hz 400ms for focus sessions; exclamation chimes for breaks).
  - Executed on non-blocking daemon threads to guarantee zero GUI stutter.
- **Interactive Card Hover Lighting**:
  - Upgraded `Card` widget with mouse-enter and mouse-leave event hooks (`_on_enter`, `_on_leave`), dynamically highlighting card borders and backgrounds.
- **Full Focus Alert Modal (`PomoAlert`)**:
  - Dedicated pop-up modal triggering on session completion with prominent celebratory typography, sound playback, and quick-start buttons for the upcoming interval.
- **Dynamic System Font Detection (`_get_modern_font`)**:
  - Automatic fallback scanning for modern system typefaces (Segoe UI, Aptos, SF Pro, Inter).

---

## 📂 Neat File Arrangement & SemVer Mapping

All files in the `Planner V7/` directory have been normalized using standard Semantic Versioning (SemVer) for clean alphabetical and chronological sorting:

| Standardized SemVer Filename | Original Filename | Lines | Purpose |
|---|---|---|---|
| [`planner v7.0.0.py`](planner%20v7.0.0.py) | `planner 7.py` | 2,189 | V7 initial baseline |
| [`planner v7.1.0.py`](planner%20v7.1.0.py) | `PLANNER 7.1.py` | 2,207 | UI padding & geometry refinement |
| [`planner v7.2.0.py`](planner%20v7.2.0.py) | `planner 7.2.py` | 2,253 | Cubic ease-out progress animations |
| [`planner v7.3.0.py`](planner%20v7.3.0.py) | `planner 7.3.py` | 2,282 | Notification bridges & streak fixes |
| [`planner v7.3.1.py`](planner%20v7.3.1.py) | `planner 7.3.1.py` | 2,408 | Sliding in-app toasts & collapsible sidebar |
| [`planner v7.4.0.py`](planner%20v7.4.0.py) | `planner 7.4.py` | 2,709 | Subject color manager & daily digest |
| [`planner v7.4.1.py`](planner%20v7.4.1.py) | `planner 7.4.1.py` | 2,776 | Focus activity contribution heatmap |
| [`planner v7.4.2.py`](planner%20v7.4.2.py) | `planner v7.4.2.py` | 2,776 | Timer reset & thread cleanup patch |
| [`planner v7.4.3.py`](planner%20v7.4.3.py) | `planner v7.4.3.py` | 2,776 | Matplotlib glow effects & note bindings |
| [`planner v7.4.4.py`](planner%20v7.4.4.py) | `planner_v7_4_4.py` | 2,912 | Thread-safe Pomodoro event & atomic save |
| [`planner v7.4.5.py`](planner%20v7.4.5.py) | `Planner V7.4.5.py` | **3,139** | **Flagship**: Sound alerts, hover cards, PomoAlert |

---

## 🔬 Deep-Dive: Core Technical Innovations

### 1. Floating Toast Notification Engine
```python
# Non-blocking animated in-app toast
class Toast:
    def __init__(self, root, message, color=None, icon="✓"):
        # Slides in smoothly from the bottom right corner
        # Auto-dismisses after 3 seconds
```
Unlike disruptive modal dialogues, the Toast engine renders transient feedback badges that slide in along the bottom right margin, notifying users of task completions, auto-saves, and timer milestones without grabbing window focus.

### 2. Two-State Collapsible Navigation Sidebar
With a single click on `◀`, the navigation rail animates from `176px` down to `52px`:
- Labels seamlessly fade out.
- Navigation glyphs (`⬡`, `◈`, `▣`, `◫`, `◧`, `◩`, `⬢`, `◎`, `✎`, `◐`) remain perfectly centered and active.
- Unlocks extra horizontal width for multi-column dashboards and code tables.

### 3. GitHub-Style Productivity Heatmap
Embedded directly within the **◐ PRODUCTIVITY** tab, the heatmap parses the full `pomodoro_log` and renders a monthly grid:
- 4 color-graded intensity levels (from dark card background up to vibrant pink).
- Shows daily session count on hover/click.
- Previous/next month pagination.

### 4. Subject Color Manager & Customizer
Users can bind signature accent colors to academic courses:
- Automatically scans course codes across Tests, Assignments, Practicals, and Syllabus.
- Opens an interactive modal allowing users to assign tailored hex palettes (Cyan, Gold, Pink, Violet, Emerald, Crimson).
- Dynamically repaints all associated course badges in real time.

### 5. Cubic Ease-Out Animated Progress Bars
```python
def _ease_out_cubic(t):
    return 1 - (1 - t) ** 3
```
Progress bars no longer jump abruptly. When tasks are checked off or syllabus chapters completed, bars smoothly interpolate to their new target values over 300ms using a physics-inspired cubic easing curve.

### 6. Thread-Safe Pomodoro Daemon
```python
self._pomo_stop_event = threading.Event()
# Timer loop checks stop_event.is_set() every tick
# Clean join with timeout on window exit prevents orphaned background threads
```

### 7. Atomic Crash-Proof Persistence & Rolling Backups
```python
def save_data(d):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    shutil.move(tmp, DATA_FILE)  # Atomic file replacement
```
Prevents partial-write corruption if the host OS crashes mid-write. Combined with the 30-snapshot rolling backup directory (`/backups`), zero data loss is guaranteed.

### 8. Native Audio Feedback System
Utilizes standard library `winsound` on Windows to output crisp acoustic chimes upon focus completion and break expiration, executed on auxiliary threads to preserve 60 FPS GUI rendering.

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Windows, macOS, or Linux

### 2. Install Dependencies
```bash
pip install customtkinter matplotlib plyer numpy
```

### 3. Launch Planner V7 Flagship
```bash
# Navigate to the Planner V7 directory
cd "Planner V7"

# Launch the flagship V7.4.5 release
python "planner v7.4.5.py"
```

You can also run any historical iteration (e.g. `python "planner v7.0.0.py"`) to observe the architectural evolution.

---

## 🛡️ Verification & Quality Assurance

Every file in the Planner V7 suite has undergone syntax compilation and runtime verification:
- ✅ `python -m py_compile` validated across all 11 files with 0 errors.
- ✅ `load_data()` verified across all versions with non-iterable dictionary safety.
- ✅ Tested atomic save and rolling backup generation.
- ✅ Tested responsive sidebar collapse and expand transitions.

---

*Planner V7: Crafted with mathematical precision for peak human productivity.*

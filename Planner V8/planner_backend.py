"""
COMMAND PLANNER — Backend Data Layer
Pure Python data logic. No UI code.
"""
import json, os, uuid, shutil, threading, time
from datetime import datetime, date, timedelta

# ── Sound alert (Windows only, graceful fallback) ─────────────────────────
try:
    import winsound
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False

# ── plyer notifications (optional) ────────────────────────────────────────
try:
    from plyer import notification as plyer_notify
    HAS_NOTIFY = True
except ImportError:
    HAS_NOTIFY = False

# ══════════════════════════════════════════════════════════════════════════
# COLOR PALETTE  (shared with QML via the bridge)
# ══════════════════════════════════════════════════════════════════════════
COLORS = {
    # Base surfaces
    "bg":       "#0B0E14",
    "panel":    "#131722",
    "card":     "#1A1F2C",
    "card2":    "#212836",
    "hover":    "#2A3345",
    "border":   "#273142",
    "border2":  "#3B4A66",
    # Text
    "text":     "#F8FAFC",
    "subtext":  "#94A3B8",
    "dim":      "#475569",
    # Accents
    "cyan":     "#06B6D4",
    "blue":     "#3B82F6",
    "green":    "#10B981",
    "orange":   "#F59E0B",
    "red":      "#EF4444",
    "gold":     "#EAB308",
    "violet":   "#8B5CF6",
    "pink":     "#EC4899",
}

COLORS_LIGHT = {
    "bg":       "#F4F6F9",
    "panel":    "#EAEFF4",
    "card":     "#FFFFFF",
    "card2":    "#F8FAFC",
    "hover":    "#E2E8F0",
    "border":   "#CBD5E1",
    "border2":  "#94A3B8",
    "text":     "#0F172A",
    "subtext":  "#64748B",
    "dim":      "#94A3B8",
    "cyan":     "#0891B2",
    "blue":     "#2563EB",
    "green":    "#059669",
    "orange":   "#D97706",
    "red":      "#DC2626",
    "gold":     "#CA8A04",
    "violet":   "#7C3AED",
    "pink":     "#DB2777",
}

PRIORITY_ORDER = ["Immediate", "Important", "2nd Priority", "3rd Priority", "Someday"]
P_COLOR = {
    "Immediate": COLORS["red"],
    "Important": COLORS["orange"],
    "2nd Priority": COLORS["blue"],
    "3rd Priority": COLORS["green"],
    "Someday": COLORS["subtext"],
}
P_BG = {
    "Immediate": "#2C1216",
    "Important": "#2C1E0A",
    "2nd Priority": "#0D1B2A",
    "3rd Priority": "#0A2016",
    "Someday": "#171A24",
}

RECUR_OPTIONS = ["None", "Daily", "Weekly", "Monthly"]

TAB_CFG = [
    ("\u2b21", "OVERVIEW",      COLORS["cyan"]),
    ("\u25c8", "TESTS",         COLORS["gold"]),
    ("\u25a3", "TASKS",         COLORS["orange"]),
    ("\u25eb", "LISTS",         COLORS["blue"]),
    ("\u25e7", "ASSIGNMENTS",   COLORS["red"]),
    ("\u25e9", "PRACTICALS",    COLORS["green"]),
    ("\u2b22", "SYLLABUS",      COLORS["violet"]),
    ("\u25ce", "POMODORO",      COLORS["pink"]),
    ("\u270e", "NOTES",         COLORS["cyan"]),
    ("\u25d0", "PRODUCTIVITY",  COLORS["pink"]),
]

SUBJECT_PALETTE = [
    "#06B6D4", "#EC4899", "#EAB308", "#3B82F6", "#8B5CF6",
    "#F59E0B", "#10B981", "#EF4444", "#67E8F9", "#C084FC",
]

# ══════════════════════════════════════════════════════════════════════════
# DATA LAYER
# ══════════════════════════════════════════════════════════════════════════
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "planner_data.json")
BCK_DIR   = os.path.join(BASE_DIR, "backups")

EMPTY_DATA = {
    "tests": [], "tasks": [], "lists": [],
    "assignments": [], "practicals": [],
    "syllabus": [], "pomodoro_log": [],
    "notes": [],
    "streak": {"last_date": "", "count": 0},
    "daily_goal": 6,
    "theme": "dark",
    "subject_colors": {},
    "last_digest_date": "",
    "window_geometry": "",
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                d = json.load(f)
            for k, v in EMPTY_DATA.items():
                d.setdefault(k, v if not isinstance(v, (dict, list)) else type(v)(v))
            return d
        except Exception:
            pass
    return json.loads(json.dumps(EMPTY_DATA))

def save_data(d):
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, DATA_FILE)
    except Exception as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise RuntimeError(f"save_data failed: {e}") from e

def backup_data(d):
    os.makedirs(BCK_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BCK_DIR, f"backup_{stamp}.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    bks = sorted(os.listdir(BCK_DIR))
    for old in bks[:-30]:
        try:
            os.remove(os.path.join(BCK_DIR, old))
        except Exception:
            pass
    return dst

def days_until(s):
    try:
        return (datetime.strptime(s, "%Y-%m-%d").date() - date.today()).days
    except Exception:
        return None

def urgency_key(d):
    """Return urgency classification string for QML to map to colors."""
    if d is None: return "none"
    if d < 0:    return "past"
    if d == 0:   return "today"
    if d <= 2:   return "urgent"
    if d <= 7:   return "soon"
    return "ok"

def urgency_color(d):
    if d is None: return COLORS["subtext"]
    if d < 0:    return COLORS["dim"]
    if d == 0:   return COLORS["red"]
    if d <= 2:   return COLORS["orange"]
    if d <= 7:   return COLORS["gold"]
    return COLORS["green"]

def urgency_lbl(d):
    if d is None: return "\u2013"
    if d < 0:    return "PAST"
    if d == 0:   return "TODAY"
    if d == 1:   return "TOMORROW"
    return f"{d}d"

def update_streak(data):
    today = date.today().isoformat()
    s = data["streak"]
    if s["last_date"] == today:
        return
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if s["last_date"] == yesterday:
        s["count"] = s.get("count", 0) + 1
    else:
        done_today = any(t.get("done") for t in data.get("tasks", []))
        s["count"] = 1 if done_today else 0
    s["last_date"] = today

def send_notify(title, msg):
    if HAS_NOTIFY:
        try:
            plyer_notify.notify(title=title, message=msg,
                                app_name="Command Planner", timeout=5)
        except Exception:
            pass

def play_pomo_sound():
    """Play the pomodoro completion beeps in a background thread."""
    def _play():
        if HAS_SOUND:
            try:
                for _ in range(3):
                    winsound.Beep(1000, 200)
                    time.sleep(0.15)
                time.sleep(0.3)
                winsound.Beep(800, 400)
            except Exception:
                try:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except Exception:
                    pass
    threading.Thread(target=_play, daemon=True).start()

def nid():
    return str(uuid.uuid4())

def get_subject_color(data, subject):
    if not subject:
        return COLORS["subtext"]
    sc = data.setdefault("subject_colors", {})
    if subject not in sc:
        used_idx = len(sc) % len(SUBJECT_PALETTE)
        sc[subject] = SUBJECT_PALETTE[used_idx]
    return sc[subject]

def set_subject_color(data, subject, color):
    data.setdefault("subject_colors", {})[subject] = color
    save_data(data)

def all_subjects(data):
    subjects = set()
    for t in data.get("tests", []):
        subjects.add(t.get("subject", ""))
    for a in data.get("assignments", []):
        subjects.add(a.get("subject", ""))
    for p in data.get("practicals", []):
        subjects.add(p.get("subject", ""))
    for s in data.get("syllabus", []):
        subjects.add(s.get("name", ""))
    for n in data.get("notes", []):
        subjects.add(n.get("subject", ""))
    return sorted(s for s in subjects if s)

def last_backup_label():
    if os.path.exists(BCK_DIR):
        bks = sorted(os.listdir(BCK_DIR))
        if bks:
            last = bks[-1].replace("backup_", "").replace(".json", "").replace("_", " ")
            return f"Last: {last[:13]}"
    return "No backups yet"

def get_heatmap_data(data, weeks=52):
    """Return heatmap data for the GitHub-style contribution graph.
    Returns list of {date, count, level} for the last N weeks."""
    today = date.today()
    goal = max(data.get("daily_goal", 6), 1)
    log = data.get("pomodoro_log", [])

    # Start from the most recent Sunday going back `weeks` weeks
    days_since_sunday = (today.weekday() + 1) % 7
    end_date = today
    start_date = today - timedelta(days=(weeks * 7) + days_since_sunday)

    result = []
    current = start_date
    while current <= end_date:
        iso = current.isoformat()
        sessions = sum(1 for p in log
                       if p.get("date", "") == iso and p.get("type", "") == "work")
        ratio = sessions / goal
        if sessions == 0:
            level = 0
        elif ratio < 0.25:
            level = 1
        elif ratio < 0.5:
            level = 2
        elif ratio < 0.75:
            level = 3
        else:
            level = 4
        result.append({
            "date": iso,
            "weekday": current.weekday(),  # 0=Mon, 6=Sun
            "count": sessions,
            "level": level,
        })
        current += timedelta(days=1)
    return result

def get_week_sessions(data, week_offset=0):
    """Get session counts for each day of a week."""
    today = date.today()
    log = data.get("pomodoro_log", [])
    ws = today - timedelta(days=today.weekday()) - timedelta(weeks=week_offset)
    result = []
    for i in range(7):
        d = (ws + timedelta(days=i)).isoformat()
        count = sum(1 for p in log if p.get("date", "") == d and p.get("type", "") == "work")
        result.append(count)
    return result

def day_sessions(data, d_iso):
    return sum(1 for p in data.get("pomodoro_log", [])
               if p.get("date", "") == d_iso and p.get("type", "") == "work")

def day_score(data, d_iso):
    goal = max(data.get("daily_goal", 6), 1)
    return min(100, int((day_sessions(data, d_iso) / goal) * 100))

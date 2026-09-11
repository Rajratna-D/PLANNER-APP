"""
COMMAND PLANNER v3 — PRINCEBLUE
Requires: pip install customtkinter matplotlib plyer
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import json, os, uuid, shutil, threading, time, csv
from datetime import datetime, date, timedelta
from tkinter import font as tkfont

# ── matplotlib (optional graceful fallback) ───────────────────────────────
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.patheffects as pe
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ── plyer notifications (optional) ────────────────────────────────────────
try:
    from plyer import notification as plyer_notify
    HAS_NOTIFY = True
except ImportError:
    HAS_NOTIFY = False


def draw_kiviat(fig_master, this_week, last_week, goal, day_labels,
                figsize=(4.4, 4.0), compact=False):
    """Premium Kiviat polygon chart — this week (glowing) vs last week (muted)."""
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    N = 7
    safe_goal = max(goal, 1)

    def norm(vals):
        return [min(v / safe_goal, 1.5) for v in vals]

    tw = norm(this_week)
    lw = norm(last_week)

    angles        = [(-np.pi/2) + (2*np.pi * i / N) for i in range(N)]
    angles_closed = angles + [angles[0]]
    tw_closed     = tw + [tw[0]]
    lw_closed     = lw + [lw[0]]

    bg  = "#09090F"
    fig = Figure(figsize=figsize, facecolor=bg)
    ax  = fig.add_axes([0.08, 0.08, 0.84, 0.84])
    ax.set_aspect("equal")
    ax.set_facecolor(bg)
    ax.axis("off")

    cx, cy = 0.5, 0.5
    max_r  = 0.36

    def pxy(r, a):
        return cx + r * np.cos(a), cy + r * np.sin(a)

    # Grid rings
    ring_lvls  = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
    ring_cols  = ["#141830","#171D38","#1B2240","#1F2748","#171D38","#141830"]
    for lvl, rc in zip(ring_lvls, ring_cols):
        rxs = [cx + max_r * lvl * np.cos(a) for a in angles_closed]
        rys = [cy + max_r * lvl * np.sin(a) for a in angles_closed]
        ax.fill(rxs, rys, color=rc, zorder=1, alpha=0.6)
        ax.plot(rxs, rys, color="#252B50", lw=0.7, zorder=2)

    # Spokes
    for a in angles:
        x1, y1 = pxy(max_r * 1.5, a)
        ax.plot([cx, x1], [cy, y1], color="#252B50", lw=0.7, zorder=2)

    # Last week polygon
    lxs = [cx + max_r * v * np.cos(a) for v, a in zip(lw_closed, angles_closed)]
    lys = [cy + max_r * v * np.sin(a) for v, a in zip(lw_closed, angles_closed)]
    ax.fill(lxs, lys, color="#7070A0", alpha=0.12, zorder=3)
    ax.plot(lxs, lys, color="#7070A0", lw=1.4, ls="--", alpha=0.50, zorder=3)

    # This week polygon — glowing fill
    txs = [cx + max_r * v * np.cos(a) for v, a in zip(tw_closed, angles_closed)]
    tys = [cy + max_r * v * np.sin(a) for v, a in zip(tw_closed, angles_closed)]
    ax.fill(txs, tys, color=PINK, alpha=0.22, zorder=4)
    ax.fill(txs, tys, color=PINK, alpha=0.08, zorder=4)
    ax.plot(txs, tys, color=PINK, lw=3.0, zorder=5,
            path_effects=[
                pe.Stroke(linewidth=7, foreground=PINK, alpha=0.20),
                pe.Normal()
            ])

    # Vertex glow dots
    for v, a in zip(tw, angles):
        vx, vy = cx + max_r * v * np.cos(a), cy + max_r * v * np.sin(a)
        ax.scatter([vx], [vy], s=200, color=PINK, alpha=0.15, zorder=6)
        ax.scatter([vx], [vy], s=60,  color=PINK, zorder=7,
                   edgecolors=bg, linewidths=1.8)

    # Day labels + counts
    label_r = max_r * 1.72
    for i, (day, count) in enumerate(zip(day_labels, this_week)):
        a = angles[i]
        lx2 = cx + label_r * np.cos(a)
        ly2 = cy + label_r * np.sin(a)
        fs_day = 7 if compact else 8
        fs_cnt = 8 if compact else 10
        ax.text(lx2, ly2 + 0.030, day,
                ha="center", va="center",
                color=TEXT, fontsize=fs_day, fontweight="bold", zorder=8)
        count_col = PINK if count >= safe_goal else (GOLD if count > 0 else "#3A4060")
        ax.text(lx2, ly2 - 0.030, str(count),
                ha="center", va="center",
                color=count_col, fontsize=fs_cnt, fontweight="bold", zorder=8)

    # Centre total
    total = sum(this_week)
    ax.text(cx, cy + 0.048, str(total),
            ha="center", va="center",
            color=PINK, fontsize=20 if not compact else 15,
            fontweight="bold", zorder=8)
    ax.text(cx, cy - 0.042, "sessions",
            ha="center", va="center",
            color=SUBTEXT, fontsize=7, zorder=8)

    fig.patch.set_alpha(0)
    canvas = FigureCanvasTkAgg(fig, master=fig_master)
    canvas.draw()
    return canvas

# ══════════════════════════════════════════════════════════════════════════
# THEME
# ══════════════════════════════════════════════════════════════════════════
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Palette
BG        = "#0A0D14"   # Premium midnight navy-black
PANEL     = "#111520"   # Sidebar and topbar
CARD      = "#161B28"   # Main card background
CARD2     = "#1C2333"   # Secondary cards / dropdowns
HOVER     = "#242C42"   # Hover states
BORDER    = "#222A3F"   # Subtle borders
BORDER2   = "#323D5C"   # Focused / active borders

TEXT      = "#F0F2F5"   # Off-white — high readability
SUBTEXT   = "#8E9BB1"   # Muted blue-grey
DIM       = "#4A556D"   # Disabled / very subtle

CYAN      = "#00E5FF"
BLUE      = "#4D96FF"
GREEN     = "#2EE87A"
ORANGE    = "#FF9E2A"
RED       = "#FF4766"
GOLD      = "#FFD700"
VIOLET    = "#B388FF"
PINK      = "#FF7EB9"

PRIORITY_ORDER = ["Immediate", "Important", "2nd Priority", "3rd Priority", "Someday"]
P_COLOR = {"Immediate": RED, "Important": ORANGE,
           "2nd Priority": BLUE, "3rd Priority": GREEN, "Someday": SUBTEXT}
P_BG    = {"Immediate": "#250810", "Important": "#251500",
           "2nd Priority": "#071525", "3rd Priority": "#07200F", "Someday": "#111420"}

RECUR_OPTIONS = ["None", "Daily", "Weekly", "Monthly"]

TAB_CFG = [
    ("⬡", "OVERVIEW",      CYAN),
    ("◈", "TESTS",         GOLD),
    ("▣", "TASKS",         ORANGE),
    ("◫", "LISTS",         BLUE),
    ("◧", "ASSIGNMENTS",   RED),
    ("◩", "PRACTICALS",    GREEN),
    ("⬢", "SYLLABUS",      VIOLET),
    ("◎", "POMODORO",      PINK),
    ("✎", "NOTES",         CYAN),
    ("◐", "PRODUCTIVITY",  PINK),
]

# ── Theme palettes ────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "BG": "#0A0D14", "PANEL": "#111520", "CARD": "#161B28", "CARD2": "#1C2333",
        "HOVER": "#242C42", "BORDER": "#222A3F", "BORDER2": "#323D5C",
        "TEXT": "#F0F2F5", "SUBTEXT": "#8E9BB1", "DIM": "#4A556D",
    },
    "light": {
        "BG": "#F0F2F8", "PANEL": "#E4E8F4", "CARD": "#FFFFFF", "CARD2": "#F5F7FF",
        "HOVER": "#E8ECF8", "BORDER": "#D0D6EC", "BORDER2": "#B8C2E0",
        "TEXT": "#1A1E30", "SUBTEXT": "#6070A0", "DIM": "#A0AACC",
    },
}

# ══════════════════════════════════════════════════════════════════════════
# DATA LAYER
# ══════════════════════════════════════════════════════════════════════════
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "planner_data.json")
BCK_DIR   = os.path.join(BASE_DIR, "backups")

# Default subject colour palette — cycles through these
SUBJECT_PALETTE = [
    "#00E5FF",  # Cyan
    "#FF7EB9",  # Pink
    "#FFD700",  # Gold
    "#4D96FF",  # Blue
    "#B388FF",  # Violet
    "#FF9E2A",  # Orange
    "#2EE87A",  # Green
    "#FF4766",  # Red
    "#80DEEA",  # Light cyan
    "#CE93D8",  # Light violet
]

EMPTY_DATA = {
    "tests": [], "tasks": [], "lists": [],
    "assignments": [], "practicals": [],
    "syllabus": [], "pomodoro_log": [],
    "notes": [],
    "streak": {"last_date": "", "count": 0},
    "daily_goal": 6,
    "theme": "dark",
    "subject_colors": {},      # {"Physics": "#00E5FF", ...}
    "last_digest_date": "",    # ISO date string, prevents double-showing
    "window_geometry": "",     # "WxH+X+Y" — restored on next launch
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                d = json.load(f)
            for k, v in EMPTY_DATA.items():
                d.setdefault(k, v)
            return d
        except Exception:
            pass
    return json.loads(json.dumps(EMPTY_DATA))

def save_data(d):
    """Atomic save: write to a temp file then replace, so a crash mid-write
    never leaves the data file in a corrupt/partial state."""
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, DATA_FILE)
    except Exception as e:
        # Clean up the temp file if something went wrong, don't silently swallow
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
    # keep only last 30 backups
    bks = sorted(os.listdir(BCK_DIR))
    for old in bks[:-30]:
        try: os.remove(os.path.join(BCK_DIR, old))
        except: pass
    return dst

def days_until(s):
    try: return (datetime.strptime(s, "%Y-%m-%d").date() - date.today()).days
    except: return None

def urgency_col(d):
    if d is None: return SUBTEXT
    if d < 0:    return DIM
    if d == 0:   return RED
    if d <= 2:   return ORANGE
    if d <= 7:   return GOLD
    return GREEN

def urgency_lbl(d):
    if d is None: return "–"
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
        # Missed a day — reset streak
        done_today = any(t.get("done") for t in data.get("tasks", []))
        s["count"] = 1 if done_today else 0
    s["last_date"] = today

def send_notify(title, msg):
    if HAS_NOTIFY:
        try:
            plyer_notify.notify(title=title, message=msg,
                                app_name="Command Planner", timeout=5)
        except: pass

def apply_theme(name):
    """Update all global color variables to match the chosen theme."""
    global BG, PANEL, CARD, CARD2, HOVER, BORDER, BORDER2, TEXT, SUBTEXT, DIM
    t = THEMES.get(name, THEMES["dark"])
    BG      = t["BG"];     PANEL   = t["PANEL"]
    CARD    = t["CARD"];   CARD2   = t["CARD2"]
    HOVER   = t["HOVER"];  BORDER  = t["BORDER"];  BORDER2 = t["BORDER2"]
    TEXT    = t["TEXT"];   SUBTEXT = t["SUBTEXT"];  DIM     = t["DIM"]
    mode = "dark" if name == "dark" else "light"
    ctk.set_appearance_mode(mode)

def nid(): return str(uuid.uuid4())

def get_subject_color(data, subject):
    """Return the colour assigned to a subject, auto-assigning if new."""
    if not subject:
        return SUBTEXT
    sc = data.setdefault("subject_colors", {})
    if subject not in sc:
        # Auto-assign next colour from palette
        used_idx = len(sc) % len(SUBJECT_PALETTE)
        sc[subject] = SUBJECT_PALETTE[used_idx]
    return sc[subject]

def set_subject_color(data, subject, color):
    data.setdefault("subject_colors", {})[subject] = color
    save_data(data)

def all_subjects(data):
    """Collect all unique subject names across the whole app."""
    subjects = set()
    for t in data.get("tests",       []): subjects.add(t.get("subject",""))
    for a in data.get("assignments",  []): subjects.add(a.get("subject",""))
    for p in data.get("practicals",   []): subjects.add(p.get("subject",""))
    for s in data.get("syllabus",     []): subjects.add(s.get("name",""))
    for n in data.get("notes",        []): subjects.add(n.get("subject",""))
    return sorted(s for s in subjects if s)

# ══════════════════════════════════════════════════════════════════════════
# REUSABLE WIDGET HELPERS
# ══════════════════════════════════════════════════════════════════════════

def mk_frame(parent, fg_color=CARD, **kw):
    return ctk.CTkFrame(parent, fg_color=fg_color, corner_radius=0, **kw)

def mk_label(parent, text, size=12, bold=False, color=TEXT, bg=None, **kw):
    weight = "bold" if bold else "normal"
    bg = bg or (parent.cget("fg_color") if hasattr(parent, "cget") else CARD)
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont(size=size, weight=weight),
                        text_color=color, fg_color="transparent", **kw)

def mk_btn(parent, text, cmd, color=BORDER2, text_color=TEXT,
           hover=None, width=120, height=32, radius=8, size=11):
    # Use Segoe UI on Windows, SF Pro on Mac, fallback to system default
    _btn_fonts = ["Segoe UI", "SF Pro Display", "Helvetica Neue", "Arial"]
    _avail = set(__import__("tkinter.font", fromlist=["families"]).families())
    _font  = next((f for f in _btn_fonts if f in _avail), None)
    font_kw = {"family": _font, "size": size, "weight": "bold"} if _font else {"size": size, "weight": "bold"}
    return ctk.CTkButton(parent, text=text, command=cmd,
                         fg_color=color, text_color=text_color,
                         hover_color=hover or HOVER,
                         width=width, height=height,
                         corner_radius=radius,
                         border_width=1,
                         border_color=BORDER,
                         font=ctk.CTkFont(**font_kw))

def mk_entry(parent, placeholder="", width=200, height=36):
    return ctk.CTkEntry(parent, placeholder_text=placeholder,
                        fg_color=PANEL, border_color=BORDER,
                        text_color=TEXT, placeholder_text_color=DIM,
                        width=width, height=height,
                        font=ctk.CTkFont(size=11),
                        corner_radius=8,
                        border_width=2)

def mk_combo(parent, values, width=160, height=36):
    return ctk.CTkComboBox(parent, values=values,
                           fg_color=PANEL, border_color=BORDER,
                           text_color=TEXT, button_color=BORDER2,
                           button_hover_color=HOVER,
                           dropdown_fg_color=CARD2,
                           dropdown_text_color=TEXT,
                           dropdown_hover_color=HOVER,
                           width=width, height=height,
                           font=ctk.CTkFont(size=11),
                           corner_radius=8,
                           border_width=2)

def mk_scroll(parent, fg_color=BG):
    return ctk.CTkScrollableFrame(parent, fg_color=fg_color,
                                  scrollbar_button_color=BORDER2,
                                  scrollbar_button_hover_color=HOVER,
                                  corner_radius=0)

def accent_line(parent, color, height=2):
    f = tk.Frame(parent, bg=color, height=height)
    f.pack(fill="x")
    return f

def divider(parent, color=BORDER, padx=20, pady=4):
    tk.Frame(parent, bg=color, height=1).pack(fill="x", padx=padx, pady=pady)

def color_dot(parent, color, size=10):
    c = tk.Canvas(parent, width=size, height=size,
                  bg=parent.cget("bg") if hasattr(parent, "cget") else CARD,
                  highlightthickness=0)
    c.create_oval(1, 1, size-1, size-1, fill=color, outline="")
    return c

# ══════════════════════════════════════════════════════════════════════════
# CARD BUILDER
# ══════════════════════════════════════════════════════════════════════════

class Card(ctk.CTkFrame):
    """Premium card — soft shadow border, thick accent bar, refined radius."""
    def __init__(self, parent, accent_color=BORDER, **kw):
        super().__init__(parent, fg_color=CARD, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        self.accent = accent_color
        # Accent bar using CTkFrame for proper radius on top edge
        self._bar = ctk.CTkFrame(self, fg_color=accent_color, height=3, corner_radius=0)
        self._bar.pack(fill="x")
        self._body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._body.pack(fill="both", expand=True, padx=16, pady=(10,12))

    @property
    def body(self):
        return self._body


# ══════════════════════════════════════════════════════════════════════════
# ANIMATED PROGRESS TWEEN ENGINE
# ══════════════════════════════════════════════════════════════════════════

def mk_progress(parent, target=0.0, color=CYAN, track=BORDER,
                height=6, width=None, duration_ms=600):
    """
    Create a CTkProgressBar that animates smoothly to its target value.
    Uses ease-out cubic: fast start, decelerates at the end.
    Call pb.animate_to(value) anytime to trigger a new transition.
    """
    kw = {"height": height, "progress_color": color, "fg_color": track,
          "corner_radius": 3}
    if width:
        kw["width"] = width
    pb = ctk.CTkProgressBar(parent, **kw)
    pb.set(0)

    # State stored on the widget itself
    pb._tween_current  = 0.0
    pb._tween_target   = target
    pb._tween_duration = duration_ms
    pb._tween_job      = None

    def _ease_out_cubic(t):
        """t in [0,1] → eased value in [0,1]. Fast then slow."""
        return 1 - (1 - t) ** 3

    def _tick(start_val, target_val, elapsed_ms):
        if pb._tween_job is None:
            return
        progress = min(elapsed_ms / pb._tween_duration, 1.0)
        eased    = _ease_out_cubic(progress)
        current  = start_val + (target_val - start_val) * eased
        pb.set(current)
        pb._tween_current = current
        if progress < 1.0:
            try:
                pb._tween_job = pb.after(
                    12,  # ~83 fps — smooth but not CPU-heavy
                    lambda: _tick(start_val, target_val, elapsed_ms + 12)
                )
            except Exception:
                pass

    def animate_to(value):
        value = max(0.0, min(1.0, value))
        if pb._tween_job:
            try: pb.after_cancel(pb._tween_job)
            except Exception: pass
        pb._tween_job = pb.after(
            0,
            lambda: _tick(pb._tween_current, value, 0)
        )
        pb._tween_target = value

    pb.animate_to = animate_to

    # Trigger initial animation after widget is visible
    if target > 0:
        pb.after(80, lambda: pb.animate_to(target))

    return pb


def mk_del_btn(parent, cmd, width=28, height=26):
    """
    Two-stage delete button.
    First click: turns RED and shows 'Sure?'
    Second click within 2s: executes cmd
    If not clicked again: resets to ✕
    """
    state = {"armed": False, "job": None}

    btn_ref = [None]

    def _reset():
        state["armed"] = False
        state["job"]   = None
        try:
            btn_ref[0].configure(text="✕", fg_color="transparent",
                                 text_color=RED, hover_color=P_BG["Immediate"])
        except Exception:
            pass

    def _click():
        if not state["armed"]:
            state["armed"] = True
            btn_ref[0].configure(text="Sure?", fg_color=RED,
                                 text_color=BG, hover_color="#CC0020")
            if state["job"]:
                try: btn_ref[0].after_cancel(state["job"])
                except: pass
            state["job"] = btn_ref[0].after(2000, _reset)
        else:
            if state["job"]:
                try: btn_ref[0].after_cancel(state["job"])
                except: pass
            cmd()

    b = ctk.CTkButton(parent, text="✕", command=_click,
                      fg_color="transparent", text_color=RED,
                      hover_color=P_BG["Immediate"],
                      width=width, height=height, corner_radius=6,
                      font=ctk.CTkFont(size=10, weight="bold"))
    btn_ref[0] = b
    return b

# ══════════════════════════════════════════════════════════════════════════
# SECTION HEADER
# ══════════════════════════════════════════════════════════════════════════

def section_header(parent, title, color, action_text=None, action_cmd=None):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="x", padx=20, pady=(20, 6))
    mk_label(f, title, size=12, bold=True, color=color).pack(side="left")
    if action_text and action_cmd:
        mk_btn(f, action_text, action_cmd, color=BORDER2, width=80, height=28, size=9
               ).pack(side="right")
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(4,0))

# ══════════════════════════════════════════════════════════════════════════
# TAB HEADER
# ══════════════════════════════════════════════════════════════════════════

def tab_header(parent, icon, title, subtitle, color):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="x", padx=24, pady=(22, 0))
    row = ctk.CTkFrame(f, fg_color="transparent")
    row.pack(anchor="w")
    mk_label(row, icon + " ", size=24, color=color).pack(side="left")
    mk_label(row, title, size=24, bold=True, color=TEXT).pack(side="left")
    mk_label(f, subtitle, size=11, color=SUBTEXT).pack(anchor="w", pady=(4,0))
    tk.Frame(parent, bg=color, height=2).pack(fill="x", padx=24, pady=(14,0))
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(1,16))



# ══════════════════════════════════════════════════════════════════════════
# TOAST NOTIFICATION SYSTEM
# ══════════════════════════════════════════════════════════════════════════

class Toast:
    """Slide-in / slide-out toast notification anchored to bottom-right of root."""
    MARGIN   = 20
    WIDTH    = 280
    HEIGHT   = 52
    DURATION = 2400
    SLIDE_MS = 14

    def __init__(self, root, message, color=None, icon="✓"):
        if color is None:
            color = "#00E5FF"
        self._root = root
        self._job  = None

        self._win = tk.Toplevel(root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.configure(bg=CARD)
        try: self._win.attributes("-alpha", 0.0)
        except: pass

        outer = tk.Frame(self._win, bg=color, bd=0)
        outer.pack(fill="both", expand=True)
        tk.Frame(outer, bg=color, width=4).pack(side="left", fill="y")
        inner = tk.Frame(outer, bg=CARD)
        inner.pack(side="left", fill="both", expand=True)
        tk.Label(inner, text=icon, font=("Segoe UI", 14, "bold"),
                 bg=CARD, fg=color).pack(side="left", padx=(12,6), pady=12)
        tk.Label(inner, text=message, font=("Segoe UI", 10),
                 bg=CARD, fg=TEXT, wraplength=200, justify="left"
                 ).pack(side="left", padx=(0,12), pady=12)

        for w in (self._win, outer, inner):
            w.bind("<Button-1>", lambda e: self._dismiss())

        self._win.withdraw()
        root.after(50, self._show)

    def _get_pos(self, offset=0):
        rx = self._root.winfo_x()
        ry = self._root.winfo_y()
        rw = self._root.winfo_width()
        rh = self._root.winfo_height()
        x  = rx + rw - self.WIDTH  - self.MARGIN
        y  = ry + rh - self.HEIGHT - self.MARGIN + offset
        return x, y

    def _show(self):
        x, y = self._get_pos(offset=self.HEIGHT)
        self._win.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        self._win.deiconify()
        self._slide("in", self.HEIGHT, 0)

    def _slide(self, direction, offset, target):
        step = 4
        offset = offset - step if direction == "in" else offset + step
        done   = offset <= target if direction == "in" else offset >= target + self.HEIGHT
        x, y   = self._get_pos(offset=max(0, offset))
        try:
            self._win.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
            alpha = max(0.0, min(1.0, 1.0 - (offset / self.HEIGHT)))
            try: self._win.attributes("-alpha", alpha)
            except: pass
        except Exception:
            return
        if done:
            if direction == "in":
                self._job = self._root.after(self.DURATION, self._dismiss)
            else:
                try: self._win.destroy()
                except: pass
        else:
            self._root.after(self.SLIDE_MS, lambda: self._slide(direction, offset, target))

    def _dismiss(self):
        if self._job:
            try: self._root.after_cancel(self._job)
            except: pass
            self._job = None
        self._slide("out", 0, self.HEIGHT)


def show_toast(root, message, color=None, icon="✓"):
    if color is None:
        color = "#00E5FF"
    Toast(root, message, color=color, icon=icon)

# ══════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════

class PlannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("COMMAND PLANNER")
        self.minsize(1024, 640)
        self.configure(fg_color=BG)
        self.data                = load_data()
        self._current_theme      = self.data.get("theme", "dark")
        apply_theme(self._current_theme)
        self._task_sort          = "Priority"
        self._task_filter        = None
        self._sbtn_refs          = {}
        self._note_selected      = None
        # ── Thread-safe Pomodoro state ─────────────────────────────────────
        self._pomo_stop_event = threading.Event()   # set() = stop, clear() = running
        self._pomo_stop_event.set()                 # starts in stopped state
        self._pomo_thread     = None
        self._pomo_seconds    = 25 * 60
        self._pomo_elapsed    = 0
        self._pomo_mode       = "work"
        self._pomo_sessions   = 0
        self._goal_toast_date = ""
        # ── Sidebar state ──────────────────────────────────────────────────
        self._sidebar_open        = True
        self._sidebar_expanded_w  = 176
        self._sidebar_collapsed_w = 52
        update_streak(self.data)
        backup_data(self.data)
        save_data(self.data)
        self._build_ui()
        # ── Restore window geometry saved from last session ────────────────
        saved_geo = self.data.get("window_geometry", "")
        if saved_geo:
            try:
                self.geometry(saved_geo)
            except Exception:
                self.geometry("1280x780")
        else:
            self.geometry("1280x780")
        # ── Graceful shutdown ──────────────────────────────────────────────
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(60000, self._auto_save_loop)
        self._maybe_show_digest()

    # ── Auto-save loop ────────────────────────────────────────────────────
    def _auto_save_loop(self):
        save_data(self.data)
        self.after(60000, self._auto_save_loop)

    # ── Graceful shutdown ─────────────────────────────────────────────────
    def _on_close(self):
        """Stop the Pomodoro timer cleanly, persist geometry, save, then exit."""
        # 1. Signal the background thread to stop and wait briefly for it
        self._pomo_stop_event.set()
        if self._pomo_thread and self._pomo_thread.is_alive():
            self._pomo_thread.join(timeout=2.0)   # max 2 s wait; daemon thread won't block exit
        # 2. Save current window geometry for next launch
        try:
            self.data["window_geometry"] = self.geometry()
        except Exception:
            pass
        # 3. Final save — use try/except so a disk error doesn't prevent the window closing
        try:
            save_data(self.data)
        except Exception:
            pass
        # 4. Destroy the window
        self.destroy()

    # ══════════════════════════════════════════════════════════════════════
    # LAYOUT SHELL
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        # Top bar
        topbar = ctk.CTkFrame(self, fg_color=PANEL, height=56, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=CYAN, width=4).pack(side="left", fill="y")

        # Sidebar collapse toggle
        self._collapse_btn = mk_btn(topbar, "◀", self._toggle_sidebar,
                                    "transparent", SUBTEXT, HOVER, 36, 56, radius=0, size=13)
        self._collapse_btn.pack(side="left", fill="y")

        lf = ctk.CTkFrame(topbar, fg_color="transparent")
        lf.pack(side="left", padx=18, fill="y")
        ctk.CTkFrame(lf, fg_color="transparent").pack(expand=True)
        row = ctk.CTkFrame(lf, fg_color="transparent")
        row.pack()
        mk_label(row, "COMMAND", size=20, bold=True, color=TEXT).pack(side="left")
        mk_label(row, " PLANNER", size=20, bold=True, color=CYAN).pack(side="left")
        mk_label(row, "  v3  //  PRINCEBLUE", size=9, color=SUBTEXT).pack(side="left", pady=(5,0))
        ctk.CTkFrame(lf, fg_color="transparent").pack(expand=True)

        rf = ctk.CTkFrame(topbar, fg_color="transparent")
        rf.pack(side="right", padx=16, fill="y")
        ctk.CTkFrame(rf, fg_color="transparent").pack(expand=True)
        self.clock_lbl = mk_label(rf, "", size=10, color=SUBTEXT)
        self.clock_lbl.pack()
        btn_row = ctk.CTkFrame(rf, fg_color="transparent")
        btn_row.pack()
        mk_btn(btn_row, "💾 SAVE", self._manual_save, BORDER2, GREEN, HOVER, 90, 26, size=9).pack(side="left", padx=4)
        mk_btn(btn_row, "📦 BACKUP", self._do_backup, BORDER2, CYAN, HOVER, 90, 26, size=9).pack(side="left", padx=4)
        self.theme_btn = mk_btn(btn_row, "☀ LIGHT", self._toggle_theme, BORDER2, GOLD, HOVER, 90, 26, size=9)
        self.theme_btn.pack(side="left", padx=4)
        ctk.CTkFrame(rf, fg_color="transparent").pack(expand=True)
        self._tick()

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Body
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = ctk.CTkFrame(body, fg_color=PANEL, width=176, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._sidebar_sep = tk.Frame(body, bg=BORDER, width=1)
        self._sidebar_sep.pack(side="left", fill="y")

        self._nav_label = mk_label(self.sidebar, "  NAVIGATION", size=9, bold=True, color=SUBTEXT)
        self._nav_label.pack(anchor="w", padx=14, pady=(18,8))

        self.content_area = ctk.CTkFrame(body, fg_color=BG, corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        self.tab_frames = {}
        self.active_tab = tk.StringVar(value="")  # blank so first _show_tab("OVERVIEW") always runs

        for icon, name, color in TAB_CFG:
            f = ctk.CTkFrame(self.content_area, fg_color=BG, corner_radius=0)
            self.tab_frames[name] = f
            self._make_sbtn(icon, name, color)

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=14, pady=14)
        mk_label(self.sidebar, "  BACKUPS", size=9, bold=True, color=SUBTEXT).pack(anchor="w", padx=14)
        self.backup_lbl = mk_label(self.sidebar, "", size=9, color=DIM)
        self.backup_lbl.pack(anchor="w", padx=14, pady=(2,0))
        self._update_backup_lbl()

        self._build_all_tabs()
        self._show_tab("OVERVIEW")

    def _make_sbtn(self, icon, name, color):
        outer = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=44)
        outer.pack(fill="x", padx=10, pady=2)
        outer.pack_propagate(False)

        # Rounded indicator bar using CTkFrame
        bar = ctk.CTkFrame(outer, fg_color="transparent", width=4, corner_radius=2)
        bar.pack(side="left", fill="y", pady=8)

        inner = ctk.CTkFrame(outer, fg_color="transparent", cursor="hand2", corner_radius=8)
        inner.pack(side="left", fill="both", expand=True, padx=(6, 0))

        ico = mk_label(inner, icon, size=14, color=color)
        ico.pack(side="left", padx=(10, 6))
        lbl = mk_label(inner, name, size=11, color=SUBTEXT)
        lbl.pack(side="left")
        cnt = mk_label(inner, "", size=10, color=DIM)
        cnt.pack(side="right", padx=10)

        self._sbtn_refs[name] = {"outer": outer, "inner": inner, "bar": bar,
                                  "ico": ico, "lbl": lbl, "color": color, "cnt": cnt}

        def _click(e=None, n=name): self._show_tab(n)
        def _enter(e=None):
            if self.active_tab.get() != name:
                inner.configure(fg_color=HOVER)
        def _leave(e=None):
            if self.active_tab.get() != name:
                inner.configure(fg_color="transparent")

        for w in (outer, inner, ico, lbl, cnt, bar):
            w.bind("<Button-1>", _click)
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)

    def _show_tab(self, name):
        """Switch tabs: lazy-build on first visit, hide only the previous frame."""
        prev = self.active_tab.get()
        if prev == name:
            return

        # Deactivate previous sidebar button
        if prev in self._sbtn_refs:
            r = self._sbtn_refs[prev]
            r["inner"].configure(fg_color="transparent")
            r["bar"].configure(fg_color="transparent")
            r["lbl"].configure(text_color=SUBTEXT)

        # Activate new sidebar button
        self.active_tab.set(name)
        r = self._sbtn_refs[name]
        r["inner"].configure(fg_color=HOVER)
        r["bar"].configure(fg_color=r["color"])
        r["lbl"].configure(text_color=TEXT)

        # Hide only the previously visible frame (not all 9)
        if prev and prev in self.tab_frames:
            self.tab_frames[prev].pack_forget()

        # Lazy-build tab scaffold on first visit
        first_visit = name not in self._tabs_built
        self._ensure_tab_built(name)

        # Show the target frame
        target_frame = self.tab_frames[name]
        target_frame.pack(fill="both", expand=True)

        # Refresh data-driven content
        if name == "OVERVIEW":
            self._refresh_overview()
        elif name == "PRODUCTIVITY":
            self._refresh_productivity()
        elif first_visit:
            # For tabs with a refresh method, run it on first build
            refreshers = {
                "TESTS":       self._refresh_tests,
                "TASKS":       self._refresh_tasks,
                "LISTS":       self._refresh_lists,
                "ASSIGNMENTS": self._refresh_assignments,
                "PRACTICALS":  self._refresh_practicals,
                "SYLLABUS":    self._refresh_syllabus,
                "NOTES":       self._refresh_notes_list,
                "POMODORO":    self._pomo_refresh_log,
            }
            if name in refreshers:
                refreshers[name]()

        # Fade-in only after the tab has already been shown once
        # (skip on first visit to avoid adding latency on a cold open)
        if not first_visit:
            self._fade_in(target_frame)

    def _fade_in(self, frame, steps=8, interval=18):
        """Overlay canvas fade-in illusion using stipple patterns."""
        overlay = tk.Canvas(frame, bg=BG, highlightthickness=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        stipple_map = {8:"gray75",7:"gray75",6:"gray50",5:"gray50",
                       4:"gray25",3:"gray25",2:"gray12",1:"gray12"}
        def _step(remaining):
            if remaining <= 0:
                try: overlay.destroy()
                except: pass
                return
            try:
                overlay.delete("all")
                overlay.create_rectangle(
                    0, 0,
                    overlay.winfo_width()  or 2000,
                    overlay.winfo_height() or 2000,
                    fill=BG,
                    stipple=stipple_map.get(remaining, "gray12"),
                    outline=""
                )
            except Exception:
                try: overlay.destroy()
                except: pass
                return
            frame.after(interval, lambda: _step(remaining - 1))
        frame.after(10, lambda: _step(steps))

    def _toggle_sidebar(self):
        """Smoothly collapse/expand the sidebar."""
        self._sidebar_open = not self._sidebar_open
        target_w = self._sidebar_expanded_w if self._sidebar_open else self._sidebar_collapsed_w
        self._collapse_btn.configure(text="◀" if self._sidebar_open else "▶")

        if self._sidebar_open:
            # Expanding: start animation first, then reveal labels at the end
            # so they don't appear squashed during the resize
            self._animate_sidebar(target_w, on_done=self._sidebar_show_labels)
        else:
            # Collapsing: hide labels immediately so they don't overflow
            self._sidebar_hide_labels()
            self._animate_sidebar(target_w, on_done=self._sidebar_center_icons)

    def _sidebar_show_labels(self):
        # Restore icon to left-pack before adding labels beside it
        for r in self._sbtn_refs.values():
            r["ico"].pack_forget()
            r["ico"].pack(side="left", padx=(10, 6))
        self._nav_label.pack(anchor="w", padx=14, pady=(18, 8))
        for r in self._sbtn_refs.values():
            r["lbl"].pack(side="left")
            r["cnt"].pack(side="right", padx=10)

    def _sidebar_hide_labels(self):
        self._nav_label.pack_forget()
        for r in self._sbtn_refs.values():
            r["lbl"].pack_forget()
            r["cnt"].pack_forget()

    def _sidebar_center_icons(self):
        """Re-pack icons so they sit centred in the collapsed 52 px strip."""
        for r in self._sbtn_refs.values():
            r["ico"].pack_forget()
            r["ico"].pack(expand=True)   # centre in the inner frame

    def _animate_sidebar(self, target_w, on_done=None):
        """Animate sidebar width with ease-out. Cancels any in-flight animation first."""
        # Cancel any previously scheduled animation step
        if hasattr(self, "_sidebar_anim_job") and self._sidebar_anim_job:
            try:
                self.after_cancel(self._sidebar_anim_job)
            except Exception:
                pass
            self._sidebar_anim_job = None

        def _step():
            current_w = self.sidebar.cget("width")
            if current_w == target_w:
                self._sidebar_anim_job = None
                if on_done:
                    on_done()
                return
            diff  = target_w - current_w
            move  = max(1, abs(diff) // 3) if abs(diff) > 4 else abs(diff)
            new_w = current_w + (move if diff > 0 else -move)
            new_w = max(self._sidebar_collapsed_w,
                        min(self._sidebar_expanded_w, new_w))
            self.sidebar.configure(width=new_w)
            if new_w != target_w:
                self._sidebar_anim_job = self.after(12, _step)
            else:
                self._sidebar_anim_job = None
                if on_done:
                    on_done()

        self._sidebar_anim_job = self.after(0, _step)

    def _tick(self):
        self.clock_lbl.configure(text=datetime.now().strftime("%a %d %b %Y  •  %H:%M:%S"))
        self.after(1000, self._tick)

    def _update_backup_lbl(self):
        if os.path.exists(BCK_DIR):
            bks = sorted(os.listdir(BCK_DIR))
            if bks:
                last = bks[-1].replace("backup_","").replace(".json","").replace("_"," ")
                self.backup_lbl.configure(text=f"  Last: {last[:13]}")
                return
        self.backup_lbl.configure(text="  No backups yet")

    def _build_all_tabs(self):
        # Build only the Overview tab eagerly (it's shown immediately).
        # All other tabs are built lazily on first visit via _ensure_tab_built().
        self._tabs_built = {"OVERVIEW"}
        self._build_overview_tab()

    def _ensure_tab_built(self, name):
        """Build a tab's static scaffold the first time it is visited."""
        if name in self._tabs_built:
            return
        self._tabs_built.add(name)
        builders = {
            "TESTS":       self._build_tests_tab,
            "TASKS":       self._build_tasks_tab,
            "LISTS":       self._build_lists_tab,
            "ASSIGNMENTS": self._build_assignments_tab,
            "PRACTICALS":  self._build_practicals_tab,
            "SYLLABUS":    self._build_syllabus_tab,
            "POMODORO":    self._build_pomodoro_tab,
            "NOTES":       self._build_notes_tab,
            "PRODUCTIVITY":self._build_productivity_tab,
        }
        if name in builders:
            builders[name]()

    # ══════════════════════════════════════════════════════════════════════
    # THEME TOGGLE
    # ══════════════════════════════════════════════════════════════════════

    def _toggle_theme(self):
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self._current_theme = new_theme
        self.data["theme"] = new_theme
        apply_theme(new_theme)
        save_data(self.data)
        self._update_theme_btn()
        # Restart app to fully repaint (simplest reliable approach)
        mode_name = "Light" if new_theme == "light" else "Dark"
        messagebox.showinfo(
            "Theme Changed",
            f"Switched to {mode_name} mode.\n\nRestart the app to see full effect."
        )

    def _update_theme_btn(self):
        if self._current_theme == "dark":
            self.theme_btn.configure(text="☀ LIGHT")
        else:
            self.theme_btn.configure(text="☾ DARK")

    # ══════════════════════════════════════════════════════════════════════
    # OVERVIEW TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_overview_tab(self):
        tab = self.tab_frames["OVERVIEW"]
        self._ov_sf = mk_scroll(tab, BG)
        self._ov_sf.pack(fill="both", expand=True)

    def _refresh_overview(self):
        for w in self._ov_sf.winfo_children():
            w.destroy()
        root = self._ov_sf

        # Greeting + streak
        gf = ctk.CTkFrame(root, fg_color="transparent")
        gf.pack(fill="x", padx=24, pady=(20,8))
        hour = datetime.now().hour
        tod = "GOOD MORNING" if hour < 12 else ("GOOD AFTERNOON" if hour < 18 else "GOOD EVENING")
        mk_label(gf, f"{tod}, PRINCEBLUE", size=22, bold=True, color=CYAN).pack(side="left", anchor="w")
        streak = self.data["streak"].get("count", 0)
        if streak > 0:
            sf2 = ctk.CTkFrame(gf, fg_color=P_BG["Important"], corner_radius=8)
            sf2.pack(side="right", padx=8)
            mk_label(sf2, f"🔥 {streak} day streak", size=11, bold=True, color=ORANGE).pack(padx=12, pady=6)
        mk_label(root, datetime.now().strftime("  %A, %d %B %Y"),
                 size=11, color=SUBTEXT).pack(anchor="w", padx=24)

        divider(root, padx=24, pady=8)

        # Stat cards
        tests_up  = len([t for t in self.data["tests"] if (days_until(t.get("date","")) or -1) >= 0])
        tasks_p   = len([t for t in self.data["tasks"] if not t.get("done")])
        asgn_p    = len([a for a in self.data["assignments"] if not a.get("submitted")])
        prac_p    = len([p for p in self.data["practicals"] if not p.get("done")])
        subj_c    = len(self.data.get("syllabus", []))
        pomo_today = sum(1 for p in self.data.get("pomodoro_log",[])
                         if p.get("date","") == date.today().isoformat())

        stats_row = ctk.CTkFrame(root, fg_color="transparent")
        stats_row.pack(fill="x", padx=24, pady=(0,16))
        for col_i, (lbl, num, col) in enumerate([
            ("TESTS DUE",   str(tests_up),  GOLD),
            ("TASKS LEFT",  str(tasks_p),   ORANGE),
            ("ASSIGNMENTS", str(asgn_p),    RED),
            ("PRACTICALS",  str(prac_p),    GREEN),
            ("SUBJECTS",    str(subj_c),    VIOLET),
            ("POMODOROS\nTODAY", str(pomo_today), PINK),
        ]):
            sc = ctk.CTkFrame(stats_row, fg_color=CARD, corner_radius=10)
            sc.grid(row=0, column=col_i, padx=(0,10), sticky="ew", ipady=4)
            stats_row.grid_columnconfigure(col_i, weight=1)
            tk.Frame(sc, bg=col, height=2).pack(fill="x")
            mk_label(sc, num, size=28, bold=True, color=col).pack(anchor="w", padx=14, pady=(8,0))
            mk_label(sc, lbl, size=9, bold=True, color=SUBTEXT).pack(anchor="w", padx=14, pady=(0,10))

        # Two-column layout for content
        cols_frame = ctk.CTkFrame(root, fg_color="transparent")
        cols_frame.pack(fill="x", padx=20, pady=4)
        left_col  = ctk.CTkFrame(cols_frame, fg_color="transparent")
        right_col = ctk.CTkFrame(cols_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        cols_frame.grid_columnconfigure(0, weight=1)
        cols_frame.grid_columnconfigure(1, weight=1)

        # ── LEFT: Tests + Tasks
        section_header(left_col, "◈  UPCOMING TESTS", GOLD)
        tests = sorted([t for t in self.data["tests"]
                        if (days_until(t.get("date","")) or -1) >= 0],
                       key=lambda x: x.get("date",""))[:4]
        if tests:
            for t in tests:
                d = days_until(t.get("date","")); c = urgency_col(d)
                card = Card(left_col, accent_color=c)
                card.pack(fill="x", padx=20, pady=3)
                row = ctk.CTkFrame(card.body, fg_color="transparent")
                row.pack(fill="x")
                mk_label(row, t.get("subject",""), size=12, bold=True, color=TEXT).pack(side="left")
                mk_label(row, urgency_lbl(d), size=9, bold=True, color=c).pack(side="right")
                mk_label(card.body, f"{t.get('date','')}  {t.get('time','')}",
                         size=10, color=SUBTEXT).pack(anchor="w")
        else:
            mk_label(left_col, "  No upcoming tests", size=11, color=DIM).pack(anchor="w", padx=24, pady=6)

        section_header(left_col, "▣  TOP TASKS", ORANGE)
        tasks = sorted([t for t in self.data["tasks"] if not t.get("done")],
                       key=lambda t: PRIORITY_ORDER.index(t.get("priority","Someday")))[:5]
        if tasks:
            for t in tasks:
                p = t.get("priority","Someday"); pc = P_COLOR.get(p, SUBTEXT)
                card = Card(left_col, pc)
                card.pack(fill="x", padx=20, pady=3)
                row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
                mk_label(row, t.get("text",""), size=11, color=TEXT).pack(side="left")
                mk_label(row, p, size=9, bold=True, color=pc).pack(side="right")
        else:
            mk_label(left_col, "  No pending tasks", size=11, color=DIM).pack(anchor="w", padx=24, pady=6)

        # ── RIGHT: Assignments + Practicals + Chart
        section_header(right_col, "◧  ASSIGNMENTS DUE", RED)
        asgns = sorted([a for a in self.data["assignments"] if not a.get("submitted")],
                       key=lambda x: x.get("due","9999"))[:4]
        if asgns:
            for a in asgns:
                d = days_until(a.get("due","")); c = urgency_col(d)
                card = Card(right_col, c)
                card.pack(fill="x", padx=20, pady=3)
                row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
                mk_label(row, f"[{a.get('subject','')}] {a.get('title','')}",
                         size=11, color=TEXT).pack(side="left")
                dl = (f"{d}d" if (d or 0) >= 0 else "OVR") if d is not None else "–"
                mk_label(row, dl, size=9, bold=True, color=c).pack(side="right")
        else:
            mk_label(right_col, "  No pending assignments", size=11, color=DIM).pack(anchor="w", padx=24, pady=6)

        section_header(right_col, "◩  PRACTICALS", GREEN)
        pracs = [p for p in self.data["practicals"] if not p.get("done")][:4]
        if pracs:
            for p in pracs:
                card = Card(right_col, GREEN)
                card.pack(fill="x", padx=20, pady=3)
                row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
                mk_label(row, f"Exp {p.get('num','?')} — {p.get('title','')}",
                         size=11, color=TEXT).pack(side="left")
                sr = ctk.CTkFrame(row, fg_color="transparent"); sr.pack(side="right")
                for sym, key in [("P","performed"),("W","writeup"),("S","submitted")]:
                    done_s = p.get(key, False)
                    mk_label(sr, sym, size=9, bold=True,
                             color=GREEN if done_s else DIM).pack(side="left", padx=2)
        else:
            mk_label(right_col, "  No pending practicals", size=11, color=DIM).pack(anchor="w", padx=24, pady=6)

        # Heatmap on overview (above spider)
        section_header(right_col, "◈  MONTHLY HEATMAP", GOLD)
        hm_card = ctk.CTkFrame(right_col, fg_color=CARD, corner_radius=10)
        hm_card.pack(fill="x", padx=20, pady=(0,6))
        tk.Frame(hm_card, bg=GOLD, height=2).pack(fill="x")
        self._draw_heatmap(hm_card, month_offset=0, compact=True)

        # Spider chart below heatmap
        if HAS_MPL:
            section_header(right_col, "◐  WEEKLY FOCUS RADAR", PINK)
            self._ov_spider_chart(right_col)

        # Syllabus summary
        section_header(left_col, "⬢  SYLLABUS PROGRESS", VIOLET)
        syllabus = self.data.get("syllabus", [])
        if syllabus:
            for subj in syllabus[:4]:
                topics = subj.get("topics", [])
                total = len(topics)
                done  = sum(1 for t in topics if t.get("done"))
                pct   = int((done/total)*100) if total else 0
                card  = Card(left_col, VIOLET)
                card.pack(fill="x", padx=20, pady=3)
                row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
                mk_label(row, subj.get("name",""), size=11, bold=True, color=TEXT).pack(side="left")
                mk_label(row, f"{pct}%", size=11, bold=True, color=VIOLET).pack(side="right")
                # progress bar using ctk
                sc2 = get_subject_color(self.data, subj.get("name",""))
                mk_label(card.body, subj.get("name",""), size=11, bold=True, color=sc2
                         ).pack(anchor="w")
                pb = mk_progress(card.body, pct/100, sc2, BORDER, height=6)
                pb.pack(fill="x", pady=(4,0))
        else:
            mk_label(left_col, "  No subjects added", size=11, color=DIM).pack(anchor="w", padx=24, pady=6)

        # ── PENDING TODAY summary panel (bottom of overview)
        divider(root, padx=24, pady=(16,4))
        pf = ctk.CTkFrame(root, fg_color="transparent")
        pf.pack(fill="x", padx=20, pady=(0,4))
        left_pend  = ctk.CTkFrame(pf, fg_color="transparent")
        right_pend = ctk.CTkFrame(pf, fg_color="transparent")
        left_pend.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        right_pend.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        pf.grid_columnconfigure(0, weight=1)
        pf.grid_columnconfigure(1, weight=1)

        # Build pending today list
        today_iso = date.today().isoformat()
        pending_items = []
        for t in self.data["tests"]:
            d = days_until(t.get("date",""))
            if d is not None and 0 <= d <= 1:
                pending_items.append(("◈ TEST", t.get("subject",""), urgency_col(d), urgency_lbl(d)))
        for t in self.data["tasks"]:
            if not t.get("done"):
                due = t.get("due","")
                d = days_until(due) if due else None
                if d is not None and d <= 0:
                    pending_items.append(("▣ TASK", t.get("text","")[:40], urgency_col(d), urgency_lbl(d)))
        for a in self.data["assignments"]:
            if not a.get("submitted"):
                d = days_until(a.get("due",""))
                if d is not None and d <= 1:
                    pending_items.append(("◧ ASGN", f"[{a.get('subject','')}] {a.get('title','')[:30]}", urgency_col(d), urgency_lbl(d)))
        overdue = [x for x in pending_items if x[3] in ("PAST","OVERDUE")]
        today_due = [x for x in pending_items if x[3] == "TODAY"]
        tomorrow_due = [x for x in pending_items if x[3] == "TOMORROW"]

        # Left: Today & Overdue
        sec_lbl = ctk.CTkFrame(left_pend, fg_color=CARD, corner_radius=10)
        sec_lbl.pack(fill="x", pady=2)
        tk.Frame(sec_lbl, bg=RED, height=2).pack(fill="x")
        hdr = ctk.CTkFrame(sec_lbl, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(8,4))
        mk_label(hdr, "🔴  DUE TODAY & OVERDUE", size=11, bold=True, color=RED).pack(side="left")
        mk_label(hdr, str(len(today_due)+len(overdue)), size=11, bold=True, color=RED).pack(side="right")
        items_to_show = today_due + overdue
        if items_to_show:
            for typ, name, col, lbl in items_to_show[:8]:
                row2 = ctk.CTkFrame(sec_lbl, fg_color="transparent")
                row2.pack(fill="x", padx=14, pady=2)
                mk_label(row2, typ, size=9, bold=True, color=col).pack(side="left", padx=(0,6))
                mk_label(row2, name, size=10, color=TEXT).pack(side="left")
                mk_label(row2, lbl, size=9, bold=True, color=col).pack(side="right")
        else:
            mk_label(sec_lbl, "  Nothing due today — great!", size=10, color=GREEN).pack(anchor="w", padx=14, pady=4)
        ctk.CTkFrame(sec_lbl, fg_color="transparent", height=8).pack()

        # Right: Tomorrow
        sec_lbl2 = ctk.CTkFrame(right_pend, fg_color=CARD, corner_radius=10)
        sec_lbl2.pack(fill="x", pady=2)
        tk.Frame(sec_lbl2, bg=ORANGE, height=2).pack(fill="x")
        hdr2 = ctk.CTkFrame(sec_lbl2, fg_color="transparent")
        hdr2.pack(fill="x", padx=14, pady=(8,4))
        mk_label(hdr2, "🟡  DUE TOMORROW", size=11, bold=True, color=ORANGE).pack(side="left")
        mk_label(hdr2, str(len(tomorrow_due)), size=11, bold=True, color=ORANGE).pack(side="right")
        if tomorrow_due:
            for typ, name, col, lbl in tomorrow_due[:8]:
                row3 = ctk.CTkFrame(sec_lbl2, fg_color="transparent")
                row3.pack(fill="x", padx=14, pady=2)
                mk_label(row3, typ, size=9, bold=True, color=col).pack(side="left", padx=(0,6))
                mk_label(row3, name, size=10, color=TEXT).pack(side="left")
        else:
            mk_label(sec_lbl2, "  Nothing due tomorrow.", size=10, color=SUBTEXT).pack(anchor="w", padx=14, pady=4)
        ctk.CTkFrame(sec_lbl2, fg_color="transparent", height=8).pack()

        ctk.CTkFrame(root, fg_color="transparent", height=24).pack()

    def _draw_heatmap(self, parent, month_offset=0, compact=False):
        """
        Render a monthly productivity heatmap into parent.
        month_offset=0 → current month, -1 → last month, etc.
        compact=True → smaller cells for overview panel.
        """
        today      = date.today()
        # Calculate target month
        target_month = today.month + month_offset
        target_year  = today.year
        while target_month < 1:
            target_month += 12
            target_year  -= 1
        while target_month > 12:
            target_month -= 12
            target_year  += 1
        month_start = today.replace(year=target_year, month=target_month, day=1)

        # Days in month
        if target_month == 12:
            next_m = month_start.replace(year=target_year+1, month=1, day=1)
        else:
            next_m = month_start.replace(month=target_month+1, day=1)
        days_in_month = (next_m - timedelta(days=1)).day

        log      = self.data.get("pomodoro_log", [])
        goal     = max(self.data.get("daily_goal", 6), 1)

        def day_score(d_iso):
            sessions = sum(1 for p in log
                           if p.get("date","") == d_iso and p.get("type","") == "work")
            return min(100, int((sessions / goal) * 100))

        cell_size = 30 if compact else 40
        cell_r    = 4  if compact else 6

        # ── Header row ───────────────────────────────────────────────────
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(8,4))
        mk_label(hdr, month_start.strftime("%B %Y").upper(),
                 size=11 if not compact else 9, bold=True, color=GOLD).pack(side="left")

        # Legend — right aligned
        for lbl_l, col_l in [("EXC",GOLD),("GOOD",CYAN),("AVG",ORANGE),("LOW",RED),("–",DIM)]:
            dot = ctk.CTkFrame(hdr, fg_color=col_l, width=7, height=7, corner_radius=3)
            dot.pack(side="right", padx=(0,1))
            mk_label(hdr, lbl_l, size=7, color=col_l).pack(side="right", padx=(0,3))

        # ── Day-of-week row ───────────────────────────────────────────────
        dow_f = ctk.CTkFrame(parent, fg_color="transparent")
        dow_f.pack(fill="x", padx=14, pady=(0,3))
        for d_name in ["M","T","W","T","F","S","S"]:
            mk_label(dow_f, d_name, size=7, bold=True, color=SUBTEXT
                     ).pack(side="left", expand=True)

        # ── Calendar grid ─────────────────────────────────────────────────
        first_dow   = month_start.weekday()
        total_cells = first_dow + days_in_month
        rows_needed = (total_cells + 6) // 7

        grid_f = ctk.CTkFrame(parent, fg_color="transparent")
        grid_f.pack(fill="x", padx=14, pady=(0,10))

        for row_i in range(rows_needed):
            row_frame = ctk.CTkFrame(grid_f, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            for col_i in range(7):
                cell_num = row_i * 7 + col_i - first_dow + 1
                cell = ctk.CTkFrame(row_frame, fg_color="transparent",
                                    width=cell_size, height=cell_size)
                cell.pack(side="left", expand=True, padx=1)
                cell.pack_propagate(False)

                if 1 <= cell_num <= days_in_month:
                    try:
                        cell_date = date(target_year, target_month, cell_num).isoformat()
                    except ValueError:
                        continue
                    s        = day_score(cell_date)
                    is_today = (cell_date == today.isoformat())
                    is_future= date(target_year, target_month, cell_num) > today

                    if is_future:
                        bg_c = CARD2; fg_c = DIM
                    elif s >= 80:  bg_c = "#2A2200"; fg_c = GOLD
                    elif s >= 60:  bg_c = "#082028"; fg_c = CYAN
                    elif s >= 40:  bg_c = "#251500"; fg_c = ORANGE
                    elif s > 0:    bg_c = "#250810"; fg_c = RED
                    else:          bg_c = CARD2;     fg_c = DIM

                    inner = ctk.CTkFrame(cell, fg_color=bg_c,
                                         corner_radius=cell_r,
                                         border_width=2 if is_today else 0,
                                         border_color=PINK)
                    inner.pack(fill="both", expand=True)
                    fsize = 7 if compact else 9
                    mk_label(inner, str(cell_num), size=fsize,
                             bold=is_today,
                             color=PINK if is_today else fg_c).pack(expand=True)
                else:
                    ctk.CTkFrame(cell, fg_color="transparent").pack(fill="both", expand=True)

    def _ov_spider_chart(self, parent):
        """Compact premium Kiviat chart for overview."""
        if not HAS_MPL: return
        today = date.today()
        day_labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        log = self.data.get("pomodoro_log", [])
        goal = self.data.get("daily_goal", 6)
        week_start = today - timedelta(days=today.weekday())
        this_week, last_week = [], []
        for i in range(7):
            d  = (week_start + timedelta(days=i)).isoformat()
            d2 = (week_start - timedelta(days=7) + timedelta(days=i)).isoformat()
            this_week.append(sum(1 for p in log if p.get("date","") == d and p.get("type","") == "work"))
            last_week.append(sum(1 for p in log if p.get("date","") == d2 and p.get("type","") == "work"))

        cf = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
        cf.pack(fill="x", padx=20, pady=6)
        leg = ctk.CTkFrame(cf, fg_color="transparent")
        leg.pack(anchor="e", padx=12, pady=(6,0))
        mk_label(leg, "● This week", size=9, color=PINK).pack(side="left", padx=4)
        mk_label(leg, "-- Last week", size=9, color=SUBTEXT).pack(side="left", padx=4)
        canvas = draw_kiviat(cf, this_week, last_week, goal, day_labels,
                             figsize=(3.8, 3.4), compact=True)
        canvas.get_tk_widget().pack(padx=8, pady=(0,8))

    # ══════════════════════════════════════════════════════════════════════
    # TESTS TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_tests_tab(self):
        tab = self.tab_frames["TESTS"]
        tab_header(tab, "◈", "TESTS", "Schedule exams and track countdown", GOLD)
        form = ctk.CTkFrame(tab, fg_color=CARD, corner_radius=10)
        form.pack(fill="x", padx=24, pady=(0,14))
        tk.Frame(form, bg=GOLD, height=2).pack(fill="x")
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=12)
        self.te_subj  = mk_entry(row, "Subject", 160); self.te_subj.pack(side="left", padx=(0,8))
        self.te_date  = mk_entry(row, "YYYY-MM-DD", 130); self.te_date.pack(side="left", padx=(0,8))
        self.te_time  = mk_entry(row, "HH:MM", 90); self.te_time.pack(side="left", padx=(0,8))
        self.te_note  = mk_entry(row, "Note (optional)", 220); self.te_note.pack(side="left", padx=(0,12))
        mk_btn(row, "＋  ADD TEST", self._add_test, GOLD, BG, "#B89020", 130, 34).pack(side="left")
        sf = mk_scroll(tab, BG); sf.pack(fill="both", expand=True, padx=24, pady=(0,12))
        self.tests_inner = sf

    def _refresh_tests(self):
        for w in self.tests_inner.winfo_children(): w.destroy()
        tests = sorted(self.data["tests"], key=lambda x: (x.get("date",""), x.get("time","")))
        if not tests:
            mk_label(self.tests_inner, "No tests scheduled.", size=12, color=DIM).pack(pady=30); return
        for t in tests:
            d  = days_until(t.get("date","")); uc = urgency_col(d)
            sc = get_subject_color(self.data, t.get("subject",""))
            card = Card(self.tests_inner, sc)
            card.pack(fill="x", pady=4)
            row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
            mk_label(row, t.get("subject",""), size=13, bold=True, color=sc).pack(side="left")
            right = ctk.CTkFrame(row, fg_color="transparent"); right.pack(side="right")
            mk_label(right, urgency_lbl(d), size=9, bold=True, color=uc).pack(side="left", padx=8)
            mk_del_btn(right, lambda tid=t["id"]: self._del_test(tid)).pack(side="left")
            mk_label(card.body, f"📅 {t.get('date','')}  ⏰ {t.get('time','')}",
                     size=10, color=SUBTEXT).pack(anchor="w", pady=(2,0))
            if t.get("note"):
                mk_label(card.body, t["note"], size=10, color=DIM).pack(anchor="w")

    def _add_test(self):
        subj = self.te_subj.get().strip(); dt = self.te_date.get().strip()
        tm = self.te_time.get().strip(); note = self.te_note.get().strip()
        if not subj or not dt: messagebox.showwarning("Missing","Subject and Date required."); return
        try: datetime.strptime(dt, "%Y-%m-%d")
        except ValueError: messagebox.showwarning("Format","Date must be YYYY-MM-DD"); return
        self.data["tests"].append({"id": nid(),"subject":subj,"date":dt,"time":tm,"note":note})
        save_data(self.data)
        for e in (self.te_subj,self.te_date,self.te_time,self.te_note): e.delete(0,"end")
        self._refresh_tests(); self._update_counts()

    def _del_test(self, tid):
        self.data["tests"] = [t for t in self.data["tests"] if t["id"] != tid]
        save_data(self.data); self._refresh_tests(); self._update_counts()

    # ══════════════════════════════════════════════════════════════════════
    # TASKS TAB  (with recurrence)
    # ══════════════════════════════════════════════════════════════════════

    def _build_tasks_tab(self):
        tab = self.tab_frames["TASKS"]
        tab_header(tab, "▣", "TASKS", "Priority-sorted tasks with recurrence", ORANGE)
        form = ctk.CTkFrame(tab, fg_color=CARD, corner_radius=10)
        form.pack(fill="x", padx=24, pady=(0,10))
        tk.Frame(form, bg=ORANGE, height=2).pack(fill="x")
        r1 = ctk.CTkFrame(form, fg_color="transparent"); r1.pack(fill="x", padx=14, pady=(10,4))
        self.ta_entry = mk_entry(r1, "Task description", 340); self.ta_entry.pack(side="left", padx=(0,8))
        self.ta_prio  = mk_combo(r1, PRIORITY_ORDER, 150); self.ta_prio.set("Immediate"); self.ta_prio.pack(side="left", padx=(0,8))
        self.ta_due   = mk_entry(r1, "Due YYYY-MM-DD", 140); self.ta_due.pack(side="left", padx=(0,8))
        r2 = ctk.CTkFrame(form, fg_color="transparent"); r2.pack(fill="x", padx=14, pady=(0,10))
        mk_label(r2, "Recurrence:", size=10, color=SUBTEXT).pack(side="left", padx=(0,6))
        self.ta_recur = mk_combo(r2, RECUR_OPTIONS, 110); self.ta_recur.set("None"); self.ta_recur.pack(side="left", padx=(0,12))
        mk_btn(r2, "＋  ADD TASK", self._add_task, ORANGE, BG, "#B06010", 130, 32).pack(side="left")

        ctrl = ctk.CTkFrame(tab, fg_color="transparent"); ctrl.pack(fill="x", padx=24, pady=(0,8))
        mk_label(ctrl, "SORT:", size=9, bold=True, color=SUBTEXT).pack(side="left", padx=(0,4))
        for s in ["Priority","Due Date","Added"]:
            mk_btn(ctrl, s, lambda x=s: self._sort_tasks(x), BORDER, SUBTEXT, HOVER, 80, 26, size=9).pack(side="left", padx=2)
        mk_label(ctrl, "   FILTER:", size=9, bold=True, color=SUBTEXT).pack(side="left", padx=(10,4))
        mk_btn(ctrl, "ALL", lambda: self._filter_tasks(None), BORDER, TEXT, HOVER, 46, 26, size=9).pack(side="left", padx=2)
        for p in PRIORITY_ORDER:
            mk_btn(ctrl, p[:3], lambda x=p: self._filter_tasks(x),
                   P_BG[p], P_COLOR[p], HOVER, 46, 26, size=9).pack(side="left", padx=2)

        sf = mk_scroll(tab, BG); sf.pack(fill="both", expand=True, padx=24, pady=(0,12))
        self.tasks_inner = sf

    def _spawn_recur_task(self, t):
        """Create the next instance of a recurring task."""
        recur = t.get("recur","None")
        if recur == "None": return
        today = date.today()
        delta = {"Daily":1,"Weekly":7,"Monthly":30}.get(recur, 0)
        if not delta: return
        new_due = (today + timedelta(days=delta)).isoformat()
        new_t = {k: v for k, v in t.items()}
        new_t["id"] = nid(); new_t["done"] = False
        new_t["due"] = new_due; new_t["added"] = datetime.now().isoformat()
        self.data["tasks"].append(new_t)

    def _refresh_tasks(self):
        for w in self.tasks_inner.winfo_children(): w.destroy()
        # Auto-spawn recurring tasks that are done
        for t in self.data["tasks"]:
            if t.get("done") and t.get("recur","None") != "None" and not t.get("spawned"):
                self._spawn_recur_task(t); t["spawned"] = True
        pending = [t for t in self.data["tasks"] if not t.get("done")]
        done    = [t for t in self.data["tasks"] if t.get("done")]
        if self._task_filter:
            pending = [t for t in pending if t.get("priority") == self._task_filter]
        pending = self._sort_list(pending, self._task_sort)
        if not pending and not done:
            mk_label(self.tasks_inner,"No tasks yet.",size=12,color=DIM).pack(pady=30); return
        for t in pending: self._task_card(self.tasks_inner, t)
        if done:
            tk.Frame(self.tasks_inner, bg=BORDER, height=1).pack(fill="x", pady=10)
            mk_label(self.tasks_inner, f"✓  COMPLETED  ({len(done)})", size=9, bold=True, color=DIM).pack(anchor="w", pady=(0,6))
            for t in done[-8:]: self._task_card(self.tasks_inner, t, done=True)

    def _task_card(self, parent, t, done=False):
        p = t.get("priority","Someday"); pc = P_COLOR.get(p, SUBTEXT)
        card = Card(parent, pc if not done else BORDER)
        if done: card.configure(fg_color="#0D0F18")
        card.pack(fill="x", pady=3)
        row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")

        var = ctk.BooleanVar(value=done)
        cb = ctk.CTkCheckBox(row, variable=var, text="",
                             checkbox_width=18, checkbox_height=18,
                             checkmark_color=BG, fg_color=pc, hover_color=pc,
                             border_color=BORDER2, width=24,
                             command=lambda tid=t["id"],v=var: self._toggle_task(tid,v))
        cb.pack(side="left", padx=(0,8))

        font_style = ctk.CTkFont(size=11, overstrike=done)
        ctk.CTkLabel(row, text=t.get("text",""), font=font_style,
                     text_color=SUBTEXT if done else TEXT,
                     fg_color="transparent").pack(side="left")

        right = ctk.CTkFrame(row, fg_color="transparent"); right.pack(side="right")
        if t.get("recur","None") != "None":
            mk_label(right, f"↻{t['recur'][0]}", size=9, bold=True, color=VIOLET).pack(side="left", padx=4)
        if not done:
            cp = mk_combo(right, PRIORITY_ORDER, 130, 28); cp.set(p); cp.pack(side="left", padx=6)
            cp.configure(command=lambda v, tid=t["id"]: self._change_prio(tid, v))
        mk_label(right, p, size=9, bold=True, color=pc).pack(side="left", padx=4)
        mk_del_btn(right, lambda tid=t["id"]: self._del_task(tid)).pack(side="left")

        if t.get("due") and t.get("due") not in ("","Due YYYY-MM-DD"):
            d = days_until(t["due"]); dc = urgency_col(d)
            mk_label(card.body, f"Due {t['due']}  •  {urgency_lbl(d)}",
                     size=10, color=dc).pack(anchor="w", pady=(2,0))

    def _add_task(self):
        text = self.ta_entry.get().strip(); prio = self.ta_prio.get()
        due  = self.ta_due.get().strip();  recur = self.ta_recur.get()
        if not text: messagebox.showwarning("Missing","Task text required."); return
        if due in ("","Due YYYY-MM-DD"): due = ""
        self.data["tasks"].append({"id":nid(),"text":text,"priority":prio,
                                    "due":due,"done":False,"recur":recur,"spawned":False,
                                    "added":datetime.now().isoformat()})
        save_data(self.data); self.ta_entry.delete(0,"end")
        self._refresh_tasks(); self._update_counts()
        show_toast(self, f"Task added — {prio}", color=P_COLOR.get(prio, CYAN), icon="▣")

    def _toggle_task(self, tid, var):
        for t in self.data["tasks"]:
            if t["id"] == tid: t["done"] = var.get()
        update_streak(self.data); save_data(self.data)
        self._refresh_tasks(); self._update_counts()
        if var.get():
            show_toast(self, "Task complete! Keep going.", color=GREEN, icon="✓")

    def _del_task(self, tid):
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != tid]
        save_data(self.data); self._refresh_tasks(); self._update_counts()

    def _change_prio(self, tid, p):
        for t in self.data["tasks"]:
            if t["id"] == tid: t["priority"] = p
        save_data(self.data); self._refresh_tasks()

    def _sort_tasks(self, by):  self._task_sort = by;  self._refresh_tasks()
    def _filter_tasks(self, p): self._task_filter = p; self._refresh_tasks()

    def _sort_list(self, tasks, by):
        if by == "Priority": return sorted(tasks, key=lambda t: PRIORITY_ORDER.index(t.get("priority","Someday")))
        if by == "Due Date":  return sorted(tasks, key=lambda t: t.get("due","9999"))
        if by == "Added":    return sorted(tasks, key=lambda t: t.get("added",""), reverse=True)
        return tasks

    # ══════════════════════════════════════════════════════════════════════
    # LISTS TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_lists_tab(self):
        tab = self.tab_frames["LISTS"]
        tab_header(tab, "◫", "LISTS", "Running master lists of work to do", BLUE)
        ctrl = ctk.CTkFrame(tab, fg_color="transparent"); ctrl.pack(fill="x", padx=24, pady=6)
        self.li_name = mk_entry(ctrl, "New list name", 260); self.li_name.pack(side="left", padx=(0,10))
        mk_btn(ctrl, "＋  CREATE LIST", self._add_list, BLUE, BG, "#1A5090", 150, 34).pack(side="left")
        sf = mk_scroll(tab, BG); sf.pack(fill="both", expand=True, padx=24, pady=(8,12))
        self.lists_inner = sf

    def _refresh_lists(self):
        for w in self.lists_inner.winfo_children(): w.destroy()
        if not self.data["lists"]:
            mk_label(self.lists_inner,"No lists created yet.",size=12,color=DIM).pack(pady=30); return
        for lst in self.data["lists"]: self._list_card(self.lists_inner, lst)

    def _list_card(self, parent, lst):
        outer = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
        outer.pack(fill="x", pady=6)
        tk.Frame(outer, bg=BLUE, height=2).pack(fill="x")
        inn = ctk.CTkFrame(outer, fg_color=CARD, corner_radius=0)
        inn.pack(fill="x", padx=16, pady=(8,12))

        hrow = ctk.CTkFrame(inn, fg_color="transparent"); hrow.pack(fill="x", pady=(0,6))
        mk_label(hrow, lst.get("name",""), size=14, bold=True, color=BLUE).pack(side="left")
        total = len(lst.get("items",[])); done_c = sum(1 for i in lst.get("items",[]) if i.get("done"))
        mk_label(hrow, f"{done_c}/{total}", size=10, color=SUBTEXT).pack(side="left", padx=10)
        mk_del_btn(hrow, lambda lid=lst["id"]: self._del_list(lid)).pack(side="right")

        if total:
            pb = mk_progress(inn, done_c/total, BLUE, BORDER, height=4)
            pb.pack(fill="x", pady=(0,8))

        for item in lst.get("items",[]):
            irow = ctk.CTkFrame(inn, fg_color="transparent"); irow.pack(fill="x", pady=1)
            var = ctk.BooleanVar(value=item.get("done",False))
            ctk.CTkCheckBox(irow, variable=var, text="",
                            checkbox_width=16, checkbox_height=16,
                            checkmark_color=BG, fg_color=BLUE, hover_color=BLUE,
                            border_color=BORDER2, width=22,
                            command=lambda lid=lst["id"],iid=item["id"],v=var: self._toggle_li(lid,iid,v)
                            ).pack(side="left")
            sty = "line" if item.get("done") else "normal"
            mk_label(irow, item.get("text",""), size=11,
                     color=SUBTEXT if item.get("done") else TEXT).pack(side="left", padx=4)
            mk_del_btn(irow, lambda lid=lst["id"],iid=item["id"]: self._del_li(lid,iid),
                       width=24, height=22).pack(side="right")

        arow = ctk.CTkFrame(inn, fg_color="transparent"); arow.pack(fill="x", pady=(8,0))
        e = mk_entry(arow, "Add item…", 320); e.pack(side="left", padx=(0,8))
        mk_btn(arow, "＋", lambda lid=lst["id"],en=e: self._add_li(lid,en),
               BLUE, BG, "#1A5090", 40, 34).pack(side="left")

    def _add_list(self):
        name = self.li_name.get().strip()
        if not name: return
        self.data["lists"].append({"id":nid(),"name":name,"items":[]})
        save_data(self.data); self.li_name.delete(0,"end"); self._refresh_lists()

    def _del_list(self, lid):
        self.data["lists"] = [l for l in self.data["lists"] if l["id"] != lid]
        save_data(self.data); self._refresh_lists()

    def _add_li(self, lid, e):
        text = e.get().strip()
        if not text: return
        for l in self.data["lists"]:
            if l["id"] == lid: l["items"].append({"id":nid(),"text":text,"done":False})
        save_data(self.data); e.delete(0,"end"); self._refresh_lists()

    def _del_li(self, lid, iid):
        for l in self.data["lists"]:
            if l["id"] == lid: l["items"] = [i for i in l["items"] if i["id"] != iid]
        save_data(self.data); self._refresh_lists()

    def _toggle_li(self, lid, iid, var):
        for l in self.data["lists"]:
            if l["id"] == lid:
                for item in l["items"]:
                    if item["id"] == iid: item["done"] = var.get()
        save_data(self.data); self._refresh_lists()

    # ══════════════════════════════════════════════════════════════════════
    # ASSIGNMENTS TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_assignments_tab(self):
        tab = self.tab_frames["ASSIGNMENTS"]
        tab_header(tab, "◧", "ASSIGNMENTS", "Track submissions and deadlines", RED)
        form = ctk.CTkFrame(tab, fg_color=CARD, corner_radius=10)
        form.pack(fill="x", padx=24, pady=(0,14))
        tk.Frame(form, bg=RED, height=2).pack(fill="x")
        row = ctk.CTkFrame(form, fg_color="transparent"); row.pack(fill="x", padx=14, pady=12)
        self.as_subj  = mk_entry(row, "Subject", 130);          self.as_subj.pack(side="left", padx=(0,8))
        self.as_title = mk_entry(row, "Assignment title", 240); self.as_title.pack(side="left", padx=(0,8))
        self.as_due   = mk_entry(row, "YYYY-MM-DD", 130);       self.as_due.pack(side="left", padx=(0,8))
        self.as_marks = mk_entry(row, "Marks", 70);             self.as_marks.pack(side="left", padx=(0,12))
        mk_btn(row, "＋  ADD", self._add_asgn, RED, TEXT, "#8B0020", 100, 34).pack(side="left")
        sf = mk_scroll(tab, BG); sf.pack(fill="both", expand=True, padx=24, pady=(0,12))
        self.asgn_inner = sf

    def _refresh_assignments(self):
        for w in self.asgn_inner.winfo_children(): w.destroy()
        pending = sorted([a for a in self.data["assignments"] if not a.get("submitted")],
                         key=lambda x: x.get("due","9999"))
        done    = [a for a in self.data["assignments"] if a.get("submitted")]
        if not pending and not done:
            mk_label(self.asgn_inner,"No assignments added.",size=12,color=DIM).pack(pady=30); return
        for a in pending: self._asgn_card(self.asgn_inner, a)
        if done:
            tk.Frame(self.asgn_inner, bg=BORDER, height=1).pack(fill="x", pady=10)
            mk_label(self.asgn_inner, f"✓  SUBMITTED  ({len(done)})", size=9, bold=True, color=DIM).pack(anchor="w", pady=(0,6))
            for a in done: self._asgn_card(self.asgn_inner, a, submitted=True)

    def _asgn_card(self, parent, a, submitted=False):
        d  = days_until(a.get("due","")); uc = GREEN if submitted else urgency_col(d)
        sc = get_subject_color(self.data, a.get("subject",""))
        card = Card(parent, sc if not submitted else BORDER)
        if submitted: card.configure(fg_color="#0D0F18")
        card.pack(fill="x", pady=3)
        row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
        subj_col = SUBTEXT if submitted else sc
        mk_label(row, f"[{a.get('subject','')}]", size=12, bold=True, color=subj_col).pack(side="left")
        mk_label(row, f"  {a.get('title','')}", size=12, bold=True,
                 color=SUBTEXT if submitted else TEXT).pack(side="left")
        right = ctk.CTkFrame(row, fg_color="transparent"); right.pack(side="right")
        if not submitted:
            dl = (f"{d}d left" if (d or 0) >= 0 else "OVERDUE") if d is not None else f"{a.get('due','')}"
            mk_label(right, dl, size=9, bold=True, color=uc).pack(side="left", padx=8)
            mk_btn(right, "✓ SUBMITTED", lambda aid=a["id"]: self._submit_asgn(aid),
                   GREEN, BG, "#0A4020", 120, 28, size=9).pack(side="left", padx=6)
        mk_del_btn(right, lambda aid=a["id"]: self._del_asgn(aid)).pack(side="left")
        if a.get("marks"):
            mk_label(card.body, f"Marks: {a['marks']}", size=10, color=SUBTEXT).pack(anchor="w", pady=(2,0))

    def _add_asgn(self):
        subj=self.as_subj.get().strip(); title=self.as_title.get().strip()
        due=self.as_due.get().strip();   marks=self.as_marks.get().strip()
        if not subj or not title: messagebox.showwarning("Missing","Subject and title required."); return
        self.data["assignments"].append({"id":nid(),"subject":subj,"title":title,
                                          "due":due,"marks":marks,"submitted":False})
        save_data(self.data)
        for e in (self.as_subj,self.as_title,self.as_due,self.as_marks): e.delete(0,"end")
        self._refresh_assignments(); self._update_counts()

    def _submit_asgn(self, aid):
        for a in self.data["assignments"]:
            if a["id"] == aid:
                a["submitted"] = True
                show_toast(self, "Assignment submitted!", color=GREEN, icon="◧")
        save_data(self.data); self._refresh_assignments(); self._update_counts()

    def _del_asgn(self, aid):
        self.data["assignments"] = [a for a in self.data["assignments"] if a["id"] != aid]
        save_data(self.data); self._refresh_assignments(); self._update_counts()

    # ══════════════════════════════════════════════════════════════════════
    # PRACTICALS TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_practicals_tab(self):
        tab = self.tab_frames["PRACTICALS"]
        tab_header(tab, "◩", "PRACTICALS", "Track lab experiments and writeup progress", GREEN)
        form = ctk.CTkFrame(tab, fg_color=CARD, corner_radius=10)
        form.pack(fill="x", padx=24, pady=(0,14))
        tk.Frame(form, bg=GREEN, height=2).pack(fill="x")
        row = ctk.CTkFrame(form, fg_color="transparent"); row.pack(fill="x", padx=14, pady=12)
        self.pr_subj  = mk_entry(row, "Subject", 130);           self.pr_subj.pack(side="left", padx=(0,8))
        self.pr_num   = mk_entry(row, "Exp No", 70);             self.pr_num.pack(side="left", padx=(0,8))
        self.pr_title = mk_entry(row, "Experiment title", 260);  self.pr_title.pack(side="left", padx=(0,8))
        self.pr_date  = mk_entry(row, "YYYY-MM-DD", 130);        self.pr_date.pack(side="left", padx=(0,12))
        mk_btn(row, "＋  ADD", self._add_prac, GREEN, BG, "#0A4020", 100, 34).pack(side="left")
        sf = mk_scroll(tab, BG); sf.pack(fill="both", expand=True, padx=24, pady=(0,12))
        self.prac_inner = sf

    def _refresh_practicals(self):
        for w in self.prac_inner.winfo_children(): w.destroy()
        pending = sorted([p for p in self.data["practicals"] if not p.get("done")],
                         key=lambda x: (x.get("subject",""), int(x.get("num","0") or 0)))
        done    = [p for p in self.data["practicals"] if p.get("done")]
        if not pending and not done:
            mk_label(self.prac_inner,"No practicals added.",size=12,color=DIM).pack(pady=30); return
        for p in pending: self._prac_card(self.prac_inner, p)
        if done:
            tk.Frame(self.prac_inner, bg=BORDER, height=1).pack(fill="x", pady=10)
            mk_label(self.prac_inner, f"✓  COMPLETED  ({len(done)})", size=9, bold=True, color=DIM).pack(anchor="w", pady=(0,6))
            for p in done: self._prac_card(self.prac_inner, p, done=True)

    def _prac_card(self, parent, p, done=False):
        sc   = get_subject_color(self.data, p.get("subject",""))
        card = Card(parent, sc if not done else BORDER)
        if done: card.configure(fg_color="#0D0F18")
        card.pack(fill="x", pady=3)
        row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
        mk_label(row, f"Exp {p.get('num','?')}  —  {p.get('title','')}",
                 size=12, bold=True, color=SUBTEXT if done else TEXT).pack(side="left")
        mk_del_btn(row, lambda pid=p["id"]: self._del_prac(pid)).pack(side="right")
        subj_col = SUBTEXT if done else sc
        mk_label(card.body, f"Subject: ", size=10, color=SUBTEXT).pack(side=None, anchor="w")
        row2 = ctk.CTkFrame(card.body, fg_color="transparent"); row2.pack(anchor="w")
        mk_label(row2, p.get("subject",""), size=10, bold=True, color=subj_col).pack(side="left")
        mk_label(row2, f"   Date: {p.get('date','')}", size=10, color=SUBTEXT).pack(side="left")
        srow = ctk.CTkFrame(card.body, fg_color="transparent"); srow.pack(anchor="w")
        for lbl_txt, key, col in [("PERFORMED","performed",GREEN),("WRITEUP DONE","writeup",BLUE),("SUBMITTED","submitted",GOLD)]:
            val = p.get(key, False)
            mk_btn(srow, ("✓ " if val else "○ ") + lbl_txt,
                   lambda pid=p["id"],k=key: self._toggle_prac(pid,k),
                   col if val else BORDER, BG if val else SUBTEXT, HOVER, 130, 30, size=9
                   ).pack(side="left", padx=(0,6))

    def _add_prac(self):
        subj=self.pr_subj.get().strip(); num=self.pr_num.get().strip()
        title=self.pr_title.get().strip(); dt=self.pr_date.get().strip()
        if not subj or not title: messagebox.showwarning("Missing","Subject and title required."); return
        self.data["practicals"].append({"id":nid(),"subject":subj,"num":num,
                                         "title":title,"date":dt,
                                         "performed":False,"writeup":False,"submitted":False,"done":False})
        save_data(self.data)
        for e in (self.pr_subj,self.pr_num,self.pr_title,self.pr_date): e.delete(0,"end")
        self._refresh_practicals(); self._update_counts()

    def _toggle_prac(self, pid, key):
        for p in self.data["practicals"]:
            if p["id"] == pid:
                p[key] = not p.get(key, False)
                p["done"] = p.get("performed") and p.get("writeup") and p.get("submitted")
                if p["done"]:
                    show_toast(self, "Practical complete!", color=GREEN, icon="◩")
                elif p.get(key):
                    stage_labels = {"performed":"Performed","writeup":"Writeup done","submitted":"Submitted"}
                    show_toast(self, stage_labels.get(key, key), color=GREEN, icon="◩")
        save_data(self.data); self._refresh_practicals(); self._update_counts()

    def _del_prac(self, pid):
        self.data["practicals"] = [p for p in self.data["practicals"] if p["id"] != pid]
        save_data(self.data); self._refresh_practicals(); self._update_counts()

    # ══════════════════════════════════════════════════════════════════════
    # SYLLABUS TRACKER TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_syllabus_tab(self):
        tab = self.tab_frames["SYLLABUS"]
        tab_header(tab, "⬢", "SYLLABUS", "Track topics per subject — see your coverage", VIOLET)

        # Add subject form
        form = ctk.CTkFrame(tab, fg_color=CARD, corner_radius=10)
        form.pack(fill="x", padx=24, pady=(0,14))
        tk.Frame(form, bg=VIOLET, height=2).pack(fill="x")
        row = ctk.CTkFrame(form, fg_color="transparent"); row.pack(fill="x", padx=14, pady=12)
        self.sy_subj = mk_entry(row, "Subject name (e.g. Engineering Physics)", 300)
        self.sy_subj.pack(side="left", padx=(0,10))
        mk_btn(row, "＋  ADD SUBJECT", self._add_subject, VIOLET, BG, "#6050C0", 160, 34).pack(side="left")
        mk_btn(row, "🎨 COLOURS", self._open_colour_manager, BORDER2, VIOLET, HOVER, 120, 34).pack(side="left", padx=8)

        sf = mk_scroll(tab, BG); sf.pack(fill="both", expand=True, padx=24, pady=(0,12))
        self.syl_inner = sf

    def _refresh_syllabus(self):
        for w in self.syl_inner.winfo_children(): w.destroy()
        if not self.data.get("syllabus"):
            mk_label(self.syl_inner, "No subjects added yet.", size=12, color=DIM).pack(pady=30)
            return
        for subj in self.data["syllabus"]:
            self._subject_card(self.syl_inner, subj)

    def _subject_card(self, parent, subj):
        topics = subj.get("topics", [])
        total  = len(topics)
        done   = sum(1 for t in topics if t.get("done"))
        pct    = int((done/total)*100) if total else 0
        sc     = get_subject_color(self.data, subj.get("name",""))

        outer = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
        outer.pack(fill="x", pady=6)
        tk.Frame(outer, bg=sc, height=2).pack(fill="x")
        inn = ctk.CTkFrame(outer, fg_color=CARD, corner_radius=0)
        inn.pack(fill="x", padx=16, pady=(8,12))

        # Header
        hrow = ctk.CTkFrame(inn, fg_color="transparent"); hrow.pack(fill="x", pady=(0,4))
        mk_label(hrow, subj.get("name",""), size=14, bold=True, color=sc).pack(side="left")
        mk_label(hrow, f"  {done}/{total} topics  ({pct}%)", size=10, color=SUBTEXT).pack(side="left")
        mk_del_btn(hrow, lambda sid=subj["id"]: self._del_subject(sid),
                   width=110, height=26).pack(side="right")

        # Progress bar
        pb = mk_progress(inn, pct/100, sc, BORDER, height=6)
        pb.pack(fill="x", pady=(0,10))

        # Topics grid
        topics_frame = ctk.CTkFrame(inn, fg_color="transparent")
        topics_frame.pack(fill="x")
        cols = 2
        for i, topic in enumerate(topics):
            trow = ctk.CTkFrame(topics_frame, fg_color=CARD2, corner_radius=6)
            trow.grid(row=i//cols, column=i%cols, padx=(0,8), pady=3, sticky="ew")
            topics_frame.grid_columnconfigure(i%cols, weight=1)
            var = ctk.BooleanVar(value=topic.get("done", False))
            ctk.CTkCheckBox(trow, variable=var, text="",
                            checkbox_width=16, checkbox_height=16,
                            checkmark_color=BG, fg_color=sc, hover_color=sc,
                            border_color=BORDER2, width=22,
                            command=lambda sid=subj["id"],tid=topic["id"],v=var: self._toggle_topic(sid,tid,v)
                            ).pack(side="left", padx=(8,4), pady=6)
            mk_label(trow, topic.get("name",""), size=10,
                     color=SUBTEXT if topic.get("done") else TEXT).pack(side="left", pady=6)
            mk_del_btn(trow, lambda sid=subj["id"],tid=topic["id"]: self._del_topic(sid,tid),
                       width=24, height=22).pack(side="right", padx=4)

        # Add topic
        arow = ctk.CTkFrame(inn, fg_color="transparent"); arow.pack(fill="x", pady=(10,0))
        e = mk_entry(arow, "Add topic (e.g. Laser Principles)", 340); e.pack(side="left", padx=(0,8))
        mk_btn(arow, "＋ TOPIC", lambda sid=subj["id"],en=e: self._add_topic(sid,en),
               sc, BG, HOVER, 100, 34).pack(side="left")

    def _add_subject(self):
        name = self.sy_subj.get().strip()
        if not name: return
        self.data["syllabus"].append({"id":nid(),"name":name,"topics":[]})
        save_data(self.data); self.sy_subj.delete(0,"end")
        self._refresh_syllabus(); self._update_counts()

    def _del_subject(self, sid):
        self.data["syllabus"] = [s for s in self.data["syllabus"] if s["id"] != sid]
        save_data(self.data); self._refresh_syllabus(); self._update_counts()

    def _add_topic(self, sid, e):
        name = e.get().strip()
        if not name: return
        for s in self.data["syllabus"]:
            if s["id"] == sid: s["topics"].append({"id":nid(),"name":name,"done":False})
        save_data(self.data); e.delete(0,"end"); self._refresh_syllabus()

    def _del_topic(self, sid, tid):
        for s in self.data["syllabus"]:
            if s["id"] == sid: s["topics"] = [t for t in s["topics"] if t["id"] != tid]
        save_data(self.data); self._refresh_syllabus()

    def _toggle_topic(self, sid, tid, var):
        for s in self.data["syllabus"]:
            if s["id"] == sid:
                for t in s["topics"]:
                    if t["id"] == tid: t["done"] = var.get()
        save_data(self.data); self._refresh_syllabus()

    # ══════════════════════════════════════════════════════════════════════
    # POMODORO TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_pomodoro_tab(self):
        tab = self.tab_frames["POMODORO"]
        tab_header(tab, "◎", "POMODORO", "Focused work sessions with built-in timer", PINK)

        center = ctk.CTkFrame(tab, fg_color="transparent")
        center.pack(expand=True, fill="both")

        # Timer display
        timer_card = ctk.CTkFrame(center, fg_color=CARD, corner_radius=16, width=420, height=320)
        timer_card.pack(pady=20)
        timer_card.pack_propagate(False)
        tk.Frame(timer_card, bg=PINK, height=3).pack(fill="x")

        self.pomo_mode_lbl = mk_label(timer_card, "FOCUS SESSION", size=13, bold=True, color=PINK)
        self.pomo_mode_lbl.pack(pady=(20,4))

        self.pomo_timer_lbl = mk_label(timer_card, "25:00", size=52, bold=True, color=TEXT)
        self.pomo_timer_lbl.pack(pady=4)

        self.pomo_session_lbl = mk_label(timer_card, "Session 0  •  Today: 0", size=10, color=SUBTEXT)
        self.pomo_session_lbl.pack(pady=(0,10))

        # Progress bar
        self.pomo_pb = mk_progress(timer_card, 0.0, PINK, BORDER,
                                   height=6, width=340, duration_ms=800)
        self.pomo_pb.pack(pady=(0,16))

        # Buttons
        btn_row = ctk.CTkFrame(timer_card, fg_color="transparent")
        btn_row.pack()
        self.pomo_start_btn = mk_btn(btn_row, "▶  START", self._pomo_start_stop,
                                      PINK, BG, "#C04080", 130, 40, size=13)
        self.pomo_start_btn.pack(side="left", padx=8)
        mk_btn(btn_row, "↺  RESET", self._pomo_reset, BORDER2, TEXT, HOVER, 110, 40, size=12).pack(side="left", padx=8)

        # Settings
        settings = ctk.CTkFrame(center, fg_color=CARD, corner_radius=10)
        settings.pack(padx=60, pady=8, fill="x")
        tk.Frame(settings, bg=BORDER2, height=1).pack(fill="x")
        srow = ctk.CTkFrame(settings, fg_color="transparent"); srow.pack(padx=20, pady=12)
        mk_label(srow, "Work (min):", size=11, color=SUBTEXT).pack(side="left", padx=(0,6))
        self.pomo_work_entry = mk_entry(srow, "25", 60, 30); self.pomo_work_entry.pack(side="left", padx=(0,16))
        mk_label(srow, "Short break:", size=11, color=SUBTEXT).pack(side="left", padx=(0,6))
        self.pomo_short_entry = mk_entry(srow, "5", 60, 30); self.pomo_short_entry.pack(side="left", padx=(0,16))
        mk_label(srow, "Long break:", size=11, color=SUBTEXT).pack(side="left", padx=(0,6))
        self.pomo_long_entry = mk_entry(srow, "15", 60, 30); self.pomo_long_entry.pack(side="left", padx=(0,16))
        mk_btn(srow, "APPLY", self._pomo_apply_settings, BORDER2, CYAN, HOVER, 70, 30, size=9).pack(side="left")

        # Task selector
        task_row = ctk.CTkFrame(settings, fg_color="transparent"); task_row.pack(padx=20, pady=(0,10))
        mk_label(task_row, "Working on:", size=11, color=SUBTEXT).pack(side="left", padx=(0,6))
        self.pomo_task_combo = mk_combo(task_row, ["(no task selected)"], 320, 30)
        self.pomo_task_combo.pack(side="left")
        mk_btn(task_row, "↻", self._pomo_refresh_tasks, BORDER2, CYAN, HOVER, 34, 30, size=12).pack(side="left", padx=6)

        # Log
        section_header(center, "◎  TODAY'S LOG", PINK)
        sf = mk_scroll(center, BG); sf.pack(fill="both", expand=True, padx=24, pady=(4,12))
        self.pomo_log_inner = sf
        self._pomo_refresh_log()
        self._pomo_refresh_tasks()

    def _pomo_work_secs(self):
        try: return int(self.pomo_work_entry.get()) * 60
        except: return 25*60

    def _pomo_short_secs(self):
        try: return int(self.pomo_short_entry.get()) * 60
        except: return 5*60

    def _pomo_long_secs(self):
        try: return int(self.pomo_long_entry.get()) * 60
        except: return 15*60

    def _pomo_apply_settings(self):
        self._pomo_reset()

    def _pomo_start_stop(self):
        if not self._pomo_stop_event.is_set():
            # Currently running → pause
            self._pomo_stop_event.set()
            self.pomo_start_btn.configure(text="▶  START")
        else:
            # Stopped → start
            self._pomo_stop_event.clear()
            self.pomo_start_btn.configure(text="⏸  PAUSE")
            self._pomo_thread = threading.Thread(
                target=self._pomo_tick_loop, daemon=True)
            self._pomo_thread.start()

    def _pomo_reset(self):
        self._pomo_stop_event.set()          # signal thread to stop
        self.pomo_start_btn.configure(text="▶  START")
        self._pomo_mode    = "work"
        self.pomo_mode_lbl.configure(text="FOCUS SESSION", text_color=PINK)
        self._pomo_elapsed = 0
        self._pomo_seconds = self._pomo_work_secs()
        self._pomo_update_display()

    def _pomo_tick_loop(self):
        total = self._pomo_seconds
        while not self._pomo_stop_event.is_set() and self._pomo_elapsed < total:
            # sleep in short chunks so the event is checked frequently
            if self._pomo_stop_event.wait(timeout=1.0):
                return   # event was set — stop cleanly
            self._pomo_elapsed += 1
            self.after(0, self._pomo_update_display)
        if not self._pomo_stop_event.is_set():
            self.after(0, self._pomo_session_done)

    def _pomo_session_done(self):
        self._pomo_stop_event.set()          # mark as stopped
        self.pomo_start_btn.configure(text="▶  START")
        session_type = self._pomo_mode

        # Log the session
        self.data["pomodoro_log"].append({
            "id": nid(), "date": date.today().isoformat(),
            "time": datetime.now().strftime("%H:%M"),
            "type": session_type,
            "task": self.pomo_task_combo.get(),
            "duration_min": (self._pomo_work_secs() if session_type=="work" else self._pomo_short_secs())//60
        })
        save_data(self.data)

        if session_type == "work":
            self._pomo_sessions += 1
            msg = f"Focus session #{self._pomo_sessions} complete! Take a break."
            send_notify("🍅 Pomodoro Done", msg)
            show_toast(self, f"Focus session #{self._pomo_sessions} done!", color=PINK, icon="◎")
            # Switch to break
            if self._pomo_sessions % 4 == 0:
                self._pomo_mode = "long_break"
                self._pomo_seconds = self._pomo_long_secs()
                self.pomo_mode_lbl.configure(text="LONG BREAK", text_color=GREEN)
            else:
                self._pomo_mode = "break"
                self._pomo_seconds = self._pomo_short_secs()
                self.pomo_mode_lbl.configure(text="SHORT BREAK", text_color=CYAN)
        else:
            self._pomo_mode = "work"
            self._pomo_seconds = self._pomo_work_secs()
            self.pomo_mode_lbl.configure(text="FOCUS SESSION", text_color=PINK)
            send_notify("⚡ Break Over", "Time to focus again!")

        self._pomo_elapsed = 0
        self._pomo_update_display()
        self._pomo_refresh_log()

    def _pomo_update_display(self):
        total = self._pomo_seconds
        remaining = max(0, total - self._pomo_elapsed)
        m, s = divmod(remaining, 60)
        self.pomo_timer_lbl.configure(text=f"{m:02d}:{s:02d}")
        _pomo_val = self._pomo_elapsed / total if total else 0
        # Use direct set for live timer (no animation lag every second)
        self.pomo_pb.set(_pomo_val)
        self.pomo_pb._tween_current = _pomo_val
        today_count = sum(1 for p in self.data.get("pomodoro_log",[])
                          if p.get("date","") == date.today().isoformat() and p.get("type","") == "work")
        self.pomo_session_lbl.configure(
            text=f"Session {self._pomo_sessions}  •  Today: {today_count}")
        goal = self.data.get("daily_goal", 6)
        today_iso = date.today().isoformat()
        if today_count == goal and self._goal_toast_date != today_iso:
            self._goal_toast_date = today_iso
            show_toast(self, f"🎯 Daily goal reached! {goal} sessions today.", color=GOLD, icon="★")

    def _pomo_refresh_tasks(self):
        tasks = ["(no task selected)"] + [t.get("text","") for t in self.data["tasks"] if not t.get("done")]
        self.pomo_task_combo.configure(values=tasks)

    def _pomo_refresh_log(self):
        for w in self.pomo_log_inner.winfo_children(): w.destroy()
        today = date.today().isoformat()
        log = [p for p in self.data.get("pomodoro_log",[]) if p.get("date","") == today]
        if not log:
            mk_label(self.pomo_log_inner, "No sessions today. Start your first Pomodoro!",
                     size=11, color=DIM).pack(pady=20); return
        for entry in reversed(log[-20:]):
            typ = entry.get("type","work")
            col = PINK if typ=="work" else (CYAN if typ=="break" else GREEN)
            card = Card(self.pomo_log_inner, col)
            card.pack(fill="x", pady=3)
            row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
            lbl = "🍅 FOCUS" if typ=="work" else ("☕ SHORT BREAK" if typ=="break" else "🌿 LONG BREAK")
            mk_label(row, lbl, size=11, bold=True, color=col).pack(side="left")
            mk_label(row, entry.get("time",""), size=10, color=SUBTEXT).pack(side="left", padx=8)
            mk_label(row, f"{entry.get('duration_min','?')} min", size=10, color=SUBTEXT).pack(side="right")
            task = entry.get("task","")
            if task and task != "(no task selected)":
                mk_label(card.body, f"↳ {task}", size=10, color=DIM).pack(anchor="w")

    # ══════════════════════════════════════════════════════════════════════
    # NOTES TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_notes_tab(self):
        tab = self.tab_frames["NOTES"]
        tab_header(tab, "✎", "NOTES", "Subject-linked notes with timestamps", CYAN)

        # Top bar: new note + search
        topbar = ctk.CTkFrame(tab, fg_color="transparent")
        topbar.pack(fill="x", padx=24, pady=(0,10))
        mk_btn(topbar, "＋  NEW NOTE", self._new_note, CYAN, BG, "#008AB0", 140, 34).pack(side="left", padx=(0,10))
        self.note_search = mk_entry(topbar, "Search notes…", 260, 34)
        self.note_search.pack(side="left", padx=(0,8))
        mk_btn(topbar, "🔍", self._search_notes, BORDER2, TEXT, HOVER, 40, 34).pack(side="left")

        # Two-panel layout: list on left, editor on right
        pane = ctk.CTkFrame(tab, fg_color="transparent")
        pane.pack(fill="both", expand=True, padx=24, pady=(0,12))
        pane.grid_columnconfigure(0, weight=1)
        pane.grid_columnconfigure(1, weight=3)
        pane.grid_rowconfigure(0, weight=1)

        # Left: note list
        list_frame = ctk.CTkFrame(pane, fg_color=CARD, corner_radius=10)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        tk.Frame(list_frame, bg=CYAN, height=2).pack(fill="x")
        mk_label(list_frame, "  ALL NOTES", size=10, bold=True, color=SUBTEXT).pack(anchor="w", padx=12, pady=(8,4))
        self.notes_list_sf = mk_scroll(list_frame, CARD)
        self.notes_list_sf.pack(fill="both", expand=True, padx=4, pady=(0,8))

        # Right: editor
        edit_frame = ctk.CTkFrame(pane, fg_color=CARD, corner_radius=10)
        edit_frame.grid(row=0, column=1, sticky="nsew")
        tk.Frame(edit_frame, bg=CYAN, height=2).pack(fill="x")

        edit_top = ctk.CTkFrame(edit_frame, fg_color="transparent")
        edit_top.pack(fill="x", padx=14, pady=(10,6))
        self.note_title_entry = mk_entry(edit_top, "Note title…", 300, 34)
        self.note_title_entry.pack(side="left", padx=(0,8))
        self.note_subject_combo = mk_combo(edit_top, ["General"], 160, 34)
        self.note_subject_combo.set("General")
        self.note_subject_combo.pack(side="left", padx=(0,8))
        mk_btn(edit_top, "💾 SAVE NOTE", self._save_note, CYAN, BG, "#008AB0", 120, 34).pack(side="left", padx=(0,6))
        mk_del_btn(edit_top, self._delete_note, width=100, height=34).pack(side="left")

        self.note_ts_lbl = mk_label(edit_frame, "", size=9, color=SUBTEXT)
        self.note_ts_lbl.pack(anchor="w", padx=16)

        self.note_body = ctk.CTkTextbox(
            edit_frame, fg_color=CARD2, text_color=TEXT,
            font=ctk.CTkFont(size=12), corner_radius=8,
            border_width=1, border_color=BORDER2,
            scrollbar_button_color=BORDER2,
            wrap="word"
        )
        self.note_body.pack(fill="both", expand=True, padx=14, pady=(6,14))
        self._note_load_placeholder()

    def _refresh_notes_list(self, filter_text=""):
        for w in self.notes_list_sf.winfo_children():
            w.destroy()
        notes = self.data.get("notes", [])
        if filter_text:
            ft = filter_text.lower()
            notes = [n for n in notes if ft in n.get("title","").lower()
                     or ft in n.get("body","").lower()
                     or ft in n.get("subject","").lower()]
        notes = sorted(notes, key=lambda n: n.get("updated",""), reverse=True)
        if not notes:
            mk_label(self.notes_list_sf, "No notes yet. Click + NEW NOTE to start.", size=10, color=DIM).pack(pady=20)
            return
        for note in notes:
            self._note_list_item(self.notes_list_sf, note)
        # Update subject combo from existing subjects
        subjects = sorted(set(["General"] + [n.get("subject","General") for n in self.data.get("notes",[])]))
        self.note_subject_combo.configure(values=subjects)

    def _note_list_item(self, parent, note):
        is_sel = self._note_selected == note["id"]
        bg = HOVER if is_sel else "transparent"
        item = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6, cursor="hand2")
        item.pack(fill="x", pady=2, padx=4)

        title = note.get("title","Untitled") or "Untitled"
        subj  = note.get("subject","General")
        ts    = note.get("updated","")[:10]
        preview = note.get("body","")[:50].replace("\n"," ")

        mk_label(item, title, size=11, bold=True, color=CYAN if is_sel else TEXT).pack(anchor="w", padx=8, pady=(6,0))
        nsc = get_subject_color(self.data, subj) if subj != "General" else SUBTEXT
        mk_label(item, f"● {subj}", size=9, bold=True, color=nsc).pack(anchor="w", padx=8)
        mk_label(item, ts, size=9, color=SUBTEXT).pack(anchor="w", padx=8)
        if preview:
            mk_label(item, preview + ("…" if len(note.get("body","")) > 50 else ""),
                     size=9, color=DIM).pack(anchor="w", padx=8, pady=(0,6))

        def _click(e=None, note_id=note["id"]):
            self._note_selected = note_id
            self._load_note(note_id)
            self._refresh_notes_list()
        for w in (item,):
            item.bind("<Button-1>", _click)
        for child in item.winfo_children():
            child.bind("<Button-1>", _click)

    def _note_load_placeholder(self):
        self.note_title_entry.delete(0, "end")
        self.note_body.delete("1.0", "end")
        self.note_body.insert("1.0", "Select a note from the left, or click + NEW NOTE to start writing.")
        self.note_ts_lbl.configure(text="")
        self._note_selected = None

    def _load_note(self, nid):
        note = next((n for n in self.data.get("notes",[]) if n["id"] == nid), None)
        if not note: return
        self.note_title_entry.delete(0, "end")
        self.note_title_entry.insert(0, note.get("title",""))
        self.note_subject_combo.set(note.get("subject","General"))
        self.note_body.delete("1.0", "end")
        self.note_body.insert("1.0", note.get("body",""))
        ts = note.get("updated","")
        self.note_ts_lbl.configure(text=f"  Last edited: {ts}")

    def _new_note(self):
        new_note = {
            "id": nid(), "title": "New Note",
            "subject": "General", "body": "",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }
        self.data["notes"].append(new_note)
        self._note_selected = new_note["id"]
        save_data(self.data)
        self._refresh_notes_list()
        self._load_note(new_note["id"])

    def _save_note(self):
        if not self._note_selected:
            # create a new one
            self._new_note()
            return
        title = self.note_title_entry.get().strip() or "Untitled"
        subject = self.note_subject_combo.get() or "General"
        body = self.note_body.get("1.0", "end").rstrip()
        for note in self.data["notes"]:
            if note["id"] == self._note_selected:
                note["title"]   = title
                note["subject"] = subject
                note["body"]    = body
                note["updated"] = datetime.now().isoformat()
        save_data(self.data)
        self._refresh_notes_list()
        self.note_ts_lbl.configure(text=f"  Last edited: {datetime.now().isoformat()[:19]}")
        show_toast(self, "Note saved.", color=CYAN, icon="✎")

    def _delete_note(self):
        if not self._note_selected: return
        self.data["notes"] = [n for n in self.data["notes"] if n["id"] != self._note_selected]
        save_data(self.data)
        self._note_load_placeholder()
        self._refresh_notes_list()

    def _search_notes(self):
        q = self.note_search.get().strip()
        self._refresh_notes_list(filter_text=q)

    # ══════════════════════════════════════════════════════════════════════
    # PRODUCTIVITY TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_productivity_tab(self):
        tab = self.tab_frames["PRODUCTIVITY"]
        tab_header(tab, "◐", "PRODUCTIVITY", "Focus analytics — spider chart, scores, streaks", PINK)
        sf = mk_scroll(tab, BG)
        sf.pack(fill="both", expand=True)
        self._prod_root = sf

    def _refresh_productivity(self):
        for w in self._prod_root.winfo_children():
            w.destroy()
        if not HAS_MPL:
            mk_label(self._prod_root,
                     "Install matplotlib: pip install matplotlib",
                     size=12, color=DIM).pack(pady=40)
            return
        import numpy as np
        root     = self._prod_root
        log      = self.data.get("pomodoro_log", [])
        today    = date.today()
        goal     = self.data.get("daily_goal", 6)
        safe_g   = max(goal, 1)

        # ── Helpers ──────────────────────────────────────────────────────
        def day_sessions(d_iso):
            return sum(1 for p in log if p.get("date","") == d_iso
                       and p.get("type","") == "work")

        def day_score(d_iso):
            return min(100, int((day_sessions(d_iso) / safe_g) * 100))

        def score_col(s):
            if s >= 80: return GOLD
            if s >= 60: return CYAN
            if s >= 40: return ORANGE
            if s >  0:  return RED
            return DIM

        def score_grade(s):
            if s >= 80: return "EXCELLENT"
            if s >= 60: return "GOOD"
            if s >= 40: return "AVERAGE"
            if s >  0:  return "NEEDS WORK"
            return "NO DATA"

        def week_sessions(week_offset=0):
            ws = today - timedelta(days=today.weekday()) - timedelta(weeks=week_offset)
            return [day_sessions((ws + timedelta(days=i)).isoformat()) for i in range(7)]

        def period_score(days_list):
            scores = [day_score(d) for d in days_list if day_sessions(d) > 0]
            return int(sum(scores) / len(scores)) if scores else 0

        yesterday     = (today - timedelta(days=1)).isoformat()
        today_iso     = today.isoformat()
        week_start    = today - timedelta(days=today.weekday())
        week_days     = [(week_start + timedelta(days=i)).isoformat() for i in range(7)]
        month_start   = today.replace(day=1)
        month_days    = [(month_start + timedelta(days=i)).isoformat()
                         for i in range((today - month_start).days + 1)]

        score_today   = day_score(today_iso)
        score_yest    = day_score(yesterday)
        score_week    = period_score(week_days)
        score_month   = period_score(month_days)

        tw_sessions   = week_sessions(0)
        lw_sessions   = week_sessions(1)
        day_labels    = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

        # ══════════════════════════════════════════════════════════════════
        # ROW 0 — Goal setter
        # ══════════════════════════════════════════════════════════════════
        gc = ctk.CTkFrame(root, fg_color=CARD, corner_radius=12)
        gc.pack(fill="x", padx=24, pady=(12,6))
        tk.Frame(gc, bg=PINK, height=2).pack(fill="x")
        gcr = ctk.CTkFrame(gc, fg_color="transparent")
        gcr.pack(fill="x", padx=18, pady=10)
        mk_label(gcr, "⚙  DAILY SESSION GOAL", size=10, bold=True, color=SUBTEXT).pack(side="left")
        self._goal_entry = mk_entry(gcr, str(goal), 60, 28)
        self._goal_entry.pack(side="left", padx=10)
        mk_btn(gcr, "SET", self._set_daily_goal, PINK, BG, "#C04080", 56, 28, size=10).pack(side="left")
        mk_label(gcr, "sessions / day", size=10, color=SUBTEXT).pack(side="left", padx=8)
        streak = self.data.get("streak", {}).get("count", 0)
        mk_label(gcr, f"🔥 {streak} day streak", size=10, bold=True, color=ORANGE).pack(side="right", padx=8)

        # ══════════════════════════════════════════════════════════════════
        # ROW 1 — Score timeline: Today / Yesterday / This Week / This Month
        # ══════════════════════════════════════════════════════════════════
        mk_label(root, "  PERFORMANCE SCORES", size=9, bold=True, color=SUBTEXT
                 ).pack(anchor="w", padx=28, pady=(10,4))
        scores_row = ctk.CTkFrame(root, fg_color="transparent")
        scores_row.pack(fill="x", padx=24, pady=(0,8))
        for col_i, (period, score, sessions_n, sub) in enumerate([
            ("TODAY",      score_today, day_sessions(today_iso),     today.strftime("%d %b")),
            ("YESTERDAY",  score_yest,  day_sessions(yesterday),     (today-timedelta(1)).strftime("%d %b")),
            ("THIS WEEK",  score_week,  sum(tw_sessions),             f"{week_start.strftime('%d %b')} – now"),
            ("THIS MONTH", score_month, sum(day_sessions(d) for d in month_days),
                                                                      today.strftime("%B %Y")),
        ]):
            sc  = score_col(score)
            crd = ctk.CTkFrame(scores_row, fg_color=CARD, corner_radius=12)
            crd.grid(row=0, column=col_i, sticky="nsew",
                     padx=(0,10) if col_i < 3 else (0,0))
            scores_row.grid_columnconfigure(col_i, weight=1)
            tk.Frame(crd, bg=sc, height=2).pack(fill="x")
            mk_label(crd, period, size=9, bold=True, color=SUBTEXT).pack(pady=(10,0))
            mk_label(crd, str(score), size=34, bold=True, color=sc).pack()
            mk_label(crd, "/ 100", size=9, color=SUBTEXT).pack()
            pb2 = mk_progress(crd, score/100, sc, BORDER, height=5)
            pb2.pack(fill="x", padx=14, pady=(4,2))
            mk_label(crd, score_grade(score), size=9, bold=True, color=sc).pack()
            mk_label(crd, f"{sessions_n} sessions  •  {sub}", size=8, color=DIM
                     ).pack(pady=(0,10))

        # ══════════════════════════════════════════════════════════════════
        # ROW 2 — Weekly report card
        # ══════════════════════════════════════════════════════════════════
        mk_label(root, "  WEEKLY REPORT CARD", size=9, bold=True, color=SUBTEXT
                 ).pack(anchor="w", padx=28, pady=(6,4))
        wrc = ctk.CTkFrame(root, fg_color=CARD, corner_radius=12)
        wrc.pack(fill="x", padx=24, pady=(0,8))
        tk.Frame(wrc, bg=GOLD, height=2).pack(fill="x")

        wrc_inner = ctk.CTkFrame(wrc, fg_color="transparent")
        wrc_inner.pack(fill="x", padx=18, pady=12)

        # Stats
        best_day_idx  = tw_sessions.index(max(tw_sessions))
        worst_active  = [v for v in tw_sessions if v > 0]
        worst_val     = min(worst_active) if worst_active else 0
        worst_day_idx = tw_sessions.index(worst_val) if worst_active else 0
        goal_hit_days = sum(1 for v in tw_sessions if v >= safe_g)
        total_focus_m = sum(
            p.get("duration_min", 0) for p in log
            if p.get("date","") in week_days and p.get("type","") == "work"
        )

        stat_items = [
            ("BEST DAY",         day_labels[best_day_idx],        GOLD),
            ("GOAL HIT",         f"{goal_hit_days}/7 days",       CYAN),
            ("TOTAL SESSIONS",   str(sum(tw_sessions)),            PINK),
            ("TOTAL FOCUS TIME", f"{total_focus_m} min",          VIOLET),
            ("WEEK SCORE",       f"{score_week}/100",              score_col(score_week)),
            ("VS LAST WEEK",     ("+" if sum(tw_sessions)>=sum(lw_sessions) else "") +
                                 str(sum(tw_sessions)-sum(lw_sessions)),
                                 GOLD if sum(tw_sessions)>=sum(lw_sessions) else RED),
        ]
        for ci, (lbl2, val2, col2) in enumerate(stat_items):
            sf2 = ctk.CTkFrame(wrc_inner, fg_color=CARD2, corner_radius=8)
            sf2.grid(row=ci//3, column=ci%3, sticky="ew",
                     padx=(0,8) if ci%3 < 2 else 0, pady=(0,8) if ci//3 == 0 else 0)
            wrc_inner.grid_columnconfigure(ci%3, weight=1)
            mk_label(sf2, lbl2, size=8, bold=True, color=SUBTEXT).pack(pady=(8,0))
            mk_label(sf2, val2, size=16, bold=True, color=col2).pack(pady=(2,8))

        # Per-day goal bar
        day_bar_row = ctk.CTkFrame(wrc, fg_color="transparent")
        day_bar_row.pack(fill="x", padx=18, pady=(0,14))
        for i, (day, cnt) in enumerate(zip(day_labels, tw_sessions)):
            hit   = cnt >= safe_g
            dc2   = ctk.CTkFrame(day_bar_row, fg_color="transparent")
            dc2.pack(side="left", expand=True, fill="x", padx=3)
            bar_h = max(6, min(60, int((cnt / safe_g) * 60)))
            bar_c = GOLD if hit else (CYAN if cnt > 0 else BORDER)
            # spacer to bottom-align bars
            ctk.CTkFrame(dc2, fg_color="transparent", height=max(0, 60-bar_h)).pack()
            ctk.CTkFrame(dc2, fg_color=bar_c, width=22, height=bar_h,
                         corner_radius=4).pack()
            mk_label(dc2, day, size=8, color=SUBTEXT if not hit else TEXT).pack(pady=(2,0))
            mk_label(dc2, str(cnt), size=8, bold=True, color=bar_c).pack()

        # ══════════════════════════════════════════════════════════════════
        # ROW 3 — Charts: Spider + Best Hours
        # ══════════════════════════════════════════════════════════════════
        mk_label(root, "  FOCUS ANALYTICS", size=9, bold=True, color=SUBTEXT
                 ).pack(anchor="w", padx=28, pady=(6,4))
        charts_row = ctk.CTkFrame(root, fg_color="transparent")
        charts_row.pack(fill="x", padx=24, pady=(0,8))
        charts_row.grid_columnconfigure(0, weight=1)
        charts_row.grid_columnconfigure(1, weight=1)

        # Spider chart
        sp_card = ctk.CTkFrame(charts_row, fg_color=CARD, corner_radius=12)
        sp_card.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        tk.Frame(sp_card, bg=PINK, height=2).pack(fill="x")
        mk_label(sp_card, "WEEKLY FOCUS RADAR", size=11, bold=True, color=PINK).pack(pady=(10,0))
        leg_r = ctk.CTkFrame(sp_card, fg_color="transparent"); leg_r.pack()
        mk_label(leg_r, "● This week", size=9, color=PINK).pack(side="left", padx=6)
        mk_label(leg_r, "-- Last week", size=9, color=SUBTEXT).pack(side="left", padx=6)
        c1 = draw_kiviat(sp_card, tw_sessions, lw_sessions, goal, day_labels,
                         figsize=(4.4, 4.0), compact=False)
        c1.get_tk_widget().pack(padx=8, pady=(4,12))

        # Best hours chart
        hrs_card = ctk.CTkFrame(charts_row, fg_color=CARD, corner_radius=12)
        hrs_card.grid(row=0, column=1, sticky="nsew")
        tk.Frame(hrs_card, bg=CYAN, height=2).pack(fill="x")
        mk_label(hrs_card, "PEAK FOCUS HOURS", size=11, bold=True, color=CYAN).pack(pady=(10,2))
        mk_label(hrs_card, "All-time sessions by hour", size=9, color=SUBTEXT).pack()

        hour_counts = [0] * 24
        for p in log:
            if p.get("type","") == "work":
                try: hour_counts[int(p.get("time","00:00").split(":")[0])] += 1
                except: pass

        show_hours  = list(range(6, 24))
        show_counts = [hour_counts[h] for h in show_hours]
        show_labels = [f"{h}" for h in show_hours]
        max_c       = max(show_counts + [1])
        bar_cols    = []
        for v in show_counts:
            r = v / max_c
            bar_cols.append(PINK if r>=0.75 else (VIOLET if r>=0.5 else (BLUE if r>=0.25 else BORDER2)))

        fig2 = Figure(figsize=(4.2, 3.8), facecolor=CARD)
        ax2  = fig2.add_subplot(111, facecolor=CARD)
        bars2 = ax2.bar(show_labels, show_counts, color=bar_cols, width=0.72, zorder=3)
        for bar, val in zip(bars2, show_counts):
            if val:
                ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                         str(val), ha="center", va="bottom", color=TEXT, fontsize=7)
        ax2.set_ylim(0, max_c + 1)
        ax2.set_xlabel("Hour of day", color=SUBTEXT, fontsize=8)
        ax2.tick_params(colors=SUBTEXT, labelsize=7)
        ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
        for sp in ["bottom","left"]: ax2.spines[sp].set_color(BORDER2)
        ax2.yaxis.set_visible(False)
        ax2.grid(axis="y", color=BORDER, zorder=0, alpha=0.5)
        ax2.set_facecolor(CARD)
        fig2.patch.set_alpha(0); fig2.tight_layout(pad=0.5)
        c2 = FigureCanvasTkAgg(fig2, master=hrs_card)
        c2.draw(); c2.get_tk_widget().pack(padx=8, pady=(4,12))

        # ══════════════════════════════════════════════════════════════════
        # ROW 4 — Monthly heatmap (this month + last month side by side)
        # ══════════════════════════════════════════════════════════════════
        mk_label(root, "  MONTHLY HEATMAP", size=9, bold=True, color=SUBTEXT
                 ).pack(anchor="w", padx=28, pady=(6,4))

        hm_outer = ctk.CTkFrame(root, fg_color="transparent")
        hm_outer.pack(fill="x", padx=24, pady=(0,8))
        hm_outer.grid_columnconfigure(0, weight=1)
        hm_outer.grid_columnconfigure(1, weight=1)

        # This month
        this_card = ctk.CTkFrame(hm_outer, fg_color=CARD, corner_radius=12)
        this_card.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        tk.Frame(this_card, bg=GOLD, height=2).pack(fill="x")
        self._draw_heatmap(this_card, month_offset=0, compact=False)

        # Last month
        last_card = ctk.CTkFrame(hm_outer, fg_color=CARD, corner_radius=12)
        last_card.grid(row=0, column=1, sticky="nsew")
        tk.Frame(last_card, bg=SUBTEXT, height=2).pack(fill="x")
        self._draw_heatmap(last_card, month_offset=-1, compact=False)

        # ══════════════════════════════════════════════════════════════════
        # ROW 5 — 30-day score line chart
        # ══════════════════════════════════════════════════════════════════
        mk_label(root, "  30-DAY SCORE HISTORY", size=9, bold=True, color=SUBTEXT
                 ).pack(anchor="w", padx=28, pady=(6,4))
        line_card = ctk.CTkFrame(root, fg_color=CARD, corner_radius=12)
        line_card.pack(fill="x", padx=24, pady=(0,14))
        tk.Frame(line_card, bg=CYAN, height=2).pack(fill="x")

        last30 = [(today - timedelta(days=i)).isoformat() for i in range(29,-1,-1)]
        scores30 = [day_score(d) for d in last30]
        x_pos    = list(range(30))

        fig3 = Figure(figsize=(9.0, 2.4), facecolor=CARD)
        ax3  = fig3.add_subplot(111, facecolor=CARD)

        # Fill zones
        ax3.axhspan(80, 100, color=GOLD,   alpha=0.06, zorder=1)
        ax3.axhspan(60,  80, color=CYAN,   alpha=0.05, zorder=1)
        ax3.axhspan(40,  60, color=ORANGE, alpha=0.05, zorder=1)
        ax3.axhspan(0,   40, color=RED,    alpha=0.04, zorder=1)

        # Line
        ax3.plot(x_pos, scores30, color=CYAN, lw=2.2, zorder=3,
                 path_effects=[pe.Stroke(linewidth=5, foreground=CYAN, alpha=0.18),
                                pe.Normal()])
        ax3.fill_between(x_pos, scores30, alpha=0.12, color=CYAN, zorder=2)

        # Dots colored by score
        for xi, si in zip(x_pos, scores30):
            ax3.scatter([xi], [si], s=28, color=score_col(si), zorder=4,
                        edgecolors=CARD, linewidths=0.8)

        # X-axis: show every 5th date
        tick_pos   = [i for i in range(0, 30, 5)]
        tick_lbls  = [last30[i][5:] for i in tick_pos]  # MM-DD
        ax3.set_xticks(tick_pos); ax3.set_xticklabels(tick_lbls, fontsize=7, color=SUBTEXT)
        ax3.set_ylim(-5, 110)
        ax3.set_yticks([0, 40, 60, 80, 100])
        ax3.set_yticklabels(["0","40","60","80","100"], fontsize=7, color=SUBTEXT)
        ax3.spines["top"].set_visible(False); ax3.spines["right"].set_visible(False)
        for sp in ["bottom","left"]: ax3.spines[sp].set_color(BORDER2)
        ax3.grid(axis="y", color=BORDER, alpha=0.5, zorder=0)
        ax3.set_facecolor(CARD)
        fig3.patch.set_alpha(0); fig3.tight_layout(pad=0.5)

        c3 = FigureCanvasTkAgg(fig3, master=line_card)
        c3.draw(); c3.get_tk_widget().pack(fill="x", padx=8, pady=(4,12))

        ctk.CTkFrame(root, fg_color="transparent", height=20).pack()

    def _set_daily_goal(self):
        try:
            val = int(self._goal_entry.get().strip())
            if val < 1: raise ValueError
            self.data["daily_goal"] = val
            save_data(self.data)
            self._refresh_productivity()
        except ValueError:
            messagebox.showwarning("Invalid", "Please enter a number greater than 0.")

    # ══════════════════════════════════════════════════════════════════════
    # SUBJECT COLOUR MANAGER
    # ══════════════════════════════════════════════════════════════════════

    def _open_colour_manager(self):
        """Popup window to view and reassign subject colours."""
        win = tk.Toplevel(self)
        win.title("Subject Colours")
        win.configure(bg=BG)
        win.geometry("420x500")
        win.resizable(False, True)
        win.attributes("-topmost", True)

        tk.Frame(win, bg=VIOLET, height=3).pack(fill="x")
        hf = tk.Frame(win, bg=BG); hf.pack(fill="x", padx=20, pady=14)
        tk.Label(hf, text="🎨  SUBJECT COLOURS", font=("Segoe UI",13,"bold"),
                 bg=BG, fg=VIOLET).pack(side="left")
        tk.Label(hf, text="Click a colour to change it", font=("Segoe UI",9),
                 bg=BG, fg=SUBTEXT).pack(side="left", padx=10)

        canvas_frame = tk.Frame(win, bg=BG); canvas_frame.pack(fill="both", expand=True, padx=20)
        subjects = all_subjects(self.data)
        if not subjects:
            tk.Label(canvas_frame, text="No subjects found. Add tests, assignments or syllabus subjects first.",
                     font=("Segoe UI",10), bg=BG, fg=SUBTEXT, justify="center").pack(pady=40)
            return

        for subj in subjects:
            color = get_subject_color(self.data, subj)
            row = tk.Frame(canvas_frame, bg=CARD); row.pack(fill="x", pady=3)
            tk.Frame(row, bg=color, width=6).pack(side="left", fill="y")
            tk.Label(row, text=subj, font=("Segoe UI",11,"bold"),
                     bg=CARD, fg=TEXT, width=22, anchor="w").pack(side="left", padx=12, pady=10)
            # Colour swatches
            swatch_frame = tk.Frame(row, bg=CARD); swatch_frame.pack(side="right", padx=8)
            for palette_col in SUBJECT_PALETTE:
                sel = palette_col == color
                sw = tk.Frame(swatch_frame, bg=palette_col,
                              width=20, height=20,
                              highlightthickness=2,
                              highlightbackground=TEXT if sel else CARD,
                              cursor="hand2")
                sw.pack(side="left", padx=2)
                sw.bind("<Button-1>", lambda e, s=subj, c=palette_col, r=row: (
                    set_subject_color(self.data, s, c),
                    self._refresh_all(),
                    win.destroy(),
                    self._open_colour_manager()
                ))

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=20, pady=10)
        tk.Button(win, text="CLOSE", command=win.destroy,
                  font=("Segoe UI",10,"bold"), bg=BORDER2, fg=TEXT,
                  relief="flat", padx=20, pady=8, cursor="hand2").pack(pady=(0,14))

    # ══════════════════════════════════════════════════════════════════════
    # WEEKLY DIGEST POPUP
    # ══════════════════════════════════════════════════════════════════════

    def _maybe_show_digest(self):
        """Show Monday morning weekly digest if not already shown today."""
        today = date.today()
        if today.weekday() != 0:   # Only Monday
            return
        last = self.data.get("last_digest_date", "")
        if last == today.isoformat():
            return
        self.data["last_digest_date"] = today.isoformat()
        save_data(self.data)
        self.after(1200, self._show_digest)   # slight delay after app loads

    def _show_digest(self):
        """Full-screen-overlay weekly digest modal."""
        today      = date.today()
        last_mon   = today - timedelta(days=7)
        log        = self.data.get("pomodoro_log", [])
        goal       = self.data.get("daily_goal", 6)

        # Last week stats
        lw_days    = [(last_mon + timedelta(days=i)).isoformat() for i in range(7)]
        lw_sessions = sum(1 for p in log if p.get("date","") in lw_days
                          and p.get("type","") == "work")
        lw_score   = min(100, int((lw_sessions / (goal * 7)) * 100)) if goal else 0
        lw_tasks   = sum(1 for t in self.data["tasks"]
                         if t.get("done") and t.get("added","")[:10] in lw_days)

        # This week outlook
        tw_tests   = [t for t in self.data["tests"]
                      if 0 <= (days_until(t.get("date","")) or -1) <= 7]
        tw_asgns   = [a for a in self.data["assignments"]
                      if not a.get("submitted") and
                      0 <= (days_until(a.get("due","")) or -1) <= 7]
        pending_t  = len([t for t in self.data["tasks"] if not t.get("done")])

        score_col  = (GOLD if lw_score >= 80 else
                      CYAN if lw_score >= 60 else
                      ORANGE if lw_score >= 40 else RED)
        grade      = ("EXCELLENT" if lw_score >= 80 else
                      "GOOD"      if lw_score >= 60 else
                      "AVERAGE"   if lw_score >= 40 else "NEEDS WORK")

        # Window
        win = tk.Toplevel(self)
        win.title("Weekly Digest")
        win.configure(bg=BG)
        win.geometry("560x620")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        # Centre on parent
        self.update_idletasks()
        px = self.winfo_x() + self.winfo_width()  // 2 - 280
        py = self.winfo_y() + self.winfo_height() // 2 - 310
        win.geometry(f"560x620+{px}+{py}")

        # Header
        tk.Frame(win, bg=CYAN, height=3).pack(fill="x")
        hf = tk.Frame(win, bg=BG); hf.pack(fill="x", padx=24, pady=(18,6))
        tk.Label(hf, text="⬡  WEEKLY DIGEST", font=("Segoe UI",16,"bold"),
                 bg=BG, fg=CYAN).pack(side="left")
        tk.Label(hf, text=today.strftime("Monday, %d %B %Y"),
                 font=("Segoe UI",10), bg=BG, fg=SUBTEXT).pack(side="right")

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24)

        # ── Last week summary
        tk.Label(win, text="  LAST WEEK", font=("Segoe UI",9,"bold"),
                 bg=BG, fg=SUBTEXT).pack(anchor="w", padx=24, pady=(14,6))

        stats_f = tk.Frame(win, bg=BG); stats_f.pack(fill="x", padx=24)
        for col_i, (val, lbl, col) in enumerate([
            (str(lw_score),    "SCORE",    score_col),
            (str(lw_sessions), "SESSIONS", PINK),
            (str(lw_tasks),    "TASKS DONE", GREEN),
            (grade,            "GRADE",    score_col),
        ]):
            card = tk.Frame(stats_f, bg=CARD); card.grid(row=0, column=col_i, padx=(0,8), sticky="ew")
            stats_f.grid_columnconfigure(col_i, weight=1)
            tk.Frame(card, bg=col, height=2).pack(fill="x")
            tk.Label(card, text=val, font=("Segoe UI",20,"bold"),
                     bg=CARD, fg=col).pack(pady=(8,0))
            tk.Label(card, text=lbl, font=("Segoe UI",8,"bold"),
                     bg=CARD, fg=SUBTEXT).pack(pady=(0,8))

        # ── This week outlook
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(16,0))
        tk.Label(win, text="  THIS WEEK OUTLOOK", font=("Segoe UI",9,"bold"),
                 bg=BG, fg=SUBTEXT).pack(anchor="w", padx=24, pady=(10,6))

        outlook_f = tk.Frame(win, bg=BG); outlook_f.pack(fill="x", padx=24)

        # Tests this week
        lc = tk.Frame(outlook_f, bg=CARD); lc.pack(side="left", fill="both", expand=True, padx=(0,8))
        tk.Frame(lc, bg=GOLD, height=2).pack(fill="x")
        tk.Label(lc, text="◈  TESTS", font=("Segoe UI",10,"bold"),
                 bg=CARD, fg=GOLD).pack(anchor="w", padx=10, pady=(8,4))
        if tw_tests:
            for t in tw_tests[:4]:
                d = days_until(t.get("date",""))
                uc = urgency_col(d)
                rf = tk.Frame(lc, bg=CARD); rf.pack(fill="x", padx=10, pady=2)
                tk.Label(rf, text=t.get("subject",""), font=("Segoe UI",10,"bold"),
                         bg=CARD, fg=get_subject_color(self.data, t.get("subject",""))
                         ).pack(side="left")
                tk.Label(rf, text=urgency_lbl(d), font=("Segoe UI",8,"bold"),
                         bg=CARD, fg=uc).pack(side="right")
        else:
            tk.Label(lc, text="  No tests this week", font=("Segoe UI",9),
                     bg=CARD, fg=DIM).pack(anchor="w", padx=10)
        tk.Frame(lc, bg=CARD, height=8).pack()

        # Assignments this week
        rc = tk.Frame(outlook_f, bg=CARD); rc.pack(side="left", fill="both", expand=True)
        tk.Frame(rc, bg=RED, height=2).pack(fill="x")
        tk.Label(rc, text="◧  ASSIGNMENTS", font=("Segoe UI",10,"bold"),
                 bg=CARD, fg=RED).pack(anchor="w", padx=10, pady=(8,4))
        if tw_asgns:
            for a in tw_asgns[:4]:
                d = days_until(a.get("due",""))
                af = tk.Frame(rc, bg=CARD); af.pack(fill="x", padx=10, pady=2)
                tk.Label(af, text=f"[{a.get('subject','')}]", font=("Segoe UI",9,"bold"),
                         bg=CARD,
                         fg=get_subject_color(self.data, a.get("subject",""))
                         ).pack(side="left")
                tk.Label(af, text=urgency_lbl(d), font=("Segoe UI",8,"bold"),
                         bg=CARD, fg=urgency_col(d)).pack(side="right")
        else:
            tk.Label(rc, text="  No assignments due", font=("Segoe UI",9),
                     bg=CARD, fg=DIM).pack(anchor="w", padx=10)
        tk.Frame(rc, bg=CARD, height=8).pack()

        # Pending tasks count
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(16,0))
        pf = tk.Frame(win, bg=CARD); pf.pack(fill="x", padx=24, pady=8)
        tk.Frame(pf, bg=ORANGE, height=2).pack(fill="x")
        pif = tk.Frame(pf, bg=CARD); pif.pack(fill="x", padx=14, pady=10)
        tk.Label(pif, text="▣  PENDING TASKS", font=("Segoe UI",10,"bold"),
                 bg=CARD, fg=ORANGE).pack(side="left")
        tk.Label(pif, text=str(pending_t), font=("Segoe UI",16,"bold"),
                 bg=CARD, fg=ORANGE).pack(side="right")

        # Motivational line
        streak = self.data.get("streak",{}).get("count",0)
        if streak > 0:
            mot = f"🔥 {streak} day streak — keep it going this week."
        elif lw_score >= 80:
            mot = "Outstanding last week. Replicate it."
        elif lw_score >= 60:
            mot = "Solid week. Push for Excellent this time."
        else:
            mot = "New week, clean slate. Make it count."

        tk.Label(win, text=mot, font=("Segoe UI",11,"italic"),
                 bg=BG, fg=SUBTEXT).pack(pady=(8,0))

        # Close button
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(14,0))
        tk.Button(win, text="  LET'S GO  →", command=win.destroy,
                  font=("Segoe UI",11,"bold"), bg=CYAN, fg=BG,
                  relief="flat", padx=24, pady=10, cursor="hand2").pack(pady=14)

    # ══════════════════════════════════════════════════════════════════════
    # MISC
    # ══════════════════════════════════════════════════════════════════════

    def _refresh_all(self):
        """Refresh every tab that has already been built.
        Unbuilt tabs are skipped — they will refresh themselves on first visit."""
        built = getattr(self, "_tabs_built", set())
        if "TESTS"       in built: self._refresh_tests()
        if "TASKS"       in built: self._refresh_tasks()
        if "LISTS"       in built: self._refresh_lists()
        if "ASSIGNMENTS" in built: self._refresh_assignments()
        if "PRACTICALS"  in built: self._refresh_practicals()
        if "SYLLABUS"    in built: self._refresh_syllabus()
        if "NOTES"       in built: self._refresh_notes_list()
        if "OVERVIEW"    in built: self._refresh_overview()
        self._update_counts()

    def _update_counts(self):
        counts = {
            "TESTS":       len([t for t in self.data["tests"] if (days_until(t.get("date","")) or -1) >= 0]),
            "TASKS":       len([t for t in self.data["tasks"] if not t.get("done")]),
            "LISTS":       len(self.data["lists"]),
            "ASSIGNMENTS": len([a for a in self.data["assignments"] if not a.get("submitted")]),
            "PRACTICALS":  len([p for p in self.data["practicals"] if not p.get("done")]),
            "SYLLABUS":    len(self.data.get("syllabus",[])),
            "NOTES":       len(self.data.get("notes",[])),
        }
        for name, count in counts.items():
            if name in self._sbtn_refs:
                self._sbtn_refs[name]["cnt"].configure(text=str(count) if count else "")

    def _manual_save(self):
        save_data(self.data)
        messagebox.showinfo("Saved", "All data saved successfully.")

    def _do_backup(self):
        dst = backup_data(self.data)
        self._update_backup_lbl()
        messagebox.showinfo("Backup", f"Backup saved:\n{os.path.basename(dst)}")


if __name__ == "__main__":
    app = PlannerApp()
    app.mainloop()
    
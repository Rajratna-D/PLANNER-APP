"""
COMMAND PLANNER v2 — PRINCEBLUE
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
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ── plyer notifications (optional) ────────────────────────────────────────
try:
    from plyer import notification as plyer_notify
    HAS_NOTIFY = True
except ImportError:
    HAS_NOTIFY = False

# ══════════════════════════════════════════════════════════════════════════
# THEME
# ══════════════════════════════════════════════════════════════════════════
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Palette
BG        = "#07090E"
PANEL     = "#0C0F18"
CARD      = "#111420"
CARD2     = "#161B2C"
HOVER     = "#1C2238"
BORDER    = "#1F2540"
BORDER2   = "#2A3055"

TEXT      = "#DDE3F5"
SUBTEXT   = "#5E6A90"
DIM       = "#2E3555"

CYAN      = "#00C8F0"
BLUE      = "#3D8EFF"
GREEN     = "#2EE87A"
ORANGE    = "#FF9020"
RED       = "#FF3358"
GOLD      = "#FFCC44"
VIOLET    = "#9D7EFF"
PINK      = "#FF6EB0"

PRIORITY_ORDER = ["Immediate", "Important", "2nd Priority", "3rd Priority", "Someday"]
P_COLOR = {"Immediate": RED, "Important": ORANGE,
           "2nd Priority": BLUE, "3rd Priority": GREEN, "Someday": SUBTEXT}
P_BG    = {"Immediate": "#250810", "Important": "#251500",
           "2nd Priority": "#071525", "3rd Priority": "#07200F", "Someday": "#111420"}

RECUR_OPTIONS = ["None", "Daily", "Weekly", "Monthly"]

TAB_CFG = [
    ("⬡", "OVERVIEW",    CYAN),
    ("◈", "TESTS",       GOLD),
    ("▣", "TASKS",       ORANGE),
    ("◫", "LISTS",       BLUE),
    ("◧", "ASSIGNMENTS", RED),
    ("◩", "PRACTICALS",  GREEN),
    ("⬢", "SYLLABUS",    VIOLET),
    ("◎", "POMODORO",    PINK),
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
    "streak": {"last_date": "", "count": 0},
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
    return {k: (v.copy() if isinstance(v, list) else dict(v)) for k, v in EMPTY_DATA.items()}

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

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
    elif s["last_date"] != today:
        # reset if missed a day
        done_today = any(t.get("done") for t in data.get("tasks", []))
        if s["last_date"] not in (today, yesterday):
            s["count"] = 1 if done_today else 0
    s["last_date"] = today

def send_notify(title, msg):
    if HAS_NOTIFY:
        try:
            plyer_notify.notify(title=title, message=msg,
                                app_name="Command Planner", timeout=5)
        except: pass

def nid(): return str(uuid.uuid4())

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
           hover=None, width=120, height=32, radius=6, size=11):
    return ctk.CTkButton(parent, text=text, command=cmd,
                         fg_color=color, text_color=text_color,
                         hover_color=hover or HOVER,
                         width=width, height=height,
                         corner_radius=radius,
                         font=ctk.CTkFont(size=size, weight="bold"))

def mk_entry(parent, placeholder="", width=200, height=34):
    return ctk.CTkEntry(parent, placeholder_text=placeholder,
                        fg_color=HOVER, border_color=BORDER2,
                        text_color=TEXT, placeholder_text_color=SUBTEXT,
                        width=width, height=height,
                        font=ctk.CTkFont(size=11),
                        corner_radius=6)

def mk_combo(parent, values, width=160, height=34):
    return ctk.CTkComboBox(parent, values=values,
                           fg_color=HOVER, border_color=BORDER2,
                           text_color=TEXT, button_color=BORDER2,
                           button_hover_color=HOVER,
                           dropdown_fg_color=CARD2,
                           dropdown_text_color=TEXT,
                           dropdown_hover_color=HOVER,
                           width=width, height=height,
                           font=ctk.CTkFont(size=11),
                           corner_radius=6)

def mk_scroll(parent, fg_color=BG):
    return ctk.CTkScrollableFrame(parent, fg_color=fg_color,
                                  scrollbar_button_color=BORDER2,
                                  scrollbar_button_hover_color=BORDER,
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
    """Rounded card with optional left color accent bar."""
    def __init__(self, parent, accent_color=BORDER, **kw):
        super().__init__(parent, fg_color=CARD, corner_radius=10, **kw)
        self.accent = accent_color
        # top accent line via tkinter frame inside
        self._bar = tk.Frame(self, bg=accent_color, height=2)
        self._bar.pack(fill="x", pady=(0,0))
        self._body = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0)
        self._body.pack(fill="both", expand=True, padx=14, pady=(8,10))

    @property
    def body(self):
        return self._body

# ══════════════════════════════════════════════════════════════════════════
# SECTION HEADER
# ══════════════════════════════════════════════════════════════════════════

def section_header(parent, title, color, action_text=None, action_cmd=None):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="x", padx=20, pady=(18, 6))
    mk_label(f, title, size=12, bold=True, color=color).pack(side="left")
    if action_text and action_cmd:
        mk_btn(f, action_text, action_cmd, color=BORDER, width=80, height=26, size=9
               ).pack(side="right")
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=20)

# ══════════════════════════════════════════════════════════════════════════
# TAB HEADER
# ══════════════════════════════════════════════════════════════════════════

def tab_header(parent, icon, title, subtitle, color):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="x", padx=24, pady=(20, 0))
    row = ctk.CTkFrame(f, fg_color="transparent")
    row.pack(anchor="w")
    mk_label(row, icon + " ", size=22, color=color).pack(side="left")
    mk_label(row, title, size=22, bold=True, color=TEXT).pack(side="left")
    mk_label(f, subtitle, size=11, color=SUBTEXT).pack(anchor="w", pady=(2,0))
    tk.Frame(parent, bg=color, height=1).pack(fill="x", padx=24, pady=(12,0))
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(1,14))


# ══════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════

class PlannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("COMMAND PLANNER")
        self.geometry("1280x780")
        self.minsize(1024, 640)
        self.configure(fg_color=BG)
        self.data         = load_data()
        self._task_sort   = "Priority"
        self._task_filter = None
        self._sbtn_refs   = {}
        self._pomo_running = False
        self._pomo_thread  = None
        self._pomo_seconds = 25 * 60
        self._pomo_elapsed = 0
        self._pomo_mode    = "work"   # work / break
        self._pomo_sessions = 0
        update_streak(self.data)
        backup_data(self.data)
        save_data(self.data)
        self._build_ui()
        self._refresh_all()
        self.after(60000, self._auto_save_loop)

    # ── Auto-save loop ────────────────────────────────────────────────────
    def _auto_save_loop(self):
        save_data(self.data)
        self.after(60000, self._auto_save_loop)

    # ══════════════════════════════════════════════════════════════════════
    # LAYOUT SHELL
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        # Top bar
        topbar = ctk.CTkFrame(self, fg_color=PANEL, height=56, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=CYAN, width=4).pack(side="left", fill="y")

        lf = ctk.CTkFrame(topbar, fg_color="transparent")
        lf.pack(side="left", padx=18, fill="y")
        ctk.CTkFrame(lf, fg_color="transparent").pack(expand=True)
        row = ctk.CTkFrame(lf, fg_color="transparent")
        row.pack()
        mk_label(row, "COMMAND", size=20, bold=True, color=TEXT).pack(side="left")
        mk_label(row, " PLANNER", size=20, bold=True, color=CYAN).pack(side="left")
        mk_label(row, "  v2  //  PRINCEBLUE", size=9, color=SUBTEXT).pack(side="left", pady=(5,0))
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
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        mk_label(self.sidebar, "  NAVIGATION", size=9, bold=True, color=SUBTEXT
                 ).pack(anchor="w", padx=14, pady=(18,8))

        self.content_area = ctk.CTkFrame(body, fg_color=BG, corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        self.tab_frames = {}
        self.active_tab = tk.StringVar(value="OVERVIEW")

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
        outer = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=40)
        outer.pack(fill="x", padx=8, pady=1)
        outer.pack_propagate(False)

        bar = tk.Frame(outer, bg=PANEL, width=3)
        bar.pack(side="left", fill="y", padx=(0,0))

        inner = ctk.CTkFrame(outer, fg_color="transparent", cursor="hand2")
        inner.pack(side="left", fill="both", expand=True, padx=4)

        ico = mk_label(inner, icon, size=13, color=color)
        ico.pack(side="left", padx=(8,4))
        lbl = mk_label(inner, name, size=10, color=SUBTEXT)
        lbl.pack(side="left")
        cnt = mk_label(inner, "", size=9, color=DIM)
        cnt.pack(side="right", padx=8)

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
        prev = self.active_tab.get()
        if prev in self._sbtn_refs:
            r = self._sbtn_refs[prev]
            r["inner"].configure(fg_color="transparent")
            r["bar"].configure(bg=PANEL)
            r["lbl"].configure(text_color=SUBTEXT)
        self.active_tab.set(name)
        r = self._sbtn_refs[name]
        r["inner"].configure(fg_color=HOVER)
        r["bar"].configure(bg=r["color"])
        r["lbl"].configure(text_color=TEXT)
        for n, fr in self.tab_frames.items():
            fr.pack_forget()
        self.tab_frames[name].pack(fill="both", expand=True)
        if name == "OVERVIEW":
            self._refresh_overview()

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
        self._build_overview_tab()
        self._build_tests_tab()
        self._build_tasks_tab()
        self._build_lists_tab()
        self._build_assignments_tab()
        self._build_practicals_tab()
        self._build_syllabus_tab()
        self._build_pomodoro_tab()

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

        # Pomodoro weekly chart
        if HAS_MPL:
            section_header(right_col, "◎  POMODOROS THIS WEEK", PINK)
            self._ov_pomo_chart(right_col)

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
                pb = ctk.CTkProgressBar(card.body, width=300, height=6,
                                         progress_color=VIOLET, fg_color=BORDER)
                pb.pack(fill="x", pady=(4,0))
                pb.set(pct/100)
        else:
            mk_label(left_col, "  No subjects added", size=11, color=DIM).pack(anchor="w", padx=24, pady=6)

        ctk.CTkFrame(root, fg_color="transparent", height=24).pack()

    def _ov_pomo_chart(self, parent):
        if not HAS_MPL: return
        today = date.today()
        days  = [(today - timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
        labels = [(today - timedelta(days=i)).strftime("%a") for i in range(6,-1,-1)]
        counts = []
        log = self.data.get("pomodoro_log", [])
        for d in days:
            counts.append(sum(1 for p in log if p.get("date","") == d and p.get("type","") == "work"))

        fig = Figure(figsize=(4.5, 1.8), facecolor=CARD)
        ax  = fig.add_subplot(111, facecolor=CARD)
        bars = ax.bar(labels, counts, color=PINK, width=0.55, zorder=3)
        for bar, val in zip(bars, counts):
            if val:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                        str(val), ha='center', va='bottom', color=TEXT, fontsize=7)
        ax.set_ylim(0, max(counts + [4]))
        ax.tick_params(colors=SUBTEXT, labelsize=8)
        ax.spines[:].set_color(BORDER)
        ax.yaxis.set_visible(False)
        ax.grid(axis='y', color=BORDER, zorder=0)
        fig.tight_layout(pad=0.5)

        cf = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
        cf.pack(fill="x", padx=20, pady=6)
        canvas = FigureCanvasTkAgg(fig, master=cf)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=8, pady=8)

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
            d = days_until(t.get("date","")); c = urgency_col(d)
            card = Card(self.tests_inner, c)
            card.pack(fill="x", pady=4)
            row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
            mk_label(row, t.get("subject",""), size=13, bold=True, color=TEXT).pack(side="left")
            right = ctk.CTkFrame(row, fg_color="transparent"); right.pack(side="right")
            mk_label(right, urgency_lbl(d), size=9, bold=True, color=c).pack(side="left", padx=8)
            mk_btn(right, "✕", lambda tid=t["id"]: self._del_test(tid),
                   CARD, RED, P_BG["Immediate"], 28, 26, size=10).pack(side="left")
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
        mk_label(row, t.get("text",""), size=11, color=SUBTEXT if done else TEXT
                 ).pack(side="left")

        right = ctk.CTkFrame(row, fg_color="transparent"); right.pack(side="right")
        if t.get("recur","None") != "None":
            mk_label(right, f"↻{t['recur'][0]}", size=9, bold=True, color=VIOLET).pack(side="left", padx=4)
        if not done:
            cp = mk_combo(right, PRIORITY_ORDER, 130, 28); cp.set(p); cp.pack(side="left", padx=6)
            cp.configure(command=lambda v, tid=t["id"]: self._change_prio(tid, v))
        mk_label(right, p, size=9, bold=True, color=pc).pack(side="left", padx=4)
        mk_btn(right, "✕", lambda tid=t["id"]: self._del_task(tid),
               "transparent", RED, P_BG["Immediate"], 28, 26, size=10).pack(side="left")

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

    def _toggle_task(self, tid, var):
        for t in self.data["tasks"]:
            if t["id"] == tid: t["done"] = var.get()
        update_streak(self.data); save_data(self.data)
        self._refresh_tasks(); self._update_counts()

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
        mk_btn(hrow, "✕", lambda lid=lst["id"]: self._del_list(lid),
               "transparent", RED, P_BG["Immediate"], 28, 26, size=10).pack(side="right")

        if total:
            pb = ctk.CTkProgressBar(inn, height=4, progress_color=BLUE, fg_color=BORDER)
            pb.pack(fill="x", pady=(0,8)); pb.set(done_c/total)

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
            mk_btn(irow, "✕", lambda lid=lst["id"],iid=item["id"]: self._del_li(lid,iid),
                   "transparent", RED, P_BG["Immediate"], 24, 22, size=9).pack(side="right")

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
        d = days_until(a.get("due","")); c = GREEN if submitted else urgency_col(d)
        card = Card(parent, c)
        if submitted: card.configure(fg_color="#0D0F18")
        card.pack(fill="x", pady=3)
        row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
        mk_label(row, f"[{a.get('subject','')}]  {a.get('title','')}",
                 size=12, bold=True, color=SUBTEXT if submitted else TEXT).pack(side="left")
        right = ctk.CTkFrame(row, fg_color="transparent"); right.pack(side="right")
        if not submitted:
            dl = (f"{d}d left" if (d or 0) >= 0 else "OVERDUE") if d is not None else f"{a.get('due','')}"
            mk_label(right, dl, size=9, bold=True, color=c).pack(side="left", padx=8)
            mk_btn(right, "✓ SUBMITTED", lambda aid=a["id"]: self._submit_asgn(aid),
                   GREEN, BG, "#0A4020", 120, 28, size=9).pack(side="left", padx=6)
        mk_btn(right, "✕", lambda aid=a["id"]: self._del_asgn(aid),
               "transparent", RED, P_BG["Immediate"], 28, 26, size=10).pack(side="left")
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
            if a["id"] == aid: a["submitted"] = True
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
        card = Card(parent, GREEN if not done else BORDER)
        if done: card.configure(fg_color="#0D0F18")
        card.pack(fill="x", pady=3)
        row = ctk.CTkFrame(card.body, fg_color="transparent"); row.pack(fill="x")
        mk_label(row, f"Exp {p.get('num','?')}  —  {p.get('title','')}",
                 size=12, bold=True, color=SUBTEXT if done else TEXT).pack(side="left")
        mk_btn(row, "✕", lambda pid=p["id"]: self._del_prac(pid),
               "transparent", RED, P_BG["Immediate"], 28, 26, size=10).pack(side="right")
        mk_label(card.body, f"Subject: {p.get('subject','')}   Date: {p.get('date','')}",
                 size=10, color=SUBTEXT).pack(anchor="w", pady=(2,6))
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

        outer = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
        outer.pack(fill="x", pady=6)
        tk.Frame(outer, bg=VIOLET, height=2).pack(fill="x")
        inn = ctk.CTkFrame(outer, fg_color=CARD, corner_radius=0)
        inn.pack(fill="x", padx=16, pady=(8,12))

        # Header
        hrow = ctk.CTkFrame(inn, fg_color="transparent"); hrow.pack(fill="x", pady=(0,4))
        mk_label(hrow, subj.get("name",""), size=14, bold=True, color=VIOLET).pack(side="left")
        mk_label(hrow, f"  {done}/{total} topics  ({pct}%)", size=10, color=SUBTEXT).pack(side="left")
        mk_btn(hrow, "✕ DEL SUBJECT", lambda sid=subj["id"]: self._del_subject(sid),
               "transparent", RED, P_BG["Immediate"], 110, 26, size=9).pack(side="right")

        # Progress bar
        pb = ctk.CTkProgressBar(inn, height=6, progress_color=VIOLET, fg_color=BORDER)
        pb.pack(fill="x", pady=(0,10)); pb.set(pct/100)

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
                            checkmark_color=BG, fg_color=VIOLET, hover_color=VIOLET,
                            border_color=BORDER2, width=22,
                            command=lambda sid=subj["id"],tid=topic["id"],v=var: self._toggle_topic(sid,tid,v)
                            ).pack(side="left", padx=(8,4), pady=6)
            mk_label(trow, topic.get("name",""), size=10,
                     color=SUBTEXT if topic.get("done") else TEXT).pack(side="left", pady=6)
            mk_btn(trow, "✕", lambda sid=subj["id"],tid=topic["id"]: self._del_topic(sid,tid),
                   "transparent", RED, P_BG["Immediate"], 24, 22, size=9).pack(side="right", padx=4)

        # Add topic
        arow = ctk.CTkFrame(inn, fg_color="transparent"); arow.pack(fill="x", pady=(10,0))
        e = mk_entry(arow, "Add topic (e.g. Laser Principles)", 340); e.pack(side="left", padx=(0,8))
        mk_btn(arow, "＋ TOPIC", lambda sid=subj["id"],en=e: self._add_topic(sid,en),
               VIOLET, BG, "#6050C0", 100, 34).pack(side="left")

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
        self.pomo_pb = ctk.CTkProgressBar(timer_card, width=340, height=6,
                                           progress_color=PINK, fg_color=BORDER)
        self.pomo_pb.pack(pady=(0,16))
        self.pomo_pb.set(0)

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
        if self._pomo_running:
            self._pomo_running = False
            self.pomo_start_btn.configure(text="▶  START")
        else:
            self._pomo_running = True
            self.pomo_start_btn.configure(text="⏸  PAUSE")
            self._pomo_thread = threading.Thread(target=self._pomo_tick_loop, daemon=True)
            self._pomo_thread.start()

    def _pomo_reset(self):
        self._pomo_running = False
        self.pomo_start_btn.configure(text="▶  START")
        self._pomo_mode = "work"
        self._pomo_elapsed = 0
        self._pomo_seconds = self._pomo_work_secs()
        self._pomo_update_display()

    def _pomo_tick_loop(self):
        total = self._pomo_seconds
        while self._pomo_running and self._pomo_elapsed < total:
            time.sleep(1)
            if not self._pomo_running: return
            self._pomo_elapsed += 1
            self.after(0, self._pomo_update_display)
        if self._pomo_running:
            self.after(0, self._pomo_session_done)

    def _pomo_session_done(self):
        self._pomo_running = False
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
        self.pomo_pb.set(self._pomo_elapsed / total if total else 0)
        today_count = sum(1 for p in self.data.get("pomodoro_log",[])
                          if p.get("date","") == date.today().isoformat() and p.get("type","") == "work")
        self.pomo_session_lbl.configure(
            text=f"Session {self._pomo_sessions}  •  Today: {today_count}")

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
    # MISC
    # ══════════════════════════════════════════════════════════════════════

    def _refresh_all(self):
        self._refresh_tests()
        self._refresh_tasks()
        self._refresh_lists()
        self._refresh_assignments()
        self._refresh_practicals()
        self._refresh_syllabus()
        self._update_counts()

    def _update_counts(self):
        counts = {
            "TESTS":       len([t for t in self.data["tests"] if (days_until(t.get("date","")) or -1) >= 0]),
            "TASKS":       len([t for t in self.data["tasks"] if not t.get("done")]),
            "LISTS":       len(self.data["lists"]),
            "ASSIGNMENTS": len([a for a in self.data["assignments"] if not a.get("submitted")]),
            "PRACTICALS":  len([p for p in self.data["practicals"] if not p.get("done")]),
            "SYLLABUS":    len(self.data.get("syllabus",[])),
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

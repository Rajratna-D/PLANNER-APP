"""
COMMAND PLANNER — PRINCEBLUE
Redesigned with Overview tab, better fonts, premium dark aesthetic.
Run: python planner.py   (stdlib only — no pip install needed)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
import json, os, uuid
from datetime import datetime, date

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "planner_data.json")

# ── Palette ──────────────────────────────────────────────────────────────────
BG       = "#090B10"
PANEL    = "#0F1219"
CARD     = "#141720"
HOVER    = "#1A1F2E"
BORDER   = "#1E2235"
BORDER2  = "#252B40"

TEXT     = "#E2E8F8"
SUBTEXT  = "#6B7494"
DIM      = "#3A4060"

BLUE     = "#4B9EFF"
CYAN     = "#00D4FF"
GREEN    = "#39E57A"
ORANGE   = "#FF9B3A"
RED      = "#FF4466"
VIOLET   = "#A78BFA"
GOLD     = "#FFD166"

PRIORITY_ORDER  = ["Immediate", "Important", "2nd Priority", "3rd Priority", "Someday"]
PRIORITY_COLOR  = {"Immediate": RED, "Important": ORANGE,
                   "2nd Priority": BLUE, "3rd Priority": GREEN, "Someday": SUBTEXT}
PRIORITY_BG     = {"Immediate": "#2A0A12", "Important": "#2A1800",
                   "2nd Priority": "#091828", "3rd Priority": "#0A2015", "Someday": "#141720"}

TAB_META = [
    ("⬡", "OVERVIEW",    CYAN),
    ("◈", "TESTS",       GOLD),
    ("▣", "TASKS",       ORANGE),
    ("◫", "LISTS",       BLUE),
    ("◧", "ASSIGNMENTS", RED),
    ("◩", "PRACTICALS",  GREEN),
]

F = {}

def init_fonts():
    mono_candidates = ["Consolas", "Menlo", "DejaVu Sans Mono", "Courier New", "Courier"]
    sans_candidates = ["Segoe UI", "SF Pro Display", "Helvetica Neue", "Helvetica", "TkDefaultFont"]
    def best(candidates):
        avail = set(tkfont.families())
        for c in candidates:
            if c in avail:
                return c
        return candidates[-1]
    mono = best(mono_candidates)
    sans = best(sans_candidates)
    F["hero"]     = (sans, 20, "bold")
    F["head"]     = (sans, 13, "bold")
    F["subhead"]  = (sans, 11, "bold")
    F["body"]     = (sans, 10)
    F["small"]    = (sans,  9)
    F["mono"]     = (mono, 10)
    F["tag"]      = (mono,  8, "bold")
    F["clock"]    = (mono, 10)
    F["num"]      = (sans, 26, "bold")
    F["numsmall"] = (sans, 16, "bold")


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"tests": [], "tasks": [], "lists": [], "assignments": [], "practicals": []}


def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)


def days_until(s):
    try:
        return (datetime.strptime(s, "%Y-%m-%d").date() - date.today()).days
    except Exception:
        return None


def urgency_color(d):
    if d is None: return SUBTEXT
    if d < 0:     return DIM
    if d == 0:    return RED
    if d <= 2:    return ORANGE
    if d <= 7:    return GOLD
    return GREEN


def urgency_label(d):
    if d is None: return "–"
    if d < 0:     return "PAST"
    if d == 0:    return "TODAY"
    if d == 1:    return "TOMORROW"
    return f"{d}d"


# ── Reusable Widgets ─────────────────────────────────────────────────────────

class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=PANEL, **kw):
        super().__init__(parent, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vsb    = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner  = tk.Frame(self.canvas, bg=bg)
        self._win   = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._win, width=e.width))
        self.bind_all("<MouseWheel>", self._scroll)

    def _scroll(self, e):
        if self.winfo_ismapped():
            self.canvas.yview_scroll(int(-1*(e.delta/120)), "units")


def mk_sep(parent, color=BORDER, height=1, padx=0, pady=6):
    tk.Frame(parent, bg=color, height=height).pack(fill="x", padx=padx, pady=pady)


def mk_entry(parent, width=22, placeholder=""):
    e = tk.Entry(parent, font=F["mono"], bg=HOVER, fg=TEXT,
                 insertbackground=CYAN, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER2,
                 highlightcolor=CYAN, width=width)
    if placeholder:
        e.insert(0, placeholder)
        e.config(fg=SUBTEXT)
        def _fi(ev, p=placeholder):
            if e.get() == p:
                e.delete(0, tk.END); e.config(fg=TEXT)
        def _fo(ev, p=placeholder):
            if not e.get():
                e.insert(0, p); e.config(fg=SUBTEXT)
        e.bind("<FocusIn>", _fi)
        e.bind("<FocusOut>", _fo)
    return e


def mk_btn(parent, text, cmd, bg=BORDER2, fg=TEXT, hover=None, padx=12, pady=5):
    b = tk.Button(parent, text=text, command=cmd, font=F["tag"],
                  bg=bg, fg=fg, relief="flat", cursor="hand2",
                  activebackground=hover or HOVER, activeforeground=fg,
                  padx=padx, pady=pady)
    b.bind("<Enter>", lambda e: b.config(bg=hover or HOVER))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def mk_del(parent, cmd):
    return mk_btn(parent, "✕", cmd, bg=CARD, fg=RED, hover="#2A0A12", padx=6, pady=3)


def mk_combo(parent, values, width=14):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("P.TCombobox",
                    fieldbackground=HOVER, background=HOVER, foreground=TEXT,
                    arrowcolor=CYAN, bordercolor=BORDER2,
                    lightcolor=BORDER2, darkcolor=BORDER2,
                    selectbackground=BORDER2, selectforeground=TEXT)
    c = ttk.Combobox(parent, values=values, state="readonly",
                     font=F["mono"], width=width, style="P.TCombobox")
    return c


def mk_card(parent, accent=BORDER, pady=4):
    outer = tk.Frame(parent, bg=CARD)
    outer.pack(fill="x", pady=pady, padx=2)
    tk.Frame(outer, bg=accent, height=1).pack(fill="x")
    inner = tk.Frame(outer, bg=CARD, padx=14, pady=10)
    inner.pack(fill="x")
    return outer, inner


# ═════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═════════════════════════════════════════════════════════════════════════════

class PlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        init_fonts()
        self.title("COMMAND PLANNER")
        self.geometry("1200x740")
        self.minsize(960, 620)
        self.configure(bg=BG)
        self.data         = load_data()
        self._task_sort   = "Priority"
        self._task_filter = None
        self._sbtn_refs   = {}
        self._build_ui()
        self._refresh_all()

    # ── Shell ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Top bar
        topbar = tk.Frame(self, bg=PANEL, height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=CYAN, width=4).pack(side="left", fill="y")
        lf = tk.Frame(topbar, bg=PANEL, padx=18); lf.pack(side="left", fill="y")
        tk.Label(lf, text="COMMAND", font=F["hero"], bg=PANEL, fg=TEXT).pack(side="left")
        tk.Label(lf, text=" PLANNER", font=F["hero"], bg=PANEL, fg=CYAN).pack(side="left")
        tk.Label(lf, text="  //  PRINCEBLUE", font=F["small"], bg=PANEL, fg=SUBTEXT).pack(side="left", pady=(6,0))
        rf = tk.Frame(topbar, bg=PANEL, padx=16); rf.pack(side="right", fill="y")
        self.clock_lbl = tk.Label(rf, font=F["clock"], bg=PANEL, fg=SUBTEXT)
        self.clock_lbl.pack(side="right", pady=4)
        mk_btn(rf, "💾  SAVE", self._manual_save, bg=BORDER2, fg=GREEN, hover=HOVER, pady=4
               ).pack(side="right", padx=8, pady=10)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        self._tick()

        # Body
        body = tk.Frame(self, bg=BG); body.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = tk.Frame(body, bg=PANEL, width=168)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Frame(self.sidebar, bg=BORDER, width=1).pack(side="right", fill="y")
        tk.Frame(self.sidebar, bg=PANEL, height=16).pack()
        tk.Label(self.sidebar, text="  NAVIGATION", font=F["tag"], fg=SUBTEXT, bg=PANEL
                 ).pack(anchor="w", padx=12, pady=(0,8))

        self.content_area = tk.Frame(body, bg=BG)
        self.content_area.pack(side="left", fill="both", expand=True)

        self.tab_frames = {}
        self.active_tab = tk.StringVar(value="OVERVIEW")

        for icon, name, color in TAB_META:
            f = tk.Frame(self.content_area, bg=BG)
            self.tab_frames[name] = f
            self._make_sbtn(icon, name, color)

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=12, pady=14)

        self._build_overview_tab()
        self._build_tests_tab()
        self._build_tasks_tab()
        self._build_lists_tab()
        self._build_assignments_tab()
        self._build_practicals_tab()

        self._show_tab("OVERVIEW")

    def _make_sbtn(self, icon, name, color):
        f   = tk.Frame(self.sidebar, bg=PANEL, cursor="hand2"); f.pack(fill="x", padx=10, pady=1)
        bar = tk.Frame(f, bg=PANEL, width=3);                   bar.pack(side="left", fill="y", pady=4)
        ico = tk.Label(f, text=icon, font=F["subhead"], bg=PANEL, fg=color, width=2)
        ico.pack(side="left", padx=(6,4), pady=8)
        lbl = tk.Label(f, text=name, font=F["small"], bg=PANEL, fg=SUBTEXT); lbl.pack(side="left")
        cnt = tk.Label(f, text="", font=F["tag"], bg=PANEL, fg=DIM);         cnt.pack(side="right", padx=10)
        self._sbtn_refs[name] = {"frame": f, "bar": bar, "ico": ico, "lbl": lbl, "color": color, "cnt": cnt}

        def enter(e):
            if self.active_tab.get() != name:
                for w in (f, bar, ico, lbl): w.config(bg=HOVER)
        def leave(e):
            if self.active_tab.get() != name:
                for w in (f, bar, ico, lbl): w.config(bg=PANEL)
        for w in (f, bar, ico, lbl):
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", lambda e, n=name: self._show_tab(n))

    def _show_tab(self, name):
        prev = self.active_tab.get()
        if prev in self._sbtn_refs:
            r = self._sbtn_refs[prev]
            for w in (r["frame"], r["bar"], r["ico"], r["lbl"]): w.config(bg=PANEL)
            r["lbl"].config(fg=SUBTEXT)
        self.active_tab.set(name)
        r = self._sbtn_refs[name]
        for w in (r["frame"], r["ico"], r["lbl"]): w.config(bg=HOVER)
        r["bar"].config(bg=r["color"]); r["lbl"].config(fg=TEXT)
        for n, fr in self.tab_frames.items(): fr.pack_forget()
        self.tab_frames[name].pack(fill="both", expand=True)
        if name == "OVERVIEW":
            self._refresh_overview()

    def _tick(self):
        self.clock_lbl.config(text=datetime.now().strftime("%a %d %b %Y  •  %H:%M:%S"))
        self.after(1000, self._tick)

    def _tab_header(self, tab, icon, title, subtitle, color):
        h = tk.Frame(tab, bg=BG, padx=24, pady=18); h.pack(fill="x")
        row = tk.Frame(h, bg=BG); row.pack(anchor="w")
        tk.Label(row, text=icon + " ", font=F["hero"], bg=BG, fg=color).pack(side="left")
        tk.Label(row, text=title,       font=F["hero"], bg=BG, fg=TEXT).pack(side="left")
        tk.Label(h,   text=subtitle,    font=F["small"], bg=BG, fg=SUBTEXT).pack(anchor="w")
        tk.Frame(tab, bg=color, height=1).pack(fill="x", padx=24)
        tk.Frame(tab, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(1,14))

    # ═══════════════════════════════════════════════════════════════════════
    # OVERVIEW TAB
    # ═══════════════════════════════════════════════════════════════════════

    def _build_overview_tab(self):
        sf = ScrollFrame(self.tab_frames["OVERVIEW"], bg=BG)
        sf.pack(fill="both", expand=True)
        self._ov_root = sf.inner

    def _refresh_overview(self):
        for w in self._ov_root.winfo_children():
            w.destroy()
        root = self._ov_root

        # Greeting
        greet = tk.Frame(root, bg=BG, padx=24, pady=20); greet.pack(fill="x")
        hour = datetime.now().hour
        tod  = "GOOD MORNING" if hour < 12 else ("GOOD AFTERNOON" if hour < 18 else "GOOD EVENING")
        tk.Label(greet, text=f"{tod}, PRINCEBLUE", font=F["hero"], bg=BG, fg=CYAN).pack(anchor="w")
        tk.Label(greet, text=datetime.now().strftime("%A, %d %B %Y"),
                 font=F["body"], bg=BG, fg=SUBTEXT).pack(anchor="w")

        mk_sep(root, BORDER, padx=24)

        # Stats row
        sf = tk.Frame(root, bg=BG, padx=24); sf.pack(fill="x", pady=(4,16))
        tests_up   = len([t for t in self.data["tests"] if (days_until(t.get("date","")) or -1) >= 0])
        tasks_p    = len([t for t in self.data["tasks"] if not t.get("done")])
        asgn_p     = len([a for a in self.data["assignments"] if not a.get("submitted")])
        prac_p     = len([p for p in self.data["practicals"] if not p.get("done")])
        lists_c    = len(self.data["lists"])
        for i, (lbl_txt, num, col) in enumerate([
            ("TESTS DUE", str(tests_up), GOLD),
            ("TASKS LEFT", str(tasks_p), ORANGE),
            ("ASSIGNMENTS", str(asgn_p), RED),
            ("PRACTICALS", str(prac_p), GREEN),
            ("LISTS", str(lists_c), BLUE),
        ]):
            sc = tk.Frame(sf, bg=CARD, padx=18, pady=14)
            sc.grid(row=0, column=i, padx=(0,10), sticky="ew")
            sf.grid_columnconfigure(i, weight=1)
            tk.Frame(sc, bg=col, height=2).pack(fill="x", pady=(0,8))
            tk.Label(sc, text=num,     font=F["num"],  bg=CARD, fg=col).pack(anchor="w")
            tk.Label(sc, text=lbl_txt, font=F["tag"],  bg=CARD, fg=SUBTEXT).pack(anchor="w")

        # ── Upcoming Tests
        self._ov_sec(root, "◈  UPCOMING TESTS", GOLD)
        tests = sorted([t for t in self.data["tests"]
                        if (days_until(t.get("date","")) or -1) >= 0],
                       key=lambda x: x.get("date",""))[:5]
        if tests:
            for t in tests:
                d = days_until(t.get("date",""))
                c = urgency_color(d)
                _, inn = mk_card(root, c, pady=2); inn.config(padx=20)
                row = tk.Frame(inn, bg=CARD); row.pack(fill="x")
                tk.Label(row, text=t.get("subject",""), font=F["subhead"], bg=CARD, fg=TEXT).pack(side="left")
                tk.Label(row, text=f"  {t.get('date','')}  {t.get('time','')}",
                         font=F["mono"], bg=CARD, fg=SUBTEXT).pack(side="left")
                tk.Label(row, text=urgency_label(d), font=F["tag"], fg=c, bg=CARD).pack(side="right")
        else:
            self._ov_empty(root, "No upcoming tests")

        # ── Priority Tasks
        self._ov_sec(root, "▣  PRIORITY TASKS", ORANGE)
        tasks = sorted([t for t in self.data["tasks"] if not t.get("done")],
                       key=lambda t: PRIORITY_ORDER.index(t.get("priority","Someday")))[:6]
        if tasks:
            for t in tasks:
                p  = t.get("priority","Someday")
                pc = PRIORITY_COLOR.get(p, SUBTEXT)
                _, inn = mk_card(root, pc, pady=2); inn.config(padx=20)
                row = tk.Frame(inn, bg=CARD); row.pack(fill="x")
                tk.Label(row, text=t.get("text",""), font=F["body"], bg=CARD, fg=TEXT).pack(side="left")
                tk.Label(row, text=p,                font=F["tag"],  fg=pc, bg=CARD).pack(side="right")
        else:
            self._ov_empty(root, "No pending tasks")

        # ── Assignments
        self._ov_sec(root, "◧  ASSIGNMENTS DUE", RED)
        asgns = sorted([a for a in self.data["assignments"] if not a.get("submitted")],
                       key=lambda x: x.get("due","9999"))[:5]
        if asgns:
            for a in asgns:
                d = days_until(a.get("due",""))
                c = urgency_color(d)
                _, inn = mk_card(root, c, pady=2); inn.config(padx=20)
                row = tk.Frame(inn, bg=CARD); row.pack(fill="x")
                tk.Label(row, text=f"[{a.get('subject','')}]  {a.get('title','')}",
                         font=F["body"], bg=CARD, fg=TEXT).pack(side="left")
                dl = (f"{d}d left" if (d or 0) >= 0 else "OVERDUE") if d is not None else "–"
                tk.Label(row, text=dl, font=F["tag"], fg=c, bg=CARD).pack(side="right")
        else:
            self._ov_empty(root, "No pending assignments")

        # ── Practicals
        self._ov_sec(root, "◩  PRACTICALS PENDING", GREEN)
        pracs = [p for p in self.data["practicals"] if not p.get("done")][:5]
        if pracs:
            for p in pracs:
                _, inn = mk_card(root, GREEN, pady=2); inn.config(padx=20)
                row = tk.Frame(inn, bg=CARD); row.pack(fill="x")
                tk.Label(row, text=f"Exp {p.get('num','?')} — {p.get('title','')}",
                         font=F["body"], bg=CARD, fg=TEXT).pack(side="left")
                sr = tk.Frame(row, bg=CARD); sr.pack(side="right")
                for sym, key in [("P","performed"),("W","writeup"),("S","submitted")]:
                    done = p.get(key, False)
                    tk.Label(sr, text=sym, font=F["tag"],
                             fg=GREEN if done else DIM, bg=CARD, padx=3).pack(side="left")
        else:
            self._ov_empty(root, "No pending practicals")

        # ── Lists
        self._ov_sec(root, "◫  LISTS SNAPSHOT", BLUE)
        if self.data["lists"]:
            grid = tk.Frame(root, bg=BG, padx=24); grid.pack(fill="x", pady=(0,8))
            cols = 3
            for i, lst in enumerate(self.data["lists"][:6]):
                total = len(lst.get("items",[]))
                done  = sum(1 for it in lst.get("items",[]) if it.get("done"))
                pct   = int((done/total)*100) if total else 0
                lc    = tk.Frame(grid, bg=CARD, padx=14, pady=10)
                lc.grid(row=i//cols, column=i%cols, padx=(0,10), pady=(0,8), sticky="ew")
                grid.grid_columnconfigure(i%cols, weight=1)
                tk.Frame(lc, bg=BLUE, height=1).pack(fill="x", pady=(0,6))
                tk.Label(lc, text=lst.get("name",""), font=F["subhead"], bg=CARD, fg=TEXT).pack(anchor="w")
                tk.Label(lc, text=f"{done}/{total} done  •  {pct}%",
                         font=F["tag"], bg=CARD, fg=SUBTEXT).pack(anchor="w")
                pb_out = tk.Frame(lc, bg=BORDER, height=4); pb_out.pack(fill="x", pady=(6,0))
                if pct > 0:
                    tk.Frame(pb_out, bg=BLUE, height=4).place(relwidth=pct/100, relheight=1)
        else:
            self._ov_empty(root, "No lists created yet")

        tk.Frame(root, bg=BG, height=24).pack()

    def _ov_sec(self, parent, title, color):
        f = tk.Frame(parent, bg=BG, padx=24); f.pack(fill="x", pady=(16,4))
        tk.Label(f, text=title, font=F["subhead"], bg=BG, fg=color).pack(anchor="w")
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", pady=(4,0))

    def _ov_empty(self, parent, msg):
        f = tk.Frame(parent, bg=BG, padx=28); f.pack(fill="x", pady=2)
        tk.Label(f, text=f"  {msg}", font=F["small"], bg=BG, fg=DIM).pack(anchor="w", pady=4)

    # ═══════════════════════════════════════════════════════════════════════
    # TESTS TAB
    # ═══════════════════════════════════════════════════════════════════════

    def _build_tests_tab(self):
        tab = self.tab_frames["TESTS"]
        self._tab_header(tab, "◈", "TESTS", "Schedule exams and track countdown", GOLD)
        form = tk.Frame(tab, bg=CARD, padx=20, pady=14); form.pack(fill="x", padx=24, pady=(0,14))
        tk.Frame(form, bg=GOLD, height=1).pack(fill="x", pady=(0,12))
        row = tk.Frame(form, bg=CARD); row.pack(fill="x")
        self.te_subj = mk_entry(row, 18, "Subject");       self.te_subj.pack(side="left", padx=(0,8))
        self.te_date = mk_entry(row, 13, "YYYY-MM-DD");    self.te_date.pack(side="left", padx=(0,8))
        self.te_time = mk_entry(row,  8, "HH:MM");         self.te_time.pack(side="left", padx=(0,8))
        self.te_note = mk_entry(row, 28, "Note (optional)"); self.te_note.pack(side="left", padx=(0,8))
        mk_btn(row, "＋  ADD TEST", self._add_test, GOLD, BG, "#BFA040", pady=6).pack(side="left")
        sf = ScrollFrame(tab, bg=BG); sf.pack(fill="both", expand=True, padx=24, pady=(0,12))
        self.tests_inner = sf.inner

    def _refresh_tests(self):
        for w in self.tests_inner.winfo_children(): w.destroy()
        tests = sorted(self.data["tests"], key=lambda x: (x.get("date",""), x.get("time","")))
        if not tests:
            tk.Label(self.tests_inner, text="No tests scheduled.", font=F["body"], bg=BG, fg=DIM).pack(pady=30); return
        for t in tests:
            d = days_until(t.get("date","")); c = urgency_color(d)
            _, inn = mk_card(self.tests_inner, c)
            row = tk.Frame(inn, bg=CARD); row.pack(fill="x")
            tk.Label(row, text=t.get("subject",""), font=F["subhead"], bg=CARD, fg=TEXT).pack(side="left")
            tk.Label(row, text=f"  {t.get('date','')}  {t.get('time','')}",
                     font=F["mono"], bg=CARD, fg=SUBTEXT).pack(side="left")
            right = tk.Frame(row, bg=CARD); right.pack(side="right")
            tk.Label(right, text=urgency_label(d), font=F["tag"], fg=c, bg=CARD, padx=8).pack(side="left")
            mk_del(right, lambda tid=t["id"]: self._del_test(tid)).pack(side="left")
            if t.get("note"):
                tk.Label(inn, text=t["note"], font=F["small"], bg=CARD, fg=SUBTEXT).pack(anchor="w", pady=(2,0))

    def _add_test(self):
        subj = self.te_subj.get().strip(); dt = self.te_date.get().strip()
        tm   = self.te_time.get().strip(); note = self.te_note.get().strip()
        for ph in ("Subject","YYYY-MM-DD","HH:MM","Note (optional)"):
            if subj==ph: subj=""
            if dt==ph:   dt=""
            if tm==ph:   tm=""
            if note==ph: note=""
        if not subj or not dt: messagebox.showwarning("Missing","Subject and Date required."); return
        try: datetime.strptime(dt, "%Y-%m-%d")
        except ValueError: messagebox.showwarning("Format","Date must be YYYY-MM-DD"); return
        self.data["tests"].append({"id": str(uuid.uuid4()), "subject": subj, "date": dt, "time": tm, "note": note})
        save_data(self.data)
        for e in (self.te_subj, self.te_date, self.te_time, self.te_note): e.delete(0, tk.END)
        self._refresh_tests()

    def _del_test(self, tid):
        self.data["tests"] = [t for t in self.data["tests"] if t["id"] != tid]
        save_data(self.data); self._refresh_tests()

    # ═══════════════════════════════════════════════════════════════════════
    # TASKS TAB
    # ═══════════════════════════════════════════════════════════════════════

    def _build_tasks_tab(self):
        tab = self.tab_frames["TASKS"]
        self._tab_header(tab, "▣", "TASKS", "Priority-sorted daily task management", ORANGE)
        form = tk.Frame(tab, bg=CARD, padx=20, pady=14); form.pack(fill="x", padx=24, pady=(0,10))
        tk.Frame(form, bg=ORANGE, height=1).pack(fill="x", pady=(0,12))
        row = tk.Frame(form, bg=CARD); row.pack(fill="x")
        self.ta_entry = mk_entry(row, 36, "Task description"); self.ta_entry.pack(side="left", padx=(0,8))
        self.ta_prio  = mk_combo(row, PRIORITY_ORDER, 14);    self.ta_prio.current(0); self.ta_prio.pack(side="left", padx=(0,8))
        self.ta_due   = mk_entry(row, 12, "YYYY-MM-DD");      self.ta_due.pack(side="left", padx=(0,8))
        mk_btn(row, "＋  ADD TASK", self._add_task, ORANGE, BG, "#C07020", pady=6).pack(side="left")

        ctrl = tk.Frame(tab, bg=BG, padx=24); ctrl.pack(fill="x", pady=(0,8))
        tk.Label(ctrl, text="SORT:", font=F["tag"], bg=BG, fg=SUBTEXT).pack(side="left", padx=(0,6))
        for s in ["Priority","Due Date","Added"]:
            mk_btn(ctrl, s, lambda x=s: self._sort_tasks(x), CARD, SUBTEXT, HOVER, 8, 3).pack(side="left", padx=2)
        tk.Label(ctrl, text="   FILTER:", font=F["tag"], bg=BG, fg=SUBTEXT).pack(side="left", padx=(10,6))
        mk_btn(ctrl, "ALL", lambda: self._filter_tasks(None), CARD, TEXT, HOVER, 8, 3).pack(side="left", padx=2)
        for p in PRIORITY_ORDER:
            c = PRIORITY_COLOR[p]
            mk_btn(ctrl, p, lambda x=p: self._filter_tasks(x),
                   PRIORITY_BG[p], c, HOVER, 8, 3).pack(side="left", padx=2)

        sf = ScrollFrame(tab, bg=BG); sf.pack(fill="both", expand=True, padx=24, pady=(0,12))
        self.tasks_inner = sf.inner

    def _refresh_tasks(self):
        for w in self.tasks_inner.winfo_children(): w.destroy()
        pending = [t for t in self.data["tasks"] if not t.get("done")]
        done    = [t for t in self.data["tasks"] if t.get("done")]
        if self._task_filter:
            pending = [t for t in pending if t.get("priority") == self._task_filter]
        pending = self._sort_list(pending, self._task_sort)
        if not pending and not done:
            tk.Label(self.tasks_inner, text="No tasks yet.", font=F["body"], bg=BG, fg=DIM).pack(pady=30); return
        for t in pending: self._task_card(self.tasks_inner, t)
        if done:
            mk_sep(self.tasks_inner, BORDER, pady=10)
            tk.Label(self.tasks_inner, text=f"✓  COMPLETED  ({len(done)})", font=F["tag"], bg=BG, fg=DIM).pack(anchor="w", pady=(0,6))
            for t in done[-6:]: self._task_card(self.tasks_inner, t, done=True)

    def _task_card(self, parent, t, done=False):
        p  = t.get("priority","Someday"); pc = PRIORITY_COLOR.get(p, SUBTEXT)
        _, inn = mk_card(parent, pc if not done else BORDER)
        inn.config(bg=CARD if not done else "#0D0F15")
        row = tk.Frame(inn, bg=inn["bg"]); row.pack(fill="x")
        var = tk.BooleanVar(value=done)
        tk.Checkbutton(row, variable=var, bg=inn["bg"], activebackground=inn["bg"],
                       fg=pc, selectcolor=HOVER,
                       command=lambda tid=t["id"], v=var: self._toggle_task(tid, v)).pack(side="left", padx=(0,6))
        sty = ("overstrike",) if done else ()
        tk.Label(row, text=t.get("text",""), font=(*F["body"][:2], *sty),
                 bg=inn["bg"], fg=SUBTEXT if done else TEXT).pack(side="left")
        right = tk.Frame(row, bg=inn["bg"]); right.pack(side="right")
        if not done:
            cp = mk_combo(right, PRIORITY_ORDER, 13); cp.set(p); cp.pack(side="left", padx=6)
            cp.bind("<<ComboboxSelected>>", lambda e, tid=t["id"], c=cp: self._change_prio(tid, c.get()))
        tk.Label(right, text=p, font=F["tag"], fg=pc, bg=inn["bg"], padx=6).pack(side="left")
        mk_del(right, lambda tid=t["id"]: self._del_task(tid)).pack(side="left")
        if t.get("due") and t.get("due") not in ("","YYYY-MM-DD"):
            d = days_until(t["due"]); dc = urgency_color(d)
            tk.Label(inn, text=f"Due {t['due']}  •  {urgency_label(d)}",
                     font=F["small"], bg=inn["bg"], fg=dc).pack(anchor="w", pady=(2,0))

    def _add_task(self):
        text = self.ta_entry.get().strip(); prio = self.ta_prio.get(); due = self.ta_due.get().strip()
        if text in ("","Task description"): messagebox.showwarning("Missing","Task text required."); return
        if due == "YYYY-MM-DD": due = ""
        self.data["tasks"].append({"id": str(uuid.uuid4()), "text": text, "priority": prio,
                                    "due": due, "done": False, "added": datetime.now().isoformat()})
        save_data(self.data); self.ta_entry.delete(0,tk.END); self._refresh_tasks()

    def _toggle_task(self, tid, var):
        for t in self.data["tasks"]:
            if t["id"] == tid: t["done"] = var.get()
        save_data(self.data); self._refresh_tasks()

    def _del_task(self, tid):
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != tid]
        save_data(self.data); self._refresh_tasks()

    def _change_prio(self, tid, p):
        for t in self.data["tasks"]:
            if t["id"] == tid: t["priority"] = p
        save_data(self.data); self._refresh_tasks()

    def _sort_tasks(self, by):  self._task_sort = by;  self._refresh_tasks()
    def _filter_tasks(self, p): self._task_filter = p; self._refresh_tasks()

    def _sort_list(self, tasks, by):
        if by == "Priority": return sorted(tasks, key=lambda t: PRIORITY_ORDER.index(t.get("priority","Someday")))
        if by == "Due Date": return sorted(tasks, key=lambda t: t.get("due","9999"))
        if by == "Added":    return sorted(tasks, key=lambda t: t.get("added",""), reverse=True)
        return tasks

    # ═══════════════════════════════════════════════════════════════════════
    # LISTS TAB
    # ═══════════════════════════════════════════════════════════════════════

    def _build_lists_tab(self):
        tab = self.tab_frames["LISTS"]
        self._tab_header(tab, "◫", "LISTS", "Running master lists of work to do", BLUE)
        ctrl = tk.Frame(tab, bg=BG, padx=24, pady=6); ctrl.pack(fill="x")
        self.li_name = mk_entry(ctrl, 28, "New list name"); self.li_name.pack(side="left", padx=(0,10))
        mk_btn(ctrl, "＋  CREATE LIST", self._add_list, BLUE, BG, "#2060A0", pady=6).pack(side="left")
        sf = ScrollFrame(tab, bg=BG); sf.pack(fill="both", expand=True, padx=24, pady=(8,12))
        self.lists_inner = sf.inner

    def _refresh_lists(self):
        for w in self.lists_inner.winfo_children(): w.destroy()
        if not self.data["lists"]:
            tk.Label(self.lists_inner, text="No lists created yet.", font=F["body"], bg=BG, fg=DIM).pack(pady=30); return
        for lst in self.data["lists"]: self._list_card(self.lists_inner, lst)

    def _list_card(self, parent, lst):
        outer = tk.Frame(parent, bg=CARD); outer.pack(fill="x", pady=6)
        tk.Frame(outer, bg=BLUE, height=1).pack(fill="x")
        inn = tk.Frame(outer, bg=CARD, padx=16, pady=12); inn.pack(fill="x")
        hrow = tk.Frame(inn, bg=CARD); hrow.pack(fill="x", pady=(0,8))
        tk.Label(hrow, text=lst.get("name",""), font=F["head"], bg=CARD, fg=BLUE).pack(side="left")
        total = len(lst.get("items",[])); done = sum(1 for i in lst.get("items",[]) if i.get("done"))
        tk.Label(hrow, text=f"{done}/{total}", font=F["tag"], bg=CARD, fg=SUBTEXT).pack(side="left", padx=10)
        mk_del(hrow, lambda lid=lst["id"]: self._del_list(lid)).pack(side="right")
        if total:
            pb = tk.Frame(inn, bg=BORDER, height=3); pb.pack(fill="x", pady=(0,10))
            if done: tk.Frame(pb, bg=BLUE, height=3).place(relwidth=done/total, relheight=1)
        for item in lst.get("items",[]):
            irow = tk.Frame(inn, bg=CARD); irow.pack(fill="x", pady=1)
            var = tk.BooleanVar(value=item.get("done",False))
            tk.Checkbutton(irow, variable=var, bg=CARD, activebackground=CARD, fg=BLUE, selectcolor=HOVER,
                           command=lambda lid=lst["id"],iid=item["id"],v=var: self._toggle_li(lid,iid,v)).pack(side="left")
            sty = ("overstrike",) if item.get("done") else ()
            tk.Label(irow, text=item.get("text",""), font=(*F["body"][:2], *sty),
                     bg=CARD, fg=SUBTEXT if item.get("done") else TEXT).pack(side="left")
            mk_del(irow, lambda lid=lst["id"],iid=item["id"]: self._del_li(lid,iid)).pack(side="right")
        arow = tk.Frame(inn, bg=CARD); arow.pack(fill="x", pady=(8,0))
        e = mk_entry(arow, 36, "Add item…"); e.pack(side="left", padx=(0,8))
        mk_btn(arow, "＋", lambda lid=lst["id"],en=e: self._add_li(lid,en),
               BLUE, BG, "#2060A0", 10, 4).pack(side="left")

    def _add_list(self):
        name = self.li_name.get().strip()
        if not name or name == "New list name": return
        self.data["lists"].append({"id": str(uuid.uuid4()), "name": name, "items": []})
        save_data(self.data); self.li_name.delete(0,tk.END); self._refresh_lists()

    def _del_list(self, lid):
        self.data["lists"] = [l for l in self.data["lists"] if l["id"] != lid]
        save_data(self.data); self._refresh_lists()

    def _add_li(self, lid, e):
        text = e.get().strip()
        if not text or text == "Add item…": return
        for l in self.data["lists"]:
            if l["id"] == lid: l["items"].append({"id": str(uuid.uuid4()), "text": text, "done": False})
        save_data(self.data); e.delete(0,tk.END); self._refresh_lists()

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

    # ═══════════════════════════════════════════════════════════════════════
    # ASSIGNMENTS TAB
    # ═══════════════════════════════════════════════════════════════════════

    def _build_assignments_tab(self):
        tab = self.tab_frames["ASSIGNMENTS"]
        self._tab_header(tab, "◧", "ASSIGNMENTS", "Track submissions and mark deadlines", RED)
        form = tk.Frame(tab, bg=CARD, padx=20, pady=14); form.pack(fill="x", padx=24, pady=(0,14))
        tk.Frame(form, bg=RED, height=1).pack(fill="x", pady=(0,12))
        row = tk.Frame(form, bg=CARD); row.pack(fill="x")
        self.as_subj  = mk_entry(row, 14, "Subject");          self.as_subj.pack(side="left", padx=(0,8))
        self.as_title = mk_entry(row, 26, "Assignment title");  self.as_title.pack(side="left", padx=(0,8))
        self.as_due   = mk_entry(row, 12, "YYYY-MM-DD");        self.as_due.pack(side="left", padx=(0,8))
        self.as_marks = mk_entry(row,  6, "Marks");             self.as_marks.pack(side="left", padx=(0,8))
        mk_btn(row, "＋  ADD", self._add_asgn, RED, TEXT, "#8B1020", pady=6).pack(side="left")
        sf = ScrollFrame(tab, bg=BG); sf.pack(fill="both", expand=True, padx=24, pady=(0,12))
        self.asgn_inner = sf.inner

    def _refresh_assignments(self):
        for w in self.asgn_inner.winfo_children(): w.destroy()
        pending = sorted([a for a in self.data["assignments"] if not a.get("submitted")],
                         key=lambda x: x.get("due","9999"))
        done    = [a for a in self.data["assignments"] if a.get("submitted")]
        if not pending and not done:
            tk.Label(self.asgn_inner, text="No assignments added.", font=F["body"], bg=BG, fg=DIM).pack(pady=30); return
        for a in pending: self._asgn_card(self.asgn_inner, a)
        if done:
            mk_sep(self.asgn_inner, BORDER, pady=10)
            tk.Label(self.asgn_inner, text=f"✓  SUBMITTED  ({len(done)})", font=F["tag"], bg=BG, fg=DIM).pack(anchor="w", pady=(0,6))
            for a in done: self._asgn_card(self.asgn_inner, a, submitted=True)

    def _asgn_card(self, parent, a, submitted=False):
        d = days_until(a.get("due","")); c = GREEN if submitted else urgency_color(d)
        _, inn = mk_card(parent, c); inn.config(bg=CARD if not submitted else "#0D0F15")
        row = tk.Frame(inn, bg=inn["bg"]); row.pack(fill="x")
        sty = ("overstrike",) if submitted else ()
        tk.Label(row, text=f"[{a.get('subject','')}]  {a.get('title','')}",
                 font=(*F["subhead"][:2], *sty), bg=inn["bg"],
                 fg=SUBTEXT if submitted else TEXT).pack(side="left")
        right = tk.Frame(row, bg=inn["bg"]); right.pack(side="right")
        if not submitted:
            dl = (f"{d}d left" if (d or 0) >= 0 else "OVERDUE") if d is not None else f"Due {a.get('due','')}"
            tk.Label(right, text=dl, font=F["tag"], fg=c, bg=inn["bg"], padx=8).pack(side="left")
            mk_btn(right, "✓ SUBMITTED", lambda aid=a["id"]: self._submit_asgn(aid),
                   GREEN, BG, "#1A6030", 8, 3).pack(side="left", padx=6)
        mk_del(right, lambda aid=a["id"]: self._del_asgn(aid)).pack(side="left")
        if a.get("marks"):
            tk.Label(inn, text=f"Marks: {a['marks']}", font=F["small"], bg=inn["bg"], fg=SUBTEXT).pack(anchor="w", pady=(2,0))

    def _add_asgn(self):
        subj=self.as_subj.get().strip(); title=self.as_title.get().strip()
        due=self.as_due.get().strip();   marks=self.as_marks.get().strip()
        for ph in ("Subject","Assignment title","YYYY-MM-DD","Marks"):
            if subj==ph: subj=""
            if title==ph: title=""
            if due==ph:   due=""
            if marks==ph: marks=""
        if not subj or not title: messagebox.showwarning("Missing","Subject and title required."); return
        self.data["assignments"].append({"id": str(uuid.uuid4()), "subject": subj, "title": title,
                                          "due": due, "marks": marks, "submitted": False})
        save_data(self.data)
        for e in (self.as_subj, self.as_title, self.as_due, self.as_marks): e.delete(0,tk.END)
        self._refresh_assignments()

    def _submit_asgn(self, aid):
        for a in self.data["assignments"]:
            if a["id"] == aid: a["submitted"] = True
        save_data(self.data); self._refresh_assignments()

    def _del_asgn(self, aid):
        self.data["assignments"] = [a for a in self.data["assignments"] if a["id"] != aid]
        save_data(self.data); self._refresh_assignments()

    # ═══════════════════════════════════════════════════════════════════════
    # PRACTICALS TAB
    # ═══════════════════════════════════════════════════════════════════════

    def _build_practicals_tab(self):
        tab = self.tab_frames["PRACTICALS"]
        self._tab_header(tab, "◩", "PRACTICALS", "Track lab experiments and writeup progress", GREEN)
        form = tk.Frame(tab, bg=CARD, padx=20, pady=14); form.pack(fill="x", padx=24, pady=(0,14))
        tk.Frame(form, bg=GREEN, height=1).pack(fill="x", pady=(0,12))
        row = tk.Frame(form, bg=CARD); row.pack(fill="x")
        self.pr_subj  = mk_entry(row, 14, "Subject");          self.pr_subj.pack(side="left", padx=(0,8))
        self.pr_num   = mk_entry(row,  6, "Exp No");           self.pr_num.pack(side="left", padx=(0,8))
        self.pr_title = mk_entry(row, 30, "Experiment title"); self.pr_title.pack(side="left", padx=(0,8))
        self.pr_date  = mk_entry(row, 12, "YYYY-MM-DD");       self.pr_date.pack(side="left", padx=(0,8))
        mk_btn(row, "＋  ADD", self._add_prac, GREEN, BG, "#1A6030", pady=6).pack(side="left")
        sf = ScrollFrame(tab, bg=BG); sf.pack(fill="both", expand=True, padx=24, pady=(0,12))
        self.prac_inner = sf.inner

    def _refresh_practicals(self):
        for w in self.prac_inner.winfo_children(): w.destroy()
        pending = sorted([p for p in self.data["practicals"] if not p.get("done")],
                         key=lambda x: (x.get("subject",""), int(x.get("num","0") or 0)))
        done    = [p for p in self.data["practicals"] if p.get("done")]
        if not pending and not done:
            tk.Label(self.prac_inner, text="No practicals added.", font=F["body"], bg=BG, fg=DIM).pack(pady=30); return
        for p in pending: self._prac_card(self.prac_inner, p)
        if done:
            mk_sep(self.prac_inner, BORDER, pady=10)
            tk.Label(self.prac_inner, text=f"✓  COMPLETED  ({len(done)})", font=F["tag"], bg=BG, fg=DIM).pack(anchor="w", pady=(0,6))
            for p in done: self._prac_card(self.prac_inner, p, done=True)

    def _prac_card(self, parent, p, done=False):
        _, inn = mk_card(parent, GREEN if not done else BORDER)
        inn.config(bg=CARD if not done else "#0D0F15")
        row = tk.Frame(inn, bg=inn["bg"]); row.pack(fill="x")
        sty = ("overstrike",) if done else ()
        tk.Label(row, text=f"Exp {p.get('num','?')}  —  {p.get('title','')}",
                 font=(*F["subhead"][:2], *sty), bg=inn["bg"],
                 fg=SUBTEXT if done else TEXT).pack(side="left")
        mk_del(row, lambda pid=p["id"]: self._del_prac(pid)).pack(side="right")
        tk.Label(inn, text=f"Subject: {p.get('subject','')}   Date: {p.get('date','')}",
                 font=F["small"], bg=inn["bg"], fg=SUBTEXT).pack(anchor="w", pady=(2,6))
        srow = tk.Frame(inn, bg=inn["bg"]); srow.pack(anchor="w")
        for lbl_txt, key, col in [("PERFORMED","performed",GREEN),("WRITEUP DONE","writeup",BLUE),("SUBMITTED","submitted",GOLD)]:
            val = p.get(key, False)
            b = mk_btn(srow, ("✓ " if val else "○ ") + lbl_txt,
                       lambda pid=p["id"],k=key: self._toggle_prac(pid,k),
                       col if val else BORDER2, BG if val else SUBTEXT, HOVER, 8, 3)
            b.pack(side="left", padx=(0,6))

    def _add_prac(self):
        subj=self.pr_subj.get().strip(); num=self.pr_num.get().strip()
        title=self.pr_title.get().strip(); dt=self.pr_date.get().strip()
        for ph in ("Subject","Exp No","Experiment title","YYYY-MM-DD"):
            if subj==ph:  subj=""
            if num==ph:   num=""
            if title==ph: title=""
            if dt==ph:    dt=""
        if not subj or not title: messagebox.showwarning("Missing","Subject and title required."); return
        self.data["practicals"].append({"id": str(uuid.uuid4()), "subject": subj, "num": num,
                                         "title": title, "date": dt,
                                         "performed": False, "writeup": False, "submitted": False, "done": False})
        save_data(self.data)
        for e in (self.pr_subj, self.pr_num, self.pr_title, self.pr_date): e.delete(0,tk.END)
        self._refresh_practicals()

    def _toggle_prac(self, pid, key):
        for p in self.data["practicals"]:
            if p["id"] == pid:
                p[key] = not p.get(key, False)
                p["done"] = p.get("performed") and p.get("writeup") and p.get("submitted")
        save_data(self.data); self._refresh_practicals()

    def _del_prac(self, pid):
        self.data["practicals"] = [p for p in self.data["practicals"] if p["id"] != pid]
        save_data(self.data); self._refresh_practicals()

    # ── Misc ──────────────────────────────────────────────────────────────

    def _refresh_all(self):
        self._refresh_tests()
        self._refresh_tasks()
        self._refresh_lists()
        self._refresh_assignments()
        self._refresh_practicals()
        self._update_sidebar_counts()

    def _update_sidebar_counts(self):
        counts = {
            "TESTS":       len([t for t in self.data["tests"] if (days_until(t.get("date","")) or -1) >= 0]),
            "TASKS":       len([t for t in self.data["tasks"] if not t.get("done")]),
            "LISTS":       len(self.data["lists"]),
            "ASSIGNMENTS": len([a for a in self.data["assignments"] if not a.get("submitted")]),
            "PRACTICALS":  len([p for p in self.data["practicals"] if not p.get("done")]),
        }
        for name, count in counts.items():
            if name in self._sbtn_refs:
                self._sbtn_refs[name]["cnt"].config(text=str(count) if count else "")

    def _manual_save(self):
        save_data(self.data)
        messagebox.showinfo("Saved", "All data saved to planner_data.json")


if __name__ == "__main__":
    app = PlannerApp()
    app.mainloop()
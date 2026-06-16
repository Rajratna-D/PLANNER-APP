import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime, date
import uuid

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "planner_data.json")

PRIORITY_ORDER = ["Immediate", "Important", "2nd Priority", "3rd Priority", "Someday"]
PRIORITY_COLORS = {
    "Immediate":    "#FF4C4C",
    "Important":    "#FF9F1C",
    "2nd Priority": "#4CC9F0",
    "3rd Priority": "#7BFF6A",
    "Someday":      "#9D9D9D",
}
PRIORITY_BG = {
    "Immediate":    "#3A1010",
    "Important":    "#3A2500",
    "2nd Priority": "#0D2A36",
    "3rd Priority": "#0D2E10",
    "Someday":      "#252525",
}

BG        = "#0E0F13"
PANEL     = "#16181F"
ACCENT    = "#4CC9F0"
ACCENT2   = "#FF4C4C"
TEXT      = "#E8EAF0"
SUBTEXT   = "#7A7D8A"
BORDER    = "#2A2D3A"
HOVER     = "#1E2130"
SUCCESS   = "#7BFF6A"
WARN      = "#FF9F1C"

FONT_TITLE  = ("Courier New", 22, "bold")
FONT_HEAD   = ("Courier New", 13, "bold")
FONT_BODY   = ("Courier New", 11)
FONT_SMALL  = ("Courier New", 9)
FONT_TAG    = ("Courier New", 9, "bold")


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "tests": [],
        "tasks": [],
        "lists": [],
        "assignments": [],
        "practicals": [],
    }


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def days_until(date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        delta = (d - date.today()).days
        return delta
    except Exception:
        return None


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, e=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, bg="#2A2D3A", fg=TEXT,
                 font=FONT_SMALL, relief="flat", padx=6, pady=3).pack()

    def hide(self, e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class ScrollFrame(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=kw.pop("bg", PANEL), **kw)
        self.canvas = tk.Canvas(self, bg=self["bg"], highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=self["bg"])
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind_all("<MouseWheel>", self._on_scroll)

    def _on_inner(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, e):
        self.canvas.itemconfig(self.inner_id, width=e.width)

    def _on_scroll(self, e):
        if self.winfo_ismapped():
            self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")


class PlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("COMMAND PLANNER — PRINCEBLUE")
        self.geometry("1160x720")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.data = load_data()
        self._build_ui()
        self._refresh_all()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG, pady=0)
        header.pack(fill="x", padx=0, pady=0)

        tk.Frame(header, bg=ACCENT, height=3).pack(fill="x")
        inner_h = tk.Frame(header, bg=BG, pady=10, padx=22)
        inner_h.pack(fill="x")
        tk.Label(inner_h, text="◈  COMMAND PLANNER", font=FONT_TITLE,
                 bg=BG, fg=ACCENT).pack(side="left")
        self.clock_lbl = tk.Label(inner_h, font=FONT_SMALL, bg=BG, fg=SUBTEXT)
        self.clock_lbl.pack(side="right", padx=10)
        self._tick()
        tk.Frame(header, bg=BORDER, height=1).pack(fill="x")

        # Sidebar + Content
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(body, bg=PANEL, width=155)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        self.content = tk.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        # Tabs
        self.tab_frames = {}
        tabs = [
            ("📅", "TESTS"),
            ("✅", "TASKS"),
            ("📋", "LISTS"),
            ("📝", "ASSIGNMENTS"),
            ("🔬", "PRACTICALS"),
        ]
        self.active_tab = tk.StringVar(value="TESTS")
        for icon, name in tabs:
            self._sidebar_btn(icon, name)

        # Separator
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=10, pady=6)
        tk.Label(self.sidebar, text="DATA", font=FONT_SMALL, bg=PANEL, fg=SUBTEXT).pack(pady=(0,4))
        save_btn = tk.Button(self.sidebar, text="💾  SAVE", font=FONT_SMALL,
                             bg=HOVER, fg=SUCCESS, relief="flat", activebackground=BORDER,
                             activeforeground=SUCCESS, cursor="hand2",
                             command=self._manual_save, pady=5)
        save_btn.pack(fill="x", padx=10)

        # Pages
        for _, name in tabs:
            f = tk.Frame(self.content, bg=BG)
            self.tab_frames[name] = f

        self._build_tests_tab()
        self._build_tasks_tab()
        self._build_lists_tab()
        self._build_assignments_tab()
        self._build_practicals_tab()

        self._show_tab("TESTS")

    def _sidebar_btn(self, icon, name):
        f = tk.Frame(self.sidebar, bg=PANEL, cursor="hand2")
        f.pack(fill="x", pady=1, padx=6)

        def enter(e): f.config(bg=HOVER); lbl.config(bg=HOVER); ico.config(bg=HOVER)
        def leave(e):
            if self.active_tab.get() != name:
                f.config(bg=PANEL); lbl.config(bg=PANEL); ico.config(bg=PANEL)

        ico = tk.Label(f, text=icon, font=("Courier New", 14), bg=PANEL, fg=TEXT, pady=8, padx=8)
        ico.pack(side="left")
        lbl = tk.Label(f, text=name, font=FONT_SMALL, bg=PANEL, fg=TEXT, pady=8)
        lbl.pack(side="left")

        for w in (f, ico, lbl):
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", lambda e, n=name: self._show_tab(n))

        setattr(self, f"_sbtn_{name}", (f, ico, lbl))

    def _show_tab(self, name):
        prev = self.active_tab.get()
        # reset previous
        if hasattr(self, f"_sbtn_{prev}"):
            f, ico, lbl = getattr(self, f"_sbtn_{prev}")
            f.config(bg=PANEL); ico.config(bg=PANEL); lbl.config(bg=PANEL, fg=TEXT)
        self.active_tab.set(name)
        f, ico, lbl = getattr(self, f"_sbtn_{name}")
        f.config(bg=HOVER); ico.config(bg=HOVER); lbl.config(bg=HOVER, fg=ACCENT)
        for n, frame in self.tab_frames.items():
            frame.pack_forget()
        self.tab_frames[name].pack(fill="both", expand=True)

    # ── Clock ───────────────────────────────────────────────────────────────

    def _tick(self):
        now = datetime.now().strftime("%a, %d %b %Y   %H:%M:%S")
        self.clock_lbl.config(text=now)
        self.after(1000, self._tick)

    # ══════════════════════════════════════════════════════════════════════════
    # TESTS TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_tests_tab(self):
        tab = self.tab_frames["TESTS"]
        self._tab_header(tab, "📅  UPCOMING TESTS", "Track exam dates & times")

        # Add test form
        form = tk.Frame(tab, bg=PANEL, padx=16, pady=14)
        form.pack(fill="x", padx=20, pady=(0, 12))
        tk.Frame(form, bg=ACCENT, height=2).pack(fill="x", pady=(0, 10))

        row1 = tk.Frame(form, bg=PANEL)
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="Subject:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT, width=9, anchor="w").pack(side="left")
        self.test_subj = self._entry(row1)
        self.test_subj.pack(side="left", padx=(4, 16))
        tk.Label(row1, text="Date (YYYY-MM-DD):", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        self.test_date = self._entry(row1, width=14)
        self.test_date.pack(side="left", padx=(4, 16))
        tk.Label(row1, text="Time (HH:MM):", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        self.test_time = self._entry(row1, width=8)
        self.test_time.pack(side="left", padx=(4, 16))

        row2 = tk.Frame(form, bg=PANEL)
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="Note:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT, width=9, anchor="w").pack(side="left")
        self.test_note = self._entry(row2, width=50)
        self.test_note.pack(side="left", padx=(4, 16))
        self._btn(row2, "＋ ADD TEST", self._add_test, ACCENT).pack(side="left")

        # List
        sf = ScrollFrame(tab, bg=BG)
        sf.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.tests_inner = sf.inner

    def _refresh_tests(self):
        for w in self.tests_inner.winfo_children():
            w.destroy()
        tests = sorted(self.data["tests"], key=lambda x: (x.get("date", ""), x.get("time", "")))
        if not tests:
            tk.Label(self.tests_inner, text="No tests scheduled. Add one above.", 
                     font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(pady=30)
            return
        for t in tests:
            self._test_card(self.tests_inner, t)

    def _test_card(self, parent, t):
        d = days_until(t.get("date", ""))
        if d is None:
            badge_col, badge_txt = SUBTEXT, "?"
        elif d < 0:
            badge_col, badge_txt = SUBTEXT, "PAST"
        elif d == 0:
            badge_col, badge_txt = ACCENT2, "TODAY"
        elif d == 1:
            badge_col, badge_txt = WARN, "TOMORROW"
        elif d <= 3:
            badge_col, badge_txt = WARN, f"{d}d"
        else:
            badge_col, badge_txt = SUCCESS, f"{d}d"

        card = tk.Frame(parent, bg=PANEL, padx=14, pady=10)
        card.pack(fill="x", pady=4)
        tk.Frame(card, bg=badge_col, width=4).pack(side="left", fill="y", padx=(0, 12))

        info = tk.Frame(card, bg=PANEL)
        info.pack(side="left", fill="both", expand=True)
        tk.Label(info, text=t.get("subject", "?"), font=FONT_HEAD, bg=PANEL, fg=TEXT).pack(anchor="w")
        details = f"📅 {t.get('date','')}  ⏰ {t.get('time','')}   {t.get('note','')}"
        tk.Label(info, text=details, font=FONT_SMALL, bg=PANEL, fg=SUBTEXT).pack(anchor="w")

        right = tk.Frame(card, bg=PANEL)
        right.pack(side="right")
        tk.Label(right, text=badge_txt, font=FONT_TAG, bg=badge_col,
                 fg=BG, padx=8, pady=3).pack(side="left", padx=8)
        self._del_btn(right, lambda tid=t["id"]: self._del_test(tid))

    def _add_test(self):
        subj = self.test_subj.get().strip()
        dt   = self.test_date.get().strip()
        tm   = self.test_time.get().strip()
        note = self.test_note.get().strip()
        if not subj or not dt:
            messagebox.showwarning("Missing", "Subject and Date are required.")
            return
        try:
            datetime.strptime(dt, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Format", "Date must be YYYY-MM-DD")
            return
        self.data["tests"].append({"id": str(uuid.uuid4()), "subject": subj,
                                    "date": dt, "time": tm, "note": note})
        save_data(self.data)
        for e in (self.test_subj, self.test_date, self.test_time, self.test_note):
            e.delete(0, tk.END)
        self._refresh_tests()

    def _del_test(self, tid):
        self.data["tests"] = [t for t in self.data["tests"] if t["id"] != tid]
        save_data(self.data)
        self._refresh_tests()

    # ══════════════════════════════════════════════════════════════════════════
    # TASKS TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_tasks_tab(self):
        tab = self.tab_frames["TASKS"]
        self._tab_header(tab, "✅  DAILY TASKS", "Sort by priority — get things done")

        # Add task form
        form = tk.Frame(tab, bg=PANEL, padx=16, pady=14)
        form.pack(fill="x", padx=20, pady=(0, 12))
        tk.Frame(form, bg=WARN, height=2).pack(fill="x", pady=(0, 10))

        row = tk.Frame(form, bg=PANEL)
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Task:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT, width=7, anchor="w").pack(side="left")
        self.task_entry = self._entry(row, width=40)
        self.task_entry.pack(side="left", padx=(4, 16))

        tk.Label(row, text="Priority:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        self.task_prio = ttk.Combobox(row, values=PRIORITY_ORDER, state="readonly",
                                       font=FONT_BODY, width=14)
        self.task_prio.current(0)
        self._style_combo(self.task_prio)
        self.task_prio.pack(side="left", padx=(4, 16))

        tk.Label(row, text="Due:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        self.task_due = self._entry(row, width=12)
        self.task_due.insert(0, "YYYY-MM-DD")
        self.task_due.pack(side="left", padx=(4, 16))
        self._btn(row, "＋ ADD", self._add_task, WARN).pack(side="left")

        # Sort bar
        sbar = tk.Frame(tab, bg=BG, padx=20)
        sbar.pack(fill="x", pady=(0, 8))
        tk.Label(sbar, text="SORT:", font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(side="left", padx=(0, 8))
        for label in ["Priority", "Due Date", "Added"]:
            self._btn(sbar, label, lambda l=label: self._sort_tasks(l), BORDER,
                      fg=SUBTEXT, active=HOVER).pack(side="left", padx=3)

        # Filter bar
        fbar = tk.Frame(tab, bg=BG, padx=20)
        fbar.pack(fill="x", pady=(0, 8))
        tk.Label(fbar, text="FILTER:", font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(side="left", padx=(0,8))
        self._btn(fbar, "All", lambda: self._filter_tasks(None), BORDER, fg=TEXT, active=HOVER).pack(side="left", padx=3)
        for p in PRIORITY_ORDER:
            c = PRIORITY_COLORS[p]
            self._btn(fbar, p, lambda prio=p: self._filter_tasks(prio),
                      PRIORITY_BG[p], fg=c, active=PRIORITY_BG[p]).pack(side="left", padx=3)

        sf = ScrollFrame(tab, bg=BG)
        sf.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.tasks_inner = sf.inner
        self._task_filter = None
        self._task_sort = "Priority"

    def _refresh_tasks(self):
        for w in self.tasks_inner.winfo_children():
            w.destroy()
        tasks = [t for t in self.data["tasks"] if not t.get("done")]
        done  = [t for t in self.data["tasks"] if t.get("done")]
        if self._task_filter:
            tasks = [t for t in tasks if t.get("priority") == self._task_filter]
        tasks = self._sort_task_list(tasks, self._task_sort)

        if not tasks and not done:
            tk.Label(self.tasks_inner, text="No tasks. Add one above.",
                     font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(pady=30)
            return

        for t in tasks:
            self._task_card(self.tasks_inner, t)

        if done:
            tk.Frame(self.tasks_inner, bg=BORDER, height=1).pack(fill="x", pady=10)
            tk.Label(self.tasks_inner, text=f"✓  COMPLETED  ({len(done)})",
                     font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(anchor="w", pady=(0,6))
            for t in done[-5:]:
                self._task_card(self.tasks_inner, t, done=True)

    def _task_card(self, parent, t, done=False):
        p = t.get("priority", "Someday")
        pc = PRIORITY_COLORS.get(p, SUBTEXT)
        pbg = PRIORITY_BG.get(p, "#252525")

        card = tk.Frame(parent, bg=PANEL if not done else "#111318", padx=14, pady=9)
        card.pack(fill="x", pady=3)
        tk.Frame(card, bg=pc if not done else BORDER, width=4).pack(side="left", fill="y", padx=(0,12))

        # Checkbox
        var = tk.BooleanVar(value=done)
        cb = tk.Checkbutton(card, variable=var, bg=PANEL if not done else "#111318",
                            activebackground=PANEL, fg=pc, selectcolor=pbg,
                            command=lambda tid=t["id"], v=var: self._toggle_task(tid, v))
        cb.pack(side="left", padx=(0, 8))

        info = tk.Frame(card, bg=card["bg"])
        info.pack(side="left", fill="both", expand=True)
        style = ("overstrike",) if done else ()
        tk.Label(info, text=t.get("text",""), font=(*FONT_BODY[:2], *style),
                 bg=card["bg"], fg=SUBTEXT if done else TEXT).pack(anchor="w")
        due = t.get("due", "")
        if due and due != "YYYY-MM-DD":
            d = days_until(due)
            due_str = f"Due: {due}"
            if d is not None:
                due_str += f"  ({d}d)" if d >= 0 else "  (overdue)"
            tk.Label(info, text=due_str, font=FONT_SMALL, bg=card["bg"], fg=SUBTEXT).pack(anchor="w")

        right = tk.Frame(card, bg=card["bg"])
        right.pack(side="right")
        tk.Label(right, text=p, font=FONT_TAG, bg=pbg, fg=pc, padx=7, pady=2).pack(side="left", padx=8)

        if not done:
            # Change priority
            cp = ttk.Combobox(right, values=PRIORITY_ORDER, state="readonly",
                               font=FONT_SMALL, width=13)
            cp.set(p)
            self._style_combo(cp)
            cp.pack(side="left", padx=4)
            cp.bind("<<ComboboxSelected>>", lambda e, tid=t["id"], c=cp: self._change_priority(tid, c.get()))

        self._del_btn(right, lambda tid=t["id"]: self._del_task(tid))

    def _add_task(self):
        text = self.task_entry.get().strip()
        prio = self.task_prio.get()
        due  = self.task_due.get().strip()
        if not text:
            messagebox.showwarning("Missing", "Task text is required.")
            return
        if due == "YYYY-MM-DD":
            due = ""
        self.data["tasks"].append({"id": str(uuid.uuid4()), "text": text,
                                    "priority": prio, "due": due,
                                    "done": False, "added": datetime.now().isoformat()})
        save_data(self.data)
        self.task_entry.delete(0, tk.END)
        self._refresh_tasks()

    def _toggle_task(self, tid, var):
        for t in self.data["tasks"]:
            if t["id"] == tid:
                t["done"] = var.get()
        save_data(self.data)
        self._refresh_tasks()

    def _del_task(self, tid):
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != tid]
        save_data(self.data)
        self._refresh_tasks()

    def _change_priority(self, tid, new_prio):
        for t in self.data["tasks"]:
            if t["id"] == tid:
                t["priority"] = new_prio
        save_data(self.data)
        self._refresh_tasks()

    def _sort_tasks(self, by):
        self._task_sort = by
        self._refresh_tasks()

    def _filter_tasks(self, prio):
        self._task_filter = prio
        self._refresh_tasks()

    def _sort_task_list(self, tasks, by):
        if by == "Priority":
            return sorted(tasks, key=lambda t: PRIORITY_ORDER.index(t.get("priority","Someday")))
        elif by == "Due Date":
            return sorted(tasks, key=lambda t: t.get("due","9999"))
        elif by == "Added":
            return sorted(tasks, key=lambda t: t.get("added",""), reverse=True)
        return tasks

    # ══════════════════════════════════════════════════════════════════════════
    # LISTS TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_lists_tab(self):
        tab = self.tab_frames["LISTS"]
        self._tab_header(tab, "📋  MASTER LISTS", "Keep running lists of work to do")

        ctrl = tk.Frame(tab, bg=BG, padx=20, pady=6)
        ctrl.pack(fill="x")
        self.new_list_entry = self._entry(ctrl, width=30)
        self.new_list_entry.pack(side="left", padx=(0,10))
        self._btn(ctrl, "＋ NEW LIST", self._add_list, ACCENT).pack(side="left")

        sf = ScrollFrame(tab, bg=BG)
        sf.pack(fill="both", expand=True, padx=20, pady=8)
        self.lists_inner = sf.inner

    def _refresh_lists(self):
        for w in self.lists_inner.winfo_children():
            w.destroy()
        if not self.data["lists"]:
            tk.Label(self.lists_inner, text="No lists yet. Create one above.",
                     font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(pady=30)
            return
        for lst in self.data["lists"]:
            self._list_card(self.lists_inner, lst)

    def _list_card(self, parent, lst):
        card = tk.Frame(parent, bg=PANEL, padx=14, pady=10)
        card.pack(fill="x", pady=6)
        tk.Frame(card, bg=ACCENT, height=2).pack(fill="x", pady=(0,8))

        header = tk.Frame(card, bg=PANEL)
        header.pack(fill="x")
        tk.Label(header, text=lst.get("name","List"), font=FONT_HEAD, bg=PANEL, fg=ACCENT).pack(side="left")
        total = len(lst.get("items",[]))
        done  = sum(1 for i in lst.get("items",[]) if i.get("done"))
        tk.Label(header, text=f"{done}/{total} done", font=FONT_SMALL, bg=PANEL, fg=SUBTEXT).pack(side="left", padx=12)
        self._del_btn(header, lambda lid=lst["id"]: self._del_list(lid))

        items_frame = tk.Frame(card, bg=PANEL)
        items_frame.pack(fill="x", pady=(6,0))

        for item in lst.get("items", []):
            irow = tk.Frame(items_frame, bg=PANEL)
            irow.pack(fill="x", pady=1)
            var = tk.BooleanVar(value=item.get("done", False))
            tk.Checkbutton(irow, variable=var, bg=PANEL, activebackground=PANEL,
                           fg=ACCENT, selectcolor=HOVER,
                           command=lambda lid=lst["id"], iid=item["id"], v=var: self._toggle_list_item(lid, iid, v)
                           ).pack(side="left")
            sty = ("overstrike",) if item.get("done") else ()
            tk.Label(irow, text=item.get("text",""), font=(*FONT_BODY[:2], *sty),
                     bg=PANEL, fg=SUBTEXT if item.get("done") else TEXT).pack(side="left")
            self._del_btn(irow, lambda lid=lst["id"], iid=item["id"]: self._del_list_item(lid, iid))

        add_row = tk.Frame(card, bg=PANEL)
        add_row.pack(fill="x", pady=(8,0))
        entry = self._entry(add_row, width=40)
        entry.pack(side="left", padx=(0,8))
        self._btn(add_row, "＋", lambda lid=lst["id"], e=entry: self._add_list_item(lid, e), ACCENT,
                  padx=6).pack(side="left")

    def _add_list(self):
        name = self.new_list_entry.get().strip()
        if not name:
            return
        self.data["lists"].append({"id": str(uuid.uuid4()), "name": name, "items": []})
        save_data(self.data)
        self.new_list_entry.delete(0, tk.END)
        self._refresh_lists()

    def _del_list(self, lid):
        self.data["lists"] = [l for l in self.data["lists"] if l["id"] != lid]
        save_data(self.data)
        self._refresh_lists()

    def _add_list_item(self, lid, entry):
        text = entry.get().strip()
        if not text:
            return
        for lst in self.data["lists"]:
            if lst["id"] == lid:
                lst["items"].append({"id": str(uuid.uuid4()), "text": text, "done": False})
        save_data(self.data)
        entry.delete(0, tk.END)
        self._refresh_lists()

    def _del_list_item(self, lid, iid):
        for lst in self.data["lists"]:
            if lst["id"] == lid:
                lst["items"] = [i for i in lst["items"] if i["id"] != iid]
        save_data(self.data)
        self._refresh_lists()

    def _toggle_list_item(self, lid, iid, var):
        for lst in self.data["lists"]:
            if lst["id"] == lid:
                for item in lst["items"]:
                    if item["id"] == iid:
                        item["done"] = var.get()
        save_data(self.data)
        self._refresh_lists()

    # ══════════════════════════════════════════════════════════════════════════
    # ASSIGNMENTS TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_assignments_tab(self):
        tab = self.tab_frames["ASSIGNMENTS"]
        self._tab_header(tab, "📝  ASSIGNMENTS", "Track submissions and deadlines")

        form = tk.Frame(tab, bg=PANEL, padx=16, pady=14)
        form.pack(fill="x", padx=20, pady=(0, 12))
        tk.Frame(form, bg=ACCENT2, height=2).pack(fill="x", pady=(0, 10))

        row = tk.Frame(form, bg=PANEL)
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Subject:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT, width=9, anchor="w").pack(side="left")
        self.asgn_subj = self._entry(row, width=20)
        self.asgn_subj.pack(side="left", padx=(4, 12))
        tk.Label(row, text="Title:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        self.asgn_title = self._entry(row, width=25)
        self.asgn_title.pack(side="left", padx=(4, 12))
        tk.Label(row, text="Due:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        self.asgn_due = self._entry(row, width=13)
        self.asgn_due.insert(0, "YYYY-MM-DD")
        self.asgn_due.pack(side="left", padx=(4, 12))
        tk.Label(row, text="Marks:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        self.asgn_marks = self._entry(row, width=6)
        self.asgn_marks.pack(side="left", padx=(4, 12))
        self._btn(row, "＋ ADD", self._add_asgn, ACCENT2).pack(side="left")

        sf = ScrollFrame(tab, bg=BG)
        sf.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.asgn_inner = sf.inner

    def _refresh_assignments(self):
        for w in self.asgn_inner.winfo_children():
            w.destroy()
        pending  = [a for a in self.data["assignments"] if not a.get("submitted")]
        done     = [a for a in self.data["assignments"] if a.get("submitted")]
        pending  = sorted(pending, key=lambda x: x.get("due", "9999"))

        if not pending and not done:
            tk.Label(self.asgn_inner, text="No assignments added yet.",
                     font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(pady=30)
            return

        for a in pending:
            self._asgn_card(self.asgn_inner, a)

        if done:
            tk.Frame(self.asgn_inner, bg=BORDER, height=1).pack(fill="x", pady=10)
            tk.Label(self.asgn_inner, text=f"✓  SUBMITTED  ({len(done)})",
                     font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(anchor="w", pady=(0,6))
            for a in done:
                self._asgn_card(self.asgn_inner, a, submitted=True)

    def _asgn_card(self, parent, a, submitted=False):
        d = days_until(a.get("due",""))
        if submitted:
            bc = SUCCESS
        elif d is None:
            bc = SUBTEXT
        elif d < 0:
            bc = SUBTEXT
        elif d == 0:
            bc = ACCENT2
        elif d <= 3:
            bc = WARN
        else:
            bc = ACCENT

        card = tk.Frame(parent, bg=PANEL if not submitted else "#111318", padx=14, pady=10)
        card.pack(fill="x", pady=4)
        tk.Frame(card, bg=bc, width=4).pack(side="left", fill="y", padx=(0,12))

        info = tk.Frame(card, bg=card["bg"])
        info.pack(side="left", fill="both", expand=True)
        sty = ("overstrike",) if submitted else ()
        tk.Label(info, text=f"[{a.get('subject','')}]  {a.get('title','')}",
                 font=(*FONT_HEAD[:2], *sty), bg=card["bg"],
                 fg=SUBTEXT if submitted else TEXT).pack(anchor="w")
        meta = f"Due: {a.get('due','')}   Marks: {a.get('marks','?')}"
        if not submitted and d is not None and d >= 0:
            meta += f"   ({d}d left)"
        elif not submitted and d is not None and d < 0:
            meta += "   ⚠ OVERDUE"
        tk.Label(info, text=meta, font=FONT_SMALL, bg=card["bg"], fg=SUBTEXT).pack(anchor="w")

        right = tk.Frame(card, bg=card["bg"])
        right.pack(side="right")
        if not submitted:
            self._btn(right, "✓ SUBMITTED", lambda aid=a["id"]: self._submit_asgn(aid), SUCCESS,
                      fg=BG, padx=8).pack(side="left", padx=8)
        self._del_btn(right, lambda aid=a["id"]: self._del_asgn(aid))

    def _add_asgn(self):
        subj  = self.asgn_subj.get().strip()
        title = self.asgn_title.get().strip()
        due   = self.asgn_due.get().strip()
        marks = self.asgn_marks.get().strip()
        if not subj or not title:
            messagebox.showwarning("Missing", "Subject and Title required.")
            return
        if due == "YYYY-MM-DD":
            due = ""
        self.data["assignments"].append({"id": str(uuid.uuid4()), "subject": subj,
                                          "title": title, "due": due, "marks": marks,
                                          "submitted": False})
        save_data(self.data)
        for e in (self.asgn_subj, self.asgn_title, self.asgn_due, self.asgn_marks):
            e.delete(0, tk.END)
        self._refresh_assignments()

    def _submit_asgn(self, aid):
        for a in self.data["assignments"]:
            if a["id"] == aid:
                a["submitted"] = True
        save_data(self.data)
        self._refresh_assignments()

    def _del_asgn(self, aid):
        self.data["assignments"] = [a for a in self.data["assignments"] if a["id"] != aid]
        save_data(self.data)
        self._refresh_assignments()

    # ══════════════════════════════════════════════════════════════════════════
    # PRACTICALS TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_practicals_tab(self):
        tab = self.tab_frames["PRACTICALS"]
        self._tab_header(tab, "🔬  PRACTICALS", "Track lab writeups and experiments")

        form = tk.Frame(tab, bg=PANEL, padx=16, pady=14)
        form.pack(fill="x", padx=20, pady=(0, 12))
        tk.Frame(form, bg=SUCCESS, height=2).pack(fill="x", pady=(0, 10))

        row = tk.Frame(form, bg=PANEL)
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Subject:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT, width=9, anchor="w").pack(side="left")
        self.prac_subj = self._entry(row, width=18)
        self.prac_subj.pack(side="left", padx=(4, 12))
        tk.Label(row, text="Exp No:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        self.prac_num = self._entry(row, width=6)
        self.prac_num.pack(side="left", padx=(4, 12))
        tk.Label(row, text="Experiment Title:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        self.prac_title = self._entry(row, width=30)
        self.prac_title.pack(side="left", padx=(4, 12))
        tk.Label(row, text="Date:", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        self.prac_date = self._entry(row, width=12)
        self.prac_date.insert(0, "YYYY-MM-DD")
        self.prac_date.pack(side="left", padx=(4, 12))
        self._btn(row, "＋ ADD", self._add_prac, SUCCESS, fg=BG).pack(side="left")

        sf = ScrollFrame(tab, bg=BG)
        sf.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.prac_inner = sf.inner

    def _refresh_practicals(self):
        for w in self.prac_inner.winfo_children():
            w.destroy()
        pending = [p for p in self.data["practicals"] if not p.get("done")]
        done    = [p for p in self.data["practicals"] if p.get("done")]
        pending = sorted(pending, key=lambda x: (x.get("subject",""), int(x.get("num","0") or 0)))

        if not pending and not done:
            tk.Label(self.prac_inner, text="No practicals added yet.",
                     font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(pady=30)
            return

        for p in pending:
            self._prac_card(self.prac_inner, p)

        if done:
            tk.Frame(self.prac_inner, bg=BORDER, height=1).pack(fill="x", pady=10)
            tk.Label(self.prac_inner, text=f"✓  COMPLETED WRITEUPS  ({len(done)})",
                     font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(anchor="w", pady=(0,6))
            for p in done:
                self._prac_card(self.prac_inner, p, done=True)

    def _prac_card(self, parent, p, done=False):
        card = tk.Frame(parent, bg=PANEL if not done else "#111318", padx=14, pady=10)
        card.pack(fill="x", pady=4)
        tk.Frame(card, bg=SUCCESS if not done else BORDER, width=4).pack(side="left", fill="y", padx=(0,12))

        info = tk.Frame(card, bg=card["bg"])
        info.pack(side="left", fill="both", expand=True)
        sty = ("overstrike",) if done else ()
        tk.Label(info, text=f"Exp {p.get('num','?')} — {p.get('title','')}",
                 font=(*FONT_HEAD[:2], *sty), bg=card["bg"],
                 fg=SUBTEXT if done else TEXT).pack(anchor="w")
        meta = f"Subject: {p.get('subject','')}   Date: {p.get('date','')}"
        tk.Label(info, text=meta, font=FONT_SMALL, bg=card["bg"], fg=SUBTEXT).pack(anchor="w")

        # Status badges
        status_frame = tk.Frame(info, bg=card["bg"])
        status_frame.pack(anchor="w", pady=(4,0))
        stages = [("Performed", "performed"), ("Writeup Done", "writeup"), ("Submitted", "submitted")]
        for label, key in stages:
            val = p.get(key, False)
            col = SUCCESS if val else BORDER
            fg  = BG if val else SUBTEXT
            b = tk.Button(status_frame, text=f"{'✓' if val else '○'} {label}",
                          font=FONT_SMALL, bg=col, fg=fg, relief="flat",
                          activebackground=col, activeforeground=fg, cursor="hand2",
                          padx=6, pady=2,
                          command=lambda pid=p["id"], k=key: self._toggle_prac_stage(pid, k))
            b.pack(side="left", padx=(0,6))

        right = tk.Frame(card, bg=card["bg"])
        right.pack(side="right")
        self._del_btn(right, lambda pid=p["id"]: self._del_prac(pid))

    def _toggle_prac_stage(self, pid, key):
        for p in self.data["practicals"]:
            if p["id"] == pid:
                p[key] = not p.get(key, False)
                # If all three stages done, mark overall done
                if p.get("performed") and p.get("writeup") and p.get("submitted"):
                    p["done"] = True
                else:
                    p["done"] = False
        save_data(self.data)
        self._refresh_practicals()

    def _add_prac(self):
        subj  = self.prac_subj.get().strip()
        num   = self.prac_num.get().strip()
        title = self.prac_title.get().strip()
        date  = self.prac_date.get().strip()
        if not subj or not title:
            messagebox.showwarning("Missing", "Subject and Title required.")
            return
        if date == "YYYY-MM-DD":
            date = ""
        self.data["practicals"].append({"id": str(uuid.uuid4()), "subject": subj,
                                         "num": num, "title": title, "date": date,
                                         "performed": False, "writeup": False,
                                         "submitted": False, "done": False})
        save_data(self.data)
        for e in (self.prac_subj, self.prac_num, self.prac_title, self.prac_date):
            e.delete(0, tk.END)
        self._refresh_practicals()

    def _del_prac(self, pid):
        self.data["practicals"] = [p for p in self.data["practicals"] if p["id"] != pid]
        save_data(self.data)
        self._refresh_practicals()

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _tab_header(self, tab, title, subtitle):
        h = tk.Frame(tab, bg=BG, padx=22, pady=16)
        h.pack(fill="x")
        tk.Label(h, text=title, font=FONT_TITLE, bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(h, text=subtitle, font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(anchor="w")
        tk.Frame(tab, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(0,12))

    def _entry(self, parent, width=22):
        e = tk.Entry(parent, font=FONT_BODY, bg=HOVER, fg=TEXT,
                     insertbackground=ACCENT, relief="flat",
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT, width=width)
        return e

    def _btn(self, parent, text, command, bg=BORDER, fg=TEXT, active=None, padx=12, pady=5):
        b = tk.Button(parent, text=text, command=command,
                      font=FONT_SMALL, bg=bg, fg=fg, relief="flat",
                      activebackground=active or HOVER, activeforeground=fg,
                      cursor="hand2", padx=padx, pady=pady)
        return b

    def _del_btn(self, parent, command):
        b = tk.Button(parent, text="✕", command=command,
                      font=FONT_SMALL, bg=PANEL, fg=ACCENT2, relief="flat",
                      activebackground=HOVER, activeforeground=ACCENT2,
                      cursor="hand2", padx=6, pady=2)
        b.pack(side="left", padx=4)

    def _style_combo(self, cb):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=HOVER, background=HOVER,
                        foreground=TEXT, arrowcolor=ACCENT,
                        bordercolor=BORDER, lightcolor=BORDER,
                        darkcolor=BORDER, selectbackground=BORDER,
                        selectforeground=TEXT)

    def _manual_save(self):
        save_data(self.data)
        messagebox.showinfo("Saved", "All data saved successfully.")

    def _refresh_all(self):
        self._refresh_tests()
        self._refresh_tasks()
        self._refresh_lists()
        self._refresh_assignments()
        self._refresh_practicals()


if __name__ == "__main__":
    app = PlannerApp()
    app.mainloop()

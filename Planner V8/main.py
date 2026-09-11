"""
COMMAND PLANNER — PySide6/QML Entry Point
Bridges Python backend data to the QML UI.
"""
import sys
import os
import json
import threading
import time

from PySide6.QtCore import (QObject, Property, Signal, Slot, QUrl, QTimer,
                             Qt, QCoreApplication, qInstallMessageHandler)
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from planner_backend import (
    load_data, save_data, backup_data, update_streak, send_notify,
    play_pomo_sound, nid, days_until, urgency_color, urgency_lbl,
    get_subject_color, set_subject_color, all_subjects, last_backup_label,
    get_heatmap_data, get_week_sessions, day_sessions, day_score,
    COLORS, COLORS_LIGHT, PRIORITY_ORDER, P_COLOR, P_BG,
    RECUR_OPTIONS, TAB_CFG, SUBJECT_PALETTE, HAS_SOUND,
)
from datetime import datetime, date, timedelta


class PlannerBridge(QObject):
    """Exposes all planner data and operations to QML."""

    dataChanged = Signal()
    toastRequested = Signal(str, str, str)    # message, color, icon
    pomoAlertRequested = Signal(str, int, str, int, str)  # sessionType, sessionNum, nextType, nextMins, taskLabel
    digestRequested = Signal()

    def __init__(self):
        super().__init__()
        self._data = load_data()
        self._current_theme = self._data.get("theme", "dark")
        update_streak(self._data)
        backup_data(self._data)
        save_data(self._data)

        # Pomodoro state
        self._pomo_running = False
        self._pomo_mode = "work"        # "work", "break", "long_break"
        self._pomo_seconds = 25 * 60
        self._pomo_elapsed = 0
        self._pomo_sessions = 0
        self._pomo_work_mins = 25
        self._pomo_short_mins = 5
        self._pomo_long_mins = 15
        self._pomo_task = "(no task selected)"
        self._pomo_stop_event = threading.Event()
        self._pomo_stop_event.set()
        self._pomo_thread = None
        self._goal_toast_date = ""

        # Auto-save timer
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.start(60000)

    # ══════════════════════════════════════════════════════════════════
    # THEME
    # ══════════════════════════════════════════════════════════════════
    themeChanged = Signal()

    @Property(str, notify=themeChanged)
    def currentTheme(self):
        return self._current_theme

    @Slot()
    def toggleTheme(self):
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self._data["theme"] = self._current_theme
        save_data(self._data)
        self.themeChanged.emit()

    @Slot(result=str)
    def getColors(self):
        c = COLORS_LIGHT if self._current_theme == "light" else COLORS
        return json.dumps(c)

    # ══════════════════════════════════════════════════════════════════
    # GENERIC DATA ACCESS
    # ══════════════════════════════════════════════════════════════════
    @Slot(result=str)
    def getTests(self):
        tests = sorted(self._data.get("tests", []),
                       key=lambda x: (x.get("date", ""), x.get("time", "")))
        for t in tests:
            d = days_until(t.get("date", ""))
            t["_days"] = d
            t["_urgency_color"] = urgency_color(d)
            t["_urgency_lbl"] = urgency_lbl(d)
            t["_subject_color"] = get_subject_color(self._data, t.get("subject", ""))
        return json.dumps(tests)

    @Slot(result=str)
    def getTasks(self):
        return json.dumps(self._data.get("tasks", []))

    @Slot(result=str)
    def getLists(self):
        return json.dumps(self._data.get("lists", []))

    @Slot(result=str)
    def getAssignments(self):
        assignments = self._data.get("assignments", [])
        for a in assignments:
            d = days_until(a.get("due", ""))
            a["_days"] = d
            a["_urgency_color"] = urgency_color(d)
            a["_urgency_lbl"] = urgency_lbl(d)
            a["_subject_color"] = get_subject_color(self._data, a.get("subject", ""))
        return json.dumps(assignments)

    @Slot(result=str)
    def getPracticals(self):
        practicals = self._data.get("practicals", [])
        for p in practicals:
            p["_subject_color"] = get_subject_color(self._data, p.get("subject", ""))
        return json.dumps(practicals)

    @Slot(result=str)
    def getSyllabus(self):
        syllabus = self._data.get("syllabus", [])
        for s in syllabus:
            s["_subject_color"] = get_subject_color(self._data, s.get("name", ""))
        return json.dumps(syllabus)

    @Slot(result=str)
    def getNotes(self):
        return json.dumps(sorted(self._data.get("notes", []),
                                 key=lambda n: n.get("updated", ""), reverse=True))

    @Slot(result=str)
    def getPomodoroLog(self):
        return json.dumps(self._data.get("pomodoro_log", []))

    @Slot(result=int)
    def getStreak(self):
        return self._data.get("streak", {}).get("count", 0)

    @Slot(result=int)
    def getDailyGoal(self):
        return self._data.get("daily_goal", 6)

    @Slot(result=str)
    def getBackupLabel(self):
        return last_backup_label()

    @Slot(result=str)
    def getSubjectColor(self, subject):
        return get_subject_color(self._data, subject)

    @Slot(result=str)
    def getAllSubjects(self):
        return json.dumps(all_subjects(self._data))

    @Slot(result=str)
    def getSubjectPalette(self):
        return json.dumps(SUBJECT_PALETTE)

    @Slot(result=str)
    def getPriorityOrder(self):
        return json.dumps(PRIORITY_ORDER)

    @Slot(result=str)
    def getTabConfig(self):
        return json.dumps([{"icon": i, "name": n, "color": c} for i, n, c in TAB_CFG])

    @Slot(result=str)
    def getHeatmapData(self):
        return json.dumps(get_heatmap_data(self._data))

    # ══════════════════════════════════════════════════════════════════
    # OVERVIEW DATA
    # ══════════════════════════════════════════════════════════════════
    @Slot(result=str)
    def getOverviewData(self):
        d = self._data
        tests_up = len([t for t in d["tests"] if (days_until(t.get("date", "")) or -1) >= 0])
        tasks_p = len([t for t in d["tasks"] if not t.get("done")])
        asgn_p = len([a for a in d["assignments"] if not a.get("submitted")])
        prac_p = len([p for p in d["practicals"] if not p.get("done")])
        subj_c = len(d.get("syllabus", []))
        pomo_today = sum(1 for p in d.get("pomodoro_log", [])
                         if p.get("date", "") == date.today().isoformat())
        streak = d["streak"].get("count", 0)
        hour = datetime.now().hour
        greeting = "GOOD MORNING" if hour < 12 else ("GOOD AFTERNOON" if hour < 18 else "GOOD EVENING")

        # Upcoming tests
        upcoming_tests = sorted(
            [t for t in d["tests"] if (days_until(t.get("date", "")) or -1) >= 0],
            key=lambda x: x.get("date", ""))[:4]
        for t in upcoming_tests:
            dd = days_until(t.get("date", ""))
            t["_urgency_color"] = urgency_color(dd)
            t["_urgency_lbl"] = urgency_lbl(dd)
            t["_subject_color"] = get_subject_color(d, t.get("subject", ""))

        # Top tasks
        top_tasks = sorted(
            [t for t in d["tasks"] if not t.get("done")],
            key=lambda t: PRIORITY_ORDER.index(t.get("priority", "Someday")))[:5]
        for t in top_tasks:
            t["_priority_color"] = P_COLOR.get(t.get("priority", "Someday"), COLORS["subtext"])

        # Assignments due
        pending_asgns = sorted(
            [a for a in d["assignments"] if not a.get("submitted")],
            key=lambda x: x.get("due", "9999"))[:4]
        for a in pending_asgns:
            dd = days_until(a.get("due", ""))
            a["_urgency_color"] = urgency_color(dd)
            a["_urgency_lbl"] = urgency_lbl(dd)
            a["_subject_color"] = get_subject_color(d, a.get("subject", ""))

        # Practicals
        pending_pracs = [p for p in d["practicals"] if not p.get("done")][:4]
        for p in pending_pracs:
            p["_subject_color"] = get_subject_color(d, p.get("subject", ""))

        # Syllabus
        syllabus_items = []
        for subj in d.get("syllabus", [])[:4]:
            topics = subj.get("topics", [])
            total = len(topics)
            done = sum(1 for t in topics if t.get("done"))
            pct = int((done / total) * 100) if total else 0
            syllabus_items.append({
                "name": subj.get("name", ""),
                "done": done,
                "total": total,
                "pct": pct,
                "color": get_subject_color(d, subj.get("name", ""))
            })

        # Pending today/tomorrow
        today_iso = date.today().isoformat()
        pending_items = []
        for t in d["tests"]:
            dd = days_until(t.get("date", ""))
            if dd is not None and 0 <= dd <= 1:
                pending_items.append({
                    "type": "\u25c8 TEST", "name": t.get("subject", ""),
                    "color": urgency_color(dd), "label": urgency_lbl(dd)
                })
        for t in d["tasks"]:
            if not t.get("done"):
                due = t.get("due", "")
                dd = days_until(due) if due else None
                if dd is not None and dd <= 0:
                    pending_items.append({
                        "type": "\u25a3 TASK", "name": t.get("text", "")[:40],
                        "color": urgency_color(dd), "label": urgency_lbl(dd)
                    })
        for a in d["assignments"]:
            if not a.get("submitted"):
                dd = days_until(a.get("due", ""))
                if dd is not None and dd <= 1:
                    pending_items.append({
                        "type": "\u25e7 ASGN",
                        "name": f"[{a.get('subject', '')}] {a.get('title', '')[:30]}",
                        "color": urgency_color(dd), "label": urgency_lbl(dd)
                    })

        overdue = [x for x in pending_items if x["label"] == "PAST"]
        today_due = [x for x in pending_items if x["label"] == "TODAY"]
        tomorrow_due = [x for x in pending_items if x["label"] == "TOMORROW"]

        # Week sessions for spider chart
        this_week = get_week_sessions(d, 0)
        last_week = get_week_sessions(d, 1)

        # Motivational quote
        lw_score = sum(day_score(d, (date.today() - timedelta(days=i)).isoformat()) for i in range(1, 8)) // 7
        mot = ""
        if streak > 0:
            mot = f"🔥 {streak} day streak — keep it going this week."
        elif lw_score >= 80:
            mot = "Outstanding last week. Replicate it."
        elif lw_score >= 60:
            mot = "Solid week. Push for Excellent this time."
        else:
            mot = "New week, clean slate. Make it count."

        return json.dumps({
            "greeting": greeting,
            "motivational": mot,
            "dateStr": datetime.now().strftime("%A, %d %B %Y"),
            "streak": streak,
            "stats": {
                "tests_up": tests_up, "tasks_p": tasks_p, "asgn_p": asgn_p,
                "prac_p": prac_p, "subj_c": subj_c, "pomo_today": pomo_today,
            },
            "upcoming_tests": upcoming_tests,
            "top_tasks": top_tasks,
            "pending_asgns": pending_asgns,
            "pending_pracs": pending_pracs,
            "syllabus_items": syllabus_items,
            "overdue": overdue,
            "today_due": today_due,
            "tomorrow_due": tomorrow_due,
            "this_week": this_week,
            "last_week": last_week,
            "daily_goal": d.get("daily_goal", 6),
        })

    # ══════════════════════════════════════════════════════════════════
    # PRODUCTIVITY DATA
    # ══════════════════════════════════════════════════════════════════
    @Slot(result=str)
    def getProductivityData(self):
        d = self._data
        today = date.today()
        goal = max(d.get("daily_goal", 6), 1)
        yesterday = (today - timedelta(days=1)).isoformat()
        today_iso = today.isoformat()
        week_start = today - timedelta(days=today.weekday())
        week_days = [(week_start + timedelta(days=i)).isoformat() for i in range(7)]
        month_start = today.replace(day=1)
        month_days = [(month_start + timedelta(days=i)).isoformat()
                      for i in range((today - month_start).days + 1)]

        def _period_score(days_list):
            scores = [day_score(d, di) for di in days_list if day_sessions(d, di) > 0]
            return int(sum(scores) / len(scores)) if scores else 0

        tw = get_week_sessions(d, 0)
        lw = get_week_sessions(d, 1)

        # Best/worst day
        best_idx = tw.index(max(tw))
        worst_active = [v for v in tw if v > 0]
        worst_val = min(worst_active) if worst_active else 0
        worst_idx = tw.index(worst_val) if worst_active else 0
        goal_hit = sum(1 for v in tw if v >= goal)
        log = d.get("pomodoro_log", [])
        total_focus_m = sum(p.get("duration_min", 0) for p in log
                           if p.get("date", "") in week_days and p.get("type", "") == "work")

        # Hour distribution
        hour_counts = [0] * 24
        for p in log:
            if p.get("type", "") == "work":
                try:
                    hour_counts[int(p.get("time", "00:00").split(":")[0])] += 1
                except Exception:
                    pass

        # 30-day scores
        last30 = [(today - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
        scores30 = [day_score(d, di) for di in last30]

        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        return json.dumps({
            "goal": goal,
            "streak": d.get("streak", {}).get("count", 0),
            "score_today": day_score(d, today_iso),
            "score_yesterday": day_score(d, yesterday),
            "score_week": _period_score(week_days),
            "score_month": _period_score(month_days),
            "sessions_today": day_sessions(d, today_iso),
            "sessions_yesterday": day_sessions(d, yesterday),
            "sessions_week": sum(tw),
            "sessions_month": sum(day_sessions(d, di) for di in month_days),
            "today_str": today.strftime("%d %b"),
            "yesterday_str": (today - timedelta(days=1)).strftime("%d %b"),
            "week_str": f"{week_start.strftime('%d %b')} \u2013 now",
            "month_str": today.strftime("%B %Y"),
            "this_week": tw,
            "last_week": lw,
            "day_labels": day_labels,
            "best_day": day_labels[best_idx],
            "goal_hit": goal_hit,
            "total_focus_min": total_focus_m,
            "vs_last_week": sum(tw) - sum(lw),
            "hour_counts": hour_counts[6:24],  # 6am-11pm
            "hour_labels": list(range(6, 24)),
            "scores_30": scores30,
            "dates_30": last30,
        })

    # ══════════════════════════════════════════════════════════════════
    # TAB COUNTS (sidebar badges)
    # ══════════════════════════════════════════════════════════════════
    @Slot(result=str)
    def getTabCounts(self):
        d = self._data
        return json.dumps({
            "TESTS": len([t for t in d["tests"] if (days_until(t.get("date", "")) or -1) >= 0]),
            "TASKS": len([t for t in d["tasks"] if not t.get("done")]),
            "LISTS": len(d["lists"]),
            "ASSIGNMENTS": len([a for a in d["assignments"] if not a.get("submitted")]),
            "PRACTICALS": len([p for p in d["practicals"] if not p.get("done")]),
            "SYLLABUS": len(d.get("syllabus", [])),
            "NOTES": len(d.get("notes", [])),
        })

    # ══════════════════════════════════════════════════════════════════
    # TESTS CRUD
    # ══════════════════════════════════════════════════════════════════
    @Slot(str, str, str, str)
    def addTest(self, subject, dt, tm, note):
        self._data["tests"].append({
            "id": nid(), "subject": subject, "date": dt, "time": tm, "note": note
        })
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str)
    def deleteTest(self, tid):
        self._data["tests"] = [t for t in self._data["tests"] if t["id"] != tid]
        save_data(self._data)
        self.dataChanged.emit()

    # ══════════════════════════════════════════════════════════════════
    # TASKS CRUD
    # ══════════════════════════════════════════════════════════════════
    @Slot(str, str, str, str)
    def addTask(self, text, priority, due, recur):
        self._data["tasks"].append({
            "id": nid(), "text": text, "priority": priority,
            "due": due, "done": False, "recur": recur, "spawned": False,
            "added": datetime.now().isoformat()
        })
        save_data(self._data)
        self.dataChanged.emit()
        self.toastRequested.emit(f"Task added \u2014 {priority}",
                                 P_COLOR.get(priority, COLORS["cyan"]), "\u25a3")

    @Slot(str, bool)
    def toggleTask(self, tid, done):
        for t in self._data["tasks"]:
            if t["id"] == tid:
                t["done"] = done
        # Spawn recurring
        for t in self._data["tasks"]:
            if t.get("done") and t.get("recur", "None") != "None" and not t.get("spawned"):
                self._spawn_recur_task(t)
                t["spawned"] = True
        update_streak(self._data)
        save_data(self._data)
        self.dataChanged.emit()
        if done:
            self.toastRequested.emit("Task complete! Keep going.", COLORS["green"], "\u2713")

    @Slot(str, str)
    def changeTaskPriority(self, tid, priority):
        for t in self._data["tasks"]:
            if t["id"] == tid:
                t["priority"] = priority
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str)
    def deleteTask(self, tid):
        self._data["tasks"] = [t for t in self._data["tasks"] if t["id"] != tid]
        save_data(self._data)
        self.dataChanged.emit()

    def _spawn_recur_task(self, t):
        recur = t.get("recur", "None")
        if recur == "None":
            return
        delta = {"Daily": 1, "Weekly": 7, "Monthly": 30}.get(recur, 0)
        if not delta:
            return
        new_due = (date.today() + timedelta(days=delta)).isoformat()
        new_t = {k: v for k, v in t.items()}
        new_t["id"] = nid()
        new_t["done"] = False
        new_t["due"] = new_due
        new_t["added"] = datetime.now().isoformat()
        new_t["spawned"] = False
        self._data["tasks"].append(new_t)

    # ══════════════════════════════════════════════════════════════════
    # LISTS CRUD
    # ══════════════════════════════════════════════════════════════════
    @Slot(str)
    def addList(self, name):
        self._data["lists"].append({"id": nid(), "name": name, "items": []})
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str)
    def deleteList(self, lid):
        self._data["lists"] = [l for l in self._data["lists"] if l["id"] != lid]
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str, str)
    def addListItem(self, lid, text):
        for l in self._data["lists"]:
            if l["id"] == lid:
                l["items"].append({"id": nid(), "text": text, "done": False})
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str, str)
    def deleteListItem(self, lid, iid):
        for l in self._data["lists"]:
            if l["id"] == lid:
                l["items"] = [i for i in l["items"] if i["id"] != iid]
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str, str, bool)
    def toggleListItem(self, lid, iid, done):
        for l in self._data["lists"]:
            if l["id"] == lid:
                for item in l["items"]:
                    if item["id"] == iid:
                        item["done"] = done
        save_data(self._data)
        self.dataChanged.emit()

    # ══════════════════════════════════════════════════════════════════
    # ASSIGNMENTS CRUD
    # ══════════════════════════════════════════════════════════════════
    @Slot(str, str, str, str)
    def addAssignment(self, subject, title, due, marks):
        self._data["assignments"].append({
            "id": nid(), "subject": subject, "title": title,
            "due": due, "marks": marks, "submitted": False
        })
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str)
    def submitAssignment(self, aid):
        for a in self._data["assignments"]:
            if a["id"] == aid:
                a["submitted"] = True
        save_data(self._data)
        self.dataChanged.emit()
        self.toastRequested.emit("Assignment submitted!", COLORS["green"], "\u25e7")

    @Slot(str)
    def deleteAssignment(self, aid):
        self._data["assignments"] = [a for a in self._data["assignments"] if a["id"] != aid]
        save_data(self._data)
        self.dataChanged.emit()

    # ══════════════════════════════════════════════════════════════════
    # PRACTICALS CRUD
    # ══════════════════════════════════════════════════════════════════
    @Slot(str, str, str, str)
    def addPractical(self, subject, num, title, dt):
        self._data["practicals"].append({
            "id": nid(), "subject": subject, "num": num,
            "title": title, "date": dt,
            "performed": False, "writeup": False, "submitted": False, "done": False
        })
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str, str)
    def togglePractical(self, pid, key):
        for p in self._data["practicals"]:
            if p["id"] == pid:
                p[key] = not p.get(key, False)
                p["done"] = p.get("performed") and p.get("writeup") and p.get("submitted")
                if p["done"]:
                    self.toastRequested.emit("Practical complete!", COLORS["green"], "\u25e9")
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str)
    def deletePractical(self, pid):
        self._data["practicals"] = [p for p in self._data["practicals"] if p["id"] != pid]
        save_data(self._data)
        self.dataChanged.emit()

    # ══════════════════════════════════════════════════════════════════
    # SYLLABUS CRUD
    # ══════════════════════════════════════════════════════════════════
    @Slot(str)
    def addSubject(self, name):
        self._data["syllabus"].append({"id": nid(), "name": name, "topics": []})
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str)
    def deleteSubject(self, sid):
        self._data["syllabus"] = [s for s in self._data["syllabus"] if s["id"] != sid]
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str, str)
    def addTopic(self, sid, name):
        for s in self._data["syllabus"]:
            if s["id"] == sid:
                s["topics"].append({"id": nid(), "name": name, "done": False})
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str, str)
    def deleteTopic(self, sid, tid):
        for s in self._data["syllabus"]:
            if s["id"] == sid:
                s["topics"] = [t for t in s["topics"] if t["id"] != tid]
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str, str, bool)
    def toggleTopic(self, sid, tid, done):
        for s in self._data["syllabus"]:
            if s["id"] == sid:
                for t in s["topics"]:
                    if t["id"] == tid:
                        t["done"] = done
        save_data(self._data)
        self.dataChanged.emit()

    @Slot(str, str)
    def setSubjectColor(self, subject, color):
        set_subject_color(self._data, subject, color)
        self.dataChanged.emit()

    # ══════════════════════════════════════════════════════════════════
    # NOTES CRUD
    # ══════════════════════════════════════════════════════════════════
    @Slot(result=str)
    def newNote(self):
        note = {
            "id": nid(), "title": "New Note",
            "subject": "General", "body": "",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }
        self._data["notes"].append(note)
        save_data(self._data)
        self.dataChanged.emit()
        return note["id"]

    @Slot(str, str, str, str)
    def saveNote(self, note_id, title, subject, body):
        for note in self._data["notes"]:
            if note["id"] == note_id:
                note["title"] = title or "Untitled"
                note["subject"] = subject or "General"
                note["body"] = body
                note["updated"] = datetime.now().isoformat()
        save_data(self._data)
        self.dataChanged.emit()
        self.toastRequested.emit("Note saved.", COLORS["cyan"], "\u270e")

    @Slot(str)
    def deleteNote(self, note_id):
        self._data["notes"] = [n for n in self._data["notes"] if n["id"] != note_id]
        save_data(self._data)
        self.dataChanged.emit()

    # ══════════════════════════════════════════════════════════════════
    # POMODORO
    # ══════════════════════════════════════════════════════════════════
    pomoStateChanged = Signal()

    @Slot(result=str)
    def getPomoState(self):
        total = self._pomo_seconds
        remaining = max(0, total - self._pomo_elapsed)
        m, s = divmod(remaining, 60)
        pomo_today = sum(1 for p in self._data.get("pomodoro_log", [])
                         if p.get("date", "") == date.today().isoformat()
                         and p.get("type", "") == "work")
        return json.dumps({
            "running": self._pomo_running,
            "mode": self._pomo_mode,
            "timeStr": f"{m:02d}:{s:02d}",
            "progress": self._pomo_elapsed / total if total else 0,
            "sessions": self._pomo_sessions,
            "todayCount": pomo_today,
        })

    @Slot()
    def pomoStartStop(self):
        if self._pomo_running:
            self._pomo_stop_event.set()
            self._pomo_running = False
            self.pomoStateChanged.emit()
        else:
            self._pomo_running = True
            self._pomo_stop_event.clear()
            self._pomo_thread = threading.Thread(target=self._pomo_tick_loop, daemon=True)
            self._pomo_thread.start()
            self.pomoStateChanged.emit()

    @Slot()
    def pomoReset(self):
        self._pomo_stop_event.set()
        self._pomo_running = False
        self._pomo_mode = "work"
        self._pomo_elapsed = 0
        self._pomo_seconds = self._pomo_work_mins * 60
        self.pomoStateChanged.emit()

    @Slot(int, int, int)
    def pomoApplySettings(self, work, short_break, long_break):
        self._pomo_work_mins = max(1, work)
        self._pomo_short_mins = max(1, short_break)
        self._pomo_long_mins = max(1, long_break)
        self.pomoReset()

    @Slot(str)
    def pomoSetTask(self, task):
        self._pomo_task = task

    @Slot(result=str)
    def pomoGetTasks(self):
        tasks = ["(no task selected)"] + [t.get("text", "")
                 for t in self._data["tasks"] if not t.get("done")]
        return json.dumps(tasks)

    @Slot(int)
    def setDailyGoal(self, val):
        if val < 1:
            return
        self._data["daily_goal"] = val
        save_data(self._data)
        self.dataChanged.emit()

    def _pomo_tick_loop(self):
        total = self._pomo_seconds
        while not self._pomo_stop_event.is_set() and self._pomo_elapsed < total:
            if self._pomo_stop_event.wait(timeout=1.0):
                return
            self._pomo_elapsed += 1
            self.pomoStateChanged.emit()
        if not self._pomo_stop_event.is_set():
            QTimer.singleShot(0, self._pomo_session_done)

    def _pomo_session_done(self):
        self._pomo_stop_event.set()
        self._pomo_running = False
        session_type = self._pomo_mode

        self._data["pomodoro_log"].append({
            "id": nid(), "date": date.today().isoformat(),
            "time": datetime.now().strftime("%H:%M"),
            "type": session_type,
            "task": self._pomo_task,
            "duration_min": (self._pomo_work_mins if session_type == "work" else
                             self._pomo_long_mins if session_type == "long_break" else
                             self._pomo_short_mins)
        })
        save_data(self._data)

        if session_type == "work":
            self._pomo_sessions += 1
            if self._pomo_sessions % 4 == 0:
                next_type = "long_break"
                next_mins = self._pomo_long_mins
                self._pomo_mode = "long_break"
                self._pomo_seconds = self._pomo_long_mins * 60
            else:
                next_type = "break"
                next_mins = self._pomo_short_mins
                self._pomo_mode = "break"
                self._pomo_seconds = self._pomo_short_mins * 60
            play_pomo_sound()
            self.pomoAlertRequested.emit("work", self._pomo_sessions,
                                         next_type, next_mins, self._pomo_task)
        else:
            next_mins = self._pomo_work_mins
            play_pomo_sound()
            self.pomoAlertRequested.emit(session_type, self._pomo_sessions,
                                         "work", next_mins, self._pomo_task)
            self._pomo_mode = "work"
            self._pomo_seconds = self._pomo_work_mins * 60

        self._pomo_elapsed = 0
        self.pomoStateChanged.emit()
        self.dataChanged.emit()

        # Check daily goal
        goal = self._data.get("daily_goal", 6)
        today_iso = date.today().isoformat()
        today_count = day_sessions(self._data, today_iso)
        if today_count == goal and self._goal_toast_date != today_iso:
            self._goal_toast_date = today_iso
            self.toastRequested.emit(
                f"\U0001f3af Daily goal reached! {goal} sessions today.",
                COLORS["gold"], "\u2605")

    # ══════════════════════════════════════════════════════════════════
    # SAVE / BACKUP
    # ══════════════════════════════════════════════════════════════════
    @Slot()
    def manualSave(self):
        save_data(self._data)
        self.toastRequested.emit("All data saved successfully.", COLORS["green"], "\U0001f4be")

    @Slot(result=str)
    def doBackup(self):
        dst = backup_data(self._data)
        return os.path.basename(dst)

    def _auto_save(self):
        save_data(self._data)

    @Slot()
    def saveGeometry(self):
        pass  # Will be handled by QML


# ══════════════════════════════════════════════════════════════════════════
# APPLICATION ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════

def qt_message_handler(mode, context, message):
    print(f"[{mode}] {message}", file=sys.stderr)

def main():
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
    qInstallMessageHandler(qt_message_handler)
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Command Planner")
    app.setOrganizationName("PrinceBlue")

    engine = QQmlApplicationEngine()

    bridge = PlannerBridge()
    app.bridge = bridge  # Prevent garbage collection
    engine.rootContext().setContextProperty("bridge", bridge)

    qml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qml", "Main.qml")
    engine.load(QUrl.fromLocalFile(qml_file))

    if not engine.rootObjects():
        print("ERROR: Failed to load QML file:", qml_file)
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

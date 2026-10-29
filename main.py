import sys, tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import data_manager, workout_session

BG, CARD, ACC, TXT = "#F0F8FF", "#E0F2FE", "#0284C7", "#0C4A6E"

def apply_theme(root):
    root.configure(bg=BG)
    s = ttk.Style(); s.theme_use("clam")
    s.configure("TFrame", background=BG); s.configure("TLabelframe", background=BG, foreground=ACC)
    s.configure("TLabelframe.Label", background=BG, foreground=ACC, font=("Malgun Gothic", 10, "bold"))
    s.configure("TLabel", background=BG, foreground=TXT, font=("Malgun Gothic", 9))
    s.configure("Sky.TButton", background="#BAE6FD", foreground=TXT, font=("Malgun Gothic", 9, "bold"))
    s.map("Sky.TButton", background=[("active", "#7DD3FC")])
    s.configure("Main.TButton", background="#38BDF8", foreground="#FFFFFF", font=("Malgun Gothic", 10, "bold"))
    s.map("Main.TButton", background=[("active", ACC)])
    s.configure("Treeview.Heading", background="#BAE6FD", foreground=TXT, font=("Malgun Gothic", 9, "bold"))

class RoutineEditorDialog:
    def __init__(self, parent, data, on_save):
        self.data, self.on_save = data, on_save
        self.win = tk.Toplevel(parent); self.win.title("루틴 설정 및 수정"); self.win.geometry("450x390")
        self.win.configure(bg=BG); self.win.grab_set()
        top_f = ttk.Frame(self.win, padding=5); top_f.pack(fill=tk.X)
        ttk.Label(top_f, text="루틴:").pack(side=tk.LEFT, padx=3)
        self.r_combo = ttk.Combobox(top_f, values=[r["name"] for r in data["routines"]], state="readonly", width=16)
        r_len = len(data["routines"])
        if r_len > 0: self.r_combo.current(min(data.get("active_routine_idx", 0), r_len - 1))
        self.r_combo.pack(side=tk.LEFT, padx=3); self.r_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())
        ttk.Button(top_f, text="+새루틴", width=7, style="Sky.TButton", command=self._add_routine).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_f, text="삭제", width=5, style="Sky.TButton", command=self._del_routine).pack(side=tk.LEFT, padx=2)
        self.lb = tk.Listbox(self.win, font=("Malgun Gothic", 9), selectbackground="#BAE6FD", selectforeground=TXT)
        self.lb.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        bf = ttk.Frame(self.win, padding=5); bf.pack(fill=tk.X)
        ttk.Button(bf, text="운동 추가", style="Sky.TButton", command=self._add_ex).pack(side=tk.LEFT, padx=3)
        ttk.Button(bf, text="선택 삭제", style="Sky.TButton", command=self._del_ex).pack(side=tk.LEFT, padx=3)
        ttk.Button(bf, text="저장 및 닫기", style="Main.TButton", command=self._save_and_close).pack(side=tk.RIGHT, padx=3)
        self._refresh()

    def _cur_r(self):
        return self.data["routines"][max(0, self.r_combo.current())]

    def _refresh(self):
        self.lb.delete(0, tk.END)
        for ex in self._cur_r().get("exercises", []):
            r = f" × {ex['reps']}" if ex.get("reps") else ""
            self.lb.insert(tk.END, f"{ex['name']} | {ex['sets']}세트{r} | 휴식 {ex.get('rest', 60)}초")

    def _add_routine(self):
        name = simpledialog.askstring("새 루틴", "루틴 이름 입력:", parent=self.win)
        if name:
            self.data["routines"].append({"name": name, "exercises": []})
            self.r_combo["values"] = [r["name"] for r in self.data["routines"]]
            self.r_combo.current(len(self.data["routines"]) - 1); self._refresh()

    def _del_routine(self):
        if len(self.data["routines"]) <= 1:
            return messagebox.showwarning("경고", "최소 1개 루틴이 필요합니다.", parent=self.win)
        del self.data["routines"][self.r_combo.current()]
        self.r_combo["values"] = [r["name"] for r in self.data["routines"]]
        self.r_combo.current(0); self._refresh()

    def _add_ex(self):
        name = simpledialog.askstring("운동 추가", "운동 이름:", parent=self.win)
        if not name: return
        s = simpledialog.askinteger("운동 추가", "세트 수:", initialvalue=3, minvalue=1, parent=self.win) or 3
        reps = simpledialog.askstring("운동 추가", "세트당 목표(예: 12회, 45초):", initialvalue="12회", parent=self.win) or "12회"
        r = simpledialog.askinteger("운동 추가", "휴식 시간(초):", initialvalue=60, minvalue=10, parent=self.win) or 60
        self._cur_r().setdefault("exercises", []).append({"name": name, "sets": s, "reps": reps, "rest": r}); self._refresh()

    def _del_ex(self):
        sel = self.lb.curselection()
        if sel: del self._cur_r()["exercises"][sel[0]]; self._refresh()

    def _save_and_close(self):
        self.data["active_routine_idx"] = max(0, self.r_combo.current())
        data_manager.save_data(self.data); self.on_save(); self.win.destroy()

class WorkoutApp:
    def __init__(self, root, start_direct=False):
        self.root = root; self.root.title("운동 기록 및 알림"); self.root.geometry("490x560")
        apply_theme(self.root)
        self.data = data_manager.load_data()
        self._build_ui(); self._refresh_status()
        if start_direct: self._start_workout()

    def _build_ui(self):
        self.banner = tk.Frame(self.root, bg=CARD, padx=10, pady=10); self.banner.pack(fill=tk.X, padx=12, pady=8)
        self.days_lbl = tk.Label(self.banner, text="", font=("Malgun Gothic", 12, "bold"), bg=CARD, fg=ACC)
        self.days_lbl.pack()
        self.sub_lbl = tk.Label(self.banner, text="", font=("Malgun Gothic", 9), bg=CARD, fg=TXT); self.sub_lbl.pack(pady=2)

        rf = ttk.LabelFrame(self.root, text="🏋️ 오늘 할 운동 루틴"); rf.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)
        sel_f = ttk.Frame(rf); sel_f.pack(fill=tk.X, padx=8, pady=5)
        ttk.Label(sel_f, text="선택 루틴:").pack(side=tk.LEFT)
        self.r_combo = ttk.Combobox(sel_f, state="readonly"); self.r_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.r_combo.bind("<<ComboboxSelected>>", self._on_routine_selected)

        cols = [("name", "운동명", 160), ("sets", "세트수", 65), ("reps", "세트당 목표", 85), ("rest", "휴식(초)", 65)]
        self.ex_tree = ttk.Treeview(rf, columns=[c[0] for c in cols], show="headings", height=6)
        for c, t, w in cols:
            self.ex_tree.heading(c, text=t); self.ex_tree.column(c, width=w, anchor="center")
        self.ex_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=5)

        ttk.Button(self.root, text="🔥 오늘 운동 시작하기", style="Main.TButton", command=self._start_workout).pack(fill=tk.X, padx=12, pady=6)
        bf = ttk.Frame(self.root); bf.pack(fill=tk.X, padx=12, pady=6)
        ttk.Button(bf, text="⚙️ 루틴 설정", style="Sky.TButton", command=lambda: RoutineEditorDialog(self.root, self.data, self._refresh_status)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(bf, text="📅 기록 보기", style="Sky.TButton", command=self._open_history).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(bf, text="⏰ 알림 설정", style="Sky.TButton", command=self._open_reminder).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    def _refresh_status(self):
        self.data = data_manager.load_data()
        days = data_manager.get_days_since_last_workout(self.data)
        msgs = {None: ("📢 아직 기록된 운동이 없습니다!", "오늘 첫 운동을 시작해보세요."),
                0: ("🎉 오늘 운동을 이미 완료했습니다!", "수고하셨습니다. 충분한 휴식을 취하세요.")}
        t, sub = msgs.get(days, (f"🔥 마지막 운동 후 {days}일 지났습니다!", "오늘은 득근하는 날! 지금 시작하세요."))
        self.days_lbl.config(text=t); self.sub_lbl.config(text=sub)
        routines = self.data.get("routines", [])
        self.r_combo["values"] = [r["name"] for r in routines]
        self.r_combo.current(min(self.data.get("active_routine_idx", 0), max(0, len(routines) - 1)))
        self._update_ex_list()

    def _on_routine_selected(self, event=None):
        self.data["active_routine_idx"] = self.r_combo.current()
        data_manager.save_data(self.data); self._update_ex_list()

    def _update_ex_list(self):
        self.ex_tree.delete(*self.ex_tree.get_children())
        idx = self.r_combo.current()
        if 0 <= idx < len(self.data.get("routines", [])):
            for ex in self.data["routines"][idx].get("exercises", []):
                self.ex_tree.insert("", "end", values=(ex["name"], f"{ex['sets']}세트", ex.get("reps", "-"), f"{ex.get('rest', 60)}초"))

    def _start_workout(self):
        idx = self.r_combo.current()
        if 0 <= idx < len(self.data["routines"]):
            workout_session.WorkoutSessionWindow(self.root, self.data["routines"][idx], self._on_workout_finished)

    def _on_workout_finished(self, r_name, comp, total, dur):
        data_manager.save_workout_record(self.data, r_name, comp, total, dur)
        self._refresh_status(); m, s = divmod(dur, 60)
        if messagebox.askyesno("운동 완료", f"기록 저장 완료 ({comp}/{total}세트, {m}분 {s}초)\n다음 운동 알림을 재설정하시겠습니까?"):
            self._open_reminder()

    def _open_history(self):
        win = tk.Toplevel(self.root); win.title("운동 기록 내역"); win.geometry("450x300"); win.configure(bg=BG)
        tree = ttk.Treeview(win, columns=("date", "routine", "sets", "dur"), show="headings", height=10)
        for c, t, w in [("date", "날짜", 90), ("routine", "루틴", 130), ("sets", "세트수", 80), ("dur", "소요시간", 90)]:
            tree.heading(c, text=t); tree.column(c, width=w, anchor="center")
        for h in reversed(self.data.get("history", [])):
            m, s = divmod(h.get("duration_sec", 0), 60)
            tree.insert("", "end", values=(h.get("date", "-"), h.get("routine", "-"), f"{h.get('completed_sets',0)}/{h.get('total_sets',0)}", f"{m}분 {s}초"))
        tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _open_reminder(self):
        win = tk.Toplevel(self.root); win.title("운동 알림 설정"); win.geometry("360x240"); win.configure(bg=BG)
        ttk.Label(win, text="🔔 Windows 작업 스케줄러 운동 알림", font=("Malgun Gothic", 10, "bold")).pack(pady=8)
        f1 = ttk.Frame(win); f1.pack(pady=3)
        ttk.Label(f1, text="알림 시간 (HH:MM):").pack(side=tk.LEFT, padx=5)
        t_var = tk.StringVar(value=self.data.get("reminder_time", "20:00"))
        ttk.Entry(f1, textvariable=t_var, width=10).pack(side=tk.LEFT)

        f2 = ttk.Frame(win); f2.pack(pady=3)
        ttk.Label(f2, text="반복 주기:").pack(side=tk.LEFT, padx=5)
        opts = ["1일마다 (매일)", "2일마다 (격일)", "3일마다", "4일마다", "5일마다", "7일마다 (주 1회)"]
        c_days = self.data.get("reminder_interval", 1)
        c_str = f"{c_days}일마다 (격일)" if c_days == 2 else (f"{c_days}일마다 (매일)" if c_days == 1 else f"{c_days}일마다")
        i_var = tk.StringVar(value=c_str if c_str in opts else opts[0])
        ttk.Combobox(f2, textvariable=i_var, values=opts, state="readonly", width=14).pack(side=tk.LEFT)

        s_desc = f"{self.data.get('reminder_interval', 1)}일마다 {self.data.get('reminder_time', '20:00')}"
        s_lbl = ttk.Label(win, text=f"현재: 등록됨 ({s_desc})" if data_manager.is_task_scheduled() else "현재 상태: 미등록")
        s_lbl.pack(pady=5)

        def apply():
            days = int(i_var.get().split("일")[0])
            ok, msg = data_manager.schedule_task(t_var.get(), days)
            self.data["reminder_time"], self.data["reminder_interval"] = t_var.get(), days
            data_manager.save_data(self.data)
            messagebox.showinfo("알림 설정", "스케줄러에 등록되었습니다!" if ok else f"등록 실패:\n{msg}", parent=win)
            s_lbl.config(text=f"현재: 등록됨 ({days}일마다 {t_var.get()})" if data_manager.is_task_scheduled() else "현재 상태: 미등록")
        def cancel():
            data_manager.delete_task(); messagebox.showinfo("알림 설정", "알림이 해제되었습니다.", parent=win)
            s_lbl.config(text="현재 상태: 미등록")
        bf = ttk.Frame(win); bf.pack(pady=8)
        ttk.Button(bf, text="스케줄러 등록", style="Main.TButton", command=apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="알림 해제", style="Sky.TButton", command=cancel).pack(side=tk.LEFT, padx=5)

def handle_notification():
    root = tk.Tk(); root.withdraw()
    if messagebox.askyesno("🔔 운동 알림", "운동할 시간입니다!\n지금 시작하시겠습니까?"):
        root.deiconify(); WorkoutApp(root, start_direct=True); root.mainloop()
    else: root.destroy(); sys.exit(0)

if __name__ == "__main__":
    if "--notify" in sys.argv: handle_notification()
    else: root = tk.Tk(); WorkoutApp(root); root.mainloop()

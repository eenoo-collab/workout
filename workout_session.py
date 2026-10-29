import datetime
import time
import tkinter as tk
from tkinter import ttk, messagebox
import winsound
import data_manager

class WorkoutSessionWindow:
    def __init__(self, parent, routine, on_finish):
        self.parent = parent
        self.routine = routine
        self.on_finish = on_finish
        self.win = tk.Toplevel(parent)
        self.win.title(f"운동 진행 - {routine['name']}")
        self.win.geometry("520x680")
        self.win.configure(bg="#F0F8FF")
        self.win.grab_set()

        self.start_time = time.time()
        self.rest_remaining = 0
        self.rest_paused = False
        self.check_vars = []

        self._build_ui()
        self._tick_timers()

    def _build_ui(self):
        q_frame = tk.Frame(self.win, bg="#E0F2FE", padx=10, pady=8)
        q_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(
            q_frame, text="✨ 오늘의 응원 문구 ✨", font=("Malgun Gothic", 10, "bold"),
            bg="#E0F2FE", fg="#0284C7"
        ).pack()
        tk.Label(
            q_frame, text=f'"{data_manager.get_quote()}"', font=("Malgun Gothic", 11, "bold"),
            bg="#E0F2FE", fg="#0C4A6E", wraplength=480
        ).pack(pady=3)

        list_frame = ttk.LabelFrame(self.win, text=f"📋 운동 체크리스트 ({self.routine['name']})")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(list_frame, highlightthickness=0, bg="#F0F8FF")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scroll_content = ttk.Frame(canvas)
        self.scroll_content.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for ex in self.routine.get("exercises", []):
            ef = ttk.Frame(self.scroll_content, padding=4)
            ef.pack(fill=tk.X, pady=4, padx=5)
            r_info = f" × {ex['reps']}" if ex.get("reps") else ""
            ttk.Label(
                ef, text=f"• {ex['name']} (총 {ex['sets']}세트{r_info} / 휴식 {ex.get('rest', 60)}초)",
                font=("Malgun Gothic", 10, "bold")
            ).pack(anchor="w")

            sets_box = ttk.Frame(ef)
            sets_box.pack(anchor="w", padx=15, pady=2)
            for s in range(ex["sets"]):
                var = tk.IntVar(value=0)
                cb = ttk.Checkbutton(
                    sets_box, text=f"{s+1}세트", variable=var,
                    command=lambda v=var, r=ex.get("rest", 60): self._on_check(v, r)
                )
                cb.pack(side=tk.LEFT, padx=5)
                self.check_vars.append(var)

        t_frame = ttk.LabelFrame(self.win, text="⏱️ 세트 사이 휴식 타이머")
        t_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_lbl = ttk.Label(
            t_frame, text="세트를 완료하고 체크하면 휴식 타이머가 시작됩니다.",
            font=("Malgun Gothic", 9)
        )
        self.status_lbl.pack(pady=2)

        self.timer_lbl = tk.Label(
            t_frame, text="00:00", font=("Consolas", 24, "bold"),
            fg="#0284C7", bg="#E0F2FE", padx=10, pady=2
        )
        self.timer_lbl.pack(pady=4)

        btn_f = ttk.Frame(t_frame)
        btn_f.pack(pady=4)
        ttk.Button(btn_f, text="-15초", width=6, style="Sky.TButton", command=lambda: self._adj_rest(-15)).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_f, text="+15초", width=6, style="Sky.TButton", command=lambda: self._adj_rest(15)).pack(side=tk.LEFT, padx=3)
        self.pause_btn = ttk.Button(btn_f, text="일시정지", width=8, style="Sky.TButton", command=self._toggle_pause)
        self.pause_btn.pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_f, text="건너뛰기", width=8, style="Sky.TButton", command=self._skip_rest).pack(side=tk.LEFT, padx=3)

        b_frame = ttk.Frame(self.win, padding=5)
        b_frame.pack(fill=tk.X, padx=10, pady=5)
        self.elapsed_lbl = ttk.Label(
            b_frame, text="진행 시간: 00:00", font=("Malgun Gothic", 10, "bold"),
            foreground="#0369A1"
        )
        self.elapsed_lbl.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            b_frame, text="🏁 운동 완료 및 저장", style="Main.TButton", command=self._finish_workout
        ).pack(side=tk.RIGHT, padx=5)

    def _on_check(self, var, rest_sec):
        if var.get() == 1:
            self.rest_remaining = rest_sec
            self.rest_paused = False
            self.pause_btn.config(text="일시정지")
            self.status_lbl.config(text="휴식 중입니다. 호흡을 가다듬으세요!", foreground="#0284C7")
            self._update_timer_label()

    def _adj_rest(self, sec):
        self.rest_remaining = max(0, self.rest_remaining + sec)
        self._update_timer_label()

    def _toggle_pause(self):
        if self.rest_remaining > 0:
            self.rest_paused = not self.rest_paused
            self.pause_btn.config(text="재개" if self.rest_paused else "일시정지")

    def _skip_rest(self):
        self.rest_remaining = 0
        self._update_timer_label()
        self.status_lbl.config(text="휴식을 건너뛰었습니다. 다음 세트를 시작하세요!", foreground="#0C4A6E")

    def _update_timer_label(self):
        m, s = divmod(self.rest_remaining, 60)
        self.timer_lbl.config(text=f"{m:02d}:{s:02d}")

    def _tick_timers(self):
        if not self.win.winfo_exists():
            return
        if self.rest_remaining > 0 and not self.rest_paused:
            self.rest_remaining -= 1
            self._update_timer_label()
            if self.rest_remaining == 0:
                try:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except Exception:
                    pass
                self.status_lbl.config(text="⏰ 휴식 끝! 다음 세트를 시작하세요!", foreground="#D93025")
        elapsed = int(time.time() - self.start_time)
        m, s = divmod(elapsed, 60)
        self.elapsed_lbl.config(text=f"진행 시간: {m:02d}:{s:02d}")
        self.win.after(1000, self._tick_timers)

    def _finish_workout(self):
        completed = sum(v.get() for v in self.check_vars)
        total = len(self.check_vars)
        msg = f"총 {total}세트 중 {completed}세트를 완료했습니다.\n운동을 완료하고 기록을 저장하시겠습니까?"
        if not messagebox.askyesno("운동 완료", msg, parent=self.win):
            return
        elapsed = int(time.time() - self.start_time)
        self.win.destroy()
        self.on_finish(self.routine["name"], completed, total, elapsed)

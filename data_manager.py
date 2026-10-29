import datetime
import json
import os
import random
import subprocess
import sys

DATA_FILE = "workout_data.json"
TASK_NAME = "DailyWorkoutReminder"

DEFAULT_DATA = {
    "routines": [
        {
            "name": "상체 집중 (가슴/등/어깨)",
            "exercises": [
                {"name": "푸시업", "sets": 4, "reps": "15회", "rest": 60},
                {"name": "덤벨 로우 / 풀업", "sets": 4, "reps": "12회", "rest": 60},
                {"name": "숄더프레스", "sets": 3, "reps": "12회", "rest": 60}
            ]
        },
        {
            "name": "하체 & 코어 집중",
            "exercises": [
                {"name": "스쿼트", "sets": 4, "reps": "15회", "rest": 60},
                {"name": "런지", "sets": 3, "reps": "12회", "rest": 60},
                {"name": "플랭크", "sets": 3, "reps": "45초", "rest": 45}
            ]
        },
        {
            "name": "전신 유산소 & 버닝",
            "exercises": [
                {"name": "버피 테스트", "sets": 3, "reps": "15회", "rest": 45},
                {"name": "마운틴 클라이머", "sets": 3, "reps": "20회", "rest": 45},
                {"name": "점핑잭", "sets": 3, "reps": "30회", "rest": 30}
            ]
        }
    ],
    "active_routine_idx": 0,
    "history": [],
    "reminder_time": "20:00",
    "reminder_interval": 1
}

QUOTES = [
    "땀은 결코 배신하지 않습니다! 오늘도 파이팅!",
    "오늘의 한 세트가 내일의 단단한 나를 만듭니다.",
    "가장 힘든 순간이 바로 근육과 마음이 성장하는 순간!",
    "시작이 반입니다. 운동을 끝마치고 느낄 뿌듯함을 상상하세요!",
    "운동을 완료하고 후회한 사람은 아무도 없습니다.",
    "포기하고 싶을 때 한 번 더! 당신의 한계는 생각보다 멉니다.",
    "작은 꾸준함이 모여 위대한 변화를 만듭니다.",
    "어제의 나보다 1%만 더 강해지면 충분합니다!"
]

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return json.loads(json.dumps(DEFAULT_DATA))

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_quote():
    return random.choice(QUOTES)

def get_days_since_last_workout(data):
    history = data.get("history", [])
    if not history:
        return None
    latest = None
    for item in history:
        try:
            d = datetime.datetime.strptime(item["date"], "%Y-%m-%d").date()
            if latest is None or d > latest:
                latest = d
        except Exception:
            continue
    if latest is None:
        return None
    return (datetime.date.today() - latest).days

def save_workout_record(data, routine_name, completed_sets, total_sets, duration_sec):
    record = {
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "time": datetime.datetime.now().strftime("%H:%M"),
        "routine": routine_name,
        "completed_sets": completed_sets,
        "total_sets": total_sets,
        "duration_sec": duration_sec
    }
    if "history" not in data:
        data["history"] = []
    data["history"].append(record)
    save_data(data)
    return record

def schedule_task(reminder_time, interval_days=1):
    py_exe = sys.executable
    pyw_exe = os.path.join(os.path.dirname(py_exe), "pythonw.exe")
    runner = pyw_exe if os.path.exists(pyw_exe) else py_exe
    script_path = os.path.abspath("main.py")
    mo = max(1, min(365, int(interval_days)))
    cmd = (
        f'schtasks /Create /SC DAILY /MO {mo} /TN "{TASK_NAME}" '
        f'/TR "\\"{runner}\\" \\"{script_path}\\" --notify" '
        f'/ST {reminder_time} /F'
    )
    try:
        res = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="cp949"
        )
        return res.returncode == 0, (res.stdout or res.stderr).strip()
    except Exception as e:
        return False, str(e)

def delete_task():
    cmd = f'schtasks /Delete /TN "{TASK_NAME}" /F'
    try:
        res = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="cp949"
        )
        return res.returncode == 0, (res.stdout or res.stderr).strip()
    except Exception as e:
        return False, str(e)

def is_task_scheduled():
    cmd = f'schtasks /Query /TN "{TASK_NAME}"'
    try:
        res = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="cp949"
        )
        return res.returncode == 0
    except Exception:
        return False

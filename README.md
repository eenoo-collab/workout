# 운동 기록 및 알림 프로그램

Python의 tkinter로 만든 Windows용 운동 기록 프로그램이다. 운동 루틴을 만들고, 운동하면서 세트를 체크하고, 세트 사이 휴식 시간을 재고, 기록을 남기고, 정해진 시간에 운동 알림을 받을 수 있다. 이번 업데이트에서 운동 정보 API를 추가하여, 루틴에 있는 운동의 대상 근육과 운동 방법을 바로 확인할 수 있게 했다.

## 1. 실행 방법

### 실행 순서

```
git clone https://github.com/eenoo-collab/workout.git
cd workout
```

그다음 프로젝트 폴더에 `.env` 파일을 만들고 API 키를 넣는다. (아래 2번 참고)

```
uv run main.py
```

uv가 Python 3.14와 필요한 라이브러리를 `uv.lock` 기준으로 자동 설치하므로 따로 `pip install`을 할 필요가 없다.

## 2. API 키 설정

운동 정보는 [API Ninjas의 Exercises API](https://api-ninjas.com/api/exercises)에서 가져온다. 무료 키가 필요하다.

1. https://api-ninjas.com/register 에서 github로 가입하고 키를 발급받는다.
2. 프로젝트 폴더(`main.py`와 같은 위치)에 `.env` 파일을 만들고 한 줄을 적는다.

```
API_NINJAS_KEY=발급받은_키
```

- 따옴표와 공백 없이 `이름=값` 형식으로 쓴다. 견본은 `.env.example`에 있다.
- `.env`는 `.gitignore`에 들어 있어서 GitHub에 올라가지 않는다. 키 값은 icampus로 따로 제출한다.
- 키가 없어도 앱은 정상 실행된다. "운동 정보"를 누르면 키가 없다는 안내가 뜬다.

## 3. 주요 기능

- **루틴 관리**: 루틴과 운동(세트 수, 세트당 목표, 휴식 시간)을 추가·삭제
- **운동 진행**: 세트를 체크하면 휴식 타이머 시작, ±15초 조절·일시정지·건너뛰기 가능
- **응원 문구**: 운동 창을 열 때 문구 하나를 무작위로 보여줌
- **기록 보기**: 날짜, 루틴, 완료 세트, 소요 시간을 목록으로 확인
- **알림 설정**: 시간과 반복 주기를 정해 Windows 작업 스케줄러에 등록
- **운동 정보 (API)**: 루틴 수정 창에서 운동을 고르고 버튼을 누르면 근육·난이도·방법을 팝업으로 표시

## 4. 코드 구조

python 파일은 세 개이다. 화면(`main.py`, `workout_session.py`)과 데이터·외부 통신(`data_manager.py`)을 나누었다.

### main.py : 메인 화면

- `apply_theme` : 하늘색 테마를 ttk 스타일로 한 번에 적용한다.
- `RoutineEditorDialog` : 루틴 수정 창이다. 운동 추가·삭제 버튼과 이번에 추가한 운동 정보 버튼(`_show_info`)이 여기에 있다.
- `WorkoutApp` : 메인 창이다. 마지막 운동 후 며칠이 지났는지 보여주고, 루틴 선택·운동 시작·기록·알림 창을 연다.
- `handle_notification` : 작업 스케줄러가 `main.py --notify`로 실행했을 때 "지금 시작하시겠습니까?"를 물어보고, 승인하면 바로 운동 창을 연다.

### workout_session.py : 운동 진행 창

- 루틴의 세트마다 체크박스를 만들고, 체크하면 그 운동의 휴식 시간으로 타이머를 시작한다.
- `_tick_timers`가 `after(1000)`으로 1초마다 휴식 시간과 전체 진행 시간을 갱신하고, 휴식이 끝나면 `winsound`로 소리를 낸다.
- 완료 버튼을 누르면 `on_finish` 콜백으로 결과를 메인 화면에 넘겨 기록을 저장한다.

### data_manager.py : 데이터와 API

- `load_data` / `save_data` : `workout_data.json`을 읽고 쓴다. 파일이 없으면 기본 루틴으로 새로 만든다.
- `save_workout_record` / `get_days_since_last_workout` : 기록을 쌓고 마지막 운동 이후 일수를 계산한다.
- `schedule_task` / `delete_task` / `is_task_scheduled` : `schtasks` 명령으로 알림을 등록·삭제·확인한다.
- `fetch_exercise_info` : 운동 정보 API 호출 (아래 5번 참고).

## 5. API 적용 방식

`RoutineEditorDialog`의 운동 정보 버튼을 누르면 다음 순서로 동작한다.

1. 목록에서 선택한 운동 이름을 가져온다. 선택이 없으면 안내 메시지를 띄운다.
2. `get_search_term`이 한국어 이름을 영어 검색어로 바꾼다. API가 영어만 지원하기 때문에 `EXERCISE_EN` 딕셔너리(예: 스쿼트 → squat)를 두었고, 목록에 없는 이름은 입력한 그대로 검색한다. `덤벨 로우 / 풀업`처럼 `/`가 있으면 앞부분만 쓴다.
3. `fetch_exercise_info`가 `GET https://api.api-ninjas.com/v1/exercises?name=검색어`를 호출한다. 헤더 `X-Api-Key`에 `.env`에서 읽은 키를 넣고, 대기 시간은 5초이다.
4. 반환값은 `(결과 목록, 오류 메시지)` 한 쌍이다. 성공하면 오류 메시지가 `None`이고, 실패하면 결과가 `None`이다. 이렇게 하면 화면 쪽에서 `if err:` 하나로 성공과 실패를 나눌 수 있다.
5. `format_exercise_info`가 결과(이름, 대상 근육, 종류, 난이도, 장비, 방법, 주의사항)를 글로 만들어 팝업의 읽기 전용 텍스트 창에 보여준다.

### 실패했을 때

- `.env`에 키가 없음: API 키가 없습니다. `.env`에 `API_NINJAS_KEY`를 넣어 주세요
- 키가 틀림 (HTTP 400·401·403): API 키가 올바르지 않습니다
- 사용 한도 초과 (HTTP 429): API 사용 한도를 넘었습니다
- 인터넷 끊김, 시간 초과: 정보를 불러올 수 없습니다
- 검색 결과 없음: 정보를 찾지 못했습니다

어느 경우에도 앱은 멈추지 않고, 운동 정보 외의 기능은 인터넷 없이 그대로 동작한다.

## 6. 한계

- API 응답은 영어이다. 번역은 하지 않았다.
- `EXERCISE_EN`에 없는 한국어 이름은 검색 결과가 없을 수 있다. 이 경우 영어 이름(예: squat)으로 운동을 추가하면 찾을 수 있다.
- 무료 키는 한 번에 최대 5개 결과만 받을 수 있고, 사용량 제한이 있을 수 있다.
- `winsound`와 `schtasks`를 쓰므로 Windows에서만 동작한다.

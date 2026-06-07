import sqlite3
from datetime import date, timedelta
from pathlib import Path

import theme

DB_NAME = "study_tracker.db"
FREE_SESSION_PREFIX = "Sesión de estudio de tema libre #"


def get_db_path() -> Path:
    return Path(__file__).parent / DB_NAME


def init_db(db_path: Path | None = None) -> None:
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT NOT NULL,
                subject TEXT NOT NULL,
                note TEXT,
                duration_seconds INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS streak_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                current_streak INTEGER NOT NULL DEFAULT 0,
                last_study_date TEXT
            )
            """
        )
        row = conn.execute("SELECT 1 FROM streak_state WHERE id = 1").fetchone()
        if not row:
            conn.execute(
                "INSERT INTO streak_state (id, current_streak, last_study_date) VALUES (1, 0, NULL)"
            )
        _ensure_default_settings(conn)


def _ensure_default_settings(conn: sqlite3.Connection) -> None:
    defaults = {
        "weekly_goal_hours": str(theme.DEFAULT_WEEKLY_GOAL_HOURS),
        "inactivity_minutes": str(theme.DEFAULT_INACTIVITY_MINUTES),
    }
    for key, value in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )


def get_setting(key: str, default: str = "", db_path: Path | None = None) -> str:
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default


def set_setting(key: str, value: str, db_path: Path | None = None) -> None:
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_weekly_goal_hours(db_path: Path | None = None) -> float:
    raw = get_setting("weekly_goal_hours", str(theme.DEFAULT_WEEKLY_GOAL_HOURS), db_path)
    try:
        return max(0.5, float(raw))
    except ValueError:
        return float(theme.DEFAULT_WEEKLY_GOAL_HOURS)


def get_inactivity_minutes(db_path: Path | None = None) -> int:
    raw = get_setting("inactivity_minutes", str(theme.DEFAULT_INACTIVITY_MINUTES), db_path)
    try:
        return max(1, int(raw))
    except ValueError:
        return theme.DEFAULT_INACTIVITY_MINUTES


def get_next_free_session_subject(db_path: Path | None = None) -> str:
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT subject FROM sessions WHERE subject LIKE ?",
            (f"{FREE_SESSION_PREFIX}%",),
        ).fetchall()

    max_num = 0
    for row in rows:
        suffix = row[0][len(FREE_SESSION_PREFIX) :]
        if suffix.isdigit():
            max_num = max(max_num, int(suffix))
    return f"{FREE_SESSION_PREFIX}{max_num + 1}"


def get_days_with_sessions(db_path: Path | None = None) -> set[date]:
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT session_date FROM sessions ORDER BY session_date"
        ).fetchall()
    return {date.fromisoformat(row[0]) for row in rows}


def compute_streak(study_days: set[date] | None = None, today: date | None = None) -> int:
    today = today or date.today()
    days = study_days if study_days is not None else set()

    anchor = today if today in days else today - timedelta(days=1)
    if anchor not in days:
        return 0

    streak = 0
    cursor = anchor
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def update_streak_cache(db_path: Path | None = None) -> int:
    path = db_path or get_db_path()
    study_days = get_days_with_sessions(path)
    streak = compute_streak(study_days)
    last_date = max(study_days).isoformat() if study_days else None
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            UPDATE streak_state
            SET current_streak = ?, last_study_date = ?
            WHERE id = 1
            """,
            (streak, last_date),
        )
    return streak


def get_streak(db_path: Path | None = None) -> int:
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT current_streak FROM streak_state WHERE id = 1"
        ).fetchone()
    if row:
        return int(row[0])
    return update_streak_cache(path)


def save_session(
    session_date: date,
    subject: str,
    note: str,
    duration_seconds: int,
    db_path: Path | None = None,
) -> None:
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_date, subject, note, duration_seconds)
            VALUES (?, ?, ?, ?)
            """,
            (session_date.isoformat(), subject.strip(), note.strip(), duration_seconds),
        )
    update_streak_cache(path)


def get_week_sessions(
    reference: date | None = None,
    db_path: Path | None = None,
) -> tuple[date, date, dict[date, list[dict]], int]:
    today = reference or date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT session_date, subject, note, duration_seconds
            FROM sessions
            WHERE session_date BETWEEN ? AND ?
            ORDER BY session_date, created_at
            """,
            (monday.isoformat(), sunday.isoformat()),
        ).fetchall()

    by_day: dict[date, list[dict]] = {}
    total_seconds = 0
    for row in rows:
        day = date.fromisoformat(row["session_date"])
        entry = {
            "subject": row["subject"],
            "note": row["note"] or "",
            "duration_seconds": row["duration_seconds"],
        }
        by_day.setdefault(day, []).append(entry)
        total_seconds += row["duration_seconds"]

    return monday, sunday, by_day, total_seconds


def get_daily_totals_map(
    start: date,
    end: date,
    db_path: Path | None = None,
) -> dict[date, int]:
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            """
            SELECT session_date, SUM(duration_seconds) AS total
            FROM sessions
            WHERE session_date BETWEEN ? AND ?
            GROUP BY session_date
            """,
            (start.isoformat(), end.isoformat()),
        ).fetchall()
    return {date.fromisoformat(row[0]): int(row[1]) for row in rows}


def get_month_daily_data(
    year: int,
    month: int,
    db_path: Path | None = None,
) -> list[tuple[date, int]]:
    import calendar

    last_day = calendar.monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, last_day)
    totals = get_daily_totals_map(start, end, db_path)
    return [
        (start + timedelta(days=i), totals.get(start + timedelta(days=i), 0))
        for i in range(last_day)
    ]


def get_heatmap_data(
    days: int = 90,
    db_path: Path | None = None,
) -> list[tuple[date, int]]:
    end = date.today()
    start = end - timedelta(days=days - 1)
    totals = get_daily_totals_map(start, end, db_path)
    return [(start + timedelta(days=i), totals.get(start + timedelta(days=i), 0)) for i in range(days)]


def heatmap_color(seconds: int) -> str:
    if seconds <= 0:
        return theme.HEAT_EMPTY
    hours = seconds / 3600
    if hours <= 2:
        return theme.HEAT_LOW
    if hours <= 4:
        return theme.HEAT_MED
    return theme.HEAT_HIGH


def format_day_tooltip(day: date, seconds: int) -> str:
    name = theme.DAY_NAMES_ES[day.weekday()]
    month = theme.MONTH_NAMES_ES[day.month - 1]
    label = f"{name} {day.day} {month}"
    if seconds <= 0:
        return f"{label} — 0h"
    return f"{label} — {format_hours_minutes(seconds)}"


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def format_hours(seconds: int) -> str:
    hours = seconds / 3600
    return f"{hours:.1f} h"


def format_timer(seconds: int) -> str:
    hours, remainder = divmod(max(0, seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_hours_minutes(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours and minutes:
        return f"{hours}h {minutes}min"
    if hours:
        return f"{hours}h"
    return f"{minutes}min"


def format_goal_progress(current_seconds: int, goal_hours: float) -> str:
    goal_seconds = int(goal_hours * 3600)
    pct = min(100, int(current_seconds / goal_seconds * 100)) if goal_seconds else 0
    return (
        f"{format_hours_minutes(current_seconds)} / {goal_hours:g}h  ({pct}%)"
    )


def get_recent_sessions(
    limit: int = 10,
    db_path: Path | None = None,
) -> list[dict]:
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT session_date, subject, note, duration_seconds, created_at
            FROM sessions
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    today = date.today()
    yesterday = today - timedelta(days=1)
    results: list[dict] = []
    for row in rows:
        session_day = date.fromisoformat(row["session_date"])
        if session_day == today:
            day_label = "Hoy"
        elif session_day == yesterday:
            day_label = "Ayer"
        else:
            day_label = session_day.strftime("%d %b")

        results.append(
            {
                "day_label": day_label,
                "subject": row["subject"],
                "note": row["note"] or "",
                "duration_seconds": row["duration_seconds"],
            }
        )
    return results


def get_daily_totals(reference: date | None = None, db_path: Path | None = None) -> list[int]:
    monday, _, by_day, _ = get_week_sessions(reference, db_path)
    return [
        sum(s["duration_seconds"] for s in by_day.get(monday + timedelta(days=i), []))
        for i in range(7)
    ]

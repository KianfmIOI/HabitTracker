import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

DB_FILE = Path(__file__).parent / "habits.db"
FIRE = "\U0001F525"
ICE = "\U0001F9CA"


def _connect():
    """Open a SQLite connection configured for named-column access and FK safety."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Enforce relational integrity on deletes/updates across related tables.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create database tables if they do not already exist."""
    with _connect() as conn:
        conn.executescript(
            # Triple-quoted SQL keeps multi-line schema statements readable in Python.
            # It is just a normal Python string literal that preserves line breaks.
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                last_check_in_date TEXT
            );

            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                creation_date TEXT NOT NULL,
                last_check_in_date TEXT,
                streak INTEGER NOT NULL DEFAULT 0,
                is_main INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (user_id, name)
            );

            CREATE TABLE IF NOT EXISTS habit_events (
                id INTEGER PRIMARY KEY,
                habit_id INTEGER NOT NULL,
                event_date TEXT NOT NULL,
                event_type TEXT NOT NULL CHECK (event_type IN ('fire', 'ice')),
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
                UNIQUE (habit_id, event_date)
            );
            """
        )


def _get_or_create_user(conn):
    """Return the single local user id, inserting a placeholder user when absent."""
    row = conn.execute("SELECT id, name, last_check_in_date FROM users LIMIT 1").fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO users (name, last_check_in_date) VALUES (?, ?)",
        ("", None),
    )
    return cur.lastrowid


def load_data():
    """Read SQL rows and rebuild the same dict shape expected by the Flask app."""
    init_db()
    with _connect() as conn:
        user_row = conn.execute(
            "SELECT id, name, last_check_in_date FROM users LIMIT 1"
        ).fetchone()
        if not user_row:
            return {"user": None, "last_check_in_date": None, "habits": {}}

        habits_rows = conn.execute(
            """
            SELECT id, name, creation_date, last_check_in_date, streak, is_main
            FROM habits
            WHERE user_id = ?
            ORDER BY name
            """,
            (user_row["id"],),
        ).fetchall()

        habits = {}
        for row in habits_rows:
            events = conn.execute(
                # Triple-quoted SQL is used for legibility when a query spans lines.
                """
                SELECT event_type
                FROM habit_events
                WHERE habit_id = ?
                ORDER BY event_date ASC
                """,
                (row["id"],),
            ).fetchall()
            history = [FIRE if ev["event_type"] == "fire" else ICE for ev in events]
            habits[row["name"]] = {
                "creation_date": row["creation_date"],
                "last_check_in_date": row["last_check_in_date"],
                "history": history,
                "streak": row["streak"],
                "is_main": bool(row["is_main"]),
            }

        return {
            "user": user_row["name"] or None,
            "last_check_in_date": user_row["last_check_in_date"],
            "habits": habits,
        }


def set_user(_data, name):
    """Validate and persist the user display name."""
    clean = (name or "").strip()
    if not clean:
        return False, "Name cannot be empty."

    init_db()
    with _connect() as conn:
        user_id = _get_or_create_user(conn)
        conn.execute(
            "UPDATE users SET name = ? WHERE id = ?",
            (clean, user_id),
        )
    return True, f"Welcome, {clean}."


def add_habit(_data, name):
    """Create a new habit with default tracking fields."""
    clean = (name or "").strip().lower()
    if not clean:
        return False, "Habit name cannot be empty."

    today = date.today().isoformat()
    init_db()
    with _connect() as conn:
        user_id = _get_or_create_user(conn)
        exists = conn.execute(
            "SELECT 1 FROM habits WHERE user_id = ? AND name = ?",
            (user_id, clean),
        ).fetchone()
        if exists:
            return False, "Habit already exists."

        conn.execute(
            # Triple quotes are used because this INSERT is easier to read on multiple lines.
            """
            INSERT INTO habits (user_id, name, creation_date, last_check_in_date, streak, is_main)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, clean, today, None, 0, 0),
        )
    return True, f"Habit '{clean}' added."


def delete_habit(_data, name):
    """Delete one habit by name for the current user."""
    init_db()
    with _connect() as conn:
        user_id = _get_or_create_user(conn)
        cur = conn.execute(
            "DELETE FROM habits WHERE user_id = ? AND name = ?",
            (user_id, name),
        )
        if cur.rowcount == 0:
            return False, "Habit not found."
    return True, f"Habit '{name}' deleted."


def select_main_habit(_data, habit_name):
    """Mark one habit as main and unset main on all other habits."""
    init_db()
    with _connect() as conn:
        user_id = _get_or_create_user(conn)
        target = conn.execute(
            "SELECT id FROM habits WHERE user_id = ? AND name = ?",
            (user_id, habit_name),
        ).fetchone()
        if not target:
            return False, "Habit not found."

        conn.execute("UPDATE habits SET is_main = 0 WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE habits SET is_main = 1 WHERE user_id = ? AND name = ?",
            (user_id, habit_name),
        )
    return True, f"Habit '{habit_name}' is now main."


def deselect_main_habit(_data, habit_name):
    """Unset the main flag for a specific habit."""
    init_db()
    with _connect() as conn:
        user_id = _get_or_create_user(conn)
        target = conn.execute(
            "SELECT id FROM habits WHERE user_id = ? AND name = ?",
            (user_id, habit_name),
        ).fetchone()
        if not target:
            return False, "Habit not found."

        conn.execute(
            "UPDATE habits SET is_main = 0 WHERE user_id = ? AND name = ?",
            (user_id, habit_name),
        )
    return True, f"Habit '{habit_name}' is no longer main."


def toggle_main_habit(data, habit_name):
    """Switch a habit between main and not-main states."""
    habit = data.get("habits", {}).get(habit_name)
    if not habit:
        return False, "Habit not found."
    if habit.get("is_main", False):
        return deselect_main_habit(data, habit_name)
    return select_main_habit(data, habit_name)


def _insert_missed_ice_events(conn, habit_id, last_iso, today_iso):
    """Insert one ICE event per missed day between last check-in and today."""
    last_day = date.fromisoformat(last_iso)
    today_day = date.fromisoformat(today_iso)
    missed = (today_day - last_day).days - 1
    if missed <= 0:
        return False

    for i in range(1, missed + 1):
        d = (last_day + timedelta(days=i)).isoformat()
        conn.execute(
            # Triple quotes are used for consistent formatting with other SQL blocks.
            """
            INSERT OR IGNORE INTO habit_events (habit_id, event_date, event_type)
            VALUES (?, ?, 'ice')
            """,
            (habit_id, d),
        )
    return True


def check_in(_data, habit_name):
    """Record today's FIRE event, fill missed ICE events, and update streak/date fields."""
    today = date.today().isoformat()
    init_db()
    with _connect() as conn:
        user_id = _get_or_create_user(conn)
        habit = conn.execute(
            """
            SELECT id, last_check_in_date, streak
            FROM habits
            WHERE user_id = ? AND name = ?
            """,
            (user_id, habit_name),
        ).fetchone()
        if not habit:
            return False, "Habit not found."

        if habit["last_check_in_date"] == today:
            return False, "Already checked in today."

        streak = habit["streak"]
        last_check = habit["last_check_in_date"]
        had_miss = False
        if last_check:
            had_miss = _insert_missed_ice_events(conn, habit["id"], last_check, today)
            if had_miss:
                streak = 0

        conn.execute(
            # Triple-quoted SQL makes this write query easier to scan and maintain.
            """
            INSERT INTO habit_events (habit_id, event_date, event_type)
            VALUES (?, ?, 'fire')
            """,
            (habit["id"], today),
        )

        streak += 1
        conn.execute(
            """
            UPDATE habits
            SET last_check_in_date = ?, streak = ?
            WHERE id = ?
            """,
            (today, streak, habit["id"]),
        )
        conn.execute(
            """
            UPDATE users
            SET last_check_in_date = ?
            WHERE id = ?
            """,
            (today, user_id),
        )
    return True, f"Checked in '{habit_name}'."


def _format_date(value):
    """Render ISO date as UI-friendly day/month text."""
    if not value:
        return "-"
    return datetime.fromisoformat(value).strftime("%d %b")


def get_habit_rows(data):
    """Build template rows from normalized habit data for the index page."""
    rows = []
    for name, habit in data.get("habits", {}).items():
        rows.append(
            {
                "name": name,
                "name_title": name.title(),
                "is_main": habit.get("is_main", False),
                "created": _format_date(habit.get("creation_date")),
                "last_check": _format_date(habit.get("last_check_in_date")),
                "streak": habit.get("streak", 0),
                "history": "".join(habit.get("history", [])[-7:]),
            }
        )
    return rows

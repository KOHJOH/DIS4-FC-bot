import sqlite3
import json
from config import DB_FILE

def connect():
    return sqlite3.connect(DB_FILE)

def setup_database():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        user_id TEXT PRIMARY KEY,
        rank TEXT DEFAULT 'New Hire',
        assignment TEXT DEFAULT 'Unassigned',
        department TEXT DEFAULT 'Unassigned',
        pick_floor TEXT DEFAULT 'Unassigned',
        stow_floor TEXT DEFAULT 'Unassigned',
        amnesty_floor TEXT DEFAULT 'Unassigned',
        productivity INTEGER DEFAULT 0,
        quality INTEGER DEFAULT 100,
        safety INTEGER DEFAULT 100,
        attendance INTEGER DEFAULT 100,
        leadership INTEGER DEFAULT 0,
        writeups INTEGER DEFAULT 0,
        certifications TEXT DEFAULT '[]',
        applications TEXT DEFAULT '{}',
        clocked_in INTEGER DEFAULT 0,
        clockin_time REAL,
        total_minutes_worked INTEGER DEFAULT 0,
        shift TEXT DEFAULT 'Unassigned',
        area TEXT DEFAULT 'Unassigned',
        reports_to TEXT DEFAULT 'Unassigned',
        upt INTEGER DEFAULT 20,
        pto INTEGER DEFAULT 10,
        vacation INTEGER DEFAULT 0,
        morale INTEGER DEFAULT 100,
        swag_points INTEGER DEFAULT 0,
        last_activity_time REAL,
        current_station TEXT DEFAULT 'Unassigned',
        station_status TEXT DEFAULT 'Idle',
        weekly_shifts INTEGER DEFAULT 0,
        weekly_minutes INTEGER DEFAULT 0
    )
    """)


    def ensure_column(column_name, column_type, default_value):
        cursor.execute("PRAGMA table_info(profiles)")
        columns = [row[1] for row in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE profiles ADD COLUMN {column_name} {column_type} DEFAULT {default_value}")

    ensure_column("shift", "TEXT", "'Unassigned'")
    ensure_column("area", "TEXT", "'Unassigned'")
    ensure_column("reports_to", "TEXT", "'Unassigned'")
    ensure_column("upt", "INTEGER", "20")
    ensure_column("pto", "INTEGER", "10")
    ensure_column("vacation", "INTEGER", "0")
    ensure_column("morale", "INTEGER", "100")
    ensure_column("swag_points", "INTEGER", "0")
    ensure_column("weekly_shifts", "INTEGER", "0")
    ensure_column("weekly_minutes", "INTEGER", "0")


    ensure_column("last_activity_time", "REAL", "NULL")
    ensure_column("current_station", "TEXT", "'Unassigned'")
    ensure_column("station_status", "TEXT", "'Idle'")

    db.commit()
    db.close()

def get_profile(user_id):
    user_id = str(user_id)
    db = connect()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row is None:
        cursor.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
        db.commit()
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

    columns = [desc[0] for desc in cursor.description]
    profile = dict(zip(columns, row))

    profile["certifications"] = json.loads(profile["certifications"])
    profile["applications"] = json.loads(profile["applications"])
    profile["clocked_in"] = bool(profile["clocked_in"])

    db.close()
    return profile


def update_profile(user_id, profile):
    user_id = str(user_id)
    db = connect()
    cursor = db.cursor()

    profile = profile.copy()
    profile["certifications"] = json.dumps(profile.get("certifications", []))
    profile["applications"] = json.dumps(profile.get("applications", {}))
    profile["clocked_in"] = 1 if profile.get("clocked_in") else 0

    fields = [
        "rank", "assignment", "department", "pick_floor", "stow_floor", "amnesty_floor",
        "productivity", "quality", "safety", "attendance", "leadership", "writeups",
        "certifications", "applications", "clocked_in", "clockin_time", "total_minutes_worked",
        "shift", "area", "reports_to", "upt", "pto", "vacation", "morale", "swag_points",
        "weekly_shifts", "weekly_minutes"
    ]

    cursor.execute("PRAGMA table_info(profiles)")
    existing = {row[1] for row in cursor.fetchall()}
    fields = [field for field in fields if field in existing]

    set_clause = ", ".join([f"{field} = ?" for field in fields])
    values = [profile.get(field) for field in fields]
    values.append(user_id)

    cursor.execute(f"UPDATE profiles SET {set_clause} WHERE user_id = ?", values)

    db.commit()
    db.close()

def list_profiles():
    db = connect()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM profiles")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    profiles = []

    for row in rows:
        profile = dict(zip(columns, row))
        profile["certifications"] = json.loads(profile.get("certifications") or "[]")
        profile["applications"] = json.loads(profile.get("applications") or "{}")
        profile["clocked_in"] = bool(profile.get("clocked_in"))
        profiles.append(profile)

    db.close()
    return profiles

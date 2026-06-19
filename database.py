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
        weekly_shifts INTEGER DEFAULT 0,
        weekly_minutes INTEGER DEFAULT 0
    )
    """)

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

    cursor.execute("""
    UPDATE profiles SET
        rank = ?,
        assignment = ?,
        department = ?,
        pick_floor = ?,
        stow_floor = ?,
        amnesty_floor = ?,
        productivity = ?,
        quality = ?,
        safety = ?,
        attendance = ?,
        leadership = ?,
        writeups = ?,
        certifications = ?,
        applications = ?,
        clocked_in = ?,
        clockin_time = ?,
        total_minutes_worked = ?,
        weekly_shifts = ?,
        weekly_minutes = ?
    WHERE user_id = ?
    """, (
        profile.get("rank", "New Hire"),
        profile.get("assignment", "Unassigned"),
        profile.get("department", "Unassigned"),
        profile.get("pick_floor", "Unassigned"),
        profile.get("stow_floor", "Unassigned"),
        profile.get("amnesty_floor", "Unassigned"),
        profile.get("productivity", 0),
        profile.get("quality", 100),
        profile.get("safety", 100),
        profile.get("attendance", 100),
        profile.get("leadership", 0),
        profile.get("writeups", 0),
        profile["certifications"],
        profile["applications"],
        profile["clocked_in"],
        profile.get("clockin_time"),
        profile.get("total_minutes_worked", 0),
        profile.get("weekly_shifts", 0),
        profile.get("weekly_minutes", 0),
        user_id
    ))

    db.commit()
    db.close()

"""
database.py — إدارة SQLite
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect("karasven.db", check_same_thread=False)
c    = conn.cursor()

c.executescript("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    username TEXT,
    first_seen TEXT
);
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    code TEXT,
    lang TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS stats (
    user_id INTEGER PRIMARY KEY,
    exec_count INTEGER DEFAULT 0,
    ai_count   INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    role       TEXT,
    message    TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS deployments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER,
    url          TEXT,
    project_name TEXT,
    created_at   TEXT
);
CREATE TABLE IF NOT EXISTS banned_users (
    user_id   INTEGER PRIMARY KEY,
    reason    TEXT,
    banned_at TEXT
);
CREATE TABLE IF NOT EXISTS message_map (
    admin_msg_id INTEGER PRIMARY KEY,
    user_id      INTEGER,
    created_at   TEXT
);
CREATE TABLE IF NOT EXISTS daily_challenges (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    date      TEXT UNIQUE,
    challenge TEXT
);
""")
conn.commit()

# migrations آمنة
for _m in [
    "ALTER TABLE stats ADD COLUMN ai_count INTEGER DEFAULT 0",
    "ALTER TABLE stats ADD COLUMN exec_count INTEGER DEFAULT 0",
]:
    try:
        c.execute(_m)
        conn.commit()
    except Exception:
        pass


# ─── Users ───────────────────────────────────────────────────
def register_user(user):
    c.execute(
        "INSERT OR IGNORE INTO users(user_id,full_name,username,first_seen) VALUES(?,?,?,?)",
        (user.id, user.full_name, user.username or "", datetime.now().strftime("%Y-%m-%d")),
    )
    conn.commit()


def is_banned(uid: int) -> bool:
    c.execute("SELECT 1 FROM banned_users WHERE user_id=?", (uid,))
    return c.fetchone() is not None


def all_users() -> list:
    c.execute("SELECT user_id FROM users")
    return [r[0] for r in c.fetchall()]


def ban_user(uid: int, reason: str = ""):
    c.execute(
        "INSERT OR REPLACE INTO banned_users(user_id,reason,banned_at) VALUES(?,?,?)",
        (uid, reason, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()


def unban_user(uid: int):
    c.execute("DELETE FROM banned_users WHERE user_id=?", (uid,))
    conn.commit()


def get_all_users_info() -> list:
    c.execute(
        "SELECT user_id,full_name,username,first_seen FROM users ORDER BY first_seen DESC LIMIT 20"
    )
    return c.fetchall()


# ─── Projects ────────────────────────────────────────────────
def save_project(uid: int, code: str, lang: str):
    c.execute(
        "INSERT INTO projects(user_id,code,lang,created_at) VALUES(?,?,?,?)",
        (uid, code, lang, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()


def get_projects(uid: int) -> list:
    c.execute(
        "SELECT id,code,lang,created_at FROM projects WHERE user_id=? ORDER BY id DESC LIMIT 10",
        (uid,),
    )
    return c.fetchall()


# ─── Stats ───────────────────────────────────────────────────
def inc_exec(uid: int):
    c.execute(
        "INSERT INTO stats(user_id,exec_count,ai_count) VALUES(?,1,0) "
        "ON CONFLICT(user_id) DO UPDATE SET exec_count=exec_count+1",
        (uid,),
    )
    conn.commit()


def inc_ai(uid: int):
    c.execute(
        "INSERT INTO stats(user_id,exec_count,ai_count) VALUES(?,0,1) "
        "ON CONFLICT(user_id) DO UPDATE SET ai_count=ai_count+1",
        (uid,),
    )
    conn.commit()


def get_stats(uid: int) -> tuple:
    c.execute("SELECT exec_count,ai_count FROM stats WHERE user_id=?", (uid,))
    r = c.fetchone()
    return (r[0], r[1]) if r else (0, 0)


def get_leaderboard() -> list:
    c.execute(
        """SELECT u.full_name, s.exec_count, s.ai_count
           FROM stats s JOIN users u ON s.user_id=u.user_id
           ORDER BY (s.exec_count + s.ai_count) DESC LIMIT 10"""
    )
    return c.fetchall()


# ─── Chat History ────────────────────────────────────────────
def save_chat(uid: int, role: str, msg: str):
    c.execute(
        "INSERT INTO chat_history(user_id,role,message,created_at) VALUES(?,?,?,?)",
        (uid, role, msg[:2000], datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()


def get_chat_history(uid: int, limit: int = 8) -> list:
    c.execute(
        "SELECT role,message FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (uid, limit),
    )
    return list(reversed(c.fetchall()))


def clear_chat_history(uid: int):
    c.execute("DELETE FROM chat_history WHERE user_id=?", (uid,))
    conn.commit()


# ─── Deployments ─────────────────────────────────────────────
def save_deployment(uid: int, url: str, name: str):
    c.execute(
        "INSERT INTO deployments(user_id,url,project_name,created_at) VALUES(?,?,?,?)",
        (uid, url, name, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()


def get_deployments(uid: int) -> list:
    c.execute(
        "SELECT url,project_name,created_at FROM deployments WHERE user_id=? ORDER BY id DESC LIMIT 5",
        (uid,),
    )
    return c.fetchall()


# ─── Message Map ─────────────────────────────────────────────
def save_message_map(admin_msg_id: int, user_id: int):
    c.execute(
        "INSERT OR REPLACE INTO message_map(admin_msg_id,user_id,created_at) VALUES(?,?,?)",
        (admin_msg_id, user_id, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()


def get_user_from_admin_msg(admin_msg_id: int):
    c.execute("SELECT user_id FROM message_map WHERE admin_msg_id=?", (admin_msg_id,))
    r = c.fetchone()
    return r[0] if r else None


# ─── Daily Challenges ────────────────────────────────────────
def get_challenge(today: str):
    c.execute("SELECT challenge FROM daily_challenges WHERE date=?", (today,))
    return c.fetchone()


def save_challenge(today: str, challenge: str):
    c.execute(
        "INSERT OR IGNORE INTO daily_challenges(date,challenge) VALUES(?,?)",
        (today, challenge),
    )
    conn.commit()

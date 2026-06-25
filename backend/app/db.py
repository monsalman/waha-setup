"""SQLite access. Single shared connection guarded by a lock (low-traffic admin tool)."""
import json
import sqlite3
import threading
from pathlib import Path

from .config import config

_lock = threading.RLock()
_conn: sqlite3.Connection | None = None


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        schema = (Path(__file__).parent / "schema.sql").read_text()
        conn.executescript(schema)
        conn.commit()
        _conn = conn
    return _conn


# init at import
_connect()


# ---------------- numbers ----------------

def upsert_number(phone, mode="agent", display_name=None):
    with _lock:
        _connect().execute(
            """
            INSERT INTO numbers (phone, mode, display_name, created_at, updated_at)
            VALUES (?, ?, ?, unixepoch(), unixepoch())
            ON CONFLICT(phone) DO UPDATE SET
              mode = excluded.mode,
              display_name = COALESCE(NULLIF(excluded.display_name, ''), numbers.display_name),
              updated_at = unixepoch()
            """,
            (phone, mode, display_name),
        )
        _connect().commit()
    return get_number(phone)


def get_number(phone):
    with _lock:
        row = _connect().execute("SELECT * FROM numbers WHERE phone = ?", (phone,)).fetchone()
    return dict(row) if row else None


def list_numbers():
    with _lock:
        rows = _connect().execute(
            "SELECT * FROM numbers ORDER BY (last_in_at IS NULL), last_in_at DESC, updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def set_mode(phone, mode):
    with _lock:
        cur = _connect().execute(
            "UPDATE numbers SET mode = ?, updated_at = unixepoch() WHERE phone = ?",
            (mode, phone),
        )
        _connect().commit()
        return cur.rowcount > 0


def delete_number(phone):
    with _lock:
        _connect().execute("DELETE FROM numbers WHERE phone = ?", (phone,))
        _connect().commit()


def bump_number_activity(phone, preview):
    with _lock:
        _connect().execute(
            """
            UPDATE numbers
            SET last_in_at = unixepoch(), last_msg_preview = ?, updated_at = unixepoch()
            WHERE phone = ?
            """,
            (str(preview or "")[:200], phone),
        )
        _connect().commit()


# ---------------- messages ----------------

def insert_message(*, waha_msg_id, phone, chat_id, direction, source,
                   body, has_media=0, media_url=None, raw_event=None) -> bool:
    """Idempotent insert. Returns True if a NEW row was inserted (False = duplicate)."""
    with _lock:
        cur = _connect().execute(
            """
            INSERT OR IGNORE INTO messages
              (waha_msg_id, phone, chat_id, direction, source, body, has_media, media_url, raw_event)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (waha_msg_id, phone, chat_id, direction, source, body,
             has_media, media_url, raw_event),
        )
        _connect().commit()
        return cur.rowcount > 0


def get_messages(phone, limit=50):
    with _lock:
        rows = _connect().execute(
            """
            SELECT id, direction, source, body, has_media, created_at
            FROM messages WHERE phone = ?
            ORDER BY created_at ASC LIMIT ?
            """,
            (phone, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_inbox():
    """Last inbound per HUMAN-mode number, with unread count (in after last out)."""
    with _lock:
        rows = _connect().execute(
            """
            SELECT n.phone, n.display_name, n.mode, n.last_in_at, n.last_msg_preview,
              (SELECT COUNT(*) FROM messages m
                 WHERE m.phone = n.phone AND m.direction = 'in'
                   AND m.created_at > COALESCE(
                     (SELECT MAX(m2.created_at) FROM messages m2
                      WHERE m2.phone = n.phone AND m2.direction = 'out'), 0)
              ) AS unread
            FROM numbers n
            WHERE n.mode = 'human'
            ORDER BY (n.last_in_at IS NULL), n.last_in_at DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------- events ----------------

def insert_event(*, event_id, event_type, session, payload):
    with _lock:
        _connect().execute(
            """
            INSERT INTO webhook_events (event_id, event_type, session, payload)
            VALUES (?, ?, ?, ?)
            """,
            (event_id, event_type, session, payload),
        )
        _connect().commit()


def recent_events(limit=100):
    with _lock:
        rows = _connect().execute(
            """
            SELECT id, event_id, event_type, session, received_at, payload
            FROM webhook_events ORDER BY received_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------- stats ----------------

def stats():
    with _lock:
        c = _connect()
        agent = c.execute("SELECT COUNT(*) c FROM numbers WHERE mode='agent'").fetchone()["c"]
        human = c.execute("SELECT COUNT(*) c FROM numbers WHERE mode='human'").fetchone()["c"]
        inbound = c.execute("SELECT COUNT(*) c FROM messages WHERE direction='in'").fetchone()["c"]
        events = c.execute("SELECT COUNT(*) c FROM webhook_events").fetchone()["c"]
    return {"agent": agent, "human": human, "inbound": inbound, "events": events}

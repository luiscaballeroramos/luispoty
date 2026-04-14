import sqlite3
from datetime import datetime

DB = "tracker.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()


# ---------------- UTILIDADES ----------------

def fmt_date(value):
    """Convierte datetime/string a formato limpio sin microsegundos"""
    if not value:
        return "-"
    try:
        if isinstance(value, str):
            value = value.split(".")[0]  # quita microsegundos
            return value
        return value.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(value)


def fmt(val, max_len=25):
    """Trunca texto largo para tabla horizontal"""
    s = str(val)
    return s[:max_len] + "..." if len(s) > max_len else s


def print_table(title, headers, rows):
    print("\n" + "=" * 120)
    print(f"📦 {title}")
    print("=" * 120)

    if not rows:
        print("Sin datos")
        return

    # imprimir headers
    header_line = " | ".join(h.ljust(18) for h in headers)
    print(header_line)
    print("-" * 120)

    # filas
    for r in rows:
        row = []
        for i, val in enumerate(r):
            if "date" in headers[i].lower() or "at" in headers[i].lower():
                val = fmt_date(val)
            row.append(fmt(val).ljust(18))

        print(" | ".join(row))


# ---------------- TABLAS ----------------

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cur.fetchall()]

print("\n🗂️ TABLAS DETECTADAS:")
print(tables)


# ---------------- TRACKS ----------------

if "tracks" in tables:
    cur.execute("""
        SELECT id, spotify_id, name, duration_ms, play_count, last_played_at
        FROM tracks
        ORDER BY play_count DESC, id ASC;
    """)

    rows = cur.fetchall()

    print_table(
        "TRACKS",
        ["id", "spotify_id", "name", "duration_ms", "play_count", "last_played_at"],
        rows
    )


# ---------------- EVENTS ----------------

if "listening_events" in tables:
    cur.execute("""
        SELECT track_id, started_at, ended_at, played_ms, is_skipped
        FROM listening_events
        ORDER BY started_at DESC;
    """)

    rows = cur.fetchall()

    print_table(
        "LISTENING EVENTS",
        ["track_id", "started_at", "ended_at", "played_ms", "skipped"],
        rows
    )


# ---------------- RAW POLLING (opcional) ----------------
if "raw_polling" in tables:
    cur.execute("""
        SELECT id, timestamp
        FROM raw_polling
        ORDER BY id DESC
        LIMIT 10;
    """)

    print_table(
        "RAW POLLING",
        ["id", "timestamp"],
        cur.fetchall()
    )


# ---------------- RECENT SYNC ----------------
if "recent_sync" in tables:
    cur.execute("""
        SELECT last_played_at
        FROM recent_sync;
    """)

    print_table(
        "RECENT SYNC",
        ["last_played_at"],
        cur.fetchall()
    )


conn.close()

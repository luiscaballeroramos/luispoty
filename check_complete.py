import sqlite3
from datetime import datetime

# DB = "combined_databases.db"
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

    # formatear datos primero
    formatted_rows = []
    for r in rows:
        new_row = []
        for i, val in enumerate(r):
            if "date" in headers[i].lower() or "at" in headers[i].lower():
                val = fmt_date(val)
            val = fmt(val)
            new_row.append(val)
        formatted_rows.append(new_row)

    # calcular ancho por columna
    col_widths = []
    for i in range(len(headers)):
        max_len = max(
            len(str(headers[i])), max(len(str(row[i])) for row in formatted_rows)
        )
        col_widths.append(max_len + 2)  # padding

    # imprimir headers
    header_line = " | ".join(
        headers[i].ljust(col_widths[i]) for i in range(len(headers))
    )
    print(header_line)
    print("-" * len(header_line))

    # imprimir filas
    for row in formatted_rows:
        line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
        print(line)


# ---------------- TABLAS ----------------

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cur.fetchall()]

print("\n🗂️ TABLAS DETECTADAS:")
print(tables, "\n")


# ---------------- TRACKS ----------------

if "tracks" in tables:
    cur.execute(
        """
        SELECT id, spotify_id, name, duration_ms, play_count, last_played_at
        FROM tracks
        ORDER BY name ASC;
    """
    )

    rows = cur.fetchall()

    print_table(
        "TRACKS",
        ["id", "spotify_id", "name", "duration_ms", "play_count", "last_played_at"],
        rows,
    )
    print(f'Number of tracks: {cur.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]}')


# ---------------- EVENTS ----------------

if "listening_events" in tables:
    cur.execute("""
            SELECT
                t.name,
                le.started_at,
                le.played_ms,
                le.is_skipped,
                le.source
            FROM listening_events le
            JOIN tracks t ON le.track_id = t.id
            ORDER BY le.started_at DESC
            LIMIT 15;
        """)
    rows = cur.fetchall()
    print_table(
        "LISTENING EVENTS",
        ["Name", "Started At", "Played (ms)", "Skipped", "Source"],
        rows,
    )
    print(f'Number of events: {cur.execute("SELECT COUNT(*) FROM listening_events").fetchone()[0]}')


# ---------------- RAW POLLING (opcional) ----------------
if "raw_polling" in tables:
    cur.execute(
        """
        SELECT id, timestamp
        FROM raw_polling
        ORDER BY id DESC
        LIMIT 5;
    """
    )

    print_table("RAW POLLING", ["id", "timestamp"], cur.fetchall())
    print(f'Number of raw polling entries: {cur.execute("SELECT COUNT(*) FROM raw_polling").fetchone()[0]}')


# ---------------- RECENT SYNC ----------------
if "recent_sync" in tables:
    cur.execute(
        """
        SELECT last_played_at
        FROM recent_sync;
    """
    )

    print_table("RECENT SYNC", ["last_played_at"], cur.fetchall())
    print(f'Number of recent sync entries: {cur.execute("SELECT COUNT(*) FROM recent_sync").fetchone()[0]}')


conn.close()

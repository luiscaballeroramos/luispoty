import sqlite3
from datetime import datetime

conn = sqlite3.connect("tracker.db")
cur = conn.cursor()

# ---------- COUNT ----------
cur.execute("SELECT COUNT(*) FROM listening_events;")
total = cur.fetchone()[0]

print("\n📊 LISTENING EVENTS")
print("-" * 40)
print(f"Total eventos: {total}\n")

# ---------- LAST EVENTS ----------
cur.execute("""
SELECT track_id, started_at, ended_at, played_ms, is_skipped
FROM listening_events
ORDER BY started_at DESC
LIMIT 10;
""")

rows = cur.fetchall()

print("🎧 Últimos eventos:\n")

for i, r in enumerate(rows, 1):
    track_id, start, end, ms, skipped = r

    print(f"[{i}] Track: {track_id}")
    print(f"    Inicio : {start}")
    print(f"    Fin    : {end}")
    print(f"    Duración: {ms/1000:.1f}s")
    print(f"    Skip   : {'Sí' if skipped else 'No'}")
    print("-" * 40)

import sqlite3

conn = sqlite3.connect("tracker.db")
cur = conn.cursor()

# añadir columnas (seguro aunque ya existan en futuro)
try:
    cur.execute("ALTER TABLE tracks ADD COLUMN play_count INTEGER DEFAULT 0;")
except Exception as e:
    print("play_count ya existe o error:", e)

try:
    cur.execute("ALTER TABLE tracks ADD COLUMN last_played_at TEXT;")
except Exception as e:
    print("last_played_at ya existe o error:", e)

conn.commit()
conn.close()


import sqlite3
from datetime import datetime

DB = "tracker.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# fecha fija
fixed_date = "1993-03-25 00:00:00"

# update masivo
cur.execute("""
UPDATE tracks
SET play_count = 1,
    last_played_at = ?
""", (fixed_date,))

conn.commit()

# verificación
cur.execute("SELECT id, name, play_count, last_played_at FROM tracks LIMIT 10;")
rows = cur.fetchall()

print("\n✔ ACTUALIZACIÓN COMPLETA\n")
for r in rows:
    print(r)

conn.close()

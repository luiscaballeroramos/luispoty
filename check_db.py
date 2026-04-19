import sqlite3
import os

dbs = ["tracker copy.db", "tracker.db", "tracker_2.db", "combined.db"]
for db in dbs:
    if os.path.exists(db):
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"{db}: Tables: {tables}")
        if tables:
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  {table[0]}: {count} rows")
        conn.close()
    else:
        print(f"{db}: does not exist")

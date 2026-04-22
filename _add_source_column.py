import sqlite3

def migrate_combined_db():
    conn = sqlite3.connect("combine_databases.db")
    cur = conn.cursor()

    print("🛠️ Añadiendo columna 'source' a combine_databases.db...")

    try:
        cur.execute("ALTER TABLE listening_events ADD COLUMN source TEXT DEFAULT 'polling';")
        conn.commit()
        print("✅ Columna 'source' añadida a listening_events.")
    except sqlite3.OperationalError as e:
        print(f"⚠️ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_combined_db()

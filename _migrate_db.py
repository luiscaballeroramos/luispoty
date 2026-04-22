import sqlite3

def migrate():
    conn = sqlite3.connect("tracker.db")
    cur = conn.cursor()

    print("🛠️ Iniciando migración...")

    # 1. Añadir columna source a listening_events
    try:
        cur.execute("ALTER TABLE listening_events ADD COLUMN source TEXT DEFAULT 'polling';")
        print("✅ Columna 'source' añadida.")
    except sqlite3.OperationalError:
        print("⚠️ La columna 'source' ya existe.")

    # 2. Crear el índice compuesto para la deduplicación
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS ix_track_start ON listening_events (track_id, started_at);")
        print("✅ Índice 'ix_track_start' creado.")
    except Exception as e:
        print(f"❌ Error creando índice: {e}")

    conn.commit()
    conn.close()
    print("🚀 Migración finalizada.")

if __name__ == "__main__":
    migrate()

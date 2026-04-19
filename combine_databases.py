import os
import sqlite3
import glob
from collections import defaultdict


def get_table_structure(db_path, table_name):
    """Obtiene la estructura de la tabla (columnas y tipos)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    conn.close()
    return [(col[1], col[2]) for col in columns]  # (name, type)


def get_all_tables(db_path):
    """Obtiene todas las tablas en la base de datos."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def merge_rows(existing_row, new_row, column_types):
    """Fusiona dos filas: max para integers, max para fechas."""
    merged = []
    for i, (existing_val, new_val) in enumerate(zip(existing_row, new_row)):
        col_type = column_types[i][1].upper()
        if col_type in ("INTEGER", "INT", "REAL", "FLOAT"):
            # Intentar convertir a float para comparar
            try:
                existing_num = float(existing_val) if existing_val is not None else None
                new_num = float(new_val) if new_val is not None else None
                if existing_num is not None and new_num is not None:
                    merged.append(max(existing_num, new_num))
                else:
                    merged.append(existing_num or new_num)
            except (ValueError, TypeError):
                merged.append(existing_val or new_val)
        elif "DATE" in col_type or "TIME" in col_type:
            # Asumiendo formato comparable, tomar el más reciente
            if existing_val and new_val:
                try:
                    merged.append(max(existing_val, new_val))
                except TypeError:
                    merged.append(
                        existing_val
                    )  # Mantener el existente si no comparable
            else:
                merged.append(existing_val or new_val)
        else:
            # Para otros tipos, mantener el existente o nuevo
            merged.append(existing_val or new_val)
    return tuple(merged)


def combine_databases(db_files, output_db):
    if not db_files:
        print("No se encontraron archivos .db")
        return

    # Usar la primera db como referencia
    reference_db = db_files[0]
    all_tables = get_all_tables(reference_db)
    if not all_tables:
        print("No hay tablas en la base de datos de referencia")
        return

    # Verificar que todas las db tengan las mismas tablas y estructuras
    for db_file in db_files[1:]:
        tables_check = get_all_tables(db_file)
        if set(tables_check) != set(all_tables):
            print(f"Las tablas en {db_file} no coinciden con la de referencia")
            return
        for table in all_tables:
            structure_check = get_table_structure(db_file, table)
            reference_structure = get_table_structure(reference_db, table)
            if structure_check != reference_structure:
                print(
                    f"Estructura de {table} en {db_file} no coincide con la de referencia"
                )
                return

    # Crear nueva db
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()

    for table in all_tables:
        reference_structure = get_table_structure(reference_db, table)

        # Leer datos de todas las db para esta tabla
        data_by_id = defaultdict(list)
        id_column_index = 0  # Asumir que la primera columna es el id

        for db_file in db_files:
            conn_read = sqlite3.connect(db_file)
            cursor_read = conn_read.cursor()
            cursor_read.execute(f"SELECT * FROM {table}")
            rows = cursor_read.fetchall()
            for row in rows:
                data_by_id[row[id_column_index]].append(row)
            conn_read.close()

        # Combinar filas con mismo id
        combined_data = []
        for id_val, rows in data_by_id.items():
            if len(rows) == 1:
                combined_data.append(rows[0])
            else:
                # Fusionar múltiples filas
                merged_row = rows[0]
                for row in rows[1:]:
                    merged_row = merge_rows(merged_row, row, reference_structure)
                combined_data.append(merged_row)

        # Eliminar tabla si existe
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

        # Crear tabla
        columns_def = ", ".join(
            [f"{name} {type_}" for name, type_ in reference_structure]
        )
        cursor.execute(f"CREATE TABLE {table} ({columns_def})")

        # Insertar datos
        placeholders = ", ".join(["?"] * len(reference_structure))
        cursor.executemany(
            f"INSERT INTO {table} VALUES ({placeholders})", combined_data
        )

    conn.commit()
    conn.close()
    print(f"Base de datos combinada guardada en {output_db}")


if __name__ == "__main__":
    # Encontrar todos los archivos .db en el directorio actual, excluyendo el output
    output_db = "combine_databases.db"
    db_files = [f for f in glob.glob("*.db") if f != output_db]
    combine_databases(db_files, output_db)

import os

# Configuración
ROOT_DIR = "."
OUTPUT_FILE = "_repo_dump.txt"
EXTENSIONS = [".py", ".md", ".json"]

EXCLUDE_DIRS = {".git", "venv", "__pycache__"}


def should_include_file(filename):
    return any(filename.endswith(ext) for ext in EXTENSIONS)


def generate_dump():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for root, dirs, files in os.walk(ROOT_DIR):
            # excluir carpetas
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if should_include_file(file):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                    except Exception as e:
                        content = f"[ERROR LEYENDO ARCHIVO: {e}]"
                    relative_path = os.path.relpath(filepath, ROOT_DIR)
                    out.write(f"\n===== {relative_path} =====\n")
                    out.write(content)
                    out.write("\n")
    print(f"Dump generado en: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_dump()

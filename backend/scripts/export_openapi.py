import os
import sys
import json
import tempfile

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

# Set temporary database path to avoid polluting real DB
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["FS_DATABASE_PATH"] = temp_db.name

try:
    from app.main import app
    openapi_schema = app.openapi()

    frontend_gen_dir = os.path.abspath(os.path.join(backend_dir, "../frontend/src/types/generated"))
    os.makedirs(frontend_gen_dir, exist_ok=True)

    output_path = os.path.join(frontend_gen_dir, "openapi.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"OpenAPI schema exported to {output_path}")
finally:
    temp_db.close()
    try:
        os.unlink(temp_db.name)
    except Exception:
        pass

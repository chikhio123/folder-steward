from backend.app.core.database import get_connection

conn = get_connection()
rows = conn.execute("SELECT id, name, rule_type FROM rules").fetchall()
for r in rows:
    print(dict(r))

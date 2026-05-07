# The backend is running in the background of the previous bash command, but output is streamed.
# Wait, let's just query the DB for the results!
import sqlite3
conn = sqlite3.connect('C:/Users/lu/AppData/Roaming/folder-steward-frontend/folder_steward.db')
rows = conn.execute("SELECT suggested_target_dir, reason FROM ai_classification_suggestions WHERE status='pending' LIMIT 5").fetchall()
for r in rows:
    print(r)

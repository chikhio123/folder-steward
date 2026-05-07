import sqlite3

conn = sqlite3.connect('C:/Users/lu/AppData/Roaming/folder-steward-frontend/folder_steward.db')
cursor = conn.cursor()

# Get all duplicate groups based on sha256 AND filename
cursor.execute('''
    SELECT sha256, filename, size_bytes, COUNT(*) as cnt
    FROM file_records
    WHERE status='active' AND sha256 IS NOT NULL
    GROUP BY sha256, filename
    HAVING COUNT(*) > 1
    ORDER BY size_bytes DESC
''')
groups = cursor.fetchall()
print(f"Found {len(groups)} groups")

for g in groups[:2]:
    print(g)
    cursor.execute("SELECT id, filename, current_path FROM file_records WHERE sha256 = ? AND filename = ?", (g[0], g[1]))
    for f in cursor.fetchall():
        print(f"  - {f}")

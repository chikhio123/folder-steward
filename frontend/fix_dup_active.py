import re

with open("D:/Code/Folder Steward/backend/app/repositories/file_repository.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "\"SELECT id, filename, current_path, modified_at FROM file_records WHERE sha256 = ? AND filename = ? ORDER BY id\",",
    "\"SELECT id, filename, current_path, modified_at FROM file_records WHERE sha256 = ? AND filename = ? AND status = 'active' ORDER BY id\","
)

with open("D:/Code/Folder Steward/backend/app/repositories/file_repository.py", "w", encoding="utf-8") as f:
    f.write(content)

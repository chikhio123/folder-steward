with open("D:/Code/Folder Steward/start.bat", "r", encoding="utf-8-sig") as f:
    content = f.read()

content = content.replace("(PID %%a)", "[PID %%a]")

with open("D:/Code/Folder Steward/start.bat", "w", encoding="utf-8") as f:
    f.write(content)

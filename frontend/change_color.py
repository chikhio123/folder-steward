import os
import glob

# Find all tsx files
files = glob.glob("D:/Code/Folder Steward/frontend/src/**/*.tsx", recursive=True)

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "sky" in content:
        # Replace all sky variants with blue
        new_content = content.replace("sky", "blue")
        with open(file, "w", encoding="utf-8") as f:
            f.write(new_content)
            
print("Color changed from sky to blue in all TSX files.")

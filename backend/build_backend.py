import os
import subprocess

backend_dir = os.path.dirname(os.path.abspath(__file__))
frontend_bin_dir = os.path.join(backend_dir, "../frontend/backend-bin")

os.makedirs(frontend_bin_dir, exist_ok=True)

subprocess.run([
    "pyinstaller",
    "--name=folder-steward-backend",
    "--onefile",
    "--clean",
    "--noconfirm",
    "--distpath", frontend_bin_dir,
    "--workpath", os.path.join(backend_dir, "build"),
    "--specpath", backend_dir,
    # Need to include all app dependencies
    "--hidden-import=app",
    "--hidden-import=app.main",
    "--hidden-import=app.api",
    "--hidden-import=app.core",
    "--hidden-import=app.models",
    "--hidden-import=app.repositories",
    "--hidden-import=app.schemas",
    "--hidden-import=app.services",
    "run_backend.py"
], cwd=backend_dir, check=True)

exe_path = os.path.join(frontend_bin_dir, "folder-steward-backend.exe")
if not os.path.exists(exe_path):
    print(f"Error: Executable not found at {exe_path}")
    exit(1)
print(f"Build successful: {exe_path}")

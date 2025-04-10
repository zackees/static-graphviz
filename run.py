import os
import subprocess
from pathlib import Path
import sys
import platform

def run(cmd: str) -> int:
    print(f"Running: {cmd}")
    return subprocess.call(cmd, shell=True)

def is_windows() -> bool:
    return platform.system().lower() == "windows"

# Define directories
project_root = Path(__file__).resolve().parent
docker_dir = project_root / "docker"
bins_dir = project_root / "bins"

# Ensure bins directory exists
bins_dir.mkdir(parents=True, exist_ok=True)

# Convert path for Docker volume mount
docker_mount_path = bins_dir.resolve()

# On Windows, convert to Docker-compatible POSIX path
if is_windows():
    # Docker on Windows expects /c/Users/... rather than C:\Users\...
    docker_mount_path_str = "/" + str(docker_mount_path).replace(":", "").replace("\\", "/")
else:
    docker_mount_path_str = str(docker_mount_path)

# Step 1: Build the Docker image
os.chdir(docker_dir)
if run("docker build -t graphviz-static .") != 0:
    sys.exit("❌ Docker build failed.")

# Step 2: Run the image normally
run("docker run --rm graphviz-static")

# Step 3: Run to check version
run("docker run --rm graphviz-static dot -V")

# Step 4: Copy the built binary out via volume mount
copy_command = f'docker run --rm -v "{docker_mount_path_str}:/out" graphviz-static cp /usr/local/bin/dot /out/dot'
if run(copy_command) != 0:
    sys.exit("❌ Failed to copy dot binary out of container.")

# Step 5: Confirm the file exists
dot_binary = bins_dir / "dot"
if dot_binary.exists():
    print(f"✅ dot binary copied to: {dot_binary}")
else:
    sys.exit("❌ dot binary not found.")

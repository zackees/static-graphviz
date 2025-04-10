"""

To shell into the container:
  docker run -it --rm -t graphviz-dl bash

"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()
PROJECT_ROOT = HERE.parent.parent
BINS = PROJECT_ROOT / "bins"

def build_docker_image():
    print("Building Docker image 'graphviz-dl'...")
    try:
        subprocess.run([
            "docker", "build",
            # "--no-cache",  # always build from scratch, you should not have to use chache unless you are debugging
            "--progress=plain",
            "-t", "graphviz-dl",
            "."
        ], check=True, cwd=str(HERE))
        print("Docker image built successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to build Docker image: {e}", file=sys.stderr)
        sys.exit(e.returncode)

def run_graphviz_dl_container():
    # Use current working directory
    host_dir = BINS

    # Convert to Docker-friendly path if on Windows
    if os.name == 'nt':
        docker_path = f"/{host_dir.drive[0].lower()}{host_dir.as_posix()[2:]}"
    else:
        docker_path = str(host_dir)

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{docker_path}:/host",
        "graphviz-dl"
    ]

    print(f"Running Docker container:\n{' '.join(docker_cmd)}")

    try:
        subprocess.run(docker_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Docker container: {e}", file=sys.stderr)
        sys.exit(e.returncode)

if __name__ == "__main__":
    build_docker_image()
    run_graphviz_dl_container()

"""
Entry point for running the ffmpeg executable.
"""

import os
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import requests  # type: ignore
from filelock import FileLock, Timeout
from progress.bar import Bar  # type: ignore
from progress.spinner import Spinner


class CustomBar(Bar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = sys.stderr  # or use any stream-like object


class CustomSpinner(Spinner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = sys.stderr


TIMEOUT = 10 * 60  # Wait upto 10 minutes to validate install
# otherwise break the lock and install anyway.

SELF_DIR = os.path.abspath(os.path.dirname(__file__))
LOCK_FILE = os.path.join(SELF_DIR, "lock.file")

PLATFORM_ZIP_FILES = {
    "win32": "https://github.com/zackees/static-graphviz/raw/refs/heads/main/bins/windows_10_cmake_Release_Graphviz-12.2.1-win32.zip",
    # "darwin": "NOT VALID YET",  # HELP WANTED
    # "linux": "http://archive.ubuntu.com/ubuntu/pool/universe/g/graphviz/graphviz_2.42.2-3build2_amd64.deb",  # Help wanted
}


def check_system() -> None:
    """Friendly error if there's a problem with the system configuration."""
    if sys.platform not in PLATFORM_ZIP_FILES:
        raise OSError(f"Please implement static_ffmpeg for {sys.platform}")


def get_platform_http_zip() -> str:
    """Return the download link for the current platform"""
    check_system()
    return PLATFORM_ZIP_FILES[sys.platform]


def get_platform_dir() -> str:
    """Either get the executable or raise an error"""
    check_system()
    return os.path.join(SELF_DIR, "bin", sys.platform)


def download_file(url: str, local_path: str) -> str:
    """Downloads a file to the give path."""

    print_stderr(f"Downloading {url} -> {local_path}")
    chunk_size = (1024 * 1024) // 4
    with requests.get(url, stream=True, timeout=TIMEOUT) as req:
        req.raise_for_status()
        spin: CustomSpinner | CustomBar = CustomSpinner("graphviz: ")
        size = -1
        try:
            size = int(req.headers.get("content-length", 0))
            spin = CustomBar(
                "graphviz: ", max=size, suffix="%(percent).1f%% - %(eta)ds"
            )
        except ValueError:
            pass
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as file_d:
            with spin as spin:
                for chunk in req.iter_content(chunk_size):
                    file_d.write(chunk)
                    spin.next(len(chunk))
            sys.stderr.write(f"\nDownload of {url} -> {local_path} completed.\n")
            sys.stderr.flush()
    return local_path


def extract_dot_from_deb(deb_path: str, extract_to: str) -> Path:
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["ar", "x", deb_path], cwd=tmpdir, check=True)
        data_files = [f for f in os.listdir(tmpdir) if f.startswith("data.tar")]
        if not data_files:
            raise FileNotFoundError("No data.tar.* found in deb package.")
        data_file = os.path.join(tmpdir, data_files[0])
        with tarfile.open(data_file) as tar:
            tar.extractall(path=extract_to)

    # Search for 'dot' binary
    for root, _, files in os.walk(extract_to):
        if "dot" in files:
            return Path(root) / "dot"

    raise FileNotFoundError(f"'dot' not found after extracting {deb_path}")


def install_graphviz_from_deb_linux(deb_url: str, exe_dir: str) -> Path:
    """Download and extract Graphviz .deb file to non-root location."""
    deb_path = os.path.join(exe_dir, "graphviz.deb")
    os.makedirs(os.path.dirname(deb_path), exist_ok=True)
    download_file(deb_url, deb_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract the .deb using 'ar'
        subprocess.run(["ar", "x", deb_path], cwd=tmpdir, check=True)

        # Find data.tar.* file
        data_files = [f for f in os.listdir(tmpdir) if f.startswith("data.tar")]
        if not data_files:
            raise FileNotFoundError("No data.tar.* file found in .deb")
        data_file = os.path.join(tmpdir, data_files[0])

        # Extract the data.tar.* archive
        with tarfile.open(data_file) as tar:
            tar.extractall(path=exe_dir)

    # ✅ Use robust search logic instead of assuming fixed layout
    dot_path = _search_for_dot_exe(str(exe_dir))

    # ✅ Only chmod AFTER confirming the path exists
    # dot_path.chmod(dot_path.stat().st_mode | stat.S_IEXEC)
    return dot_path


def _search_for_dot_exe(exe_dir: str) -> Path:
    for root, _, files in os.walk(exe_dir):
        for file in files:
            if file in ["dot", "dot.exe"]:
                return Path(root) / file
    raise FileNotFoundError(f"dot executable not found in {exe_dir}")


def print_stderr(*args, **kwargs) -> None:
    sys.stderr.write(f"{__file__}: ")
    print(*args, file=sys.stderr, **kwargs)
    sys.stderr.flush()


def _get_or_fetch_platform_executables_else_raise_no_lock(
    fix_permissions=True, download_dir: str | None = None
) -> Path:
    exe_dir = Path(download_dir if download_dir else get_platform_dir())
    installed_crumb = exe_dir / "installed.crumb"

    if not installed_crumb.exists():
        install_dir = exe_dir.parent
        install_dir.mkdir(parents=True, exist_ok=True)

        if sys.platform == "linux":
            _ = install_graphviz_from_deb_linux(get_platform_http_zip(), exe_dir)
        else:
            url = get_platform_http_zip()
            local_archive = str(exe_dir) + ".zip"
            download_file(url, local_archive)
            print_stderr(f"Extracting {local_archive} -> {install_dir}")
            with zipfile.ZipFile(local_archive, mode="r") as zipf:
                zipf.extractall(install_dir)
            os.remove(local_archive)
            _ = _search_for_dot_exe(str(install_dir))

        os.makedirs(os.path.dirname(installed_crumb), exist_ok=True)
        with open(installed_crumb, "w") as f:
            f.write(f"Installed from {get_platform_http_zip()} on {datetime.now()}")

    dot_exe = _search_for_dot_exe(str(exe_dir.parent))

    if sys.platform == "linux":
        ld_path = str(dot_exe.parent)
        prev_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        if ld_path not in prev_ld_path:
            full_path = f"{ld_path}" + (":" + prev_ld_path if prev_ld_path else "")
            os.environ["LD_LIBRARY_PATH"] = full_path

    if fix_permissions and sys.platform != "win32":
        exe_bits = stat.S_IXOTH | stat.S_IXUSR | stat.S_IXGRP
        read_bits = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        os.chmod(dot_exe, exe_bits | read_bits)
        assert os.access(dot_exe, os.X_OK)
        assert os.access(dot_exe, os.R_OK)
        try:
            print_stderr(f"Running: {dot_exe} -c")
            subprocess.run([str(dot_exe), "-c"], check=True)
        except Exception as e:
            print_stderr(f"Warning: failed to run '{dot_exe} -c': {e}")

    return dot_exe


def get_or_fetch_platform_executables_else_raise(
    fix_permissions=True, download_dir=None
) -> Path:
    lock = FileLock(LOCK_FILE, timeout=TIMEOUT)
    try:
        with lock.acquire():
            return _get_or_fetch_platform_executables_else_raise_no_lock(
                fix_permissions=fix_permissions, download_dir=download_dir
            )
    except Timeout:
        sys.stderr.write(
            f"{__file__}: Warning, could not acquire lock at {LOCK_FILE}\n"
        )
        return _get_or_fetch_platform_executables_else_raise_no_lock(
            fix_permissions=fix_permissions, download_dir=download_dir
        )

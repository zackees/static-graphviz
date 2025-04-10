"""
add_paths() Adds ffmpeg and ffprobe to the path, overriding any system ffmpeg/ffprobe.
"""

import os
import shutil
import sys

from .run import get_or_fetch_platform_executables_else_raise


def _has(name: str) -> bool:
    """Check if the path has the name"""
    return shutil.which(name) is not None


def add_paths(weak=False, download_dir=None) -> bool:
    """Add the ffmpeg executable to the path"""
    if getattr(sys, "frozen", False):
        sys.stdout = sys.stderr  # support frozen apps like pyinstaller
    if weak:
        has_dot = _has("dot")
        if has_dot:
            return False
    dot = get_or_fetch_platform_executables_else_raise(download_dir=download_dir)
    dot_path = os.path.dirname(dot)
    if dot_path not in os.environ["PATH"]:
        os.environ["PATH"] = os.pathsep.join([dot_path, os.environ["PATH"]])
    return True

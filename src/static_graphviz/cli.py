import subprocess
import sys

from static_graphviz.run import get_or_fetch_platform_executables_else_raise


def main_static_dot() -> None:
    """Entry point for running static_ffmpeg, which delegates to ffmpeg."""
    dot_exe = get_or_fetch_platform_executables_else_raise()
    rtn: int = subprocess.call([str(dot_exe)] + sys.argv[1:])
    sys.exit(rtn)


def main_print_paths() -> None:
    """Entry point for printing ffmpeg paths"""
    dot_exe = get_or_fetch_platform_executables_else_raise()
    print(f"DOT={dot_exe}")
    sys.exit(0)


if __name__ == "__main__":
    get_or_fetch_platform_executables_else_raise()

"""
Build script for Computer Lockdown.

Creates a single-file Windows executable using PyInstaller with UAC admin
elevation, all required hidden imports, and bundled data directories.

Usage::

    python build.py            # standard build
    python build.py --debug    # include console window for debugging
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

# Project root (same directory as this script).
PROJECT_ROOT: Path = Path(__file__).resolve().parent


def _clean_build_artefacts() -> None:
    """Remove previous ``build/`` and ``dist/`` directories."""
    for folder_name in ("build", "dist"):
        folder = PROJECT_ROOT / folder_name
        if folder.exists():
            print(f"  Removing {folder} ...")
            shutil.rmtree(folder)

    spec_file = PROJECT_ROOT / "ComputerLockdown.spec"
    if spec_file.exists():
        spec_file.unlink()
        print(f"  Removed {spec_file}")


def _resolve_separator() -> str:
    """Return the PyInstaller ``--add-data`` separator for the current OS.

    Windows uses ``;``, everything else uses ``:``.
    """
    return ";" if sys.platform == "win32" else ":"


def build(*, debug: bool = False) -> None:
    """Run PyInstaller to produce ``dist/ComputerLockdown.exe``.

    Parameters
    ----------
    debug:
        When ``True`` the executable is built **with** a console window
        attached so that ``print`` / logging output is visible.
    """
    try:
        import PyInstaller.__main__  # noqa: F401
    except ImportError:
        print(
            "ERROR: PyInstaller is not installed.\n"
            "       Install it with:  pip install pyinstaller>=6.0.0",
            file=sys.stderr,
        )
        sys.exit(1)

    print("=== Computer Lockdown — Build ===\n")

    # 1. Clean previous artefacts
    print("[1/3] Cleaning previous build artefacts...")
    _clean_build_artefacts()

    # 2. Assemble PyInstaller arguments
    sep: str = _resolve_separator()

    pyinstaller_args: list[str] = [
        str(PROJECT_ROOT / "run.py"),
        f"--name=ComputerLockdown",
        "--onefile",
        # Data directories
        f"--add-data=config{sep}config",
        f"--add-data=assets{sep}assets",
        # Hidden imports that PyInstaller may not detect automatically
        "--hidden-import=customtkinter",
        "--hidden-import=pystray",
        "--hidden-import=PIL",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=bcrypt",
        "--hidden-import=psutil",
        "--hidden-import=watchdog",
        "--hidden-import=watchdog.observers",
        "--hidden-import=watchdog.events",
    ]

    # Icon (only add if the file actually exists)
    icon_path: Path = PROJECT_ROOT / "assets" / "icon.ico"
    if icon_path.exists():
        pyinstaller_args.append(f"--icon={icon_path}")
    else:
        print(
            f"  WARNING: Icon file not found at {icon_path}.\n"
            "           The executable will use the default Python icon.\n"
            "           Place an .ico file at assets/icon.ico to customise it."
        )

    # Console / windowed mode
    if debug:
        pyinstaller_args.append("--console")
        print("  Mode: DEBUG (console window enabled)")
    else:
        pyinstaller_args.append("--windowed")
        pyinstaller_args.append("--noconsole")
        print("  Mode: RELEASE (no console window)")

    # Request UAC elevation on Windows
    if sys.platform == "win32":
        pyinstaller_args.append("--uac-admin")

    # 3. Run PyInstaller
    print("\n[2/3] Running PyInstaller...\n")
    import PyInstaller.__main__

    PyInstaller.__main__.run(pyinstaller_args)

    # 4. Report results
    exe_path: Path = PROJECT_ROOT / "dist" / "ComputerLockdown.exe"
    alt_path: Path = PROJECT_ROOT / "dist" / "ComputerLockdown"  # Unix (no .exe)

    print("\n[3/3] Build complete!")

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  Executable: {exe_path}  ({size_mb:.1f} MB)")
    elif alt_path.exists():
        size_mb = alt_path.stat().st_size / (1024 * 1024)
        print(f"  Executable: {alt_path}  ({size_mb:.1f} MB)")
    else:
        print("  WARNING: Executable not found — check the PyInstaller output above.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Computer Lockdown into a standalone executable.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Build with a console window for debugging output.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    build(debug=args.debug)

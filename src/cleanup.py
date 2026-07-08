"""
Full cleanup / factory reset for Computer Lockdown.

Removes ALL traces of the application:
- Config files and HMAC signatures
- Log files
- Quarantined downloads
- Windows Firewall rules (DoH blocks)
- Registry policies
- Instance lock file

Usage:
    ComputerLockdown.exe --reset
"""

import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _get_config_dir() -> Path:
    """Return the config directory path."""
    if platform.system() == "Windows":
        programdata = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        return Path(programdata) / "ComputerLockdown"
    else:
        return Path.home() / ".config" / "ComputerLockdown"


def _remove_dir(path: Path, label: str) -> None:
    """Remove a directory and print status."""
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
        print(f"  [OK] Removed {label}: {path}")
    else:
        print(f"  [--] Not found: {path}")


def _remove_file(path: Path, label: str) -> None:
    """Remove a single file and print status."""
    if path.exists():
        try:
            path.unlink()
            print(f"  [OK] Removed {label}: {path}")
        except OSError as e:
            print(f"  [!!] Failed to remove {label}: {e}")
    else:
        print(f"  [--] Not found: {path}")


def _remove_firewall_rules() -> None:
    """Remove any Windows Firewall rules created by the app."""
    if platform.system() != "Windows":
        print("  [--] Not Windows, skipping firewall cleanup")
        return
    try:
        result = subprocess.run(
            ["netsh", "advfirewall", "firewall", "delete", "rule",
             "name=ComputerLockdown_BlockDoH"],
            capture_output=True, timeout=10,
        )
        if result.returncode == 0:
            print("  [OK] Removed DoH firewall rules")
        else:
            print("  [--] No DoH firewall rules found")
    except Exception as e:
        print(f"  [!!] Firewall cleanup failed: {e}")


def _remove_registry_policies() -> None:
    """Remove any registry policies set by the app."""
    if platform.system() != "Windows":
        print("  [--] Not Windows, skipping registry cleanup")
        return

    import winreg

    policies = [
        (r"Software\Microsoft\Windows\CurrentVersion\Policies\System", "DisableTaskMgr"),
        (r"Software\Policies\Microsoft\Windows\System", "DisableCMD"),
        (r"Software\Microsoft\Windows\CurrentVersion\Policies\System", "DisableRegistryTools"),
        (r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoControlPanel"),
        (r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoSettings"),
    ]

    for key_path, value_name in policies:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, value_name)
            winreg.CloseKey(key)
            print(f"  [OK] Removed registry: {value_name}")
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"  [!!] Registry cleanup failed for {value_name}: {e}")

    print("  [OK] Registry policies cleaned")


def _remove_hosts_entries() -> None:
    """Remove any hosts file entries added by the app."""
    if platform.system() != "Windows":
        hosts_path = Path("/etc/hosts")
    else:
        hosts_path = Path(r"C:\Windows\System32\drivers\etc\hosts")

    if not hosts_path.exists():
        return

    try:
        lines = hosts_path.read_text(encoding="utf-8").splitlines()
        marker = "# ComputerLockdown"
        cleaned = [line for line in lines if marker not in line]

        if len(cleaned) < len(lines):
            hosts_path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
            print(f"  [OK] Cleaned hosts file ({len(lines) - len(cleaned)} entries removed)")
        else:
            print("  [--] No entries in hosts file")
    except PermissionError:
        print("  [!!] Cannot edit hosts file - run as Administrator")
    except Exception as e:
        print(f"  [!!] Hosts cleanup failed: {e}")


def _remove_lock_file() -> None:
    """Remove the single-instance lock file."""
    lock_path = Path(tempfile.gettempdir()) / "computer_lockdown.lock"
    _remove_file(lock_path, "instance lock")


def full_cleanup() -> None:
    """Perform a complete factory reset - remove all traces of the app."""
    print("=" * 50)
    print("  Computer Lockdown - Full Cleanup / Factory Reset")
    print("=" * 50)
    print()

    config_dir = _get_config_dir()

    # Config and signature files
    print("[1/6] Config files...")
    _remove_file(config_dir / "config.json", "config")
    _remove_file(config_dir / "config.json.sig", "config signature")
    _remove_file(config_dir / "config.tmp", "config temp")

    # Logs
    print("\n[2/6] Log files...")
    _remove_file(config_dir / "lockdown.log", "main log")
    _remove_file(config_dir / "lockdown.log.1", "log backup 1")
    _remove_file(config_dir / "lockdown.log.2", "log backup 2")
    _remove_file(config_dir / "lockdown.log.3", "log backup 3")

    # Quarantine directory
    print("\n[3/6] Quarantine...")
    quarantine_dir = config_dir / "quarantine"
    _remove_dir(quarantine_dir, "quarantine folder")

    # Firewall rules
    print("\n[4/6] Firewall rules...")
    _remove_firewall_rules()

    # Registry policies
    print("\n[5/6] Registry policies...")
    _remove_registry_policies()

    # Hosts file entries
    print("\n[6/6] Hosts file & lock...")
    _remove_hosts_entries()
    _remove_lock_file()

    # Remove the config directory itself if empty
    if config_dir.exists():
        try:
            config_dir.rmdir()
            print(f"\n  [OK] Removed config directory: {config_dir}")
        except OSError:
            # Not empty (maybe other files)
            print(f"\n  [--] Config directory not empty, left in place: {config_dir}")

    print("\n" + "=" * 50)
    print("  Cleanup complete. All traces removed.")
    print("  Run ComputerLockdown.exe normally to start fresh.")
    print("=" * 50)


if __name__ == "__main__":
    full_cleanup()

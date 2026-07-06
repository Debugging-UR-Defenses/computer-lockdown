"""Utility modules for Computer Lockdown."""

from src.utils.config import ConfigManager, DEFAULT_CONFIG
from src.utils.crypto import hash_password, verify_password, generate_salt, is_password_set
from src.utils.system import (
    is_admin,
    is_windows,
    request_admin,
    get_running_processes,
    kill_process,
    get_system_drive,
    get_hosts_file_path,
    add_to_startup,
    remove_from_startup,
    lock_workstation,
    log_off_user,
)

__all__ = [
    # config
    "ConfigManager",
    "DEFAULT_CONFIG",
    # crypto
    "hash_password",
    "verify_password",
    "generate_salt",
    "is_password_set",
    # system
    "is_admin",
    "is_windows",
    "request_admin",
    "get_running_processes",
    "kill_process",
    "get_system_drive",
    "get_hosts_file_path",
    "add_to_startup",
    "remove_from_startup",
    "lock_workstation",
    "log_off_user",
]

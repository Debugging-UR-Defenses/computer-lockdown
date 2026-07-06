# Computer Lockdown

A parental control application for Windows 11 that allows you to lock down a computer with application whitelisting, website blocking, time limits, and more.

## Features

- **Application Whitelisting** — Only approved applications can run. All others are automatically terminated.
- **Website Blocking** — Block specific websites or use whitelist-only mode. Quick-add categories (social media, gaming, etc).
- **Time Limits** — Set daily usage limits and per-day schedules. Automatic lockout when time is up.
- **Download Blocking** — Prevents downloading executable files (.exe, .msi, .bat, etc).
- **Security Policies** — Block Task Manager, Command Prompt, Registry Editor, and more via Group Policy.
- **Admin Mode** — Enter a PIN to temporarily unlock everything for administration. One-click re-lock.
- **Modern Dark UI** — Clean, polished interface built with CustomTkinter.
- **System Tray** — Runs in the background with system tray integration.

## Requirements

- Windows 11 (Windows 10 may work but is untested)
- Python 3.10+ (for development)
- Administrator privileges (required for hosts file, registry, and process management)

## Installation

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/computer-lockdown.git
   cd computer-lockdown
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python run.py
   ```

### Building an Executable

```bash
python build.py
```

The executable will be created at `dist/ComputerLockdown.exe`.

To build with a console window for debugging:

```bash
python build.py --debug
```

## First Run

On first launch, you'll be prompted to set an admin password/PIN. This is required to access settings and enter admin mode.

## Usage

### Locked Mode (Default)

The application runs in the background enforcing all restrictions. The child can see the app is running but cannot modify any settings without the admin password.

### Admin Mode

1. Click on the Computer Lockdown window
2. Click "Admin Login"
3. Enter your password/PIN
4. All restrictions are temporarily suspended
5. Use the admin panel to:
   - Add/remove allowed applications
   - Manage blocked websites
   - Adjust time limits and schedules
   - Configure security policies
   - Change settings
6. Click "Lock Down" to re-engage all restrictions

## Architecture

```
computer-lockdown/
├── run.py                  # Convenience entry point
├── build.py                # PyInstaller build script
├── requirements.txt        # Python dependencies
├── config/
│   └── default_config.json # Default configuration template
├── assets/
│   └── icon.ico            # Application icon (add your own)
└── src/
    ├── main.py              # Application entry point & bootstrapping
    ├── core/
    │   ├── app_monitor.py    # Application whitelist enforcement
    │   ├── web_blocker.py    # Website blocking via hosts file
    │   ├── time_manager.py   # Time limits and scheduling
    │   ├── download_blocker.py # Download prevention
    │   ├── policy_manager.py  # Windows Group Policy integration
    │   └── lockdown_service.py # Main coordinator service
    ├── gui/
    │   ├── app.py            # Main application window
    │   ├── theme.py          # Dark theme configuration
    │   ├── login_screen.py   # Locked screen / PIN entry
    │   ├── dashboard.py      # Admin dashboard
    │   ├── app_manager_gui.py # App whitelist management
    │   ├── web_manager_gui.py # Website blocking management
    │   ├── time_manager_gui.py # Time limits management
    │   └── settings_gui.py   # Settings page
    └── utils/
        ├── config.py         # Configuration management (JSON, dot-notation)
        ├── crypto.py         # Password hashing (bcrypt / PBKDF2 fallback)
        └── system.py         # System utilities (privileges, startup, processes)
```

## Configuration

Configuration is stored as JSON:

- **Windows:** `%APPDATA%\ComputerLockdown\config.json`
- **Development:** `./config/config.json`

The default configuration is defined in `config/default_config.json` and in `src/utils/config.py`. On first launch the config file is created automatically with sensible defaults.

### Key Configuration Sections

| Section              | Description                                    |
|----------------------|------------------------------------------------|
| `app_whitelist`      | Enabled flag and list of allowed applications  |
| `web_blocking`       | Blacklist/whitelist mode and domain lists       |
| `time_limits`        | Daily minute caps and per-day schedule windows  |
| `download_blocking`  | Blocked file extensions                        |
| `policy`             | Windows policy toggles (Task Manager, CMD, etc) |
| `startup`            | Run-on-startup and start-locked flags          |

## Security Notes

- The admin password is stored as a bcrypt hash (or PBKDF2-HMAC-SHA256 fallback) — it cannot be reversed.
- The application requires administrator privileges to modify the hosts file and Windows registry.
- A temp-file lock prevents multiple instances from running simultaneously.
- For maximum security, set the application to run on Windows startup.
- Consider also setting a Windows user account password for the child's account.
- Logs are written to `%APPDATA%\ComputerLockdown\lockdown.log` with automatic rotation (2 MB max, 3 backups).

## Security Hardening

Computer Lockdown implements several layers of protection, but for maximum security
the following additional measures are recommended:

### Automatic Protections (built-in)
- **Config file integrity**: HMAC-signed configuration file — tampered configs are rejected and reset to defaults
- **Config storage**: Stored in `%PROGRAMDATA%\ComputerLockdown\` (requires admin to modify)
- **Dangerous tool blocking**: PowerShell, CMD, WSL, wscript, certutil, regedit, taskmgr, and 20+ other tools are blocked in locked mode
- **DNS-over-HTTPS blocking**: Known DoH provider IPs blocked via Windows Firewall to prevent bypass of web filtering
- **Safe Mode protection**: BCD modified to prevent Safe Mode boot bypass

### Recommended Manual Steps
1. **Set a BIOS/UEFI password** — prevents booting from USB
2. **Enable Secure Boot** — prevents unauthorized OS booting
3. **Enable BitLocker** — prevents offline disk access
4. **Create a standard (non-admin) Windows account** for the child
5. **Block Microsoft Store** via Group Policy (`gpedit.msc` → Computer Configuration → Administrative Templates → Windows Components → Store)
6. **Disable USB boot** in BIOS settings
7. **Set Windows Update to admin-only** to prevent feature changes
8. **Use a DNS-level blocker** (e.g. OpenDNS Family Shield at router level) as a second layer of web filtering

### Known Limitations
- **User-space application**: Runs as a regular process, not a kernel driver. A sufficiently advanced user with admin access could terminate it.
- **Hosts file web blocking**: Effective for basic blocking but can be bypassed by apps that use their own DNS resolution. DoH blocking mitigates the most common bypass.
- **Download monitoring**: Only watches Downloads, Desktop, and Documents folders. Files saved to other locations are not monitored.
- **Browser extensions**: Cannot prevent installation of browser extensions that may provide proxy/VPN functionality.

For enterprise-grade protection, consider supplementing with Microsoft Family Safety,
Windows Defender Application Control (WDAC), or an MDM solution like Microsoft Intune.

## Development

### Project Setup

```bash
# Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Running in Development

```bash
python run.py
```

On non-Windows platforms the application runs in a limited mode:
- Process monitoring uses dry-run mode (no processes are killed).
- The hosts file writes to a local `config/hosts_dev` file instead of the system hosts file.
- Windows-specific features (registry, Group Policy) are skipped with warnings.

## License

MIT License

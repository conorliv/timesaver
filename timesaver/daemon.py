"""Background daemon for scheduled blocking."""

import os
import sys
from datetime import datetime
from pathlib import Path

from . import blocker, config, scheduler

PLIST_NAME = "com.timesaver.daemon.plist"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"


def generate_plist(python_path: str | None = None) -> str:
    """Generate launchd plist content.

    Args:
        python_path: Path to Python executable (defaults to current)

    Returns:
        Plist XML content
    """
    if python_path is None:
        python_path = sys.executable

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_NAME.replace('.plist', '')}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>-m</string>
        <string>timesaver.daemon</string>
        <string>check</string>
    </array>
    <key>StartInterval</key>
    <integer>60</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>{Path.home()}/.timesaver/daemon.log</string>
    <key>StandardOutPath</key>
    <string>{Path.home()}/.timesaver/daemon.log</string>
</dict>
</plist>
"""


def get_plist_path() -> Path:
    """Get the path to the launchd plist file."""
    return LAUNCH_AGENTS_DIR / PLIST_NAME


def install_daemon(python_path: str | None = None) -> bool:
    """Install the launchd daemon.

    Args:
        python_path: Path to Python executable

    Returns:
        True if installation successful
    """
    import subprocess

    # Ensure LaunchAgents directory exists
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure config directory exists
    config.get_config_path().parent.mkdir(parents=True, exist_ok=True)

    plist_path = get_plist_path()
    plist_content = generate_plist(python_path)

    # Unload existing daemon if present
    if plist_path.exists():
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
        )

    # Write plist file
    plist_path.write_text(plist_content)

    # Load daemon
    result = subprocess.run(
        ["launchctl", "load", str(plist_path)],
        capture_output=True,
    )

    return result.returncode == 0


def uninstall_daemon() -> bool:
    """Uninstall the launchd daemon.

    Returns:
        True if uninstallation successful
    """
    import subprocess

    plist_path = get_plist_path()

    if not plist_path.exists():
        return True

    # Unload daemon
    subprocess.run(
        ["launchctl", "unload", str(plist_path)],
        capture_output=True,
    )

    # Remove plist file
    plist_path.unlink()

    return True


def is_daemon_installed() -> bool:
    """Check if the daemon is installed."""
    return get_plist_path().exists()


def check_and_apply() -> str:
    """Check schedules and apply/remove blocks as needed.

    Returns:
        Status message indicating what action was taken
    """
    cfg = config.load_config()

    if not cfg["enabled"]:
        return "Blocking is disabled"

    sites = cfg["blocked_sites"]
    schedules = cfg["schedules"]

    if not sites:
        return "No sites configured to block"

    current_time = datetime.now()
    should_block = scheduler.is_in_schedule(schedules, current_time)
    current_blocks = blocker.get_current_blocks()

    if should_block:
        if set(current_blocks) != set(sites):
            blocker.apply_blocks(sites)
            blocker.flush_dns_cache()
            return f"Applied blocks for {len(sites)} sites"
        return "Blocks already applied"
    else:
        if current_blocks:
            blocker.remove_blocks()
            blocker.flush_dns_cache()
            return "Removed blocks (outside schedule)"
        return "No blocks to remove"


def main() -> None:
    """Main entry point for daemon."""
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        result = check_and_apply()
        print(f"[{datetime.now().isoformat()}] {result}")
    else:
        print("Usage: python -m timesaver.daemon check")
        sys.exit(1)


if __name__ == "__main__":
    main()

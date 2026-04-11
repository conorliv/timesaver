"""Hosts file manipulation for blocking websites."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

HOSTS_PATH = Path("/etc/hosts")
BACKUP_PATH = Path("/etc/hosts.timesaver.bak")
MARKER_START = "# TIMESAVER-START"
MARKER_END = "# TIMESAVER-END"
REDIRECT_IP = "127.0.0.1"
REDIRECT_IP6 = "::1"


def read_hosts_file(hosts_path: Path | None = None) -> str:
    """Read the hosts file content.

    Args:
        hosts_path: Path to hosts file (defaults to /etc/hosts)

    Returns:
        Content of the hosts file
    """
    path = hosts_path or HOSTS_PATH
    return path.read_text()


def write_hosts_file(content: str, hosts_path: Path | None = None) -> None:
    """Write content to the hosts file atomically with backup.

    Uses atomic write pattern:
    1. Create backup of original file
    2. Write to temporary file
    3. Atomically rename temp file to target

    Args:
        content: Content to write
        hosts_path: Path to hosts file (defaults to /etc/hosts)
    """
    path = hosts_path or HOSTS_PATH
    backup_path = path.parent / f"{path.name}.timesaver.bak"

    # Create backup if original exists
    if path.exists():
        shutil.copy2(path, backup_path)

    # Write to temp file in same directory (required for atomic rename)
    temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=".hosts_tmp_")
    temp_file = Path(temp_path)
    try:
        os.close(temp_fd)  # Close the file descriptor from mkstemp
        temp_file.write_text(content)
        # Preserve original permissions
        if path.exists():
            shutil.copymode(path, temp_file)
        # Atomic rename
        temp_file.rename(path)
    except Exception:
        # Clean up temp file on failure
        temp_file.unlink(missing_ok=True)
        raise


def generate_block_entries(domains: list[str]) -> str:
    """Generate hosts file entries for blocking domains.

    Args:
        domains: List of domains to block

    Returns:
        String with hosts file entries
    """
    if not domains:
        return ""

    lines = [MARKER_START]
    for domain in sorted(set(domains)):
        # Add both with and without www, for both IPv4 and IPv6
        lines.append(f"{REDIRECT_IP} {domain}")
        lines.append(f"{REDIRECT_IP6} {domain}")
        if not domain.startswith("www."):
            lines.append(f"{REDIRECT_IP} www.{domain}")
            lines.append(f"{REDIRECT_IP6} www.{domain}")
    lines.append(MARKER_END)

    return "\n".join(lines)


def remove_timesaver_entries(content: str) -> str:
    """Remove existing TimeSaver entries from hosts content.

    Args:
        content: Current hosts file content

    Returns:
        Content with TimeSaver entries removed
    """
    lines = content.split("\n")
    result = []
    in_block = False

    for line in lines:
        if line.strip() == MARKER_START:
            in_block = True
            continue
        if line.strip() == MARKER_END:
            in_block = False
            continue
        if not in_block:
            result.append(line)

    # Remove trailing empty lines that might have been before our block
    while result and result[-1] == "":
        result.pop()

    return "\n".join(result)


def apply_blocks(domains: list[str], hosts_path: Path | None = None) -> None:
    """Apply domain blocks to the hosts file.

    Args:
        domains: List of domains to block
        hosts_path: Path to hosts file (defaults to /etc/hosts)
    """
    content = read_hosts_file(hosts_path)
    content = remove_timesaver_entries(content)

    if domains:
        block_entries = generate_block_entries(domains)
        content = content.rstrip() + "\n\n" + block_entries + "\n"

    write_hosts_file(content, hosts_path)


def remove_blocks(hosts_path: Path | None = None) -> None:
    """Remove all TimeSaver blocks from the hosts file.

    Args:
        hosts_path: Path to hosts file (defaults to /etc/hosts)
    """
    content = read_hosts_file(hosts_path)
    content = remove_timesaver_entries(content)
    # Ensure file ends with newline
    content = content.rstrip() + "\n"
    write_hosts_file(content, hosts_path)


def get_backup_path(hosts_path: Path | None = None) -> Path:
    """Get the path to the backup file.

    Args:
        hosts_path: Path to hosts file (defaults to /etc/hosts)

    Returns:
        Path to the backup file
    """
    path = hosts_path or HOSTS_PATH
    return path.parent / f"{path.name}.timesaver.bak"


def has_backup(hosts_path: Path | None = None) -> bool:
    """Check if a backup file exists.

    Args:
        hosts_path: Path to hosts file (defaults to /etc/hosts)

    Returns:
        True if backup exists
    """
    return get_backup_path(hosts_path).exists()


def restore_from_backup(hosts_path: Path | None = None) -> bool:
    """Restore hosts file from backup.

    Args:
        hosts_path: Path to hosts file (defaults to /etc/hosts)

    Returns:
        True if restored successfully, False if no backup exists
    """
    path = hosts_path or HOSTS_PATH
    backup_path = get_backup_path(hosts_path)

    if not backup_path.exists():
        return False

    shutil.copy2(backup_path, path)
    return True


def flush_dns_cache() -> bool:
    """Flush the DNS cache on macOS.

    Returns:
        True if successful, False otherwise
    """
    try:
        subprocess.run(
            ["dscacheutil", "-flushcache"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_current_blocks(hosts_path: Path | None = None) -> list[str]:
    """Get list of currently blocked domains from hosts file.

    Args:
        hosts_path: Path to hosts file (defaults to /etc/hosts)

    Returns:
        List of blocked domains (without www prefix)
    """
    try:
        content = read_hosts_file(hosts_path)
    except FileNotFoundError:
        return []

    domains = set()
    in_block = False

    for line in content.split("\n"):
        if line.strip() == MARKER_START:
            in_block = True
            continue
        if line.strip() == MARKER_END:
            in_block = False
            continue
        if in_block and line.strip():
            parts = line.split()
            if len(parts) >= 2:
                domain = parts[1]
                # Remove www. prefix for consistency
                if domain.startswith("www."):
                    domain = domain[4:]
                domains.add(domain)

    return sorted(domains)

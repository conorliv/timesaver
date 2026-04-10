"""Configuration file management for TimeSaver."""

import copy
import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "blocked_sites": [],
    "schedules": [],
    "enabled": False,
    "accountability_emails": [],
    "smtp_config": {
        "server": "",
        "port": 587,
        "username": "",
        "password": "",
    },
}


def get_config_path() -> Path:
    """Get the path to the config file."""
    return Path.home() / ".timesaver" / "config.json"


def load_config() -> dict[str, Any]:
    """Load configuration from file.

    Returns:
        Configuration dictionary with blocked_sites, schedules, and enabled state.
    """
    config_path = get_config_path()

    if not config_path.exists():
        return copy.deepcopy(DEFAULT_CONFIG)

    with open(config_path) as f:
        config = json.load(f)

    # Ensure all required keys exist
    for key, default_value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = default_value

    return config


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file.

    Args:
        config: Configuration dictionary to save.
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def add_site(domain: str) -> bool:
    """Add a site to the blocked list.

    Args:
        domain: Domain to block (e.g., 'twitter.com')

    Returns:
        True if site was added, False if already exists.
    """
    config = load_config()

    # Normalize domain (remove protocol and www if present)
    domain = normalize_domain(domain)

    if domain in config["blocked_sites"]:
        return False

    config["blocked_sites"].append(domain)
    save_config(config)
    return True


def remove_site(domain: str) -> bool:
    """Remove a site from the blocked list.

    Args:
        domain: Domain to unblock

    Returns:
        True if site was removed, False if not found.
    """
    config = load_config()
    domain = normalize_domain(domain)

    if domain not in config["blocked_sites"]:
        return False

    config["blocked_sites"].remove(domain)
    save_config(config)
    return True


def get_blocked_sites() -> list[str]:
    """Get list of blocked sites."""
    config = load_config()
    return config["blocked_sites"]


def add_schedule(start: str, end: str) -> bool:
    """Add a schedule for blocking.

    Args:
        start: Start time in HH:MM format
        end: End time in HH:MM format

    Returns:
        True if schedule was added, False if already exists.
    """
    config = load_config()
    schedule = {"start": start, "end": end}

    if schedule in config["schedules"]:
        return False

    config["schedules"].append(schedule)
    save_config(config)
    return True


def remove_schedule(start: str, end: str) -> bool:
    """Remove a schedule.

    Args:
        start: Start time in HH:MM format
        end: End time in HH:MM format

    Returns:
        True if schedule was removed, False if not found.
    """
    config = load_config()
    schedule = {"start": start, "end": end}

    if schedule not in config["schedules"]:
        return False

    config["schedules"].remove(schedule)
    save_config(config)
    return True


def clear_schedules() -> int:
    """Clear all schedules.

    Returns:
        Number of schedules removed.
    """
    config = load_config()
    count = len(config["schedules"])
    config["schedules"] = []
    save_config(config)
    return count


def get_schedules() -> list[dict[str, str]]:
    """Get list of schedules."""
    config = load_config()
    return config["schedules"]


def set_enabled(enabled: bool) -> None:
    """Set the enabled state.

    Args:
        enabled: Whether blocking is enabled.
    """
    config = load_config()
    config["enabled"] = enabled
    save_config(config)


def is_enabled() -> bool:
    """Check if blocking is enabled."""
    config = load_config()
    return config["enabled"]


def normalize_domain(domain: str) -> str:
    """Normalize a domain by removing protocol and www prefix.

    Args:
        domain: Domain to normalize

    Returns:
        Normalized domain (e.g., 'twitter.com')
    """
    # Remove protocol
    if "://" in domain:
        domain = domain.split("://", 1)[1]

    # Remove path
    domain = domain.split("/")[0]

    # Remove www. prefix for storage (we'll add both versions when blocking)
    if domain.startswith("www."):
        domain = domain[4:]

    return domain.lower()


def add_accountability_email(email: str) -> bool:
    """Add an accountability partner email.

    Args:
        email: Email address to add

    Returns:
        True if email was added, False if already exists.
    """
    config = load_config()
    email = email.lower().strip()

    if email in config["accountability_emails"]:
        return False

    config["accountability_emails"].append(email)
    save_config(config)
    return True


def remove_accountability_email(email: str) -> bool:
    """Remove an accountability partner email.

    Args:
        email: Email address to remove

    Returns:
        True if email was removed, False if not found.
    """
    config = load_config()
    email = email.lower().strip()

    if email not in config["accountability_emails"]:
        return False

    config["accountability_emails"].remove(email)
    save_config(config)
    return True


def get_accountability_emails() -> list[str]:
    """Get list of accountability partner emails."""
    config = load_config()
    return config["accountability_emails"]


def set_smtp_config(server: str, port: int, username: str, password: str) -> None:
    """Set SMTP configuration.

    Args:
        server: SMTP server hostname
        port: SMTP server port
        username: SMTP username
        password: SMTP password
    """
    config = load_config()
    config["smtp_config"] = {
        "server": server,
        "port": port,
        "username": username,
        "password": password,
    }
    save_config(config)


def get_smtp_config() -> dict[str, Any]:
    """Get SMTP configuration."""
    config = load_config()
    return config["smtp_config"]

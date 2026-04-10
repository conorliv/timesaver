"""CLI entry point for TimeSaver."""

import click

from . import __version__, blocker, config, daemon, notifier, presets, scheduler


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """TimeSaver - Block distracting websites on a schedule."""
    pass


@cli.command()
@click.argument("url")
def add(url: str) -> None:
    """Add a site to the block list."""
    domain = config.normalize_domain(url)
    if config.add_site(domain):
        click.echo(f"Added {domain} to block list")
    else:
        click.echo(f"{domain} is already in the block list")


@cli.command()
@click.argument("url")
def remove(url: str) -> None:
    """Remove a site from the block list."""
    domain = config.normalize_domain(url)
    if config.remove_site(domain):
        click.echo(f"Removed {domain} from block list")
    else:
        click.echo(f"{domain} is not in the block list")


@cli.command(name="list")
def list_sites() -> None:
    """Show all blocked sites."""
    sites = config.get_blocked_sites()
    if not sites:
        click.echo("No sites in block list")
        return

    click.echo("Blocked sites:")
    for site in sorted(sites):
        click.echo(f"  - {site}")


@cli.command()
@click.argument("name")
def preset(name: str) -> None:
    """Add a preset category of sites (social, news, all)."""
    try:
        sites = presets.get_preset(name)
    except ValueError as e:
        click.echo(str(e))
        return

    added = 0
    for site in sites:
        if config.add_site(site):
            added += 1

    click.echo(f"Added {added} sites from '{name}' preset ({len(sites) - added} already existed)")


@cli.group()
def schedule() -> None:
    """Manage blocking schedules."""
    pass


@schedule.command(name="add")
@click.argument("start")
@click.argument("end")
def schedule_add(start: str, end: str) -> None:
    """Add a schedule (e.g., 09:00 17:00)."""
    # Validate time formats
    if not scheduler.validate_time_format(start):
        click.echo(f"Invalid start time: {start}. Use HH:MM format.")
        return
    if not scheduler.validate_time_format(end):
        click.echo(f"Invalid end time: {end}. Use HH:MM format.")
        return

    if config.add_schedule(start, end):
        click.echo(f"Added schedule: {start} to {end}")
    else:
        click.echo(f"Schedule {start} to {end} already exists")


@schedule.command(name="list")
def schedule_list() -> None:
    """Show all schedules."""
    schedules = config.get_schedules()
    if not schedules:
        click.echo("No schedules configured (blocking applies 24/7 when enabled)")
        return

    click.echo("Schedules:")
    for s in schedules:
        click.echo(f"  - {s['start']} to {s['end']}")


@schedule.command(name="clear")
def schedule_clear() -> None:
    """Remove all schedules."""
    count = config.clear_schedules()
    click.echo(f"Removed {count} schedule(s)")


@cli.command()
def status() -> None:
    """Show current blocking status."""
    cfg = config.load_config()

    # Enabled state
    enabled = cfg["enabled"]
    click.echo(f"Blocking: {'enabled' if enabled else 'disabled'}")

    # Current blocks in hosts file
    current_blocks = blocker.get_current_blocks()
    if current_blocks:
        click.echo(f"Currently blocking: {len(current_blocks)} sites")
    else:
        click.echo("Currently blocking: none")

    # Configured sites
    sites = cfg["blocked_sites"]
    click.echo(f"Configured sites: {len(sites)}")

    # Schedules
    schedules = cfg["schedules"]
    if schedules:
        click.echo(f"Schedules: {len(schedules)}")
        for s in schedules:
            click.echo(f"  - {s['start']} to {s['end']}")
    else:
        click.echo("Schedules: none (24/7 when enabled)")

    # Daemon status
    if daemon.is_daemon_installed():
        click.echo("Daemon: installed")
    else:
        click.echo("Daemon: not installed")


@cli.command()
def enable() -> None:
    """Enable blocking."""
    config.set_enabled(True)
    sites = config.get_blocked_sites()

    if not sites:
        click.echo("Blocking enabled, but no sites configured. Use 'timesaver add' or 'timesaver preset'.")
        return

    schedules = config.get_schedules()
    if scheduler.is_in_schedule(schedules):
        blocker.apply_blocks(sites)
        blocker.flush_dns_cache()
        click.echo(f"Blocking enabled. {len(sites)} sites are now blocked.")
    else:
        click.echo("Blocking enabled, but current time is outside schedule.")


@cli.command()
def disable() -> None:
    """Disable blocking."""
    # Check if in shame schedule and send notification
    if scheduler.is_in_shame_schedule():
        emails = config.get_accountability_emails()
        if emails:
            smtp = config.get_smtp_config()
            if smtp.get("server"):
                if notifier.send_shame_email(emails, smtp):
                    click.echo(f"Notification sent to {len(emails)} accountability partner(s).")
                else:
                    click.echo("Warning: Failed to send notification email.")
            else:
                click.echo("Warning: SMTP not configured, no notification sent.")

    config.set_enabled(False)
    blocker.remove_blocks()
    blocker.flush_dns_cache()
    click.echo("Blocking disabled.")


@cli.command(name="install-daemon")
def install_daemon_cmd() -> None:
    """Install the launchd background service."""
    if daemon.install_daemon():
        click.echo("Daemon installed successfully.")
        click.echo(f"Plist location: {daemon.get_plist_path()}")
        click.echo("The daemon will check schedules every minute.")
    else:
        click.echo("Failed to install daemon.")


@cli.command(name="uninstall-daemon")
def uninstall_daemon_cmd() -> None:
    """Uninstall the launchd background service."""
    if daemon.uninstall_daemon():
        click.echo("Daemon uninstalled successfully.")
    else:
        click.echo("Failed to uninstall daemon.")


@cli.command()
def restore() -> None:
    """Restore /etc/hosts from backup (emergency recovery)."""
    if not blocker.has_backup():
        click.echo("No backup file found.")
        return

    backup_path = blocker.get_backup_path()
    click.echo(f"Backup found at: {backup_path}")

    if blocker.restore_from_backup():
        blocker.flush_dns_cache()
        config.set_enabled(False)
        click.echo("Hosts file restored from backup.")
        click.echo("Blocking has been disabled.")
    else:
        click.echo("Failed to restore from backup.")


@cli.group()
def shame() -> None:
    """Manage accountability partners for shame notifications."""
    pass


@shame.command(name="add")
@click.argument("email")
def shame_add(email: str) -> None:
    """Add an accountability partner email."""
    if config.add_accountability_email(email):
        click.echo(f"Added {email.lower().strip()} as accountability partner.")
    else:
        click.echo(f"{email.lower().strip()} is already an accountability partner.")


@shame.command(name="remove")
@click.argument("email")
def shame_remove(email: str) -> None:
    """Remove an accountability partner email."""
    if config.remove_accountability_email(email):
        click.echo(f"Removed {email.lower().strip()} from accountability partners.")
    else:
        click.echo(f"{email.lower().strip()} is not an accountability partner.")


@shame.command(name="list")
def shame_list() -> None:
    """List all accountability partners."""
    emails = config.get_accountability_emails()
    if not emails:
        click.echo("No accountability partners configured.")
        return

    click.echo("Accountability partners:")
    for email in sorted(emails):
        click.echo(f"  - {email}")


@shame.command(name="config")
def shame_config() -> None:
    """Configure SMTP settings interactively."""
    click.echo("Configure SMTP settings for shame notifications.")
    click.echo("(Press Enter to keep existing value)")

    current = config.get_smtp_config()

    server = click.prompt(
        "SMTP Server",
        default=current.get("server") or "",
        show_default=bool(current.get("server")),
    )
    port = click.prompt(
        "SMTP Port",
        default=current.get("port", 587),
        type=int,
    )
    username = click.prompt(
        "SMTP Username",
        default=current.get("username") or "",
        show_default=bool(current.get("username")),
    )
    password = click.prompt(
        "SMTP Password",
        default=current.get("password") or "",
        hide_input=True,
        show_default=False,
    )

    config.set_smtp_config(server, port, username, password)
    click.echo("SMTP configuration saved.")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()

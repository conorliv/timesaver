"""Tests for main CLI module."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from timesaver import blocker, config, daemon
from timesaver.main import cli


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


def test_add_site(runner, isolated_env):
    """Test adding a site."""
    result = runner.invoke(cli, ["add", "twitter.com"])
    assert result.exit_code == 0
    assert "Added twitter.com" in result.output


def test_add_site_duplicate(runner, isolated_env):
    """Test adding a duplicate site."""
    runner.invoke(cli, ["add", "twitter.com"])
    result = runner.invoke(cli, ["add", "twitter.com"])
    assert result.exit_code == 0
    assert "already in the block list" in result.output


def test_remove_site(runner, isolated_env):
    """Test removing a site."""
    runner.invoke(cli, ["add", "twitter.com"])
    result = runner.invoke(cli, ["remove", "twitter.com"])
    assert result.exit_code == 0
    assert "Removed twitter.com" in result.output


def test_remove_site_not_found(runner, isolated_env):
    """Test removing a site that doesn't exist."""
    result = runner.invoke(cli, ["remove", "twitter.com"])
    assert result.exit_code == 0
    assert "not in the block list" in result.output


def test_list_sites_empty(runner, isolated_env):
    """Test listing sites when empty."""
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "No sites" in result.output


def test_list_sites(runner, isolated_env):
    """Test listing sites."""
    runner.invoke(cli, ["add", "twitter.com"])
    runner.invoke(cli, ["add", "facebook.com"])
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "twitter.com" in result.output
    assert "facebook.com" in result.output


def test_preset_social(runner, isolated_env):
    """Test adding social preset."""
    result = runner.invoke(cli, ["preset", "social"])
    assert result.exit_code == 0
    assert "Added" in result.output
    assert "social" in result.output


def test_preset_all_sites_already_exist(runner, isolated_env):
    """Test adding preset when all sites already exist."""
    # Add all social sites first
    runner.invoke(cli, ["preset", "social"])
    # Try adding again - all should already exist
    result = runner.invoke(cli, ["preset", "social"])
    assert result.exit_code == 0
    assert "Added 0 sites" in result.output


def test_preset_invalid(runner, isolated_env):
    """Test adding invalid preset."""
    result = runner.invoke(cli, ["preset", "invalid"])
    assert result.exit_code == 0
    assert "Unknown preset" in result.output


def test_schedule_add(runner, isolated_env):
    """Test adding a schedule."""
    result = runner.invoke(cli, ["schedule", "add", "09:00", "17:00"])
    assert result.exit_code == 0
    assert "Added schedule" in result.output


def test_schedule_add_duplicate(runner, isolated_env):
    """Test adding a duplicate schedule."""
    runner.invoke(cli, ["schedule", "add", "09:00", "17:00"])
    result = runner.invoke(cli, ["schedule", "add", "09:00", "17:00"])
    assert result.exit_code == 0
    assert "already exists" in result.output


def test_schedule_add_invalid_start(runner, isolated_env):
    """Test adding schedule with invalid start time."""
    result = runner.invoke(cli, ["schedule", "add", "invalid", "17:00"])
    assert result.exit_code == 0
    assert "Invalid start time" in result.output


def test_schedule_add_invalid_end(runner, isolated_env):
    """Test adding schedule with invalid end time."""
    result = runner.invoke(cli, ["schedule", "add", "09:00", "invalid"])
    assert result.exit_code == 0
    assert "Invalid end time" in result.output


def test_schedule_list_empty(runner, isolated_env):
    """Test listing schedules when empty."""
    result = runner.invoke(cli, ["schedule", "list"])
    assert result.exit_code == 0
    assert "No schedules" in result.output


def test_schedule_list(runner, isolated_env):
    """Test listing schedules."""
    runner.invoke(cli, ["schedule", "add", "09:00", "17:00"])
    result = runner.invoke(cli, ["schedule", "list"])
    assert result.exit_code == 0
    assert "09:00" in result.output
    assert "17:00" in result.output


def test_schedule_clear(runner, isolated_env):
    """Test clearing schedules."""
    runner.invoke(cli, ["schedule", "add", "09:00", "17:00"])
    result = runner.invoke(cli, ["schedule", "clear"])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_status(runner, isolated_env):
    """Test status command."""
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Blocking:" in result.output
    assert "disabled" in result.output


def test_status_with_sites_and_schedules(runner, isolated_env):
    """Test status with sites and schedules configured."""
    runner.invoke(cli, ["add", "twitter.com"])
    runner.invoke(cli, ["schedule", "add", "09:00", "17:00"])

    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Configured sites: 1" in result.output
    assert "Schedules: 1" in result.output


def test_status_with_daemon(runner, isolated_env):
    """Test status shows daemon installed."""
    launch_agents = isolated_env["launch_agents"]
    launch_agents.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents / daemon.PLIST_NAME
    plist_path.write_text("content")

    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Daemon: installed" in result.output


def test_status_with_current_blocks(runner, isolated_env):
    """Test status shows current blocks when sites are blocked."""
    runner.invoke(cli, ["add", "twitter.com"])

    with patch.object(blocker, "flush_dns_cache", return_value=True):
        runner.invoke(cli, ["enable"])

    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Currently blocking: 1 sites" in result.output


def test_enable_no_sites(runner, isolated_env):
    """Test enabling with no sites configured."""
    result = runner.invoke(cli, ["enable"])
    assert result.exit_code == 0
    assert "no sites configured" in result.output


def test_enable_with_sites(runner, isolated_env):
    """Test enabling with sites configured."""
    runner.invoke(cli, ["add", "twitter.com"])

    with patch.object(blocker, "flush_dns_cache", return_value=True):
        result = runner.invoke(cli, ["enable"])

    assert result.exit_code == 0
    assert "Blocking enabled" in result.output


def test_enable_outside_schedule(runner, isolated_env):
    """Test enabling when outside schedule."""
    from timesaver import scheduler

    runner.invoke(cli, ["add", "twitter.com"])
    runner.invoke(cli, ["schedule", "add", "03:00", "04:00"])

    with patch.object(scheduler, "is_in_schedule", return_value=False):
        result = runner.invoke(cli, ["enable"])

    assert result.exit_code == 0
    assert "outside schedule" in result.output


def test_disable(runner, isolated_env):
    """Test disabling blocking."""
    with patch.object(blocker, "flush_dns_cache", return_value=True):
        result = runner.invoke(cli, ["disable"])

    assert result.exit_code == 0
    assert "Blocking disabled" in result.output


def test_install_daemon(runner, isolated_env):
    """Test installing daemon."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(cli, ["install-daemon"])

    assert result.exit_code == 0
    assert "Daemon installed" in result.output


def test_install_daemon_failure(runner, isolated_env):
    """Test daemon installation failure."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        result = runner.invoke(cli, ["install-daemon"])

    assert result.exit_code == 0
    assert "Failed to install" in result.output


def test_uninstall_daemon(runner, isolated_env):
    """Test uninstalling daemon."""
    launch_agents = isolated_env["launch_agents"]
    launch_agents.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents / daemon.PLIST_NAME
    plist_path.write_text("content")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(cli, ["uninstall-daemon"])

    assert result.exit_code == 0
    assert "Daemon uninstalled" in result.output


def test_uninstall_daemon_failure(runner, isolated_env):
    """Test daemon uninstallation failure."""
    launch_agents = isolated_env["launch_agents"]
    launch_agents.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents / daemon.PLIST_NAME
    plist_path.write_text("content")

    with patch.object(daemon, "uninstall_daemon", return_value=False):
        result = runner.invoke(cli, ["uninstall-daemon"])

    assert result.exit_code == 0
    assert "Failed to uninstall" in result.output


def test_version(runner):
    """Test version flag."""
    from timesaver import __version__
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_main_function(isolated_env):
    """Test the main() entry point function."""
    from timesaver.main import main
    from unittest.mock import patch

    # Mock cli to avoid actual CLI invocation
    with patch.object(cli, "main", return_value=None) as mock_cli:
        main()
        mock_cli.assert_called_once()

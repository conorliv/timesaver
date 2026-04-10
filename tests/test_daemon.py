"""Tests for daemon module."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from timesaver import daemon


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    from timesaver import config

    config_path = tmp_path / ".timesaver" / "config.json"
    with patch.object(config, "get_config_path", return_value=config_path):
        yield config_path


@pytest.fixture
def temp_launch_agents(tmp_path):
    """Create a temporary LaunchAgents directory."""
    launch_agents = tmp_path / "Library" / "LaunchAgents"
    with patch.object(daemon, "LAUNCH_AGENTS_DIR", launch_agents):
        yield launch_agents


def test_generate_plist():
    """Test plist generation."""
    plist = daemon.generate_plist("/usr/bin/python3")
    assert "com.timesaver.daemon" in plist
    assert "/usr/bin/python3" in plist
    assert "-m" in plist
    assert "timesaver.daemon" in plist
    assert "StartInterval" in plist
    assert "60" in plist


def test_generate_plist_default_python():
    """Test plist generation uses current Python by default."""
    plist = daemon.generate_plist()
    assert sys.executable in plist


def test_get_plist_path():
    """Test getting plist path."""
    path = daemon.get_plist_path()
    assert "LaunchAgents" in str(path)
    assert daemon.PLIST_NAME in str(path)


def test_install_daemon(temp_launch_agents, temp_config_dir):
    """Test daemon installation."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = daemon.install_daemon("/usr/bin/python3")

    assert result is True
    plist_path = temp_launch_agents / daemon.PLIST_NAME
    assert plist_path.exists()


def test_install_daemon_unloads_existing(temp_launch_agents, temp_config_dir):
    """Test that install_daemon unloads existing daemon."""
    temp_launch_agents.mkdir(parents=True, exist_ok=True)
    plist_path = temp_launch_agents / daemon.PLIST_NAME
    plist_path.write_text("old content")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        daemon.install_daemon("/usr/bin/python3")

    # Should have been called at least twice (unload and load)
    assert mock_run.call_count >= 2


def test_uninstall_daemon(temp_launch_agents):
    """Test daemon uninstallation."""
    temp_launch_agents.mkdir(parents=True, exist_ok=True)
    plist_path = temp_launch_agents / daemon.PLIST_NAME
    plist_path.write_text("content")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = daemon.uninstall_daemon()

    assert result is True
    assert not plist_path.exists()


def test_uninstall_daemon_not_installed(temp_launch_agents):
    """Test uninstalling daemon that's not installed."""
    result = daemon.uninstall_daemon()
    assert result is True


def test_is_daemon_installed(temp_launch_agents):
    """Test checking if daemon is installed."""
    assert daemon.is_daemon_installed() is False

    temp_launch_agents.mkdir(parents=True, exist_ok=True)
    plist_path = temp_launch_agents / daemon.PLIST_NAME
    plist_path.write_text("content")

    assert daemon.is_daemon_installed() is True


def test_check_and_apply_disabled(temp_config_dir):
    """Test check_and_apply when blocking is disabled."""
    from timesaver import config

    config.save_config({"blocked_sites": ["twitter.com"], "schedules": [], "enabled": False})

    result = daemon.check_and_apply()
    assert "disabled" in result


def test_check_and_apply_no_sites(temp_config_dir):
    """Test check_and_apply with no sites configured."""
    from timesaver import config

    config.save_config({"blocked_sites": [], "schedules": [], "enabled": True})

    result = daemon.check_and_apply()
    assert "No sites" in result


def test_check_and_apply_applies_blocks(temp_config_dir, tmp_path):
    """Test check_and_apply applies blocks when in schedule."""
    from timesaver import blocker, config

    config.save_config(
        {"blocked_sites": ["twitter.com"], "schedules": [{"start": "00:00", "end": "23:59"}], "enabled": True}
    )

    hosts_file = tmp_path / "hosts"
    hosts_file.write_text("127.0.0.1 localhost\n")

    with patch.object(blocker, "HOSTS_PATH", hosts_file):
        with patch.object(blocker, "flush_dns_cache", return_value=True):
            result = daemon.check_and_apply()

    assert "Applied blocks" in result


def test_check_and_apply_already_blocked(temp_config_dir, tmp_path):
    """Test check_and_apply when blocks already applied."""
    from timesaver import blocker, config

    config.save_config(
        {"blocked_sites": ["twitter.com"], "schedules": [{"start": "00:00", "end": "23:59"}], "enabled": True}
    )

    hosts_file = tmp_path / "hosts"
    hosts_file.write_text("127.0.0.1 localhost\n")

    with patch.object(blocker, "HOSTS_PATH", hosts_file):
        with patch.object(blocker, "flush_dns_cache", return_value=True):
            # Apply blocks first
            blocker.apply_blocks(["twitter.com"], hosts_file)
            # Now check should say already applied
            result = daemon.check_and_apply()

    assert "already applied" in result


def test_check_and_apply_removes_blocks_outside_schedule(temp_config_dir, tmp_path):
    """Test check_and_apply removes blocks outside schedule."""
    from timesaver import blocker, config, scheduler

    config.save_config(
        {"blocked_sites": ["twitter.com"], "schedules": [{"start": "03:00", "end": "04:00"}], "enabled": True}
    )

    hosts_file = tmp_path / "hosts"
    hosts_file.write_text("127.0.0.1 localhost\n")

    with patch.object(blocker, "HOSTS_PATH", hosts_file):
        # Apply blocks first
        blocker.apply_blocks(["twitter.com"], hosts_file)

        # Mock time to be outside schedule
        outside_time = datetime(2024, 1, 1, 12, 0, 0)
        with patch.object(scheduler, "is_in_schedule", return_value=False):
            with patch.object(blocker, "flush_dns_cache", return_value=True):
                result = daemon.check_and_apply()

    assert "Removed blocks" in result


def test_check_and_apply_no_blocks_to_remove(temp_config_dir, tmp_path):
    """Test check_and_apply when no blocks to remove."""
    from timesaver import blocker, config, scheduler

    config.save_config(
        {"blocked_sites": ["twitter.com"], "schedules": [{"start": "03:00", "end": "04:00"}], "enabled": True}
    )

    hosts_file = tmp_path / "hosts"
    hosts_file.write_text("127.0.0.1 localhost\n")

    with patch.object(blocker, "HOSTS_PATH", hosts_file):
        with patch.object(scheduler, "is_in_schedule", return_value=False):
            result = daemon.check_and_apply()

    assert "No blocks to remove" in result


def test_main_check(temp_config_dir, capsys):
    """Test main function with check argument."""
    from timesaver import config

    config.save_config({"blocked_sites": [], "schedules": [], "enabled": False})

    with patch.object(sys, "argv", ["daemon", "check"]):
        daemon.main()

    captured = capsys.readouterr()
    assert "disabled" in captured.out


def test_main_no_args(capsys):
    """Test main function without arguments."""
    with patch.object(sys, "argv", ["daemon"]):
        with pytest.raises(SystemExit) as exc_info:
            daemon.main()
    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "Usage" in captured.out

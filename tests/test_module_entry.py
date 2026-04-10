"""Tests for module entry points."""

import subprocess
import sys


def test_module_entry_point():
    """Test running as python -m timesaver."""
    result = subprocess.run(
        [sys.executable, "-m", "timesaver", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "TimeSaver" in result.stdout


def test_daemon_module_entry():
    """Test running daemon module with no args shows usage."""
    result = subprocess.run(
        [sys.executable, "-m", "timesaver.daemon"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Usage" in result.stdout


def test_dunder_main_import():
    """Test that __main__.py can be imported."""
    from timesaver import __main__
    assert hasattr(__main__, "main")

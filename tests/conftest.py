"""Shared fixtures for tests."""

import pytest
from pathlib import Path
from unittest.mock import patch

from timesaver import blocker, config, daemon


@pytest.fixture
def isolated_env(tmp_path):
    """Provide an isolated environment for each test.

    Patches config.get_config_path, blocker.HOSTS_PATH, and daemon.LAUNCH_AGENTS_DIR
    to use temporary directories.
    """
    config_path = tmp_path / ".timesaver" / "config.json"
    hosts_file = tmp_path / "hosts"
    hosts_file.write_text("127.0.0.1 localhost\n")
    launch_agents = tmp_path / "Library" / "LaunchAgents"

    with patch.object(config, "get_config_path", return_value=config_path):
        with patch.object(blocker, "HOSTS_PATH", hosts_file):
            with patch.object(daemon, "LAUNCH_AGENTS_DIR", launch_agents):
                yield {
                    "config_path": config_path,
                    "hosts_file": hosts_file,
                    "launch_agents": launch_agents,
                    "tmp_path": tmp_path,
                }

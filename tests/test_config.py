"""Tests for config module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from timesaver import config


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_path = tmp_path / ".timesaver" / "config.json"
    with patch.object(config, "get_config_path", return_value=config_path):
        yield config_path


def test_get_config_path():
    """Test that config path is in home directory."""
    path = config.get_config_path()
    assert ".timesaver" in str(path)
    assert "config.json" in str(path)


def test_load_config_default(temp_config_dir):
    """Test loading config when file doesn't exist."""
    cfg = config.load_config()
    assert cfg["blocked_sites"] == []
    assert cfg["schedules"] == []
    assert cfg["enabled"] is False


def test_save_and_load_config(temp_config_dir):
    """Test saving and loading config."""
    cfg = {
        "blocked_sites": ["twitter.com"],
        "schedules": [{"start": "09:00", "end": "17:00"}],
        "enabled": True,
    }
    config.save_config(cfg)

    loaded = config.load_config()
    assert loaded == cfg


def test_load_config_fills_missing_keys(temp_config_dir):
    """Test that loading config fills in missing keys."""
    temp_config_dir.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_config_dir, "w") as f:
        json.dump({"blocked_sites": ["test.com"]}, f)

    cfg = config.load_config()
    assert cfg["blocked_sites"] == ["test.com"]
    assert cfg["schedules"] == []
    assert cfg["enabled"] is False


def test_add_site(temp_config_dir):
    """Test adding a site."""
    assert config.add_site("twitter.com") is True
    assert "twitter.com" in config.get_blocked_sites()


def test_add_site_duplicate(temp_config_dir):
    """Test adding a duplicate site."""
    config.add_site("twitter.com")
    assert config.add_site("twitter.com") is False


def test_add_site_with_url(temp_config_dir):
    """Test adding a site with full URL."""
    config.add_site("https://www.twitter.com/path")
    sites = config.get_blocked_sites()
    assert "twitter.com" in sites


def test_remove_site(temp_config_dir):
    """Test removing a site."""
    config.add_site("twitter.com")
    assert config.remove_site("twitter.com") is True
    assert "twitter.com" not in config.get_blocked_sites()


def test_remove_site_not_found(temp_config_dir):
    """Test removing a site that doesn't exist."""
    assert config.remove_site("nonexistent.com") is False


def test_get_blocked_sites(temp_config_dir):
    """Test getting blocked sites."""
    config.add_site("twitter.com")
    config.add_site("facebook.com")
    sites = config.get_blocked_sites()
    assert "twitter.com" in sites
    assert "facebook.com" in sites


def test_add_schedule(temp_config_dir):
    """Test adding a schedule."""
    assert config.add_schedule("09:00", "17:00") is True
    schedules = config.get_schedules()
    assert {"start": "09:00", "end": "17:00"} in schedules


def test_add_schedule_duplicate(temp_config_dir):
    """Test adding a duplicate schedule."""
    config.add_schedule("09:00", "17:00")
    assert config.add_schedule("09:00", "17:00") is False


def test_remove_schedule(temp_config_dir):
    """Test removing a schedule."""
    config.add_schedule("09:00", "17:00")
    assert config.remove_schedule("09:00", "17:00") is True
    assert config.get_schedules() == []


def test_remove_schedule_not_found(temp_config_dir):
    """Test removing a schedule that doesn't exist."""
    assert config.remove_schedule("09:00", "17:00") is False


def test_clear_schedules(temp_config_dir):
    """Test clearing all schedules."""
    config.add_schedule("09:00", "12:00")
    config.add_schedule("13:00", "17:00")
    count = config.clear_schedules()
    assert count == 2
    assert config.get_schedules() == []


def test_set_and_is_enabled(temp_config_dir):
    """Test setting and checking enabled state."""
    assert config.is_enabled() is False
    config.set_enabled(True)
    assert config.is_enabled() is True
    config.set_enabled(False)
    assert config.is_enabled() is False


def test_normalize_domain():
    """Test domain normalization."""
    assert config.normalize_domain("twitter.com") == "twitter.com"
    assert config.normalize_domain("www.twitter.com") == "twitter.com"
    assert config.normalize_domain("https://twitter.com") == "twitter.com"
    assert config.normalize_domain("https://www.twitter.com/path") == "twitter.com"
    assert config.normalize_domain("http://TWITTER.COM") == "twitter.com"

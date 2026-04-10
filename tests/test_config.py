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
        "accountability_emails": [],
        "smtp_config": {
            "server": "",
            "port": 587,
            "username": "",
            "password": "",
        },
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


def test_add_accountability_email(temp_config_dir):
    """Test adding an accountability partner email."""
    assert config.add_accountability_email("partner@example.com") is True
    emails = config.get_accountability_emails()
    assert "partner@example.com" in emails


def test_add_accountability_email_duplicate(temp_config_dir):
    """Test adding a duplicate accountability partner email."""
    config.add_accountability_email("partner@example.com")
    assert config.add_accountability_email("partner@example.com") is False


def test_add_accountability_email_normalizes_case(temp_config_dir):
    """Test that email is normalized to lowercase."""
    config.add_accountability_email("Partner@EXAMPLE.com")
    emails = config.get_accountability_emails()
    assert "partner@example.com" in emails


def test_add_accountability_email_strips_whitespace(temp_config_dir):
    """Test that email whitespace is stripped."""
    config.add_accountability_email("  partner@example.com  ")
    emails = config.get_accountability_emails()
    assert "partner@example.com" in emails


def test_remove_accountability_email(temp_config_dir):
    """Test removing an accountability partner email."""
    config.add_accountability_email("partner@example.com")
    assert config.remove_accountability_email("partner@example.com") is True
    emails = config.get_accountability_emails()
    assert "partner@example.com" not in emails


def test_remove_accountability_email_not_found(temp_config_dir):
    """Test removing an email that doesn't exist."""
    assert config.remove_accountability_email("nobody@example.com") is False


def test_get_accountability_emails_empty(temp_config_dir):
    """Test getting accountability emails when empty."""
    emails = config.get_accountability_emails()
    assert emails == []


def test_get_accountability_emails(temp_config_dir):
    """Test getting accountability emails."""
    config.add_accountability_email("partner1@example.com")
    config.add_accountability_email("partner2@example.com")
    emails = config.get_accountability_emails()
    assert "partner1@example.com" in emails
    assert "partner2@example.com" in emails


def test_set_smtp_config(temp_config_dir):
    """Test setting SMTP configuration."""
    config.set_smtp_config("smtp.example.com", 587, "user@example.com", "password123")
    smtp = config.get_smtp_config()
    assert smtp["server"] == "smtp.example.com"
    assert smtp["port"] == 587
    assert smtp["username"] == "user@example.com"
    assert smtp["password"] == "password123"


def test_get_smtp_config_default(temp_config_dir):
    """Test getting SMTP config when not configured."""
    smtp = config.get_smtp_config()
    assert smtp["server"] == ""
    assert smtp["port"] == 587
    assert smtp["username"] == ""
    assert smtp["password"] == ""


def test_load_config_fills_new_keys(temp_config_dir):
    """Test that loading config fills in new accountability keys."""
    # Create config without new keys
    temp_config_dir.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_config_dir, "w") as f:
        json.dump({"blocked_sites": ["test.com"], "enabled": True, "schedules": []}, f)

    cfg = config.load_config()
    assert cfg["accountability_emails"] == []
    assert cfg["smtp_config"]["server"] == ""
    assert cfg["smtp_config"]["port"] == 587

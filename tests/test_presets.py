"""Tests for presets module."""

import pytest

from timesaver.presets import PRESETS, get_preset, list_presets


def test_social_preset_exists():
    """Test that social preset exists and has expected sites."""
    sites = get_preset("social")
    assert "twitter.com" in sites
    assert "facebook.com" in sites
    assert "reddit.com" in sites


def test_news_preset_exists():
    """Test that news preset exists and has expected sites."""
    sites = get_preset("news")
    assert "news.ycombinator.com" in sites
    assert "cnn.com" in sites


def test_all_preset_combines_categories():
    """Test that 'all' preset combines social and news."""
    all_sites = get_preset("all")
    social_sites = get_preset("social")
    news_sites = get_preset("news")

    for site in social_sites:
        assert site in all_sites
    for site in news_sites:
        assert site in all_sites


def test_get_preset_invalid():
    """Test that invalid preset raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        get_preset("nonexistent")
    assert "Unknown preset" in str(exc_info.value)
    assert "nonexistent" in str(exc_info.value)


def test_list_presets():
    """Test listing available presets."""
    names = list_presets()
    assert "social" in names
    assert "news" in names
    assert "all" in names


def test_presets_dict_structure():
    """Test that PRESETS dict has expected structure."""
    assert isinstance(PRESETS, dict)
    for name, sites in PRESETS.items():
        assert isinstance(name, str)
        assert isinstance(sites, list)
        for site in sites:
            assert isinstance(site, str)
            assert "." in site  # Should be a domain

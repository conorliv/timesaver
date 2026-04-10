"""Preset site categories for blocking."""

PRESETS: dict[str, list[str]] = {
    "social": [
        "twitter.com",
        "x.com",
        "facebook.com",
        "instagram.com",
        "tiktok.com",
        "reddit.com",
        "linkedin.com",
        "snapchat.com",
        "threads.net",
    ],
    "news": [
        "news.ycombinator.com",
        "cnn.com",
        "foxnews.com",
        "bbc.com",
        "nytimes.com",
        "theguardian.com",
    ],
}

# "all" preset combines all categories
PRESETS["all"] = PRESETS["social"] + PRESETS["news"]


def get_preset(name: str) -> list[str]:
    """Get a preset by name.

    Args:
        name: Name of the preset (social, news, all)

    Returns:
        List of domains in the preset

    Raises:
        ValueError: If preset name is not found
    """
    if name not in PRESETS:
        available = ", ".join(PRESETS.keys())
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")
    return PRESETS[name]


def list_presets() -> list[str]:
    """Get list of available preset names."""
    return list(PRESETS.keys())

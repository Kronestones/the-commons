"""Profile theme system — a curated, safe stand-in for "custom CSS": users pick from a
fixed set of palettes rather than typing HTML/CSS, so there's no injection surface.

Stored as JSON in User.profile_theme, e.g. {"palette": "bubblegum"}.
Later stages add "font", "stickers", "background", and country palettes to this same dict.
"""
import json

PALETTES = {
    "bubblegum": {
        "label": "Bubblegum",
        "primary": "#ff6fb0", "secondary": "#c9a7ff", "accent": "#ff9edb",
        "bg": "#fff0f8", "text": "#4a1f38",
        "card_bg": "#ffffff",
    },
    "y2k_chrome": {
        "label": "Y2K Chrome",
        "primary": "#8fa3b3", "secondary": "#1c1c1e", "accent": "#4fc3f7",
        "bg": "#e8ecef", "text": "#1c1c1e",
        "card_bg": "#ffffff",
    },
    "cyberpunk": {
        "label": "Cyberpunk",
        "primary": "#ff2fd0", "secondary": "#0d0d0d", "accent": "#39ff14",
        "bg": "#12001a", "text": "#f5f5f5",
        "card_bg": "#1e0530",
    },
    "forest_witch": {
        "label": "Forest Witch",
        "primary": "#1e4d2b", "secondary": "#d4af37", "accent": "#4a7c59",
        "bg": "#12240f", "text": "#f2e9d8",
        "card_bg": "#1c3618",
    },
    "sunset_glow": {
        "label": "Sunset Glow",
        "primary": "#ff8a5c", "secondary": "#c46fd6", "accent": "#ffd15c",
        "bg": "#2b1930", "text": "#fff3e6",
        "card_bg": "#3a2340",
    },
    "barbie_energy": {
        "label": "Barbie Energy",
        "primary": "#ff1493", "secondary": "#ffffff", "accent": "#ffd700",
        "bg": "#ffe4f1", "text": "#7a0045",
        "card_bg": "#ffffff",
    },
    "pride": {
        "label": "Pride",
        "primary": "#e02020", "secondary": "#2050e0", "accent": "#ffd400",
        "bg": "#120d1c", "text": "#ffffff",
        "card_bg": "#1e1830",
        "gradient": "linear-gradient(90deg, #e02020, #ff9500, #ffd400, #2ba84a, #2050e0, #7b2fbe)",
    },
}


def load_theme(user) -> dict:
    """Safely parse a User's profile_theme column. Never raises."""
    if not getattr(user, "profile_theme", None):
        return {}
    try:
        return json.loads(user.profile_theme)
    except (json.JSONDecodeError, TypeError):
        return {}


def set_palette(user, palette_key: str) -> dict:
    """
    Validates and stores a palette choice on the user object
    (caller is responsible for db.commit()).
    """
    if palette_key not in PALETTES:
        return {"ok": False, "error": "That's not a theme we offer."}

    data = load_theme(user)
    data["palette"] = palette_key
    user.profile_theme = json.dumps(data)
    return {"ok": True, "palette": palette_key}


def remove_palette(user) -> dict:
    data = load_theme(user)
    data.pop("palette", None)
    user.profile_theme = json.dumps(data)
    return {"ok": True}


def get_theme_output(user) -> dict:
    """
    Returns what the profile template needs, or None if the user hasn't
    picked a theme (so the page just uses the site default green look).
    """
    data = load_theme(user)
    key = data.get("palette")
    if not key or key not in PALETTES:
        return None
    p = PALETTES[key]
    return {"key": key, **p}


def list_palettes() -> list:
    """For the edit-profile picker: [{"key": ..., "label": ..., "primary": ...}, ...]."""
    return [{"key": k, "label": v["label"], "primary": v["primary"],
             "secondary": v["secondary"], "accent": v["accent"]}
            for k, v in PALETTES.items()]

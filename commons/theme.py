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
    "galaxy": {
        "label": "Galaxy",
        "primary": "#6a4fd6", "secondary": "#1b1035", "accent": "#b39ddb",
        "bg": "#0d0620", "text": "#f0e9ff",
        "card_bg": "#1a0f38",
    },
    "mermaid_core": {
        "label": "Mermaid Core",
        "primary": "#2fd9c4", "secondary": "#0a3d40", "accent": "#7fe8d0",
        "bg": "#e6fbf8", "text": "#063a37",
        "card_bg": "#ffffff",
    },
    "retro_arcade": {
        "label": "Retro Arcade",
        "primary": "#ff5e1a", "secondary": "#1a0033", "accent": "#ff2fb0",
        "bg": "#12001f", "text": "#fff0e0",
        "card_bg": "#240a3a",
    },
    "cottagecore": {
        "label": "Cottagecore",
        "primary": "#7c9473", "secondary": "#d8c3a5", "accent": "#c98a97",
        "bg": "#f6f1e7", "text": "#3f4a37",
        "card_bg": "#ffffff",
    },
    "vaporwave": {
        "label": "Vaporwave",
        "primary": "#ff6ec7", "secondary": "#7afcff", "accent": "#b967ff",
        "bg": "#1a1033", "text": "#f5f5ff",
        "card_bg": "#26124a",
        "gradient": "linear-gradient(135deg, #ff6ec7, #7afcff)",
    },
    "goth_glam": {
        "label": "Goth Glam",
        "primary": "#6b0f1a", "secondary": "#0d0d0d", "accent": "#c0c0c0",
        "bg": "#0a0a0a", "text": "#eaeaea",
        "card_bg": "#1a1a1a",
    },
    "tropical_punch": {
        "label": "Tropical Punch",
        "primary": "#ff6f59", "secondary": "#17c3b2", "accent": "#ffcb47",
        "bg": "#fff8ea", "text": "#073b3a",
        "card_bg": "#ffffff",
    },
    "midnight_gold": {
        "label": "Midnight Gold",
        "primary": "#d4af37", "secondary": "#0b1120", "accent": "#f1d97a",
        "bg": "#05070f", "text": "#f5e9c8",
        "card_bg": "#10162a",
    },
    "jewish_heritage": {
        "label": "Jewish Heritage",
        "primary": "#0038b8", "secondary": "#ffffff", "accent": "#7ba7e0",
        "bg": "#f4f7ff", "text": "#0a1a3a",
        "card_bg": "#ffffff",
    },
    "lavender_dreams": {
        "label": "Lavender Dreams",
        "primary": "#b39ddb", "secondary": "#e8daf5", "accent": "#ffffff",
        "bg": "#f6f0fb", "text": "#4a3a5c",
        "card_bg": "#ffffff",
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

FONTS = {
    "bungee":           {"label": "Bungee",              "family": "'Bungee', cursive",             "google": "family=Bungee"},
    "caveat":           {"label": "Caveat",               "family": "'Caveat', cursive",             "google": "family=Caveat:wght@700"},
    "press_start":      {"label": "Press Start 2P",       "family": "'Press Start 2P', cursive",     "google": "family=Press+Start+2P"},
    "fredoka":          {"label": "Fredoka",               "family": "'Fredoka', sans-serif",         "google": "family=Fredoka:wght@600"},
    "pacifico":         {"label": "Pacifico",              "family": "'Pacifico', cursive",           "google": "family=Pacifico"},
    "permanent_marker": {"label": "Permanent Marker",      "family": "'Permanent Marker', cursive",   "google": "family=Permanent+Marker"},
    "bangers":          {"label": "Bangers",               "family": "'Bangers', cursive",            "google": "family=Bangers"},
    "monoton":          {"label": "Monoton",               "family": "'Monoton', cursive",            "google": "family=Monoton"},
    "righteous":        {"label": "Righteous",             "family": "'Righteous', cursive",          "google": "family=Righteous"},
    "playfair":         {"label": "Playfair Display",      "family": "'Playfair Display', serif",     "google": "family=Playfair+Display:wght@700"},
    "space_mono":       {"label": "Space Mono",            "family": "'Space Mono', monospace",       "google": "family=Space+Mono:wght@700"},
    "comic_neue":       {"label": "Comic Neue",            "family": "'Comic Neue', cursive",         "google": "family=Comic+Neue:wght@700"},
    "lobster":          {"label": "Lobster",               "family": "'Lobster', cursive",            "google": "family=Lobster"},
    "orbitron":         {"label": "Orbitron",              "family": "'Orbitron', sans-serif",        "google": "family=Orbitron:wght@700"},
    "shadows_light":    {"label": "Shadows Into Light",    "family": "'Shadows Into Light', cursive", "google": "family=Shadows+Into+Light"},
}


def set_font(user, font_key: str) -> dict:
    """
    Validates and stores a font choice on the user object
    (caller is responsible for db.commit()). Independent of the color palette —
    someone can pick a font with no palette, or a palette with no font.
    """
    if font_key not in FONTS:
        return {"ok": False, "error": "That's not a font we offer."}

    data = load_theme(user)
    data["font"] = font_key
    user.profile_theme = json.dumps(data)
    return {"ok": True, "font": font_key}


def remove_font(user) -> dict:
    data = load_theme(user)
    data.pop("font", None)
    user.profile_theme = json.dumps(data)
    return {"ok": True}


def get_font_output(user) -> dict:
    """Returns what the profile template needs, or None if no font is picked."""
    data = load_theme(user)
    key = data.get("font")
    if not key or key not in FONTS:
        return None
    f = FONTS[key]
    return {"key": key, **f}


def list_fonts() -> list:
    """For the edit-profile picker: [{"key": ..., "label": ..., "family": ...}, ...]."""
    return [{"key": k, "label": v["label"], "family": v["family"]}
            for k, v in FONTS.items()]


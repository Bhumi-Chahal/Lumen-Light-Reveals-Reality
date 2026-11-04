"""engine/characters.py — Cosmetic Character Profiles and Palettes for Lumen.

Defines the available cosmetic characters for Phase 1 Character Selection.
All characters share identical physics, speed, hitboxes, animations, and gameplay mechanics.
Variations are purely visual/cosmetic, matching the ancient wizard-explorer aesthetic:
- Indigo Scholar (Default): Classic indigo wizard robes, celestial gold trim, silver-white beard.
- Solar Acolyte: Radiant crimson/amber sun vestments, solar gold banding, warm grey beard.
- Emerald Sage: Deep moss and jade silks, silver filigree trim, elder frost beard.
"""

from typing import Any

CHARACTER_PROFILES: dict[str, dict[str, Any]] = {
    "indigo": {
        "id": "indigo",
        "name": "Indigo Scholar",
        "title": "Adept of Celestial Light",
        "description": "Wears traditional indigo robes and star-gold trims. A classic temple scholar attuned to ancient light and geometry.",
        "palette": {
            "robe_dark": (26, 36, 85),
            "robe_color": (38, 52, 125),
            "robe_light": (52, 72, 168),
            "gold_trim": (215, 175, 60),
            "hat_color": (32, 44, 105),
            "hat_light": (48, 65, 150),
            "hat_trim": (220, 180, 60),
            "beard_white": (248, 248, 252),
            "beard_shadow": (200, 205, 218),
            "skin_color": (220, 185, 150),
            "boot_color": (48, 34, 22),
            "belt_buckle": (250, 220, 100),
        },
    },
    "solar": {
        "id": "solar",
        "name": "Solar Acolyte",
        "title": "Guardian of the Dawn Pyres",
        "description": "Clad in crimson vestments with solar brass ornaments. Devoted to the radiant sun crystals of the upper terraces.",
        "palette": {
            "robe_dark": (95, 26, 24),
            "robe_color": (145, 42, 38),
            "robe_light": (185, 62, 52),
            "gold_trim": (245, 195, 65),
            "hat_color": (125, 34, 32),
            "hat_light": (165, 50, 44),
            "hat_trim": (245, 195, 65),
            "beard_white": (218, 208, 198),
            "beard_shadow": (172, 162, 152),
            "skin_color": (225, 188, 155),
            "boot_color": (54, 32, 22),
            "belt_buckle": (255, 225, 110),
        },
    },
    "emerald": {
        "id": "emerald",
        "name": "Emerald Sage",
        "title": "Watcher of Verdant Sanctums",
        "description": "Garbed in deep moss and jade silks with silver filigree. An elder seer of the subterranean forest sanctuaries.",
        "palette": {
            "robe_dark": (20, 68, 44),
            "robe_color": (32, 98, 64),
            "robe_light": (48, 138, 92),
            "gold_trim": (205, 220, 215),
            "hat_color": (26, 82, 54),
            "hat_light": (40, 118, 78),
            "hat_trim": (215, 230, 225),
            "beard_white": (232, 236, 238),
            "beard_shadow": (186, 196, 200),
            "skin_color": (215, 185, 155),
            "boot_color": (38, 42, 36),
            "belt_buckle": (220, 240, 235),
        },
    },
}

CHARACTER_ORDER = ["indigo", "solar", "emerald"]
DEFAULT_CHARACTER = "indigo"


def get_character_profile(character_id: str) -> dict[str, Any]:
    """Retrieves the character profile dictionary, falling back to default if invalid."""
    if character_id in CHARACTER_PROFILES:
        return CHARACTER_PROFILES[character_id]
    return CHARACTER_PROFILES[DEFAULT_CHARACTER]


def get_character_palette(character_id: str) -> dict[str, tuple[int, int, int]]:
    """Retrieves the color palette dictionary for a given character ID."""
    return get_character_profile(character_id)["palette"]

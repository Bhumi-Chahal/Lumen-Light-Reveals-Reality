"""engine/settings.py — Configuration and Persistence System for Lumen.

Manages user settings across Audio, Display, Accessibility, Gameplay, and Character Selection.
Handles missing, malformed, or partial settings files safely with graceful defaults.
Saves atomically to `saves/settings.json`.
"""

import json
import os
from pathlib import Path
from typing import Any
from engine.characters import DEFAULT_CHARACTER, CHARACTER_PROFILES

SETTINGS_FILE = Path(__file__).resolve().parent.parent / "saves" / "settings.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    # Character Selection (Feature A)
    "selected_character": DEFAULT_CHARACTER,
    # Audio Settings (Feature B)
    "music_volume": 0.8,
    "sfx_volume": 1.0,
    "muted": False,
    # Display Settings (Feature B)
    "fullscreen": True,
    # Accessibility Settings (Feature B)
    "screen_shake": True,
    "reduced_motion": False,
    # Gameplay & Interface Settings (Feature B & C)
    "show_minimap": True,
    "contextual_prompts": True,
}


class SettingsManager:
    """Singleton manager for game settings persistence and live application."""

    def __init__(self, filepath: Path | None = None, save_path: Path | None = None, config_path: Path | None = None):
        self.filepath = filepath or save_path or config_path or SETTINGS_FILE
        self._data: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.load()

    @property
    def minimap_enabled(self) -> bool:
        return self.show_minimap

    @minimap_enabled.setter
    def minimap_enabled(self, val: bool):
        self.show_minimap = val

    @property
    def selected_character(self) -> str:
        return self._data.get("selected_character", DEFAULT_CHARACTER)

    @selected_character.setter
    def selected_character(self, val: str):
        if val in CHARACTER_PROFILES:
            self._data["selected_character"] = val
            self.save()

    @property
    def music_volume(self) -> float:
        return float(self._data.get("music_volume", 0.8))

    @music_volume.setter
    def music_volume(self, val: float):
        self._data["music_volume"] = max(0.0, min(1.0, float(val)))
        self.save()

    @property
    def sfx_volume(self) -> float:
        return float(self._data.get("sfx_volume", 1.0))

    @sfx_volume.setter
    def sfx_volume(self, val: float):
        self._data["sfx_volume"] = max(0.0, min(1.0, float(val)))
        self.save()

    @property
    def muted(self) -> bool:
        return bool(self._data.get("muted", False))

    @muted.setter
    def muted(self, val: bool):
        self._data["muted"] = bool(val)
        self.save()

    @property
    def fullscreen(self) -> bool:
        return bool(self._data.get("fullscreen", True))

    @fullscreen.setter
    def fullscreen(self, val: bool):
        self._data["fullscreen"] = bool(val)
        self.save()

    @property
    def screen_shake(self) -> bool:
        return bool(self._data.get("screen_shake", True))

    @screen_shake.setter
    def screen_shake(self, val: bool):
        self._data["screen_shake"] = bool(val)
        self.save()

    @property
    def shake_enabled(self) -> bool:
        return self.screen_shake

    @shake_enabled.setter
    def shake_enabled(self, val: bool):
        self.screen_shake = val

    @property
    def reduced_motion(self) -> bool:
        return bool(self._data.get("reduced_motion", False))

    @reduced_motion.setter
    def reduced_motion(self, val: bool):
        self._data["reduced_motion"] = bool(val)
        self.save()

    @property
    def show_minimap(self) -> bool:
        return bool(self._data.get("show_minimap", True))

    @show_minimap.setter
    def show_minimap(self, val: bool):
        self._data["show_minimap"] = bool(val)
        self.save()

    @property
    def contextual_prompts(self) -> bool:
        return bool(self._data.get("contextual_prompts", True))

    @contextual_prompts.setter
    def contextual_prompts(self, val: bool):
        self._data["contextual_prompts"] = bool(val)
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))

    def set(self, key: str, val: Any, auto_save: bool = True):
        if key in DEFAULT_SETTINGS:
            self._data[key] = val
            if auto_save:
                self.save()

    def load(self):
        """Loads settings from file. Falls back gracefully to defaults on any error."""
        self._data = dict(DEFAULT_SETTINGS)
        if not self.filepath.exists():
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return
                loaded = json.loads(content)
                if isinstance(loaded, dict):
                    # Validate and copy supported keys
                    for key, def_val in DEFAULT_SETTINGS.items():
                        if key in loaded:
                            val = loaded[key]
                            # Validate type
                            if isinstance(def_val, bool) and isinstance(val, bool):
                                self._data[key] = val
                            elif isinstance(def_val, float) and (isinstance(val, float) or isinstance(val, int)):
                                self._data[key] = max(0.0, min(1.0, float(val)))
                            elif key == "selected_character" and isinstance(val, str) and val in CHARACTER_PROFILES:
                                self._data[key] = val
        except (json.JSONDecodeError, OSError, ValueError, TypeError):
            # Graceful fallback on malformed or corrupted file
            self._data = dict(DEFAULT_SETTINGS)

    def save(self) -> bool:
        """Atomically saves settings to JSON file."""
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.filepath.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.filepath)
            return True
        except OSError:
            return False

    def reset_to_defaults(self):
        """Resets all settings back to default values and saves."""
        self._data = dict(DEFAULT_SETTINGS)
        self.save()

    def apply_to_game(self, game_manager):
        """Applies relevant live settings to game components without resetting level state."""
        # 1. Audio
        try:
            from systems.audio import audio
            audio.set_sfx_volume(self.sfx_volume)
            audio.set_music_volume(self.music_volume)
            audio.set_muted(self.muted)
        except Exception:
            pass

        # 2. Camera screen shake & reduced motion
        if hasattr(game_manager, "camera"):
            game_manager.camera.shake_enabled = self.screen_shake and not self.reduced_motion

        # 3. Minimap visibility
        if hasattr(game_manager, "minimap"):
            game_manager.minimap.visible = self.show_minimap

        # 4. Player cosmetic character
        if hasattr(game_manager, "player") and game_manager.player:
            game_manager.player.character_id = self.selected_character


# Global settings singleton
settings = SettingsManager()

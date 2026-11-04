"""
Lumen — engine/progression.py
Milestone 6: Level Selection and Progression Persistence.

Manages persistent level unlocks across playthroughs:
- Level 1 is always unlocked.
- Levels 2, 3, 4 are unlocked sequentially through story progression.
- Level 5 is marked 'Coming Soon' and cannot be unlocked until implemented.
- Unlocks persist across deaths, runs, and restarts in `saves/progression.json`.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

PROGRESSION_FILE = Path(__file__).resolve().parent.parent / "saves" / "progression.json"

LEVEL_SLOTS: List[Dict[str, Any]] = [
    {
        "id": "level1",
        "number": 1,
        "title": "Level 1 — The First Light",
        "name": "The Ancient Sanctum",
        "subtitle": "Awakening & The Sun Door",
        "description": "Navigate the subterranean sanctum in darkness. Recover the sacred lantern and collect the three keys to unseal the ancient portal.",
        "implemented": True,
    },
    {
        "id": "level2",
        "number": 2,
        "title": "Level 2 — The Shadow Trial",
        "name": "The Deepening Dark",
        "subtitle": "Battery Conservation & Shadow Threat",
        "description": "Venture into the catacombs where the Shadow lurks. Manage limited battery, discover hidden passages, and gather the three refractor mirrors.",
        "implemented": True,
    },
    {
        "id": "level3",
        "number": 3,
        "title": "Level 3 — The Mirror Chambers",
        "name": "The Path of Light",
        "subtitle": "Mirror Reflection & Crystal Resonance",
        "description": "Align refractor mirrors and direct colored light beams through ancient chambers to resonate the three celestial crystals.",
        "implemented": True,
    },
    {
        "id": "level4",
        "number": 4,
        "title": "Level 4 — The Ancient Forge",
        "name": "The Ancient Forge",
        "subtitle": "Harmonization Puzzle & The Lumen Sigil",
        "description": "Enter the volcanic vault. Restore faded runic inscriptions and submit the correct relic combination to awaken the Guardian and claim the Lumen Sigil.",
        "implemented": True,
    },
    {
        "id": "level5",
        "number": 5,
        "title": "Level 5 — The Hall of Fate",
        "name": "The Hall of Fate",
        "subtitle": "Coming Soon",
        "description": "The deep sanctum beyond the ancient northern portal. Three monumental arches await in silent trial. Under construction.",
        "implemented": False,
    },
]


class ProgressionManager:
    """Manages persistent level unlocks and story progression across game sessions."""

    DEFAULT_UNLOCKED: Set[str] = {"level1"}

    def __init__(self, filepath: Optional[Path] = None):
        if filepath is not None:
            self.filepath = Path(filepath)
        elif "LUMEN_PROGRESSION_SAVE" in os.environ:
            self.filepath = Path(os.environ["LUMEN_PROGRESSION_SAVE"])
        else:
            self.filepath = PROGRESSION_FILE
        self._unlocked: Set[str] = set(self.DEFAULT_UNLOCKED)
        self._story_reached: Set[str] = set(self.DEFAULT_UNLOCKED)
        self._story_current: str = "level1"
        self.load()

    @property
    def unlocked_levels(self) -> Set[str]:
        """Returns a copy of the unlocked level IDs."""
        return set(self._unlocked)

    @property
    def story_reached_levels(self) -> Set[str]:
        """Returns a copy of the levels reached in story progression."""
        return set(self._story_reached)

    @property
    def story_current_level(self) -> str:
        """Returns the player's current story position."""
        return self._story_current

    def is_unlocked(self, level_id: str) -> bool:
        """Returns True if the level is unlocked and playable."""
        lid = str(level_id).lower()
        if lid == "level5":
            return False  # Coming soon
        return lid in self._unlocked

    def is_story_reached(self, level_id: str) -> bool:
        """Returns True if the level was previously reached during story progression."""
        lid = str(level_id).lower()
        if lid == "level5":
            return False
        return lid in self._story_reached

    def is_coming_soon(self, level_id: str) -> bool:
        """Returns True if the level is marked as Coming Soon."""
        return str(level_id).lower() == "level5"

    def get_status(self, level_id: str) -> str:
        """Returns 'unlocked', 'locked', or 'coming_soon'."""
        lid = str(level_id).lower()
        if self.is_coming_soon(lid):
            return "coming_soon"
        if self.is_unlocked(lid):
            return "unlocked"
        return "locked"

    def unlock_level(self, level_id: str) -> bool:
        """
        Unlocks the specified level if valid.
        Reaching Level 4 automatically ensures Levels 1-4 are unlocked.
        Level 5 cannot be unlocked while marked Coming Soon.
        """
        lid = str(level_id).lower()
        if lid == "level5":
            return False

        valid_ids = {slot["id"] for slot in LEVEL_SLOTS if slot["implemented"]}
        if lid not in valid_ids:
            return False

        newly_unlocked = False
        if lid not in self._unlocked:
            self._unlocked.add(lid)
            newly_unlocked = True

        # Reaching Level 4 unlocks Levels 1-4
        if lid == "level4":
            for prev in ("level1", "level2", "level3"):
                if prev not in self._unlocked:
                    self._unlocked.add(prev)
                    newly_unlocked = True

        if newly_unlocked:
            self.save()
        return True

    def unlock_story_level(self, level_id: str) -> bool:
        """Unlocks a level reached through normal story progression."""
        lid = str(level_id).lower()
        if lid == "level5":
            return False

        valid_ids = {slot["id"] for slot in LEVEL_SLOTS if slot["implemented"]}
        if lid not in valid_ids:
            return False

        changed = False
        if lid not in self._story_reached:
            self._story_reached.add(lid)
            changed = True
        if lid not in self._unlocked:
            self._unlocked.add(lid)
            changed = True

        if changed:
            self.save()
        return True

    def unlock_next_after(self, current_level_id: str) -> Optional[str]:
        """Unlocks the level sequentially following current_level_id."""
        lid = str(current_level_id).lower()
        order = ["level1", "level2", "level3", "level4", "level5"]
        if lid in order:
            idx = order.index(lid)
            if idx + 1 < len(order):
                next_lvl = order[idx + 1]
                if next_lvl != "level5":
                    self.unlock_level(next_lvl)
                    return next_lvl
        return None

    def reset_story_run(self) -> None:
        """Resets story run progression back to Level 1 while retaining persistent practice unlocks."""
        self._story_reached = set(self.DEFAULT_UNLOCKED)
        self._story_current = "level1"
        self.save()

    def reset_to_default(self) -> None:
        """Resets all unlocked levels and story back to initial baseline (Level 1 only)."""
        self._unlocked = set(self.DEFAULT_UNLOCKED)
        self._story_reached = set(self.DEFAULT_UNLOCKED)
        self._story_current = "level1"
        self.save()

    def save(self) -> bool:
        """Persists unlock and story state atomically to disk."""
        data = {
            "version": 2,
            "unlocked": sorted(list(self._unlocked)),
            "story_reached": sorted(list(self._story_reached)),
            "story_current": self._story_current,
        }
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            temp = self.filepath.with_suffix(".tmp")
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, self.filepath)
            return True
        except OSError:
            return False

    def load(self) -> None:
        """Loads unlock state from disk, safely migrating v1 data without deleting saves."""
        self._unlocked = set(self.DEFAULT_UNLOCKED)
        self._story_reached = set(self.DEFAULT_UNLOCKED)
        self._story_current = "level1"
        if not self.filepath.exists():
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return
                data = json.loads(content)

            # Load persistent unlocked levels (retained for practice / dev access)
            unlocked = data.get("unlocked", data.get("unlocked_levels", []))
            for lvl in unlocked:
                lvl_str = str(lvl).lower()
                if lvl_str != "level5" and any(s["id"] == lvl_str for s in LEVEL_SLOTS):
                    self._unlocked.add(lvl_str)

            # Story progression: if v2 data exists, load it; if legacy v1, initialize story at level1
            # so historical unlock data cannot bypass new story-access rules.
            story_reached = data.get("story_reached", None)
            if story_reached is not None and isinstance(story_reached, list):
                self._story_reached = {str(l).lower() for l in story_reached if str(l).lower() != "level5"}
                if not self._story_reached:
                    self._story_reached = {"level1"}
            else:
                self._story_reached = {"level1"}

            self._story_current = str(data.get("story_current", "level1")).lower()
            if self._story_current not in self._story_reached:
                self._story_current = "level1"
        except Exception:
            self._unlocked = set(self.DEFAULT_UNLOCKED)
            self._story_reached = set(self.DEFAULT_UNLOCKED)
            self._story_current = "level1"


# Global singleton instance
progression = ProgressionManager()

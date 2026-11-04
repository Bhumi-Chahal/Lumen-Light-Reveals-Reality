"""systems/forge.py — Ancient Forge Combination Engine (Milestone 4C).

Pure logical domain engine implementing the Forge combination rules:
- 3 keys × 3 mirrors × 3 crystals = 27 possible combinations.
- Exactly two valid combinations in (key_id, mirror_id, crystal_id) order.
- Maximum 3 attempts per playthrough.
- Incomplete submissions consume 0 attempts.
- Correct combination solves the Forge and stores successful combination.
- Third incorrect submission locks the Forge for the playthrough.
- Zero item consumption (inventory remains untouched).
- Full state serialization for persistence.
"""

from typing import Any


ALL_KEYS: tuple[str, ...] = ("key_bronze", "key_silver", "key_gold")
ALL_MIRRORS: tuple[str, ...] = ("mirror_red", "mirror_blue", "mirror_green")
ALL_CRYSTALS: tuple[str, ...] = ("crystal_1", "crystal_2", "crystal_3")

# Canonical set of valid combinations in (key_id, mirror_id, crystal_id) order
# Jumbled across colors and tiers to prevent obvious identical-color pairings
VALID_COMBINATIONS: frozenset[tuple[str, str, str]] = frozenset({
    ("key_silver", "mirror_blue", "crystal_2"),
    ("key_gold", "mirror_green", "crystal_3"),
})

MAX_FORGE_ATTEMPTS: int = 3


class ForgeEngine:
    """Encapsulates the state and rule evaluation for the Ancient Forge combination puzzle."""

    def __init__(self, max_attempts: int = MAX_FORGE_ATTEMPTS):
        self.max_attempts: int = max_attempts
        self.attempts_used: int = 0
        self.is_solved: bool = False
        self.is_locked: bool = False
        self.sigil_awarded: bool = False
        self.successful_combination: tuple[str, str, str] | None = None
        self.submission_history: list[tuple[str, str, str]] = []

    @property
    def attempts_left(self) -> int:
        """Returns remaining submission attempts."""
        return max(0, self.max_attempts - self.attempts_used)

    @property
    def is_complete(self) -> bool:
        """Alias indicating whether the Forge puzzle is solved."""
        return self.is_solved

    @staticmethod
    def get_all_possible_combinations() -> list[tuple[str, str, str]]:
        """Generates all 27 possible cartesian combinations."""
        combos = []
        for k in ALL_KEYS:
            for m in ALL_MIRRORS:
                for c in ALL_CRYSTALS:
                    combos.append((k, m, c))
        return combos

    @staticmethod
    def is_valid_combination(key_id: str | None, mirror_id: str | None, crystal_id: str | None) -> bool:
        """Checks if a given triple is one of the valid combinations."""
        if not (key_id and mirror_id and crystal_id):
            return False
        return (str(key_id), str(mirror_id), str(crystal_id)) in VALID_COMBINATIONS

    def submit(self, key_id: str | None, mirror_id: str | None, crystal_id: str | None) -> tuple[bool, str]:
        """Submits a candidate relic combination to the Forge.

        Returns:
            (success: bool, status: str)
            Status codes:
            - 'incomplete': Missing one or more relic selections (0 attempts consumed).
            - 'already_solved': Forge was already successfully solved (0 attempts consumed).
            - 'already_locked': Forge is already permanently locked (0 attempts consumed).
            - 'success': Valid combination submitted (1 attempt consumed; solved).
            - 'incorrect': Invalid combination submitted with attempts remaining (1 attempt consumed).
            - 'locked': Third invalid combination submitted; Forge is now locked (1 attempt consumed).
        """
        # Guard 1: Already solved
        if self.is_solved:
            return True, "already_solved"

        # Guard 2: Already locked
        if self.is_locked:
            return False, "already_locked"

        # Guard 3: Incomplete selection
        if not (key_id and mirror_id and crystal_id):
            return False, "incomplete"

        combo = (str(key_id), str(mirror_id), str(crystal_id))

        # Consume exactly one attempt
        self.attempts_used += 1
        self.submission_history.append(combo)

        # Validate against agreed combinations
        if combo in VALID_COMBINATIONS:
            self.is_solved = True
            self.sigil_awarded = True
            self.successful_combination = combo
            return True, "success"

        # Incorrect submission
        if self.attempts_used >= self.max_attempts:
            self.is_locked = True
            return False, "locked"

        return False, "incorrect"

    def reset(self):
        """Resets engine state to initial conditions."""
        self.attempts_used = 0
        self.is_solved = False
        self.is_locked = False
        self.sigil_awarded = False
        self.successful_combination = None
        self.submission_history.clear()

    def to_dict(self) -> dict[str, Any]:
        """Serializes Forge state for checkpoint persistence."""
        return {
            "attempts_used": self.attempts_used,
            "max_attempts": self.max_attempts,
            "is_solved": self.is_solved,
            "is_locked": self.is_locked,
            "sigil_awarded": self.sigil_awarded,
            "successful_combination": list(self.successful_combination) if self.successful_combination else None,
            "submission_history": [list(c) for c in self.submission_history],
        }

    def load_dict(self, data: dict[str, Any]):
        """Restores Forge state from checkpoint dictionary."""
        if not isinstance(data, dict):
            return
        self.attempts_used = int(data.get("attempts_used", 0))
        self.max_attempts = int(data.get("max_attempts", MAX_FORGE_ATTEMPTS))
        self.is_solved = bool(data.get("is_solved", False))
        self.is_locked = bool(data.get("is_locked", False))
        self.sigil_awarded = bool(data.get("sigil_awarded", self.is_solved))
        succ = data.get("successful_combination")
        self.successful_combination = tuple(succ) if succ and len(succ) == 3 else None
        history = data.get("submission_history", [])
        self.submission_history = [tuple(c) for c in history if len(c) == 3]

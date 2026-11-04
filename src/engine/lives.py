"""
Lumen - engine/lives.py
Milestone 5: Global Lives and Life-Loss Mechanics.

Tracks the player's remaining lives during a run (3 lives default),
manages invulnerability / damage cooldowns, and handles life loss.
"""

from typing import Tuple, Dict, Any, Optional


class LivesSystem:
    """Manages the player's life count and invulnerability status during a playthrough."""

    DEFAULT_MAX_LIVES: int = 3
    DEFAULT_INVULNERABILITY_DURATION: float = 3.0  # seconds

    def __init__(self, max_lives: int = DEFAULT_MAX_LIVES):
        self.max_lives: int = max(1, int(max_lives))
        self.lives: int = self.max_lives
        self.invulnerable_timer: float = 0.0
        self.invulnerability_duration: float = self.DEFAULT_INVULNERABILITY_DURATION
        self.last_damage_cause: str = ""

    @property
    def is_invulnerable(self) -> bool:
        """Returns True if the player is currently invulnerable to damage."""
        return self.invulnerable_timer > 0.0

    @property
    def is_alive(self) -> bool:
        """Returns True if the player has at least one life remaining."""
        return self.lives > 0

    def trigger_invulnerability(self, duration: Optional[float] = None) -> None:
        """Grants temporary invulnerability to prevent multi-frame or rapid repeated damage."""
        dur = duration if duration is not None else self.invulnerability_duration
        self.invulnerable_timer = max(self.invulnerable_timer, float(dur))

    def update(self, dt: float) -> None:
        """Tick down the invulnerability timer."""
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - float(dt))

    def lose_life(self, cause: str = "", ignore_invulnerability: bool = False) -> Tuple[bool, int, bool]:
        """
        Attempts to deduct exactly one life.
        
        Args:
            cause: Optional description of damage source.
            ignore_invulnerability: If True, bypasses invulnerability check
                (e.g. for scripted trial failure so prior cooldown does not block it).

        Returns:
            Tuple[life_lost: bool, remaining_lives: int, run_failed: bool]
            - life_lost: True if a life was successfully deducted (was not invulnerable).
            - remaining_lives: Remaining lives after deduction (0 if all exhausted).
            - run_failed: True if the 3rd life was lost, indicating total run exhaustion.
        """
        if not ignore_invulnerability and self.is_invulnerable:
            # Prevent repeated frame damage or damage during active invulnerability
            return False, self.lives, False

        self.last_damage_cause = cause
        self.lives = max(0, self.lives - 1)
        # Grant invulnerability immediately on damage to prevent multiple frame deductions
        self.trigger_invulnerability(self.invulnerability_duration)

        run_failed = (self.lives <= 0)
        return True, self.lives, run_failed

    def take_damage(self, source: str = "", ignore_invulnerability: bool = False) -> Tuple[bool, int, bool]:
        """Alias for lose_life."""
        return self.lose_life(cause=source, ignore_invulnerability=ignore_invulnerability)

    def restore_life(self, amount: int = 1) -> int:
        """Restores life up to max_lives."""
        self.lives = min(self.max_lives, self.lives + amount)
        return self.lives

    def reset_run(self) -> None:
        """Resets lives count to full for a new run."""
        self.lives = self.max_lives
        self.invulnerable_timer = 0.0
        self.last_damage_cause = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes lives system state for save files."""
        return {
            "lives": self.lives,
            "max_lives": self.max_lives,
            "invulnerable_timer": self.invulnerable_timer,
            "last_damage_cause": self.last_damage_cause,
        }

    def load_dict(self, data: Dict[str, Any]) -> None:
        """Restores lives system state from save files."""
        if not isinstance(data, dict):
            return
        self.max_lives = int(data.get("max_lives", self.DEFAULT_MAX_LIVES))
        self.lives = int(data.get("lives", self.max_lives))
        self.invulnerable_timer = float(data.get("invulnerable_timer", 0.0))
        self.last_damage_cause = str(data.get("last_damage_cause", ""))


def draw_lives_hud(
    surface: Any,
    x: int,
    y: int,
    lives: int,
    max_lives: int = 3,
    font: Optional[Any] = None,
) -> None:
    """Renders a sleek ancient-temple lives indicator with heart/crystal life pips."""
    import pygame
    if font is None:
        font = pygame.font.SysFont("consolas", 12, bold=True)

    # Label
    label_surf = font.render(f"Lives: {lives}/{max_lives}", True, (245, 225, 160))
    surface.blit(label_surf, (x, y))

    # Visual Life Orbs / Crystal Hearts
    start_px = x + label_surf.get_width() + 10
    py = y + label_surf.get_height() // 2
    for i in range(max_lives):
        px = start_px + i * 14
        active = (i < lives)
        if active:
            # Radiant ruby-gold life gem
            pygame.draw.polygon(surface, (235, 60, 75), [
                (px, py - 6), (px + 5, py - 1), (px, py + 6), (px - 5, py - 1)
            ])
            pygame.draw.polygon(surface, (255, 225, 130), [
                (px, py - 6), (px + 5, py - 1), (px, py + 6), (px - 5, py - 1)
            ], width=1)
        else:
            # Depleted hollow relic slot
            pygame.draw.polygon(surface, (70, 60, 75), [
                (px, py - 6), (px + 5, py - 1), (px, py + 6), (px - 5, py - 1)
            ], width=1)


"""content/level4.py — Level 4: The Ancient Forge.

Level 4 is the culmination of Levels 1–3: an abandoned machine-temple where the player
must restore a broken "Lumen Forge" whose image-processing and graphics systems have been
corrupted. The player repairs the systems through exploration, visual manipulation,
light transformation, particle stabilization, and environmental reconstruction.

Multi-zone architecture:
- Zone A: The Ashen Entrance (introduces Forge lore, ash particles, broken conduits, damaged mural).
- Zone B: The Resonance Foundry (physical interaction with Key, Mirror, and Crystal socket stations).
- Zone C: The Optical Gallery (light transformation, color-space RGB separation, harmonic frequency bands).
- Zone D: The Memory Vault (corrupted crystal plates, Gaussian denoising & unsharp mask edge restoration).
- Zone E: The Dynamic Core (Forge Core state machine, phasing platforms, particle streams, stabilization).
"""

import math
import numpy as np
import pygame

_SMOOTH_COOKIE_CACHE: dict[tuple, pygame.Surface] = {}

def _get_smooth_cutout_cookie(radius: int, max_alpha: int = 115) -> pygame.Surface:
    """Generates a cubic-hermite smoothstep radial alpha subtraction cookie."""
    key = ("cutout", radius, max_alpha)
    if key in _SMOOTH_COOKIE_CACHE:
        return _SMOOTH_COOKIE_CACHE[key]
    size = radius * 2
    y, x = np.ogrid[:size, :size]
    dist = np.sqrt((x - radius) ** 2 + (y - radius) ** 2)
    t = np.clip(dist / radius, 0.0, 1.0)
    smooth = 1.0 - (3.0 * t**2 - 2.0 * t**3)
    alpha = (smooth * max_alpha).astype(np.uint8)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.surfarray.pixels_alpha(surf)[:] = alpha.T
    _SMOOTH_COOKIE_CACHE[key] = surf
    return surf

def _get_smooth_glow_cookie(radius: int, color: tuple[int, int, int], center_alpha: int = 55) -> pygame.Surface:
    """Generates a smooth radial atmospheric bloom cookie with soft alpha falloff."""
    key = ("glow", radius, color[:3], center_alpha)
    if key in _SMOOTH_COOKIE_CACHE:
        return _SMOOTH_COOKIE_CACHE[key]
    size = radius * 2
    y, x = np.ogrid[:size, :size]
    dist = np.sqrt((x - radius) ** 2 + (y - radius) ** 2)
    t = np.clip(dist / radius, 0.0, 1.0)
    smooth = 1.0 - (3.0 * t**2 - 2.0 * t**3)
    alpha = (smooth * center_alpha).astype(np.uint8)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    r, g, b = color[:3]
    pygame.surfarray.pixels3d(surf)[:] = np.array([r, g, b], dtype=np.uint8)
    pygame.surfarray.pixels_alpha(surf)[:] = alpha.T
    _SMOOTH_COOKIE_CACHE[key] = surf
    return surf

LEVEL4_ZONE_DESCRIPTIONS = {
    "Dynamic Forge Core": "Ancient Forge: The Forge accepts only matching relics. Think carefully before making your choice.",
    "Resonance Foundry": "Ancient Forge: The Forge accepts only matching relics. Think carefully before making your choice.",
    "Ashen Entrance": "Ashen Entrance: Cross the threshold into the ancient heart of the Celestial Forge.",
}

import random
import os
import json
from pathlib import Path
import pygame

from engine.collision import move_with_collision
from engine.lighting import LightingSystem, build_darkness_mask
from systems.audio import audio
from systems.ui import wrap_text
from systems.forge import ForgeEngine, VALID_COMBINATIONS
from systems.forge_ui import ForgeModal
from systems.particles import ParticleSystem
from engine.settings import settings
from content.guardian_renderer import draw_guardian, draw_guardian_portrait
from content.forge_celestial_renderer import CelestialForgeRenderer, get_forge_lighting_radius
from content.level4_helpers import (
    bezier_quadratic,
    bezier_cubic,
    ease_in_out,
    lerp,
    CoreStabilizerMachine,
    ForgeJournalModal,
)
from content.level4_puzzles import (
    BrokenRelicPuzzle,
    MemoryFragmentsPuzzle,
    AncientBlueprintPuzzle,
    AncientRuleModal,
    ForgeEntranceModal,
)


GUARDIAN_SUCCESS_DIALOGUE = (
    "\"Awaken, traveler. You have balanced the ancient conduits "
    "and claimed the Lumen Sigil.\n\n"
    "Three colossal arches stand in silent vigil in the Hall of Fate ahead. One leads to safety, one brings ruin, "
    "and only the middle path opens the true way forward.\n\n"
    "Your Lumen Sigil will reveal a hidden architectural mark upon the stone arches. Trust your lantern and mirrors, "
    "and choose carefully.\""
)

GUARDIAN_REPEATABLE_LORE = (
    "\"The ancient Forge hums in tranquil harmony once more.\n\n"
    "Three colossal arches stand in silent vigil in the Hall of Fate ahead: "
    "one leads to safety, one brings ruin, and only the middle path opens the true way forward.\n\n"
    "Your Lumen Sigil will reveal a hidden architectural mark upon the stone arches. "
    "Trust your lantern and mirrors, and choose carefully.\""
)

GUARDIAN_LOCKED_DIALOGUE = (
    "The large stone guardian remains locked in petrified slumber.\n\n"
    "Its carved eyes are cold and dark, covered in old ash. "
    "Because the Forge failed to balance, no power flows through its stone body.\n\n"
    "It cannot speak or guide you while the Forge remains quiet."
)

GUARDIAN_DORMANT_DIALOGUE = (
    "A tall stone guardian stands quietly near the northern gate.\n\n"
    "Ancient lines run down its stone armor, connecting directly to the central Forge altar.\n\n"
    "The guardian sleeps deeply. Only lighting the Forge altar can awaken this ancient protector."
)

LEVEL4_DISCOVERY_TEXT = {
    "memory_vault": (
        "The Forge saved the temple's history as patterns of light rather than ink. "
        "Ash and heat blurred those pictures over time, leaving noise around the edges.\n\n"
        "The old plates explain how to fix them: find the pattern, clean the noise, "
        "and sharpen the edges."
    ),
    "optical_gallery": (
        "This room splits incoming light beams into clean colors before the Forge focuses them. "
        "Glass prisms filter the light: Emerald glass captures green, Azure glass aligns blue, "
        "and Crimson glass directs red.\n\n"
        "Ancient marks show that each mirror must match a key of the same rank to channel light into the crystals. "
        "A clear warning remains: the Bronze path is broken and cannot power the core."
    ),
    "dynamic_core": (
        "The Forge Core wakes in stages: quiet, warming, balancing, and stable. "
        "Its glowing sparks show when energy flows smoothly.\n\n"
        "Watch the glowing particles and place the matching relics upon the altar."
    ),
}

# Chamber Dimensions
L4_SCREEN_WIDTH = 800
L4_SCREEN_HEIGHT = 600
L4_WORLD_WIDTH = 1200
L4_WORLD_HEIGHT = 900

# Player Spawn Position (South Entrance facing North toward the Forge)
L4_SPAWN_X = 585.0
L4_SPAWN_Y = 740.0



class Level4Room:
    """The Ancient Forge Chamber: composition root for Level 4."""

    def __init__(self, inventory=None):
        self.inventory = inventory
        self.width = L4_WORLD_WIDTH
        self.height = L4_WORLD_HEIGHT

        # Chamber bounds
        self.playable_bounds = pygame.Rect(100, 120, 1000, 680)

        # Environmental structures & obstacles
        self.walls: list[pygame.Rect] = self._build_walls()
        self.pillars: list[pygame.Rect] = self._build_pillars()

        # Central Forge Altar & Crucible
        self.altar_rect = pygame.Rect(500, 360, 200, 140)
        self.crucible_rect = pygame.Rect(550, 395, 100, 70)
        self.sigil_rect = pygame.Rect(550, 395, 100, 70)
        self.selected_interaction_target = None

        # Three Relic Socket Triads (Physical stations in Zone B)
        self.key_sockets = [
            {"id": "socket_key_bronze", "relic_id": "key_bronze", "name": "Bronze Keyway", "rect": pygame.Rect(370, 420, 44, 44), "color": (180, 115, 60)},
            {"id": "socket_key_silver", "relic_id": "key_silver", "name": "Silver Keyway", "rect": pygame.Rect(370, 480, 44, 44), "color": (195, 200, 215)},
            {"id": "socket_key_gold", "relic_id": "key_gold", "name": "Gold Keyway", "rect": pygame.Rect(370, 540, 44, 44), "color": (240, 195, 55)},
        ]

        self.mirror_sockets = [
            {"id": "socket_mirror_red", "relic_id": "mirror_red", "name": "Crimson Reflector Stand", "rect": pygame.Rect(470, 260, 48, 48), "color": (230, 80, 70)},
            {"id": "socket_mirror_blue", "relic_id": "mirror_blue", "name": "Azure Reflector Stand", "rect": pygame.Rect(576, 260, 48, 48), "color": (70, 140, 240)},
            {"id": "socket_mirror_green", "relic_id": "mirror_green", "name": "Emerald Reflector Stand", "rect": pygame.Rect(682, 260, 48, 48), "color": (80, 220, 100)},
        ]

        self.crystal_sockets = [
            {"id": "socket_crystal_1", "relic_id": "crystal_1", "name": "Resonance Receptacle I", "rect": pygame.Rect(786, 420, 44, 44), "color": (245, 60, 80)},
            {"id": "socket_crystal_2", "relic_id": "crystal_2", "name": "Resonance Receptacle II", "rect": pygame.Rect(786, 480, 44, 44), "color": (60, 235, 110)},
            {"id": "socket_crystal_3", "relic_id": "crystal_3", "name": "Resonance Receptacle III", "rect": pygame.Rect(786, 540, 44, 44), "color": (60, 160, 255)},
        ]

        # Physical station occupation state
        self.placed_relics = {
            "keys": None,       # e.g. "key_silver"
            "mirrors": None,    # e.g. "mirror_blue"
            "crystals": None,   # e.g. "crystal_2"
        }
        self.mirror_rotations = {
            "socket_mirror_red": 0.0,
            "socket_mirror_blue": 0.0,
            "socket_mirror_green": 0.0,
        }

        # Sealed Forge Mechanism / Great Northern Threshold
        self.sealed_gate_rect = pygame.Rect(480, 60, 240, 60)

        # Entrance Threshold (South)
        self.entrance_rect = pygame.Rect(540, 780, 120, 40)

        # Ancient Guardian Dais (Northeast alcove beside the sealed gate)
        self.guardian_rect = pygame.Rect(740, 140, 52, 56)

        # All solid obstacles for AABB collision
        self.all_obstacles: list[pygame.Rect] = list(self.walls) + list(self.pillars) + [self.altar_rect, self.guardian_rect]
        for s in self.key_sockets:
            self.all_obstacles.append(s["rect"])
        for s in self.mirror_sockets:
            self.all_obstacles.append(s["rect"])
        for s in self.crystal_sockets:
            self.all_obstacles.append(s["rect"])

        # Atmospheric lighting & embers
        self.lighting = LightingSystem(L4_WORLD_WIDTH, L4_WORLD_HEIGHT, num_particles=45)
        self.flicker_phase = 0.0
        self.forge_phase = 0.0
        self.forge_state = "Dormant"
        self.current_zone = "Ashen Entrance"
        self.discovered_zones: set[str] = set()
        self.forge_journal: list[str] = []

        # Interactive discovery stations
        self.discovery_stations = [
            {"id": "dynamic_core", "name": "Dynamic Forge Core",
             "rect": pygame.Rect(500, 570, 200, 74), "color": (235, 135, 65),
             "prompt": "[E] Inspect Ancient Forge"},
        ]

        # Four-Direction Mini-Puzzle Stations (Part 2)
        # Symmetrically centered around the Central Forge (Center: 600, 430)
        self.station_broken_relic = {
            "id": "broken_relic",
            "name": "Broken Relic",
            "rect": pygame.Rect(180, 400, 60, 60),
            "color": (215, 175, 75),
            "prompt": "[E] Broken Relic",
        }
        self.station_memory_fragments = {
            "id": "memory_fragments",
            "name": "Memory Fragments",
            "rect": pygame.Rect(960, 400, 60, 60),
            "color": (100, 170, 240),
            "prompt": "[E] Memory Fragments",
        }
        self.station_ancient_blueprint = {
            "id": "ancient_blueprint",
            "name": "Ancient Blueprint",
            "rect": pygame.Rect(560, 680, 80, 50),
            "color": (225, 145, 65),
            "prompt": "[E] Ancient Blueprint",
        }
        self.station_ancient_rule = {
            "id": "ancient_rule",
            "name": "Ancient Rule",
            "rect": pygame.Rect(560, 185, 80, 44),
            "color": (230, 200, 90),
            "prompt": "[E] Ancient Rule",
        }
        self.all_puzzle_stations = [
            self.station_broken_relic,
            self.station_memory_fragments,
            self.station_ancient_blueprint,
            self.station_ancient_rule,
        ]
        for ps in self.all_puzzle_stations:
            self.all_obstacles.append(ps["rect"])

        # Interactive sub-machines (Memory Vault & Optical Gallery removed)
        self.core_stabilizer = CoreStabilizerMachine(L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT)
        self.core_stabilizer.on_success = self._on_stabilization_success
        self.journal_modal = ForgeJournalModal(L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT)

        # Dynamic Core Phasing Platforms (Oscillate via temporal cosine wave)
        self.phasing_platforms = [
            {"rect": pygame.Rect(440, 650, 80, 20), "phase_offset": 0.0, "is_solid": True},
            {"rect": pygame.Rect(680, 650, 80, 20), "phase_offset": math.pi * 0.5, "is_solid": True},
        ]

        # Ambient floating embers from the crucible
        self.embers: list[dict] = []
        for _ in range(40):
            self.embers.append({
                "x": random.uniform(520, 680),
                "y": random.uniform(370, 480),
                "vx": random.uniform(-10, 10),
                "vy": random.uniform(-35, -15),
                "size": random.uniform(1.2, 3.2),
                "alpha": random.uniform(80, 220),
                "life": random.uniform(1.0, 3.5),
            })

        # Procedural ash particles in Zone A (Ashen Entrance)
        self.ash_particles: list[dict] = []
        for _ in range(35):
            self.ash_particles.append({
                "x": random.uniform(150, 1050),
                "y": random.uniform(660, 860),
                "vx": random.uniform(-15, 15),
                "vy": random.uniform(-8, 8),
                "alpha": random.uniform(40, 120),
                "life": random.uniform(2.0, 5.0),
                "size": random.uniform(1.0, 2.5),
            })

        # Checkpoint path for state persistence
        self.checkpoint_path = Path(
            os.environ.get("LUMEN_LEVEL4_SAVE", str(Path(__file__).resolve().parents[1] / "saves/level4.json"))
        )

        # Modal inspection and Forge interface state
        self.on_lose_life = None
        self.active_modal: dict | None = None
        self.forge_engine: ForgeEngine = ForgeEngine()
        self.forge_renderer: CelestialForgeRenderer = CelestialForgeRenderer()
        self.forge_modal: ForgeModal = ForgeModal(L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT, engine=self.forge_engine)
        self.forge_modal.inventory = self.inventory
        self.particle_system: ParticleSystem = ParticleSystem()
        self.forge_modal.on_solve = self.trigger_celebration_particles
        self.forge_modal.on_lose_life = lambda cause="Exhausted Forge Attempts": (
            self.on_lose_life(cause) if callable(getattr(self, "on_lose_life", None)) else None
        )
        self.toast_msg: str = ""
        self.toast_timer: float = 0.0

        # Guardian multi-stage animation timer
        self.guardian_awakening_time: float = 0.0
        self.guardian_anim_time: float = 0.0

        # Level 4 completion & Level 5 transition hook (Milestone 4F)
        self.is_complete: bool = False
        self.trigger_level5_transition: bool = False
        self.has_received_guardian_congratulations: bool = False

        # Four Mini-Puzzle modals and Forge Entrance popup (Parts 3-6, 8)
        self.broken_relic_puzzle = BrokenRelicPuzzle(L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT)
        self.broken_relic_puzzle.on_solve = self._on_broken_relic_solved

        self.memory_fragments_puzzle = MemoryFragmentsPuzzle(L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT)
        self.memory_fragments_puzzle.on_solve = self._on_memory_fragments_solved

        self.ancient_blueprint_puzzle = AncientBlueprintPuzzle(L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT)
        self.ancient_blueprint_puzzle.on_solve = self._on_ancient_blueprint_solved

        self.ancient_rule_modal = AncientRuleModal(L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT)
        self.ancient_rule_modal.on_inspect = self._on_ancient_rule_inspected

        self.forge_entrance_modal = ForgeEntranceModal(L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT)

        # Puzzle persistence states
        self.broken_relic_solved: bool = False
        self.memory_fragments_solved: bool = False
        self.ancient_blueprint_solved: bool = False
        self.ancient_rule_discovered: bool = False
        self.forge_intro_shown: bool = False

        # Objective definition
        self.objective: str = "Examine the ancient Forge and discover how its relics fit together."

    def _on_broken_relic_solved(self):
        self.broken_relic_solved = True
        if self.inventory and hasattr(self.inventory, "add_clue"):
            self.inventory.add_clue("clue_broken_relic", "Broken Relic", BrokenRelicPuzzle.CLUE_TEXT, "RELIC")
        self._toast("Broken Relic restored! Clue discovered in Journal.")

    def _on_memory_fragments_solved(self):
        self.memory_fragments_solved = True
        if self.inventory and hasattr(self.inventory, "add_clue"):
            self.inventory.add_clue("clue_memory_fragments", "Memory Fragments", MemoryFragmentsPuzzle.CLUE_TEXT, "MEMORY")
        self._toast("Memory Fragments restored! Clue discovered in Journal.")

    def _on_ancient_blueprint_solved(self):
        self.ancient_blueprint_solved = True
        if self.inventory and hasattr(self.inventory, "add_clue"):
            self.inventory.add_clue("clue_ancient_blueprint", "Ancient Blueprint", AncientBlueprintPuzzle.CLUE_TEXT, "BLUEPRINT")
        self._toast("Ancient Blueprint repaired! Clue discovered in Journal.")

    def _on_ancient_rule_inspected(self):
        self.ancient_rule_discovered = True
        if self.inventory and hasattr(self.inventory, "add_clue"):
            self.inventory.add_clue("clue_ancient_rule", "Ancient Rule", AncientRuleModal.CLUE_TEXT, "RULE")

    def trigger_celebration_particles(self):
        """Emits celebratory particle burst upon successful Forge activation and awards Sigil."""
        self.forge_engine.is_solved = True
        self.forge_state = "Stabilized"
        self.guardian_awakening_time = 0.0

        # Bidirectionally synchronize placed relics and forge_modal selections
        if self.forge_modal.selected_key:
            self.placed_relics["keys"] = self.forge_modal.selected_key
        elif self.placed_relics["keys"]:
            self.forge_modal.selected_key = self.placed_relics["keys"]

        if self.forge_modal.selected_mirror:
            self.placed_relics["mirrors"] = self.forge_modal.selected_mirror
        elif self.placed_relics["mirrors"]:
            self.forge_modal.selected_mirror = self.placed_relics["mirrors"]

        if self.forge_modal.selected_crystal:
            self.placed_relics["crystals"] = self.forge_modal.selected_crystal
        elif self.placed_relics["crystals"]:
            self.forge_modal.selected_crystal = self.placed_relics["crystals"]

        if not self.forge_engine.successful_combination and self.placed_relics["keys"]:
            self.forge_engine.successful_combination = (
                self.placed_relics["keys"],
                self.placed_relics["mirrors"],
                self.placed_relics["crystals"],
            )

        self.particle_system.emit_celebration_burst(
            float(self.crucible_rect.centerx),
            float(self.crucible_rect.centery),
            count=75,
        )
        if self.inventory is not None:
            if hasattr(self.inventory, "add_sigil"):
                self.inventory.add_sigil()
            elif isinstance(self.inventory, dict):
                self.inventory["has_sigil"] = True
        self.objective = "The Forge is harmonized. Speak with the awakened Temple Guardian."
        self._toast("The Ancient Forge awakens! The Lumen Sigil has manifested!")

        # Close apparatus window & modals; awaken the Guardian with his message and halo!
        if self.core_stabilizer.is_open:
            self.core_stabilizer.close()
        if self.forge_modal.is_open:
            self.forge_modal.close()
        self.active_modal = {
            "title": "THE AWAKENED GUARDIAN",
            "kind": "guardian",
            "text": GUARDIAN_SUCCESS_DIALOGUE,
        }
        audio.play("clue")

    def _on_stabilization_success(self):
        """Invoked when player completes Stage 3 Core Stabilization."""
        self.forge_engine.is_solved = True
        self.forge_engine.successful_combination = (
            self.placed_relics["keys"],
            self.placed_relics["mirrors"],
            self.placed_relics["crystals"],
        )
        self.trigger_celebration_particles()

    def _build_walls(self) -> list[pygame.Rect]:
        """Constructs outer stone walls enclosing the Forge chamber."""
        return [
            # North perimeter wall
            pygame.Rect(0, 0, L4_WORLD_WIDTH, 120),
            # West perimeter wall
            pygame.Rect(0, 0, 100, L4_WORLD_HEIGHT),
            # East perimeter wall
            pygame.Rect(L4_WORLD_WIDTH - 100, 0, 100, L4_WORLD_HEIGHT),
            # South wall left flank
            pygame.Rect(0, L4_WORLD_HEIGHT - 100, 520, 100),
            # South wall right flank
            pygame.Rect(680, L4_WORLD_HEIGHT - 100, 520, 100),
            # Sealed south entrance portcullis (preventing backwards exit)
            pygame.Rect(520, L4_WORLD_HEIGHT - 80, 160, 80),
        ]

    def _build_pillars(self) -> list[pygame.Rect]:
        """Constructs 4 massive stone pillars supporting the volcanic vaulted ceiling."""
        return [
            pygame.Rect(260, 240, 70, 70),  # Northwest
            pygame.Rect(870, 240, 70, 70),  # Northeast
            pygame.Rect(260, 600, 70, 70),  # Southwest
            pygame.Rect(870, 600, 70, 70),  # Southeast
        ]

    def has_active_modal(self) -> bool:
        """Returns True if any interactive puzzle modal, journal, machine, or lore popup is open."""
        return bool(
            getattr(self, "forge_entrance_modal", None) and self.forge_entrance_modal.is_open
            or getattr(self, "broken_relic_puzzle", None) and self.broken_relic_puzzle.is_open
            or getattr(self, "memory_fragments_puzzle", None) and self.memory_fragments_puzzle.is_open
            or getattr(self, "ancient_blueprint_puzzle", None) and self.ancient_blueprint_puzzle.is_open
            or getattr(self, "ancient_rule_modal", None) and self.ancient_rule_modal.is_open
            or getattr(self, "active_modal", None)
            or (getattr(self, "forge_modal", None) and self.forge_modal.is_open)
            or (getattr(self, "core_stabilizer", None) and self.core_stabilizer.is_open)
            or (getattr(self, "journal_modal", None) and self.journal_modal.is_open)
        )

    def _draw_active_modal(self, surface: pygame.Surface):
        """Renders whatever modal or interactive machine is currently active on top of all HUD layers."""
        if getattr(self, "forge_entrance_modal", None) and self.forge_entrance_modal.is_open:
            self.forge_entrance_modal.draw(surface)
        elif getattr(self, "broken_relic_puzzle", None) and self.broken_relic_puzzle.is_open:
            self.broken_relic_puzzle.draw(surface)
        elif getattr(self, "memory_fragments_puzzle", None) and self.memory_fragments_puzzle.is_open:
            self.memory_fragments_puzzle.draw(surface)
        elif getattr(self, "ancient_blueprint_puzzle", None) and self.ancient_blueprint_puzzle.is_open:
            self.ancient_blueprint_puzzle.draw(surface)
        elif getattr(self, "ancient_rule_modal", None) and self.ancient_rule_modal.is_open:
            self.ancient_rule_modal.draw(surface)
        elif getattr(self, "active_modal", None):
            self._draw_modal(surface)
        elif getattr(self, "forge_modal", None) and self.forge_modal.is_open:
            self.forge_modal.draw(surface, self.inventory)
        elif getattr(self, "core_stabilizer", None) and self.core_stabilizer.is_open:
            self.core_stabilizer.draw(surface)
        elif getattr(self, "journal_modal", None) and self.journal_modal.is_open:
            self.journal_modal.draw(surface, self)

    def update(self, player, lantern, dt: float):
        """Updates chamber animations, player movement/collision, and atmospheric systems."""
        if self.has_active_modal():
            return  # Gameplay world paused while any modal or journal is open

        if lantern is not None and getattr(lantern, "active", False) and getattr(lantern, "radius", 0) <= 0:
            lantern.radius = getattr(lantern, "base_radius", 130)

        self.flicker_phase += dt * 4.0
        self.guardian_anim_time += dt
        self.forge_phase = (self.forge_phase + dt * 2.2) % (2 * math.pi)

        # Dynamic Core State Machine progression (unless locked or solved)
        if not (self.forge_engine.is_solved or self.forge_engine.is_locked):
            # Oscillate between Dormant, Warming, Calibrating, Resonating
            cycle = (self.forge_phase / (2 * math.pi))
            if cycle < 0.25:
                self.forge_state = "Dormant"
            elif cycle < 0.50:
                self.forge_state = "Warming"
            elif cycle < 0.75:
                self.forge_state = "Calibrating"
            else:
                self.forge_state = "Resonating"
        elif self.forge_engine.is_solved:
            self.forge_state = "Stabilized"
            self.guardian_awakening_time += dt
        elif self.forge_engine.is_locked:
            self.forge_state = "Overloaded"

        # Update phasing platforms
        for p in self.phasing_platforms:
            alpha_wave = 0.5 + 0.5 * math.cos(self.forge_phase * 1.5 + p["phase_offset"])
            p["is_solid"] = (alpha_wave > 0.45)
            # Remove or add to all_obstacles dynamically if needed
            if p["is_solid"] and p["rect"] not in self.all_obstacles:
                self.all_obstacles.append(p["rect"])
            elif not p["is_solid"] and p["rect"] in self.all_obstacles:
                self.all_obstacles.remove(p["rect"])

        # Track narrative zone
        zone = self._zone_for_position(player.center)
        if zone != self.current_zone:
            self.current_zone = zone
            desc = LEVEL4_ZONE_DESCRIPTIONS.get(zone, f"Entered {zone}.")
            self._toast(desc, 3.5)

        # Update toast timer
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast_msg = ""

        # Update crucible embers
        for p in self.embers:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            if p["life"] <= 0 or p["y"] < 250:
                p["x"] = random.uniform(520, 680)
                p["y"] = random.uniform(380, 470)
                p["vx"] = random.uniform(-12, 12)
                p["vy"] = random.uniform(-40, -18)
                p["life"] = random.uniform(1.2, 3.2)
                p["alpha"] = random.uniform(100, 240)

        # Update celestial forge internal simulation
        reduced_motion = getattr(self, "reduced_motion", False) or getattr(settings, "reduced_motion", False)
        self.forge_renderer.update(dt, self.forge_state, reduced_motion=reduced_motion)

        # Update procedural ash particles in Zone A
        for p in self.ash_particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            if p["life"] <= 0 or p["x"] < 120 or p["x"] > 1080 or p["y"] < 640 or p["y"] > 880:
                p["x"] = random.uniform(150, 1050)
                p["y"] = random.uniform(660, 860)
                p["vx"] = random.uniform(-15, 15)
                p["vy"] = random.uniform(-8, 8)
                p["life"] = random.uniform(2.0, 5.0)
                p["alpha"] = random.uniform(40, 120)

        # Update modals & machines
        if self.forge_modal.is_open:
            self.forge_modal.update(dt)
        if self.core_stabilizer.is_open:
            self.core_stabilizer.update(dt)
        if self.broken_relic_puzzle.is_open:
            self.broken_relic_puzzle.update(dt)
        if self.memory_fragments_puzzle.is_open:
            self.memory_fragments_puzzle.update(dt)
        if self.ancient_blueprint_puzzle.is_open:
            self.ancient_blueprint_puzzle.update(dt)

        # Forge Entrance First Approach Trigger (Part 8)
        pr_forge = player.rect.inflate(80, 80)
        if pr_forge.colliderect(self.altar_rect) and not self.forge_intro_shown and not self.forge_engine.is_solved:
            if not (self.active_modal or self.forge_modal.is_open or self.broken_relic_puzzle.is_open or
                    self.memory_fragments_puzzle.is_open or self.ancient_blueprint_puzzle.is_open or
                    self.ancient_rule_modal.is_open):
                self.forge_intro_shown = True
                self.forge_entrance_modal.open()

        # Update particle system
        self.particle_system.update(dt)

        # Objective state
        if self.forge_engine.is_solved:
            self.objective = "The Forge is harmonized. Speak with the awakened Temple Guardian."
        elif self.forge_engine.is_locked:
            self.objective = "The Forge is locked. Search for the descent into the Hall of Fate."
        elif self.discovered_zones:
            self.objective = "Align the sacred relics at the Crucible Altar to awaken the Forge."

        # Player movement with collision
        modal_open = (
            self.active_modal or
            self.forge_modal.is_open or
            self.core_stabilizer.is_open or
            self.journal_modal.is_open or
            self.broken_relic_puzzle.is_open or
            self.memory_fragments_puzzle.is_open or
            self.ancient_blueprint_puzzle.is_open or
            self.ancient_rule_modal.is_open or
            self.forge_entrance_modal.is_open
        )
        if not modal_open:
            dx, dy = player.get_input_vector()
            is_moving = (dx != 0.0 or dy != 0.0)
            if is_moving:
                move_with_collision(
                    player,
                    dx,
                    dy,
                    self.all_obstacles,
                    dt,
                    world_bounds=self.playable_bounds,
                )
            player.update_animation(is_moving, dt)
        else:
            player.update_animation(False, dt)

    def handle_keydown(self, key: int, inventory=None) -> bool:
        """Central keydown dispatcher for Level 4 interactive machines & modals."""
        # 1. Forge Entrance modal
        if self.forge_entrance_modal.is_open:
            return self.forge_entrance_modal.handle_keydown(key)

        # 2. Four Mini-Puzzle modals
        if self.broken_relic_puzzle.is_open:
            return self.broken_relic_puzzle.handle_keydown(key)
        if self.memory_fragments_puzzle.is_open:
            return self.memory_fragments_puzzle.handle_keydown(key)
        if self.ancient_blueprint_puzzle.is_open:
            return self.ancient_blueprint_puzzle.handle_keydown(key)
        if self.ancient_rule_modal.is_open:
            return self.ancient_rule_modal.handle_keydown(key)

        # 3. Forge Journal toggle
        if self.journal_modal.is_open:
            return self.journal_modal.handle_keydown(key)
        elif key == pygame.K_j and not (self.active_modal or self.forge_modal.is_open):
            self.journal_modal.open()
            audio.play("clue")
            return True
        elif key == pygame.K_f and not (self.active_modal or self.has_active_modal()):
            if self.placed_relics.get("keys"):
                self.forge_modal.selected_key = self.placed_relics["keys"]
            if self.placed_relics.get("mirrors"):
                self.forge_modal.selected_mirror = self.placed_relics["mirrors"]
            if self.placed_relics.get("crystals"):
                self.forge_modal.selected_crystal = self.placed_relics["crystals"]
            self.forge_modal.open(inventory or self.inventory)
            return True

        # 4. Core Stabilizer Machine
        if self.core_stabilizer.is_open:
            return self.core_stabilizer.handle_keydown(key)

        return False

    def handle_click(self, mx: int, my: int, inventory=None) -> bool:
        """Central mouse click dispatcher for Level 4 interactive machines & modals."""
        if self.forge_entrance_modal.is_open:
            return self.forge_entrance_modal.handle_click(mx, my)
        if self.broken_relic_puzzle.is_open:
            return self.broken_relic_puzzle.handle_click(mx, my)
        if self.memory_fragments_puzzle.is_open:
            return self.memory_fragments_puzzle.handle_click(mx, my)
        if self.ancient_blueprint_puzzle.is_open:
            return self.ancient_blueprint_puzzle.handle_click(mx, my)
        if self.ancient_rule_modal.is_open:
            return self.ancient_rule_modal.handle_click(mx, my)
        if self.journal_modal.is_open:
            return self.journal_modal.handle_click(mx, my)
        return False

    def handle_mouse_up(self, mx: int, my: int) -> bool:
        """Handles mouse release events for interactive drag-and-drop puzzles."""
        if self.broken_relic_puzzle.is_open:
            return self.broken_relic_puzzle.handle_mouse_up(mx, my)
        if self.ancient_blueprint_puzzle.is_open:
            return self.ancient_blueprint_puzzle.handle_mouse_up(mx, my)
        return False

    def handle_mouse_motion(self, mx: int, my: int):
        """Handles mouse motion events for interactive dragging."""
        if self.broken_relic_puzzle.is_open:
            self.broken_relic_puzzle.handle_mouse_motion(mx, my)
        elif self.ancient_blueprint_puzzle.is_open:
            self.ancient_blueprint_puzzle.handle_mouse_motion(mx, my)

    @property
    def current_interaction_target(self):
        """Returns the currently active interaction target dict."""
        return self.selected_interaction_target

    def get_interaction_target(self, player) -> dict | None:
        """Alias for get_active_interaction_target."""
        return self.get_active_interaction_target(player)

    def get_active_interaction_target(self, player) -> dict | None:
        """Resolves the single closest valid interactive target for the player."""
        if (self.active_modal or self.forge_modal.is_open or
            self.core_stabilizer.is_open or self.journal_modal.is_open or
            self.broken_relic_puzzle.is_open or self.memory_fragments_puzzle.is_open or
            self.ancient_blueprint_puzzle.is_open or self.ancient_rule_modal.is_open or
            self.forge_entrance_modal.is_open):
            self.selected_interaction_target = None
            return None

        p_cx = getattr(player.rect, "centerx", getattr(player, "x", 0))
        p_cy = getattr(player.rect, "centery", getattr(player, "y", 0))
        pr = player.rect.inflate(40, 40)
        candidates = []

        # 0. Northern Threshold / Hall of Fate Descent
        gate_trig = self.sealed_gate_rect.inflate(40, 40)
        if pr.colliderect(gate_trig):
            dx = max(self.sealed_gate_rect.left - p_cx, 0, p_cx - self.sealed_gate_rect.right)
            dy = max(self.sealed_gate_rect.top - p_cy, 0, p_cy - self.sealed_gate_rect.bottom)
            d = math.hypot(dx, dy)
            if self.forge_engine.is_solved or self.forge_engine.is_locked:
                prompt = "[E] Descend into the Hall of Fate"
            else:
                prompt = "[E] Examine Sealed Forge Mechanism"
            candidates.append({
                "type": "exit_gate",
                "id": "sealed_gate",
                "name": "Northern Threshold",
                "prompt": prompt,
                "rect": self.sealed_gate_rect,
                "dist": d,
            })

        # 1. Activated Lumen Sigil (When Forge is solved, radiant sigil manifests at Central Forge)
        if self.forge_engine.is_solved:
            sigil_trig = self.altar_rect.inflate(100, 100)
            if pr.colliderect(sigil_trig):
                d = math.hypot(p_cx - self.sigil_rect.centerx, p_cy - self.sigil_rect.centery)
                candidates.append({
                    "type": "sigil",
                    "id": "lumen_sigil",
                    "name": "Lumen Sigil",
                    "prompt": "[E] Inspect Lumen",
                    "rect": self.sigil_rect,
                    "dist": d,
                })

        # 2. Temple Guardian (Northeast alcove dais)
        guard_trig = self.guardian_rect.inflate(40, 40)
        if pr.colliderect(guard_trig):
            dx = max(self.guardian_rect.left - p_cx, 0, p_cx - self.guardian_rect.right)
            dy = max(self.guardian_rect.top - p_cy, 0, p_cy - self.guardian_rect.bottom)
            d = math.hypot(dx, dy)
            if self.forge_engine.is_solved:
                prompt = "[E] Speak to Temple Guardian"
            elif self.forge_engine.is_locked:
                prompt = "[E] Inspect Dormant Guardian"
            else:
                prompt = "[E] Inspect Slumbering Sentinel"
            candidates.append({
                "type": "guardian",
                "id": "guardian",
                "name": "Temple Guardian",
                "prompt": prompt,
                "rect": self.guardian_rect,
                "dist": d,
            })

        # 3. Central Forge Altar (when NOT solved)
        if not self.forge_engine.is_solved:
            altar_trig = self.altar_rect.inflate(60, 60)
            if pr.colliderect(altar_trig):
                d = math.hypot(p_cx - self.altar_rect.centerx, p_cy - self.altar_rect.centery)
                k = self.placed_relics.get("keys")
                m = self.placed_relics.get("mirrors")
                c = self.placed_relics.get("crystals")
                placed_count = sum(1 for v in (k, m, c) if v is not None)
                if placed_count == 3:
                    prompt = "[E] Harmonize Forge Core"
                else:
                    prompt = "[E] Examine Ancient Forge Altar"
                candidates.append({
                    "type": "altar",
                    "id": "forge_altar",
                    "name": "Ancient Forge Altar",
                    "prompt": prompt,
                    "rect": self.altar_rect,
                    "dist": d,
                })

        # 4. Relic Sockets
        for ks in self.key_sockets:
            if pr.colliderect(ks["rect"]):
                d = math.hypot(p_cx - ks["rect"].centerx, p_cy - ks["rect"].centery)
                relic_id = ks["relic_id"]
                has_item = self._has_inventory_item("keys", relic_id)
                placed = self.placed_relics.get("keys")
                if placed == relic_id:
                    prompt = f"[E] Remove {ks['name'].split()[0]} Key"
                elif has_item:
                    prompt = f"[E] Place {ks['name'].split()[0]} Key"
                else:
                    prompt = f"[E] Inspect {ks['name']}"
                candidates.append({
                    "type": "socket_key",
                    "id": ks["id"],
                    "relic_id": relic_id,
                    "name": ks["name"],
                    "prompt": prompt,
                    "rect": ks["rect"],
                    "dist": d,
                })

        for ms in self.mirror_sockets:
            if pr.colliderect(ms["rect"]):
                d = math.hypot(p_cx - ms["rect"].centerx, p_cy - ms["rect"].centery)
                relic_id = ms["relic_id"]
                has_item = self._has_inventory_item("mirrors", relic_id)
                placed = self.placed_relics.get("mirrors")
                if placed == relic_id:
                    prompt = f"[E] Remove {ms['name'].split()[0]} Mirror"
                elif has_item:
                    prompt = f"[E] Install {ms['name'].split()[0]} Mirror"
                else:
                    prompt = f"[E] Inspect {ms['name']}"
                candidates.append({
                    "type": "socket_mirror",
                    "id": ms["id"],
                    "relic_id": relic_id,
                    "name": ms["name"],
                    "prompt": prompt,
                    "rect": ms["rect"],
                    "dist": d,
                })

        for cs in self.crystal_sockets:
            if pr.colliderect(cs["rect"]):
                d = math.hypot(p_cx - cs["rect"].centerx, p_cy - cs["rect"].centery)
                relic_id = cs["relic_id"]
                has_item = self._has_inventory_item("crystals", relic_id)
                placed = self.placed_relics.get("crystals")
                if placed == relic_id:
                    prompt = f"[E] Remove {cs['name']}"
                elif has_item:
                    prompt = f"[E] Insert {cs['name']}"
                else:
                    prompt = f"[E] Inspect {cs['name']}"
                candidates.append({
                    "type": "socket_crystal",
                    "id": cs["id"],
                    "relic_id": relic_id,
                    "name": cs["name"],
                    "prompt": prompt,
                    "rect": cs["rect"],
                    "dist": d,
                })

        # 5. Four-direction mini-puzzle stations
        for st_key in ("station_broken_relic", "station_memory_fragments", "station_ancient_blueprint", "station_ancient_rule"):
            st = getattr(self, st_key)
            if pr.colliderect(st["rect"]):
                d = math.hypot(p_cx - st["rect"].centerx, p_cy - st["rect"].centery)
                candidates.append({
                    "type": "mini_puzzle",
                    "id": st["id"],
                    "name": st["name"],
                    "prompt": st["prompt"],
                    "rect": st["rect"],
                    "dist": d,
                })

        # 6. Discovery stations
        for station in self.discovery_stations:
            if pr.colliderect(station["rect"]):
                # When Forge is solved, Sigil at Altar takes priority near the Forge
                if self.forge_engine.is_solved and pr.colliderect(self.altar_rect.inflate(100, 100)):
                    continue
                d = math.hypot(p_cx - station["rect"].centerx, p_cy - station["rect"].centery)
                candidates.append({
                    "type": "discovery",
                    "id": station["id"],
                    "name": station["name"],
                    "prompt": station["prompt"],
                    "rect": station["rect"],
                    "dist": d,
                })

        # 7. South entrance archway
        if pr.colliderect(self.entrance_rect.inflate(40, 40)):
            d = math.hypot(p_cx - self.entrance_rect.centerx, p_cy - self.entrance_rect.centery)
            candidates.append({
                "type": "entrance",
                "id": "entrance",
                "name": "South Entrance",
                "prompt": "[E] Inspect Sealed Sanctum Threshold",
                "rect": self.entrance_rect,
                "dist": d,
            })

        if not candidates:
            self.selected_interaction_target = None
            return None

        # Prioritize territorial intent: if player is within the Northern gate bay (p_cx <= 725),
        # gate takes precedence over guardian. If player is near the Guardian dais (p_cx > 725),
        # guardian takes precedence over gate.
        if any(c["type"] == "exit_gate" for c in candidates) and any(c["type"] == "guardian" for c in candidates):
            if p_cx <= 725:
                candidates = [c for c in candidates if c["type"] != "guardian"]
            else:
                candidates = [c for c in candidates if c["type"] != "exit_gate"]

        candidates.sort(key=lambda c: c["dist"])
        best = candidates[0]
        self.selected_interaction_target = best
        return best

    def get_contextual_prompt(self, player) -> str:
        """Returns simplified non-overlapping context prompt depending on player proximity."""
        target = self.get_active_interaction_target(player)
        self.selected_interaction_target = target
        return target["prompt"] if target else ""

    def _has_inventory_item(self, category: str, item_id: str) -> bool:
        """Resilient inventory item presence checker."""
        if not self.inventory:
            return False
        from systems.forge_ui import check_item_possession
        if check_item_possession(self.inventory, item_id):
            return True
        if hasattr(self.inventory, "has_item"):
            return self.inventory.has_item(item_id)
        if isinstance(self.inventory, dict):
            items = self.inventory.get(category, [])
            return item_id in items
        items = getattr(self.inventory, category, [])
        return item_id in items

    def handle_interact(self, player) -> bool:
        """Handles player interaction [E] near environmental objects & machines."""
        # Use the SAME resolved interaction target as displayed in the contextual prompt
        target = self.get_active_interaction_target(player)
        self.selected_interaction_target = target
        if not target:
            return False

        t_type = target.get("type")
        t_id = target.get("id")

        # 1. Lumen Sigil inspection (Final Hint)
        if t_type == "sigil" or t_id == "lumen_sigil":
            self.active_modal = {
                "title": "THE LUMEN SIGIL — FINAL HINT",
                "kind": "sigil_hint",
                "text": (
                    "The Lumen Sigil hovers within the crucible, burning with calm, undivided brilliance.\n\n"
                    "As you approach, the light resonates with your carried relics and casts an ethereal inscription across the obsidian dais:\n\n"
                    "\"Truth dwells not at the reckless left boundary of shadow, nor at the deceptive right margin of false dawn. Where diverging rays converge in equilibrium, there the archway of wholeness shall yield.\"\n\n"
                    "The Sigil pulses in harmony with your lantern, assuring you that the path of convergence will reveal the true way in the hall below."
                ),
            }
            audio.play("clue")
            return True

        # 2. Temple Guardian
        if t_type == "guardian" or t_id == "guardian":
            if self.forge_engine.is_solved:
                if not self.has_received_guardian_congratulations:
                    self.has_received_guardian_congratulations = True
                    dialogue_text = GUARDIAN_SUCCESS_DIALOGUE
                else:
                    dialogue_text = GUARDIAN_REPEATABLE_LORE

                self.active_modal = {
                    "title": "THE AWAKENED GUARDIAN",
                    "kind": "guardian",
                    "text": dialogue_text,
                }
                audio.play("clue")
                return True
            elif self.forge_engine.is_locked:
                self.active_modal = {
                    "title": "DORMANT STONE SENTINEL",
                    "kind": "guardian",
                    "text": GUARDIAN_LOCKED_DIALOGUE,
                }
                audio.play("door_locked")
                return True
            else:
                self._toast("The Guardian rests in deep shadow. Only the harmony of the Ancient Forge can awaken him.", 3.5)
                audio.play("door_locked")
                return True

        # 3. Northern Threshold / Hall of Fate Descent
        if t_type == "exit_gate":
            if self.forge_engine.is_solved:
                self.trigger_level5_transition = True
                self.is_complete = True
                self.active_modal = {
                    "title": "THE DESCENT UNSEALED",
                    "kind": "exit_success",
                    "text": (
                        "The colossal obsidian gate has unsealed, its heavy hydraulic pistons retracted into the bedrock.\n\n"
                        "A spiraling stone stairway descends into the subterranean abyss toward the Hall of Fate.\n\n"
                        "The Lumen Sigil in your possession pulses with serene celestial energy, ready to reveal the hidden mark when you reach the arches below."
                    ),
                }
                audio.play("door_open")
                return True
            elif self.forge_engine.is_locked:
                self.trigger_level5_transition = True
                self.is_complete = True
                self.active_modal = {
                    "title": "THE EMERGENCY PASSAGE",
                    "kind": "exit_failure",
                    "text": (
                        "With the Forge locked in dissonance, the emergency seismic release has forced open the heavy iron bars.\n\n"
                        "The spiraling stone stairway descends into the subterranean abyss toward the Hall of Fate.\n\n"
                        "You proceed forward into the final trials without the guidance or blessing of the Lumen Sigil."
                    ),
                }
                audio.play("door_open")
                return True
            else:
                self.active_modal = {
                    "title": "THE SEALED FORGE MECHANISM",
                    "kind": "mechanism",
                    "text": (
                        "A massive subterranean portal barred by interlocking obsidian pistons and heavy iron bands.\n\n"
                        "Dormant magma conduits trace lines across the threshold toward the central forge.\n\n"
                        "The mechanism is firmly locked. The path beyond will remain sealed until the ancient Forge is activated or its trial concludes."
                    ),
                }
                audio.play("door_locked")
                return True

        # 4. Central Forge Altar (when NOT solved)
        if t_type == "altar":
            if self.forge_engine.is_locked:
                self._toast("The Forge is locked in overload. Proceed to the descent gate.")
                audio.play("door_locked")
                return True

            k = self.placed_relics.get("keys")
            m = self.placed_relics.get("mirrors")
            c = self.placed_relics.get("crystals")

            if k and m and c:
                combo = (k, m, c)
                if combo in VALID_COMBINATIONS:
                    self.forge_engine.submit(k, m, c)
                    self.trigger_celebration_particles()
                    audio.play("door_open")
                    return True
                else:
                    success, status = self.forge_engine.submit(k, m, c)
                    attempts_left = self.forge_engine.attempts_left
                    if status == "locked" or attempts_left <= 0:
                        self.forge_state = "Overloaded"
                        if callable(getattr(self, "on_lose_life", None)):
                            self.on_lose_life("Exhausted Forge Attempts")
                        self.forge_engine.attempts_used = 0
                        self.forge_engine.is_locked = False
                        self._toast("Attempts exhausted. You lost one life.", 4.0)
                        audio.play("door_locked")
                    else:
                        self._toast(f"Incorrect combination. {attempts_left} attempts remaining.", 3.5)
                        audio.play("door_locked")
                    return True
            else:
                placed_count = sum(1 for v in (k, m, c) if v is not None)
                missing = []
                if not k:
                    missing.append("Key")
                if not m:
                    missing.append("Mirror")
                if not c:
                    missing.append("Crystal")
                missing_str = " & ".join(missing) if missing else "offerings"
                self._toast(f"The Forge awaits all 3 sacred conduits! ({placed_count}/3 active — Awaiting {missing_str})")
                audio.play("door_locked")
                return True

        # 5. Relic Sockets
        if t_type == "socket_key":
            relic_id = target["relic_id"]
            if self.placed_relics["keys"] == relic_id:
                self.placed_relics["keys"] = None
                self._toast(f"Removed {target['name'].split()[0]} Key from socket.")
                audio.play("pickup")
                return True
            elif self._has_inventory_item("keys", relic_id):
                self.placed_relics["keys"] = relic_id
                self._toast(f"Inserted {target['name'].split()[0]} Key into {target['name']}!")
                audio.play("clue")
                return True
            else:
                self.active_modal = {
                    "title": target["name"].upper(),
                    "kind": "socket_key",
                    "text": (
                        f"An ornate stone pedestal etched with deep runic grooves and a {target['name'].split()[0]} keyway.\n\n"
                        "It is designed to receive one of the progression keys recovered from the upper temple chambers.\n\n"
                        "The keyway's internal tumblers remain locked in place."
                    ),
                }
                audio.play("clue")
                return True

        if t_type == "socket_mirror":
            relic_id = target["relic_id"]
            if self.placed_relics["mirrors"] == relic_id:
                self.placed_relics["mirrors"] = None
                self._toast(f"Removed {target['name'].split()[0]} Mirror from stand.")
                audio.play("pickup")
                return True
            elif self._has_inventory_item("mirrors", relic_id):
                self.placed_relics["mirrors"] = relic_id
                self._toast(f"Installed {target['name'].split()[0]} Mirror on reflector stand!")
                audio.play("clue")
                return True
            else:
                self.active_modal = {
                    "title": target["name"].upper(),
                    "kind": "socket_mirror",
                    "text": (
                        f"A rotatable stone pedestal fitted with ancient brass alignment clamps.\n\n"
                        f"Engravings around the rim indicate this stand is attuned to receive a reflector mirror.\n\n"
                        "Without a mirror installed, light cannot be focused into the crucible."
                    ),
                }
                audio.play("clue")
                return True

        if t_type == "socket_crystal":
            relic_id = target["relic_id"]
            if self.placed_relics["crystals"] == relic_id:
                self.placed_relics["crystals"] = None
                self._toast("Removed Crystal from receptacle.")
                audio.play("pickup")
                return True
            elif self._has_inventory_item("crystals", relic_id):
                self.placed_relics["crystals"] = relic_id
                self._toast("Placed Crystal into receptacle!")
                audio.play("clue")
                return True
            else:
                self.active_modal = {
                    "title": target["name"].upper(),
                    "kind": "socket_crystal",
                    "text": (
                        f"A slender stone spire crowned with a faceted concave indentation.\n\n"
                        "Faint harmonic vibrations pulse through the volcanic rock.\n\n"
                        "It awaits one of the sacred resonance crystals to harmonize the forge apparatus."
                    ),
                }
                audio.play("clue")
                return True

        # 6. Mini puzzle stations
        if t_type == "mini_puzzle":
            p_id = target["id"]
            if p_id == "broken_relic":
                self.broken_relic_puzzle.open()
                audio.play("clue")
                return True
            if p_id == "memory_fragments":
                self.memory_fragments_puzzle.open()
                audio.play("clue")
                return True
            if p_id == "ancient_blueprint":
                self.ancient_blueprint_puzzle.open()
                audio.play("clue")
                return True
            if p_id == "ancient_rule":
                self.ancient_rule_discovered = True
                self.ancient_rule_modal.open()
                audio.play("clue")
                return True

        # 7. Discovery stations
        if t_type == "discovery":
            station_id = target["id"]
            if station_id not in self.discovered_zones:
                self.discovered_zones.add(station_id)
                self.forge_journal.append(station_id)
            if station_id == "dynamic_core":
                self.active_modal = {
                    "title": target["name"].upper(),
                    "kind": "discovery",
                    "text": LEVEL4_DISCOVERY_TEXT[station_id],
                }
                audio.play("clue")
                return True

        # 8. South entrance archway
        if t_type == "entrance":
            self.active_modal = {
                "title": "THE SANCTUM THRESHOLD",
                "kind": "entrance",
                "text": (
                    "The passage back to the Path of Light has sealed shut behind you with ancient finality.\n\n"
                    "The only way forward is through the trials of the Ancient Forge."
                ),
            }
            audio.play("door_locked")
            return True

        return False

    def dismiss_modal(self):
        """Dismisses any active inspection modal, machine, or Forge interface."""
        self.active_modal = None
        self.selected_interaction_target = None
        if self.forge_modal.is_open:
            self.forge_modal.close()
        if self.core_stabilizer.is_open:
            self.core_stabilizer.close()
        if self.journal_modal.is_open:
            self.journal_modal.close()
        if self.broken_relic_puzzle.is_open:
            self.broken_relic_puzzle.close()
        if self.memory_fragments_puzzle.is_open:
            self.memory_fragments_puzzle.close()
        if self.ancient_blueprint_puzzle.is_open:
            self.ancient_blueprint_puzzle.close()
        if self.ancient_rule_modal.is_open:
            self.ancient_rule_modal.close()
        if self.forge_entrance_modal.is_open:
            self.forge_entrance_modal.close()
        audio.play("clue")

    def _toast(self, msg: str, duration: float = 3.0):
        """Displays a temporary notification banner."""
        self.toast_msg = msg
        self.toast_timer = duration

    def save_checkpoint(self, player=None, lantern=None) -> bool:
        """Serializes and persists Level 4 chamber and Forge state to disk."""
        data = {
            "version": 1,
            "forge": self.forge_engine.to_dict(),
            "forge_state": self.forge_state,
            "discovered_zones": sorted(self.discovered_zones),
            "forge_journal": list(self.forge_journal),
            "placed_relics": self.placed_relics,
            "has_sigil": getattr(self.inventory, "has_sigil", False) if self.inventory else False,
            "is_complete": self.is_complete,
            "has_received_guardian_congratulations": self.has_received_guardian_congratulations,
            "position": [player.x, player.y] if player else [L4_SPAWN_X, L4_SPAWN_Y],
            "puzzles": {
                "broken_relic_solved": self.broken_relic_solved,
                "memory_fragments_solved": self.memory_fragments_solved,
                "ancient_blueprint_solved": self.ancient_blueprint_solved,
                "ancient_rule_discovered": self.ancient_rule_discovered,
                "forge_intro_shown": self.forge_intro_shown,
            },
        }
        try:
            self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.checkpoint_path.with_suffix(".tmp")
            with temp.open("w", encoding="utf-8") as f:
                json.dump(data, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, self.checkpoint_path)
            self._toast("Checkpoint saved.")
            return True
        except OSError:
            self._toast("Checkpoint could not be saved.")
            return False

    def load_checkpoint(self, player=None, lantern=None) -> bool:
        """Restores Level 4 chamber and Forge state from persisted checkpoint."""
        try:
            if not self.checkpoint_path.exists():
                self._toast("No Level 4 checkpoint found.")
                return False
            data = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            if data.get("version") != 1:
                self._toast("Incompatible Level 4 checkpoint.")
                return False
            forge_data = data.get("forge", {})
            self.forge_engine.load_dict(forge_data)
            self.forge_state = str(data.get("forge_state", "Dormant"))
            self.discovered_zones = set(data.get("discovered_zones", []))
            self.forge_journal = list(data.get("forge_journal", self.discovered_zones))
            self.placed_relics = data.get("placed_relics", {"keys": None, "mirrors": None, "crystals": None})
            has_sigil = data.get("has_sigil", False)
            if self.inventory and hasattr(self.inventory, "has_sigil"):
                self.inventory.has_sigil = bool(has_sigil)
            elif isinstance(self.inventory, dict):
                self.inventory["has_sigil"] = bool(has_sigil)
            self.is_complete = bool(data.get("is_complete", False))
            self.has_received_guardian_congratulations = bool(data.get("has_received_guardian_congratulations", self.forge_engine.is_solved))
            if self.forge_engine.is_solved:
                self.objective = "The Forge is harmonized. Speak with the awakened Temple Guardian."
            elif self.forge_engine.is_locked:
                self.objective = "The Forge is locked. Search for the descent into the Hall of Fate."
            pos = data.get("position")
            if player and pos and len(pos) == 2:
                player.x, player.y = float(pos[0]), float(pos[1])

            puzzles = data.get("puzzles", {})
            self.broken_relic_solved = bool(puzzles.get("broken_relic_solved", False))
            self.memory_fragments_solved = bool(puzzles.get("memory_fragments_solved", False))
            self.ancient_blueprint_solved = bool(puzzles.get("ancient_blueprint_solved", False))
            self.ancient_rule_discovered = bool(puzzles.get("ancient_rule_discovered", False))
            self.forge_intro_shown = bool(puzzles.get("forge_intro_shown", False))
            self.broken_relic_puzzle.is_solved = self.broken_relic_solved
            self.memory_fragments_puzzle.is_solved = self.memory_fragments_solved
            self.ancient_blueprint_puzzle.is_solved = self.ancient_blueprint_solved

            self._toast("Level 4 checkpoint restored.")
            return True
        except Exception:
            self._toast("Error loading Level 4 checkpoint.")
            return False

    def _zone_for_position(self, pos: tuple[float, float]) -> str:
        """Maps world position to a readable narrative zone."""
        x, y = pos
        if y >= 650:
            return "Ashen Entrance"
        if y > 520:
            return "Dynamic Forge Core"
        return "Resonance Foundry"

    def draw(self, surface: pygame.Surface, player, lantern, camera_offset: tuple[int, int] = (0, 0)):
        """Renders the Forge chamber environment, multi-zone stations, and visual effects."""
        ox, oy = camera_offset or (0, 0)
        vp = pygame.Rect(ox, oy, L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT)

        # 1. Base volcanic flagstone floor
        surface.fill((16, 12, 18))
        self._draw_floor(surface, ox, oy, vp)

        # 2. Connected narrative zones and visual evidence stations
        self._draw_discovery_zones(surface, ox, oy, vp)
        self._draw_puzzle_stations(surface, ox, oy, vp)

        # 3. Phasing platforms (Zone E: Dynamic Core)
        self._draw_phasing_platforms(surface, ox, oy)

        # 4. Runic conduits leading from sockets to crucible
        self._draw_conduits(surface, ox, oy)

        # 5. Outer walls & grand stone pillars
        self._draw_architecture(surface, ox, oy, vp)

        # 6. Northern Threshold & South entrance
        self._draw_gates(surface, ox, oy)

        # 7. Central Forge Altar & Crucible
        self._draw_altar(surface, ox, oy)

        # 8. Sockets & Physical relic representations
        self._draw_sockets(surface, ox, oy)

        # 9. Ancient Guardian Sentinel
        self._draw_guardian(surface, ox, oy)

        # 10. Rising ash & volcanic ember particles
        self._draw_particles(surface, ox, oy)
        self.particle_system.draw(surface, camera_offset)

        # 11. Player explorer
        player.draw(surface, camera_offset, is_lantern_lit=getattr(lantern, "active", False))

        # 12. Dynamic darkness & lighting mask
        self._draw_lighting(surface, player, lantern, ox, oy)

        # 13. Active Inspection Modals & Interactive Machines
        self._draw_active_modal(surface)

    def _draw_floor(self, surface: pygame.Surface, ox: int, oy: int, vp: pygame.Rect):
        """Draws ancient weathered flagstones, sacred astrological mandala, and navigation inlays."""
        tile_w = 60
        tile_h = 60
        start_x = (vp.left // tile_w) * tile_w
        start_y = (vp.top // tile_h) * tile_h
        end_x = vp.right + tile_w
        end_y = vp.bottom + tile_h

        # 1. Base flagstones with wear seams
        for y in range(start_y, end_y, tile_h):
            for x in range(start_x, end_x, tile_w):
                if 100 <= x < L4_WORLD_WIDTH - 100 and 120 <= y < L4_WORLD_HEIGHT - 100:
                    rx = x - ox
                    ry = y - oy
                    is_alt = ((x // tile_w) + (y // tile_h)) % 2 == 0
                    base_val = 23 if is_alt else 18
                    tile_col = (base_val + 2, base_val - 2, base_val + 4)
                    pygame.draw.rect(surface, tile_col, (rx, ry, tile_w, tile_h))
                    pygame.draw.rect(surface, (12, 9, 14), (rx, ry, tile_w, tile_h), 1)

                    # Subtle stone fracture lines on select tiles
                    seed = (x * 17 + y * 31) % 19
                    if seed == 0:
                        pygame.draw.line(surface, (15, 12, 18), (rx + 8, ry + 12), (rx + 24, ry + 36), 1)
                        pygame.draw.line(surface, (15, 12, 18), (rx + 24, ry + 36), (rx + 48, ry + 42), 1)
                    elif seed == 3:
                        pygame.draw.line(surface, (14, 11, 16), (rx + 42, ry + 6), (rx + 20, ry + 32), 1)

        # 2. Inlaid Temple Navigation Runes (Guiding pathways radiating from the south entrance)
        altar_cx = self.altar_rect.centerx - ox
        altar_cy = self.altar_rect.centery - oy
        ent_cx = self.entrance_rect.centerx - ox
        ent_top = self.entrance_rect.top - oy

        brass_muted = (75, 60, 40)
        brass_node = (125, 95, 50)

        # Path northward toward the Forge Core
        pygame.draw.line(surface, brass_muted, (ent_cx, ent_top), (altar_cx, altar_cy + 170), 2)
        # Fork toward West Wing (Keys & Memory Vault)
        pygame.draw.line(surface, brass_muted, (ent_cx, ent_top - 60), (ent_cx - 180, ent_top - 160), 2)
        pygame.draw.line(surface, brass_muted, (ent_cx - 180, ent_top - 160), (370 - ox + 22, 540 - oy + 22), 2)
        # Fork toward East Wing (Crystals & Optical Gallery)
        pygame.draw.line(surface, brass_muted, (ent_cx, ent_top - 60), (ent_cx + 180, ent_top - 160), 2)
        pygame.draw.line(surface, brass_muted, (ent_cx + 180, ent_top - 160), (786 - ox + 22, 540 - oy + 22), 2)

        # Inlaid intersection nodes
        for nx, ny in [(ent_cx, ent_top - 60), (ent_cx - 180, ent_top - 160), (ent_cx + 180, ent_top - 160)]:
            pygame.draw.circle(surface, (16, 12, 20), (nx, ny), 6)
            pygame.draw.circle(surface, brass_node, (nx, ny), 5, width=1)
            pygame.draw.circle(surface, (190, 150, 75), (nx, ny), 2)

        # 3. Sacred Geometry Astrological Mandala around the Central Forge Altar
        pulse = 0.5 + 0.5 * math.sin(self.forge_phase * 1.5)
        mandala_gold = (int(105 + 30 * pulse), int(80 + 25 * pulse), 45)

        # Outer Astrological Circle (Radius 180)
        pygame.draw.circle(surface, brass_muted, (altar_cx, altar_cy), 180, width=1)
        # 12 Astrological tick marks around the outer perimeter
        for i in range(12):
            ang = i * (math.pi / 6.0)
            tx1 = altar_cx + int(174 * math.cos(ang))
            ty1 = altar_cy + int(174 * math.sin(ang))
            tx2 = altar_cx + int(186 * math.cos(ang))
            ty2 = altar_cy + int(186 * math.sin(ang))
            pygame.draw.line(surface, brass_muted, (tx1, ty1), (tx2, ty2), 1)

        # Middle Sacred Octagram Star (Radius 140)
        star_pts = []
        for i in range(8):
            ang = i * (math.pi / 4.0) + (0.0 if not pulse else self.forge_phase * 0.05)
            r_val = 140 if i % 2 == 0 else 110
            sx = altar_cx + int(r_val * math.cos(ang))
            sy = altar_cy + int(r_val * math.sin(ang))
            star_pts.append((sx, sy))
        if len(star_pts) >= 8:
            pygame.draw.polygon(surface, (brass_muted[0] // 2, brass_muted[1] // 2, brass_muted[2] // 2), star_pts, width=1)

        # Inner Celestial Runic Ring (Radius 105)
        pygame.draw.circle(surface, mandala_gold, (altar_cx, altar_cy), 105, width=1)
        # Cardinal direction glyph pips
        for cang in (0.0, math.pi * 0.5, math.pi, math.pi * 1.5):
            cpx = altar_cx + int(105 * math.cos(cang))
            cpy = altar_cy + int(105 * math.sin(cang))
            pygame.draw.circle(surface, mandala_gold, (cpx, cpy), 3)
            pygame.draw.circle(surface, (255, 230, 140), (cpx, cpy), 1)

    def _draw_discovery_zones(self, surface: pygame.Surface, ox: int, oy: int, vp: pygame.Rect):
        """Draws bounded zone accents and visual evidence stations."""
        # Physical in-world machine consoles
        for station in self.discovery_stations:
            rect = station["rect"]
            if not vp.colliderect(rect):
                continue
            sr = rect.move(-ox, -oy)
            sid = station["id"]
            col = station["color"]

            # 1. Heavy stone console plinth base
            pygame.draw.rect(surface, (18, 14, 24), sr, border_radius=6)
            pygame.draw.rect(surface, (48, 38, 56), sr, width=2, border_radius=6)
            pygame.draw.rect(surface, (120, 95, 50), (sr.x + 2, sr.y + 2, sr.width - 4, 6), border_radius=2)

            if sid == "dynamic_core":
                # Core state monitor with pulsating energy waveform
                mon_r = pygame.Rect(sr.x + 14, sr.y + 12, sr.width - 28, 32)
                pygame.draw.rect(surface, (18, 12, 10), mon_r, border_radius=3)
                pygame.draw.rect(surface, (160, 85, 40), mon_r, width=1, border_radius=3)

                # Waveform line
                prev_pt = None
                for wx in range(mon_r.left + 4, mon_r.right - 4, 6):
                    norm = (wx - mon_r.left) / max(1, mon_r.width)
                    wy = int(mon_r.centery + 7 * math.sin(norm * math.pi * 3.0 + self.forge_phase * 2.0))
                    if prev_pt:
                        pygame.draw.line(surface, (255, 145, 60), prev_pt, (wx, wy), 1)
                    prev_pt = (wx, wy)

                # Status LED pips
                for i, led_col in enumerate([(70, 210, 120), (240, 180, 50), (220, 60, 50)]):
                    pygame.draw.circle(surface, led_col, (sr.left + 22 + i * 14, sr.bottom - 14), 2)

    def _draw_puzzle_stations(self, surface: pygame.Surface, ox: int, oy: int, vp: pygame.Rect):
        """Draws the four directional mini-puzzle stations around the central Forge (Parts 2-6, 10)."""
        f_lbl = pygame.font.SysFont("consolas", 10, bold=True)

        # -------------------------------------------------------------
        # Left Station: Broken Relic (Ear-Clipping Triangulation)
        # -------------------------------------------------------------
        relic_r = self.station_broken_relic["rect"]
        if vp.colliderect(relic_r):
            rx = relic_r.x - ox
            ry = relic_r.y - oy
            rw, rh = relic_r.width, relic_r.height
            rcx, rcy = rx + rw // 2, ry + rh // 2

            # Stone Plinth Base
            pygame.draw.rect(surface, (22, 18, 28), (rx, ry, rw, rh), border_radius=6)
            pygame.draw.rect(surface, (140, 105, 50), (rx, ry, rw, rh), width=2, border_radius=6)
            pygame.draw.rect(surface, (45, 36, 54), (rx + 4, ry + 4, rw - 8, rh - 8), border_radius=4)

            if self.broken_relic_solved:
                # Pulsing golden harmonic glow
                glow_s = pygame.Surface((rw + 24, rh + 24), pygame.SRCALPHA)
                pygame.draw.circle(glow_s, (240, 195, 60, 45), (rw // 2 + 12, rh // 2 + 12), rw // 2 + 8)
                surface.blit(glow_s, (rx - 12, ry - 12))

                # Restored geometric golden relic with triangulated facets
                rel_pts = [
                    (rcx, rcy - 16),
                    (rcx + 15, rcy - 5),
                    (rcx + 11, rcy + 14),
                    (rcx - 11, rcy + 14),
                    (rcx - 15, rcy - 5),
                ]
                pygame.draw.polygon(surface, (230, 185, 65), rel_pts)
                pygame.draw.polygon(surface, (255, 240, 150), rel_pts, width=2)
                # Ear-clipping triangulation inner chord lines
                pygame.draw.line(surface, (255, 240, 150), (rcx, rcy - 16), (rcx + 11, rcy + 14), 1)
                pygame.draw.line(surface, (255, 240, 150), (rcx, rcy - 16), (rcx - 11, rcy + 14), 1)
                pygame.draw.circle(surface, (255, 255, 220), (rcx, rcy - 1), 3)

                lbl = f_lbl.render("RELIC [RESTORED]", True, (110, 235, 150))
            else:
                # Broken polygon shards with jagged fracture lines
                shard1 = [(rcx - 12, rcy - 10), (rcx - 2, rcy - 14), (rcx - 4, rcy - 2)]
                shard2 = [(rcx + 2, rcy - 12), (rcx + 14, rcy - 6), (rcx + 6, rcy + 4)]
                shard3 = [(rcx - 10, rcy + 4), (rcx + 2, rcy + 12), (rcx - 4, rcy + 15)]
                for sh, col in [(shard1, (175, 125, 50)), (shard2, (195, 140, 60)), (shard3, (155, 110, 45))]:
                    pygame.draw.polygon(surface, col, sh)
                    pygame.draw.polygon(surface, (255, 195, 90), sh, 1)
                # Red-gold fissure crack
                pygame.draw.line(surface, (245, 90, 60), (rcx - 6, rcy - 2), (rcx + 4, rcy + 2), 1)
                lbl = f_lbl.render("BROKEN RELIC", True, (215, 175, 75))

            surface.blit(lbl, (rcx - lbl.get_width() // 2, ry - 14))

        # -------------------------------------------------------------
        # Right Station: Memory Fragments (Median Filter & Plaque)
        # -------------------------------------------------------------
        mem_r = self.station_memory_fragments["rect"]
        if vp.colliderect(mem_r):
            mx = mem_r.x - ox
            my = mem_r.y - oy
            mw, mh = mem_r.width, mem_r.height
            mcx, mcy = mx + mw // 2, my + mh // 2

            # Stone Pedestal Base
            pygame.draw.rect(surface, (18, 22, 30), (mx, my, mw, mh), border_radius=6)
            pygame.draw.rect(surface, (60, 130, 190), (mx, my, mw, mh), width=2, border_radius=6)
            pygame.draw.rect(surface, (28, 38, 52), (mx + 4, my + 4, mw - 8, mh - 8), border_radius=4)

            tablet_r = pygame.Rect(mx + 8, my + 8, mw - 16, mh - 16)
            pygame.draw.rect(surface, (14, 18, 26), tablet_r, border_radius=3)

            if self.memory_fragments_solved:
                # Cyan restored aura
                glow_s = pygame.Surface((mw + 24, mh + 24), pygame.SRCALPHA)
                pygame.draw.circle(glow_s, (50, 180, 255, 45), (mw // 2 + 12, mh // 2 + 12), mw // 2 + 8)
                surface.blit(glow_s, (mx - 12, my - 12))

                # Crisp runic inscription glyphs (denoised)
                pygame.draw.line(surface, (120, 220, 255), (tablet_r.left + 5, tablet_r.centery - 6), (tablet_r.right - 5, tablet_r.centery - 6), 2)
                pygame.draw.line(surface, (120, 220, 255), (tablet_r.left + 5, tablet_r.centery + 6), (tablet_r.right - 5, tablet_r.centery + 6), 2)
                pygame.draw.circle(surface, (210, 250, 255), (mcx, mcy), 4)
                pygame.draw.circle(surface, (60, 190, 255), (mcx, mcy), 7, width=1)
                lbl = f_lbl.render("PLAQUE [RESTORED]", True, (110, 235, 150))
            else:
                # Salt & Pepper noisy dots simulating impulse noise
                for px in range(tablet_r.left + 4, tablet_r.right - 4, 4):
                    for py in range(tablet_r.top + 4, tablet_r.bottom - 4, 4):
                        h = ((px * 37) ^ (py * 59)) % 10
                        if h < 2:
                            surface.set_at((px, py), (255, 255, 255))
                        elif h < 4:
                            surface.set_at((px, py), (0, 0, 0))
                        elif h == 5:
                            surface.set_at((px, py), (70, 140, 210))
                lbl = f_lbl.render("MEMORY PLAQUE", True, (100, 170, 240))

            surface.blit(lbl, (mcx - lbl.get_width() // 2, my - 14))

        # -------------------------------------------------------------
        # Bottom Station: Ancient Blueprint (UV Texture Mapping)
        # -------------------------------------------------------------
        bp_r = self.station_ancient_blueprint["rect"]
        if vp.colliderect(bp_r):
            bx = bp_r.x - ox
            by = bp_r.y - oy
            bw, bh = bp_r.width, bp_r.height
            bcx, bcy = bx + bw // 2, by + bh // 2

            # Drafting Table Base
            pygame.draw.rect(surface, (28, 20, 16), (bx, by, bw, bh), border_radius=6)
            pygame.draw.rect(surface, (190, 115, 55), (bx, by, bw, bh), width=2, border_radius=6)
            pygame.draw.rect(surface, (36, 26, 20), (bx + 4, by + 4, bw - 8, bh - 8), border_radius=4)

            paper_r = pygame.Rect(bx + 8, by + 6, bw - 16, bh - 12)
            pygame.draw.rect(surface, (24, 30, 42), paper_r, border_radius=3)
            pygame.draw.rect(surface, (70, 110, 160), paper_r, width=1, border_radius=3)

            if self.ancient_blueprint_solved:
                # Emerald harmonic glow
                glow_s = pygame.Surface((bw + 20, bh + 20), pygame.SRCALPHA)
                pygame.draw.circle(glow_s, (60, 220, 120, 45), (bw // 2 + 10, bh // 2 + 10), bh // 2 + 8)
                surface.blit(glow_s, (bx - 10, by - 10))

                # Fully mapped mosaic grid (4 quads with radiant compass)
                pygame.draw.line(surface, (100, 230, 160), (paper_r.centerx, paper_r.top + 2), (paper_r.centerx, paper_r.bottom - 2), 1)
                pygame.draw.line(surface, (100, 230, 160), (paper_r.left + 2, paper_r.centery), (paper_r.right - 2, paper_r.centery), 1)
                pygame.draw.circle(surface, (240, 255, 180), (paper_r.centerx, paper_r.centery), 4)
                lbl = f_lbl.render("BLUEPRINT [MAPPED]", True, (110, 235, 150))
            else:
                # Drafting grid lines & drafting compass tool
                pygame.draw.line(surface, (50, 80, 120), (paper_r.left + 4, paper_r.centery), (paper_r.right - 4, paper_r.centery), 1)
                pygame.draw.line(surface, (50, 80, 120), (paper_r.centerx, paper_r.top + 3), (paper_r.centerx, paper_r.bottom - 3), 1)
                pygame.draw.line(surface, (225, 175, 75), (bcx - 5, bcy + 5), (bcx, bcy - 5), 2)
                pygame.draw.line(surface, (225, 175, 75), (bcx + 5, bcy + 5), (bcx, bcy - 5), 2)
                lbl = f_lbl.render("ANCIENT BLUEPRINT", True, (225, 145, 65))

            surface.blit(lbl, (bcx - lbl.get_width() // 2, by - 14))

        # -------------------------------------------------------------
        # Top Station: Ancient Rule (Path Markers 1, 2, 3)
        # -------------------------------------------------------------
        rule_r = self.station_ancient_rule["rect"]
        if vp.colliderect(rule_r):
            tx = rule_r.x - ox
            ty = rule_r.y - oy
            tw, th = rule_r.width, rule_r.height
            tcx, tcy = tx + tw // 2, ty + th // 2

            # Frieze Arch Base
            pygame.draw.rect(surface, (24, 20, 28), (tx, ty, tw, th), border_radius=6)
            pygame.draw.rect(surface, (180, 150, 70), (tx, ty, tw, th), width=2, border_radius=6)
            pygame.draw.rect(surface, (38, 30, 42), (tx + 4, ty + 4, tw - 8, th - 8), border_radius=4)

            # Three colored path markers: Red (1), Blue (2), Green (3)
            p_colors = [(235, 75, 75), (65, 145, 250), (70, 225, 110)]
            p_spacing = (tw - 20) // 3
            for i, p_col in enumerate(p_colors):
                px = tx + 12 + i * p_spacing
                py = tcy
                pygame.draw.circle(surface, p_col, (px, py), 5)
                pygame.draw.circle(surface, (255, 255, 255), (px, py), 2)
                num_lbl = f_lbl.render(str(i + 1), True, (240, 230, 210))
                surface.blit(num_lbl, (px - num_lbl.get_width() // 2, py + 6))

            if self.ancient_rule_discovered:
                pygame.draw.circle(surface, (255, 230, 110), (tcx, ty - 6), 4)
                lbl = f_lbl.render("ANCIENT RULE [READ]", True, (110, 235, 150))
            else:
                lbl = f_lbl.render("ANCIENT RULE", True, (230, 200, 90))

            surface.blit(lbl, (tcx - lbl.get_width() // 2, ty - 14))


    def _draw_phasing_platforms(self, surface: pygame.Surface, ox: int, oy: int):
        """Draws temporal oscillating platforms bridging the subterranean abyss in Zone E."""
        # 1. Subterranean Dynamic Core Fissure / Chasm
        chasm_x = 420 - ox
        chasm_y = 642 - oy
        chasm_w = 360
        chasm_h = 36

        # Deep abyss void
        pygame.draw.rect(surface, (8, 6, 12), (chasm_x, chasm_y, chasm_w, chasm_h), border_radius=6)
        # Jagged cavern lip / glowing rift edge
        fissure_pulse = int(140 + 35 * math.sin(self.forge_phase * 2.0))
        glow_color = (min(255, fissure_pulse + 50), 90, max(40, fissure_pulse - 60))
        pygame.draw.rect(surface, (45, 30, 55), (chasm_x - 2, chasm_y - 2, chasm_w + 4, chasm_h + 4), width=2, border_radius=6)
        pygame.draw.line(surface, glow_color, (chasm_x + 10, chasm_y), (chasm_x + chasm_w - 10, chasm_y), 1)
        pygame.draw.line(surface, glow_color, (chasm_x + 10, chasm_y + chasm_h), (chasm_x + chasm_w - 10, chasm_y + chasm_h), 1)

        # Stone buttress pier anchors
        for anchor_x in (chasm_x + 60, chasm_x + 180, chasm_x + 300):
            pygame.draw.rect(surface, (26, 22, 34), (anchor_x - 12, chasm_y - 4, 24, chasm_h + 8), border_radius=2)
            pygame.draw.rect(surface, (60, 48, 72), (anchor_x - 12, chasm_y - 4, 24, chasm_h + 8), width=1, border_radius=2)

        # 2. Phasing energy platform spans
        for p in self.phasing_platforms:
            pr = p["rect"].move(-ox, -oy)
            alpha_wave = 0.5 + 0.5 * math.cos(self.forge_phase * 1.5 + p["phase_offset"])
            alpha_int = int(255 * alpha_wave)
            surf = pygame.Surface((pr.width, pr.height), pygame.SRCALPHA)
            # Energy grid fill
            surf.fill((140, 80, 220, int(alpha_int * 0.75)))
            # Golden runic lattice trim
            pygame.draw.rect(surf, (240, 200, 255, alpha_int), (0, 0, pr.width, pr.height), width=2, border_radius=4)
            # Center energy beam bar
            pygame.draw.line(surf, (255, 255, 255, alpha_int), (6, pr.height // 2), (pr.width - 6, pr.height // 2), 2)
            surface.blit(surf, (pr.x, pr.y))

    def _draw_conduits(self, surface: pygame.Surface, ox: int, oy: int):
        """Draws carved stone rune trenches with dynamic flowing energy streams into the Forge."""
        altar_cx = self.crucible_rect.centerx - ox
        altar_cy = self.crucible_rect.centery - oy

        conduit_groups = [
            # 1. Key Conduits (West — Liquid Bronze / Imperial Gold)
            {
                "sockets": self.key_sockets,
                "placed_id": self.placed_relics["keys"],
                "target": (altar_cx - 42, altar_cy),
                "base_col": (75, 50, 30),
                "active_glow": (245, 175, 60),
                "active_core": (255, 235, 170),
                "name": "keys",
            },
            # 2. Mirror Conduits (North — Spectral Silver / Azure)
            {
                "sockets": self.mirror_sockets,
                "placed_id": self.placed_relics["mirrors"],
                "target": (altar_cx, altar_cy - 28),
                "base_col": (50, 60, 75),
                "active_glow": (140, 205, 255),
                "active_core": (230, 250, 255),
                "name": "mirrors",
            },
            # 3. Crystal Conduits (East — Radiant RGB Prism Light)
            {
                "sockets": self.crystal_sockets,
                "placed_id": self.placed_relics["crystals"],
                "target": (altar_cx + 42, altar_cy),
                "base_col": (40, 65, 70),
                "active_glow": (100, 245, 215),
                "active_core": (225, 255, 245),
                "name": "crystals",
            },
        ]

        for grp in conduit_groups:
            target_x, target_y = grp["target"]
            for i, sock in enumerate(grp["sockets"]):
                sx = sock["rect"].centerx - ox
                sy = sock["rect"].centery - oy
                is_active = (grp["placed_id"] == sock["relic_id"])

                # Determine active color (attuned to specific relic if active)
                if is_active and grp["name"] == "crystals":
                    glow_c = sock["color"]
                    core_c = (255, 255, 255)
                elif is_active:
                    glow_c = grp["active_glow"]
                    core_c = grp["active_core"]
                else:
                    glow_c = grp["base_col"]
                    core_c = (grp["base_col"][0] // 2, grp["base_col"][1] // 2, grp["base_col"][2] // 2)

                # 1. Carved stone trench bedding (3D floor channel)
                pygame.draw.line(surface, (10, 8, 14), (sx, sy), (target_x, target_y), 6)
                pygame.draw.line(surface, (38, 30, 44), (sx, sy), (target_x, target_y), 4)

                # 2. Inner conduit line
                if not is_active:
                    pygame.draw.line(surface, glow_c, (sx, sy), (target_x, target_y), 2)
                    pygame.draw.circle(surface, glow_c, (sx, sy), 3)
                else:
                    # Luminous active beam
                    beam_w = 4 if not getattr(self, "reduced_motion", False) else 3
                    pygame.draw.line(surface, glow_c, (sx, sy), (target_x, target_y), beam_w)
                    pygame.draw.line(surface, core_c, (sx, sy), (target_x, target_y), 1)

                    # Dynamic flowing energy pulses streaming into the crucible
                    t_pulse = (self.forge_phase * 2.8 + i * 0.33) % 1.0
                    px = int(sx + (target_x - sx) * t_pulse)
                    py = int(sy + (target_y - sy) * t_pulse)
                    pygame.draw.circle(surface, glow_c, (px, py), 4)
                    pygame.draw.circle(surface, (255, 255, 255), (px, py), 2)

                    # Socket connection node
                    pygame.draw.circle(surface, glow_c, (sx, sy), 5)
                    pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 2)

                    # Terminal Altar influx spark
                    pygame.draw.circle(surface, glow_c, (target_x, target_y), 6)
                    pygame.draw.circle(surface, (255, 255, 255), (target_x, target_y), 3)

    def _draw_architecture(self, surface: pygame.Surface, ox: int, oy: int, vp: pygame.Rect):
        """Draws perimeter masonry walls and massive stone pillars."""
        for w in self.walls:
            wr = w.move(-ox, -oy)
            if vp.colliderect(w):
                pygame.draw.rect(surface, (34, 28, 38), wr)
                pygame.draw.rect(surface, (18, 14, 22), wr, 2)
                if w.y == 0:
                    pygame.draw.line(surface, (135, 105, 50), (wr.left, wr.bottom - 2), (wr.right, wr.bottom - 2), 3)

        for p in self.pillars:
            pr = p.move(-ox, -oy)
            if vp.colliderect(p):
                shd = pr.inflate(14, 14)
                pygame.draw.rect(surface, (8, 6, 12), shd, border_radius=6)
                pygame.draw.rect(surface, (44, 38, 50), pr, border_radius=4)
                pygame.draw.rect(surface, (140, 110, 55), pr, width=2, border_radius=4)
                pygame.draw.rect(surface, (70, 58, 40), pr.inflate(-12, -12), width=1)
                pygame.draw.circle(surface, (200, 165, 75), pr.center, 6)



    def _draw_gates(self, surface: pygame.Surface, ox: int, oy: int):
        """Draws the colossal sealed Northern Forge mechanism and south entrance."""
        gr = self.sealed_gate_rect.move(-ox, -oy)
        is_solved = self.forge_engine.is_solved
        is_locked = self.forge_engine.is_locked
        is_open = is_solved or is_locked

        if is_open:
            pygame.draw.rect(surface, (10, 8, 14), gr, border_radius=6)
            frame_color = (130, 210, 255) if is_solved else (225, 140, 75)
            pygame.draw.rect(surface, frame_color, gr, width=2, border_radius=6)

            step_w = gr.width - 32
            for i, sy in enumerate(range(gr.top + 8, gr.bottom - 10, 10)):
                depth_shade = max(8, 35 - i * 6)
                pygame.draw.rect(surface, (depth_shade + 4, depth_shade, depth_shade + 8),
                                 (gr.centerx - step_w // 2 + i * 4, sy, step_w - i * 8, 8))
                pygame.draw.rect(surface, (frame_color[0] // 3, frame_color[1] // 3, frame_color[2] // 3),
                                 (gr.centerx - step_w // 2 + i * 4, sy, step_w - i * 8, 8), 1)

            if is_solved:
                pygame.draw.circle(surface, (90, 210, 255), (gr.centerx, gr.top + 12), 6)
                pygame.draw.circle(surface, (255, 255, 240), (gr.centerx, gr.top + 12), 3)
            else:
                pygame.draw.circle(surface, (220, 110, 50), (gr.centerx, gr.top + 12), 5)

            f_lbl = pygame.font.SysFont("consolas", 10, bold=True)
            lbl_text = "DESCENT UNSEALED" if is_solved else "EMERGENCY DESCENT"
            lbl_color = (200, 235, 255) if is_solved else (235, 170, 120)
            lbl = f_lbl.render(lbl_text, True, lbl_color)
            surface.blit(lbl, (gr.centerx - lbl.get_width() // 2, gr.bottom - 16))
        else:
            pygame.draw.rect(surface, (24, 20, 28), gr, border_radius=6)
            pygame.draw.rect(surface, (170, 130, 60), gr, width=2, border_radius=6)
            pygame.draw.rect(surface, (80, 60, 35), gr.inflate(-8, -8), width=1)

            for px in range(gr.left + 24, gr.right - 20, 36):
                pygame.draw.rect(surface, (40, 34, 46), (px, gr.top + 6, 14, gr.height - 12), border_radius=2)
                pygame.draw.rect(surface, (110, 90, 55), (px, gr.top + 6, 14, gr.height - 12), width=1, border_radius=2)

            pygame.draw.circle(surface, (16, 12, 20), gr.center, 18)
            pygame.draw.circle(surface, (190, 145, 60), gr.center, 18, width=2)
            pygame.draw.circle(surface, (80, 60, 35), gr.center, 8, width=1)

            f_lbl = pygame.font.SysFont("consolas", 10, bold=True)
            lbl = f_lbl.render("SEALED FORGE GATE", True, (190, 160, 110))
            surface.blit(lbl, (gr.centerx - lbl.get_width() // 2, gr.bottom - 16))

        # South entrance
        er = self.entrance_rect.move(-ox, -oy)
        pygame.draw.rect(surface, (22, 18, 26), er)
        pygame.draw.rect(surface, (120, 95, 50), er, width=2)
        for bx in range(er.left + 15, er.right - 10, 18):
            pygame.draw.line(surface, (70, 55, 35), (bx, er.top), (bx, er.bottom), 2)

    def _draw_altar(self, surface: pygame.Surface, ox: int, oy: int):
        """Draws the central raised Forge Altar with celestial golden structure, orbital rings, and magical fire."""
        ar = self.altar_rect.move(-ox, -oy)
        cr = self.crucible_rect.move(-ox, -oy)

        reduced_motion = getattr(self, "reduced_motion", False) or getattr(settings, "reduced_motion", False)
        self.forge_renderer.draw(
            surface=surface,
            altar_rect=ar,
            crucible_rect=cr,
            forge_state=self.forge_state,
            anim_time=self.forge_phase,
            flicker_phase=self.flicker_phase,
            placed_relics=self.placed_relics,
            reduced_motion=reduced_motion,
            awakening_time=self.guardian_awakening_time,
        )

        if self.forge_engine.is_solved:
            self._draw_lumen_sigil(surface, ox, oy)

    def _draw_lumen_sigil(self, surface: pygame.Surface, ox: int, oy: int):
        """Renders the manifested 3D-styled celestial diamond Lumen Sigil hovering above the crucible."""
        cx = int(self.crucible_rect.centerx - ox)
        cy = int(self.crucible_rect.centery - oy)
        reduced_motion = getattr(self, "reduced_motion", False) or getattr(settings, "reduced_motion", False)
        bob = 0.0 if reduced_motion else math.sin(self.forge_phase * 2.5) * 5.0
        sy = cy - 8 + bob

        # 1. Soft celestial blue radiant glow aura
        aura_rad = 28
        aura_surf = pygame.Surface((aura_rad * 2, aura_rad * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (100, 200, 255, 45), (aura_rad, aura_rad), aura_rad)
        pygame.draw.circle(aura_surf, (160, 230, 255, 70), (aura_rad, aura_rad), int(aura_rad * 0.6))
        surface.blit(aura_surf, (cx - aura_rad, int(sy - aura_rad)))

        # 2. Rotating ethereal celestial ring
        ang = 0.0 if reduced_motion else self.forge_phase * 1.5
        rx, ry = 22, 9
        ring_pts = []
        for i in range(16):
            theta = ang + i * (2 * math.pi / 16)
            ring_pts.append((int(cx + rx * math.cos(theta)), int(sy + ry * math.sin(theta))))
        if len(ring_pts) > 2:
            pygame.draw.lines(surface, (140, 225, 255), True, ring_pts, 1)

        # 3. Faceted celestial diamond sigil
        w, h = 14, 20
        top = (cx, int(sy - h))
        right = (cx + w, int(sy))
        bottom = (cx, int(sy + h))
        left = (cx - w, int(sy))

        # Upper left facet (bright starlight cyan)
        pygame.draw.polygon(surface, (190, 240, 255), [top, left, (cx, int(sy))])
        # Upper right facet (pure radiant white-cyan)
        pygame.draw.polygon(surface, (230, 250, 255), [top, right, (cx, int(sy))])
        # Lower left facet (deep celestial azure)
        pygame.draw.polygon(surface, (70, 150, 240), [bottom, left, (cx, int(sy))])
        # Lower right facet (vibrant royal blue)
        pygame.draw.polygon(surface, (90, 180, 255), [bottom, right, (cx, int(sy))])

        # Facet borders in bright gold/starlight
        pygame.draw.polygon(surface, (245, 240, 200), [top, right, bottom, left], 1)
        pygame.draw.line(surface, (255, 255, 255), top, bottom, 1)
        pygame.draw.line(surface, (255, 255, 255), left, right, 1)

        # 4. Brilliant center glint spark & starburst
        pygame.draw.circle(surface, (255, 255, 255), (cx, int(sy)), 3)
        pygame.draw.line(surface, (255, 255, 255), (cx - 7, int(sy)), (cx + 7, int(sy)), 1)
        pygame.draw.line(surface, (255, 255, 255), (cx, int(sy - 7)), (cx, int(sy + 7)), 1)

    def _draw_sockets(self, surface: pygame.Surface, ox: int, oy: int):
        """Draws Keyways, Mirror Stands, and Crystal Spires with physical placed items."""
        # 1. Key Sockets (West) — Level 1 Ornate Keys
        for ks in self.key_sockets:
            r = ks["rect"].move(-ox, -oy)
            cx, cy = r.center
            is_placed = (self.placed_relics["keys"] == ks["relic_id"])
            relic_id = ks["relic_id"]

            # Ancient carved stone keyway plinth
            pygame.draw.rect(surface, (28, 24, 34), r, border_radius=6)
            pygame.draw.rect(surface, (55, 46, 64), r, width=2, border_radius=6)
            inner_box = r.inflate(-8, -8)
            pygame.draw.rect(surface, (18, 15, 22), inner_box, border_radius=4)

            if not is_placed:
                # Dim unplaced state: Carved keyhole slot with subtle accent rim
                dim_rim = (ks["color"][0] // 3, ks["color"][1] // 3, ks["color"][2] // 3)
                pygame.draw.rect(surface, dim_rim, inner_box, width=1, border_radius=4)
                # Keyhole silhouette: circular top and tapered trapezoid slot
                pygame.draw.circle(surface, (10, 8, 14), (cx, cy - 3), 5)
                pygame.draw.polygon(surface, (10, 8, 14), [
                    (cx - 3, cy - 1), (cx + 3, cy - 1),
                    (cx + 1, cy + 8), (cx - 1, cy + 8)
                ])
                # Delicate inner bevel
                pygame.draw.circle(surface, (36, 30, 42), (cx, cy - 3), 5, width=1)
            else:
                # Placed state: Shining Level 1 ornate fantasy key inserted into the plinth!
                k_pulse = 0.5 + 0.5 * math.sin(self.flicker_phase * 2.5)
                aura_r = int(22 + 4 * k_pulse)
                aura_s = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)

                if "bronze" in relic_id:
                    c_metal = (185, 120, 55)
                    c_light = (225, 165, 95)
                    c_dark = (100, 65, 30)
                    aura_col = (215, 145, 60, int(35 + 20 * k_pulse))
                elif "silver" in relic_id:
                    c_metal = (195, 205, 220)
                    c_light = (245, 250, 255)
                    c_dark = (110, 120, 135)
                    aura_col = (180, 210, 255, int(35 + 20 * k_pulse))
                else:  # gold
                    c_metal = (235, 195, 55)
                    c_light = (255, 240, 130)
                    c_dark = (150, 115, 25)
                    aura_col = (255, 215, 75, int(45 + 20 * k_pulse))

                pygame.draw.circle(aura_s, aura_col, (aura_r, aura_r), aura_r)
                surface.blit(aura_s, (cx - aura_r, cy - aura_r))

                # Exact Level 1 Key geometry inserted in socket
                head_y = cy - 7
                if "bronze" in relic_id:
                    # Bronze Key: Triple crescent head with central astrological star cross
                    pygame.draw.circle(surface, c_dark, (cx, head_y), 6, width=2)
                    pygame.draw.circle(surface, c_metal, (cx, head_y), 5, width=2)
                    pygame.draw.line(surface, c_light, (cx - 3, head_y), (cx + 3, head_y), 1)
                    pygame.draw.line(surface, c_light, (cx, head_y - 3), (cx, head_y + 3), 1)
                    pygame.draw.circle(surface, c_light, (cx, head_y - 8), 2)
                    pygame.draw.arc(surface, c_light, (cx - 10, head_y - 10, 9, 9), 0.3, 2.8, 2)
                    pygame.draw.arc(surface, c_light, (cx + 1, head_y - 10, 9, 9), 0.3, 2.8, 2)
                elif "silver" in relic_id:
                    # Silver Key: Filigree heart bow with crown finial
                    pygame.draw.polygon(surface, c_light, [(cx, head_y - 10), (cx - 3, head_y - 7), (cx + 3, head_y - 7)])
                    pygame.draw.circle(surface, c_metal, (cx - 3, head_y - 3), 3, width=2)
                    pygame.draw.circle(surface, c_metal, (cx + 3, head_y - 3), 3, width=2)
                    pygame.draw.polygon(surface, c_metal, [
                        (cx - 6, head_y - 2), (cx + 6, head_y - 2), (cx, head_y + 5)
                    ], width=2)
                    pygame.draw.circle(surface, c_light, (cx - 1, head_y - 2), 2)
                else:  # gold
                    # Gold Key: Imperial crown crest with fleur-de-lis finial
                    pygame.draw.circle(surface, c_light, (cx, head_y - 9), 2)
                    ov_r = pygame.Rect(cx - 7, head_y - 7, 14, 13)
                    pygame.draw.ellipse(surface, c_metal, ov_r, width=2)
                    pygame.draw.polygon(surface, c_light, [
                        (cx - 4, head_y + 1), (cx - 3, head_y - 3), (cx, head_y - 1),
                        (cx + 3, head_y - 3), (cx + 4, head_y + 1)
                    ], width=1)

                # Neck collar & shaft
                neck_y = head_y + 6
                pygame.draw.line(surface, c_light, (cx - 3, neck_y), (cx + 3, neck_y), 2)
                shaft_bot = cy + 12
                pygame.draw.line(surface, c_dark, (cx + 1, neck_y + 2), (cx + 1, shaft_bot), 2)
                pygame.draw.line(surface, c_metal, (cx, neck_y + 2), (cx, shaft_bot), 2)
                pygame.draw.line(surface, c_light, (cx - 1, neck_y + 2), (cx - 1, shaft_bot), 1)

                # Antique ward bit with hollow notch
                bit_y = cy + 4
                pygame.draw.rect(surface, c_metal, (cx, bit_y, 6, 7))
                pygame.draw.rect(surface, c_dark, (cx, bit_y, 6, 7), width=1)
                pygame.draw.rect(surface, (18, 15, 22), (cx + 2, bit_y + 2, 2, 2))
                pygame.draw.line(surface, c_light, (cx + 5, bit_y), (cx + 5, bit_y + 7), 1)

        # 2. Mirror Sockets (North) — Level 2 Refractor Mirrors
        for ms in self.mirror_sockets:
            r = ms["rect"].move(-ox, -oy)
            cx, cy = r.center
            is_placed = (self.placed_relics["mirrors"] == ms["relic_id"])
            relic_id = ms["relic_id"]

            # Circular pedestal stand base
            pygame.draw.ellipse(surface, (22, 18, 28), (cx - 18, cy + 10, 36, 12))
            pygame.draw.rect(surface, (42, 35, 48), (cx - 14, cy + 4, 28, 8), border_radius=3)
            pygame.draw.line(surface, (140, 110, 55), (cx - 12, cy + 5), (cx + 12, cy + 5), 2)

            if not is_placed:
                # Dim unplaced stand: Empty circular mount with dark cavity
                dim_rim = (ms["color"][0] // 3, ms["color"][1] // 3, ms["color"][2] // 3)
                pygame.draw.circle(surface, (32, 26, 40), (cx, cy - 2), 16)
                pygame.draw.circle(surface, dim_rim, (cx, cy - 2), 16, width=2)
                pygame.draw.circle(surface, (14, 11, 18), (cx, cy - 2), 11)
                pygame.draw.circle(surface, dim_rim, (cx - 9, cy - 2), 2)
                pygame.draw.circle(surface, dim_rim, (cx + 9, cy - 2), 2)
            else:
                # Placed state: Exact Level 2 Refractor Mirror shining bright!
                m_pulse = 0.5 + 0.5 * math.sin(self.flicker_phase * 2.8)
                aura_r = int(24 + 5 * m_pulse)
                aura_s = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)

                if "red" in relic_id:
                    m_style = {
                        "glass": (225, 175, 185), "sheen": (255, 220, 230),
                        "rim": (140, 65, 75), "aura": (255, 95, 115), "gem": (220, 50, 65),
                    }
                elif "blue" in relic_id:
                    m_style = {
                        "glass": (175, 215, 240), "sheen": (225, 245, 255),
                        "rim": (65, 95, 145), "aura": (90, 165, 255), "gem": (50, 135, 245),
                    }
                else:  # green
                    m_style = {
                        "glass": (175, 235, 195), "sheen": (225, 255, 235),
                        "rim": (65, 135, 85), "aura": (90, 245, 145), "gem": (50, 215, 105),
                    }

                # Reflective aura
                pygame.draw.circle(aura_s, (*m_style["aura"], int(45 + 25 * m_pulse)), (aura_r, aura_r), aura_r)
                pygame.draw.circle(aura_s, (*m_style["sheen"], int(70 + 30 * m_pulse)), (aura_r, aura_r), int(aura_r * 0.6))
                surface.blit(aura_s, (cx - aura_r, cy - 2 - aura_r))

                # Outer bronze frame & rococo crest
                frame_r = pygame.Rect(cx - 13, cy - 16, 26, 26)
                pygame.draw.rect(surface, (85, 65, 30), frame_r, border_radius=8)
                pygame.draw.rect(surface, (165, 130, 65), frame_r, width=2, border_radius=8)
                # Top finial crest
                pygame.draw.polygon(surface, (165, 130, 65), [(cx, cy - 20), (cx - 4, cy - 16), (cx + 4, cy - 16)])
                pygame.draw.circle(surface, m_style["gem"], (cx, cy - 16), 2)

                # Resonant reflective glass face
                glass = pygame.Rect(cx - 9, cy - 12, 18, 18)
                pygame.draw.rect(surface, m_style["glass"], glass, border_radius=5)
                pygame.draw.rect(surface, m_style["rim"], glass, width=1, border_radius=5)
                # Diagonal sheen beam line
                pygame.draw.line(surface, m_style["sheen"], (glass.x + 2, glass.bottom - 3), (glass.right - 2, glass.y + 3), 2)
                # Specular white sparkle
                pygame.draw.circle(surface, (255, 255, 255), (glass.centerx - 2, glass.centery - 2), 2)

        # 3. Crystal Sockets (East) — Level 3 Source Crystals (RGB)
        for cs in self.crystal_sockets:
            r = cs["rect"].move(-ox, -oy)
            cx, cy = r.center
            is_placed = (self.placed_relics["crystals"] == cs["relic_id"])
            relic_id = cs["relic_id"]

            # Exact Level 3 carved stone mounting base with bronze trim
            base_r = pygame.Rect(cx - 16, cy + 10, 32, 10)
            pygame.draw.rect(surface, (45, 38, 52), base_r, border_radius=3)
            pygame.draw.rect(surface, (150, 120, 60), base_r, width=1, border_radius=3)

            # Palette configuration: RGB (Socket 1: Red, Socket 2: Green, Socket 3: Blue)
            if "1" in relic_id or "red" in relic_id:
                if not is_placed:
                    c_dark = (65, 18, 25)
                    c_mid = (95, 28, 38)
                    c_light = (130, 40, 52)
                    c_core = (85, 25, 35)
                    c_border = (110, 40, 50)
                else:
                    c_dark = (195, 25, 45)
                    c_mid = (245, 55, 80)
                    c_light = (255, 115, 135)
                    c_core = (255, 225, 235)
                    c_border = (255, 180, 195)
                    c_aura_outer = (255, 60, 80)
                    c_aura_inner = (255, 120, 140)
            elif "2" in relic_id or "green" in relic_id:
                if not is_placed:
                    c_dark = (18, 55, 28)
                    c_mid = (28, 85, 42)
                    c_light = (42, 115, 60)
                    c_core = (32, 75, 40)
                    c_border = (50, 100, 60)
                else:
                    c_dark = (25, 175, 65)
                    c_mid = (55, 235, 105)
                    c_light = (115, 255, 155)
                    c_core = (220, 255, 230)
                    c_border = (180, 255, 200)
                    c_aura_outer = (60, 235, 110)
                    c_aura_inner = (120, 255, 160)
            else:  # 3 or blue
                if not is_placed:
                    c_dark = (20, 40, 75)
                    c_mid = (30, 65, 115)
                    c_light = (48, 95, 155)
                    c_core = (35, 60, 105)
                    c_border = (60, 90, 140)
                else:
                    c_dark = (25, 110, 215)
                    c_mid = (55, 165, 255)
                    c_light = (120, 210, 255)
                    c_core = (220, 240, 255)
                    c_border = (180, 225, 255)
                    c_aura_outer = (60, 160, 255)
                    c_aura_inner = (130, 210, 255)

            # Levitation bob & Aura
            if is_placed:
                float_y = cy - 2 + int(3.0 * math.sin(self.flicker_phase * 2.2))
                pulse = 0.5 + 0.5 * math.sin(self.flicker_phase * 3.0)
                aura_rad = int(32 + 6 * pulse)
                aura_surf = pygame.Surface((aura_rad * 2, aura_rad * 2), pygame.SRCALPHA)
                alpha = int(50 + 25 * pulse)
                pygame.draw.circle(aura_surf, (*c_aura_outer, alpha), (aura_rad, aura_rad), aura_rad)
                pygame.draw.circle(aura_surf, (*c_aura_inner, alpha + 35), (aura_rad, aura_rad), int(aura_rad * 0.65))
                surface.blit(aura_surf, (cx - aura_rad, float_y - aura_rad))
            else:
                float_y = cy + 2

            # Exact Level 3 Faceted diamond spire
            pts_outer = [
                (cx, float_y - 20),
                (cx + 12, float_y),
                (cx, float_y + 14),
                (cx - 12, float_y),
            ]
            pts_left = [(cx, float_y - 20), (cx - 12, float_y), (cx, float_y + 14)]
            pts_right = [(cx, float_y - 20), (cx + 12, float_y), (cx, float_y + 14)]

            pygame.draw.polygon(surface, c_dark, pts_outer)
            pygame.draw.polygon(surface, c_mid, pts_left)
            pygame.draw.polygon(surface, c_light, pts_right)

            # Inner crystal core
            pts_core = [
                (cx, float_y - 10),
                (cx + 5, float_y),
                (cx, float_y + 7),
                (cx - 5, float_y),
            ]
            pygame.draw.polygon(surface, c_core, pts_core)
            pygame.draw.polygon(surface, c_border, pts_outer, width=1)

            if is_placed:
                # Radiant white center spark & starburst gleam cross
                pygame.draw.circle(surface, (255, 255, 255), (cx, float_y), 3)
                pygame.draw.line(surface, (255, 255, 255), (cx - 6, float_y), (cx + 6, float_y), 1)
                pygame.draw.line(surface, (255, 255, 255), (cx, float_y - 6), (cx, float_y + 6), 1)

    def _draw_guardian(self, surface: pygame.Surface, ox: int, oy: int):
        """Renders the celestial Temple Guardian with sanctum terrace, twin braziers, and halo."""
        gr = self.guardian_rect.move(-ox, -oy)
        is_awake = self.forge_engine.is_solved
        is_locked = self.forge_engine.is_locked
        reduced_motion = getattr(self, "reduced_motion", False) or getattr(settings, "reduced_motion", False)

        tcx = gr.centerx
        t_base_y = gr.bottom - 6

        if not is_awake:
            # 1. Sanctum Platform in deep shadow
            step_w1, step_w2 = 96, 80
            pygame.draw.rect(surface, (14, 12, 18), (tcx - step_w1 // 2, t_base_y - 2, step_w1, 14), border_radius=4)
            pygame.draw.rect(surface, (32, 26, 40), (tcx - step_w1 // 2, t_base_y - 2, step_w1, 14), width=1, border_radius=4)
            pygame.draw.rect(surface, (18, 14, 24), (tcx - step_w2 // 2, t_base_y - 8, step_w2, 10), border_radius=3)
            pygame.draw.rect(surface, (55, 45, 30), (tcx - step_w2 // 2, t_base_y - 8, step_w2, 10), width=1, border_radius=3)

            # Cold dormant runic arc
            pygame.draw.arc(surface, (38, 30, 48), (tcx - 42, t_base_y - 32, 84, 38), 3.14, 6.28, 1)

            # Cold dormant braziers (unlit dark charcoal, no flames)
            for bx in (tcx - 48, tcx + 48):
                by = t_base_y - 6
                pygame.draw.rect(surface, (16, 14, 20), (bx - 7, by - 12, 14, 16), border_radius=2)
                pygame.draw.rect(surface, (50, 40, 25), (bx - 7, by - 12, 14, 16), width=1, border_radius=2)
                pygame.draw.ellipse(surface, (60, 48, 30), (bx - 9, by - 16, 18, 8))
                pygame.draw.ellipse(surface, (20, 16, 22), (bx - 7, by - 15, 14, 6))

            # Guardian Dark Shadow Silhouette
            # Soft dark violet shadow ambient aura behind silhouette
            aura_surf = pygame.Surface((gr.width + 30, gr.height + 30), pygame.SRCALPHA)
            pygame.draw.ellipse(aura_surf, (15, 8, 25, 75), (0, 0, gr.width + 30, gr.height + 30))
            surface.blit(aura_surf, (gr.x - 15, gr.y - 15))

            # Dark shadow silhouette body
            s_pts = [
                (gr.centerx, gr.top + 2),
                (gr.right - 10, gr.top + 16),
                (gr.right - 6, gr.bottom - 4),
                (gr.left + 6, gr.bottom - 4),
                (gr.left + 10, gr.top + 16),
            ]
            pygame.draw.polygon(surface, (14, 12, 18), s_pts)
            pygame.draw.polygon(surface, (28, 22, 34), s_pts, 1)

            # Dormant staff in shadow
            staff_x = gr.left + 8
            pygame.draw.line(surface, (30, 25, 35), (staff_x, gr.top + 6), (staff_x, gr.bottom), 2)
            pygame.draw.circle(surface, (22, 18, 28), (staff_x, gr.top + 6), 4)
            pygame.draw.circle(surface, (45, 38, 55), (staff_x, gr.top + 6), 4, 1)
            return

        # 1. Architectural Sanctum Terrace Platform (Awakened)
        step_w1, step_w2 = 96, 80
        pygame.draw.rect(surface, (20, 16, 26), (tcx - step_w1 // 2, t_base_y - 2, step_w1, 14), border_radius=4)
        pygame.draw.rect(surface, (55, 42, 68), (tcx - step_w1 // 2, t_base_y - 2, step_w1, 14), width=1, border_radius=4)
        pygame.draw.rect(surface, (28, 22, 38), (tcx - step_w2 // 2, t_base_y - 8, step_w2, 10), border_radius=3)
        pygame.draw.rect(surface, (140, 110, 55), (tcx - step_w2 // 2, t_base_y - 8, step_w2, 10), width=1, border_radius=3)

        # Inlaid sacred runic floor arc
        arc_col = (90, 210, 255)
        pygame.draw.arc(surface, arc_col, (tcx - 42, t_base_y - 32, 84, 38), 3.14, 6.28, 1)

        # 2. Twin Ceremonial Braziers flanking the terrace (Awakened Flames)
        for bx in (tcx - 48, tcx + 48):
            by = t_base_y - 6
            # Pedestal
            pygame.draw.rect(surface, (22, 18, 28), (bx - 7, by - 12, 14, 16), border_radius=2)
            pygame.draw.rect(surface, (130, 100, 50), (bx - 7, by - 12, 14, 16), width=1, border_radius=2)
            # Bronze bowl
            pygame.draw.ellipse(surface, (160, 120, 55), (bx - 9, by - 16, 18, 8))
            pygame.draw.ellipse(surface, (40, 30, 20), (bx - 7, by - 15, 14, 6))

            # Cyan sacred flame
            f_phase = self.flicker_phase * 2.5 + (0.5 if bx > tcx else 0.0)
            f_height = 12 + int(2.0 * math.sin(f_phase))
            f_col_outer = (50, 180, 255) if not is_locked else (180, 50, 40)
            f_col_inner = (210, 245, 255) if not is_locked else (255, 160, 140)

            # Flame glow
            g_rad = 12
            g_surf = pygame.Surface((g_rad * 2, g_rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(g_surf, (*f_col_outer, 45), (g_rad, g_rad), g_rad)
            surface.blit(g_surf, (bx - g_rad, by - 18 - g_rad))

            # Flame tongue polygon
            f_pts = [(bx - 4, by - 14), (bx, by - 14 - f_height), (bx + 4, by - 14)]
            pygame.draw.polygon(surface, f_col_outer, f_pts)
            f_core = [(bx - 2, by - 14), (bx, by - 13 - f_height * 0.65), (bx + 2, by - 14)]
            pygame.draw.polygon(surface, f_col_inner, f_core)

        # 3. Celestial Guardian Character (Awakened Radiance)
        draw_guardian(
            surface=surface,
            rect=gr,
            is_awake=True,
            is_locked=is_locked,
            anim_time=self.guardian_anim_time,
            awakening_time=self.guardian_awakening_time,
            reduced_motion=reduced_motion,
        )

    def _draw_particles(self, surface: pygame.Surface, ox: int, oy: int):
        """Draws crucible embers and procedural ash particles."""
        # Embers
        for p in self.embers:
            ex = int(p["x"] - ox)
            ey = int(p["y"] - oy)
            if 0 <= ex < L4_SCREEN_WIDTH and 0 <= ey < L4_SCREEN_HEIGHT:
                alpha = int(max(10, min(255, p["alpha"])))
                e_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(e_surf, (255, 140, 40, alpha), (3, 3), max(1, int(p["size"])))
                surface.blit(e_surf, (ex - 3, ey - 3))

        # Ash particles (Zone A)
        for p in self.ash_particles:
            ax = int(p["x"] - ox)
            ay = int(p["y"] - oy)
            if 0 <= ax < L4_SCREEN_WIDTH and 0 <= ay < L4_SCREEN_HEIGHT:
                alpha = int(max(10, min(255, p["alpha"])))
                a_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                pygame.draw.circle(a_surf, (160, 150, 170, alpha), (2, 2), max(1, int(p["size"])))
                surface.blit(a_surf, (ax - 2, ay - 2))

    def _draw_lighting(self, surface: pygame.Surface, player, lantern, ox: int, oy: int):
        """Renders dim ambient temple darkness with smooth continuous alpha-composited radial light."""
        if getattr(lantern, "active", False):
            if getattr(lantern, "radius", 0) <= 0:
                lantern.radius = getattr(lantern, "base_radius", 130)

        # 1. Dim atmospheric temple darkness mask (ambient alpha = 115)
        # Not pitch black: allows ancient architecture and relics to remain dimly visible
        ambient_alpha = 115
        dim_mask = pygame.Surface((L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_mask.fill((10, 8, 16, ambient_alpha))

        # 2. Subtract smooth radial light cutouts using cubic-hermite smoothstep
        # A. Player Lantern Light Cutout
        l_active = getattr(lantern, "active", False) and player is not None
        if l_active:
            px = int(player.center[0] - ox)
            py = int(player.center[1] - oy)
            l_radius = max(80, int(getattr(lantern, "radius", 130)))
            flicker = 3.0 * math.sin(self.flicker_phase * 2.0)
            cur_r = int(l_radius + flicker)

            l_cookie = _get_smooth_cutout_cookie(cur_r, ambient_alpha)
            dim_mask.blit(l_cookie, (px - cur_r, py - cur_r), special_flags=pygame.BLEND_RGBA_SUB)

        # B. Celestial Forge & Lumen Sigil Hearth Light Cutout
        cx = int(self.crucible_rect.centerx - ox)
        cy = int(self.crucible_rect.centery - oy)
        forge_light_r = get_forge_lighting_radius(self.forge_state, self.forge_phase)
        f_pulse = 5.0 * math.sin(self.flicker_phase * 2.5)
        fr = int(max(100, forge_light_r + f_pulse))

        f_cookie = _get_smooth_cutout_cookie(fr, ambient_alpha)
        dim_mask.blit(f_cookie, (cx - fr, cy - fr), special_flags=pygame.BLEND_RGBA_SUB)

        # Blit the composited dim visibility mask onto world surface
        surface.blit(dim_mask, (0, 0))

        # 3. Soft Radial Atmospheric Bloom & Radiant Tinting
        # A. Lantern warm glow
        if l_active:
            color_map = {
                "white": (255, 235, 175),
                "red": (255, 120, 100),
                "green": (110, 255, 140),
                "blue": (120, 180, 255),
            }
            l_col_name = getattr(lantern, "color", "white")
            base_col = color_map.get(l_col_name, (255, 235, 175))
            l_glow = _get_smooth_glow_cookie(cur_r, base_col, 50)
            surface.blit(l_glow, (px - cur_r, py - cur_r))

        # B. Forge Hearth radiant bloom
        if self.forge_state == "harmonized":
            f_col = (180, 240, 255)
            f_alpha = 65
        elif self.forge_state == "locked":
            f_col = (255, 90, 60)
            f_alpha = 55
        else:
            f_col = (255, 220, 130)
            f_alpha = 50

        f_glow = _get_smooth_glow_cookie(fr, f_col, f_alpha)
        surface.blit(f_glow, (cx - fr, cy - fr))

        # 4. Lumen Sigil Starburst Glint
        flare_len = int(fr * 0.65)
        f_line_surf = pygame.Surface((flare_len * 2 + 10, flare_len * 2 + 10), pygame.SRCALPHA)
        fl_center = flare_len + 5
        line_a = int(f_alpha * 1.2)
        pygame.draw.line(f_line_surf, (*f_col, line_a), (fl_center - flare_len, fl_center), (fl_center + flare_len, fl_center), 2)
        pygame.draw.line(f_line_surf, (*f_col, line_a), (fl_center, fl_center - flare_len), (fl_center, fl_center + flare_len), 2)
        surface.blit(f_line_surf, (cx - fl_center, cy - fl_center))

    def _draw_modal(self, surface: pygame.Surface):
        """Renders the inspection lore modal popup."""
        if not self.active_modal:
            return

        dim = pygame.Surface((L4_SCREEN_WIDTH, L4_SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((6, 4, 10, 190))
        surface.blit(dim, (0, 0))

        is_guardian = self.active_modal.get("kind") == "guardian"
        mw, mh = (700, 390) if is_guardian else (620, 360)
        mx = (L4_SCREEN_WIDTH - mw) // 2
        my = (L4_SCREEN_HEIGHT - mh) // 2

        tablet = pygame.Surface((mw, mh), pygame.SRCALPHA)
        tablet.fill((20, 16, 28, 250))
        pygame.draw.rect(tablet, (200, 160, 75), (0, 0, mw, mh), width=2, border_radius=8)
        pygame.draw.rect(tablet, (80, 65, 40), (4, 4, mw - 8, mh - 8), width=1, border_radius=6)
        for cx, cy in [(6, 6), (mw - 10, 6), (6, mh - 10), (mw - 10, mh - 10)]:
            pygame.draw.rect(tablet, (240, 200, 80), (cx, cy, 4, 4))
        surface.blit(tablet, (mx, my))

        f_title = pygame.font.SysFont("georgia", 18, bold=True)
        f_body = pygame.font.SysFont("consolas", 13)
        f_foot = pygame.font.SysFont("consolas", 11, bold=True)

        t_surf = f_title.render(self.active_modal["title"], True, (248, 224, 148))
        surface.blit(t_surf, (mx + (mw - t_surf.get_width()) // 2, my + 22))
        pygame.draw.line(surface, (155, 125, 55), (mx + 40, my + 54), (mx + mw - 40, my + 54), 1)
        pygame.draw.circle(surface, (220, 185, 80), (mx + mw // 2, my + 54), 3)

        body_left = mx + 40
        body_width = mw - 80
        if is_guardian:
            self._draw_guardian_portrait(surface, pygame.Rect(mx + 28, my + 78, 170, 245))
            body_left = mx + 220
            body_width = mw - 255

        body_clip = pygame.Rect(body_left, my + 76, body_width, mh - 125)
        previous_clip = surface.get_clip()
        surface.set_clip(body_clip)
        lines = wrap_text(self.active_modal["text"], f_body, body_width)
        curr_y = body_clip.top
        for ln in lines:
            if not ln.strip():
                curr_y += 10
                continue
            l_surf = f_body.render(ln, True, (235, 228, 215))
            lx = body_left if is_guardian else body_left + (body_width - l_surf.get_width()) // 2
            surface.blit(l_surf, (lx, curr_y))
            curr_y += 18
        surface.set_clip(previous_clip)

        foot_txt = "Press [E], [SPACE], or [ESC] to return"
        foot_surf = f_foot.render(foot_txt, True, (180, 165, 135))
        surface.blit(foot_surf, (mx + (mw - foot_surf.get_width()) // 2, my + mh - 30))

    def _draw_guardian_portrait(self, surface: pygame.Surface, rect: pygame.Rect):
        """Draws a compact awakened Guardian portrait inside the success message."""
        reduced_motion = getattr(self, "reduced_motion", False) or getattr(settings, "reduced_motion", False)
        draw_guardian_portrait(
            surface=surface,
            rect=rect,
            anim_time=self.guardian_anim_time,
            reduced_motion=reduced_motion,
        )

    def draw_hud(self, surface: pygame.Surface, font_small=None, lantern=None, inventory=None, lives: int = 3):
        """Renders the Level 4 HUD with clean, non-overlapping multi-line layout."""
        if inventory is None and hasattr(font_small, "key_count"):
            inventory = font_small

        f_title = pygame.font.SysFont("georgia", 16, bold=True)
        f_obj = pygame.font.SysFont("consolas", 11)
        f_badge = pygame.font.SysFont("consolas", 11, bold=True)

        bar_h = 80
        bar = pygame.Surface((L4_SCREEN_WIDTH, bar_h))
        bar.fill((14, 11, 20))
        pygame.draw.line(bar, (90, 70, 45), (0, bar_h - 1), (L4_SCREEN_WIDTH, bar_h - 1), 1)
        surface.blit(bar, (0, 0))

        # Row 1 (y = 8): Level Title (Left) & Upper Navigation Shortcuts (Right)
        t_surf = f_title.render("THE ANCIENT FORGE", True, (245, 220, 145))
        surface.blit(t_surf, (20, 8))

        nav_str = "[2] Levels  |  [H] Guide  |  [P] Concepts  |  [I] Inventory  |  [J] Journal"
        n_surf = f_badge.render(nav_str, True, (175, 165, 150))
        surface.blit(n_surf, (L4_SCREEN_WIDTH - n_surf.get_width() - 20, 10))

        # Row 2 (y = 31): Conduit Status (Left) & Carried Relics (Right)
        placed_cnt = sum(1 for v in self.placed_relics.values() if v is not None)
        status_txt = f"CONDUITS: {placed_cnt}/3"
        state_surf = f_badge.render(status_txt, True, (180, 220, 195))
        surface.blit(state_surf, (20, 31))

        k_cnt = inventory.key_count if inventory else 0
        m_cnt = inventory.mirror_count if inventory else 0
        c_cnt = inventory.crystal_count if inventory else 0
        relics_str = f"Keys: {k_cnt}/3  |  Mirrors: {m_cnt}/3  |  Crystals: {c_cnt}/3"
        if inventory and getattr(inventory, "has_sigil", False):
            relics_str += "  |  Sigil: Claimed"
        r_surf = f_badge.render(relics_str, True, (220, 195, 135))
        surface.blit(r_surf, (L4_SCREEN_WIDTH - r_surf.get_width() - 20, 31))

        # Row 3 (y = 53): Lives Indicator (Left) & Dedicated Goal Box (Beside Lives)
        from engine.lives import draw_lives_hud
        draw_lives_hud(surface, 20, 53, lives=lives, max_lives=3, font=f_badge)

        # Subtle vertical separator between Lives and Goal
        pygame.draw.line(surface, (70, 55, 40), (142, 53), (142, 73), 1)

        # Goal Box: placed beside Lives area so it never crowds upper rows
        goal_prefix = "Goal: "
        g_lbl = f_badge.render(goal_prefix, True, (245, 215, 120))
        surface.blit(g_lbl, (152, 53))

        gw = f_badge.size(goal_prefix)[0]
        max_goal_w = L4_SCREEN_WIDTH - 20 - (152 + gw)
        goal_text = self.objective
        if f_obj.size(goal_text)[0] > max_goal_w:
            words = goal_text.split()
            l1, l2 = [], []
            for w in words:
                if f_obj.size(" ".join(l1 + [w]))[0] <= max_goal_w:
                    l1.append(w)
                else:
                    l2.append(w)
            o_surf1 = f_obj.render(" ".join(l1), True, (215, 205, 180))
            surface.blit(o_surf1, (152 + gw, 53))
            if l2:
                o_surf2 = f_obj.render(" ".join(l2), True, (215, 205, 180))
                surface.blit(o_surf2, (152 + gw, 65))
        else:
            o_surf = f_obj.render(goal_text, True, (215, 205, 180))
            surface.blit(o_surf, (152 + gw, 53))

        modal_open = self.has_active_modal()
        if self.toast_msg and not modal_open:
            msg_s = f_obj.render(self.toast_msg, True, (255, 235, 140))
            tw = min(720, msg_s.get_width() + 28)
            th = 26
            tx = (L4_SCREEN_WIDTH - tw) // 2
            ty = 562  # Centered at bottom of the screen
            t_box = pygame.Surface((tw, th), pygame.SRCALPHA)
            t_box.fill((16, 12, 22, 235))
            pygame.draw.rect(t_box, (195, 155, 75), (0, 0, tw, th), width=1, border_radius=5)
            surface.blit(t_box, (tx, ty))
            surface.blit(msg_s, (tx + (tw - msg_s.get_width()) // 2, ty + 6))

        if self.has_active_modal():
            self._draw_active_modal(surface)

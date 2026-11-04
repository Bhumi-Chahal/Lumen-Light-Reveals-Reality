"""content/forge_celestial_renderer.py — Procedural Celestial Forge & Magical Fire Renderer.

Visual redesign for Level 4 Ancient Forge activation:
- Circular golden structure with stepped plinths and carved rune notches
- Celestial orbital concentric rings with rotating glyph nodes
- Procedural magical celestial fire (layered glowing flame tongues)
- Floating embers with deterministic life and upward drift
- Soft ambient light radius scaling across states:
  Dormant -> Warming -> Calibrating -> Resonating -> Stabilized -> Overloaded
- Chamber illumination & harmonic stabilization celebration
"""

import math
import random
import pygame


# Color Palettes for Forge States
STATE_PALETTES = {
    "Dormant": {
        "core": (180, 120, 50),
        "flame_outer": (160, 80, 30),
        "flame_mid": (205, 140, 55),
        "flame_inner": (240, 200, 110),
        "rim": (145, 110, 55),
        "rings": (140, 105, 50),
        "glow_alpha": 45,
        "glow_radius": 34,
        "ember_count": 5,
        "flame_h": 10,
    },
    "Warming": {
        "core": (225, 140, 45),
        "flame_outer": (205, 95, 30),
        "flame_mid": (235, 165, 55),
        "flame_inner": (255, 220, 130),
        "rim": (185, 145, 65),
        "rings": (180, 135, 60),
        "glow_alpha": 85,
        "glow_radius": 46,
        "ember_count": 10,
        "flame_h": 15,
    },
    "Calibrating": {
        "core": (210, 160, 95),
        "flame_outer": (215, 105, 45),
        "flame_mid": (245, 185, 75),
        "flame_inner": (255, 235, 165),
        "rim": (215, 175, 75),
        "rings": (205, 165, 85),
        "glow_alpha": 120,
        "glow_radius": 58,
        "ember_count": 16,
        "flame_h": 20,
    },
    "Resonating": {
        "core": (245, 185, 65),
        "flame_outer": (235, 115, 40),
        "flame_mid": (255, 205, 80),
        "flame_inner": (255, 245, 195),
        "rim": (240, 200, 85),
        "rings": (235, 195, 95),
        "glow_alpha": 155,
        "glow_radius": 72,
        "ember_count": 22,
        "flame_h": 25,
    },
    "Stabilized": {
        "core": (255, 245, 180),
        "flame_outer": (245, 165, 55),
        "flame_mid": (255, 225, 105),
        "flame_inner": (255, 255, 235),
        "rim": (255, 220, 105),
        "rings": (255, 230, 125),
        "glow_alpha": 210,
        "glow_radius": 92,
        "ember_count": 32,
        "flame_h": 28,
    },
    "Overloaded": {
        "core": (215, 55, 50),
        "flame_outer": (160, 35, 30),
        "flame_mid": (210, 65, 50),
        "flame_inner": (245, 140, 110),
        "rim": (145, 60, 50),
        "rings": (165, 50, 45),
        "glow_alpha": 90,
        "glow_radius": 44,
        "ember_count": 8,
        "flame_h": 12,
    },
}


class CelestialForgeRenderer:
    """Manages the procedural rendering and internal ember particle simulation of the Celestial Forge."""

    def __init__(self):
        self.embers: list[dict] = []
        # Pre-seed internal embers for smooth ongoing animation
        for _ in range(35):
            self._spawn_ember(random.uniform(0.0, 2.5))

    def _spawn_ember(self, initial_age: float = 0.0):
        """Spawns an upward drifting ember spark within the crucible."""
        self.embers.append({
            "dx": random.uniform(-16, 16),
            "dy": random.uniform(-4, 10),
            "vx": random.uniform(-6, 6),
            "vy": random.uniform(-22, -10),
            "size": random.uniform(1.2, 2.8),
            "life": random.uniform(1.2, 2.8) - initial_age,
            "max_life": random.uniform(1.2, 2.8),
            "color_kind": random.choice(["gold", "amber", "starlight"]),
        })

    def update(self, dt: float, forge_state: str, reduced_motion: bool = False):
        """Updates internal ember particles with time-based upward drift."""
        palette = STATE_PALETTES.get(forge_state, STATE_PALETTES["Dormant"])
        max_embers = palette["ember_count"]
        if reduced_motion:
            max_embers = max(3, max_embers // 2)

        # Update living embers
        alive = []
        for e in self.embers:
            e["life"] -= dt
            if e["life"] > 0:
                e["dx"] += e["vx"] * dt
                e["dy"] += e["vy"] * dt
                alive.append(e)
        self.embers = alive

        # Trim or spawn new embers to state allowance
        if len(self.embers) > max_embers:
            self.embers = self.embers[:max_embers]
        else:
            while len(self.embers) < max_embers:
                self._spawn_ember()

    def draw(
        self,
        surface: pygame.Surface,
        altar_rect: pygame.Rect,
        crucible_rect: pygame.Rect,
        forge_state: str,
        anim_time: float,
        flicker_phase: float,
        placed_relics: dict | None = None,
        reduced_motion: bool = False,
        awakening_time: float = 0.0,
    ) -> None:
        """Draws the redesigned Celestial Forge Altar, celestial orbital rings, magical flame, and embers."""
        palette = STATE_PALETTES.get(forge_state, STATE_PALETTES["Dormant"])
        cx, cy = crucible_rect.center

        # =========================================================================
        # 1. Altar Stone Foundation
        # =========================================================================
        # Deep stone drop shadow
        shd = altar_rect.inflate(20, 20)
        pygame.draw.rect(surface, (8, 6, 12), shd, border_radius=10)

        # Main temple altar stone
        pygame.draw.rect(surface, (34, 26, 42), altar_rect, border_radius=8)
        # Ancient engraved gold perimeter trim
        pygame.draw.rect(surface, (185, 145, 65), altar_rect, width=3, border_radius=8)

        # Stepped inner plinth
        step = altar_rect.inflate(-24, -24)
        pygame.draw.rect(surface, (26, 20, 32), step, border_radius=6)
        pygame.draw.rect(surface, (105, 80, 50), step, width=1, border_radius=6)

        # Carved corner brackets in antique gold
        self._draw_altar_corners(surface, altar_rect)

        # Engraved banner text
        f_font = pygame.font.SysFont("georgia", 11, bold=True)
        lbl = f_font.render("CELESTIAL FORGE CRUCIBLE", True, (245, 220, 150))
        surface.blit(lbl, (altar_rect.centerx - lbl.get_width() // 2, altar_rect.top + 8))

        # Core status subtext
        f_sub = pygame.font.SysFont("consolas", 9, bold=True)
        st_col = palette["core"]
        st_lbl = f_sub.render(f"CORE: {forge_state.upper()}", True, st_col)
        surface.blit(st_lbl, (altar_rect.centerx - st_lbl.get_width() // 2, altar_rect.top + 22))

        # =========================================================================
        # 2. Soft Ambient Radial Light Glow Aura
        # =========================================================================
        motion_mult = 0.2 if reduced_motion else 1.0
        pulse_wave = math.sin(anim_time * 2.8 * motion_mult + flicker_phase * 0.3)
        glow_r = int(palette["glow_radius"] + 5 * pulse_wave)
        glow_a = int(max(15, min(255, palette["glow_alpha"] + 18 * pulse_wave)))

        # Create glowing radial halo surface
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        c_outer = (*palette["core"], int(glow_a * 0.4))
        c_mid = (*palette["flame_mid"], int(glow_a * 0.75))
        c_inner = (*palette["flame_inner"], glow_a)
        pygame.draw.circle(glow_surf, c_outer, (glow_r, glow_r), glow_r)
        pygame.draw.circle(glow_surf, c_mid, (glow_r, glow_r), int(glow_r * 0.65))
        pygame.draw.circle(glow_surf, c_inner, (glow_r, glow_r), int(glow_r * 0.35))
        surface.blit(glow_surf, (cx - glow_r, cy - glow_r))

        # =========================================================================
        # 3. Concentric Celestial Orbital Rings & Rotating Glyph Nodes
        # =========================================================================
        self._draw_celestial_rings(surface, cx, cy, palette, anim_time, motion_mult, forge_state)

        # =========================================================================
        # 4. Circular Golden Structure & Hearth Bowl
        # =========================================================================
        # Stepped circular golden rim
        rim_outer_r = 34
        rim_mid_r = 28
        bowl_r = 22

        # Outer carved plinth
        pygame.draw.circle(surface, (28, 22, 34), (cx, cy + 2), rim_outer_r)
        pygame.draw.circle(surface, palette["rim"], (cx, cy), rim_outer_r, width=2)

        # Middle polished gold tier with compass notches
        pygame.draw.circle(surface, (44, 34, 52), (cx, cy), rim_mid_r)
        pygame.draw.circle(surface, (215, 175, 75), (cx, cy), rim_mid_r, width=2)
        for i in range(8):
            ang = i * (math.pi / 4)
            nx1 = cx + int((rim_mid_r - 4) * math.cos(ang))
            ny1 = cy + int((rim_mid_r - 4) * math.sin(ang))
            nx2 = cx + int(rim_mid_r * math.cos(ang))
            ny2 = cy + int(rim_mid_r * math.sin(ang))
            pygame.draw.line(surface, (245, 215, 120), (nx1, ny1), (nx2, ny2), 1)

        # Deep obsidian hearth bowl
        pygame.draw.circle(surface, (14, 10, 18), (cx, cy), bowl_r)
        pygame.draw.circle(surface, (80, 60, 40), (cx, cy), bowl_r, width=1)

        # =========================================================================
        # 5. Floating Embers Rising within Crucible
        # =========================================================================
        self._draw_embers(surface, cx, cy)

        # =========================================================================
        # 6. Procedural Magical Celestial Fire
        # =========================================================================
        self._draw_celestial_fire(surface, cx, cy, palette, anim_time, motion_mult, reduced_motion)

        # =========================================================================
        # 7. Stabilized Harmonic Corona (when Solved)
        # =========================================================================
        if forge_state == "Stabilized":
            self._draw_stabilized_corona(surface, cx, cy, anim_time, awakening_time, motion_mult)

    def _draw_altar_corners(self, surface: pygame.Surface, ar: pygame.Rect):
        """Renders ornate antique gold corner brackets on the stone altar."""
        c_gold = (205, 165, 75)
        # Top-left
        pygame.draw.lines(surface, c_gold, False, [(ar.left + 5, ar.top + 16), (ar.left + 5, ar.top + 5), (ar.left + 16, ar.top + 5)], 2)
        # Top-right
        pygame.draw.lines(surface, c_gold, False, [(ar.right - 6, ar.top + 16), (ar.right - 6, ar.top + 5), (ar.right - 17, ar.top + 5)], 2)
        # Bottom-left
        pygame.draw.lines(surface, c_gold, False, [(ar.left + 5, ar.bottom - 17), (ar.left + 5, ar.bottom - 6), (ar.left + 16, ar.bottom - 6)], 2)
        # Bottom-right
        pygame.draw.lines(surface, c_gold, False, [(ar.right - 6, ar.bottom - 17), (ar.right - 6, ar.bottom - 6), (ar.right - 17, ar.bottom - 6)], 2)

    def _draw_celestial_rings(
        self,
        surface: pygame.Surface,
        cx: int,
        cy: int,
        palette: dict,
        anim_time: float,
        motion_mult: float,
        forge_state: str,
    ):
        """Draws concentric celestial orbital rings with rotating starlight nodes."""
        r_col = palette["rings"]

        # Inner celestial ring
        r1 = 44
        pygame.draw.circle(surface, r_col, (cx, cy), r1, width=1)

        # Outer celestial resonance ring
        r2 = 56
        pygame.draw.circle(surface, (*r_col[:3],), (cx, cy), r2, width=1)

        # Rotating orbital starlight nodes
        node_angle_1 = anim_time * 0.9 * motion_mult
        node_angle_2 = -anim_time * 0.6 * motion_mult

        for k in range(3):
            # Inner ring nodes (triad)
            ang1 = node_angle_1 + k * (2 * math.pi / 3)
            nx1 = cx + int(r1 * math.cos(ang1))
            ny1 = cy + int(r1 * math.sin(ang1))
            pygame.draw.circle(surface, palette["core"], (nx1, ny1), 2)

            # Outer ring nodes (counter-rotating)
            ang2 = node_angle_2 + k * (2 * math.pi / 3)
            nx2 = cx + int(r2 * math.cos(ang2))
            ny2 = cy + int(r2 * math.sin(ang2))
            pygame.draw.circle(surface, palette["flame_inner"], (nx2, ny2), 2)
            pygame.draw.circle(surface, (255, 255, 255), (nx2, ny2), 1)

        # Concentric harmonic resonance arcs
        arc_w = 2 if forge_state in ("Resonating", "Stabilized") else 1
        arc_ang = anim_time * 1.2 * motion_mult
        pygame.draw.arc(surface, palette["flame_mid"], (cx - 50, cy - 50, 100, 100), arc_ang, arc_ang + math.pi * 0.9, arc_w)
        pygame.draw.arc(surface, palette["flame_inner"], (cx - 50, cy - 50, 100, 100), arc_ang + math.pi, arc_ang + math.pi * 1.9, arc_w)

    def _draw_celestial_fire(
        self,
        surface: pygame.Surface,
        cx: int,
        cy: int,
        palette: dict,
        anim_time: float,
        motion_mult: float,
        reduced_motion: bool,
    ):
        """Draws a cosmic gravitational singularity with tilted luminous accretion disk and rising celestial fire."""
        flame_h = palette["flame_h"]
        t = anim_time * 3.2 * motion_mult

        # =====================================================================
        # 1. Rear Gravitational Lensing Arc (Bending light behind singularity)
        # =====================================================================
        lens_pulse = 0.5 + 0.5 * math.sin(t * 1.5)
        lens_rad = int(18 + 4 * lens_pulse)
        lens_rect = pygame.Rect(cx - lens_rad, cy - int(lens_rad * 0.75), lens_rad * 2, int(lens_rad * 1.5))
        pygame.draw.arc(surface, palette["flame_outer"], lens_rect, 0.2, 2.9, 2)
        pygame.draw.arc(surface, palette["flame_mid"], lens_rect.inflate(-4, -4), 0.4, 2.7, 1)

        # =====================================================================
        # 2. Celestial Flame Tongues rising from the Accretion Vortex
        # =====================================================================
        w1 = math.sin(t) * (2 if not reduced_motion else 0)
        w2 = math.cos(t * 1.4) * (2 if not reduced_motion else 0)
        w3 = math.sin(t * 2.1) * (1.5 if not reduced_motion else 0)

        # Outer flame silhouette
        pts_outer = [
            (cx - 14, cy + 6),
            (cx - 10, cy - int(flame_h * 0.55)),
            (cx - 4 + int(w1), cy - int(flame_h * 0.95)),
            (cx + int(w2), cy - int(flame_h * 1.15)),
            (cx + 4 + int(w3), cy - int(flame_h * 0.90)),
            (cx + 10, cy - int(flame_h * 0.55)),
            (cx + 14, cy + 6),
        ]
        pygame.draw.polygon(surface, palette["flame_outer"], pts_outer)

        # Mid golden flame
        pts_mid = [
            (cx - 10, cy + 5),
            (cx - 7, cy - int(flame_h * 0.45)),
            (cx - 2 + int(w2), cy - int(flame_h * 0.85)),
            (cx + int(w1), cy - int(flame_h * 1.0)),
            (cx + 3 + int(w3), cy - int(flame_h * 0.80)),
            (cx + 7, cy - int(flame_h * 0.45)),
            (cx + 10, cy + 5),
        ]
        pygame.draw.polygon(surface, palette["flame_mid"], pts_mid)

        # Inner celestial core flame
        pts_inner = [
            (cx - 6, cy + 4),
            (cx - 4, cy - int(flame_h * 0.35)),
            (cx + int(w3), cy - int(flame_h * 0.70)),
            (cx + 4, cy - int(flame_h * 0.35)),
            (cx + 6, cy + 4),
        ]
        pygame.draw.polygon(surface, palette["flame_inner"], pts_inner)

        # =====================================================================
        # 3. Gravitational Singularity Core (Cosmic Black Void Center)
        # =====================================================================
        # Deep black event horizon sphere
        singularity_r = 9
        pygame.draw.circle(surface, (6, 4, 10), (cx, cy), singularity_r)
        # Relativistic photon boundary ring
        pygame.draw.circle(surface, palette["flame_inner"], (cx, cy), singularity_r, width=1)

        # =====================================================================
        # 4. Front Tilted Accretion Disk (Crosses in front of the Event Horizon)
        # =====================================================================
        disk_w = int(32 + 6 * lens_pulse)
        disk_h = int(12 + 2 * lens_pulse)
        disk_rect = pygame.Rect(cx - disk_w // 2, cy - disk_h // 2, disk_w, disk_h)

        # Outer relativistic accretion stream
        pygame.draw.arc(surface, palette["flame_mid"], disk_rect, 3.2, 6.2, 2)
        # Inner white-hot accretion belt
        pygame.draw.arc(surface, (255, 255, 240), disk_rect.inflate(-4, -4), 3.4, 6.0, 2)

        # Orbiting cosmic starlight photons around the accretion disk
        for idx in range(3):
            ang = t * 1.8 + idx * (math.pi * 2.0 / 3.0)
            orb_x = cx + int((disk_w // 2 - 2) * math.cos(ang))
            orb_y = cy + int((disk_h // 2 - 1) * math.sin(ang))
            pygame.draw.circle(surface, (255, 255, 255), (orb_x, orb_y), 2)
            pygame.draw.circle(surface, palette["flame_inner"], (orb_x, orb_y), 3, width=1)

        # =====================================================================
        # 5. Brilliant White Heart Spark (Preserved at cx, cy - 2 for test contract)
        # =====================================================================
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy - 2), max(2, int(flame_h * 0.15)))

    def _draw_embers(self, surface: pygame.Surface, cx: int, cy: int):
        """Draws floating embers rising upward within the crucible structure."""
        for e in self.embers:
            ex = int(cx + e["dx"])
            ey = int(cy + e["dy"])
            ratio = max(0.0, min(1.0, e["life"] / e["max_life"]))
            alpha = int(220 * ratio)

            if e["color_kind"] == "starlight":
                col = (255, 255, 255)
            elif e["color_kind"] == "gold":
                col = (255, 215, 80)
            else:
                col = (245, 130, 45)

            sz = max(1, int(e["size"] * ratio + 0.5))
            e_surf = pygame.Surface((sz * 2 + 2, sz * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(e_surf, (*col, alpha), (sz + 1, sz + 1), sz)
            surface.blit(e_surf, (ex - sz - 1, ey - sz - 1))

    def _draw_stabilized_corona(
        self,
        surface: pygame.Surface,
        cx: int,
        cy: int,
        anim_time: float,
        awakening_time: float,
        motion_mult: float,
    ):
        """Renders radiant celestial starlight rays and harmonic corona upon stabilization."""
        # Radiant 8-point starlight rays emanating from core
        star_pulse = math.sin(anim_time * 3.5 * motion_mult)
        star_len = int(32 + 6 * star_pulse)
        c_star = (255, 245, 200)

        for ang_deg in (0, 45, 90, 135, 180, 225, 270, 315):
            rad = math.radians(ang_deg + anim_time * 15.0 * motion_mult)
            x1 = cx + int(14 * math.cos(rad))
            y1 = cy + int(14 * math.sin(rad))
            x2 = cx + int(star_len * math.cos(rad))
            y2 = cy + int(star_len * math.sin(rad))
            pygame.draw.line(surface, c_star, (x1, y1), (x2, y2), 1)

        # Concentric golden-emerald harmony rings
        wave_rad = int(38 + 12 * ((anim_time * 0.8) % 1.0))
        wave_a = int(140 * (1.0 - ((anim_time * 0.8) % 1.0)))
        w_surf = pygame.Surface((wave_rad * 2 + 4, wave_rad * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(w_surf, (160, 245, 200, wave_a), (wave_rad + 2, wave_rad + 2), wave_rad, width=2)
        surface.blit(w_surf, (cx - wave_rad - 2, cy - wave_rad - 2))


def get_forge_lighting_radius(forge_state: str, anim_time: float = 0.0) -> int:
    """Calculates ambient illumination radius for darkness mask based on Forge state."""
    base_radii = {
        "Dormant": 120,
        "Warming": 150,
        "Calibrating": 180,
        "Resonating": 215,
        "Stabilized": 390,  # Illuminates the chamber
        "Overloaded": 125,
    }
    base_r = base_radii.get(forge_state, 140)
    pulse = int(5 * math.sin(anim_time * 2.5))
    return base_r + pulse

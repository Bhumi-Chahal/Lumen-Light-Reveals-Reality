"""systems/concepts_ui.py — Educational CG/IP Concepts Panel for Lumen.

Explains the academic Computer Graphics and Digital Image Processing techniques
demonstrated in each level. Keeps educational concepts separate from puzzle clues
and controls (Explorer's Guide).
"""

from typing import Any
import pygame
from systems.ui import wrap_text
from systems.audio import audio


# Verified educational content per level.
# Only concepts genuinely implemented and observable in the codebase are included.
LEVEL_CONCEPTS: dict[str, list[dict[str, str]]] = {
    "level1": [
        {
            "id": "vis_alpha",
            "name": "Dynamic Visibility & Alpha Blending",
            "category": "Computer Graphics",
            "explanation": "Subterranean darkness is rendered as an alpha-blended surface mask, while the lantern punches out a smooth, warm circle of vision through transparency attenuation.",
            "appears": "The radiant circle of light following the explorer through the pitch-black sanctum, illuminating nearby walls and floor flagstones.",
            "technical": "Multi-pass destination alpha attenuation with cubic hermite interpolation: A(t) = t² · (3 - 2t), producing soft-edge light falloff without hard pixel stepping.",
        },
        {
            "id": "aabb_collision",
            "name": "Deterministic AABB Collision Detection",
            "category": "Computer Graphics",
            "explanation": "Solid walls, pillars, and pedestals prevent the explorer from penetrating geometry by testing bounding box overlaps on each spatial axis independently.",
            "appears": "The explorer sliding smoothly along ancient stone walls, statues, and pedestals without getting stuck or clipping through solid masonry.",
            "technical": "Dual-axis Axis-Aligned Bounding Box (AABB) overlap testing: Δx < (w₁ + w₂)/2 and Δy < (h₁ + h₂)/2, resolving X and Y independently to allow wall-sliding.",
        },
        {
            "id": "sprite_shading",
            "name": "2D Sprite Animation & Layered Shading",
            "category": "Computer Graphics",
            "explanation": "The explorer and temple chamber are composed of multi-layered 2D procedural pixel-art elements, animated walk cycles, and translucent drop shadows.",
            "appears": "The wizard explorer's 4-directional walking motion, flowing robes, and the elliptical drop shadow cast onto the ancient stone floor tiles.",
            "technical": "Multi-frame procedural sprite animation with sine-driven bobbing offset and alpha-blended elliptical drop shadow (RGBA = (10, 8, 16, 120)).",
        },
        {
            "id": "camera_transform",
            "name": "Camera Viewport & Coordinate Transform",
            "category": "Computer Graphics",
            "explanation": "Expansive chamber world coordinates are translated into visible screen coordinates, keeping the camera centered on the explorer within room boundaries.",
            "appears": "Smooth viewport scrolling as the explorer traverses the sanctum, seamlessly stopping at the ancient chamber's outer stone boundaries.",
            "technical": "2D affine translation transformation: P_screen = P_world - C_offset, with camera bounds clamped to [0, WorldSize - ViewportSize].",
        },
    ],
    "level2": [
        {
            "id": "chromatic_filtering",
            "name": "Chromatic Filtering & Spectral Revelation",
            "category": "Computer Graphics",
            "explanation": "Different light wavelengths reveal distinct hidden geometry. Environmental objects react and manifest only when illuminated by matching light frequencies.",
            "appears": "Ancient inscriptions, concealed doorways, and hidden structures emerging from darkness when bathed in specific lantern colors.",
            "technical": "Spectral channel isolation: C_visible = C_object · δ(λ_light, λ_target), where visibility and interaction collision are conditionally enabled by matching color modes.",
        },
        {
            "id": "wavelength_lighting",
            "name": "Dynamic Darkness Masking & Wavelength Tinting",
            "category": "Computer Graphics",
            "explanation": "The darkness mask modulates both transparency and RGB color hue based on the lantern's active color mode, casting colored ambient halos.",
            "appears": "The lantern's illumination halo shifting between radiant white, crimson red, emerald green, and sapphire blue, tinting the surrounding environment.",
            "technical": "Multi-pass alpha blending with wavelength tinting: I_out = α · I_light + (1 - α) · I_ambient, blending point-light radiance with deep ambient shadows.",
        },
        {
            "id": "collision_gating",
            "name": "Dynamic Collision Swapping & State Gating",
            "category": "Computer Graphics",
            "explanation": "Physical collision boundaries adapt dynamically at runtime when hidden environmental features are illuminated and activated.",
            "appears": "Deep chasm voids becoming traversable solid ground, or impassable barriers yielding passage when illuminated by the correct light wavelength.",
            "technical": "Dynamic AABB collision state switching: conditional insertion and removal of bounding boxes from the active spatial collision list at runtime.",
        },
        {
            "id": "energy_decay",
            "name": "Finite Energy Attenuation & Battery Simulation",
            "category": "Game Engine Systems",
            "explanation": "The lantern's magical energy depletes continuously over time while lit, requiring the player to recharge at resonance crystal stations.",
            "appears": "The HUD lantern power meter steadily draining as light is emitted, with warnings before darkness envelops the chamber.",
            "technical": "Rate-based energy decay model: E(t + Δt) = max(0, E(t) - r_drain · Δt), replenished instantaneously or incrementally at energy crystal stations.",
        },
    ],
    "level3": [
        {
            "id": "reflection_law",
            "name": "Law of Reflection & Normal Vectors",
            "category": "Physics & Optics",
            "explanation": "Light reflects off smooth planar surfaces such that the angle of incidence equals the angle of reflection relative to the surface normal.",
            "appears": "Rotating ancient mirrors in stone sockets redirects incoming light beams across the chamber to strike distant targets.",
            "technical": "Vector reflection formula: r = d - 2 · (d · n) · n, where d is the incoming beam direction and n is the mirror surface unit normal vector.",
        },
        {
            "id": "ray_intersection",
            "name": "Raycasting & Analytical Ray-Box Intersection",
            "category": "Computer Graphics",
            "explanation": "Light beams travel through space until they intersect walls, mirrors, or receivers, splitting into piecewise continuous segments.",
            "appears": "Continuous colored light beams propagating across the temple halls, stopping cleanly at stone obstacles and reflective surfaces.",
            "technical": "Ray-AABB slab intersection method: t_min = max(min(t_x1, t_x2), min(t_y1, t_y2)), constructing discrete piecewise BeamSegment chains.",
        },
        {
            "id": "dip_grayscale",
            "name": "DIP Stage 1: Grayscale Luminance Conversion",
            "category": "Digital Image Processing",
            "explanation": "Converts color fresco pixels into pure brightness values, removing chromatic noise while preserving perceptual human brightness.",
            "appears": "Stage 1 of the Faded Mural / Ancient Glyph Scanner in Chamber 1.",
            "technical": "Standard ITU-R BT.601 photometric weighting formula: Y = 0.299 · R + 0.587 · G + 0.114 · B.",
        },
        {
            "id": "dip_contrast",
            "name": "DIP Stage 2: Linear Contrast Stretching",
            "category": "Digital Image Processing",
            "explanation": "Expands the faded mural's narrow gray range across the full brightness spectrum to amplify faint inscriptions.",
            "appears": "Stage 2 of the Faded Mural / Ancient Glyph Scanner, making weathered glyph lines stand out against porous stone.",
            "technical": "Linear histogram normalization: s = round((v - v_min) · 255 / (v_max - v_min)), mapping subtle gray levels to [0, 255].",
        },
        {
            "id": "dip_threshold",
            "name": "DIP Stage 3: Binary Threshold Segmentation",
            "category": "Digital Image Processing",
            "explanation": "Classifies each pixel as either foreground ink or background stone based on a numerical cutoff value.",
            "appears": "Stage 3 of the Faded Mural / Ancient Glyph Scanner, turning faint gray sketches into crisp black-and-white runes.",
            "technical": "Step threshold function: g(x, y) = 255 if f(x, y) ≥ 128, else 0, segmenting ink from limestone.",
        },
        {
            "id": "dip_sobel",
            "name": "DIP Stage 4: Sobel Spatial Edge Detection",
            "category": "Digital Image Processing",
            "explanation": "Convolves the image with horizontal and vertical gradient kernels to detect rapid changes in intensity and extract rune outlines.",
            "appears": "Stage 4 of the Faded Mural / Ancient Glyph Scanner, outlining the sharp boundaries of ancient symbols.",
            "technical": "2D spatial convolution with 3x3 kernels Kx and Ky, computing gradient magnitude |G| = √(Gx² + Gy²).",
        },
    ],
    "level4": [
        {
            "id": "cg_polygon_triangulation",
            "name": "Polygon Reconstruction & Triangulation",
            "category": "Computer Graphics",
            "explanation": "Triangulation divides any complex polygon shape into simple triangles that graphics hardware can easily fill and render.",
            "appears": "Broken Relic station on the western wall of the Ancient Forge.",
            "technical": "Ear-clipping triangulation decomposes an n-vertex simple polygon into n-2 triangles: T = {t_i}.",
        },
        {
            "id": "cg_rotation_2d",
            "name": "2D Geometric Rotation Transformations",
            "category": "Computer Graphics",
            "explanation": "Rotates points and sprites around a central origin by an angle using trigonometric sine and cosine functions.",
            "appears": "Broken Relic station when rotating polygon shards into proper alignment.",
            "technical": "2D affine rotation matrix: [x', y'] = [x·cos(θ) - y·sin(θ), x·sin(θ) + y·cos(θ)].",
        },
        {
            "id": "cg_texture_mapping",
            "name": "Texture Mapping & UV Coordinates",
            "category": "Computer Graphics",
            "explanation": "Maps a 2D image or pattern onto geometric surfaces using normalized coordinates ranging from (0, 0) to (1, 1).",
            "appears": "Ancient Blueprint station on the southern wall of the Ancient Forge.",
            "technical": "Parametric UV surface mapping: samples (u, v) ∈ [0, 1] texture coordinates and maps transformed subregions onto polygonal quad surfaces.",
        },
        {
            "id": "ip_median_filter",
            "name": "3×3 Median Filter Noise Reduction",
            "category": "Digital Image Processing",
            "explanation": "Removes pepper-like noise from an image by sorting each pixel's 3×3 neighborhood and choosing the middle value, keeping edges sharp.",
            "appears": "Memory Fragments station on the eastern wall of the Ancient Forge.",
            "technical": "Non-linear spatial filter sorting a 3×3 sliding window: I_out(x, y) = median({I(x+i, y+j)}), effectively eliminating impulse salt-and-pepper noise while preserving sharp boundary edges.",
        },
        {
            "id": "cg_counting_principle",
            "name": "Fundamental Counting Principle",
            "category": "Mathematics",
            "explanation": "When making independent choices, multiply the options together: 3 keys × 3 mirrors × 3 crystals = 27 total combinations.",
            "appears": "Ancient Rule tablet on the northern wall of the Ancient Forge.",
            "technical": "Product rule for independent choice sets: |S₁ × S₂ × S₃| = |S₁| · |S₂| · |S₃| = 3 · 3 · 3 = 27 total combinations.",
        },
        {
            "id": "cg_particle_system",
            "name": "Particle Systems & Kinematic Simulation",
            "category": "Computer Graphics",
            "explanation": "Animates hundreds of individual glowing embers or celebration sparks, each updating its position, speed, and fade over time.",
            "appears": "Volcanic crucible fire and celebratory burst when the Forge awakens.",
            "technical": "Kinematic numerical integration: p(t+Δt) = p(t) + v(t)·Δt, with alpha transparency attenuating linearly with remaining life fraction α(t) = α₀ · (life / max_life).",
        },
        {
            "id": "cg_dynamic_lighting_l4",
            "name": "Dynamic Lighting & Alpha Blending",
            "category": "Computer Graphics",
            "explanation": "Casts circular fields of light that smoothly fade into shadows by blending semi-transparent pixels over the chamber scene.",
            "appears": "Lantern light cones, glowing relic socket pedestals, and smooth ambient darkness.",
            "technical": "Quadratic distance attenuation I(d) = I_0 / (1 + c·d²) composited via Porter-Duff alpha blending: C = α·C_src + (1-α)·C_dst.",
        },
    ],
}

LEVEL_TITLES: dict[str, str] = {
    "level1": "LEVEL 1 — THE AWAKENING",
    "level2": "LEVEL 2 — THE DEEPENING DARK",
    "level3": "LEVEL 3 — THE PATH OF LIGHT",
    "level4": "LEVEL 4 — THE ANCIENT FORGE",
}

LEVEL_KEYS = ["level1", "level2", "level3", "level4"]


class ConceptsModal:
    """Temple-themed CG & IP Concepts Panel for Lumen."""

    def __init__(self, screen_width: int = 800, screen_height: int = 600):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_open: bool = False
        self.active_level: str = "level1"
        self.selected_index: int = 0
        self.list_scroll: int = 0
        self.pulse: float = 0.0

        # Modal Dimensions (800x600 resolution)
        self.box_w = 740
        self.box_h = 520
        self.box_x = (self.screen_width - self.box_w) // 2
        self.box_y = (self.screen_height - self.box_h) // 2

        # Fonts
        self.font_title = pygame.font.SysFont("georgia", 18, bold=True)
        self.font_subtitle = pygame.font.SysFont("consolas", 11)
        self.font_tab = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_section = pygame.font.SysFont("consolas", 11, bold=True)
        self.font_name = pygame.font.SysFont("georgia", 15, bold=True)
        self.font_badge = pygame.font.SysFont("consolas", 10, bold=True)
        self.font_body = pygame.font.SysFont("consolas", 12)
        self.font_code = pygame.font.SysFont("consolas", 11)
        self.font_footer = pygame.font.SysFont("consolas", 11, bold=True)

        # Interactive bounds
        self.tab_rects: dict[str, pygame.Rect] = {}
        self.item_rects: list[pygame.Rect] = []
        self.close_btn_rect = pygame.Rect(self.box_x + self.box_w - 120, self.box_y + self.box_h - 38, 100, 28)

    def open(self, level_id: str = "level1"):
        """Opens the concepts panel for the specified level."""
        if level_id in LEVEL_CONCEPTS:
            self.active_level = level_id
        else:
            self.active_level = "level1"
        self.selected_index = 0
        self.list_scroll = 0
        self.is_open = True
        audio.play("clue")

    def close(self):
        """Closes the concepts panel."""
        self.is_open = False
        audio.play("clue")

    def toggle(self, level_id: str | None = None):
        """Toggles modal visibility."""
        if self.is_open:
            self.close()
        else:
            self.open(level_id or "level1")

    def set_level(self, level_id: str):
        """Switches active level concepts tab."""
        if level_id in LEVEL_CONCEPTS and level_id != self.active_level:
            self.active_level = level_id
            self.selected_index = 0
            self.list_scroll = 0
            audio.play("clue")

    def prev_concept(self):
        """Navigates to previous concept."""
        concepts = self.get_current_concepts()
        if concepts:
            self.selected_index = (self.selected_index - 1) % len(concepts)
            self._ensure_selected_visible()
            audio.play("footstep")

    def next_concept(self):
        """Navigates to next concept."""
        concepts = self.get_current_concepts()
        if concepts:
            self.selected_index = (self.selected_index + 1) % len(concepts)
            self._ensure_selected_visible()
            audio.play("footstep")

    def _list_geometry(self) -> tuple[int, int, int, int, int]:
        """Returns the left concept-list viewport and card spacing."""
        sep_y = self.box_y + 60
        col1_y = sep_y + 12
        card_start_y = col1_y + 24
        foot_y = self.box_y + self.box_h - 40
        return card_start_y, foot_y - 12, 56, 6, card_start_y

    def _max_list_scroll(self) -> int:
        """Returns the maximum vertical offset needed to fit the concept cards."""
        _, viewport_bottom, card_h, card_gap, card_start_y = self._list_geometry()
        content_h = max(0, len(self.get_current_concepts()) * (card_h + card_gap) - card_gap)
        return max(0, content_h - (viewport_bottom - card_start_y))

    def _ensure_selected_visible(self) -> None:
        """Keeps the selected card inside the left-list viewport."""
        viewport_top, viewport_bottom, card_h, card_gap, card_start_y = self._list_geometry()
        card_top = card_start_y + self.selected_index * (card_h + card_gap) - self.list_scroll
        card_bottom = card_top + card_h
        if card_top < viewport_top:
            self.list_scroll -= viewport_top - card_top
        elif card_bottom > viewport_bottom:
            self.list_scroll += card_bottom - viewport_bottom
        self.list_scroll = max(0, min(self.list_scroll, self._max_list_scroll()))

    def get_current_concepts(self) -> list[dict[str, str]]:
        """Returns the concepts list for the active level."""
        return LEVEL_CONCEPTS.get(self.active_level, [])

    def get_selected_concept(self) -> dict[str, str] | None:
        """Returns the currently selected concept dictionary."""
        concepts = self.get_current_concepts()
        if concepts and 0 <= self.selected_index < len(concepts):
            return concepts[self.selected_index]
        return None

    def update(self, dt: float):
        """Updates animation pulse."""
        self.pulse = (self.pulse + dt * 3.0) % (2.0 * 3.14159)

    def handle_input(self, event: pygame.event.Event, game_pos: tuple[int, int] | None = None) -> bool:
        """Handles keyboard and mouse events when panel is open. Returns True if handled."""
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_p, pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
                self.close()
                return True
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                idx = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}[event.key]
                self.set_level(LEVEL_KEYS[idx])
                return True
            elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT):
                self.prev_concept()
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT):
                self.next_concept()
                return True
            elif event.key == pygame.K_TAB:
                # Cycle level tabs
                cur_idx = LEVEL_KEYS.index(self.active_level)
                next_lvl = LEVEL_KEYS[(cur_idx + 1) % len(LEVEL_KEYS)]
                self.set_level(next_lvl)
                return True
            return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = game_pos if game_pos is not None else event.pos

            # Close button
            if self.close_btn_rect.collidepoint(mx, my):
                self.close()
                return True

            # Level tabs
            for lvl_id, r in self.tab_rects.items():
                if r.collidepoint(mx, my):
                    self.set_level(lvl_id)
                    return True

            # Concept item selection
            for i, r in enumerate(self.item_rects):
                if r.collidepoint(mx, my):
                    if i != self.selected_index:
                        self.selected_index = i
                        audio.play("clue")
                    return True

            # Click outside modal closes it
            modal_rect = pygame.Rect(self.box_x, self.box_y, self.box_w, self.box_h)
            if not modal_rect.collidepoint(mx, my):
                self.close()
                return True
            return True

        elif event.type == pygame.MOUSEWHEEL:
            mx, my = game_pos if game_pos is not None else pygame.mouse.get_pos()
            viewport_top, viewport_bottom, _, _, _ = self._list_geometry()
            list_rect = pygame.Rect(self.box_x + 20, viewport_top, 230, viewport_bottom - viewport_top)
            if list_rect.collidepoint(mx, my):
                self.list_scroll -= event.y * 24
                self.list_scroll = max(0, min(self.list_scroll, self._max_list_scroll()))
            elif event.y > 0:
                self.prev_concept()
            elif event.y < 0:
                self.next_concept()
            return True

        return True

    def draw(self, surface: pygame.Surface, game_pos: tuple[int, int] | None = None):
        """Renders the educational concepts panel tablet overlay."""
        if not self.is_open:
            return

        mx, my = game_pos if game_pos is not None else pygame.mouse.get_pos()

        # 1. Background dim
        dim = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim.fill((8, 6, 14, 215))
        surface.blit(dim, (0, 0))

        # 2. Main Stone Tablet
        tablet = pygame.Surface((self.box_w, self.box_h), pygame.SRCALPHA)
        tablet.fill((20, 17, 28, 248))
        pygame.draw.rect(tablet, (185, 155, 75), (0, 0, self.box_w, self.box_h), width=2, border_radius=8)
        pygame.draw.rect(tablet, (75, 62, 38), (4, 4, self.box_w - 8, self.box_h - 8), width=1, border_radius=6)

        # Ornate Corner Accents
        for cx, cy in [(6, 6), (self.box_w - 10, 6), (6, self.box_h - 10), (self.box_w - 10, self.box_h - 10)]:
            pygame.draw.rect(tablet, (220, 185, 80), (cx, cy, 4, 4))
        surface.blit(tablet, (self.box_x, self.box_y))

        # 3. Header Title & Subtitle
        title_str = "CG & IP CONCEPTS"
        sub_str = f"Academic Foundations — {LEVEL_TITLES.get(self.active_level, 'LUMEN')}"
        t_surf = self.font_title.render(title_str, True, (248, 224, 148))
        s_surf = self.font_subtitle.render(sub_str, True, (185, 175, 155))
        surface.blit(t_surf, (self.box_x + 24, self.box_y + 16))
        surface.blit(s_surf, (self.box_x + 24, self.box_y + 40))

        # 4. Level Tabs (top-right)
        self.tab_rects.clear()
        tab_names = [
            ("level1", "[1] L1"),
            ("level2", "[2] L2"),
            ("level3", "[3] L3"),
            ("level4", "[4] L4"),
        ]
        tab_w = 76
        tab_h = 28
        tab_gap = 6
        total_tab_w = len(tab_names) * tab_w + (len(tab_names) - 1) * tab_gap
        tab_start_x = self.box_x + self.box_w - total_tab_w - 24
        tab_y = self.box_y + 20

        for idx, (lvl_id, label) in enumerate(tab_names):
            tx = tab_start_x + idx * (tab_w + tab_gap)
            tr = pygame.Rect(tx, tab_y, tab_w, tab_h)
            self.tab_rects[lvl_id] = tr
            is_active = (lvl_id == self.active_level)
            is_hover = tr.collidepoint(mx, my)

            tsurf = pygame.Surface((tab_w, tab_h), pygame.SRCALPHA)
            if is_active:
                tsurf.fill((50, 40, 24, 230))
                pygame.draw.rect(tsurf, (245, 215, 110), (0, 0, tab_w, tab_h), width=2, border_radius=5)
                text_col = (255, 240, 190)
            elif is_hover:
                tsurf.fill((34, 28, 44, 210))
                pygame.draw.rect(tsurf, (180, 150, 80), (0, 0, tab_w, tab_h), width=1, border_radius=5)
                text_col = (230, 220, 200)
            else:
                tsurf.fill((16, 13, 22, 180))
                pygame.draw.rect(tsurf, (70, 58, 40), (0, 0, tab_w, tab_h), width=1, border_radius=5)
                text_col = (160, 150, 140)

            lbl = self.font_tab.render(label, True, text_col)
            tsurf.blit(lbl, ((tab_w - lbl.get_width()) // 2, (tab_h - lbl.get_height()) // 2))
            surface.blit(tsurf, (tx, tab_y))

        # Horizontal separator
        sep_y = self.box_y + 60
        pygame.draw.line(surface, (140, 110, 50), (self.box_x + 20, sep_y), (self.box_x + self.box_w - 20, sep_y), 1)
        pygame.draw.circle(surface, (220, 185, 80), (self.box_x + self.box_w // 2, sep_y), 3)

        # 5. Left Column: Concept List
        col1_x = self.box_x + 20
        col1_w = 230
        col1_y = sep_y + 12
        col1_h = self.box_h - 120

        list_hdr = self.font_section.render("CONCEPTS IN THIS LEVEL", True, (210, 190, 140))
        surface.blit(list_hdr, (col1_x + 6, col1_y))

        concepts = self.get_current_concepts()
        self.item_rects.clear()
        card_h = 56
        card_gap = 6
        viewport_top, viewport_bottom, _, _, card_start_y = self._list_geometry()
        self.list_scroll = max(0, min(self.list_scroll, self._max_list_scroll()))
        list_clip = pygame.Rect(col1_x, viewport_top, col1_w, viewport_bottom - viewport_top)
        old_clip = surface.get_clip()
        surface.set_clip(old_clip.clip(list_clip))

        for i, c in enumerate(concepts):
            cy = card_start_y + i * (card_h + card_gap) - self.list_scroll
            full_rect = pygame.Rect(col1_x, cy, col1_w, card_h)
            cr = full_rect.clip(list_clip)
            self.item_rects.append(cr)
            is_sel = (i == self.selected_index)
            is_hov = full_rect.collidepoint(mx, my) and list_clip.collidepoint(mx, my)

            csurf = pygame.Surface((col1_w, card_h), pygame.SRCALPHA)
            if is_sel:
                csurf.fill((44, 36, 56, 240))
                pygame.draw.rect(csurf, (245, 215, 110), (0, 0, col1_w, card_h), width=2, border_radius=6)
                pygame.draw.rect(csurf, (245, 215, 110), (0, 0, 4, card_h), border_radius=2)
                tcol = (255, 245, 215)
                bcol = (240, 205, 120)
            elif is_hov:
                csurf.fill((30, 25, 40, 200))
                pygame.draw.rect(csurf, (165, 135, 75), (0, 0, col1_w, card_h), width=1, border_radius=6)
                tcol = (230, 220, 200)
                bcol = (180, 165, 135)
            else:
                csurf.fill((16, 13, 22, 160))
                pygame.draw.rect(csurf, (55, 45, 60), (0, 0, col1_w, card_h), width=1, border_radius=6)
                tcol = (190, 180, 170)
                bcol = (140, 130, 120)

            # Badge category
            badge = self.font_badge.render(c["category"].upper(), True, bcol)
            csurf.blit(badge, (12, 8))

            # Truncated or wrapped concept name
            name_lines = wrap_text(f"{i + 1}. {c['name']}", self.font_tab, col1_w - 24)
            for nl_idx, nl in enumerate(name_lines[:2]):
                nl_surf = self.font_tab.render(nl, True, tcol)
                csurf.blit(nl_surf, (12, 22 + nl_idx * 14))

            surface.blit(csurf, (col1_x, cy))

        surface.set_clip(old_clip)

        if self._max_list_scroll() > 0:
            track = pygame.Rect(col1_x + col1_w + 3, viewport_top, 6, viewport_bottom - viewport_top)
            pygame.draw.rect(surface, (35, 29, 42), track, border_radius=3)
            content_h = len(concepts) * (card_h + card_gap) - card_gap
            thumb_h = max(24, int(track.height * (track.height / content_h)))
            thumb_y = track.top + int(
                (track.height - thumb_h) * (self.list_scroll / self._max_list_scroll())
            )
            pygame.draw.rect(surface, (175, 140, 70), (track.left, thumb_y, track.width, thumb_h), border_radius=3)

        # Vertical Divider between columns
        div_x = col1_x + col1_w + 14
        pygame.draw.line(surface, (75, 62, 40), (div_x, sep_y + 10), (div_x, self.box_y + self.box_h - 48), 1)

        # 6. Right Column: Detailed View of Selected Concept
        col2_x = div_x + 14
        col2_w = self.box_w - (col2_x - self.box_x) - 20
        cur_concept = self.get_selected_concept()

        if cur_concept:
            # Concept Header Card
            head_h = 48
            h_box = pygame.Surface((col2_w, head_h), pygame.SRCALPHA)
            h_box.fill((25, 20, 34, 220))
            pygame.draw.rect(h_box, (140, 115, 65), (0, 0, col2_w, head_h), width=1, border_radius=6)

            c_name_surf = self.font_name.render(cur_concept["name"], True, (255, 235, 165))
            c_cat_surf = self.font_badge.render(f"[{cur_concept['category'].upper()}]", True, (130, 210, 255))
            h_box.blit(c_cat_surf, (14, 7))
            h_box.blit(c_name_surf, (14, 22))
            surface.blit(h_box, (col2_x, sep_y + 12))

            content_y = sep_y + 12 + head_h + 10

            # Section A: Explanation (Simple English)
            lbl_a = self.font_section.render("CONCEPT OVERVIEW & SCIENTIFIC PRINCIPLE", True, (215, 195, 135))
            surface.blit(lbl_a, (col2_x + 4, content_y))
            content_y += 18

            exp_lines = wrap_text(cur_concept["explanation"], self.font_body, col2_w - 16)
            for el in exp_lines:
                e_surf = self.font_body.render(el, True, (240, 235, 225))
                surface.blit(e_surf, (col2_x + 10, content_y))
                content_y += 18

            content_y += 8

            # Section B: Where It Appears in This Level
            lbl_b = self.font_section.render("OBSERVED IN THIS LEVEL", True, (215, 195, 135))
            surface.blit(lbl_b, (col2_x + 4, content_y))
            content_y += 18

            app_lines = wrap_text(cur_concept["appears"], self.font_body, col2_w - 32)
            box_b_h = max(42, len(app_lines) * 18 + 14)
            b_box = pygame.Surface((col2_w, box_b_h), pygame.SRCALPHA)
            b_box.fill((14, 12, 20, 200))
            pygame.draw.rect(b_box, (65, 55, 45), (0, 0, col2_w, box_b_h), width=1, border_radius=5)
            for al_idx, al in enumerate(app_lines):
                a_surf = self.font_body.render(al, True, (220, 230, 215))
                b_box.blit(a_surf, (12, 7 + al_idx * 18))
            surface.blit(b_box, (col2_x, content_y))
            content_y += box_b_h + 10

            # Section C: Technical Detail & Mathematical Formulation
            lbl_c = self.font_section.render("TECHNICAL FORMULATION & ALGORITHM", True, (215, 195, 135))
            surface.blit(lbl_c, (col2_x + 4, content_y))
            content_y += 18

            tech_lines = wrap_text(cur_concept["technical"], self.font_code, col2_w - 32)
            box_c_h = max(46, len(tech_lines) * 17 + 14)
            c_box = pygame.Surface((col2_w, box_c_h), pygame.SRCALPHA)
            c_box.fill((12, 16, 24, 220))
            pygame.draw.rect(c_box, (60, 95, 115), (0, 0, col2_w, box_c_h), width=1, border_radius=5)
            for tl_idx, tl in enumerate(tech_lines):
                t_surf = self.font_code.render(tl, True, (190, 225, 235))
                c_box.blit(t_surf, (12, 7 + tl_idx * 17))
            surface.blit(c_box, (col2_x, content_y))

        # 7. Bottom Footer Controls & Close Button
        foot_y = self.box_y + self.box_h - 40
        pygame.draw.line(surface, (80, 65, 40), (self.box_x + 20, foot_y - 6), (self.box_x + self.box_w - 20, foot_y - 6), 1)

        f_txt = "[↑/↓] Select Concept   |   [1/2/3] Level   |   [ESC] / [P] Close   |   Gameplay Paused"
        f_surf = self.font_footer.render(f_txt, True, (175, 165, 145))
        surface.blit(f_surf, (self.box_x + 24, foot_y + 4))

        # Close button (bottom right)
        c_hov = self.close_btn_rect.collidepoint(mx, my)
        c_surf = pygame.Surface((self.close_btn_rect.width, self.close_btn_rect.height), pygame.SRCALPHA)
        c_bg = (45, 35, 55, 240) if c_hov else (24, 20, 32, 210)
        c_bor = (255, 220, 110) if c_hov else (150, 120, 60)
        pygame.draw.rect(c_surf, c_bg, (0, 0, self.close_btn_rect.width, self.close_btn_rect.height), border_radius=5)
        pygame.draw.rect(c_surf, c_bor, (0, 0, self.close_btn_rect.width, self.close_btn_rect.height), width=1, border_radius=5)
        btn_lbl = self.font_tab.render("[ESC] Close", True, (255, 240, 190) if c_hov else (210, 200, 185))
        c_surf.blit(btn_lbl, ((self.close_btn_rect.width - btn_lbl.get_width()) // 2, (self.close_btn_rect.height - btn_lbl.get_height()) // 2))
        surface.blit(c_surf, (self.close_btn_rect.x, self.close_btn_rect.y))

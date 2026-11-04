"""content/level4_puzzles.py — Four Mini-Puzzle Stations & Forge Clue System for Level 4.

Implements the four-direction puzzle system surrounding the central Ancient Forge:
1. LEFT STATION: Broken Relic
   - Geometric polygon reconstruction with 2D transformations (rotation, translation).
   - Real polygon triangulation (ear-clipping decomposition into triangles).
   - Reveals: "The Bronze Key, Red Mirror and First Crystal never opened the Forge."
   - Eliminates: Bronze + Red + Crystal 1.

2. RIGHT STATION: Memory Fragments
   - Real impulse (salt-and-pepper) noise reduction.
   - Real 3x3 Median Filtering on pixel data (sorting 9 neighbors, selecting median).
   - Comparative filters: Box Blur (averaging) and Linear Contrast.
   - Reveals: "The Bronze Key, Blue Mirror and Third Crystal cannot work together."
   - Eliminates: Bronze + Blue + Crystal 3.

3. BOTTOM STATION: Ancient Blueprint
   - Texture mapping engine mapping 2D pattern/texture coordinates (UV) onto surface quads.
   - Geometric transformations (rotation, scaling) and snapping.
   - Reveals: "The Gold Key, Red Mirror and Second Crystal lead nowhere."
   - Eliminates: Gold + Red + Crystal 2.

4. TOP STATION: The Ancient Rule
   - Monumental tablet with three numbered paths.
   - Guide: "The key and crystal must share the same rank. The second path shines blue; the third shines green."
   - Combinatorics: 3 × 3 × 3 = 27 combinations.

5. FORGE ENTRANCE POPUP:
   - Explains 27 combinations and 2 awakening combinations on first approach.
"""

from typing import Any, Callable, List, Optional, Tuple
import math
import numpy as np
import pygame

from systems.audio import audio
from systems.ui import wrap_text


# ===========================================================================
# 1. COMPUTER GRAPHICS: Polygon Geometry & Triangulation (Broken Relic)
# ===========================================================================

def rotate_point_2d(x: float, y: float, angle_deg: float) -> Tuple[float, float]:
    """Applies a 2D rotation matrix R(θ) to point (x, y)."""
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)


def rotate_polygon_vertices(
    vertices: List[Tuple[float, float]], angle_deg: float
) -> List[Tuple[float, float]]:
    """Rotates a list of polygon vertices around origin (0, 0)."""
    return [rotate_point_2d(vx, vy, angle_deg) for vx, vy in vertices]


def translate_polygon_vertices(
    vertices: List[Tuple[float, float]], dx: float, dy: float
) -> List[Tuple[float, float]]:
    """Translates polygon vertices by offset (dx, dy)."""
    return [(vx + dx, vy + dy) for vx, vy in vertices]


def polygon_signed_area(vertices: List[Tuple[float, float]]) -> float:
    """Calculates the signed area of a 2D polygon using the Shoelace formula."""
    n = len(vertices)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return area * 0.5


def is_point_inside_triangle(
    pt: Tuple[float, float],
    a: Tuple[float, float],
    b: Tuple[float, float],
    c: Tuple[float, float],
) -> bool:
    """Tests if point pt lies inside triangle (a, b, c) using barycentric cross products."""
    px, py = pt
    ax, ay = a
    bx, by = b
    cx, cy = c

    v0x, v0y = cx - ax, cy - ay
    v1x, v1y = bx - ax, by - ay
    v2x, v2y = px - ax, py - ay

    dot00 = v0x * v0x + v0y * v0y
    dot01 = v0x * v1x + v0y * v1y
    dot02 = v0x * v2x + v0y * v2y
    dot11 = v1x * v1x + v1y * v1y
    dot12 = v1x * v2x + v1y * v2y

    denom = dot00 * dot11 - dot01 * dot01
    if abs(denom) < 1e-9:
        return False
    inv = 1.0 / denom
    u = (dot11 * dot02 - dot01 * dot12) * inv
    v = (dot00 * dot12 - dot01 * dot02) * inv
    return (u >= -1e-5) and (v >= -1e-5) and (u + v <= 1.00001)


def triangulate_polygon_ear_clipping(
    vertices: List[Tuple[float, float]]
) -> List[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]]:
    """Divides a simple 2D polygon into triangles using the Ear-Clipping triangulation algorithm.
    
    Guarantees that an N-vertex simple polygon is partitioned into N - 2 triangles
    without adding extra interior vertices.
    """
    n = len(vertices)
    if n < 3:
        return []
    if n == 3:
        return [(vertices[0], vertices[1], vertices[2])]

    # Ensure counter-clockwise vertex orientation (positive signed area)
    poly = list(vertices)
    if polygon_signed_area(poly) < 0.0:
        poly.reverse()

    triangles = []
    indices = list(range(len(poly)))

    max_iter = len(poly) * 3
    iter_count = 0

    while len(indices) > 3 and iter_count < max_iter:
        iter_count += 1
        ear_found = False

        for i in range(len(indices)):
            prev_idx = indices[(i - 1) % len(indices)]
            curr_idx = indices[i]
            next_idx = indices[(i + 1) % len(indices)]

            a = poly[prev_idx]
            b = poly[curr_idx]
            c = poly[next_idx]

            # Convex test (cross product > 0 for CCW)
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 1e-7:
                continue

            # Ear test: no other remaining vertex can be inside triangle (a, b, c)
            contains_vertex = False
            for j in range(len(indices)):
                chk_idx = indices[j]
                if chk_idx in (prev_idx, curr_idx, next_idx):
                    continue
                if is_point_inside_triangle(poly[chk_idx], a, b, c):
                    contains_vertex = True
                    break

            if not contains_vertex:
                triangles.append((a, b, c))
                indices.pop(i)
                ear_found = True
                break

        if not ear_found:
            # Fallback for degenerate polygons: fan triangulation
            break

    if len(indices) == 3:
        triangles.append((poly[indices[0]], poly[indices[1]], poly[indices[2]]))
    elif len(indices) > 3:
        # Fan fallback
        v0 = poly[indices[0]]
        for k in range(1, len(indices) - 1):
            triangles.append((v0, poly[indices[k]], poly[indices[k + 1]]))

    return triangles


# ===========================================================================
# 2. IMAGE PROCESSING: Median Filtering & Noise Reduction (Memory Fragments)
# ===========================================================================

def apply_median_filter_3x3(image: np.ndarray) -> np.ndarray:
    """Applies a genuine 3×3 Median Filter to a 2D grayscale or 3D RGB image array.
    
    Algorithm:
    1. For each pixel, read neighboring pixel values in a 3×3 window.
    2. Sort the 9 neighboring values.
    3. Select the median value (middle value at index 4).
    4. Replace the original pixel with this median value.
    
    Eliminates high-frequency impulse noise (salt-and-pepper) while preserving sharp edges.
    """
    if image.ndim == 3:
        out = np.zeros_like(image)
        for c in range(image.shape[2]):
            out[:, :, c] = apply_median_filter_3x3(image[:, :, c])
        return out

    h, w = image.shape
    out = np.zeros((h, w), dtype=image.dtype)
    padded = np.pad(image, ((1, 1), (1, 1)), mode="edge")

    for y in range(h):
        for x in range(w):
            window = padded[y : y + 3, x : x + 3].flatten()
            window.sort()
            out[y, x] = window[4]  # 5th element of 9 is median
    return out


def apply_box_blur_3x3(image: np.ndarray) -> np.ndarray:
    """Applies a 3×3 simple averaging / box blur filter (for comparison against median)."""
    if image.ndim == 3:
        out = np.zeros_like(image)
        for c in range(image.shape[2]):
            out[:, :, c] = apply_box_blur_3x3(image[:, :, c])
        return out

    h, w = image.shape
    out = np.zeros((h, w), dtype=np.uint8)
    padded = np.pad(image.astype(np.float32), ((1, 1), (1, 1)), mode="edge")

    for y in range(h):
        for x in range(w):
            avg = np.mean(padded[y : y + 3, x : x + 3])
            out[y, x] = np.clip(int(round(avg)), 0, 255)
    return out


def apply_linear_contrast_stretch(image: np.ndarray) -> np.ndarray:
    """Linearly stretches dynamic range [min, max] across [0, 255] (for comparison)."""
    vmin = float(np.min(image))
    vmax = float(np.max(image))
    if vmax <= vmin:
        return image.copy()
    scaled = (image.astype(np.float32) - vmin) * 255.0 / (vmax - vmin)
    return np.clip(scaled, 0, 255).astype(np.uint8)


def add_salt_and_pepper_noise(
    image: np.ndarray, noise_ratio: float = 0.20, seed: int = 42
) -> np.ndarray:
    """Adds genuine salt-and-pepper (impulse) noise to an image array."""
    rng = np.random.RandomState(seed)
    noisy = image.copy()
    h, w = noisy.shape[:2]
    num_noisy = int(h * w * noise_ratio)

    # Pepper (0)
    for _ in range(num_noisy // 2):
        ry = rng.randint(0, h)
        rx = rng.randint(0, w)
        if noisy.ndim == 3:
            noisy[ry, rx, :] = 0
        else:
            noisy[ry, rx] = 0

    # Salt (255)
    for _ in range(num_noisy // 2):
        ry = rng.randint(0, h)
        rx = rng.randint(0, w)
        if noisy.ndim == 3:
            noisy[ry, rx, :] = 255
        else:
            noisy[ry, rx] = 255

    return noisy


# ===========================================================================
# 3. COMPUTER GRAPHICS: Texture Mapping Engine (Ancient Blueprint)
# ===========================================================================

def generate_procedural_mosaic_texture(size: int = 160) -> pygame.Surface:
    """Generates a rich ancient geometric mosaic pattern texture for UV texture mapping."""
    surf = pygame.Surface((size, size))
    surf.fill((32, 28, 42))

    # Base stone tiles
    tile_size = 16
    for y in range(0, size, tile_size):
        for x in range(0, size, tile_size):
            tone = 35 + ((x * 7 + y * 13) % 20)
            pygame.draw.rect(surf, (tone, tone - 4, tone + 6), (x, y, tile_size - 1, tile_size - 1))

    center = size // 2

    # Lapis lazuli & gold concentric geometric borders
    pygame.draw.circle(surf, (40, 85, 160), (center, center), int(size * 0.44), width=4)
    pygame.draw.circle(surf, (215, 175, 75), (center, center), int(size * 0.38), width=3)
    pygame.draw.circle(surf, (190, 60, 50), (center, center), int(size * 0.28), width=3)

    # 8-pointed star rosette
    for i in range(8):
        ang = i * (math.pi / 4.0)
        p1 = (center + math.cos(ang) * (size * 0.34), center + math.sin(ang) * (size * 0.34))
        p2 = (center + math.cos(ang + math.pi / 8) * (size * 0.16), center + math.sin(ang + math.pi / 8) * (size * 0.16))
        p3 = (center + math.cos(ang - math.pi / 8) * (size * 0.16), center + math.sin(ang - math.pi / 8) * (size * 0.16))
        pygame.draw.polygon(surf, (245, 205, 95), [p1, p2, p3])
        pygame.draw.polygon(surf, (160, 125, 45), [p1, p2, p3], width=1)

    # Central gemstone core
    pygame.draw.circle(surf, (255, 225, 120), (center, center), 12)
    pygame.draw.circle(surf, (50, 180, 240), (center, center), 7)

    return surf


def map_texture_subregion(
    source_texture: pygame.Surface,
    uv_bounds: Tuple[float, float, float, float],
    target_rect: pygame.Rect,
    rotation_deg: float = 0.0,
) -> pygame.Surface:
    """Maps 2D texture coordinates (UV) onto a target quad surface geometry with rotation.
    
    uv_bounds: (u_min, v_min, u_max, v_max) where u, v ∈ [0.0, 1.0].
    """
    tw, th = source_texture.get_size()
    u0, v0, u1, v1 = uv_bounds
    src_x = int(round(u0 * tw))
    src_y = int(round(v0 * th))
    src_w = max(1, int(round((u1 - u0) * tw)))
    src_h = max(1, int(round((v1 - v0) * th)))

    # Extract sub-surface according to UV mapping
    sub_rect = pygame.Rect(src_x, src_y, src_w, src_h)
    sub_surf = source_texture.subsurface(sub_rect).copy()

    # Scale to match target quad geometry
    if sub_surf.get_size() != (target_rect.width, target_rect.height):
        sub_surf = pygame.transform.scale(sub_surf, (target_rect.width, target_rect.height))

    # Apply 2D geometric rotation transformation
    rot = int(round(rotation_deg)) % 360
    if rot != 0:
        sub_surf = pygame.transform.rotate(sub_surf, -rot)

    return sub_surf


# ===========================================================================
# 4. PUZZLE MODAL: LEFT STATION — BROKEN RELIC
# ===========================================================================

class BrokenRelicPuzzle:
    """Left Station: Geometric polygon reconstruction and triangulation puzzle."""

    CLUE_TEXT = "The Crimson Mirror was shattered in the cataclysm; red light cannot focus resonance through any crystal."
    ELIMINATED_MIRROR = "mirror_red"
    ELIMINATED_COMBO = ("key_bronze", "mirror_red", "crystal_1")

    def __init__(self, screen_w: int = 800, screen_h: int = 600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open = False
        self.is_solved = False
        self.on_solve: Optional[Callable[[], None]] = None

        # Modal window geometry - centered and spacious, cleared below HUD
        self.width = 720
        self.height = 436
        self.x = (screen_w - self.width) // 2
        self.y = max(48, (screen_h - self.height) // 2)

        # Puzzle Board & Pieces Tray
        self.board_rect = pygame.Rect(self.x + 20, self.y + 46, 336, 296)
        self.tray_rect = pygame.Rect(self.x + 372, self.y + 46, 328, 296)

        # Target center on the board
        self.target_cx = self.board_rect.centerx
        self.target_cy = self.board_rect.centery

        # Define 5 geometric polygon pieces that form a symmetrical ancient solar crest:
        # Piece 0: Top triangular crest (triangle)
        # Piece 1: Central trapezoid (quad -> ear-clipping decomposes into 2 triangles)
        # Piece 2: Left wing triangle (triangle)
        # Piece 3: Right wing triangle (triangle)
        # Piece 4: Bottom triangular base (triangle)
        raw_pieces = [
            {
                "id": 0,
                "name": "Top Crest",
                "local_verts": [(0.0, -52.0), (36.0, -18.0), (-36.0, -18.0)],
                "offset": (0.0, -18.0),
                "init_tray": (self.tray_rect.x + 80, self.tray_rect.y + 50),
                "init_rot": 90.0,
                "color": (215, 175, 75),
            },
            {
                "id": 1,
                "name": "Central Core",
                "local_verts": [(-36.0, -18.0), (36.0, -18.0), (28.0, 22.0), (-28.0, 22.0)],
                "offset": (0.0, 2.0),
                "init_tray": (self.tray_rect.x + 220, self.tray_rect.y + 50),
                "init_rot": 180.0,
                "color": (195, 150, 60),
            },
            {
                "id": 2,
                "name": "Left Wing",
                "local_verts": [(-74.0, 0.0), (-36.0, -18.0), (-28.0, 22.0)],
                "offset": (-26.0, 2.0),
                "init_tray": (self.tray_rect.x + 80, self.tray_rect.y + 140),
                "init_rot": 270.0,
                "color": (230, 190, 95),
            },
            {
                "id": 3,
                "name": "Right Wing",
                "local_verts": [(36.0, -18.0), (74.0, 0.0), (28.0, 22.0)],
                "offset": (26.0, 2.0),
                "init_tray": (self.tray_rect.x + 220, self.tray_rect.y + 140),
                "init_rot": 90.0,
                "color": (230, 190, 95),
            },
            {
                "id": 4,
                "name": "Base Keystone",
                "local_verts": [(-28.0, 22.0), (28.0, 22.0), (0.0, 60.0)],
                "offset": (0.0, 24.0),
                "init_tray": (self.tray_rect.x + 150, self.tray_rect.y + 220),
                "init_rot": 180.0,
                "color": (185, 140, 55),
            },
        ]

        self.pieces = []
        for p in raw_pieces:
            tx = self.target_cx + p["offset"][0]
            ty = self.target_cy + p["offset"][1]
            # Triangulate polygon vertices using ear-clipping
            triangles = triangulate_polygon_ear_clipping(p["local_verts"])
            self.pieces.append({
                "id": p["id"],
                "name": p["name"],
                "local_verts": p["local_verts"],
                "triangles": triangles,
                "target_pos": (tx, ty),
                "target_rot": 0.0,
                "pos": list(p["init_tray"]),
                "rot": p["init_rot"],
                "snapped": False,
                "color": p["color"],
            })

        self.selected_piece_idx: Optional[int] = None
        self.drag_offset = (0.0, 0.0)
        self.success_flash = 0.0

    def open(self):
        self.is_open = True
        if self.is_solved:
            for p in self.pieces:
                p["pos"] = list(p["target_pos"])
                p["rot"] = p["target_rot"]
                p["snapped"] = True

    def close(self):
        self.is_open = False
        self.selected_piece_idx = None

    def rotate_selected(self, delta: float = 90.0):
        """Rotates the currently selected piece by delta degrees (default 90°)."""
        if self.selected_piece_idx is not None:
            p = self.pieces[self.selected_piece_idx]
            if not p["snapped"]:
                p["rot"] = (p["rot"] + delta) % 360.0
                audio.play("clue")

    def handle_keydown(self, key: int) -> bool:
        if not self.is_open:
            return False
        if key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
            self.close()
            return True
        elif key in (pygame.K_r, pygame.K_t):
            self.rotate_selected(90.0)
            return True
        return False

    def handle_click(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False

        # Close button [X]
        close_btn = pygame.Rect(self.x + self.width - 32, self.y + 14, 20, 20)
        if close_btn.collidepoint(mx, my):
            self.close()
            return True

        # Rotate button
        rot_btn = pygame.Rect(self.tray_rect.x + (self.tray_rect.width - 120) // 2, self.tray_rect.bottom - 28, 120, 22)
        if rot_btn.collidepoint(mx, my):
            self.rotate_selected(90.0)
            return True

        # Check piece selection
        for idx in reversed(range(len(self.pieces))):
            p = self.pieces[idx]
            if p["snapped"] and self.is_solved:
                continue
            px, py = p["pos"]
            # Bounding check
            if math.hypot(mx - px, my - py) < 42:
                self.selected_piece_idx = idx
                self.drag_offset = (px - mx, py - my)
                return True

        self.selected_piece_idx = None
        return True

    def handle_mouse_up(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False
        if self.selected_piece_idx is not None:
            p = self.pieces[self.selected_piece_idx]
            # Check snap condition: proximity to target and correct rotation
            tx, ty = p["target_pos"]
            dist = math.hypot(p["pos"][0] - tx, p["pos"][1] - ty)
            rot_diff = abs((p["rot"] % 360.0) - p["target_rot"])
            if rot_diff > 180.0:
                rot_diff = 360.0 - rot_diff

            if dist < 32.0 and rot_diff < 15.0:
                p["pos"] = [tx, ty]
                p["rot"] = p["target_rot"]
                p["snapped"] = True
                audio.play("clue")
                self._check_completion()
            self.selected_piece_idx = None
            return True
        return False

    def handle_mouse_motion(self, mx: int, my: int):
        if self.is_open and self.selected_piece_idx is not None:
            p = self.pieces[self.selected_piece_idx]
            if not p["snapped"]:
                p["pos"][0] = mx + self.drag_offset[0]
                p["pos"][1] = my + self.drag_offset[1]

    def _check_completion(self):
        if all(p["snapped"] for p in self.pieces) and not self.is_solved:
            self.is_solved = True
            self.success_flash = 1.0
            audio.play("door_open")
            if callable(self.on_solve):
                self.on_solve()

    def update(self, dt: float):
        if self.success_flash > 0:
            self.success_flash = max(0.0, self.success_flash - dt * 1.5)

    def draw(self, surface: pygame.Surface):
        if not self.is_open:
            return

        # Dim overlay
        dim = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        dim.fill((6, 5, 12, 205))
        surface.blit(dim, (0, 0))

        # Main Outer Tablet
        tablet = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        tablet.fill((20, 17, 28, 250))
        pygame.draw.rect(tablet, (200, 160, 75), (0, 0, self.width, self.height), width=2, border_radius=8)
        pygame.draw.rect(tablet, (75, 60, 38), (4, 4, self.width - 8, self.height - 8), width=1, border_radius=6)
        surface.blit(tablet, (self.x, self.y))

        # Fonts
        f_title = pygame.font.SysFont("georgia", 17, bold=True)
        f_body = pygame.font.SysFont("consolas", 12)
        f_clue_hdr = pygame.font.SysFont("consolas", 12, bold=True)
        f_clue_txt = pygame.font.SysFont("consolas", 13, bold=True)
        f_small = pygame.font.SysFont("consolas", 11)

        # Title
        t_surf = f_title.render("BROKEN RELIC — GEOMETRIC RECONSTRUCTION", True, (248, 224, 148))
        surface.blit(t_surf, (self.x + (self.width - t_surf.get_width()) // 2, self.y + 16))
        pygame.draw.line(surface, (150, 120, 50), (self.x + 30, self.y + 42), (self.x + self.width - 30, self.y + 42), 1)

        # Close button [X]
        close_btn = pygame.Rect(self.x + self.width - 32, self.y + 14, 20, 20)
        pygame.draw.rect(surface, (45, 36, 55), close_btn, border_radius=3)
        pygame.draw.rect(surface, (180, 140, 60), close_btn, width=1, border_radius=3)
        x_lbl = f_small.render("X", True, (240, 210, 150))
        surface.blit(x_lbl, (close_btn.centerx - x_lbl.get_width() // 2, close_btn.centery - x_lbl.get_height() // 2))

        # 1. Left: Reconstruction Board
        pygame.draw.rect(surface, (14, 11, 20), self.board_rect, border_radius=6)
        pygame.draw.rect(surface, (80, 65, 45), self.board_rect, width=1, border_radius=6)
        b_lbl = f_small.render("ASSEMBLY BOARD (POLYGON OUTLINE)", True, (160, 145, 125))
        surface.blit(b_lbl, (self.board_rect.x + 12, self.board_rect.y + 8))

        # Faint target silhouette outline
        for p in self.pieces:
            tx, ty = p["target_pos"]
            verts = translate_polygon_vertices(p["local_verts"], tx, ty)
            pygame.draw.polygon(surface, (45, 38, 55), [(int(vx), int(vy)) for vx, vy in verts], width=1)

        # 2. Right: Fragments Tray
        pygame.draw.rect(surface, (14, 11, 20), self.tray_rect, border_radius=6)
        pygame.draw.rect(surface, (80, 65, 45), self.tray_rect, width=1, border_radius=6)
        tr_lbl = f_small.render("RELIC SHARDS (DRAG & [R] ROTATE)", True, (160, 145, 125))
        surface.blit(tr_lbl, (self.tray_rect.x + 12, self.tray_rect.y + 8))

        # Rotate button
        rot_btn = pygame.Rect(self.tray_rect.x + (self.tray_rect.width - 120) // 2, self.tray_rect.bottom - 28, 120, 22)
        pygame.draw.rect(surface, (35, 28, 48), rot_btn, border_radius=4)
        pygame.draw.rect(surface, (190, 150, 70), rot_btn, width=1, border_radius=4)
        rot_lbl = f_small.render("[R] Rotate 90°", True, (245, 225, 160))
        surface.blit(rot_lbl, (rot_btn.centerx - rot_lbl.get_width() // 2, rot_btn.centery - rot_lbl.get_height() // 2))

        # Draw all pieces (and their triangulated sub-faces)
        for idx, p in enumerate(self.pieces):
            px, py = p["pos"]
            rot = p["rot"]
            rotated_verts = rotate_polygon_vertices(p["local_verts"], rot)
            world_verts = translate_polygon_vertices(rotated_verts, px, py)
            pts = [(int(vx), int(vy)) for vx, vy in world_verts]

            # Shaded polygon surface
            col = (255, 235, 140) if p["snapped"] else p["color"]
            pygame.draw.polygon(surface, col, pts)

            # Triangulation lines: Render actual ear-clipping triangles
            for tri in p["triangles"]:
                tri_rot = rotate_polygon_vertices(list(tri), rot)
                tri_pts = [(int(vx + px), int(vy + py)) for vx, vy in tri_rot]
                pygame.draw.polygon(surface, (85, 60, 25), tri_pts, width=1)

            # Highlight selected piece
            if idx == self.selected_piece_idx:
                pygame.draw.polygon(surface, (255, 255, 255), pts, width=2)
            else:
                pygame.draw.polygon(surface, (130, 95, 40), pts, width=1)

        # Success / Clue Banner (or Instruction Footer)
        if self.is_solved:
            banner = pygame.Rect(self.x + 20, self.y + self.height - 82, self.width - 40, 68)
            pygame.draw.rect(surface, (28, 22, 16), banner, border_radius=6)
            pygame.draw.rect(surface, (230, 185, 75), banner, width=2, border_radius=6)
            hdr = f_clue_hdr.render("★ RELIC HARMONIZED — DISCOVERY CLUE ADDED TO JOURNAL", True, (255, 215, 100))
            surface.blit(hdr, (banner.centerx - hdr.get_width() // 2, banner.y + 8))
            clue_lines = wrap_text(f"\"{self.CLUE_TEXT}\"", f_clue_txt, banner.width - 40)
            for idx, ln in enumerate(clue_lines):
                c_lbl = f_clue_txt.render(ln, True, (255, 245, 185))
                surface.blit(c_lbl, (banner.centerx - c_lbl.get_width() // 2, banner.y + 26 + idx * 17))
        else:
            foot = f_small.render("Drag shards into the outline. Align orientation to snap into place. [ESC] Close", True, (160, 150, 140))
            surface.blit(foot, (self.x + (self.width - foot.get_width()) // 2, self.y + self.height - 20))


# ===========================================================================
# 5. PUZZLE MODAL: RIGHT STATION — MEMORY FRAGMENTS
# ===========================================================================

class MemoryFragmentsPuzzle:
    """Right Station: Genuine image noise reduction with 3×3 Median Filtering."""

    CLUE_TEXT = "The Bronze Key fractured during the First Trial; the first rank cannot sustain Crucible resonance."
    ELIMINATED_KEY = "key_bronze"
    ELIMINATED_COMBO = ("key_bronze", "mirror_blue", "crystal_3")

    def __init__(self, screen_w: int = 800, screen_h: int = 600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open = False
        self.is_solved = False
        self.on_solve: Optional[Callable[[], None]] = None

        # Modal window geometry - centered and spacious, cleared below HUD
        self.width = 730
        self.height = 436
        self.x = (screen_w - self.width) // 2
        self.y = max(48, (screen_h - self.height) // 2)

        # Plate resolution and display bounding box
        self.plate_size = 64
        self.plate_box = pygame.Rect(self.x + 24, self.y + 48, 246, 246)

        # Generate base memory symbol array (sharp geometric solar emblem)
        self.clean_array = self._generate_clean_memory_array(self.plate_size)
        # Apply genuine salt-and-pepper noise
        self.noisy_array = add_salt_and_pepper_noise(self.clean_array, noise_ratio=0.22, seed=108)

        # Process genuine algorithm outcomes for instant preview & comparison
        self.box_array = apply_box_blur_3x3(self.noisy_array)
        self.median_array = apply_median_filter_3x3(self.noisy_array)
        self.contrast_array = apply_linear_contrast_stretch(self.noisy_array)

        # Active display state: Start with noisy array
        self.current_filter: Optional[str] = None
        self.display_array = self.noisy_array.copy()

        # Visual feedback message
        self.status_msg = "Select a filter [1-3] to preview results, then press [CONFIRM]."
        self.sweep_progress = 0.0

    def _generate_clean_memory_array(self, size: int) -> np.ndarray:
        """Generates a high-contrast ancient runic glyph on stone background."""
        surf = pygame.Surface((size, size))
        surf.fill((45, 42, 56))
        center = size // 2

        # Outer sun halo
        pygame.draw.circle(surf, (180, 160, 210), (center, center), int(size * 0.40), width=3)
        # Inner diamond glyph
        pts = [
            (center, center - int(size * 0.32)),
            (center + int(size * 0.32), center),
            (center, center + int(size * 0.32)),
            (center - int(size * 0.32), center),
        ]
        pygame.draw.polygon(surf, (235, 220, 255), pts, width=3)
        # Central eye rune
        pygame.draw.circle(surf, (245, 240, 255), (center, center), int(size * 0.12))

        # Convert to 2D grayscale uint8 array
        arr = pygame.surfarray.array2d(surf)
        # Extract luminance
        gray = ((arr & 0xFF) * 0.33 + ((arr >> 8) & 0xFF) * 0.33 + ((arr >> 16) & 0xFF) * 0.34).astype(np.uint8)
        return gray

    def open(self):
        self.is_open = True
        if self.is_solved:
            self.current_filter = "median"
            self.display_array = self.median_array.copy()
            self.status_msg = "Restored: The Median Filter cleanly isolated the runic inscription."

    def close(self):
        self.is_open = False

    def select_filter(self, filter_name: str):
        """Previews the selected image processing filter on the noisy memory plate."""
        self.current_filter = filter_name
        audio.play("clue")

        if filter_name == "box":
            self.display_array = self.box_array.copy()
            self.status_msg = "Preview: Box Blur smears noise into gray halos; edges are severely blurred."
        elif filter_name == "contrast":
            self.display_array = self.contrast_array.copy()
            self.status_msg = "Preview: Linear Contrast stretches extremes, amplifying noise speckles."
        elif filter_name == "median":
            self.display_array = self.median_array.copy()
            self.status_msg = "Preview: Median Filter eliminates salt-and-pepper noise while preserving sharp contours."

    def confirm_selection(self) -> bool:
        """Confirms the active filter selection to solve the puzzle."""
        if self.is_solved:
            return True
        if self.current_filter == "median":
            self.is_solved = True
            self.status_msg = "Confirmed! The Median Filter restored the inscription without edge distortion."
            self.sweep_progress = 1.0
            audio.play("door_open")
            if callable(self.on_solve):
                self.on_solve()
            return True
        elif self.current_filter in ("box", "contrast"):
            self.status_msg = "Incorrect filter: Noise remains or edges blurred. Compare other filters and confirm again."
            audio.play("door_locked")
            return False
        else:
            self.status_msg = "Please select a filter option [1, 2, or 3] before confirming."
            audio.play("door_locked")
            return False

    def handle_keydown(self, key: int) -> bool:
        if not self.is_open:
            return False
        if key == pygame.K_ESCAPE:
            self.close()
            return True
        elif key == pygame.K_1:
            self.select_filter("box")
            return True
        elif key == pygame.K_2:
            self.select_filter("median")
            return True
        elif key == pygame.K_3:
            self.select_filter("contrast")
            return True
        elif key in (pygame.K_SPACE, pygame.K_RETURN):
            if not self.is_solved:
                if self.current_filter is not None:
                    self.confirm_selection()
                else:
                    self.close()
            else:
                self.close()
            return True
        return False

    def handle_click(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False

        # Close button [X]
        close_btn = pygame.Rect(self.x + self.width - 32, self.y + 14, 20, 20)
        if close_btn.collidepoint(mx, my):
            self.close()
            return True

        # Filter option buttons (422 width)
        btn_box = pygame.Rect(self.x + 284, self.y + 46, 422, 58)
        btn_med = pygame.Rect(self.x + 284, self.y + 112, 422, 58)
        btn_cnt = pygame.Rect(self.x + 284, self.y + 178, 422, 58)
        btn_confirm = pygame.Rect(self.x + 284, self.y + 248, 422, 32)

        if btn_box.collidepoint(mx, my):
            self.select_filter("box")
            return True
        elif btn_med.collidepoint(mx, my):
            self.select_filter("median")
            return True
        elif btn_cnt.collidepoint(mx, my):
            self.select_filter("contrast")
            return True
        elif btn_confirm.collidepoint(mx, my):
            self.confirm_selection()
            return True

        return True

    def update(self, dt: float):
        if self.sweep_progress > 0:
            self.sweep_progress = max(0.0, self.sweep_progress - dt * 1.5)

    def draw(self, surface: pygame.Surface):
        if not self.is_open:
            return

        dim = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        dim.fill((6, 5, 12, 205))
        surface.blit(dim, (0, 0))

        tablet = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        tablet.fill((20, 18, 30, 250))
        pygame.draw.rect(tablet, (100, 170, 240), (0, 0, self.width, self.height), width=2, border_radius=8)
        pygame.draw.rect(tablet, (40, 65, 90), (4, 4, self.width - 8, self.height - 8), width=1, border_radius=6)
        surface.blit(tablet, (self.x, self.y))

        f_title = pygame.font.SysFont("georgia", 17, bold=True)
        f_body = pygame.font.SysFont("consolas", 12, bold=True)
        f_clue_hdr = pygame.font.SysFont("consolas", 12, bold=True)
        f_clue_txt = pygame.font.SysFont("consolas", 13, bold=True)
        f_small = pygame.font.SysFont("consolas", 11)

        # Header
        t_surf = f_title.render("MEMORY FRAGMENTS — NOISE REDUCTION", True, (160, 215, 255))
        surface.blit(t_surf, (self.x + (self.width - t_surf.get_width()) // 2, self.y + 16))
        pygame.draw.line(surface, (70, 130, 190), (self.x + 30, self.y + 42), (self.x + self.width - 30, self.y + 42), 1)

        # Close button [X]
        close_btn = pygame.Rect(self.x + self.width - 32, self.y + 14, 20, 20)
        pygame.draw.rect(surface, (30, 42, 60), close_btn, border_radius=3)
        pygame.draw.rect(surface, (100, 160, 230), close_btn, width=1, border_radius=3)
        x_lbl = f_small.render("X", True, (210, 235, 255))
        surface.blit(x_lbl, (close_btn.centerx - x_lbl.get_width() // 2, close_btn.centery - x_lbl.get_height() // 2))

        # 1. Left: Memory Plate Display (230x230 clean preview)
        plate_box = pygame.Rect(self.x + 20, self.y + 46, 246, 246)
        pygame.draw.rect(surface, (12, 10, 18), plate_box, border_radius=6)
        pygame.draw.rect(surface, (60, 110, 170), plate_box, width=2, border_radius=6)

        # Render active image array to surface
        rgb_plate = np.stack([self.display_array] * 3, axis=-1)
        raw_surf = pygame.surfarray.make_surface(rgb_plate.swapaxes(0, 1))
        scaled_surf = pygame.transform.scale(raw_surf, (230, 230))
        surface.blit(scaled_surf, (plate_box.x + 8, plate_box.y + 8))

        # Restoration sweep wave animation
        if self.sweep_progress > 0:
            sw_y = int(plate_box.y + 8 + (1.0 - self.sweep_progress) * 230)
            sweep_line = pygame.Surface((230, 4), pygame.SRCALPHA)
            sweep_line.fill((160, 240, 255, 180))
            surface.blit(sweep_line, (plate_box.x + 8, sw_y))

        # 2. Right: Filter Selection Panel (422 width, cards with multi-line wrapped text)
        filters = [
            ("box", "[1] Box Blur (Averaging 3x3)",
             "Replaces pixel with neighbor average. Blurs noise into muddy gray patches; loses sharp edges.",
             (180, 180, 180)),
            ("median", "[2] Median Filter (Rank 3x3)",
             "Sorts 3x3 neighbors and selects median value. Completely eliminates impulse noise and preserves contours.",
             (210, 230, 255)),
            ("contrast", "[3] Linear Contrast Stretch",
             "Stretches dynamic range across [0, 255]. Amplifies noise speckles across the entire plate.",
             (180, 180, 180)),
        ]

        card_w = 422
        card_h = 58
        for i, (fid, title, desc, col) in enumerate(filters):
            b_rect = pygame.Rect(self.x + 284, self.y + 46 + i * 66, card_w, card_h)
            is_active = (self.current_filter == fid)
            bg_col = (30, 46, 70) if is_active else (18, 16, 26)
            border_col = (110, 195, 255) if is_active else (55, 50, 70)
            pygame.draw.rect(surface, bg_col, b_rect, border_radius=5)
            pygame.draw.rect(surface, border_col, b_rect, width=2 if is_active else 1, border_radius=5)

            # Title
            t_col = (255, 230, 120) if is_active else col
            t_s = f_body.render(title, True, t_col)
            surface.blit(t_s, (b_rect.x + 12, b_rect.y + 6))

            # Multi-line wrapped description inside card width
            words = desc.split()
            lines = []
            cur_line = []
            for w in words:
                test_str = " ".join(cur_line + [w])
                if f_small.size(test_str)[0] <= card_w - 24:
                    cur_line.append(w)
                else:
                    if cur_line:
                        lines.append(" ".join(cur_line))
                    cur_line = [w]
            if cur_line:
                lines.append(" ".join(cur_line))

            for l_idx, line_txt in enumerate(lines[:2]):
                d_s = f_small.render(line_txt, True, (160, 168, 180))
                surface.blit(d_s, (b_rect.x + 12, b_rect.y + 24 + l_idx * 15))

        # Confirm Button
        btn_confirm = pygame.Rect(self.x + 284, self.y + 248, card_w, 32)
        conf_bg = (35, 65, 45) if self.current_filter else (24, 28, 38)
        conf_border = (80, 210, 120) if self.current_filter else (60, 65, 80)
        pygame.draw.rect(surface, conf_bg, btn_confirm, border_radius=5)
        pygame.draw.rect(surface, conf_border, btn_confirm, width=2 if self.current_filter else 1, border_radius=5)
        conf_txt = f_body.render("[CONFIRM FILTER SELECTION]  (or press ENTER)", True, (220, 255, 225) if self.current_filter else (140, 145, 155))
        surface.blit(conf_txt, (btn_confirm.centerx - conf_txt.get_width() // 2, btn_confirm.centery - conf_txt.get_height() // 2))

        # Status feedback line
        st_col = (110, 230, 150) if self.is_solved else ((245, 205, 110) if self.current_filter else (180, 175, 170))
        st_s = f_small.render(self.status_msg, True, st_col)
        surface.blit(st_s, (self.x + 20, self.y + 298))

        # Success / Clue Banner (or Instruction Footer)
        if self.is_solved:
            banner = pygame.Rect(self.x + 20, self.y + self.height - 82, self.width - 40, 68)
            pygame.draw.rect(surface, (18, 24, 34), banner, border_radius=6)
            pygame.draw.rect(surface, (110, 195, 255), banner, width=2, border_radius=6)
            hdr = f_clue_hdr.render("★ MEMORY RESTORED — DISCOVERY CLUE ADDED TO JOURNAL", True, (140, 220, 255))
            surface.blit(hdr, (banner.centerx - hdr.get_width() // 2, banner.y + 8))
            clue_lines = wrap_text(f"\"{self.CLUE_TEXT}\"", f_clue_txt, banner.width - 40)
            for idx, ln in enumerate(clue_lines):
                c_lbl = f_clue_txt.render(ln, True, (225, 245, 255))
                surface.blit(c_lbl, (banner.centerx - c_lbl.get_width() // 2, banner.y + 26 + idx * 17))
        else:
            foot = f_small.render("Press 1, 2, or 3 to preview filters. Press [ENTER] or click Confirm to apply. [ESC] Close", True, (150, 155, 165))
            surface.blit(foot, (self.x + (self.width - foot.get_width()) // 2, self.y + self.height - 20))


# ===========================================================================
# 6. PUZZLE MODAL: BOTTOM STATION — ANCIENT BLUEPRINT
# ===========================================================================

class AncientBlueprintPuzzle:
    """Bottom Station: Texture mapping puzzle restoring missing decorative floor pattern."""

    CLUE_TEXT = "The sacred blueprint confirms: The Crimson conduit is permanently severed; only Azure and Emerald paths are active."
    ELIMINATED_CONDUIT = "mirror_red"
    ELIMINATED_COMBO = ("key_gold", "mirror_red", "crystal_2")

    def __init__(self, screen_w: int = 800, screen_h: int = 600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open = False
        self.is_solved = False
        self.on_solve: Optional[Callable[[], None]] = None

        # Modal window geometry - centered and spacious, cleared below HUD
        self.width = 730
        self.height = 490
        self.x = (screen_w - self.width) // 2
        self.y = max(48, (screen_h - self.height) // 2)

        # Generate source procedural texture (160×160)
        self.source_texture = generate_procedural_mosaic_texture(160)

        # Target blueprint area on left (240×240) partitioned into 4 quadrants
        self.blueprint_rect = pygame.Rect(self.x + 24, self.y + 82, 240, 240)
        # Tile tray on right (410x296)
        self.tray_rect = pygame.Rect(self.x + 296, self.y + 82, 410, 296)

        qw = self.blueprint_rect.width // 2   # 120
        qh = self.blueprint_rect.height // 2  # 120

        # 4 distinct tray pedestal coordinates with generous padding
        tray_col0 = self.tray_rect.x + 32
        tray_col1 = self.tray_rect.x + 214
        tray_row0 = self.tray_rect.y + 10
        tray_row1 = self.tray_rect.y + 138

        self.pedestal_rects = [
            pygame.Rect(tray_col0, tray_row0, qw, qh),
            pygame.Rect(tray_col1, tray_row0, qw, qh),
            pygame.Rect(tray_col0, tray_row1, qw, qh),
            pygame.Rect(tray_col1, tray_row1, qw, qh),
        ]

        raw_tiles = [
            {
                "id": 0,
                "name": "Northwest Quadrant",
                "uv_bounds": (0.0, 0.0, 0.5, 0.5),
                "target_rect": pygame.Rect(self.blueprint_rect.x, self.blueprint_rect.y, qw, qh),
                "init_tray": (tray_col0, tray_row0),
                "init_rot": 90.0,
            },
            {
                "id": 1,
                "name": "Northeast Quadrant",
                "uv_bounds": (0.5, 0.0, 1.0, 0.5),
                "target_rect": pygame.Rect(self.blueprint_rect.x + qw, self.blueprint_rect.y, qw, qh),
                "init_tray": (tray_col1, tray_row0),
                "init_rot": 180.0,
            },
            {
                "id": 2,
                "name": "Southwest Quadrant",
                "uv_bounds": (0.0, 0.5, 0.5, 1.0),
                "target_rect": pygame.Rect(self.blueprint_rect.x, self.blueprint_rect.y + qh, qw, qh),
                "init_tray": (tray_col0, tray_row1),
                "init_rot": 270.0,
            },
            {
                "id": 3,
                "name": "Southeast Quadrant",
                "uv_bounds": (0.5, 0.5, 1.0, 1.0),
                "target_rect": pygame.Rect(self.blueprint_rect.x + qw, self.blueprint_rect.y + qh, qw, qh),
                "init_tray": (tray_col1, tray_row1),
                "init_rot": 90.0,
            },
        ]

        self.tiles = []
        for t in raw_tiles:
            self.tiles.append({
                "id": t["id"],
                "name": t["name"],
                "uv_bounds": t["uv_bounds"],
                "target_rect": t["target_rect"],
                "target_rot": 0.0,
                "pos": list(t["init_tray"]),
                "rot": t["init_rot"],
                "snapped": False,
            })

        self.selected_tile_idx: Optional[int] = None
        self.drag_offset = (0.0, 0.0)

    def open(self):
        self.is_open = True
        if self.is_solved:
            for t in self.tiles:
                tr = t["target_rect"]
                t["pos"] = [float(tr.x), float(tr.y)]
                t["rot"] = t["target_rot"]
                t["snapped"] = True

    def close(self):
        self.is_open = False
        self.selected_tile_idx = None

    def rotate_selected(self, delta: float = 90.0):
        if self.selected_tile_idx is not None:
            t = self.tiles[self.selected_tile_idx]
            if not t["snapped"]:
                t["rot"] = (t["rot"] + delta) % 360.0
                audio.play("clue")

    def handle_keydown(self, key: int) -> bool:
        if not self.is_open:
            return False
        if key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
            self.close()
            return True
        elif key in (pygame.K_r, pygame.K_t):
            self.rotate_selected(90.0)
            return True
        return False

    def handle_click(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False

        # Close button [X]
        close_btn = pygame.Rect(self.x + self.width - 32, self.y + 14, 20, 20)
        if close_btn.collidepoint(mx, my):
            self.close()
            return True

        # Rotate button
        rot_btn = pygame.Rect(self.tray_rect.x + (self.tray_rect.width - 150) // 2, self.tray_rect.y + 266, 150, 22)
        if rot_btn.collidepoint(mx, my):
            self.rotate_selected(90.0)
            return True

        # Check tile selection
        qw = self.blueprint_rect.width // 2
        qh = self.blueprint_rect.height // 2
        for idx in reversed(range(len(self.tiles))):
            t = self.tiles[idx]
            if t["snapped"] and self.is_solved:
                continue
            r = pygame.Rect(int(t["pos"][0]), int(t["pos"][1]), qw, qh)
            if r.collidepoint(mx, my):
                self.selected_tile_idx = idx
                self.drag_offset = (t["pos"][0] - mx, t["pos"][1] - my)
                return True

        self.selected_tile_idx = None
        return True

    def handle_mouse_up(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False
        if self.selected_tile_idx is not None:
            t = self.tiles[self.selected_tile_idx]
            tr = t["target_rect"]
            dist = math.hypot(t["pos"][0] - tr.x, t["pos"][1] - tr.y)
            rot_diff = abs((t["rot"] % 360.0) - t["target_rot"])
            if rot_diff > 180.0:
                rot_diff = 360.0 - rot_diff

            # Forgiving snapping: within 36 pixels and correct rotation
            if dist < 36.0 and rot_diff < 15.0:
                t["pos"] = [float(tr.x), float(tr.y)]
                t["rot"] = t["target_rot"]
                t["snapped"] = True
                audio.play("clue")
                self._check_completion()
            self.selected_piece_idx = None
            self.selected_tile_idx = None
            return True
        return False

    def handle_mouse_motion(self, mx: int, my: int):
        if self.is_open and self.selected_tile_idx is not None:
            t = self.tiles[self.selected_tile_idx]
            if not t["snapped"]:
                t["pos"][0] = mx + self.drag_offset[0]
                t["pos"][1] = my + self.drag_offset[1]

    def _check_completion(self):
        if all(t["snapped"] for t in self.tiles) and not self.is_solved:
            self.is_solved = True
            audio.play("door_open")
            if callable(self.on_solve):
                self.on_solve()

    def update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface):
        if not self.is_open:
            return

        dim = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        dim.fill((6, 5, 12, 205))
        surface.blit(dim, (0, 0))

        tablet = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        tablet.fill((20, 16, 26, 250))
        pygame.draw.rect(tablet, (215, 145, 65), (0, 0, self.width, self.height), width=2, border_radius=8)
        pygame.draw.rect(tablet, (75, 50, 30), (4, 4, self.width - 8, self.height - 8), width=1, border_radius=6)
        surface.blit(tablet, (self.x, self.y))

        f_title = pygame.font.SysFont("georgia", 17, bold=True)
        f_body = pygame.font.SysFont("consolas", 12)
        f_clue_hdr = pygame.font.SysFont("consolas", 12, bold=True)
        f_clue_txt = pygame.font.SysFont("consolas", 13, bold=True)
        f_small = pygame.font.SysFont("consolas", 11)

        # Header: Title (Y + 12), Subtitle (Y + 34), Divider (Y + 54)
        t_surf = f_title.render("ANCIENT BLUEPRINT — TEXTURE MAPPING", True, (255, 205, 140))
        surface.blit(t_surf, (self.x + (self.width - t_surf.get_width()) // 2, self.y + 12))

        sub_surf = f_small.render("Align texture coordinates and map tiles to the ancient blueprint", True, (190, 175, 160))
        surface.blit(sub_surf, (self.x + (self.width - sub_surf.get_width()) // 2, self.y + 34))

        pygame.draw.line(surface, (170, 105, 45), (self.x + 30, self.y + 54), (self.x + self.width - 30, self.y + 54), 1)

        # Close button [X]
        close_btn = pygame.Rect(self.x + self.width - 32, self.y + 14, 20, 20)
        pygame.draw.rect(surface, (45, 32, 25), close_btn, border_radius=3)
        pygame.draw.rect(surface, (200, 130, 60), close_btn, width=1, border_radius=3)
        x_lbl = f_small.render("X", True, (255, 215, 175))
        surface.blit(x_lbl, (close_btn.centerx - x_lbl.get_width() // 2, close_btn.centery - x_lbl.get_height() // 2))

        # 1. Left: Blueprint Frame & Target Surface Quads
        pygame.draw.rect(surface, (12, 10, 18), self.blueprint_rect, border_radius=6)
        pygame.draw.rect(surface, (150, 95, 45), self.blueprint_rect, width=2, border_radius=6)
        bp_lbl = f_small.render("BLUEPRINT SURFACE (TARGET SLOTS)", True, (180, 155, 135))
        surface.blit(bp_lbl, (self.blueprint_rect.x + 8, self.y + 64))

        # Faint architectural grid and slot division lines
        qw = self.blueprint_rect.width // 2
        qh = self.blueprint_rect.height // 2
        pygame.draw.line(surface, (55, 45, 35), (self.blueprint_rect.x + qw, self.blueprint_rect.y), (self.blueprint_rect.x + qw, self.blueprint_rect.bottom), 1)
        pygame.draw.line(surface, (55, 45, 35), (self.blueprint_rect.x, self.blueprint_rect.y + qh), (self.blueprint_rect.right, self.blueprint_rect.y + qh), 1)

        # Target slot ghost labels
        quad_labels = ["NW Quad", "NE Quad", "SW Quad", "SE Quad"]
        quad_rects = [
            pygame.Rect(self.blueprint_rect.x, self.blueprint_rect.y, qw, qh),
            pygame.Rect(self.blueprint_rect.x + qw, self.blueprint_rect.y, qw, qh),
            pygame.Rect(self.blueprint_rect.x, self.blueprint_rect.y + qh, qw, qh),
            pygame.Rect(self.blueprint_rect.x + qw, self.blueprint_rect.y + qh, qw, qh),
        ]
        for qr, ql in zip(quad_rects, quad_labels):
            ql_surf = f_small.render(ql, True, (65, 55, 45))
            surface.blit(ql_surf, (qr.centerx - ql_surf.get_width() // 2, qr.centery - ql_surf.get_height() // 2))

        # 2. Central ornamental divider line
        divider_x = self.x + 280
        pygame.draw.line(surface, (80, 50, 30), (divider_x, self.y + 64), (divider_x, self.y + 378), 2)
        pygame.draw.line(surface, (170, 105, 45), (divider_x, self.y + 74), (divider_x, self.y + 368), 1)

        # 3. Right: Pattern Tiles Tray
        pygame.draw.rect(surface, (14, 12, 20), self.tray_rect, border_radius=6)
        pygame.draw.rect(surface, (90, 60, 35), self.tray_rect, width=1, border_radius=6)
        tr_lbl = f_small.render("TEXTURE TILE TRAY (DRAG & [R] ROTATE)", True, (180, 155, 135))
        surface.blit(tr_lbl, (self.tray_rect.x + 8, self.y + 64))

        # Draw 4 clearly defined pedestals in tray with status
        slot_names = ["SLOT I", "SLOT II", "SLOT III", "SLOT IV"]
        for p_idx, (pr, sname) in enumerate(zip(self.pedestal_rects, slot_names)):
            pygame.draw.rect(surface, (20, 16, 26), pr, border_radius=4)
            pygame.draw.rect(surface, (60, 42, 32), pr, width=1, border_radius=4)
            is_snapped = self.tiles[p_idx]["snapped"]
            ped_status = "• MAPPED TO BLUEPRINT •" if is_snapped else sname
            ped_col = (85, 160, 120) if is_snapped else (95, 75, 60)
            p_lbl = f_small.render(ped_status, True, ped_col)
            surface.blit(p_lbl, (pr.centerx - p_lbl.get_width() // 2, pr.centery - p_lbl.get_height() // 2))

        # Rotate button
        rot_btn = pygame.Rect(self.tray_rect.x + (self.tray_rect.width - 150) // 2, self.tray_rect.y + 266, 150, 22)
        pygame.draw.rect(surface, (45, 30, 25), rot_btn, border_radius=4)
        pygame.draw.rect(surface, (215, 145, 65), rot_btn, width=1, border_radius=4)
        rot_lbl = f_small.render("[R] Rotate Tile 90°", True, (255, 225, 175))
        surface.blit(rot_lbl, (rot_btn.centerx - rot_lbl.get_width() // 2, rot_btn.centery - rot_lbl.get_height() // 2))

        # Draw Tiles using actual Texture Mapping
        for idx, t in enumerate(self.tiles):
            mapped_surf = map_texture_subregion(
                source_texture=self.source_texture,
                uv_bounds=t["uv_bounds"],
                target_rect=pygame.Rect(0, 0, qw, qh),
                rotation_deg=t["rot"],
            )

            tx = int(round(t["pos"][0]))
            ty = int(round(t["pos"][1]))
            surface.blit(mapped_surf, (tx, ty))

            # Tile border
            border_col = (255, 235, 140) if t["snapped"] else ((255, 255, 255) if idx == self.selected_tile_idx else (130, 90, 40))
            pygame.draw.rect(surface, border_col, (tx, ty, qw, qh), width=2 if (idx == self.selected_tile_idx or t["snapped"]) else 1)

        # Success / Clue Banner (or Instruction Footer)
        if self.is_solved:
            banner = pygame.Rect(self.x + 20, self.y + self.height - 96, self.width - 40, 80)
            pygame.draw.rect(surface, (30, 20, 15), banner, border_radius=6)
            pygame.draw.rect(surface, (245, 160, 65), banner, width=2, border_radius=6)
            hdr = f_clue_hdr.render("★ BLUEPRINT HARMONIZED — DISCOVERY CLUE ADDED TO JOURNAL", True, (255, 185, 75))
            surface.blit(hdr, (banner.centerx - hdr.get_width() // 2, banner.y + 8))
            clue_lines = wrap_text(f"\"{self.CLUE_TEXT}\"", f_clue_txt, banner.width - 40)
            for idx, ln in enumerate(clue_lines):
                c_lbl = f_clue_txt.render(ln, True, (255, 235, 180))
                surface.blit(c_lbl, (banner.centerx - c_lbl.get_width() // 2, banner.y + 28 + idx * 18))
        else:
            foot = f_small.render("Drag texture tiles to match UV coordinates on the blueprint. [ESC] Close", True, (160, 150, 140))
            surface.blit(foot, (self.x + (self.width - foot.get_width()) // 2, self.y + self.height - 24))


# ===========================================================================
# 7. TOP STATION — THE ANCIENT RULE TABLET MODAL
# ===========================================================================

class AncientRuleModal:
    """Top Station: Ancient carved stone tablet with three numbered harmonic paths."""

    CLUE_TEXT = "A key and crystal must share the same rank. The second path bears blue; the third wears green."

    def __init__(self, screen_w: int = 800, screen_h: int = 600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open = False
        self.on_inspect: Optional[Callable[[], None]] = None

        self.width = 680
        self.height = 430
        self.x = (screen_w - self.width) // 2
        self.y = max(48, (screen_h - self.height) // 2)

    def open(self):
        self.is_open = True
        if callable(self.on_inspect):
            self.on_inspect()

    def close(self):
        self.is_open = False

    def handle_keydown(self, key: int) -> bool:
        if not self.is_open:
            return False
        if key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
            self.close()
            return True
        return False

    def handle_click(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False
        close_btn = pygame.Rect(self.x + self.width - 32, self.y + 14, 20, 20)
        if close_btn.collidepoint(mx, my):
            self.close()
            return True
        # Click outside modal
        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        if not panel.collidepoint(mx, my):
            self.close()
            return True
        return True

    def draw(self, surface: pygame.Surface):
        if not self.is_open:
            return

        dim = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        dim.fill((6, 5, 12, 205))
        surface.blit(dim, (0, 0))

        tablet = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        tablet.fill((20, 18, 28, 250))
        pygame.draw.rect(tablet, (230, 200, 90), (0, 0, self.width, self.height), width=2, border_radius=8)
        pygame.draw.rect(tablet, (80, 65, 40), (4, 4, self.width - 8, self.height - 8), width=1, border_radius=6)
        surface.blit(tablet, (self.x, self.y))

        f_title = pygame.font.SysFont("georgia", 17, bold=True)
        f_body = pygame.font.SysFont("consolas", 12)
        f_bold = pygame.font.SysFont("consolas", 12, bold=True)
        f_small = pygame.font.SysFont("consolas", 11)

        # Header
        t_surf = f_title.render("THE ANCIENT RULE — HARMONIC PATHWAYS", True, (255, 230, 130))
        surface.blit(t_surf, (self.x + (self.width - t_surf.get_width()) // 2, self.y + 16))
        pygame.draw.line(surface, (170, 140, 60), (self.x + 36, self.y + 42), (self.x + self.width - 36, self.y + 42), 1)

        # Close button [X]
        close_btn = pygame.Rect(self.x + self.width - 32, self.y + 14, 20, 20)
        pygame.draw.rect(surface, (45, 36, 55), close_btn, border_radius=3)
        pygame.draw.rect(surface, (190, 155, 70), close_btn, width=1, border_radius=3)
        x_lbl = f_small.render("X", True, (245, 220, 150))
        surface.blit(x_lbl, (close_btn.centerx - x_lbl.get_width() // 2, close_btn.centery - x_lbl.get_height() // 2))

        # 3 Numbered Harmonic Paths (Graphic conduits)
        paths_y = self.y + 54
        pw = 186
        ph = 68
        paths = [
            ("PATH 1", "Crimson (Red)", (235, 75, 75), "Rank 1"),
            ("PATH 2", "Azure (Blue)", (65, 145, 250), "Rank 2"),
            ("PATH 3", "Emerald (Green)", (70, 225, 110), "Rank 3"),
        ]

        for i, (p_name, p_color, col_val, rank_txt) in enumerate(paths):
            px = self.x + 38 + i * (pw + 24)
            pr = pygame.Rect(px, paths_y, pw, ph)
            pygame.draw.rect(surface, (15, 13, 22), pr, border_radius=6)
            pygame.draw.rect(surface, col_val, pr, width=2, border_radius=6)

            pn = f_bold.render(p_name, True, col_val)
            surface.blit(pn, (pr.centerx - pn.get_width() // 2, pr.y + 10))
            pc = f_small.render(p_color, True, (220, 215, 205))
            surface.blit(pc, (pr.centerx - pc.get_width() // 2, pr.y + 28))
            prank = f_small.render(f"Attuned: {rank_txt}", True, (160, 150, 140))
            surface.blit(prank, (pr.centerx - prank.get_width() // 2, pr.y + 46))

        # Inscription Tablet Text (spacious container with proper word-wrapped text)
        rule_box = pygame.Rect(self.x + 36, self.y + 134, self.width - 72, 256)
        pygame.draw.rect(surface, (14, 11, 20), rule_box, border_radius=6)
        pygame.draw.rect(surface, (70, 55, 35), rule_box, width=1, border_radius=6)

        max_text_w = rule_box.width - 28

        # Word-wrap the inscription text properly so it never extends beyond the container boundary
        inscription_words = f"\"{self.CLUE_TEXT}\"".split()
        wrapped_inscription = []
        cur_line = []
        for w in inscription_words:
            test_str = " ".join(cur_line + [w])
            if f_bold.size(test_str)[0] <= max_text_w:
                cur_line.append(w)
            else:
                if cur_line:
                    wrapped_inscription.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            wrapped_inscription.append(" ".join(cur_line))

        cy = rule_box.y + 12
        # Section 1: Inscription title
        hdr = f_bold.render("ANCIENT INSCRIPTION:", True, (245, 215, 110))
        surface.blit(hdr, (rule_box.x + 14, cy))
        cy += 20

        # Section 2: Wrapped inscription lines
        for insc_line in wrapped_inscription:
            rendered = f_bold.render(insc_line, True, (255, 240, 160))
            surface.blit(rendered, (rule_box.x + 14, cy))
            cy += 18

        cy += 8
        # Section 3: Relic Rank Mapping
        map_hdr = f_bold.render("RELIC RANK MAPPING:", True, (215, 190, 130))
        surface.blit(map_hdr, (rule_box.x + 14, cy))
        cy += 18

        mapping_lines = [
            ("• Keys:     Bronze Key (Rank 1)  |  Silver Key (Rank 2)  |  Gold Key (Rank 3)", (225, 220, 210)),
            ("• Mirrors:  Crimson (Path 1)     |  Azure (Path 2)       |  Emerald (Path 3)", (225, 220, 210)),
            ("• Crystals: Crystal 1 (Rank 1)   |  Crystal 2 (Rank 2)   |  Crystal 3 (Rank 3)", (225, 220, 210)),
        ]
        for m_text, m_col in mapping_lines:
            rendered = f_body.render(m_text, True, m_col)
            surface.blit(rendered, (rule_box.x + 14, cy))
            cy += 18

        cy += 6
        rule_note = f_small.render("Fundamental Counting Principle: 3 Keys × 3 Mirrors × 3 Crystals = 27 combinations.", True, (180, 170, 160))
        surface.blit(rule_note, (rule_box.x + 14, cy))

        foot = f_small.render("Press [E], [SPACE], or [ESC] to return", True, (165, 150, 130))
        surface.blit(foot, (self.x + (self.width - foot.get_width()) // 2, self.y + self.height - 20))


# ===========================================================================
# 8. FORGE ENTRANCE INTRODUCTION POPUP (PART 8)
# ===========================================================================

class ForgeEntranceModal:
    """Pop-up modal introducing the Ancient Forge on first approach."""

    TITLE = "THE ANCIENT FORGE"
    BODY_TEXT = (
        "Three keys. Three mirrors. Three crystals.\n\n"
        "Choose one item from each group to create a combination.\n\n"
        "3 × 3 × 3 = 27 possible combinations.\n\n"
        "Two combinations can awaken the Forge. Explore the four clues around the room "
        "to eliminate the wrong choices and discover the correct ones.\n\n"
        "You have 3 attempts. Three incorrect submissions will cost one life."
    )

    def __init__(self, screen_w: int = 800, screen_h: int = 600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open = False

        self.width = 620
        self.height = 370
        self.x = (screen_w - self.width) // 2
        self.y = (screen_h - self.height) // 2

    def open(self):
        self.is_open = True
        audio.play("clue")

    def close(self):
        self.is_open = False

    def handle_keydown(self, key: int) -> bool:
        if not self.is_open:
            return False
        if key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
            self.close()
            return True
        return False

    def handle_click(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False
        close_btn = pygame.Rect(self.x + self.width - 32, self.y + 14, 20, 20)
        if close_btn.collidepoint(mx, my):
            self.close()
            return True
        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        if not panel.collidepoint(mx, my):
            self.close()
            return True
        return True

    def draw(self, surface: pygame.Surface):
        if not self.is_open:
            return

        dim = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        dim.fill((6, 5, 12, 205))
        surface.blit(dim, (0, 0))

        tablet = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        tablet.fill((22, 17, 28, 252))
        pygame.draw.rect(tablet, (240, 195, 80), (0, 0, self.width, self.height), width=2, border_radius=8)
        pygame.draw.rect(tablet, (80, 60, 35), (4, 4, self.width - 8, self.height - 8), width=1, border_radius=6)
        surface.blit(tablet, (self.x, self.y))

        f_title = pygame.font.SysFont("georgia", 18, bold=True)
        f_body = pygame.font.SysFont("consolas", 12)
        f_foot = pygame.font.SysFont("consolas", 11)

        t_surf = f_title.render(self.TITLE, True, (255, 225, 120))
        surface.blit(t_surf, (self.x + (self.width - t_surf.get_width()) // 2, self.y + 22))
        pygame.draw.line(surface, (170, 135, 55), (self.x + 36, self.y + 52), (self.x + self.width - 36, self.y + 52), 1)

        # Close button [X]
        close_btn = pygame.Rect(self.x + self.width - 32, self.y + 14, 20, 20)
        pygame.draw.rect(surface, (45, 34, 52), close_btn, border_radius=3)
        pygame.draw.rect(surface, (190, 150, 65), close_btn, width=1, border_radius=3)
        x_lbl = f_foot.render("X", True, (245, 215, 140))
        surface.blit(x_lbl, (close_btn.centerx - x_lbl.get_width() // 2, close_btn.centery - x_lbl.get_height() // 2))

        # Text body
        lines = wrap_text(self.BODY_TEXT, f_body, self.width - 72)
        curr_y = self.y + 70
        for ln in lines:
            if not ln.strip():
                curr_y += 10
                continue
            l_surf = f_body.render(ln, True, (235, 225, 210))
            surface.blit(l_surf, (self.x + 36, curr_y))
            curr_y += 18

        foot = f_foot.render("Press [SPACE], [ENTER], or [ESC] to proceed", True, (160, 150, 135))
        surface.blit(foot, (self.x + (self.width - foot.get_width()) // 2, self.y + self.height - 24))

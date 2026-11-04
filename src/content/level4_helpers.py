"""content/level4_helpers.py — CG/IP Algorithms, Machines, and Journal for Level 4.

Provides mathematical foundations, image processing routines, and interactive
temple machine systems for the Ancient Forge complex:
1. Procedural generation & particle trajectories (Bézier curves, easing).
2. Noise generation, Gaussian blur, and unsharp masking (Denoising & Edge reconstruction).
3. Histogram analysis, contrast stretching, and color-space decomposition (RGB).
4. Forge Core state machine & temporal platform oscillation.
5. Interactive sub-machines:
   - Memory Restoration Console (Zone D: Memory Vault)
   - Optical Prism Transformer (Zone C: Optical Gallery)
   - Core Stabilization Alignment (Zone E & Crucible)
   - Forge Journal modal (Discoveries, Memories, Harmonic Paths, CG/IP Principles)
"""

import math
import random
import pygame
from systems.ui import wrap_text


# ---------------------------------------------------------------------------
# 1. Mathematical Curves & Interpolation (CG)
# ---------------------------------------------------------------------------

def bezier_quadratic(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], t: float) -> tuple[float, float]:
    """Evaluates a 2D quadratic Bézier curve at parameter t in [0, 1]."""
    u = 1.0 - t
    x = u * u * p0[0] + 2.0 * u * t * p1[0] + t * t * p2[0]
    y = u * u * p0[1] + 2.0 * u * t * p1[1] + t * t * p2[1]
    return (x, y)


def bezier_cubic(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float], t: float) -> tuple[float, float]:
    """Evaluates a 2D cubic Bézier curve at parameter t in [0, 1]."""
    u = 1.0 - t
    u2 = u * u
    t2 = t * t
    x = u2 * u * p0[0] + 3.0 * u2 * t * p1[0] + 3.0 * u * t2 * p2[0] + t2 * t * p3[0]
    y = u2 * u * p0[1] + 3.0 * u2 * t * p1[1] + 3.0 * u * t2 * p2[1] + t2 * t * p3[1]
    return (x, y)


def ease_in_out(t: float) -> float:
    """Smooth hermite cubic interpolation easing: 3t^2 - 2t^3."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * max(0.0, min(1.0, t))


# ---------------------------------------------------------------------------
# 2. Image Processing Algorithms (IP)
# ---------------------------------------------------------------------------

def generate_gaussian_kernel_3x3(sigma: float = 1.0) -> list[list[float]]:
    """Generates a normalized 3x3 Gaussian convolution kernel for discrete smoothing."""
    kernel = [[0.0] * 3 for _ in range(3)]
    total = 0.0
    two_sig_sq = 2.0 * sigma * sigma
    for y in range(-1, 2):
        for x in range(-1, 2):
            val = math.exp(-(x * x + y * y) / two_sig_sq) / (math.pi * two_sig_sq)
            kernel[y + 1][x + 1] = val
            total += val
    # Normalize
    if total > 0.0:
        for y in range(3):
            for x in range(3):
                kernel[y][x] /= total
    return kernel


def apply_gaussian_blur(grid: list[list[int]], sigma: float = 1.0) -> list[list[int]]:
    """Convolves a 2D integer intensity grid with a 3x3 Gaussian smoothing kernel."""
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    if h < 3 or w < 3:
        return [row[:] for row in grid]

    kernel = generate_gaussian_kernel_3x3(sigma)
    out = [[0] * w for _ in range(h)]

    for y in range(h):
        for x in range(w):
            accum = 0.0
            for ky in range(-1, 2):
                ny = max(0, min(h - 1, y + ky))
                for kx in range(-1, 2):
                    nx = max(0, min(w - 1, x + kx))
                    accum += grid[ny][nx] * kernel[ky + 1][kx + 1]
            out[y][x] = max(0, min(255, int(round(accum))))
    return out


def apply_unsharp_mask(grid: list[list[int]], strength: float = 1.5, sigma: float = 1.0) -> list[list[int]]:
    """Applies unsharp masking: I_sharp = I + strength * (I - I_blur).

    Amplifies high-frequency spatial transitions (edges) by subtracting a blurred
    copy and adding the scaled residual back to the original image.
    """
    blurred = apply_gaussian_blur(grid, sigma=sigma)
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    out = [[0] * w for _ in range(h)]

    for y in range(h):
        for x in range(w):
            orig = grid[y][x]
            blur = blurred[y][x]
            detail = orig - blur
            sharpened = orig + strength * detail
            out[y][x] = max(0, min(255, int(round(sharpened))))
    return out


def compute_histogram(grid: list[list[int]]) -> list[int]:
    """Computes a 256-bin intensity histogram distribution for a 2D grayscale grid."""
    hist = [0] * 256
    for row in grid:
        for val in row:
            clamped = max(0, min(255, int(val)))
            hist[clamped] += 1
    return hist


def stretch_contrast(grid: list[list[int]], low_in: int = 40, high_in: int = 210) -> list[list[int]]:
    """Linearly stretches dynamic range from [low_in, high_in] to [0, 255]."""
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    out = [[0] * w for _ in range(h)]
    span = max(1, high_in - low_in)

    for y in range(h):
        for x in range(w):
            v = grid[y][x]
            stretched = ((v - low_in) * 255.0) / span
            out[y][x] = max(0, min(255, int(round(stretched))))
    return out


# ---------------------------------------------------------------------------
# 3. Memory Vault: Memory Restoration Console (Zone D)
# ---------------------------------------------------------------------------

# Canonical 16x16 glyph pattern for the Wing symbol (Lunar Path)
GLYPH_WING_16x16 = [
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 2, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 2, 3, 3, 3, 3, 2, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 2, 3, 3, 2, 2, 3, 3, 2, 1, 0, 0, 0, 0],
    [0, 1, 2, 3, 3, 2, 1, 1, 2, 3, 3, 2, 1, 0, 0, 0],
    [1, 2, 3, 3, 2, 1, 0, 0, 1, 2, 3, 3, 2, 1, 0, 0],
    [1, 3, 3, 2, 1, 0, 0, 0, 0, 1, 2, 3, 3, 1, 0, 0],
    [1, 3, 2, 1, 0, 0, 1, 1, 0, 0, 1, 2, 3, 1, 0, 0],
    [0, 1, 1, 0, 0, 1, 3, 3, 1, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 1, 3, 3, 3, 3, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 2, 3, 2, 2, 3, 2, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 2, 2, 1, 0, 0, 1, 2, 2, 1, 0, 0, 0, 0],
    [0, 1, 2, 1, 0, 0, 0, 0, 0, 0, 1, 2, 1, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

# Canonical 16x16 glyph pattern for the Sun symbol (Solar Path)
GLYPH_SUN_16x16 = [
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0],
    [0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0],
    [0, 0, 0, 1, 2, 3, 3, 3, 3, 3, 3, 2, 1, 0, 0, 0],
    [0, 0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 1, 0, 0],
    [0, 0, 1, 2, 3, 3, 1, 1, 1, 1, 3, 3, 2, 1, 0, 0],
    [1, 2, 1, 2, 3, 3, 1, 0, 0, 1, 3, 3, 2, 1, 2, 1],
    [1, 2, 1, 2, 3, 3, 1, 0, 0, 1, 3, 3, 2, 1, 2, 1],
    [0, 0, 1, 2, 3, 3, 1, 1, 1, 1, 3, 3, 2, 1, 0, 0],
    [0, 0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 1, 0, 0],
    [0, 0, 0, 1, 2, 3, 3, 3, 3, 3, 3, 2, 1, 0, 0, 0],
    [0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
]


class MemoryRestorationMachine:
    """Interactive modal machine for restoring corrupted crystal plates."""

    def __init__(self, screen_w: int = 800, screen_h: int = 600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open: bool = False
        self.current_memory_idx: int = 0  # 0: Wing (Lunar), 1: Sun (Solar)
        self.denoise_dial: int = 20       # 0 to 100
        self.sharpen_dial: int = 15       # 0 to 100
        self.selected_control: int = 0     # 0: Denoise, 1: Sharpen, 2: Switch Memory
        self.restored_flags: list[bool] = [False, False]
        self._generate_noisy_plates()

    def _generate_noisy_plates(self):
        """Builds noisy grid representations with deterministic pseudorandom noise."""
        self.base_grids = []
        self.noisy_grids = []
        glyph_maps = [GLYPH_WING_16x16, GLYPH_SUN_16x16]

        rng = random.Random(42)
        for gmap in glyph_maps:
            h = len(gmap)
            w = len(gmap[0])
            base = [[0] * w for _ in range(h)]
            noisy = [[0] * w for _ in range(h)]
            for y in range(h):
                for x in range(w):
                    val = int(gmap[y][x] * 75)
                    base[y][x] = val
                    # Add heavy salt-and-pepper and speckle noise
                    n_offset = rng.randint(-85, 85) if rng.random() < 0.65 else rng.choice([-140, 140])
                    noisy[y][x] = max(0, min(255, val + n_offset))
            self.base_grids.append(base)
            self.noisy_grids.append(noisy)

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def handle_keydown(self, key: int) -> bool:
        if not self.is_open:
            return False

        if key in (pygame.K_ESCAPE, pygame.K_SPACE):
            self.close()
            return True
        elif key in (pygame.K_UP, pygame.K_w):
            self.selected_control = (self.selected_control - 1) % 3
            return True
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.selected_control = (self.selected_control + 1) % 3
            return True
        elif key in (pygame.K_LEFT, pygame.K_a):
            if self.selected_control == 0:
                self.denoise_dial = max(0, self.denoise_dial - 5)
            elif self.selected_control == 1:
                self.sharpen_dial = max(0, self.sharpen_dial - 5)
            elif self.selected_control == 2:
                self.current_memory_idx = (self.current_memory_idx - 1) % 2
            self._check_restoration()
            return True
        elif key in (pygame.K_RIGHT, pygame.K_d):
            if self.selected_control == 0:
                self.denoise_dial = min(100, self.denoise_dial + 5)
            elif self.selected_control == 1:
                self.sharpen_dial = min(100, self.sharpen_dial + 5)
            elif self.selected_control == 2:
                self.current_memory_idx = (self.current_memory_idx + 1) % 2
            self._check_restoration()
            return True
        elif key in (pygame.K_TAB, pygame.K_1, pygame.K_2):
            self.current_memory_idx = 0 if key == pygame.K_1 else (1 if key == pygame.K_2 else (self.current_memory_idx + 1) % 2)
            self._check_restoration()
            return True
        return False

    def handle_click(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False
        # Clicking inside modal dismisses or selects controls
        bx = (self.screen_w - 680) // 2
        by = (self.screen_h - 480) // 2
        # Close button rect
        close_rect = pygame.Rect(bx + 680 - 40, by + 10, 30, 30)
        if close_rect.collidepoint(mx, my):
            self.close()
            return True
        return True

    def _check_restoration(self):
        """Checks if current dial values fall in the optimal restoration range."""
        # Denoise optimal: 45 to 70; Sharpen optimal: 40 to 65
        is_denoise_opt = 45 <= self.denoise_dial <= 70
        is_sharpen_opt = 40 <= self.sharpen_dial <= 65
        if is_denoise_opt and is_sharpen_opt:
            self.restored_flags[self.current_memory_idx] = True

    def get_processed_grid(self) -> list[list[int]]:
        """Processes the noisy grid using the active dial parameters."""
        raw = self.noisy_grids[self.current_memory_idx]
        # 1. Blur strength proportional to denoise dial
        blur_sigma = 0.3 + (self.denoise_dial / 100.0) * 1.8
        blurred = apply_gaussian_blur(raw, sigma=blur_sigma)
        # 2. Sharpen strength proportional to sharpen dial
        sharp_strength = (self.sharpen_dial / 100.0) * 2.8
        processed = apply_unsharp_mask(blurred, strength=sharp_strength, sigma=0.8)
        return processed

    def draw(self, surface: pygame.Surface):
        if not self.is_open:
            return

        dim = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        dim.fill((6, 4, 10, 215))
        surface.blit(dim, (0, 0))

        # Compact dialog bounds (410px height fits easily within 600px screen with 95px safety margins)
        mw, mh = 660, 410
        mx = (self.screen_w - mw) // 2
        my = (self.screen_h - mh) // 2

        # Tablet Frame
        panel = pygame.Surface((mw, mh), pygame.SRCALPHA)
        panel.fill((20, 16, 28, 252))
        pygame.draw.rect(panel, (160, 210, 255), (0, 0, mw, mh), width=2, border_radius=8)
        pygame.draw.rect(panel, (60, 95, 135), (4, 4, mw - 8, mh - 8), width=1, border_radius=6)
        surface.blit(panel, (mx, my))

        f_title = pygame.font.SysFont("georgia", 15, bold=True)
        f_sub = pygame.font.SysFont("consolas", 10)
        f_val = pygame.font.SysFont("consolas", 11, bold=True)

        # Title
        t_surf = f_title.render("MEMORY VAULT - VISUAL SIGNAL RESTORATION", True, (200, 235, 255))
        surface.blit(t_surf, (mx + 24, my + 14))
        pygame.draw.line(surface, (80, 130, 180), (mx + 24, my + 36), (mx + mw - 24, my + 36), 1)

        # Left Column: Restored Visual Plate Display (16x16 scaled cleanly to 160x160)
        plate_x = mx + 24
        plate_y = my + 46
        scale = 10
        grid = self.get_processed_grid()

        # Canvas frame
        pygame.draw.rect(surface, (12, 10, 16), (plate_x - 3, plate_y - 3, 16 * scale + 6, 16 * scale + 6), border_radius=4)
        pygame.draw.rect(surface, (110, 165, 215), (plate_x - 3, plate_y - 3, 16 * scale + 6, 16 * scale + 6), width=2, border_radius=4)

        for py in range(16):
            for px in range(16):
                val = grid[py][px]
                # Tone map to temple spectral blue
                col = (int(val * 0.7), int(val * 0.9), val)
                pygame.draw.rect(surface, col, (plate_x + px * scale, plate_y + py * scale, scale, scale))

        # Status badge below canvas
        is_restored = self.restored_flags[self.current_memory_idx]
        st_text = "SIGNAL RESTORED: GLYPH COHERENT" if is_restored else "SIGNAL CORRUPTED: ADJUST FILTERS"
        st_col = (110, 245, 160) if is_restored else (245, 140, 100)
        st_surf = f_val.render(st_text, True, st_col)
        surface.blit(st_surf, (plate_x, plate_y + 16 * scale + 8))

        algo_surf = f_sub.render("Image Processing: 2D Gaussian + High-Pass", True, (135, 160, 190))
        surface.blit(algo_surf, (plate_x, plate_y + 16 * scale + 24))

        # Right Column: Controls & Story Clue
        ctrl_x = mx + 205
        curr_y = my + 46

        # Memory Plate Selector
        c2_col = (255, 235, 140) if self.selected_control == 2 else (175, 185, 205)
        p_name = "MEMORY FRAGMENT 01: LUNAR WING" if self.current_memory_idx == 0 else "MEMORY FRAGMENT 02: SOLAR SUN"
        p_surf = f_val.render(f"[< A / D >] {p_name}", True, c2_col)
        surface.blit(p_surf, (ctrl_x, curr_y))
        curr_y += 24

        # Slider 1: Denoise Filter (Gaussian Blur)
        c0_col = (255, 235, 140) if self.selected_control == 0 else (175, 185, 205)
        d_lbl = f_val.render(f"1. Denoise Filter (Gaussian Smoothing): {self.denoise_dial}%", True, c0_col)
        surface.blit(d_lbl, (ctrl_x, curr_y))
        curr_y += 16
        # Slider Bar
        pygame.draw.rect(surface, (30, 25, 40), (ctrl_x, curr_y, 420, 9), border_radius=3)
        pygame.draw.rect(surface, (70, 140, 230), (ctrl_x, curr_y, int(420 * (self.denoise_dial / 100.0)), 9), border_radius=3)
        # Optimal zone marker
        pygame.draw.rect(surface, (100, 240, 150), (ctrl_x + int(420 * 0.45), curr_y, int(420 * 0.25), 9), width=1)
        curr_y += 20

        # Slider 2: Sharpen Filter (Unsharp Masking)
        c1_col = (255, 235, 140) if self.selected_control == 1 else (175, 185, 205)
        s_lbl = f_val.render(f"2. Boundary Sharpening (High-Pass Detail): {self.sharpen_dial}%", True, c1_col)
        surface.blit(s_lbl, (ctrl_x, curr_y))
        curr_y += 16
        # Slider Bar
        pygame.draw.rect(surface, (30, 25, 40), (ctrl_x, curr_y, 420, 9), border_radius=3)
        pygame.draw.rect(surface, (230, 140, 70), (ctrl_x, curr_y, int(420 * (self.sharpen_dial / 100.0)), 9), border_radius=3)
        # Optimal zone marker
        pygame.draw.rect(surface, (100, 240, 150), (ctrl_x + int(420 * 0.40), curr_y, int(420 * 0.25), 9), width=1)
        curr_y += 24

        # Story & Harmonic Clue Revealed (Sleek container with ample text room)
        box_w, box_h = 430, 180
        pygame.draw.rect(surface, (14, 12, 20), (ctrl_x, curr_y, box_w, box_h), border_radius=6)
        pygame.draw.rect(surface, (65, 85, 115), (ctrl_x, curr_y, box_w, box_h), width=1, border_radius=6)

        if is_restored:
            if self.current_memory_idx == 0:
                clue_txt = (
                    "HARMONIC RECORD DECODED - LUNAR HARMONY:\n\n"
                    "The restored plate depicts a Silver Key bearing the Wing Glyph. "
                    "In ancient days, this key focused light through the Emerald Reflector (Green) "
                    "into Resonance Crystal I."
                )
            else:
                clue_txt = (
                    "HARMONIC RECORD DECODED - SOLAR HARMONY:\n\n"
                    "The restored plate depicts a Sacred Gold Key bearing the Sun Glyph. "
                    "It focused celestial light through the Azure Reflector (Blue) "
                    "into Resonance Crystal III."
                )
            clue_col = (215, 240, 255)
        else:
            clue_txt = (
                "Corrupted visual memory plate.\n\n"
                "Balance Gaussian smoothing to suppress mineral noise, then apply "
                "unsharp masking to reconstruct genuine edge boundaries. "
                "Target the green calibration brackets."
            )
            clue_col = (155, 145, 165)

        lines = wrap_text(clue_txt, f_sub, box_w - 24)
        ly = curr_y + 10
        for ln in lines:
            surface.blit(f_sub.render(ln, True, clue_col), (ctrl_x + 12, ly))
            ly += 15

        # Footer
        foot_txt = "[W/S] Select Filter  |  [A/D] Adjust Dial  |  [TAB] Next Plate  |  [ESC] Close"
        foot_s = f_sub.render(foot_txt, True, (160, 175, 195))
        surface.blit(foot_s, (mx + (mw - foot_s.get_width()) // 2, my + mh - 24))


# ---------------------------------------------------------------------------
# 4. Optical Gallery: Channel Prism Machine (Zone C)
# ---------------------------------------------------------------------------

class OpticalPrismMachine:
    """Interactive modal machine for separating and inspecting light frequency channels."""

    def __init__(self, screen_w: int = 800, screen_h: int = 600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open: bool = False
        self.channel_mode: str = "ALL"  # "ALL", "RED", "GREEN", "BLUE"
        self.frequency_bands: int = 2   # 1 to 4
        self.intensity: int = 80        # 10 to 100
        self.selected_control: int = 0  # 0: Channel, 1: Bands, 2: Intensity

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def handle_keydown(self, key: int) -> bool:
        if not self.is_open:
            return False

        if key in (pygame.K_ESCAPE, pygame.K_SPACE):
            self.close()
            return True
        elif key in (pygame.K_UP, pygame.K_w):
            self.selected_control = (self.selected_control - 1) % 3
            return True
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.selected_control = (self.selected_control + 1) % 3
            return True
        elif key in (pygame.K_LEFT, pygame.K_a):
            if self.selected_control == 0:
                channels = ["ALL", "RED", "GREEN", "BLUE"]
                idx = (channels.index(self.channel_mode) - 1) % 4
                self.channel_mode = channels[idx]
            elif self.selected_control == 1:
                self.frequency_bands = max(1, self.frequency_bands - 1)
            elif self.selected_control == 2:
                self.intensity = max(10, self.intensity - 10)
            return True
        elif key in (pygame.K_RIGHT, pygame.K_d):
            if self.selected_control == 0:
                channels = ["ALL", "RED", "GREEN", "BLUE"]
                idx = (channels.index(self.channel_mode) + 1) % 4
                self.channel_mode = channels[idx]
            elif self.selected_control == 1:
                self.frequency_bands = min(4, self.frequency_bands + 1)
            elif self.selected_control == 2:
                self.intensity = min(100, self.intensity + 10)
            return True
        return False

    def draw(self, surface: pygame.Surface):
        if not self.is_open:
            return

        dim = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        dim.fill((6, 4, 10, 215))
        surface.blit(dim, (0, 0))

        # Compact dialog bounds (410px height fits easily within 600px screen with 95px safety margins)
        mw, mh = 660, 410
        mx = (self.screen_w - mw) // 2
        my = (self.screen_h - mh) // 2

        panel = pygame.Surface((mw, mh), pygame.SRCALPHA)
        panel.fill((20, 16, 28, 252))
        pygame.draw.rect(panel, (180, 140, 240), (0, 0, mw, mh), width=2, border_radius=8)
        pygame.draw.rect(panel, (90, 65, 135), (4, 4, mw - 8, mh - 8), width=1, border_radius=6)
        surface.blit(panel, (mx, my))

        f_title = pygame.font.SysFont("georgia", 15, bold=True)
        f_sub = pygame.font.SysFont("consolas", 10)
        f_val = pygame.font.SysFont("consolas", 11, bold=True)

        t_surf = f_title.render("OPTICAL GALLERY - CHANNEL PRISM & WAVELENGTH TRANSFORM", True, (230, 215, 255))
        surface.blit(t_surf, (mx + 24, my + 14))
        pygame.draw.line(surface, (120, 85, 175), (mx + 24, my + 36), (mx + mw - 24, my + 36), 1)

        # Left Column: Interactive Optical Projection Canvas (230x230)
        proj_x = mx + 24
        proj_y = my + 46
        pw, ph = 230, 230
        pygame.draw.rect(surface, (10, 8, 16), (proj_x, proj_y, pw, ph), border_radius=6)
        pygame.draw.rect(surface, (140, 105, 210), (proj_x, proj_y, pw, ph), width=2, border_radius=6)

        # Clip rendering strictly inside the prism preview canvas so rays never escape
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(proj_x + 2, proj_y + 2, pw - 4, ph - 4))

        cy = proj_y + ph // 2
        # Draw incoming beam to prism
        pygame.draw.line(surface, (255, 255, 240), (proj_x + 8, cy), (proj_x + 55, cy), 3)

        # Draw triangular crystal prism
        pts = [(proj_x + 55, cy + 30), (proj_x + 90, cy), (proj_x + 55, cy - 30)]
        pygame.draw.polygon(surface, (40, 32, 60), pts)
        pygame.draw.polygon(surface, (190, 160, 255), pts, 2)

        # Projected spectral bands exiting prism (constrained strictly within [proj_x + 115, proj_x + pw - 24])
        channel_colors = {
            "ALL": [(235, 75, 75), (70, 225, 110), (65, 145, 250)],
            "RED": [(235, 75, 75)],
            "GREEN": [(70, 225, 110)],
            "BLUE": [(65, 145, 250)],
        }
        active_cols = channel_colors.get(self.channel_mode, channel_colors["ALL"])
        start_x = proj_x + 115
        end_x = proj_x + pw - 24

        for idx, col in enumerate(active_cols):
            spread_y = cy - 32 + (idx + 1) * (64 // (len(active_cols) + 1))
            for b in range(self.frequency_bands):
                bx = start_x + int(b * ((end_x - start_x) / 3.0))
                pygame.draw.line(surface, col, (proj_x + 80, cy), (bx, spread_y), 2)
                pygame.draw.circle(surface, col, (bx, spread_y), 3 + b)

        surface.set_clip(old_clip)

        # Subtitle below canvas
        cg_surf = f_sub.render("Computer Graphics: Refraction & Dispersion", True, (155, 135, 185))
        surface.blit(cg_surf, (proj_x + 4, proj_y + ph + 8))

        # Right Column: Controls & Guidance
        ctrl_x = mx + 275
        curr_y = my + 46

        # Channel selector
        c0_col = (255, 235, 140) if self.selected_control == 0 else (175, 185, 205)
        c_lbl = f_val.render(f"1. Color-Space Channel: < {self.channel_mode} >", True, c0_col)
        surface.blit(c_lbl, (ctrl_x, curr_y))
        curr_y += 24

        # Frequency bands
        c1_col = (255, 235, 140) if self.selected_control == 1 else (175, 185, 205)
        f_lbl = f_val.render(f"2. Resonance Bands: < {self.frequency_bands} Bands >", True, c1_col)
        surface.blit(f_lbl, (ctrl_x, curr_y))
        curr_y += 24

        # Beam intensity
        c2_col = (255, 235, 140) if self.selected_control == 2 else (175, 185, 205)
        i_lbl = f_val.render(f"3. Beam Intensity / Gain: < {self.intensity}% >", True, c2_col)
        surface.blit(i_lbl, (ctrl_x, curr_y))
        curr_y += 30

        # Optical Guidance Box
        box_w, box_h = 360, 180
        pygame.draw.rect(surface, (14, 12, 20), (ctrl_x, curr_y, box_w, box_h), border_radius=6)
        pygame.draw.rect(surface, (95, 75, 135), (ctrl_x, curr_y, box_w, box_h), width=1, border_radius=6)

        if self.channel_mode == "BLUE":
            obs_txt = (
                "AZURE CHANNEL ISOLATED:\n\n"
                "The 450nm wavelength produces 2 harmonic interference nodes. "
                "Harmonizes with the Silver Keyway and Crystal II."
            )
        elif self.channel_mode == "GREEN":
            obs_txt = (
                "EMERALD CHANNEL ISOLATED:\n\n"
                "The 530nm wavelength focuses coherent ray alignment. "
                "Harmonizes with the Sacred Gold Keyway and Crystal III."
            )
        elif self.channel_mode == "RED":
            obs_txt = (
                "CRIMSON CHANNEL ISOLATED:\n\n"
                "Thermal dissipation without coherent fringe stability. "
                "Belongs to the corrupted bronze path."
            )
        else:
            obs_txt = (
                "FULL SPECTRUM DECOMPOSITION:\n\n"
                "Light separates into discrete chromatic channels. "
                "Examine Azure (450nm) and Emerald (530nm) channels to discover "
                "which relics resonate across the spectrum."
            )

        lines = wrap_text(obs_txt, f_sub, box_w - 24)
        ly = curr_y + 10
        for ln in lines:
            surface.blit(f_sub.render(ln, True, (225, 215, 245)), (ctrl_x + 12, ly))
            ly += 15

        # Footer
        foot_txt = "[W/S] Select Control  |  [A/D] Change Channel/Band  |  [ESC] Close"
        foot_s = f_sub.render(foot_txt, True, (175, 160, 205))
        surface.blit(foot_s, (mx + (mw - foot_s.get_width()) // 2, my + mh - 24))

# ---------------------------------------------------------------------------
# 5. Dynamic Core: State Machine & Stabilization
# ---------------------------------------------------------------------------

class CoreStabilizerMachine:
    """Stage 3 Final Core Stabilization alignment sequence."""

    def __init__(self, screen_w: int = 800, screen_h: int = 600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open: bool = False
        self.ring_angle: float = 0.0          # Player controlled angle
        self.target_angle: float = 180.0       # Harmonic sweet spot
        self.resonance_hold: float = 0.0       # Must hold within ±15 degrees for 2.0s
        self.is_stabilized: bool = False
        self.on_success = None

    def open(self):
        self.is_open = True
        self.ring_angle = 45.0
        self.resonance_hold = 0.0
        self.is_stabilized = False

    def close(self):
        self.is_open = False

    def update(self, dt: float):
        if not self.is_open or self.is_stabilized:
            return

        diff = abs((self.ring_angle - self.target_angle + 180) % 360 - 180)
        if diff < 16.0:
            self.resonance_hold += dt
            if self.resonance_hold >= 1.8:
                self.is_stabilized = True
                self.close()
                if self.on_success:
                    self.on_success()
        else:
            self.resonance_hold = max(0.0, self.resonance_hold - dt * 1.5)

    def handle_keydown(self, key: int) -> bool:
        if not self.is_open:
            return False

        if key in (pygame.K_ESCAPE, pygame.K_SPACE) and self.is_stabilized:
            self.close()
            return True
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.ring_angle = (self.ring_angle - 8.0) % 360.0
            return True
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.ring_angle = (self.ring_angle + 8.0) % 360.0
            return True
        return False

    def draw(self, surface: pygame.Surface):
        if not self.is_open:
            return

        dim = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        dim.fill((6, 4, 10, 215))
        surface.blit(dim, (0, 0))

        mw, mh = 640, 440
        mx = (self.screen_w - mw) // 2
        my = (self.screen_h - mh) // 2

        panel = pygame.Surface((mw, mh), pygame.SRCALPHA)
        panel.fill((22, 18, 28, 252))
        pygame.draw.rect(panel, (240, 190, 80), (0, 0, mw, mh), width=2, border_radius=8)
        surface.blit(panel, (mx, my))

        f_title = pygame.font.SysFont("georgia", 16, bold=True)
        f_sub = pygame.font.SysFont("consolas", 11)
        f_val = pygame.font.SysFont("consolas", 12, bold=True)

        t_surf = f_title.render("FORGE CORE STABILIZATION APPARATUS", True, (250, 225, 140))
        surface.blit(t_surf, (mx + 28, my + 18))
        pygame.draw.line(surface, (160, 120, 50), (mx + 28, my + 44), (mx + mw - 28, my + 44), 1)

        # Central Rotating Rings
        cx = mx + mw // 2
        cy = my + 180

        # Outer target ring
        pygame.draw.circle(surface, (45, 38, 55), (cx, cy), 90, width=8)
        # Target alignment notches
        t_rad = math.radians(self.target_angle)
        tx = cx + int(90 * math.cos(t_rad))
        ty = cy + int(90 * math.sin(t_rad))
        pygame.draw.circle(surface, (100, 240, 160), (tx, ty), 8)

        # Player rotating ring
        r_rad = math.radians(self.ring_angle)
        rx = cx + int(90 * math.cos(r_rad))
        ry = cy + int(90 * math.sin(r_rad))
        ring_col = (110, 240, 160) if self.resonance_hold > 0.5 else (245, 195, 75)
        pygame.draw.circle(surface, ring_col, (rx, ry), 10)
        pygame.draw.line(surface, ring_col, (cx, cy), (rx, ry), 2)

        # Core crucible center
        pygame.draw.circle(surface, (230, 140, 45), (cx, cy), 22)
        pygame.draw.circle(surface, (255, 240, 180), (cx, cy), 8)

        # Hold Progress Bar
        bar_w = 300
        bar_x = cx - bar_w // 2
        bar_y = cy + 115
        pygame.draw.rect(surface, (30, 24, 38), (bar_x, bar_y, bar_w, 14), border_radius=4)
        progress = min(1.0, self.resonance_hold / 1.8)
        pygame.draw.rect(surface, (100, 235, 160), (bar_x, bar_y, int(bar_w * progress), 14), border_radius=4)
        pygame.draw.rect(surface, (170, 135, 60), (bar_x, bar_y, bar_w, 14), width=1, border_radius=4)

        if self.is_stabilized:
            stat_msg = "FORGE CORE HARMONIZED — CELESTIAL STABILITY ATTAINED!"
            stat_col = (110, 255, 175)
        else:
            stat_msg = f"ALIGN THE RUNIC CONDUIT: {int(progress * 100)}%"
            stat_col = (245, 215, 135)
        s_surf = f_val.render(stat_msg, True, stat_col)
        surface.blit(s_surf, (cx - s_surf.get_width() // 2, bar_y + 24))

        foot_txt = "[A/D] Rotate Runic Conduit  |  Align with the emerald resonance node  |  [ESC] Close"
        foot_s = f_sub.render(foot_txt, True, (190, 175, 145))
        surface.blit(foot_s, (mx + (mw - foot_s.get_width()) // 2, my + mh - 26))


# ---------------------------------------------------------------------------
# 6. Forge Journal Modal System
# ---------------------------------------------------------------------------

class ForgeJournalModal:
    """The Ancient Forge Journal: tracks discoveries, restored memories, paths, and CG/IP concepts."""

    def __init__(self, screen_w: int = 800, screen_h: int = 600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open: bool = False
        self.active_tab: int = 0  # 0: Discoveries, 1: Memories, 2: Harmonic Paths, 3: CG & IP Principles
        self.scroll_y: int = 0
        self.max_scroll: int = 0
        self.tab_titles = ["DISCOVERIES", "MEMORIES", "HARMONIC PATHS"]

    def open(self, tab: int = 0):
        self.is_open = True
        self.active_tab = tab
        self.scroll_y = 0
        self.max_scroll = 0

    def close(self):
        self.is_open = False

    def handle_keydown(self, key: int) -> bool:
        if not self.is_open:
            return False

        if key in (pygame.K_ESCAPE, pygame.K_j, pygame.K_SPACE):
            self.close()
            return True
        elif key in (pygame.K_TAB, pygame.K_RIGHT, pygame.K_d):
            self.active_tab = (self.active_tab + 1) % len(self.tab_titles)
            self.scroll_y = 0
            return True
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.active_tab = (self.active_tab - 1) % len(self.tab_titles)
            self.scroll_y = 0
            return True
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3):
            self.active_tab = key - pygame.K_1
            self.scroll_y = 0
            return True
        elif key in (pygame.K_UP, pygame.K_w):
            self.scroll_y = max(0, self.scroll_y - 24)
            return True
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.scroll_y = min(self.max_scroll, self.scroll_y + 24)
            return True
        return False

    def handle_scroll(self, dy: int) -> bool:
        """Handles mouse wheel scrolling."""
        if not self.is_open:
            return False
        self.scroll_y = max(0, min(self.max_scroll, self.scroll_y + dy * 24))
        return True

    def handle_click(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False
        mw = 700
        mh = 440 if self.screen_h <= 550 else 500
        bx = (self.screen_w - mw) // 2
        by = (self.screen_h - mh) // 2

        # Tab bar clicks
        tab_w = 200
        tab_spacing = 15
        for i in range(len(self.tab_titles)):
            tx = bx + 35 + i * (tab_w + tab_spacing)
            if pygame.Rect(tx, by + 40, tab_w, 32).collidepoint(mx, my):
                self.active_tab = i
                self.scroll_y = 0
                return True

        # Close button
        if pygame.Rect(bx + mw - 38, by + 10, 30, 30).collidepoint(mx, my):
            self.close()
            return True

        # Content plinth scrollbar track click
        content_rect = pygame.Rect(bx + 30, by + 78, mw - 60, mh - 114)
        if self.max_scroll > 0 and pygame.Rect(content_rect.right - 14, content_rect.top, 14, content_rect.height).collidepoint(mx, my):
            track_y = content_rect.top + 8
            track_h = content_rect.height - 16
            click_ratio = max(0.0, min(1.0, (my - track_y) / track_h))
            self.scroll_y = int(click_ratio * self.max_scroll)
            return True
        return True

    def draw(self, surface: pygame.Surface, level4_room):
        if not self.is_open:
            return

        dim = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        dim.fill((8, 6, 12, 248))
        surface.blit(dim, (0, 0))

        mw = 700
        mh = 440 if self.screen_h <= 550 else 500
        mx = (self.screen_w - mw) // 2
        my = (self.screen_h - mh) // 2

        # Outer Tablet Surface
        panel = pygame.Surface((mw, mh), pygame.SRCALPHA)
        panel.fill((16, 12, 20, 252))
        surface.blit(panel, (mx, my))

        # Restrained primary border and inner hairline with gold rosettes
        pygame.draw.rect(surface, (185, 145, 75), (mx, my, mw, mh), width=2, border_radius=8)
        pygame.draw.rect(surface, (70, 55, 38), (mx + 4, my + 4, mw - 8, mh - 8), width=1, border_radius=6)

        # Corner quadrant studs with central jewel pips
        c_len = 10
        c_col = (220, 185, 95)
        for cx_c, cy_c, dx, dy in [
            (mx + 6, my + 6, 1, 1),
            (mx + mw - 6, my + 6, -1, 1),
            (mx + 6, my + mh - 6, 1, -1),
            (mx + mw - 6, my + mh - 6, -1, -1),
        ]:
            pygame.draw.line(surface, c_col, (cx_c, cy_c), (cx_c + dx * c_len, cy_c), 2)
            pygame.draw.line(surface, c_col, (cx_c, cy_c), (cx_c + dx * c_len, cy_c + dy * c_len), 2)
            pygame.draw.circle(surface, (255, 235, 140), (cx_c + dx * 2, cy_c + dy * 2), 2)

        f_title = pygame.font.SysFont("georgia", 15, bold=True)
        f_tab = pygame.font.SysFont("consolas", 10, bold=True)
        f_body = pygame.font.SysFont("consolas", 11)
        f_bold = pygame.font.SysFont("consolas", 11, bold=True)

        # Header Title with subtle wing ornament lines
        t_surf = f_title.render("THE FORGE JOURNAL — CHRONICLES OF LIGHT", True, (248, 224, 148))
        tcx = mx + (mw - t_surf.get_width()) // 2
        surface.blit(t_surf, (tcx, my + 14))
        pygame.draw.line(surface, (140, 110, 55), (mx + 35, my + 23), (tcx - 14, my + 23), 1)
        pygame.draw.line(surface, (140, 110, 55), (tcx + t_surf.get_width() + 14, my + 23), (mx + mw - 45, my + 23), 1)

        # Close [X] Button (top right)
        close_rect = pygame.Rect(mx + mw - 34, my + 12, 22, 22)
        pygame.draw.rect(surface, (28, 22, 34), close_rect, border_radius=4)
        pygame.draw.rect(surface, (150, 120, 65), close_rect, width=1, border_radius=4)
        x_lbl = f_tab.render("X", True, (240, 215, 140))
        surface.blit(x_lbl, (close_rect.x + (close_rect.width - x_lbl.get_width()) // 2, close_rect.y + 4))

        # Tabs Bar with active bookmarks
        tab_w = 200
        tab_spacing = 15
        for i, title in enumerate(self.tab_titles):
            tx = mx + 35 + i * (tab_w + tab_spacing)
            ty = my + 44
            is_active = (i == self.active_tab)
            t_col = (42, 32, 52) if is_active else (22, 17, 26)
            b_col = (235, 195, 85) if is_active else (70, 56, 40)
            txt_col = (255, 235, 180) if is_active else (160, 148, 130)

            pygame.draw.rect(surface, t_col, (tx, ty, tab_w, 26), border_top_left_radius=4, border_top_right_radius=4)
            pygame.draw.rect(surface, b_col, (tx, ty, tab_w, 26), width=1, border_top_left_radius=4, border_top_right_radius=4)
            if is_active:
                # Active tab gold highlight baseline
                pygame.draw.line(surface, (255, 225, 120), (tx + 2, ty + 25), (tx + tab_w - 2, ty + 25), 2)
                # Active pip
                pygame.draw.circle(surface, (245, 215, 110), (tx + 12, ty + 13), 3)

            lbl = f_tab.render(title, True, txt_col)
            surface.blit(lbl, (tx + (tab_w - lbl.get_width()) // 2 + (4 if is_active else 0), ty + 6))

        # Content Plinth: dark parchment / slate tablet
        content_rect = pygame.Rect(mx + 30, my + 74, mw - 60, mh - 108)
        pygame.draw.rect(surface, (13, 10, 16), content_rect, border_radius=6)
        pygame.draw.rect(surface, (90, 72, 48), content_rect, width=1, border_radius=6)

        raw_items = []
        if self.active_tab == 0:
            b_relic = getattr(level4_room, "broken_relic_solved", False) if level4_room else False
            m_frag = getattr(level4_room, "memory_fragments_solved", False) if level4_room else False
            a_blue = getattr(level4_room, "ancient_blueprint_solved", False) if level4_room else False
            a_rule = getattr(level4_room, "ancient_rule_discovered", False) if level4_room else False

            relic_st = '[RESTORED] "The Crimson Mirror was shattered in the cataclysm; red light cannot focus resonance through any crystal."' if b_relic else "[UNDISCOVERED] Station at Western Alcove"
            mem_st = '[RESTORED] "The Bronze Key fractured during the First Trial; the first rank cannot sustain Crucible resonance."' if m_frag else "[UNDISCOVERED] Station at Eastern Archive"
            blue_st = '[RESTORED] "The sacred blueprint confirms: The Crimson conduit is permanently severed; only Azure and Emerald paths are active."' if a_blue else "[UNDISCOVERED] Station at Southern Dais"
            rule_st = '[DISCOVERED] "A key and crystal must share the same rank. The second path bears blue; the third wears green."' if a_rule else "[UNDISCOVERED] Northern Dais Wall"

            raw_items = [
                ("THE ANCIENT FORGE — INVESTIGATION LOG", True, (248, 224, 148)),
                ("The Crucible requires three matching relics: one Key, one Mirror, and one Crystal.", False, (225, 220, 210)),
                ("Decipher discovered evidence across the temple to isolate the valid harmonic awakenings.", False, (200, 195, 185)),
                ("", False, (0, 0, 0)),
                ("MINI-PUZZLE STATIONS & DISCOVERIES", True, (130, 225, 160)),
                ("• West: Broken Relic (Geometric Reconstruction)", True, (240, 200, 110)),
                (f"  {relic_st}", False, (100, 230, 150) if b_relic else (175, 170, 165)),
                ("• East: Memory Fragments (Median Filter Denoising)", True, (120, 200, 255)),
                (f"  {mem_st}", False, (100, 230, 150) if m_frag else (175, 170, 165)),
                ("• South: Ancient Blueprint (Texture Mapping Alignment)", True, (255, 180, 100)),
                (f"  {blue_st}", False, (100, 230, 150) if a_blue else (175, 170, 165)),
                ("• North: Ancient Rule (Path Inscription Ingot)", True, (255, 225, 120)),
                (f"  {rule_st}", False, (100, 230, 150) if a_rule else (175, 170, 165)),
            ]
        elif self.active_tab == 1:
            raw_items = [
                ("TEMPLE ARCHIVES & CHRONICLES OF LIGHT", True, (248, 224, 148)),
                ("Ancient chronicles record the lost history of the Ancient Forge and its sacred fires:", False, (220, 215, 205)),
                ("", False, (0, 0, 0)),
                ("CHRONICLE I: THE ARCHITECTS' CREED", True, (140, 210, 255)),
                ('"Light is neither created nor destroyed in the Crucible; it only aligns with its true twin.', False, (215, 210, 200)),
                ("When Key and Crystal resonate at equal rank, the optical mirror focuses the conduit.", False, (215, 210, 200)),
                ('A mismatch of wavelength causes the energy to simply fade away into the stone."', False, (215, 210, 200)),
                ("", False, (0, 0, 0)),
                ("CHRONICLE II: THE SHATTERING OF CRIMSON", True, (245, 130, 110)),
                ('"During the Great Quake, the Crimson Reflector shattered into broken pieces.', False, (230, 205, 195)),
                ("Its light could no longer focus through any of the three crystals.", False, (230, 205, 195)),
                ('The Ancients sealed the red focusing chamber and turned exclusively to the cooler spectra."', False, (230, 205, 195)),
                ("", False, (0, 0, 0)),
                ("CHRONICLE III: THE TWO AWAKENINGS", True, (255, 220, 130)),
                ('"Two distinct paths were laid for future seekers: the quiet path of the Moon,', False, (240, 230, 210)),
                ("and the blazing path of the Sun. Each demands its own attuned metal and mirror color.", False, (240, 230, 210)),
                ('One cannot cross the streams, or the fire will go out."', False, (240, 230, 210)),
            ]
        elif self.active_tab == 2:
            b_relic = getattr(level4_room, "broken_relic_solved", False) if level4_room else False
            m_frag = getattr(level4_room, "memory_fragments_solved", False) if level4_room else False
            a_blue = getattr(level4_room, "ancient_blueprint_solved", False) if level4_room else False
            a_rule = getattr(level4_room, "ancient_rule_discovered", False) if level4_room else False
            forge_engine = getattr(level4_room, "forge_engine", None)
            is_solved = getattr(forge_engine, "is_solved", False) if forge_engine else False

            # Deduction statuses for Candidates A, B, C, D
            if is_solved:
                cand_a_status = "AWAKENED & PROVEN: Lunar Harmony active at the Crucible!"
                cand_b_status = "ELIMINATED BY RULE: Path color mismatch (Rank 2 requires Blue, not Green)"
                cand_c_status = "ELIMINATED BY RULE: Path color mismatch (Rank 3 requires Green, not Blue)"
                cand_d_status = "AWAKENED & PROVEN: Solar Harmony active at the Crucible!"
            elif a_rule:
                cand_a_status = "POSSIBLE — Rank 2 matches Crystal 2; Second Path aligns with Blue mirror. Ready for Crucible trial."
                cand_b_status = "ELIMINATED BY RULE: Path color mismatch — Rank 2 requires Blue (second path), not Green."
                cand_c_status = "ELIMINATED BY RULE: Path color mismatch — Rank 3 requires Green (third path), not Blue."
                cand_d_status = "POSSIBLE — Rank 3 matches Crystal 3; Third Path aligns with Green mirror. Ready for Crucible trial."
            else:
                cand_a_status = "POSSIBLE — Under investigation: Silver Key + Blue Mirror + Crystal 2"
                cand_b_status = "POSSIBLE — Under investigation: Silver Key + Green Mirror + Crystal 2"
                cand_c_status = "POSSIBLE — Under investigation: Gold Key + Blue Mirror + Crystal 3"
                cand_d_status = "POSSIBLE — Under investigation: Gold Key + Green Mirror + Crystal 3"

            crimson_unlocked = b_relic or a_blue

            raw_items = [
                ("THE FORGE DEDUCTION — HARMONIC PATHWAYS", True, (248, 224, 148)),
                ("The Crucible has 27 possible combinations (3 Keys × 3 Mirrors × 3 Crystals).", False, (220, 215, 205)),
                ("Decipher discovered evidence to eliminate flawed conduits and awaken the core.", False, (220, 215, 205)),
                ("", False, (0, 0, 0)),
                ("THE DEDUCTION PROGRESSION (27 -> 9 -> 6 -> 4 -> 2):", True, (130, 225, 160)),
                ("1. Step 1 [27 -> 9]: Ancient Rule (Matching Ranks)", True, (245, 225, 140) if a_rule else (175, 170, 165)),
                ("   Why 27 becomes 9: The Ancient Rule requires key and crystal to share rank (Bronze I, Silver II, Gold III). Eliminates all 18 cross-rank pairings.", False, (210, 210, 210) if a_rule else (160, 155, 150)),
                ("2. Step 2 [9 -> 6]: Mirror Restriction (Crimson Reflector)", True, (245, 200, 110) if crimson_unlocked else (175, 170, 165)),
                ("   Why 9 becomes 6: Discovered clues (Broken Relic / Blueprint) prove the Crimson Mirror is shattered and its conduit severed. Eliminates all 3 Crimson combinations (Bronze+Red+1, Silver+Red+2, Gold+Red+3).", False, (210, 210, 210) if crimson_unlocked else (160, 155, 150)),
                ("3. Step 3 [6 -> 4]: Key Restriction (Bronze Dissipation)", True, (140, 210, 255) if m_frag else (175, 170, 165)),
                ("   Why 6 becomes 4: Discovered archive (Memory Fragments) proves the Bronze Key fractured under trial and cannot sustain resonance. Eliminates both remaining Bronze paths (Bronze+Blue+1, Bronze+Green+1). Exactly 4 candidates remain.", False, (210, 210, 210) if m_frag else (160, 155, 150)),
                ("4. Step 4 [4 -> 2]: Path Color Rule (Second Path Blue, Third Path Green)", True, (130, 240, 150) if a_rule else (175, 170, 165)),
                ("   Why only A and D satisfy the rule: The Ancient Rule dictates the second path (Rank 2) bears Blue, and the third path (Rank 3) wears Green. Distinguishes the 2 harmonic awakenings from the 2 color-mismatched pairings.", False, (210, 210, 210) if a_rule else (160, 155, 150)),
                ("", False, (0, 0, 0)),
                ("THE FOUR PLAUSIBLE CANDIDATES:", True, (255, 220, 130)),
                ("• Candidate A: Silver Key + Blue Mirror + Crystal 2", True, (120, 220, 255)),
                (f"  Deduction: {cand_a_status}", False, (100, 245, 150) if a_rule else (220, 220, 220)),
                ("• Candidate B: Silver Key + Green Mirror + Crystal 2", True, (220, 190, 160)),
                (f"  Deduction: {cand_b_status}", False, (245, 120, 110) if a_rule else (220, 220, 220)),
                ("• Candidate C: Gold Key + Blue Mirror + Crystal 3", True, (220, 190, 160)),
                (f"  Deduction: {cand_c_status}", False, (245, 120, 110) if a_rule else (220, 220, 220)),
                ("• Candidate D: Gold Key + Green Mirror + Crystal 3", True, (140, 240, 160)),
                (f"  Deduction: {cand_d_status}", False, (100, 245, 150) if a_rule else (220, 220, 220)),
            ]

        # Word wrap raw items to comfortably fit content width
        max_text_w = content_rect.width - 44
        wrapped_lines = []
        for text, is_bold, col in raw_items:
            if not text.strip():
                wrapped_lines.append(("", is_bold, col))
                continue
            f = f_bold if is_bold else f_body
            words = text.split()
            cur_line = []
            for w in words:
                test_str = " ".join(cur_line + [w])
                if f.size(test_str)[0] <= max_text_w:
                    cur_line.append(w)
                else:
                    if cur_line:
                        wrapped_lines.append((" ".join(cur_line), is_bold, col))
                    cur_line = [w]
            if cur_line:
                wrapped_lines.append((" ".join(cur_line), is_bold, col))

        # Dynamic scroll bounds calculation
        line_h = 19
        total_content_h = 24 + len(wrapped_lines) * line_h
        visible_h = content_rect.height - 20
        self.max_scroll = max(0, total_content_h - visible_h)
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

        # Render content strictly clipped inside content_rect
        orig_clip = surface.get_clip()
        surface.set_clip(content_rect)

        curr_y = content_rect.top + 14 - self.scroll_y
        for text, is_bold, col in wrapped_lines:
            if not text.strip():
                curr_y += 10
                continue
            f = f_bold if is_bold else f_body
            if curr_y + line_h >= content_rect.top and curr_y <= content_rect.bottom:
                rendered = f.render(text, True, col)
                surface.blit(rendered, (content_rect.left + 18, curr_y))
            curr_y += line_h

        surface.set_clip(orig_clip)

        # Scrollbar indicator (if content overflows)
        if self.max_scroll > 0:
            track_x = content_rect.right - 8
            track_y = content_rect.top + 8
            track_h = content_rect.height - 16
            pygame.draw.rect(surface, (28, 22, 34), (track_x, track_y, 4, track_h), border_radius=2)
            thumb_ratio = visible_h / total_content_h
            thumb_h = max(20, int(track_h * thumb_ratio))
            scroll_ratio = self.scroll_y / self.max_scroll
            thumb_y = track_y + int((track_h - thumb_h) * scroll_ratio)
            pygame.draw.rect(surface, (185, 145, 75), (track_x, thumb_y, 4, thumb_h), border_radius=2)

        # Footer
        foot_txt = "[W/S / ↑/↓] Scroll   |   [J / ESC] Close"
        foot_s = f_body.render(foot_txt, True, (175, 160, 135))
        surface.blit(foot_s, (mx + (mw - foot_s.get_width()) // 2, my + mh - 24))


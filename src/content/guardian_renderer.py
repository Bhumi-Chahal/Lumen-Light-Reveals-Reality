"""content/guardian_renderer.py — Procedural Pixel-Art Renderer for the Level 4 Temple Guardian.

Renders the celestial Temple Guardian on its dais in Level 4:
- Dark indigo hooded robe with draped folds and golden embroidery
- Pale face framed in a deep hood recess
- Small glowing cyan / white eyes (awake) or serene dormant slits (slumbering / locked)
- Ornate gold staff crowned with a celestial finial and glowing crystal orb
- Animated celestial halo drawn behind the character (smooth time-based rotation & pulse)
- Awakening effects: brightness surge, initial glow pulse, and floating celestial particles
- Full support for the reduced-motion accessibility setting
- Pixel-art aesthetic matching Lumen's drawing primitive conventions
"""

import math
import pygame


def draw_guardian(
    surface: pygame.Surface,
    rect: pygame.Rect,
    is_awake: bool,
    is_locked: bool,
    anim_time: float,
    awakening_time: float = 0.0,
    reduced_motion: bool = False,
) -> None:
    """Renders the procedural pixel-art Guardian on its dais.

    Parameters:
        surface: Pygame target surface (world/camera space).
        rect: Screen-space bounding rect of the Guardian dais (52x56).
        is_awake: Whether the Forge has been solved (Awakened state).
        is_locked: Whether the Forge is locked in overload (Petrified state).
        anim_time: Continuous elapsed time in seconds for deterministic animations.
        awakening_time: Seconds elapsed since the Forge solved trigger.
        reduced_motion: If True, disables rotation and suppresses pulsing/rapid flashes.
    """
    cx = rect.centerx
    foot_y = rect.bottom - 14
    head_y = foot_y - 36

    # -------------------------------------------------------------------------
    # 1. Ancient Stone Dais / Pedestal Base
    # -------------------------------------------------------------------------
    _draw_dais(surface, rect, cx, is_awake, is_locked)

    # -------------------------------------------------------------------------
    # 2. Animated Celestial Halo (Drawn BEHIND the character body)
    # -------------------------------------------------------------------------
    halo_cx = cx
    halo_cy = head_y + 11
    _draw_halo(
        surface=surface,
        hcx=halo_cx,
        hcy=halo_cy,
        is_awake=is_awake,
        is_locked=is_locked,
        anim_time=anim_time,
        awakening_time=awakening_time,
        reduced_motion=reduced_motion,
    )

    # -------------------------------------------------------------------------
    # 3. Awakening Floating Particles (Only present when awakened)
    # -------------------------------------------------------------------------
    if is_awake:
        _draw_floating_particles(
            surface=surface,
            cx=cx,
            foot_y=foot_y,
            anim_time=anim_time,
            awakening_time=awakening_time,
            reduced_motion=reduced_motion,
        )

    # -------------------------------------------------------------------------
    # 4. Color Palette Resolution
    # -------------------------------------------------------------------------
    if is_awake:
        c_robe = (30, 32, 66)
        c_robe_dark = (18, 20, 44)
        c_robe_light = (50, 56, 106)
        c_hood_inner = (12, 14, 28)
        c_face = (236, 232, 240)
        c_eye_glow = (90, 230, 255)
        c_eye_core = (255, 255, 255)
        c_gold_trim = (240, 202, 70)
        c_gold_trim_hi = (255, 235, 140)
        c_belt = (215, 172, 55)
        c_gem = (100, 235, 255)
        c_staff_shaft = (215, 175, 52)
        c_staff_hi = (255, 230, 120)
        c_orb = (120, 238, 255)
        c_orb_core = (255, 255, 255)
    elif is_locked:
        c_robe = (36, 34, 42)
        c_robe_dark = (24, 22, 28)
        c_robe_light = (48, 46, 56)
        c_hood_inner = (16, 15, 20)
        c_face = (124, 118, 126)
        c_eye_glow = (50, 46, 54)
        c_eye_core = (60, 56, 64)
        c_gold_trim = (112, 98, 68)
        c_gold_trim_hi = (138, 122, 88)
        c_belt = (92, 80, 58)
        c_gem = (55, 50, 58)
        c_staff_shaft = (105, 90, 65)
        c_staff_hi = (128, 112, 85)
        c_orb = (64, 60, 70)
        c_orb_core = (80, 76, 88)
    else:
        # Slumbering Sentinel (Dormant celestial state)
        c_robe = (32, 34, 56)
        c_robe_dark = (20, 22, 38)
        c_robe_light = (45, 48, 76)
        c_hood_inner = (14, 16, 26)
        c_face = (212, 206, 218)
        c_eye_glow = (52, 75, 98)
        c_eye_core = (80, 125, 145)
        c_gold_trim = (185, 150, 65)
        c_gold_trim_hi = (218, 184, 95)
        c_belt = (165, 132, 54)
        c_gem = (220, 185, 75)
        c_staff_shaft = (175, 140, 58)
        c_staff_hi = (215, 180, 85)
        c_orb = (130, 185, 215)
        c_orb_core = (210, 235, 245)

    # -------------------------------------------------------------------------
    # 5. Boots / Feet
    # -------------------------------------------------------------------------
    boot_col = (20, 18, 26) if not is_locked else (24, 22, 28)
    pygame.draw.rect(surface, boot_col, (cx - 7, foot_y - 2, 5, 3), border_radius=1)
    pygame.draw.rect(surface, boot_col, (cx + 2, foot_y - 2, 5, 3), border_radius=1)

    # -------------------------------------------------------------------------
    # 6. Dark Indigo Robe Body & Folds
    # -------------------------------------------------------------------------
    pts_robe = [
        (cx - 9, head_y + 13),
        (cx + 9, head_y + 13),
        (cx + 14, foot_y - 2),
        (cx - 14, foot_y - 2),
    ]
    pygame.draw.polygon(surface, c_robe, pts_robe)

    # Left & Right shadowed pleats
    pts_left_fold = [
        (cx - 14, foot_y - 2),
        (cx - 9, head_y + 13),
        (cx - 5, head_y + 24),
        (cx - 9, foot_y - 2),
    ]
    pygame.draw.polygon(surface, c_robe_dark, pts_left_fold)

    pts_right_fold = [
        (cx + 14, foot_y - 2),
        (cx + 9, head_y + 13),
        (cx + 5, head_y + 24),
        (cx + 9, foot_y - 2),
    ]
    pygame.draw.polygon(surface, c_robe_dark, pts_right_fold)

    # Center highlighted vestment column
    pts_center_panel = [
        (cx - 4, head_y + 14),
        (cx + 4, head_y + 14),
        (cx + 5, foot_y - 2),
        (cx - 5, foot_y - 2),
    ]
    pygame.draw.polygon(surface, c_robe_light, pts_center_panel)

    # Gold embroidered hem across robe bottom
    pygame.draw.line(surface, c_gold_trim, (cx - 14, foot_y - 2), (cx + 14, foot_y - 2), 2)
    pygame.draw.line(surface, c_gold_trim_hi, (cx - 12, foot_y - 3), (cx + 12, foot_y - 3), 1)

    # Small gold celestial runic dots along hem
    for dot_x in (cx - 10, cx - 5, cx, cx + 5, cx + 10):
        pygame.draw.rect(surface, c_gold_trim_hi, (dot_x, foot_y - 5, 2, 2))

    # Celestial gold star cross embroidery on robe flanks
    for sx, sy in ((cx - 9, foot_y - 10), (cx + 9, foot_y - 10)):
        pygame.draw.line(surface, c_gold_trim, (sx - 2, sy), (sx + 2, sy), 1)
        pygame.draw.line(surface, c_gold_trim, (sx, sy - 2), (sx, sy + 2), 1)

    # -------------------------------------------------------------------------
    # 7. Gold Belt & Celestial Talisman
    # -------------------------------------------------------------------------
    belt_y = head_y + 16
    pygame.draw.rect(surface, c_belt, (cx - 8, belt_y, 16, 4))
    pygame.draw.rect(surface, c_gold_trim_hi, (cx - 8, belt_y, 16, 1))

    # Buckle / Talisman
    pygame.draw.rect(surface, c_gold_trim, (cx - 2, belt_y - 1, 5, 6), border_radius=1)
    pygame.draw.rect(surface, c_gem, (cx - 1, belt_y, 3, 4))

    # Hanging sash tails
    pygame.draw.line(surface, c_belt, (cx - 1, belt_y + 5), (cx - 2, belt_y + 12), 2)
    pygame.draw.line(surface, c_belt, (cx + 1, belt_y + 5), (cx + 2, belt_y + 11), 2)
    pygame.draw.rect(surface, c_gold_trim_hi, (cx - 3, belt_y + 11, 2, 2))
    pygame.draw.rect(surface, c_gold_trim_hi, (cx + 1, belt_y + 10, 2, 2))

    # -------------------------------------------------------------------------
    # 8. Sleeves & Hands
    # -------------------------------------------------------------------------
    staff_x = cx + 16

    # Right arm / sleeve (holding the staff at right side)
    pts_r_sleeve = [
        (cx + 7, head_y + 13),
        (staff_x - 1, head_y + 16),
        (staff_x - 1, head_y + 20),
        (cx + 6, head_y + 19),
    ]
    pygame.draw.polygon(surface, c_robe, pts_r_sleeve)
    pygame.draw.line(surface, c_gold_trim, (staff_x - 3, head_y + 16), (staff_x - 3, head_y + 20), 2)
    # Pale right hand grasping staff
    pygame.draw.rect(surface, c_face, (staff_x - 2, head_y + 17, 3, 3), border_radius=1)

    # Left arm / sleeve (draped gracefully at left flank)
    pts_l_sleeve = [
        (cx - 7, head_y + 13),
        (cx - 13, head_y + 17),
        (cx - 13, head_y + 22),
        (cx - 6, head_y + 19),
    ]
    pygame.draw.polygon(surface, c_robe, pts_l_sleeve)
    pygame.draw.line(surface, c_gold_trim, (cx - 13, head_y + 18), (cx - 13, head_y + 22), 2)
    # Pale left hand
    pygame.draw.rect(surface, c_face, (cx - 12, head_y + 22, 3, 3), border_radius=1)

    # If awake, a tiny floating celestial spark hovers over the left palm
    if is_awake:
        spark_alpha = int(180 + 75 * math.sin(anim_time * 3.0)) if not reduced_motion else 200
        spark_surf = pygame.Surface((5, 5), pygame.SRCALPHA)
        spark_surf.fill((120, 235, 255, spark_alpha))
        pygame.draw.rect(spark_surf, (255, 255, 255, min(255, spark_alpha + 40)), (1, 1, 3, 3))
        surface.blit(spark_surf, (cx - 13, head_y + 16))

    # -------------------------------------------------------------------------
    # 9. Hood & Head Covering (Draped dark indigo cowl with gold trim)
    # -------------------------------------------------------------------------
    # Outer Cowl Polygon
    pts_hood = [
        (cx, head_y - 6),           # Top hood peak
        (cx + 7, head_y - 4),       # Upper right
        (cx + 10, head_y + 3),      # Mid right
        (cx + 9, head_y + 12),      # Lower right shoulder
        (cx + 5, head_y + 14),      # Collar right
        (cx - 5, head_y + 14),      # Collar left
        (cx - 9, head_y + 12),      # Lower left shoulder
        (cx - 10, head_y + 3),      # Mid left
        (cx - 7, head_y - 4),       # Upper left
    ]
    pygame.draw.polygon(surface, c_robe, pts_hood)

    # Hood fold shading
    pts_hood_shd = [
        (cx, head_y - 6),
        (cx - 7, head_y - 4),
        (cx - 10, head_y + 3),
        (cx - 6, head_y + 3),
    ]
    pygame.draw.polygon(surface, c_robe_dark, pts_hood_shd)

    # Gold rim lining the cowl face opening
    pts_cowl_rim = [
        (cx - 6, head_y + 11),
        (cx - 7, head_y + 4),
        (cx - 5, head_y - 1),
        (cx, head_y - 3),
        (cx + 5, head_y - 1),
        (cx + 7, head_y + 4),
        (cx + 6, head_y + 11),
    ]
    pygame.draw.lines(surface, c_gold_trim, False, pts_cowl_rim, 2)

    # -------------------------------------------------------------------------
    # 10. Deep Inner Hood Recess & Pale Face
    # -------------------------------------------------------------------------
    # Deep shadow pocket inside hood
    pygame.draw.rect(surface, c_hood_inner, (cx - 6, head_y, 12, 11), border_radius=3)

    # Pale mystical face inside the hood
    pygame.draw.rect(surface, c_face, (cx - 5, head_y + 2, 10, 8), border_radius=2)
    # Subtle jawline contour
    pygame.draw.line(surface, (c_face[0] - 25, c_face[1] - 25, c_face[2] - 25), (cx - 4, head_y + 9), (cx + 4, head_y + 9), 1)

    # -------------------------------------------------------------------------
    # 11. Small Cyan / White Eyes
    # -------------------------------------------------------------------------
    eye_y = head_y + 4
    if is_awake:
        # Awake: small luminous cyan eyes with bright white core
        # Eye glow aura
        eye_glow_surf = pygame.Surface((8, 6), pygame.SRCALPHA)
        glow_a = int(90 + 35 * math.sin(anim_time * 2.5)) if not reduced_motion else 100
        pygame.draw.circle(eye_glow_surf, (*c_eye_glow, glow_a), (2, 3), 3)
        pygame.draw.circle(eye_glow_surf, (*c_eye_glow, glow_a), (6, 3), 3)
        surface.blit(eye_glow_surf, (cx - 4, eye_y - 1))

        # Cyan pixels
        pygame.draw.rect(surface, c_eye_glow, (cx - 4, eye_y, 2, 2))
        pygame.draw.rect(surface, c_eye_glow, (cx + 2, eye_y, 2, 2))
        # White inner core
        pygame.draw.rect(surface, c_eye_core, (cx - 3, eye_y, 1, 1))
        pygame.draw.rect(surface, c_eye_core, (cx + 2, eye_y, 1, 1))
    elif is_locked:
        # Cold, petrified lifeless stone grey slits
        pygame.draw.line(surface, c_eye_glow, (cx - 4, eye_y + 1), (cx - 2, eye_y + 1), 1)
        pygame.draw.line(surface, c_eye_glow, (cx + 2, eye_y + 1), (cx + 4, eye_y + 1), 1)
    else:
        # Slumbering: peaceful sleeping eye slits with faint celestial cyan hint
        pygame.draw.line(surface, c_eye_glow, (cx - 4, eye_y + 1), (cx - 2, eye_y + 1), 1)
        pygame.draw.line(surface, c_eye_glow, (cx + 2, eye_y + 1), (cx + 4, eye_y + 1), 1)
        pygame.draw.rect(surface, c_eye_core, (cx - 3, eye_y + 1, 1, 1))
        pygame.draw.rect(surface, c_eye_core, (cx + 3, eye_y + 1, 1, 1))

    # -------------------------------------------------------------------------
    # 12. Golden Staff with Celestial Finial & Glowing Orb
    # -------------------------------------------------------------------------
    staff_top_y = head_y - 13
    # Staff golden shaft
    pygame.draw.line(surface, c_staff_shaft, (staff_x, foot_y - 2), (staff_x, staff_top_y + 4), 2)
    pygame.draw.line(surface, c_staff_hi, (staff_x - 1, foot_y - 2), (staff_x - 1, staff_top_y + 4), 1)

    # Decorative golden rings / bindings
    for ring_y in (foot_y - 7, head_y + 15, head_y + 6):
        pygame.draw.line(surface, c_gold_trim_hi, (staff_x - 2, ring_y), (staff_x + 1, ring_y), 1)

    # Celestial Finial: Golden crescent / celestial arc holding the orb
    pts_crescent = [
        (staff_x - 4, staff_top_y + 3),
        (staff_x - 5, staff_top_y - 2),
        (staff_x - 3, staff_top_y - 7),
        (staff_x, staff_top_y - 8),
        (staff_x + 3, staff_top_y - 7),
        (staff_x + 5, staff_top_y - 2),
        (staff_x + 4, staff_top_y + 3),
        (staff_x + 1, staff_top_y + 4),
        (staff_x - 1, staff_top_y + 4),
    ]
    pygame.draw.lines(surface, c_staff_shaft, False, pts_crescent, 2)
    pygame.draw.circle(surface, c_gold_trim_hi, (staff_x - 4, staff_top_y + 3), 1)
    pygame.draw.circle(surface, c_gold_trim_hi, (staff_x + 4, staff_top_y + 3), 1)

    # Celestial Orb resting inside the finial
    orb_cx = staff_x
    orb_cy = staff_top_y - 2
    if is_awake:
        # Luminous glowing cyan-white celestial orb
        orb_pulse = math.sin(anim_time * 3.5) if not reduced_motion else 0.0
        orb_rad = 3
        # Ethereal glow aura around orb
        aura_rad = int(7 + 2 * orb_pulse)
        aura_surf = pygame.Surface((aura_rad * 2 + 2, aura_rad * 2 + 2), pygame.SRCALPHA)
        aura_a = int(95 + 40 * orb_pulse) if not reduced_motion else 110
        pygame.draw.circle(aura_surf, (*c_orb, aura_a), (aura_rad + 1, aura_rad + 1), aura_rad)
        surface.blit(aura_surf, (orb_cx - aura_rad - 1, orb_cy - aura_rad - 1))

        # Orb body & white star core
        pygame.draw.circle(surface, c_orb, (orb_cx, orb_cy), orb_rad)
        pygame.draw.circle(surface, c_orb_core, (orb_cx, orb_cy), orb_rad - 1)
    elif is_locked:
        # Cold lifeless stone bead
        pygame.draw.circle(surface, c_orb, (orb_cx, orb_cy), 3)
        pygame.draw.circle(surface, c_orb_core, (orb_cx - 1, orb_cy - 1), 1)
    else:
        # Slumbering: soft tranquil blue-gold crystal
        pygame.draw.circle(surface, c_orb, (orb_cx, orb_cy), 3)
        pygame.draw.circle(surface, c_orb_core, (orb_cx - 1, orb_cy - 1), 1)

    # -------------------------------------------------------------------------
    # 13. Nameplate Badge Below Dais
    # -------------------------------------------------------------------------
    f_badge = pygame.font.SysFont("consolas", 9, bold=True)
    if is_awake:
        lbl_text = "TEMPLE GUARDIAN"
        lbl_col = (135, 230, 255)
    elif is_locked:
        lbl_text = "DORMANT SENTINEL"
        lbl_col = (135, 122, 132)
    else:
        lbl_text = "SLUMBERING SENTINEL"
        lbl_col = (205, 175, 105)

    lbl_surf = f_badge.render(lbl_text, True, lbl_col)
    surface.blit(lbl_surf, (cx - lbl_surf.get_width() // 2, rect.bottom + 8))


def _draw_dais(surface: pygame.Surface, rect: pygame.Rect, cx: int, is_awake: bool, is_locked: bool) -> None:
    """Draws the ancient stone dais plinth beneath the Guardian."""
    # Bottom stepped plinth
    step_bottom = pygame.Rect(cx - 30, rect.bottom - 10, 60, 10)
    pygame.draw.rect(surface, (22, 18, 28), step_bottom, border_radius=4)
    pygame.draw.rect(surface, (60, 48, 70), step_bottom, width=1, border_radius=4)

    # Upper dais platform
    step_top = pygame.Rect(cx - 24, rect.bottom - 17, 48, 9)
    pygame.draw.rect(surface, (34, 28, 42), step_top, border_radius=3)

    # Gold rim border on upper platform
    trim_col = (235, 195, 75) if is_awake else ((100, 85, 60) if is_locked else (160, 130, 60))
    pygame.draw.rect(surface, trim_col, step_top, width=2, border_radius=3)

    # Runic carvings along the dais front face
    if is_awake:
        # Radiant celestial cyan runic inlays
        rune_col = (90, 220, 255)
        for rx in (cx - 16, cx - 8, cx, cx + 8, cx + 16):
            pygame.draw.rect(surface, rune_col, (rx, rect.bottom - 15, 2, 5))
            pygame.draw.rect(surface, (255, 255, 255), (rx, rect.bottom - 13, 2, 2))
    elif not is_locked:
        # Ancient muted gold glyphs
        rune_col = (130, 105, 50)
        for rx in (cx - 16, cx - 8, cx, cx + 8, cx + 16):
            pygame.draw.rect(surface, rune_col, (rx, rect.bottom - 15, 2, 4))


def _draw_halo(
    surface: pygame.Surface,
    hcx: int,
    hcy: int,
    is_awake: bool,
    is_locked: bool,
    anim_time: float,
    awakening_time: float,
    reduced_motion: bool,
) -> None:
    """Draws the animated celestial circular halo behind the Guardian.

    Requirements:
    - Gold or pale-cyan color
    - Slowly rotate (deterministic time-based)
    - Soft pulsing glow
    - Remain behind the character
    - Visible without dominating the screen
    - Respect reduced-motion setting
    - Awakening: increased brightness & short initial glow pulse
    """
    base_r = 28

    if reduced_motion:
        rot_angle = 0.0
        pulse_val = 0.0
        pulse_mult = 1.0
        glow_pulse = 0.0
    else:
        rot_angle = anim_time * 0.35  # Slow smooth rotation (~18 seconds per full revolution)
        pulse_val = math.sin(anim_time * 1.8)
        pulse_mult = 0.85 + 0.25 * (0.5 + 0.5 * pulse_val)

        # Awakening glow pulse: short initial surge decaying over 3.0 seconds
        if is_awake and awakening_time < 3.0:
            decay = max(0.0, 1.0 - awakening_time / 3.0)
            glow_pulse = math.sin(awakening_time * math.pi * 2.0) * decay * 0.6
        else:
            glow_pulse = 0.0

    # Halo radius with subtle pulse
    halo_r = int(base_r + (2 * pulse_val if not reduced_motion else 0) + (4 * glow_pulse if not reduced_motion else 0))

    # Calculate alpha brightness based on state
    if is_awake:
        # Brightened halo with extra burst during awakening pulse
        base_alpha = 130
        dyn_alpha = int((base_alpha + 45 * pulse_val + glow_pulse * 80) * pulse_mult)
        halo_alpha = max(70, min(255, dyn_alpha))
        c_glow = (100, 225, 255)
        c_primary_ring = (255, 215, 80)
        c_secondary_ring = (140, 235, 255)
        c_rays = (255, 235, 120)
    elif is_locked:
        # Faint petrified cold grey ring
        halo_alpha = 25
        c_glow = (70, 70, 90)
        c_primary_ring = (95, 85, 75)
        c_secondary_ring = (70, 75, 90)
        c_rays = (85, 80, 75)
    else:
        # Slumbering Sentinel: serene, visible without dominating
        base_alpha = 55
        dyn_alpha = int((base_alpha + 18 * pulse_val) * pulse_mult)
        halo_alpha = max(35, min(90, dyn_alpha))
        c_glow = (220, 180, 70)
        c_primary_ring = (215, 175, 65)
        c_secondary_ring = (120, 195, 225)
        c_rays = (235, 195, 85)

    surf_dim = halo_r * 2 + 28
    halo_surf = pygame.Surface((surf_dim, surf_dim), pygame.SRCALPHA)
    scx = surf_dim // 2
    scy = surf_dim // 2

    # 1. Soft Outer Glow (Broad translucent aura)
    glow_alpha = int(halo_alpha * 0.35)
    pygame.draw.circle(halo_surf, (*c_glow, glow_alpha), (scx, scy), halo_r + 6)

    # 2. Outer Pale-Cyan / Gold Celestial Ring
    ring1_alpha = int(halo_alpha * 0.85)
    pygame.draw.circle(halo_surf, (*c_secondary_ring, ring1_alpha), (scx, scy), halo_r, width=2)

    # 3. Inner Gold Concentric Accent Ring
    ring2_alpha = halo_alpha
    inner_r = max(4, halo_r - 5)
    pygame.draw.circle(halo_surf, (*c_primary_ring, ring2_alpha), (scx, scy), inner_r, width=1)

    # 4. Slowly Rotating Celestial Radiating Rays & Star Nodes
    if not is_locked:
        num_rays = 8
        for i in range(num_rays):
            angle = rot_angle + i * (2.0 * math.pi / num_rays)
            is_cardinal = (i % 2 == 0)

            # Ray endpoints
            r_start = inner_r - 1
            r_end = halo_r + (6 if is_cardinal else 3)

            x1 = scx + int(math.cos(angle) * r_start)
            y1 = scy + int(math.sin(angle) * r_start)
            x2 = scx + int(math.cos(angle) * r_end)
            y2 = scy + int(math.sin(angle) * r_end)

            ray_alpha = int(halo_alpha * (0.9 if is_cardinal else 0.6))
            pygame.draw.line(halo_surf, (*c_rays, ray_alpha), (x1, y1), (x2, y2), 1 if not is_cardinal else 2)

            # Diamond starlight pip at cardinal tips
            if is_cardinal:
                pip_x = scx + int(math.cos(angle) * (halo_r + 4))
                pip_y = scy + int(math.sin(angle) * (halo_r + 4))
                pygame.draw.circle(halo_surf, (*c_primary_ring, halo_alpha), (pip_x, pip_y), 2)
                pygame.draw.circle(halo_surf, (255, 255, 255, halo_alpha), (pip_x, pip_y), 1)

    surface.blit(halo_surf, (hcx - scx, hcy - scy))


def _draw_floating_particles(
    surface: pygame.Surface,
    cx: int,
    foot_y: int,
    anim_time: float,
    awakening_time: float,
    reduced_motion: bool,
) -> None:
    """Renders a small number of smooth, deterministic floating celestial particles.

    Requirements:
    - Add a small number of floating particles when awakened
    - Deterministic time-based animation (no per-frame random values)
    - Respect reduced-motion setting
    """
    num_particles = 8
    cycle_duration = 3.6  # Seconds per particle vertical loop

    for i in range(num_particles):
        # Deterministic phase offsets
        phase = i * (2.0 * math.pi / num_particles)
        # Staggered temporal offset
        p_time = (anim_time + i * (cycle_duration / num_particles)) % cycle_duration
        progress = p_time / cycle_duration  # [0.0, 1.0]

        # Particles drift upward from dais level to above head
        base_y = foot_y - 6
        travel_distance = 46.0
        py = int(base_y - progress * travel_distance)

        # Smooth horizontal sway
        sway_speed = 1.2 if not reduced_motion else 0.2
        sway_amp = 18.0 + (i % 3) * 4.0
        px = int(cx + math.sin(phase + anim_time * sway_speed) * sway_amp)

        # Bell-curve alpha: fade in as particle ascends, fade out at apex
        alpha_env = math.sin(progress * math.pi)
        p_alpha = int(220 * alpha_env)
        if p_alpha <= 0:
            continue

        # Alternating celestial cyan & starlight gold
        is_cyan = (i % 2 == 0)
        p_col = (130, 240, 255) if is_cyan else (255, 230, 130)

        # Draw crisp pixel-art sparkle: center white dot + cross motes
        p_surf = pygame.Surface((5, 5), pygame.SRCALPHA)
        # Center core
        pygame.draw.rect(p_surf, (255, 255, 255, p_alpha), (2, 2, 2, 2))
        # Cross arms
        cross_alpha = int(p_alpha * 0.75)
        p_surf.set_at((2, 0), (*p_col, cross_alpha))
        p_surf.set_at((2, 4), (*p_col, cross_alpha))
        p_surf.set_at((0, 2), (*p_col, cross_alpha))
        p_surf.set_at((4, 2), (*p_col, cross_alpha))

        surface.blit(p_surf, (px - 2, py - 2))


def draw_guardian_portrait(
    surface: pygame.Surface,
    rect: pygame.Rect,
    anim_time: float = 0.0,
    reduced_motion: bool = False,
) -> None:
    """Draws a detailed awakened Guardian portrait card for the success dialogue modal.

    Features the redesigned hooded dark-indigo robe, pale face, glowing cyan eyes,
    gold details, and celestial halo.
    """
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    # Background card
    pygame.draw.rect(panel, (14, 16, 28, 240), panel.get_rect(), border_radius=8)
    pygame.draw.rect(panel, (215, 175, 70), panel.get_rect(), width=2, border_radius=8)
    pygame.draw.rect(panel, (70, 95, 135), panel.get_rect().inflate(-6, -6), width=1, border_radius=6)

    cx = rect.width // 2
    head_y = 66

    # 1. Rotating Celestial Halo behind portrait
    halo_r = 38
    pulse = math.sin(anim_time * 2.0) if not reduced_motion else 0.0
    rot = anim_time * 0.35 if not reduced_motion else 0.0

    halo_surf = pygame.Surface((110, 110), pygame.SRCALPHA)
    hcx, hcy = 55, 55
    pygame.draw.circle(halo_surf, (100, 220, 255, 45), (hcx, hcy), halo_r + 6)
    pygame.draw.circle(halo_surf, (140, 235, 255, 160), (hcx, hcy), halo_r, width=2)
    pygame.draw.circle(halo_surf, (255, 215, 80, 180), (hcx, hcy), halo_r - 6, width=1)
    for i in range(8):
        ang = rot + i * (math.pi / 4.0)
        rx1 = hcx + int(math.cos(ang) * (halo_r - 7))
        ry1 = hcy + int(math.sin(ang) * (halo_r - 7))
        rx2 = hcx + int(math.cos(ang) * (halo_r + 7))
        ry2 = hcy + int(math.sin(ang) * (halo_r + 7))
        pygame.draw.line(halo_surf, (255, 230, 120, 180), (rx1, ry1), (rx2, ry2), 2 if i % 2 == 0 else 1)
    panel.blit(halo_surf, (cx - hcx, head_y - hcy + 4))

    # 2. Dark Indigo Robe
    pts_robe = [
        (cx - 42, 208),
        (cx - 20, 95),
        (cx + 20, 95),
        (cx + 42, 208),
    ]
    pygame.draw.polygon(panel, (30, 32, 66), pts_robe)
    # Robe shading folds
    pygame.draw.polygon(panel, (18, 20, 44), [(cx - 42, 208), (cx - 20, 95), (cx - 10, 140), (cx - 22, 208)])
    pygame.draw.polygon(panel, (18, 20, 44), [(cx + 42, 208), (cx + 20, 95), (cx + 10, 140), (cx + 22, 208)])
    # Robe center highlight
    pygame.draw.polygon(panel, (50, 56, 106), [(cx - 9, 96), (cx + 9, 96), (cx + 12, 208), (cx - 12, 208)])
    # Gold embroidery along hem and center vestment
    pygame.draw.line(panel, (240, 202, 70), (cx - 9, 96), (cx - 12, 208), 2)
    pygame.draw.line(panel, (240, 202, 70), (cx + 9, 96), (cx + 12, 208), 2)

    # 3. Gold Staff held at right flank
    staff_x = cx + 32
    pygame.draw.line(panel, (215, 175, 52), (staff_x, 208), (staff_x, 34), 3)
    pygame.draw.line(panel, (255, 230, 120), (staff_x - 1, 208), (staff_x - 1, 34), 1)
    # Celestial Finial & Glowing Orb on staff
    pygame.draw.circle(panel, (120, 238, 255, 100), (staff_x, 32), 10)
    pygame.draw.circle(panel, (120, 238, 255), (staff_x, 32), 6)
    pygame.draw.circle(panel, (255, 255, 255), (staff_x, 32), 3)
    pygame.draw.arc(panel, (240, 202, 70), (staff_x - 8, 24, 16, 16), 0.5, 5.8, 2)

    # 4. Hood Outer Cowl
    pts_hood = [
        (cx, head_y - 24),
        (cx + 22, head_y - 12),
        (cx + 26, head_y + 12),
        (cx + 20, head_y + 32),
        (cx - 20, head_y + 32),
        (cx - 26, head_y + 12),
        (cx - 22, head_y - 12),
    ]
    pygame.draw.polygon(panel, (30, 32, 66), pts_hood)
    pygame.draw.polygon(panel, (18, 20, 44), [(cx, head_y - 24), (cx - 22, head_y - 12), (cx - 26, head_y + 12), (cx - 14, head_y + 6)])
    # Gold rim along cowl face opening
    pts_rim = [
        (cx - 16, head_y + 26),
        (cx - 18, head_y + 8),
        (cx - 14, head_y - 8),
        (cx, head_y - 14),
        (cx + 14, head_y - 8),
        (cx + 18, head_y + 8),
        (cx + 16, head_y + 26),
    ]
    pygame.draw.lines(panel, (240, 202, 70), False, pts_rim, 2)

    # 5. Inner Hood Recess & Pale Face
    pygame.draw.rect(panel, (12, 14, 28), (cx - 16, head_y - 8, 32, 34), border_radius=6)
    pygame.draw.rect(panel, (236, 232, 240), (cx - 13, head_y - 2, 26, 24), border_radius=4)

    # 6. Glowing Cyan / White Eyes
    eye_y = head_y + 5
    # Eye auras
    pygame.draw.circle(panel, (90, 230, 255, 120), (cx - 7, eye_y), 5)
    pygame.draw.circle(panel, (90, 230, 255, 120), (cx + 7, eye_y), 5)
    # Luminous cyan rects
    pygame.draw.rect(panel, (90, 230, 255), (cx - 9, eye_y - 2, 4, 4))
    pygame.draw.rect(panel, (90, 230, 255), (cx + 5, eye_y - 2, 4, 4))
    # Bright white core
    pygame.draw.rect(panel, (255, 255, 255), (cx - 8, eye_y - 1, 2, 2))
    pygame.draw.rect(panel, (255, 255, 255), (cx + 6, eye_y - 1, 2, 2))

    # 7. Nameplate Label
    f_lbl = pygame.font.SysFont("consolas", 11, bold=True)
    lbl = f_lbl.render("TEMPLE GUARDIAN", True, (150, 235, 255))
    panel.blit(lbl, (cx - lbl.get_width() // 2, 220))

    surface.blit(panel, rect.topleft)


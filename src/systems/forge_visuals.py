"""systems/forge_visuals.py — Procedural Visuals for the Ancient Forge Temple Altar.

Renders ancient temple altar visuals for the Level 4 Forge relic selection:
- Central Volcanic Forge Crucible with dynamic core fire and harmonic socket nodes
- Carved circular stone pedestals with stepped moldings and bronze rims
- Time-based floating relic elevation and smooth levitation animations
- Dedicated circular glow auras (Gold for Keys, Mirror-color for Mirrors, Crystal-color for Crystals)
- High-fidelity illuminated Level 3 crystal spires with faceted shading and starburst gleams
- Elegant ancient temple alcove framing without modern dashboard cards or circuit diagram lines
"""

import math
import pygame
from systems.inventory_ui import InventoryModal


# Relic glow color mappings
GLOW_COLORS = {
    # Keys: Warm celestial gold
    "key_bronze": (245, 195, 75),
    "key_silver": (225, 235, 255),
    "key_gold": (255, 215, 60),
    "keys": (255, 215, 75),
    # Mirrors: Resonant spectral glass tones
    "mirror_red": (255, 65, 85),
    "mirror_blue": (60, 160, 255),
    "mirror_green": (65, 235, 120),
    "mirrors": (140, 200, 255),
    # Crystals: Harmonic prism frequencies
    "crystal_1": (255, 75, 105),
    "crystal_2": (65, 175, 255),
    "crystal_3": (60, 245, 130),
    "crystals": (120, 235, 210),
}


def draw_central_crucible(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    state: str,
    attempts_left: int,
    max_attempts: int,
    selected_key: str | None,
    selected_mirror: str | None,
    selected_crystal: str | None,
    pulse_phase: float,
    resonance_phase: float,
) -> None:
    """Renders the visually dominant Central Forge Crucible in the upper altar focal area.

    Communicates slot placement and harmonic resonance through socket nodes along
    the crucible rim, eliminating rigid map/circuit lines.
    """
    is_solved = (state == "solved")
    is_locked = (state == "locked")

    # 1. Outer Volcanic Bedrock Plinth
    plinth_r = 30
    plinth_rect = pygame.Rect(cx - 70, cy - 22, 140, 44)
    pygame.draw.rect(surface, (22, 18, 28), plinth_rect, border_radius=8)
    plinth_border = (255, 215, 90) if is_solved else ((140, 65, 55) if is_locked else (150, 115, 60))
    pygame.draw.rect(surface, plinth_border, plinth_rect, width=2, border_radius=8)

    # 2. Stepped Inner Hearth
    hearth_rect = plinth_rect.inflate(-12, -10)
    pygame.draw.rect(surface, (14, 11, 18), hearth_rect, border_radius=6)
    pygame.draw.rect(surface, (85, 65, 40), hearth_rect, width=1, border_radius=6)

    # 3. Central Crucible Hearth Bowl
    bowl_r = 18
    bowl_pulse = math.sin(pulse_phase * 2.5)

    # Ambient Core Glow Aura
    if is_solved:
        c_core = (120, 235, 180)
        c_fire = (255, 245, 150)
        glow_a = int(120 + 40 * bowl_pulse)
    elif is_locked:
        c_core = (95, 40, 40)
        c_fire = (160, 60, 50)
        glow_a = 40
    else:
        num_placed = sum(1 for s in (selected_key, selected_mirror, selected_crystal) if s is not None)
        c_core = (235, 115, 40)
        c_fire = (255, 195, 75)
        glow_a = int(50 + 25 * num_placed + 20 * bowl_pulse)

    aura_surf = pygame.Surface((70, 70), pygame.SRCALPHA)
    pygame.draw.circle(aura_surf, (*c_core, glow_a), (35, 35), 26)
    pygame.draw.circle(aura_surf, (*c_fire, int(glow_a * 0.7)), (35, 35), 16)
    surface.blit(aura_surf, (cx - 35, cy - 35))

    # Crucible rim circle
    pygame.draw.circle(surface, (36, 28, 42), (cx, cy), bowl_r)
    pygame.draw.circle(surface, (200, 160, 70), (cx, cy), bowl_r, width=2)
    pygame.draw.circle(surface, c_fire, (cx, cy), 5)

    # Concentric harmonic resonance arcs
    if not is_locked:
        arc_angle = resonance_phase
        pygame.draw.arc(surface, c_core, (cx - 24, cy - 24, 48, 48), arc_angle, arc_angle + math.pi * 1.2, 1)

    # 4. Three Sacred Socket Nodes along Crucible Plinth Flanks
    # Left node: Key socket indicator
    _draw_socket_node(surface, cx - 48, cy, selected_key, "key_gold", GLOW_COLORS.get(selected_key, (245, 195, 75)), "KEY")
    # Top-center node: Mirror socket indicator
    _draw_socket_node(surface, cx, cy - 18, selected_mirror, "mirror_blue", GLOW_COLORS.get(selected_mirror, (65, 160, 255)), "MIR")
    # Right node: Crystal socket indicator
    _draw_socket_node(surface, cx + 48, cy, selected_crystal, "crystal_1", GLOW_COLORS.get(selected_crystal, (60, 245, 130)), "CRY")


def _draw_socket_node(
    surface: pygame.Surface,
    nx: int,
    ny: int,
    selected_id: str | None,
    fallback_id: str,
    glow_color: tuple[int, int, int],
    label: str,
) -> None:
    """Renders a socket indicator node on the central crucible plinth."""
    is_socketed = (selected_id is not None)
    node_r = 7

    # Base stone socket indentation
    pygame.draw.circle(surface, (16, 12, 22), (nx, ny), node_r)
    border_col = glow_color if is_socketed else (90, 70, 50)
    pygame.draw.circle(surface, border_col, (nx, ny), node_r, width=1)

    if is_socketed:
        # Luminous placed gem
        pygame.draw.circle(surface, glow_color, (nx, ny), node_r - 2)
        pygame.draw.circle(surface, (255, 255, 255), (nx, ny), 2)
    else:
        # Dormant hollow socket
        pygame.draw.circle(surface, (32, 26, 38), (nx, ny), node_r - 2)


def draw_relic_pedestal(
    surface: pygame.Surface,
    rect: pygame.Rect,
    item: dict,
    cat_key: str,
    has_item: bool,
    is_selected: bool,
    is_focused: bool,
    is_hovered: bool,
    pulse_phase: float,
    font_bold: pygame.font.Font,
    font_tag: pygame.font.Font,
) -> None:
    """Renders a single relic offering choice on a carved circular stone pedestal.

    Replaces large rectangular cards with an ancient temple alcove featuring:
    - Stepped circular pedestal
    - Elevated floating relic with smooth levitation
    - Glowing circular aura (gold for keys, specific colors for mirrors/crystals)
    - Clearly styled text and status badge
    """
    item_id = item["id"]
    pedestal_cx = rect.x + 30
    pedestal_cy = rect.centery

    # 1. Subtle Temple Alcove Background
    alcove_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    if is_selected:
        # Warm sanctuary amber with radiant gold border
        alcove_bg = (42, 32, 22, 220)
        alcove_border = (245, 205, 80)
        border_w = 2
    elif is_focused or is_hovered:
        # Subtle illuminated temple stone
        alcove_bg = (34, 26, 44, 210)
        alcove_border = (200, 170, 100) if has_item else (145, 75, 65)
        border_w = 2
    else:
        # Quiet ancient stone recess
        alcove_bg = (22, 17, 28, 190) if has_item else (16, 13, 20, 160)
        alcove_border = (95, 75, 50) if has_item else (55, 45, 38)
        border_w = 1

    alcove_surf.fill(alcove_bg)
    pygame.draw.rect(alcove_surf, alcove_border, (0, 0, rect.width, rect.height), width=border_w, border_radius=6)
    surface.blit(alcove_surf, rect.topleft)

    # 2. Carved Circular Stone Pedestal
    ped_r = 18
    # Outer stone step
    pygame.draw.circle(surface, (24, 20, 32), (pedestal_cx, pedestal_cy + 2), ped_r)
    # Upper polished plinth
    pygame.draw.circle(surface, (38, 30, 48), (pedestal_cx, pedestal_cy), ped_r - 2)
    # Bronze/gold rim
    rim_col = (215, 175, 65) if is_selected else ((150, 120, 70) if has_item else (70, 60, 52))
    pygame.draw.circle(surface, rim_col, (pedestal_cx, pedestal_cy), ped_r - 2, width=1)

    # 3. Glowing Circular Aura & Floating Elevation
    glow_color = GLOW_COLORS.get(item_id, GLOW_COLORS.get(cat_key, (245, 200, 75)))

    if is_selected:
        # Float upward above pedestal
        float_dy = int(-6 + 2.0 * math.sin(pulse_phase * 2.2 + rect.y * 0.1))
        aura_rad = 28
        aura_surf = pygame.Surface((aura_rad * 2, aura_rad * 2), pygame.SRCALPHA)
        pulse_alpha = int(105 + 35 * math.sin(pulse_phase * 3.0))
        # Concentric soft radial light
        pygame.draw.circle(aura_surf, (*glow_color, pulse_alpha), (aura_rad, aura_rad), aura_rad)
        pygame.draw.circle(aura_surf, (255, 255, 255, int(pulse_alpha * 0.4)), (aura_rad, aura_rad), int(aura_rad * 0.5))
        surface.blit(aura_surf, (pedestal_cx - aura_rad, pedestal_cy + float_dy - aura_rad))

        # Pedestal reflects subtle colored light puddle
        puddle_surf = pygame.Surface((ped_r * 2, ped_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(puddle_surf, (*glow_color, 75), (ped_r, ped_r), ped_r - 3)
        surface.blit(puddle_surf, (pedestal_cx - ped_r, pedestal_cy - ped_r))
    elif is_focused or is_hovered:
        float_dy = -2
        # Soft focus ring
        if has_item:
            focus_surf = pygame.Surface((ped_r * 2 + 8, ped_r * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(focus_surf, (220, 185, 95, 45), (ped_r + 4, ped_r + 4), ped_r + 3)
            surface.blit(focus_surf, (pedestal_cx - ped_r - 4, pedestal_cy - ped_r - 4))
    elif has_item:
        float_dy = int(1.2 * math.sin(pulse_phase * 1.5 + rect.y * 0.1))
    else:
        float_dy = 0

    relic_cy = pedestal_cy + float_dy

    # 4. Render Relic on Pedestal using Lumen Procedural Art
    if cat_key == "crystals":
        draw_crystal_relic(
            surface=surface,
            cx=pedestal_cx,
            cy=relic_cy,
            item_id=item_id,
            has_item=has_item,
            is_selected=is_selected,
            pulse_phase=pulse_phase,
        )
    else:
        # Keys and Mirrors reuse InventoryModal._draw_item_icon
        cat_name = "KEY" if cat_key == "keys" else "MIRROR"
        draw_dict = {
            **item,
            "category": cat_name,
            "collected": has_item,
        }
        InventoryModal._draw_item_icon(None, surface, pedestal_cx, relic_cy, draw_dict, small=True)

    # 5. Relic Description & Status Labels (Right of Pedestal)
    text_x = rect.x + 58
    text_max_w = rect.width - 66

    # Row 1: Relic Name
    if is_selected:
        name_col = (255, 235, 145)
    elif has_item:
        name_col = (235, 220, 195)
    else:
        name_col = (135, 125, 120)
    name_surf = font_bold.render(item["name"], True, name_col)
    surface.blit(name_surf, (text_x, rect.y + 10))

    # Row 2: Status Badge
    if is_selected:
        badge_txt = "SELECTED [v]"
        badge_col = (255, 215, 85)
        # Small glowing pip beside badge
        pygame.draw.circle(surface, glow_color, (text_x + 3, rect.y + 32), 3)
        pygame.draw.circle(surface, (255, 255, 255), (text_x + 3, rect.y + 32), 1)
        badge_offset_x = 10
    elif has_item:
        badge_txt = "IN SATCHEL"
        badge_col = (130, 215, 140)
        badge_offset_x = 0
    else:
        badge_txt = "MISSING"
        badge_col = (195, 105, 95)
        badge_offset_x = 0

    badge_surf = font_tag.render(badge_txt, True, badge_col)
    surface.blit(badge_surf, (text_x + badge_offset_x, rect.y + 27))

    # Row 3: Short Lore Snippet
    desc_str = item.get("desc", "")
    if len(desc_str) > 28:
        desc_str = desc_str[:26].rstrip() + "..."
    desc_col = (180, 170, 155) if has_item else (105, 95, 90)
    desc_surf = font_tag.render(desc_str, True, desc_col)
    surface.blit(desc_surf, (text_x, rect.y + 45))


def draw_crystal_relic(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    item_id: str,
    has_item: bool,
    is_selected: bool,
    pulse_phase: float,
) -> None:
    """Renders an illuminated Level 3 crystal spire with radial light and faceted highlights.

    Ensures crystals appear as illuminated glowing prisms rather than flat diamond dots:
    - Circular glow beneath the crystal
    - Soft radial light effect
    - Faceted 3D prism polygons
    - Specular center ridge highlight
    - Starburst gleam at apex
    """
    scale = 0.70

    if not has_item:
        c_core = (50, 45, 55)
        c_face_dark = (36, 32, 40)
        c_face_light = (65, 58, 70)
        c_hl = (85, 78, 90)
        c_glow = (60, 50, 70)
    elif "1" in item_id or "red" in item_id:
        c_core = (245, 55, 80)
        c_face_dark = (175, 25, 45)
        c_face_light = (255, 95, 120)
        c_hl = (255, 195, 210)
        c_glow = (255, 70, 95)
    elif "2" in item_id or "blue" in item_id:
        c_core = (55, 155, 255)
        c_face_dark = (25, 95, 195)
        c_face_light = (120, 205, 255)
        c_hl = (215, 240, 255)
        c_glow = (65, 175, 255)
    else:
        c_core = (50, 225, 115)
        c_face_dark = (22, 155, 70)
        c_face_light = (110, 250, 160)
        c_hl = (205, 255, 225)
        c_glow = (60, 245, 130)

    cw = int(9 * scale)
    ch = int(18 * scale)

    # 1. Soft Radial Light Effect
    if has_item:
        glow_r = int(ch + 8 + (6 if is_selected else 0))
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        base_a = 90 if is_selected else 40
        pulse_a = int(base_a + 25 * math.sin(pulse_phase * 2.5))
        pygame.draw.circle(glow_surf, (*c_glow, pulse_a), (glow_r, glow_r), glow_r)
        pygame.draw.circle(glow_surf, (255, 255, 255, int(pulse_a * 0.5)), (glow_r, glow_r), int(glow_r * 0.45))
        surface.blit(glow_surf, (cx - glow_r, cy - glow_r))

    # 2. Faceted Double-Pointed Prism Spire
    top_pt = (cx, cy - ch)
    bot_pt = (cx, cy + ch)
    mid_l = (cx - cw, cy)
    mid_r = (cx + cw, cy)
    mid_c = (cx, cy + int(3 * scale))

    # Left Dark Shaded Facets
    pygame.draw.polygon(surface, c_face_dark, [top_pt, mid_l, mid_c])
    pygame.draw.polygon(surface, c_face_dark, [mid_l, bot_pt, mid_c])

    # Right Light Illuminated Facets
    pygame.draw.polygon(surface, c_face_light, [top_pt, mid_r, mid_c])
    pygame.draw.polygon(surface, c_face_light, [mid_r, bot_pt, mid_c])

    # 3. Specular Center Ridge Highlight Line
    hl_width = 2 if is_selected else 1
    pygame.draw.line(surface, c_hl, top_pt, mid_c, hl_width)
    pygame.draw.line(surface, c_hl, mid_c, bot_pt, 1)

    # 4. Brilliant Starburst Gleam at Crystal Apex (strongest when selected)
    if has_item:
        star_x = cx + int(3 * scale)
        star_y = cy - int(6 * scale)
        star_len = 4 if is_selected else 2
        pygame.draw.line(surface, (255, 255, 255), (star_x - star_len, star_y), (star_x + star_len, star_y), 1)
        pygame.draw.line(surface, (255, 255, 255), (star_x, star_y - star_len), (star_x, star_y + star_len), 1)
        pygame.draw.circle(surface, (255, 255, 255), (star_x, star_y), 1)


"""systems/forge_ui.py — Dedicated Forge Interaction Interface (Milestone 4B).

Provides an interactive temple altar modal featuring:
- Three clearly separated selection slots: Key, Mirror, Crystal.
- Visual display of selected relics and inventory availability.
- Missing relics explicitly shown as unavailable.
- 'Submit Combination' and 'Clear Selection' actions.
- Reserved feedback area for validation/status feedback without revealing puzzle outcomes.
- Robust keyboard navigation (Arrows/WASD/Enter/Space/Hotkeys) and mouse click support.
- Zero item consumption (relics remain in satchel).
- Resilient inventory handling (gracefully handles None, dicts, or custom objects).
"""

import math
from typing import Any, Callable, Optional
import pygame

from systems.audio import audio
from systems.ui import wrap_text
from systems.forge import ForgeEngine
from systems.forge_visuals import (
    draw_central_crucible,
    draw_relic_pedestal,
    draw_crystal_relic,
    GLOW_COLORS,
)


# Canonical relic definitions matching LUMEN's inventory system
FORGE_CATEGORIES = [
    {
        "key": "keys",
        "title": "KEY SOCKET",
        "short_name": "Key",
        "items": [
            {
                "id": "key_bronze",
                "name": "Bronze Key",
                "color": (185, 120, 65),
                "desc": "Heavy brass key recovered from the upper temple urns.",
                "aliases": ["key_bronze", "bronze_key"],
            },
            {
                "id": "key_silver",
                "name": "Silver Key",
                "color": (195, 205, 220),
                "desc": "Fine silver key etched with solar wing motifs.",
                "aliases": ["key_silver", "silver_key"],
            },
            {
                "id": "key_gold",
                "name": "Gold Key",
                "color": (245, 200, 55),
                "desc": "Sacred gilded key that unsealed the Sanctum portals.",
                "aliases": ["key_gold", "gold_key"],
            },
        ],
    },
    {
        "key": "mirrors",
        "title": "MIRROR SOCKET",
        "short_name": "Mirror",
        "items": [
            {
                "id": "mirror_red",
                "name": "Crimson Mirror",
                "color": (235, 75, 75),
                "desc": "Faceted ruby reflector focusing thermal wavelengths.",
                "aliases": ["mirror_red", "red_mirror", "red"],
            },
            {
                "id": "mirror_blue",
                "name": "Azure Mirror",
                "color": (65, 145, 250),
                "desc": "Deep sapphire reflector directing coherent solar light.",
                "aliases": ["mirror_blue", "blue_mirror", "blue"],
            },
            {
                "id": "mirror_green",
                "name": "Emerald Mirror",
                "color": (70, 225, 110),
                "desc": "Verdant crystal lens shifting harmonic ray frequencies.",
                "aliases": ["mirror_green", "green_mirror", "green"],
            },
        ],
    },
    {
        "key": "crystals",
        "title": "CRYSTAL SOCKET",
        "short_name": "Crystal",
        "items": [
            {
                "id": "crystal_1",
                "name": "Resonance Crystal I",
                "color": (255, 95, 120),
                "desc": "Solar prism crystal attuned to the primary resonance wave.",
                "aliases": ["crystal_1", "crystal_red", "red"],
            },
            {
                "id": "crystal_2",
                "name": "Resonance Crystal II",
                "color": (85, 175, 255),
                "desc": "Harmonic sapphire node pulsating with calm celestial flux.",
                "aliases": ["crystal_2", "crystal_blue", "blue"],
            },
            {
                "id": "crystal_3",
                "name": "Resonance Crystal III",
                "color": (80, 240, 140),
                "desc": "Convergence emerald prism carrying living temple resonance.",
                "aliases": ["crystal_3", "crystal_green", "green"],
            },
        ],
    },
]


def check_item_possession(inventory, item_id: str, aliases: list[str] | None = None) -> bool:
    """Safely determines if the player possesses the requested relic item."""
    if inventory is None:
        return False

    # 1. Dictionary structure handling
    if isinstance(inventory, dict):
        for k in ("keys", "mirrors", "crystals"):
            col = inventory.get(k, [])
            if isinstance(col, (list, tuple, set)):
                if item_id in col or (aliases and any(a in col for a in aliases)):
                    return True
        return False

    # 2. Standard engine.inventory.Inventory methods
    if hasattr(inventory, "has_key") and callable(inventory.has_key) and inventory.has_key(item_id):
        return True
    if hasattr(inventory, "has_mirror") and callable(inventory.has_mirror) and inventory.has_mirror(item_id):
        return True
    if hasattr(inventory, "has_crystal") and callable(inventory.has_crystal) and inventory.has_crystal(item_id):
        return True

    # 3. Check aliases if defined
    if aliases:
        for alias in aliases:
            if hasattr(inventory, "has_key") and callable(inventory.has_key) and inventory.has_key(alias):
                return True
            if hasattr(inventory, "has_mirror") and callable(inventory.has_mirror) and inventory.has_mirror(alias):
                return True
            if hasattr(inventory, "has_crystal") and callable(inventory.has_crystal) and inventory.has_crystal(alias):
                return True

    # 4. Direct collection attributes (lists/sets)
    for attr in ("keys", "mirrors", "crystals"):
        col = getattr(inventory, attr, None)
        if isinstance(col, (list, tuple, set)):
            if item_id in col:
                return True
            if aliases and any(a in col for a in aliases):
                return True

    return False


class ForgeModal:
    """Interactive Ancient Forge chamber interface (Milestone 4B)."""

    def __init__(
        self,
        screen_width: int = 800,
        screen_height: int = 600,
        engine: ForgeEngine | None = None,
        on_lose_life: Any = None,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.engine: ForgeEngine = engine if engine is not None else ForgeEngine()

        self.is_open: bool = False
        self.anim_alpha: float = 0.0
        self.pulse_phase: float = 0.0
        self.resonance_phase: float = 0.0

        # Slot selections: stores relic ID or None
        self.selected_key: str | None = None
        self.selected_mirror: str | None = None
        self.selected_crystal: str | None = None
        self.inventory = None
        self.on_solve = None
        self.on_lose_life = on_lose_life
        self.just_solved: bool = False

        # Feedback banner state
        self.feedback_msg: str = (
            f"Align one relic per socket and submit. Attempts remaining: "
            f"{self.engine.attempts_left}/{self.engine.max_attempts}."
        )
        self.feedback_color: tuple[int, int, int] = (235, 215, 160)

        # Keyboard navigation focus:
        # col: 0 = Keys, 1 = Mirrors, 2 = Crystals
        # row: 0, 1, 2 = Candidate items; 3 = Actions row
        self.focus_col: int = 0
        self.focus_row: int = 0
        # When focus_row == 3, action_idx: 0 = Clear, 1 = Submit
        self.action_idx: int = 1

        # Interactive click bounding boxes (updated on draw)
        self.item_rects: dict[tuple[int, int], pygame.Rect] = {}
        self.btn_clear_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.btn_submit_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.btn_close_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)

        # Fonts
        self.font_title = pygame.font.SysFont("georgia", 18, bold=True)
        self.font_subtitle = pygame.font.SysFont("consolas", 12)
        self.font_sec = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_body = pygame.font.SysFont("consolas", 12)
        self.font_bold = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 11)
        self.font_tag = pygame.font.SysFont("consolas", 10, bold=True)

    @property
    def title(self) -> str:
        return "THE ANCIENT FORGE"

    def open(self, inventory=None):
        """Opens the Forge interface and activates pause."""
        self.is_open = True
        self.anim_alpha = 0.0
        if inventory is not None:
            self.inventory = inventory
        if self.engine.is_solved:
            self.feedback_msg = "Harmonic resonance achieved! The Lumen Sigil has been claimed."
            self.feedback_color = (255, 235, 120)
        elif self.engine.is_locked:
            self.feedback_msg = "The Forge mechanisms lock with ancient finality. No attempts remain."
            self.feedback_color = (235, 95, 85)
        else:
            self.feedback_msg = (
                f"Align one relic per socket and submit. Attempts remaining: "
                f"{self.engine.attempts_left}/{self.engine.max_attempts}."
            )
            self.feedback_color = (235, 215, 160)
        audio.play("clue")

    def close(self):
        """Closes the Forge interface and resumes chamber exploration."""
        self.is_open = False
        audio.play("clue")

    def toggle(self, inventory=None):
        if self.is_open:
            self.close()
        else:
            self.open(inventory)

    def update(self, dt: float):
        """Updates animation timings and pulsing visual glow."""
        if not self.is_open:
            return
        if self.anim_alpha < 1.0:
            self.anim_alpha = min(1.0, self.anim_alpha + dt * 7.0)
        self.pulse_phase = (self.pulse_phase + dt * 4.0) % (2 * math.pi)
        self.resonance_phase = (self.resonance_phase + dt * 2.5) % (2 * math.pi)

    def get_selection(self) -> dict[str, str | None]:
        """Returns the current relic selections across the three slots."""
        return {
            "key": self.selected_key,
            "mirror": self.selected_mirror,
            "crystal": self.selected_crystal,
        }

    def select_slot_item(self, category_key: str, item_id: str, inventory=None) -> bool:
        """Selects a relic item for the given category without consuming it."""
        if inventory is None:
            inventory = self.inventory

        # Find item definition
        item_def = None
        for cat in FORGE_CATEGORIES:
            if cat["key"] == category_key:
                for itm in cat["items"]:
                    if itm["id"] == item_id:
                        item_def = itm
                        break
                break

        if not item_def:
            return False

        # Verify possession
        has_item = check_item_possession(inventory, item_id, item_def.get("aliases"))
        if not has_item:
            self.feedback_msg = f"{item_def['name']} is missing from your satchel."
            self.feedback_color = (235, 125, 95)
            audio.play("door_locked")
            return False

        # Apply selection
        if category_key == "keys":
            self.selected_key = item_id
        elif category_key == "mirrors":
            self.selected_mirror = item_id
        elif category_key == "crystals":
            self.selected_crystal = item_id

        self.feedback_msg = f"{item_def['name']} placed into the {category_key[:-1]} conduit."
        self.feedback_color = (235, 220, 165)
        audio.play("clue")
        return True

    def clear_selection(self):
        """Resets all three selection slots without modifying inventory."""
        self.selected_key = None
        self.selected_mirror = None
        self.selected_crystal = None
        if self.engine.is_solved:
            self.feedback_msg = "Selections cleared. The Forge conduits remain harmonized."
            self.feedback_color = (255, 235, 120)
        elif self.engine.is_locked:
            self.feedback_msg = "Selections cleared. The Forge remains locked."
            self.feedback_color = (235, 95, 85)
        else:
            self.feedback_msg = (
                f"Selections cleared. Attempts remaining: "
                f"{self.engine.attempts_left}/{self.engine.max_attempts}."
            )
            self.feedback_color = (205, 195, 175)
        audio.play("clue")

    def submit_combination(self, inventory=None) -> bool:
        """Validates slot completeness and evaluates combination against ForgeEngine rules."""
        if inventory is None:
            inventory = self.inventory

        # Guard 1: Already solved
        if self.engine.is_solved:
            self.feedback_msg = "The Forge conduits are already harmonized. The Lumen Sigil has been claimed."
            self.feedback_color = (255, 235, 120)
            audio.play("clue")
            return True

        # Guard 2: Already locked
        if self.engine.is_locked:
            self.feedback_msg = "The Forge mechanisms lock with ancient finality. No attempts remain."
            self.feedback_color = (235, 95, 85)
            audio.play("door_locked")
            return False

        k = self.selected_key
        m = self.selected_mirror
        c = self.selected_crystal

        # Guard 3: Incomplete selection (consumes 0 attempts)
        if not (k and m and c):
            missing = []
            if not k:
                missing.append("Key")
            if not m:
                missing.append("Mirror")
            if not c:
                missing.append("Crystal")
            self.feedback_msg = f"Incomplete offering: Select a {', '.join(missing)} before submitting."
            self.feedback_color = (245, 155, 95)
            audio.play("door_locked")
            return False

        # Submit to ForgeEngine (consumes exactly 1 attempt)
        success, status = self.engine.submit(k, m, c)

        if status == "success":
            if inventory is not None:
                if hasattr(inventory, "add_sigil"):
                    inventory.add_sigil()
                elif isinstance(inventory, dict):
                    inventory["has_sigil"] = True
            self.just_solved = True
            if self.on_solve and callable(self.on_solve):
                self.on_solve()
            self.feedback_msg = "Harmonic resonance achieved! The Lumen Sigil awakens within the crucible!"
            self.feedback_color = (255, 235, 120)
            audio.play("door_open")
            return True
        elif status == "locked" or self.engine.attempts_left <= 0:
            if callable(getattr(self, "on_lose_life", None)):
                self.on_lose_life("Exhausted Forge Attempts")
            self.engine.attempts_used = 0
            self.engine.is_locked = False
            self.feedback_msg = "Attempts exhausted. You lost one life. The conduits have reset."
            self.feedback_color = (235, 95, 85)
            audio.play("door_locked")
            return False
        else:  # status == "incorrect"
            self.feedback_msg = (
                f"The conduits shudder in dissonance. Attempts remaining: "
                f"{self.engine.attempts_left}/{self.engine.max_attempts}."
            )
            self.feedback_color = (245, 155, 95)
            audio.play("door_locked")
            return False

    def handle_keydown(self, key: int, inventory=None) -> bool:
        """Handles keyboard navigation, slot selection, actions, and dismissal."""
        if not self.is_open:
            return False

        if inventory is None:
            inventory = self.inventory

        # Close shortcuts
        if key in (pygame.K_ESCAPE,):
            self.close()
            return True

        # Quick action hotkeys
        if key in (pygame.K_c, pygame.K_x):
            self.clear_selection()
            return True

        if key in (pygame.K_s,):
            # If all 3 slots are selected or focused on action row, submit.
            # Otherwise, move down if focus_row < 3 to support WASD navigation seamlessly.
            if (self.selected_key and self.selected_mirror and self.selected_crystal) or self.focus_row == 3:
                self.submit_combination(inventory)
                return True
            elif self.focus_row < 3:
                self.focus_row += 1
                audio.play("clue")
                return True
            else:
                self.submit_combination(inventory)
                return True

        # Number hotkeys [1], [2], [3] select item in active category
        if key in (pygame.K_1, pygame.K_2, pygame.K_3):
            item_idx = key - pygame.K_1
            cat = FORGE_CATEGORIES[self.focus_col]
            if item_idx < len(cat["items"]):
                item_id = cat["items"][item_idx]["id"]
                self.select_slot_item(cat["key"], item_id, inventory)
            return True

        # Navigation: Column switching (Left / Right / Tab)
        if key in (pygame.K_LEFT, pygame.K_a):
            if self.focus_row == 3:
                self.action_idx = 0 if self.action_idx == 1 else 1
            else:
                self.focus_col = (self.focus_col - 1) % 3
            audio.play("clue")
            return True

        if key in (pygame.K_RIGHT, pygame.K_d):
            if self.focus_row == 3:
                self.action_idx = 1 if self.action_idx == 0 else 0
            else:
                self.focus_col = (self.focus_col + 1) % 3
            audio.play("clue")
            return True

        if key == pygame.K_TAB:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                self.focus_col = (self.focus_col - 1) % 3
            else:
                self.focus_col = (self.focus_col + 1) % 3
            audio.play("clue")
            return True

        # Navigation: Row switching (Up / Down)
        if key in (pygame.K_UP, pygame.K_w):
            if self.focus_row > 0:
                self.focus_row -= 1
                audio.play("clue")
            return True

        if key in (pygame.K_DOWN, pygame.K_s):
            if self.focus_row < 3:
                self.focus_row += 1
                audio.play("clue")
            return True

        # Activation (Space / Return / E)
        if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
            if self.focus_row in (0, 1, 2):
                cat = FORGE_CATEGORIES[self.focus_col]
                item_id = cat["items"][self.focus_row]["id"]
                self.select_slot_item(cat["key"], item_id, inventory)
            elif self.focus_row == 3:
                if self.action_idx == 0:
                    self.clear_selection()
                else:
                    self.submit_combination(inventory)
            return True

        return True

    def handle_click(self, gx: int, gy: int, inventory=None) -> bool:
        """Handles mouse selection of relic cards, action buttons, and close button."""
        if not self.is_open:
            return False

        if inventory is None:
            inventory = self.inventory

        # Close button
        if self.btn_close_rect.collidepoint(gx, gy):
            self.close()
            return True

        # Clear button
        if self.btn_clear_rect.collidepoint(gx, gy):
            self.clear_selection()
            return True

        # Submit button
        if self.btn_submit_rect.collidepoint(gx, gy):
            self.submit_combination(inventory)
            return True

        # Item cards
        for (col_idx, item_idx), rect in self.item_rects.items():
            if rect.collidepoint(gx, gy):
                self.focus_col = col_idx
                self.focus_row = item_idx
                cat = FORGE_CATEGORIES[col_idx]
                item_id = cat["items"][item_idx]["id"]
                self.select_slot_item(cat["key"], item_id, inventory)
                return True

        return True

    def draw(self, surface: pygame.Surface, inventory=None):
        """Renders the Forge interaction tablet, slots, items, feedback, and action buttons."""
        if not self.is_open:
            return

        alpha_int = int(245 * max(0.1, self.anim_alpha))

        # 1. Dim background
        dim = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim.fill((6, 4, 10, int(195 * self.anim_alpha)))
        surface.blit(dim, (0, 0))

        # 2. Main Tablet Frame (720 x 510, centered in 800 x 600)
        mw, mh = 720, 510
        mx = (self.screen_width - mw) // 2
        my = (self.screen_height - mh) // 2

        tablet = pygame.Surface((mw, mh), pygame.SRCALPHA)
        tablet.fill((20, 16, 26, alpha_int))
        pygame.draw.rect(tablet, (195, 155, 75), (0, 0, mw, mh), width=2, border_radius=10)
        pygame.draw.rect(tablet, (80, 62, 38), (5, 5, mw - 10, mh - 10), width=1, border_radius=8)

        # Ornamental brass rivets at corners
        for rx, ry in [(7, 7), (mw - 11, 7), (7, mh - 11), (mw - 11, mh - 11)]:
            pygame.draw.rect(tablet, (245, 205, 85), (rx, ry, 4, 4))
        surface.blit(tablet, (mx, my))

        # 3. Header: Title & Atmospheric description
        t_surf = self.font_title.render("THE ANCIENT FORGE", True, (248, 224, 148))
        surface.blit(t_surf, (mx + (mw - t_surf.get_width()) // 2, my + 16))

        # Attempts/Status Badge in Header
        if self.engine.is_solved:
            badge_txt = "[HARMONIZED]"
            badge_col = (255, 235, 120)
        elif self.engine.is_locked:
            badge_txt = "[SEALED & LOCKED]"
            badge_col = (235, 95, 85)
        else:
            badge_txt = f"[ATTEMPTS: {self.engine.attempts_left}/{self.engine.max_attempts}]"
            badge_col = (220, 195, 140)
        b_surf = self.font_tag.render(badge_txt, True, badge_col)
        surface.blit(b_surf, (mx + 26, my + 20))

        sub_txt = "Align sacred relics within the three elemental conduits to awaken the volcanic crucible."
        sub_surf = self.font_subtitle.render(sub_txt, True, (195, 185, 165))
        surface.blit(sub_surf, (mx + (mw - sub_surf.get_width()) // 2, my + 44))

        pygame.draw.line(surface, (140, 110, 50), (mx + 36, my + 64), (mx + mw - 36, my + 64), 1)
        pygame.draw.circle(surface, (220, 185, 80), (mx + mw // 2, my + 64), 3)

        # Close [X] button top right
        self.btn_close_rect = pygame.Rect(mx + mw - 38, my + 14, 24, 24)
        pygame.draw.rect(surface, (36, 28, 44), self.btn_close_rect, border_radius=4)
        pygame.draw.rect(surface, (150, 120, 65), self.btn_close_rect, width=1, border_radius=4)
        x_label = self.font_bold.render("X", True, (230, 205, 150))
        surface.blit(x_label, (self.btn_close_rect.centerx - x_label.get_width() // 2,
                               self.btn_close_rect.centery - x_label.get_height() // 2))

        # 4. Central Forge Crucible (Visually Dominant in Upper Focal Area)
        draw_central_crucible(
            surface=surface,
            cx=mx + mw // 2,
            cy=my + 82,
            state="solved" if self.engine.is_solved else ("locked" if self.engine.is_locked else "active"),
            attempts_left=self.engine.attempts_left,
            max_attempts=self.engine.max_attempts,
            selected_key=self.selected_key,
            selected_mirror=self.selected_mirror,
            selected_crystal=self.selected_crystal,
            pulse_phase=self.pulse_phase,
            resonance_phase=self.resonance_phase,
        )

        # 5. Three Relic Category Temple Sanctuaries
        col_w = 216
        col_gap = 14
        left_margin = mx + 23
        start_y = my + 114

        mouse_pos = pygame.mouse.get_pos()
        self.item_rects.clear()

        for c_idx, cat in enumerate(FORGE_CATEGORIES):
            col_x = left_margin + c_idx * (col_w + col_gap)
            col_rect = pygame.Rect(col_x, start_y, col_w, 260)

            # Sanctuary Alcove Frame
            is_col_focused = (self.focus_col == c_idx)
            c_bg = (26, 21, 35, 220) if is_col_focused else (20, 16, 28, 180)
            c_border = (230, 190, 85) if is_col_focused else (90, 70, 48)

            c_surf = pygame.Surface((col_w, 260), pygame.SRCALPHA)
            c_surf.fill(c_bg)
            pygame.draw.rect(c_surf, c_border, (0, 0, col_w, 260), width=2 if is_col_focused else 1, border_radius=8)
            surface.blit(c_surf, (col_x, start_y))

            # Sanctuary Header: Category Name
            cat_header = self.font_sec.render(cat["title"], True, (245, 215, 120) if is_col_focused else (195, 175, 140))
            surface.blit(cat_header, (col_x + (col_w - cat_header.get_width()) // 2, start_y + 8))

            # Active Offering Status Pill
            cur_sel_id = getattr(self, f"selected_{cat['key'][:-1]}", None)
            sel_pill_rect = pygame.Rect(col_x + 8, start_y + 28, col_w - 16, 22)
            pill_surf = pygame.Surface((sel_pill_rect.width, sel_pill_rect.height), pygame.SRCALPHA)

            if cur_sel_id:
                sel_item_def = next((it for it in cat["items"] if it["id"] == cur_sel_id), None)
                sel_name = sel_item_def["name"] if sel_item_def else cur_sel_id
                pill_surf.fill((45, 34, 20, 240))
                pygame.draw.rect(pill_surf, (240, 195, 75), (0, 0, sel_pill_rect.width, sel_pill_rect.height), width=1, border_radius=4)
                surface.blit(pill_surf, sel_pill_rect.topleft)

                # Active glowing dot
                dot_col = sel_item_def["color"] if sel_item_def else (240, 195, 75)
                pygame.draw.circle(surface, dot_col, (sel_pill_rect.x + 10, sel_pill_rect.centery), 4)

                sel_txt = self.font_tag.render(sel_name.upper(), True, (255, 235, 160))
                surface.blit(sel_txt, (sel_pill_rect.x + 20, sel_pill_rect.centery - sel_txt.get_height() // 2))
            else:
                pill_surf.fill((16, 13, 22, 180))
                pygame.draw.rect(pill_surf, (75, 62, 50), (0, 0, sel_pill_rect.width, sel_pill_rect.height), width=1, border_radius=4)
                surface.blit(pill_surf, sel_pill_rect.topleft)
                none_txt = self.font_tag.render("[EMPTY CONDUIT]", True, (135, 125, 115))
                surface.blit(none_txt, (sel_pill_rect.centerx - none_txt.get_width() // 2,
                                        sel_pill_rect.centery - none_txt.get_height() // 2))

            # 3 Relic Choice Pedestals per category
            card_y = start_y + 56
            card_h = 63
            card_w = col_w - 16

            for i_idx, item in enumerate(cat["items"]):
                c_rect = pygame.Rect(col_x + 8, card_y + i_idx * (card_h + 4), card_w, card_h)
                self.item_rects[(c_idx, i_idx)] = c_rect

                has_item = check_item_possession(inventory, item["id"], item.get("aliases"))
                is_selected = (cur_sel_id == item["id"])
                is_focused = (is_col_focused and self.focus_row == i_idx)
                is_hovered = c_rect.collidepoint(mouse_pos)

                draw_relic_pedestal(
                    surface=surface,
                    rect=c_rect,
                    item=item,
                    cat_key=cat["key"],
                    has_item=has_item,
                    is_selected=is_selected,
                    is_focused=is_focused,
                    is_hovered=is_hovered,
                    pulse_phase=self.pulse_phase,
                    font_bold=self.font_bold,
                    font_tag=self.font_tag,
                )

        # 6. Reserved Feedback Area (Milestone 4B & future validation display)
        feed_y = my + 382
        feed_h = 36
        feed_w = mw - 46
        feed_rect = pygame.Rect(mx + 23, feed_y, feed_w, feed_h)

        feed_surf = pygame.Surface((feed_w, feed_h), pygame.SRCALPHA)
        feed_surf.fill((16, 12, 22, 230))
        pygame.draw.rect(feed_surf, (110, 85, 50), (0, 0, feed_w, feed_h), width=1, border_radius=6)
        surface.blit(feed_surf, feed_rect.topleft)

        # Centered feedback message
        msg_surf = self.font_bold.render(self.feedback_msg, True, self.feedback_color)
        surface.blit(msg_surf, (feed_rect.centerx - msg_surf.get_width() // 2,
                                feed_rect.centery - msg_surf.get_height() // 2))

        # 6. Action Buttons: [Clear Selection] and [Submit Combination]
        btn_y = my + 434
        btn_h = 38

        # Clear Selection Button
        clear_w = 190
        clear_x = mx + 60
        self.btn_clear_rect = pygame.Rect(clear_x, btn_y, clear_w, btn_h)

        is_clear_focused = (self.focus_row == 3 and self.action_idx == 0)
        is_clear_hovered = self.btn_clear_rect.collidepoint(mouse_pos)
        clear_bg = (38, 28, 42, 240) if (is_clear_focused or is_clear_hovered) else (24, 18, 30, 200)
        clear_border = (235, 195, 90) if (is_clear_focused or is_clear_hovered) else (140, 105, 60)

        c_btn_surf = pygame.Surface((clear_w, btn_h), pygame.SRCALPHA)
        c_btn_surf.fill(clear_bg)
        pygame.draw.rect(c_btn_surf, clear_border, (0, 0, clear_w, btn_h), width=2 if (is_clear_focused or is_clear_hovered) else 1, border_radius=6)
        surface.blit(c_btn_surf, self.btn_clear_rect.topleft)

        c_lbl = self.font_bold.render("[C] Clear Selection", True, (245, 220, 160) if (is_clear_focused or is_clear_hovered) else (195, 180, 160))
        surface.blit(c_lbl, (self.btn_clear_rect.centerx - c_lbl.get_width() // 2,
                             self.btn_clear_rect.centery - c_lbl.get_height() // 2))

        # Submit Combination Button
        submit_w = 240
        submit_x = mx + mw - submit_w - 60
        self.btn_submit_rect = pygame.Rect(submit_x, btn_y, submit_w, btn_h)

        is_submit_focused = (self.focus_row == 3 and self.action_idx == 1)
        is_submit_hovered = self.btn_submit_rect.collidepoint(mouse_pos)
        sub_bg = (52, 38, 20, 245) if (is_submit_focused or is_submit_hovered) else (34, 25, 16, 210)
        sub_border = (255, 220, 95) if (is_submit_focused or is_submit_hovered) else (180, 135, 65)

        s_btn_surf = pygame.Surface((submit_w, btn_h), pygame.SRCALPHA)
        s_btn_surf.fill(sub_bg)
        pygame.draw.rect(s_btn_surf, sub_border, (0, 0, submit_w, btn_h), width=2 if (is_submit_focused or is_submit_hovered) else 1, border_radius=6)
        surface.blit(s_btn_surf, self.btn_submit_rect.topleft)

        if self.engine.is_solved:
            s_label_str = "[S] Forge Harmonized"
            s_label_col = (255, 235, 120)
        elif self.engine.is_locked:
            s_label_str = "[S] Forge Locked"
            s_label_col = (220, 120, 110)
        else:
            s_label_str = "[S] Submit Combination"
            s_label_col = (255, 240, 175) if (is_submit_focused or is_submit_hovered) else (225, 200, 140)

        s_lbl = self.font_bold.render(s_label_str, True, s_label_col)
        surface.blit(s_lbl, (self.btn_submit_rect.centerx - s_lbl.get_width() // 2,
                             self.btn_submit_rect.centery - s_lbl.get_height() // 2))

        # 7. Navigation footer hint
        foot_txt = "[Arrows/WASD] Navigate   |   [SPACE/E] Select/Toggle   |   [1-3] Quick Select   |   [ESC] Exit"
        foot_surf = self.font_small.render(foot_txt, True, (165, 150, 130))
        surface.blit(foot_surf, (mx + (mw - foot_surf.get_width()) // 2, my + mh - 22))

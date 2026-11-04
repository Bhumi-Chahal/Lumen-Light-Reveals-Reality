"""
Lumen — systems/level_select_ui.py
Milestone 6: Ancient Temple Level Selection and Replay Modal.

Provides a polished, responsive level selection interface displaying 5 level slots:
- Level 1 — The First Light (The Ancient Sanctum)
- Level 2 — The Shadow Trial (The Deepening Dark)
- Level 3 — The Mirror Chambers (The Path of Light)
- Level 4 — The Ancient Forge
- Level 5 — The Hall of Fate (Coming Soon)

Fixes layout so that titles, descriptions, status badges, keyboard hints,
and bottom action buttons never overlap and occupy dedicated, consistent regions.
Supports full keyboard (Up/Down/WASD/Enter/Space/ESC) and mouse click navigation.
"""

import math
import pygame
from typing import Optional, Callable, Dict, Any, List, Set

from engine.progression import LEVEL_SLOTS, ProgressionManager, progression
from systems.audio import audio


class LevelSelectModal:
    """Temple-themed Level Selection and Replay interface with non-overlapping layout."""

    def __init__(self, render_w: int = 800, render_h: int = 600,
                 prog_mgr: Optional[ProgressionManager] = None, **kwargs):
        self.screen_width = kwargs.get("screen_width", kwargs.get("screen_w", render_w))
        self.screen_height = kwargs.get("screen_height", kwargs.get("screen_h", render_h))
        self.prog_mgr = prog_mgr or progression

        self.is_open: bool = False
        self.selected_index: int = 0
        self.pulse: float = 0.0
        self.anim_alpha: float = 0.0
        self.on_select_level: Optional[Callable[[str], None]] = None
        self.accessible_levels: Optional[Set[str]] = None

        # Dimensions
        self.card_w: int = 700
        self.card_h: int = 70

        # Fonts
        if not pygame.font.get_init():
            pygame.font.init()
        self.font_header = pygame.font.SysFont("georgia", 20, bold=True)
        self.font_sub = pygame.font.SysFont("consolas", 12)
        self.font_slot_title = pygame.font.SysFont("georgia", 14, bold=True)
        self.font_slot_sub = pygame.font.SysFont("consolas", 10, bold=True)
        self.font_slot_desc = pygame.font.SysFont("consolas", 11)
        self.font_badge = pygame.font.SysFont("consolas", 10, bold=True)
        self.font_btn = pygame.font.SysFont("consolas", 12, bold=True)

        # Slot bounding rects for mouse interaction (computed in draw)
        self.slot_rects: List[pygame.Rect] = []
        tx, ty, tw, th = self._calc_tablet_rect()
        btn_y = ty + th - 62
        self.back_btn_rect: pygame.Rect = pygame.Rect(tx + 36, btn_y, 180, 36)
        self.play_btn_rect: pygame.Rect = pygame.Rect(tx + tw - 246, btn_y, 210, 36)

    @property
    def btn_back_rect(self) -> pygame.Rect:
        return self.back_btn_rect

    @property
    def btn_play_rect(self) -> pygame.Rect:
        return self.play_btn_rect

    def _calc_tablet_rect(self) -> tuple[int, int, int, int]:
        tw, th = 740, 556
        tx = (self.screen_width - tw) // 2
        ty = (self.screen_height - th) // 2
        return tx, ty, tw, th

    def _calc_card_rect(self, index: int) -> pygame.Rect:
        tx, ty, tw, th = self._calc_tablet_rect()
        slot_w = tw - 40
        slot_h = 70
        gap = 6
        start_y = ty + 66
        return pygame.Rect(tx + 20, start_y + index * (slot_h + gap), slot_w, slot_h)

    def open(self, on_select_level: Optional[Callable[[str], None]] = None,
             accessible_levels: Optional[Set[str]] = None):
        """Opens the Level Selection screen."""
        self.is_open = True
        self.anim_alpha = 0.0
        self.pulse = 0.0
        self.on_select_level = on_select_level
        self.accessible_levels = set(accessible_levels) if accessible_levels is not None else None
        # Set selection to first unlocked slot
        self.selected_index = 0

    def close(self):
        """Closes the Level Selection screen."""
        self.is_open = False

    def update(self, dt: float):
        """Updates animation pulse and modal alpha."""
        if not self.is_open:
            return
        if self.anim_alpha < 1.0:
            self.anim_alpha = min(1.0, self.anim_alpha + dt * 6.0)
        self.pulse = (self.pulse + dt * 3.5) % (2 * math.pi)

    def is_level_accessible(self, level_id: str) -> bool:
        """Returns True if the level is currently accessible."""
        lid = str(level_id).lower()
        if self.prog_mgr.is_coming_soon(lid):
            return False
        if self.accessible_levels is not None:
            return lid in self.accessible_levels
        return self.prog_mgr.is_unlocked(lid)

    def get_status(self, level_id: str) -> str:
        """Returns 'unlocked', 'locked', or 'coming_soon'."""
        lid = str(level_id).lower()
        if self.prog_mgr.is_coming_soon(lid):
            return "coming_soon"
        if self.is_level_accessible(lid):
            return "unlocked"
        return "locked"

    def get_selected_slot(self) -> Dict[str, Any]:
        """Returns the currently highlighted level slot definition."""
        return LEVEL_SLOTS[self.selected_index]

    def select_level(self, index: int) -> bool:
        """Selects a level by index if accessible."""
        if 0 <= index < len(LEVEL_SLOTS):
            slot = LEVEL_SLOTS[index]
            if self.is_level_accessible(slot["id"]):
                audio.play("door_open")
                self.close()
                if self.on_select_level:
                    self.on_select_level(slot["id"])
                return True
            else:
                audio.play("clue")
                return False
        return False

    def handle_input(self, event: pygame.event.Event,
                     game_pos: Optional[tuple[int, int]] = None) -> bool:
        """Handles keyboard and mouse events. Returns True if event was consumed."""
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(LEVEL_SLOTS)
                audio.play("clue")
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(LEVEL_SLOTS)
                audio.play("clue")
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.select_level(self.selected_index)
                return True
            elif event.key in (pygame.K_ESCAPE, pygame.K_l, pygame.K_2):
                self.close()
                audio.play("clue")
                return True
            return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            gx, gy = game_pos if game_pos is not None else event.pos

            # Back button
            if self.back_btn_rect.collidepoint(gx, gy):
                self.close()
                audio.play("clue")
                return True

            # Launch / Play button
            if self.play_btn_rect.collidepoint(gx, gy):
                self.select_level(self.selected_index)
                return True

            # Click on level slot cards
            for idx, r in enumerate(self.slot_rects):
                if r.collidepoint(gx, gy):
                    if idx == self.selected_index:
                        # Double-clicked / clicked currently selected -> launch
                        self.select_level(idx)
                    else:
                        self.selected_index = idx
                        audio.play("clue")
                    return True
            return True

        elif event.type == pygame.MOUSEMOTION:
            gx, gy = game_pos if game_pos is not None else event.pos
            for idx, r in enumerate(self.slot_rects):
                if r.collidepoint(gx, gy):
                    if self.selected_index != idx:
                        self.selected_index = idx
                    return True

        return True

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int, max_lines: int = 2) -> List[str]:
        """Wraps text into at most max_lines that fit within max_width."""
        words = text.split()
        lines: List[str] = []
        cur_words: List[str] = []
        for w in words:
            test_str = (" ".join(cur_words + [w])) if cur_words else w
            if font.size(test_str)[0] <= max_width:
                cur_words.append(w)
            else:
                if cur_words:
                    lines.append(" ".join(cur_words))
                    cur_words = [w]
                    if len(lines) >= max_lines:
                        break
                else:
                    lines.append(w)
                    cur_words = []
                    if len(lines) >= max_lines:
                        break
        if cur_words and len(lines) < max_lines:
            lines.append(" ".join(cur_words))
        return lines

    def draw(self, surface: pygame.Surface, game_pos: Optional[tuple[int, int]] = None):
        """Renders the level selection tablet with strictly bounded, non-overlapping layout."""
        if not self.is_open:
            return

        mx, my = game_pos if game_pos is not None else pygame.mouse.get_pos()

        # Dim backdrop
        dim = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim.fill((5, 4, 10, int(210 * self.anim_alpha)))
        surface.blit(dim, (0, 0))

        # Main tablet dimensions (740 x 556 fits comfortably on 800 x 600)
        tw, th = 740, 556
        tx = (self.screen_width - tw) // 2
        ty = (self.screen_height - th) // 2

        tablet = pygame.Surface((tw, th), pygame.SRCALPHA)
        tablet.fill((20, 17, 28, int(248 * self.anim_alpha)))
        pygame.draw.rect(tablet, (185, 150, 70), (0, 0, tw, th), width=2, border_radius=10)
        pygame.draw.rect(tablet, (75, 60, 40), (4, 4, tw - 8, th - 8), width=1, border_radius=8)

        # Corner gold gems
        for cx, cy in [(6, 6), (tw - 10, 6), (6, th - 10), (tw - 10, th - 10)]:
            pygame.draw.rect(tablet, (240, 205, 90), (cx, cy, 4, 4))
        surface.blit(tablet, (tx, ty))

        # Header Title
        t_surf = self.font_header.render("SANCTUM LEVEL SELECTION & REPLAY", True, (248, 225, 145))
        surface.blit(t_surf, (tx + (tw - t_surf.get_width()) // 2, ty + 14))

        sub_txt = "Revisit unlocked chambers to investigate clues or practice ancient trials"
        s_surf = self.font_sub.render(sub_txt, True, (185, 175, 160))
        surface.blit(s_surf, (tx + (tw - s_surf.get_width()) // 2, ty + 38))

        # Divider line
        div_y = ty + 58
        pygame.draw.line(surface, (155, 120, 55), (tx + 36, div_y), (tx + tw - 36, div_y), 1)
        pygame.draw.circle(surface, (235, 195, 80), (tx + tw // 2, div_y), 3)

        # Render 5 Level Slots (strict padding and height)
        slot_w = tw - 40   # 700
        slot_h = 70
        gap = 6
        start_y = ty + 66
        self.slot_rects = []

        for idx, slot in enumerate(LEVEL_SLOTS):
            sy = start_y + idx * (slot_h + gap)
            sx = tx + 20
            r = pygame.Rect(sx, sy, slot_w, slot_h)
            self.slot_rects.append(r)

            status = self.get_status(slot["id"])
            is_active = (idx == self.selected_index)
            is_hovered = r.collidepoint(mx, my)

            # Slot background card
            card = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
            if status == "unlocked":
                if is_active:
                    bg_col = (42, 34, 58, 240)
                    border_col = (255, 220, 110)
                    border_w = 2
                else:
                    bg_col = (28, 23, 38, 220) if is_hovered else (24, 20, 32, 190)
                    border_col = (200, 165, 85) if is_hovered else (120, 100, 60)
                    border_w = 1
            elif status == "coming_soon":
                bg_col = (18, 16, 26, 170)
                border_col = (85, 75, 110)
                border_w = 1
            else:  # locked
                bg_col = (15, 13, 22, 160)
                border_col = (65, 55, 70)
                border_w = 1

            pygame.draw.rect(card, bg_col, (0, 0, slot_w, slot_h), border_radius=6)
            pygame.draw.rect(card, border_col, (0, 0, slot_w, slot_h), width=border_w, border_radius=6)

            # Zone A: Chamber Number Pill Box (Left: x = 12..108)
            num_box = pygame.Surface((96, 50), pygame.SRCALPHA)
            num_box.fill((18, 14, 26, 200))
            pygame.draw.rect(num_box, (140, 115, 65) if status == "unlocked" else (65, 55, 70), (0, 0, 96, 50), width=1, border_radius=4)
            ch_lbl = self.font_slot_sub.render(f"CHAMBER", True, (215, 190, 110) if status == "unlocked" else (120, 110, 125))
            num_box.blit(ch_lbl, ((96 - ch_lbl.get_width()) // 2, 6))
            ch_num = self.font_slot_title.render(f"0{slot['number']}", True, (255, 235, 150) if status == "unlocked" else (115, 105, 120))
            num_box.blit(ch_num, ((96 - ch_num.get_width()) // 2, 22))
            card.blit(num_box, (12, 10))

            # Zone C: Dedicated Status Badge (Right: x = slot_w - bw - 14)
            # Status badges sit in a dedicated area on the right and never overlap text.
            bw = 108
            bh = 26
            bx = slot_w - bw - 14
            by = (slot_h - bh) // 2

            if status == "unlocked":
                badge_bg = (35, 60, 40, 240) if is_active else (25, 45, 30, 210)
                badge_border = (110, 230, 130) if is_active else (70, 170, 90)
                badge_text = "PLAYABLE" if is_active else "UNLOCKED"
                badge_text_col = (220, 255, 230)
            elif status == "coming_soon":
                badge_bg = (35, 30, 55, 200)
                badge_border = (120, 105, 180)
                badge_text = "COMING SOON"
                badge_text_col = (195, 180, 235)
            else:
                badge_bg = (25, 20, 30, 180)
                badge_border = (80, 70, 85)
                badge_text = "LOCKED"
                badge_text_col = (145, 135, 150)

            pygame.draw.rect(card, badge_bg, (bx, by, bw, bh), border_radius=4)
            pygame.draw.rect(card, badge_border, (bx, by, bw, bh), width=1, border_radius=4)
            badge_surf = self.font_badge.render(badge_text, True, badge_text_col)
            card.blit(badge_surf, (bx + (bw - badge_surf.get_width()) // 2, by + (bh - badge_surf.get_height()) // 2))

            # Zone B: Middle Content Area (x = 120 to bx - 14 = 564, max_width = 444)
            text_x = 120
            max_text_w = bx - text_x - 14

            # Level Name & Title
            title_text = f"{slot['title']} — {slot['name']}"
            if self.font_slot_title.size(title_text)[0] > max_text_w:
                title_text = slot["title"]
            t_col = (245, 235, 215) if status == "unlocked" else ((175, 165, 195) if status == "coming_soon" else (125, 120, 130))
            title_render = self.font_slot_title.render(title_text, True, t_col)
            card.blit(title_render, (text_x, 10))

            # Long descriptions wrap within their card boundaries and never reach the badge
            desc_col = (205, 195, 180) if status == "unlocked" else (115, 110, 120)
            desc_lines = self._wrap_text(slot["description"], self.font_slot_desc, max_text_w, max_lines=2)
            for line_idx, line_str in enumerate(desc_lines):
                line_surf = self.font_slot_desc.render(line_str, True, desc_col)
                card.blit(line_surf, (text_x, 32 + line_idx * 16))

            surface.blit(card, (sx, sy))

        # Bottom Actions Bar: Divided into 2 separate non-overlapping rows
        div2_y = ty + 448
        pygame.draw.line(surface, (90, 75, 55), (tx + 36, div2_y), (tx + tw - 36, div2_y), 1)

        # Row 1: Dedicated Keyboard Navigation Hints
        hint_y = ty + 458
        hint_txt = "UP / DOWN — Navigate chambers    |    ENTER — Select and play    |    ESC — Return"
        h_surf = self.font_sub.render(hint_txt, True, (170, 160, 145))
        surface.blit(h_surf, (tx + (tw - h_surf.get_width()) // 2, hint_y))

        # Row 2: Dedicated Action Buttons
        btn_y = ty + 490
        btn_h = 36
        active_slot = self.get_selected_slot()
        active_status = self.get_status(active_slot["id"])

        # Return to Menu Button (Bottom Left)
        self.back_btn_rect = pygame.Rect(tx + 36, btn_y, 180, btn_h)
        back_hovered = self.back_btn_rect.collidepoint(mx, my)
        back_surf = pygame.Surface((180, btn_h), pygame.SRCALPHA)
        back_bg = (36, 28, 48, 230) if back_hovered else (24, 18, 32, 200)
        back_border = (255, 220, 110) if back_hovered else (150, 120, 60)
        pygame.draw.rect(back_surf, back_bg, (0, 0, 180, btn_h), border_radius=6)
        pygame.draw.rect(back_surf, back_border, (0, 0, 180, btn_h), width=1, border_radius=6)
        back_lbl = self.font_btn.render("[ESC] Return to Menu", True, (240, 225, 200))
        back_surf.blit(back_lbl, ((180 - back_lbl.get_width()) // 2, (btn_h - back_lbl.get_height()) // 2))
        surface.blit(back_surf, (self.back_btn_rect.x, self.back_btn_rect.y))

        # Launch / Revisit Button (Bottom Right)
        self.play_btn_rect = pygame.Rect(tx + tw - 246, btn_y, 210, btn_h)
        play_hovered = self.play_btn_rect.collidepoint(mx, my)

        if active_status == "unlocked":
            play_surf = pygame.Surface((210, btn_h), pygame.SRCALPHA)
            play_bg = (45, 75, 45, 240) if play_hovered else (32, 58, 34, 210)
            play_border = (120, 240, 140) if play_hovered else (80, 190, 100)
            pygame.draw.rect(play_surf, play_bg, (0, 0, 210, btn_h), border_radius=6)
            pygame.draw.rect(play_surf, play_border, (0, 0, 210, btn_h), width=1, border_radius=6)
            btn_txt = f"[ENTER] Play Chamber {active_slot['number']}"
            play_lbl = self.font_btn.render(btn_txt, True, (230, 255, 230))
            play_surf.blit(play_lbl, ((210 - play_lbl.get_width()) // 2, (btn_h - play_lbl.get_height()) // 2))
            surface.blit(play_surf, (self.play_btn_rect.x, self.play_btn_rect.y))
        else:
            play_surf = pygame.Surface((210, btn_h), pygame.SRCALPHA)
            play_bg = (22, 18, 28, 160)
            play_border = (65, 55, 70)
            pygame.draw.rect(play_surf, play_bg, (0, 0, 210, btn_h), border_radius=6)
            pygame.draw.rect(play_surf, play_border, (0, 0, 210, btn_h), width=1, border_radius=6)
            btn_txt = "Chamber Locked" if active_status == "locked" else "Coming Soon"
            play_lbl = self.font_btn.render(btn_txt, True, (130, 120, 135))
            play_surf.blit(play_lbl, ((210 - play_lbl.get_width()) // 2, (btn_h - play_lbl.get_height()) // 2))
            surface.blit(play_surf, (self.play_btn_rect.x, self.play_btn_rect.y))

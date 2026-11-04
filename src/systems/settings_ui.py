"""systems/settings_ui.py - Functional Settings Menu for Lumen.

Implements Feature B (Functional Settings Menu):
- Accessible from Main Menu and Pause overlays.
- Organized into clear, functional categories:
    1. Audio: Music/Ambient Volume, SFX Volume, Mute All.
    2. Display: Fullscreen vs Windowed mode.
    3. Accessibility: Camera Screen Shake, Reduced Motion.
    4. Gameplay & Interface: Minimap Visibility, Contextual Interaction Prompts.
- Reset to Defaults with confirmation.
- Full keyboard (Up/Down, Left/Right, Enter/Space, Esc) and mouse navigation.
- Real-time live application without restarting the level, room, or player progress.
"""

import math
from typing import Any
import pygame
from engine.settings import settings
from systems.audio import audio


class SettingsModal:
    """Temple-themed functional settings menu with category organization."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_open = False
        self.selected_row = 0
        self.reset_confirm_open = False
        self.pulse = 0.0

        # Setting items list
        # Each item: (id, label, category, type)
        self.items = [
            ("music_volume", "Music / Ambience", "AUDIO", "slider"),
            ("sfx_volume", "Sound Effects", "AUDIO", "slider"),
            ("muted", "Mute All Audio", "AUDIO", "toggle"),
            ("fullscreen", "Display Mode", "DISPLAY", "fullscreen_toggle"),
            ("screen_shake", "Screen Shake", "ACCESSIBILITY", "toggle"),
            ("reduced_motion", "Reduced Motion", "ACCESSIBILITY", "toggle"),
            ("show_minimap", "Minimap Display", "GAMEPLAY", "toggle"),
            ("contextual_prompts", "Contextual Prompts", "GAMEPLAY", "toggle"),
            ("reset_defaults", "Reset to Defaults", "SYSTEM", "action"),
        ]

        # Fonts
        self.font_title = pygame.font.SysFont("georgia", 22, bold=True)
        self.font_cat = pygame.font.SysFont("georgia", 13, bold=True)
        self.font_label = pygame.font.SysFont("consolas", 14)
        self.font_val = pygame.font.SysFont("consolas", 13, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 12)
        self.font_btn = pygame.font.SysFont("consolas", 13, bold=True)

        # Interactive bounds
        self.row_rects: list[pygame.Rect] = []
        self.left_btn_rects: list[pygame.Rect] = []
        self.right_btn_rects: list[pygame.Rect] = []
        self.close_btn_rect = pygame.Rect(0, 0, 140, 32)
        self.reset_yes_rect = pygame.Rect(0, 0, 100, 30)
        self.reset_no_rect = pygame.Rect(0, 0, 100, 30)

        # Reference to game manager for display/live hooks
        self.game_manager = None

    def open(self, game_manager=None):
        """Opens the settings modal."""
        self.is_open = True
        self.reset_confirm_open = False
        if game_manager:
            self.game_manager = game_manager

    def close(self):
        """Closes the settings modal."""
        self.is_open = False
        self.reset_confirm_open = False

    def update(self, dt: float):
        """Updates animation pulse."""
        if self.is_open:
            self.pulse = (self.pulse + dt * 4.0) % (2 * math.pi)

    def _apply_live_changes(self):
        """Applies current settings to live systems."""
        if self.game_manager:
            settings.apply_to_game(self.game_manager)

    def handle_input(
        self,
        event: pygame.event.Event,
        game_pos: tuple[int, int] | None = None,
        game_manager: Any = None,
        **kwargs: Any,
    ) -> bool:
        """Handles keyboard and mouse navigation. Returns True if event was handled."""
        if not self.is_open:
            return False

        if game_manager is not None:
            self.game_manager = game_manager

        if self.reset_confirm_open:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_y, pygame.K_RETURN, pygame.K_SPACE):
                    settings.reset_to_defaults()
                    self._apply_live_changes()
                    self.reset_confirm_open = False
                    audio.play("pickup")
                    return True
                elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                    self.reset_confirm_open = False
                    audio.play("clue")
                    return True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = game_pos if game_pos else event.pos
                if self.reset_yes_rect.collidepoint(mx, my):
                    settings.reset_to_defaults()
                    self._apply_live_changes()
                    self.reset_confirm_open = False
                    audio.play("pickup")
                    return True
                elif self.reset_no_rect.collidepoint(mx, my):
                    self.reset_confirm_open = False
                    audio.play("clue")
                    return True
            return True

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_row = (self.selected_row - 1) % len(self.items)
                audio.play("clue")
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_row = (self.selected_row + 1) % len(self.items)
                audio.play("clue")
                return True
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._modify_value(self.selected_row, delta=-1)
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._modify_value(self.selected_row, delta=1)
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_row(self.selected_row)
                return True
            elif event.key == pygame.K_ESCAPE:
                self.close()
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = game_pos if game_pos else event.pos

            # Close button
            if self.close_btn_rect.collidepoint(mx, my):
                self.close()
                return True

            # Row item clicks
            for idx, r in enumerate(self.row_rects):
                if r.collidepoint(mx, my):
                    self.selected_row = idx
                    # Check left / right arrows
                    if idx < len(self.left_btn_rects) and self.left_btn_rects[idx].collidepoint(mx, my):
                        self._modify_value(idx, delta=-1)
                    elif idx < len(self.right_btn_rects) and self.right_btn_rects[idx].collidepoint(mx, my):
                        self._modify_value(idx, delta=1)
                    else:
                        self._activate_row(idx)
                    return True

        return True

    def _modify_value(self, index: int, delta: int):
        """Decrements or increments a slider or toggles a boolean."""
        item_id, _, _, item_type = self.items[index]

        if item_type == "slider":
            cur = float(settings.get(item_id, 1.0))
            new_val = max(0.0, min(1.0, round(cur + delta * 0.1, 1)))
            settings.set(item_id, new_val)
            self._apply_live_changes()
            if item_id == "sfx_volume" and not settings.muted:
                audio.play("clue")
        elif item_type == "toggle":
            cur = bool(settings.get(item_id, False))
            settings.set(item_id, not cur)
            self._apply_live_changes()
            audio.play("clue")
        elif item_type == "fullscreen_toggle":
            cur = bool(settings.get("fullscreen", True))
            settings.set("fullscreen", not cur)
            if self.game_manager and hasattr(self.game_manager, "_toggle_fullscreen"):
                self.game_manager._toggle_fullscreen()
            audio.play("clue")

    def _activate_row(self, index: int):
        """Action or toggle trigger for Enter / Space / Click."""
        item_id, _, _, item_type = self.items[index]

        if item_id == "reset_defaults":
            self.reset_confirm_open = True
            audio.play("clue")
        elif item_type in ("toggle", "fullscreen_toggle"):
            self._modify_value(index, delta=1)
        elif item_type == "slider":
            self._modify_value(index, delta=1)

    def draw(self, surface: pygame.Surface, game_pos: tuple[int, int] | None = None):
        """Renders the settings modal overlay."""
        if not self.is_open:
            return

        # Dim background
        dim = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim.fill((6, 5, 12, 225))
        surface.blit(dim, (0, 0))

        # Main Tablet Box
        box_w = min(680, self.screen_width - 40)
        box_h = 480
        bx = (self.screen_width - box_w) // 2
        by = (self.screen_height - box_h) // 2

        tablet = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        tablet.fill((18, 15, 24, 250))
        pygame.draw.rect(tablet, (190, 155, 75), (0, 0, box_w, box_h), width=2, border_radius=10)
        pygame.draw.rect(tablet, (65, 52, 32), (5, 5, box_w - 10, box_h - 10), width=1, border_radius=8)

        # Corner gold jewels
        for cx, cy in [(6, 6), (box_w - 10, 6), (6, box_h - 10), (box_w - 10, box_h - 10)]:
            pygame.draw.rect(tablet, (230, 195, 80), (cx, cy, 4, 4))
        surface.blit(tablet, (bx, by))

        # Header Title
        title_surf = self.font_title.render("TEMPLE ARCHIVES - SETTINGS", True, (255, 225, 130))
        surface.blit(title_surf, (bx + (box_w - title_surf.get_width()) // 2, by + 14))

        sub_text = "Adjust audio resonances, visual scaling, and exploration comfort."
        sub_surf = self.font_small.render(sub_text, True, (185, 175, 160))
        surface.blit(sub_surf, (bx + (box_w - sub_surf.get_width()) // 2, by + 37))

        # Divider
        div_y = by + 54
        pygame.draw.line(surface, (150, 120, 55), (bx + 35, div_y), (bx + box_w - 35, div_y), 1)
        pygame.draw.circle(surface, (220, 185, 75), (bx + box_w // 2, div_y), 3)

        # Draw Settings Rows
        start_y = by + 60
        row_h = 27
        self.row_rects = []
        self.left_btn_rects = []
        self.right_btn_rects = []
        mx, my = game_pos if game_pos is not None else pygame.mouse.get_pos()

        cur_cat = ""
        current_draw_y = start_y

        for idx, (item_id, label, cat, item_type) in enumerate(self.items):
            # Category Header
            if cat != cur_cat:
                cur_cat = cat
                # Procedural golden diamond glyph (replaces non-ASCII special symbols)
                cdx = bx + 42
                cdy = current_draw_y + 9
                diamond_pts = [(cdx, cdy - 4), (cdx + 4, cdy), (cdx, cdy + 4), (cdx - 4, cdy)]
                pygame.draw.polygon(surface, (230, 195, 80), diamond_pts)
                pygame.draw.polygon(surface, (140, 110, 45), diamond_pts, 1)

                cat_surf = self.font_cat.render(cur_cat, True, (220, 185, 95))
                surface.blit(cat_surf, (bx + 52, current_draw_y + 1))
                current_draw_y += 18

            row_rect = pygame.Rect(bx + 35, current_draw_y, box_w - 70, row_h - 4)
            self.row_rects.append(row_rect)

            is_selected = (idx == self.selected_row)
            is_hovered = row_rect.collidepoint(mx, my)

            # Row background
            row_surf = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
            if is_selected:
                row_bg = (38, 30, 52, 240)
                border_col = (255, 220, 110)
                border_w = 2
            elif is_hovered:
                row_bg = (26, 22, 34, 230)
                border_col = (180, 150, 85)
                border_w = 1
            else:
                row_bg = (14, 12, 18, 180)
                border_col = (55, 45, 35)
                border_w = 1

            pygame.draw.rect(row_surf, row_bg, (0, 0, row_rect.width, row_rect.height), border_radius=4)
            pygame.draw.rect(row_surf, border_col, (0, 0, row_rect.width, row_rect.height), width=border_w, border_radius=4)
            surface.blit(row_surf, (row_rect.x, row_rect.y))

            # Row Label
            lbl_col = (255, 240, 190) if is_selected else (220, 210, 195)
            lbl_surf = self.font_label.render(label, True, lbl_col)
            surface.blit(lbl_surf, (row_rect.x + 12, row_rect.y + (row_rect.height - lbl_surf.get_height()) // 2))

            # Row Value Widget
            val_x = row_rect.x + row_rect.width - 230
            val_w = 215

            left_btn = pygame.Rect(val_x, row_rect.y + 1, 22, 20)
            right_btn = pygame.Rect(val_x + val_w - 22, row_rect.y + 1, 22, 20)
            self.left_btn_rects.append(left_btn)
            self.right_btn_rects.append(right_btn)

            if item_type == "slider":
                val = int(round(settings.get(item_id, 1.0) * 100))
                # Left arrow button (procedural arrow)
                l_hover = left_btn.collidepoint(mx, my)
                l_col = (255, 225, 120) if l_hover else (170, 145, 80)
                l_bg = (35, 28, 44, 220) if l_hover else (16, 12, 22, 180)
                pygame.draw.rect(surface, l_bg, left_btn, border_radius=3)
                pygame.draw.rect(surface, l_col, left_btn, width=1, border_radius=3)
                lx = left_btn.centerx
                ly = left_btn.centery
                pygame.draw.polygon(surface, l_col, [(lx + 3, ly - 4), (lx - 3, ly), (lx + 3, ly + 4)])

                # Progress Bar
                bar_x = val_x + 24
                bar_w = val_w - 48
                bar_rect = pygame.Rect(bar_x, row_rect.y + 4, bar_w, 15)
                pygame.draw.rect(surface, (10, 8, 14), bar_rect, border_radius=3)
                fill_w = int(bar_w * (val / 100.0))
                if fill_w > 0:
                    fill_col = (235, 195, 75) if is_selected else (180, 145, 55)
                    pygame.draw.rect(surface, fill_col, (bar_x, row_rect.y + 4, fill_w, 15), border_radius=3)
                pygame.draw.rect(surface, (100, 80, 50), bar_rect, width=1, border_radius=3)

                # Numeric text
                txt_surf = self.font_val.render(f"{val}%", True, (255, 250, 220))
                surface.blit(txt_surf, (bar_x + (bar_w - txt_surf.get_width()) // 2, row_rect.y + 3))

                # Right arrow button (procedural arrow)
                r_hover = right_btn.collidepoint(mx, my)
                r_col = (255, 225, 120) if r_hover else (170, 145, 80)
                r_bg = (35, 28, 44, 220) if r_hover else (16, 12, 22, 180)
                pygame.draw.rect(surface, r_bg, right_btn, border_radius=3)
                pygame.draw.rect(surface, r_col, right_btn, width=1, border_radius=3)
                rx = right_btn.centerx
                ry = right_btn.centery
                pygame.draw.polygon(surface, r_col, [(rx - 3, ry - 4), (rx + 3, ry), (rx - 3, ry + 4)])

            elif item_type in ("toggle", "fullscreen_toggle"):
                val = bool(settings.get(item_id, False))
                if item_type == "fullscreen_toggle":
                    val_str = "FULLSCREEN" if val else "WINDOWED"
                    val_col = (130, 220, 160) if val else (220, 180, 130)
                else:
                    val_str = "ENABLED" if val else "DISABLED"
                    val_col = (130, 220, 160) if val else (180, 170, 165)

                t_surf = self.font_val.render(f"[ {val_str} ]", True, val_col)
                # Small procedural indicator light dot
                dot_col = (130, 220, 160) if val else (90, 80, 85)
                dot_x = val_x + val_w - t_surf.get_width() - 10
                dot_y = row_rect.y + row_rect.height // 2
                pygame.draw.circle(surface, dot_col, (dot_x, dot_y), 3)
                if val:
                    pygame.draw.circle(surface, (180, 255, 205), (dot_x, dot_y), 1)

                surface.blit(t_surf, (val_x + (val_w - t_surf.get_width()), row_rect.y + 3))

            elif item_type == "action":
                act_str = "[ ACTIVATE ]"
                t_surf = self.font_val.render(act_str, True, (255, 140, 120) if is_selected else (200, 110, 100))
                surface.blit(t_surf, (val_x + (val_w - t_surf.get_width()), row_rect.y + 3))

            current_draw_y += row_h

        # Footer Divider
        foot_div_y = by + box_h - 68
        pygame.draw.line(surface, (70, 56, 36), (bx + 35, foot_div_y), (bx + box_w - 35, foot_div_y), 1)
        pygame.draw.circle(surface, (140, 115, 55), (bx + box_w // 2, foot_div_y), 2)

        # Close Button
        foot_y = by + box_h - 60
        self.close_btn_rect = pygame.Rect(bx + box_w // 2 - 70, foot_y, 140, 26)
        c_hover = self.close_btn_rect.collidepoint(mx, my)

        c_surf = pygame.Surface((self.close_btn_rect.width, self.close_btn_rect.height), pygame.SRCALPHA)
        c_surf.fill((34, 28, 44, 240) if c_hover else (20, 16, 26, 220))
        pygame.draw.rect(c_surf, (240, 210, 120) if c_hover else (140, 115, 60),
                         (0, 0, self.close_btn_rect.width, self.close_btn_rect.height), width=1, border_radius=5)
        c_lbl = self.font_btn.render("[ESC] CLOSE", True, (255, 230, 160) if c_hover else (195, 180, 150))
        c_surf.blit(c_lbl, ((self.close_btn_rect.width - c_lbl.get_width()) // 2, 4))
        surface.blit(c_surf, (self.close_btn_rect.x, self.close_btn_rect.y))

        # Instructions / Navigation Legend cleanly formatted inside panel
        inst = "UP/DOWN: Select   |   LEFT/RIGHT: Change   |   ENTER: Toggle   |   ESC: Close"
        i_surf = self.font_small.render(inst, True, (175, 165, 150))
        surface.blit(i_surf, (bx + (box_w - i_surf.get_width()) // 2, by + box_h - 26))

        # Reset Confirmation Dialog
        if self.reset_confirm_open:
            self._draw_reset_dialog(surface, bx, by, box_w, box_h, mx, my)

    def _draw_reset_dialog(self, surface: pygame.Surface, bx: int, by: int, box_w: int, box_h: int, mx: int, my: int):
        """Draws modal confirmation for Reset to Defaults with generous spacing and alignment."""
        # Dim inner box
        d_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        d_surf.fill((0, 0, 0, 210))
        surface.blit(d_surf, (bx, by))

        dlg_w = 520
        dlg_h = 175
        dx = bx + (box_w - dlg_w) // 2
        dy = by + (box_h - dlg_h) // 2

        dlg = pygame.Surface((dlg_w, dlg_h), pygame.SRCALPHA)
        dlg.fill((24, 18, 26, 252))
        pygame.draw.rect(dlg, (230, 95, 85), (0, 0, dlg_w, dlg_h), width=2, border_radius=8)
        pygame.draw.rect(dlg, (85, 45, 45), (4, 4, dlg_w - 8, dlg_h - 8), width=1, border_radius=6)
        surface.blit(dlg, (dx, dy))

        t1 = self.font_title.render("RESET ALL SETTINGS?", True, (255, 140, 120))
        surface.blit(t1, (dx + (dlg_w - t1.get_width()) // 2, dy + 22))

        t2 = self.font_small.render("This will restore all audio, display, and controls to default.", True, (230, 215, 205))
        surface.blit(t2, (dx + (dlg_w - t2.get_width()) // 2, dy + 58))

        btn_w, btn_h = 110, 32
        self.reset_yes_rect = pygame.Rect(dx + dlg_w // 2 - btn_w - 15, dy + 98, btn_w, btn_h)
        self.reset_no_rect = pygame.Rect(dx + dlg_w // 2 + 15, dy + 98, btn_w, btn_h)

        # Yes button
        y_hov = self.reset_yes_rect.collidepoint(mx, my)
        y_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        y_surf.fill((70, 25, 25, 240) if y_hov else (45, 18, 18, 220))
        pygame.draw.rect(y_surf, (255, 120, 110) if y_hov else (200, 90, 80), (0, 0, btn_w, btn_h), width=1, border_radius=5)
        yl = self.font_btn.render("[Y] YES", True, (255, 215, 205) if y_hov else (220, 175, 165))
        y_surf.blit(yl, ((btn_w - yl.get_width()) // 2, (btn_h - yl.get_height()) // 2))
        surface.blit(y_surf, (self.reset_yes_rect.x, self.reset_yes_rect.y))

        # No button
        n_hov = self.reset_no_rect.collidepoint(mx, my)
        n_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        n_surf.fill((40, 32, 48, 240) if n_hov else (25, 20, 30, 220))
        pygame.draw.rect(n_surf, (190, 180, 205) if n_hov else (125, 115, 135), (0, 0, btn_w, btn_h), width=1, border_radius=5)
        nl = self.font_btn.render("[N] NO", True, (245, 240, 255) if n_hov else (185, 180, 195))
        n_surf.blit(nl, ((btn_w - nl.get_width()) // 2, (btn_h - nl.get_height()) // 2))
        surface.blit(n_surf, (self.reset_no_rect.x, self.reset_no_rect.y))

        # Escape instruction hint at bottom of popup
        hint = self.font_small.render("[Y] Confirm Reset   |   [N] / [ESC] Cancel", True, (160, 145, 135))
        surface.blit(hint, (dx + (dlg_w - hint.get_width()) // 2, dy + 144))

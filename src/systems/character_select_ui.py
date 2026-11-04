"""systems/character_select_ui.py — Character Selection Screen for Lumen.

Implements Feature A (Character Selection):
- Offers 3 cosmetic wizard-explorer choices:
  1. Indigo Scholar (Default)
  2. Solar Acolyte
  3. Emerald Sage
- Displays animated sprite preview, character name, title, and lore description.
- Clearly displays the active and hovered selection state.
- Full keyboard (Arrows / WASD, Enter / Space, Esc) and mouse navigation.
- Confirmed selection persists across sessions via SettingsManager.
- Strict cosmetic-only guarantee: collision, movement, puzzles, and rules are unchanged.
"""

import math
import pygame
from engine.player import Player
from engine.characters import CHARACTER_PROFILES, CHARACTER_ORDER, DEFAULT_CHARACTER
from engine.settings import settings
from systems.audio import audio


class CharacterSelectModal:
    """Temple-themed Character Selection Screen."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_open = False
        self.current_index = 0
        self.confirmed_character = settings.selected_character
        self.anim_timer = 0.0
        self.pulse = 0.0

        # Initialize current index to match saved setting
        if self.confirmed_character in CHARACTER_ORDER:
            self.current_index = CHARACTER_ORDER.index(self.confirmed_character)
        else:
            self.current_index = 0

        # Create preview players for each character
        self.preview_players: dict[str, Player] = {
            cid: Player(x=0, y=0, character_id=cid) for cid in CHARACTER_ORDER
        }

        # Fonts
        self.font_title = pygame.font.SysFont("georgia", 24, bold=True)
        self.font_sub = pygame.font.SysFont("consolas", 13)
        self.font_name = pygame.font.SysFont("georgia", 18, bold=True)
        self.font_title_sub = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_desc = pygame.font.SysFont("consolas", 12)
        self.font_btn = pygame.font.SysFont("consolas", 13, bold=True)
        self.font_badge = pygame.font.SysFont("consolas", 11, bold=True)

        # Card rects (computed in draw or stored)
        self.card_rects: list[pygame.Rect] = []
        self.confirm_btn_rect = pygame.Rect(0, 0, 160, 34)
        self.back_btn_rect = pygame.Rect(0, 0, 130, 34)

    def open(self):
        """Opens the character selection screen."""
        self.is_open = True
        self.confirmed_character = settings.selected_character
        if self.confirmed_character in CHARACTER_ORDER:
            self.current_index = CHARACTER_ORDER.index(self.confirmed_character)
        else:
            self.current_index = 0
        self.anim_timer = 0.0

    def close(self):
        """Closes the character selection screen."""
        self.is_open = False

    def update(self, dt: float):
        """Updates animation timers for previews and pulsating UI glow."""
        if not self.is_open:
            return
        self.anim_timer += dt
        self.pulse = (self.pulse + dt * 3.5) % (2 * math.pi)
        for p in self.preview_players.values():
            p.glow_phase = (p.glow_phase + dt * 3.0) % (2 * math.pi)
            p.anim_timer += dt * 4.0
            p.walk_frame = int(p.anim_timer) % 4

    def handle_input(self, event: pygame.event.Event, game_pos: tuple[int, int] | None = None) -> bool:
        """Handles keyboard and mouse events. Returns True if event was consumed."""
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.current_index = (self.current_index - 1) % len(CHARACTER_ORDER)
                audio.play("clue")
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.current_index = (self.current_index + 1) % len(CHARACTER_ORDER)
                audio.play("clue")
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.confirm_selection()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.close()
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = game_pos if game_pos else event.pos
            # Check card clicks
            for idx, r in enumerate(self.card_rects):
                if r.collidepoint(mx, my):
                    self.current_index = idx
                    audio.play("clue")
                    return True

            # Check Confirm button
            if self.confirm_btn_rect.collidepoint(mx, my):
                self.confirm_selection()
                return True

            # Check Back button
            if self.back_btn_rect.collidepoint(mx, my):
                self.close()
                return True

        return True

    def confirm_selection(self):
        """Persists the chosen character to settings and closes."""
        chosen_id = CHARACTER_ORDER[self.current_index]
        self.confirmed_character = chosen_id
        settings.selected_character = chosen_id
        audio.play("pickup")
        self.close()

    def draw(self, surface: pygame.Surface, game_pos: tuple[int, int] | None = None):
        """Renders the character selection screen."""
        if not self.is_open:
            return

        # Dim background
        dim = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim.fill((6, 5, 12, 225))
        surface.blit(dim, (0, 0))

        # Main Tablet Box
        box_w = min(740, self.screen_width - 40)
        box_h = 510
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
        title_surf = self.font_title.render("EXPLORER ATTIRE & ATTUNEMENT", True, (255, 225, 130))
        surface.blit(title_surf, (bx + (box_w - title_surf.get_width()) // 2, by + 18))

        sub_text = "Select your character's visual lineage. Puzzles, speed, and abilities remain identical."
        sub_surf = self.font_sub.render(sub_text, True, (185, 175, 160))
        surface.blit(sub_surf, (bx + (box_w - sub_surf.get_width()) // 2, by + 48))

        # Divider line
        div_y = by + 70
        pygame.draw.line(surface, (150, 120, 55), (bx + 40, div_y), (bx + box_w - 40, div_y), 1)
        pygame.draw.circle(surface, (220, 185, 75), (bx + box_w // 2, div_y), 3)

        # Draw 3 Character Cards
        card_w = 210
        card_h = 330
        gap = 20
        total_cards_w = len(CHARACTER_ORDER) * card_w + (len(CHARACTER_ORDER) - 1) * gap
        start_x = bx + (box_w - total_cards_w) // 2
        cards_y = by + 88

        self.card_rects = []
        mx, my = game_pos if game_pos is not None else pygame.mouse.get_pos()

        for idx, cid in enumerate(CHARACTER_ORDER):
            cx = start_x + idx * (card_w + gap)
            cy = cards_y
            crect = pygame.Rect(cx, cy, card_w, card_h)
            self.card_rects.append(crect)

            is_highlighted = (idx == self.current_index)
            is_active_equipped = (cid == self.confirmed_character)
            is_hovered = crect.collidepoint(mx, my)

            # Card background
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            if is_highlighted:
                bg_col = (28, 22, 38, 245)
                border_col = (255, 220, 100)
                border_w = 2
            elif is_hovered:
                bg_col = (24, 20, 32, 235)
                border_col = (200, 175, 95)
                border_w = 1
            else:
                bg_col = (16, 14, 22, 220)
                border_col = (85, 70, 50)
                border_w = 1

            pygame.draw.rect(card_surf, bg_col, (0, 0, card_w, card_h), border_radius=8)
            pygame.draw.rect(card_surf, border_col, (0, 0, card_w, card_h), width=border_w, border_radius=8)

            # Character Profile Data
            prof = CHARACTER_PROFILES[cid]

            # 1. Preview Box (Top of card)
            prev_w = card_w - 24
            prev_h = 100
            prev_rect = pygame.Rect(12, 12, prev_w, prev_h)
            pygame.draw.rect(card_surf, (10, 8, 14, 240), prev_rect, border_radius=6)
            pygame.draw.rect(card_surf, (60, 50, 40), prev_rect, width=1, border_radius=6)

            # Render Character inside preview
            dummy = self.preview_players[cid]
            # Offsets to center player in preview box
            char_cx = prev_rect.x + prev_w // 2 - dummy.width // 2
            char_cy = prev_rect.y + prev_h // 2 - dummy.height // 2 - 4
            dummy.x = char_cx
            dummy.y = char_cy
            dummy.draw(card_surf, camera_offset=(0, 0), is_lantern_lit=True)

            surface.blit(card_surf, (cx, cy))

            # 2. Name & Title
            name_txt = self.font_name.render(prof["name"], True, (255, 235, 170) if is_highlighted else (220, 210, 190))
            surface.blit(name_txt, (cx + (card_w - name_txt.get_width()) // 2, cy + 122))

            title_txt = self.font_title_sub.render(prof["title"], True, (190, 160, 95))
            surface.blit(title_txt, (cx + (card_w - title_txt.get_width()) // 2, cy + 146))

            # 3. Lore Description
            words = prof["description"].split()
            desc_lines = []
            cur_line = ""
            for w in words:
                test = f"{cur_line} {w}".strip()
                if self.font_desc.size(test)[0] <= card_w - 24:
                    cur_line = test
                else:
                    if cur_line:
                        desc_lines.append(cur_line)
                    cur_line = w
            if cur_line:
                desc_lines.append(cur_line)

            for line_idx, dl in enumerate(desc_lines):
                dl_surf = self.font_desc.render(dl, True, (180, 175, 170))
                surface.blit(dl_surf, (cx + 12, cy + 175 + line_idx * 17))

            # 4. Status Badge (Equipped / Focus)
            badge_y = cy + card_h - 38
            if is_active_equipped:
                b_surf = pygame.Surface((card_w - 24, 24), pygame.SRCALPHA)
                b_surf.fill((35, 30, 20, 230))
                pygame.draw.rect(b_surf, (220, 185, 75), (0, 0, card_w - 24, 24), width=1, border_radius=4)
                lbl = self.font_badge.render("[ CURRENTLY EQUIPPED ]", True, (255, 225, 120))
                b_surf.blit(lbl, ((card_w - 24 - lbl.get_width()) // 2, 4))
                surface.blit(b_surf, (cx + 12, badge_y))
            elif is_highlighted:
                b_surf = pygame.Surface((card_w - 24, 24), pygame.SRCALPHA)
                b_surf.fill((25, 35, 45, 230))
                pygame.draw.rect(b_surf, (120, 180, 240), (0, 0, card_w - 24, 24), width=1, border_radius=4)
                lbl = self.font_badge.render("READY TO CONFIRM", True, (160, 210, 255))
                b_surf.blit(lbl, ((card_w - 24 - lbl.get_width()) // 2, 4))
                surface.blit(b_surf, (cx + 12, badge_y))

        # Bottom Buttons (Confirm & Back)
        btn_y = by + box_h - 52
        self.confirm_btn_rect = pygame.Rect(bx + box_w // 2 - 165, btn_y, 160, 34)
        self.back_btn_rect = pygame.Rect(bx + box_w // 2 + 15, btn_y, 140, 34)

        # Confirm Button
        conf_hover = self.confirm_btn_rect.collidepoint(mx, my)
        conf_surf = pygame.Surface((self.confirm_btn_rect.width, self.confirm_btn_rect.height), pygame.SRCALPHA)
        conf_surf.fill((35, 28, 16, 240) if conf_hover else (24, 18, 12, 220))
        pygame.draw.rect(conf_surf, (255, 220, 110) if conf_hover else (180, 145, 60),
                         (0, 0, self.confirm_btn_rect.width, self.confirm_btn_rect.height), width=1, border_radius=6)
        c_lbl = self.font_btn.render("[ENTER] CONFIRM", True, (255, 235, 160) if conf_hover else (220, 195, 130))
        conf_surf.blit(c_lbl, ((self.confirm_btn_rect.width - c_lbl.get_width()) // 2, 8))
        surface.blit(conf_surf, (self.confirm_btn_rect.x, self.confirm_btn_rect.y))

        # Back Button
        back_hover = self.back_btn_rect.collidepoint(mx, my)
        back_surf = pygame.Surface((self.back_btn_rect.width, self.back_btn_rect.height), pygame.SRCALPHA)
        back_surf.fill((28, 24, 34, 240) if back_hover else (18, 15, 24, 220))
        pygame.draw.rect(back_surf, (200, 180, 150) if back_hover else (110, 95, 80),
                         (0, 0, self.back_btn_rect.width, self.back_btn_rect.height), width=1, border_radius=6)
        b_lbl = self.font_btn.render("[ESC] BACK", True, (230, 220, 200) if back_hover else (160, 150, 140))
        back_surf.blit(b_lbl, ((self.back_btn_rect.width - b_lbl.get_width()) // 2, 8))
        surface.blit(back_surf, (self.back_btn_rect.x, self.back_btn_rect.y))

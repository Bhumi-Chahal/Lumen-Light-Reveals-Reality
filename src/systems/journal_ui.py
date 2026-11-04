"""systems/journal_ui.py — Universal Level Journal Modal for Lumen.

Provides an immersive, temple-styled Field Journal across Levels 1, 2, and 3:
- Level 1: Discoveries (Clues & Keys) and Observations (Light Mechanics, Sanctum Door, Forest)
- Level 2: Inscriptions (Ancient Inscription, Refractor Mirrors, Crystals) and Spectral Notes (Light Channels, Barriers & Shadows, Exit Portal)
- Level 3: Tablets (Mural Inscriptions, Headstones, Laser Receivers, Prisms) and Reflection Laws (Optics, Splitters, Chamber Doors)

Visual presentation adheres to the established Forge Journal aesthetic:
- Aged parchment/tablet theme with dark plinth and gold/amber trim
- Bookmarked tabs with active pips and gold baselines
- Smooth scrolling with styled scrollbar
- Consistent footer: [W/S / ↑/↓] Scroll   |   [J / ESC] Close
"""

import math
from typing import List, Tuple, Optional, Any
import pygame
from systems.audio import audio


class LevelJournalModal:
    """Universal Journal Modal rendering level-specific lore, clues, and observations."""

    def __init__(self, screen_w: int = 800, screen_h: int = 600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open: bool = False
        self.level_id: str = "level1"
        self.active_tab: int = 0
        self.scroll_y: int = 0
        self.max_scroll: int = 0

        # Modal window geometry matching the temple aesthetic
        self.width = 700
        self.height = 500
        self.x = (screen_w - self.width) // 2
        self.y = max(40, (screen_h - self.height) // 2)

    def open(self, level_id: str = "level1", tab: int = 0):
        self.level_id = level_id
        self.active_tab = tab
        self.scroll_y = 0
        self.is_open = True
        audio.play("clue")

    def close(self):
        self.is_open = False

    def toggle(self, level_id: str = "level1"):
        if self.is_open:
            self.close()
        else:
            self.open(level_id)

    def handle_keydown(self, key: int) -> bool:
        if not self.is_open:
            return False

        if key in (pygame.K_ESCAPE, pygame.K_j):
            self.close()
            return True

        num_tabs = len(self._get_tab_titles())
        if key == pygame.K_TAB:
            self.active_tab = (self.active_tab + 1) % num_tabs
            self.scroll_y = 0
            audio.play("clue")
            return True
        elif key == pygame.K_1 and num_tabs >= 1:
            self.active_tab = 0
            self.scroll_y = 0
            audio.play("clue")
            return True
        elif key == pygame.K_2 and num_tabs >= 2:
            self.active_tab = 1
            self.scroll_y = 0
            audio.play("clue")
            return True
        elif key == pygame.K_3 and num_tabs >= 3:
            self.active_tab = 2
            self.scroll_y = 0
            audio.play("clue")
            return True

        # Scrolling controls
        if key in (pygame.K_w, pygame.K_UP):
            self.scroll_y = max(0, self.scroll_y - 28)
            return True
        elif key in (pygame.K_s, pygame.K_DOWN):
            self.scroll_y = min(self.max_scroll, self.scroll_y + 28)
            return True

        return True

    def handle_scroll(self, dy: int):
        if self.is_open:
            self.scroll_y = max(0, min(self.max_scroll, self.scroll_y + dy * 24))

    def handle_click(self, mx: int, my: int) -> bool:
        if not self.is_open:
            return False

        # Close [X] button
        close_rect = pygame.Rect(self.x + self.width - 34, self.y + 12, 22, 22)
        if close_rect.collidepoint(mx, my):
            self.close()
            return True

        # Tab bar clicks
        tab_titles = self._get_tab_titles()
        tab_w = 200
        tab_spacing = 15
        for i in range(len(tab_titles)):
            tx = self.x + 35 + i * (tab_w + tab_spacing)
            ty = self.y + 44
            t_rect = pygame.Rect(tx, ty, tab_w, 26)
            if t_rect.collidepoint(mx, my):
                if self.active_tab != i:
                    self.active_tab = i
                    self.scroll_y = 0
                    audio.play("clue")
                return True

        # Click outside modal closes it
        modal_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if not modal_rect.collidepoint(mx, my):
            self.close()
            return True

        return True

    def handle_input(self, event: pygame.event.Event, game_pos: Optional[Tuple[int, int]] = None) -> bool:
        """Central event dispatcher for LevelJournalModal."""
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            return self.handle_keydown(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = game_pos if game_pos is not None else event.pos
            if event.button == 1:
                return self.handle_click(mx, my)
            elif event.button == 4:
                self.handle_scroll(-1)
                return True
            elif event.button == 5:
                self.handle_scroll(1)
                return True
        elif event.type == pygame.MOUSEWHEEL:
            self.handle_scroll(-event.y)
            return True
        return False

    def _get_tab_titles(self) -> List[str]:
        if self.level_id == "level1":
            return ["I. DISCOVERIES & CLUES", "II. FIELD OBSERVATIONS"]
        elif self.level_id == "level2":
            return ["I. ANCIENT INSCRIPTIONS", "II. SPECTRAL NOTES"]
        elif self.level_id == "level3":
            return ["I. CHAMBER TABLETS", "II. LAWS OF REFLECTION"]
        elif self.level_id == "level4":
            return ["I. FORGE INVESTIGATION", "II. TEMPLE ARCHIVES"]
        return ["I. DISCOVERIES", "II. OBSERVATIONS"]

    def _get_journal_header(self) -> str:
        if self.level_id == "level1":
            return "LEVEL 1 JOURNAL — THE THRESHOLD OF LIGHT"
        elif self.level_id == "level2":
            return "LEVEL 2 JOURNAL — THE DEEPENING DARK"
        elif self.level_id == "level3":
            return "LEVEL 3 JOURNAL — THE HALL OF MIRRORS"
        elif self.level_id == "level4":
            return "LEVEL 4 JOURNAL — THE ANCIENT FORGE"
        return "FIELD JOURNAL — LUMEN EXPEDITION"

    def _build_content_level1(self, inventory: Any, room: Any) -> List[Tuple[str, bool, Tuple[int, int, int]]]:
        clues_list = getattr(inventory, "clues", []) if inventory else []
        clue_names = {c.get("name", ""): c.get("text", "") for c in clues_list if isinstance(c, dict)}

        has_bronze = inventory.has_key("key_bronze") if inventory else False
        has_silver = inventory.has_key("key_silver") if inventory else False
        has_gold = inventory.has_key("key_gold") if inventory else False

        pedestal_found = any("pedestal" in k.lower() or "lantern" in k.lower() for k in clue_names) or (inventory and getattr(inventory, "has_lantern", False))
        tablet_found = any("tablet" in k.lower() or "stone" in k.lower() for k in clue_names)
        stump_found = any("stump" in k.lower() or "whispering" in k.lower() for k in clue_names)
        statue_found = any("statue" in k.lower() or "carving" in k.lower() for k in clue_names)

        if self.active_tab == 0:
            # Tab 1: Discoveries / Clues
            ped_st = '[RESTORED] "The Lantern of Lumina awakens in darkness. Carry its flame to reveal what remains unseen."' if pedestal_found else "[UNDISCOVERED] Stone Pedestal at the Ancient Grove"
            tab_st = '[RESTORED] "Only the pure of heart may enter. Seek the three keys of rank: Bronze, Silver, and Gold."' if tablet_found else "[UNDISCOVERED] Weathered Tablet near the Forest Clearing"
            stu_st = '[RESTORED] "Shadows shrink where illumination falls; walk within the perimeter of light to cross the chasm."' if stump_found else "[UNDISCOVERED] Whispering Stump across the Lower Glade"
            sta_st = '[RESTORED] "Three seals bar the Threshold. Insert the attuned key matching the Sanctum\'s resonance."' if statue_found else "[UNDISCOVERED] Ancient Statue before the Sanctum Arch"

            b_key_st = "[COLLECTED] Bronze Key (Rank I) — First tier of ancient metalwork" if has_bronze else "[UNCLAIMED] Bronze Key — Resting in the Upper Clearing"
            s_key_st = "[COLLECTED] Silver Key (Rank II) — Second tier, cold polished sheen" if has_silver else "[UNCLAIMED] Silver Key — Hidden near the Whispering Glade"
            g_key_st = "[COLLECTED] Gold Key (Rank III) — Final tier, radiant golden alloy" if has_gold else "[UNCLAIMED] Gold Key — Concealed atop the High Canopy"

            return [
                ("THE EXPEDITION DIARY — DISCOVERIES & RELICS", True, (248, 224, 148)),
                ("Documenting relics, clues, and keys recovered along the Threshold of Light.", False, (220, 215, 205)),
                ("", False, (0, 0, 0)),
                ("RECOVERED CLUES & INSCRIPTIONS:", True, (130, 225, 160)),
                ("• The Ancient Pedestal:", True, (240, 200, 110)),
                (f"  {ped_st}", False, (100, 230, 150) if pedestal_found else (175, 170, 165)),
                ("• The Weathered Stone Tablet:", True, (240, 200, 110)),
                (f"  {tab_st}", False, (100, 230, 150) if tablet_found else (175, 170, 165)),
                ("• The Whispering Stump:", True, (240, 200, 110)),
                (f"  {stu_st}", False, (100, 230, 150) if stump_found else (175, 170, 165)),
                ("• The Ancient Statue:", True, (240, 200, 110)),
                (f"  {sta_st}", False, (100, 230, 150) if statue_found else (175, 170, 165)),
                ("", False, (0, 0, 0)),
                ("SANCTUM KEYS (RANK 1 — 3):", True, (255, 215, 120)),
                ("• Bronze Key [1]:", True, (205, 140, 80)),
                (f"  {b_key_st}", False, (100, 230, 150) if has_bronze else (175, 170, 165)),
                ("• Silver Key [2]:", True, (195, 205, 220)),
                (f"  {s_key_st}", False, (100, 230, 150) if has_silver else (175, 170, 165)),
                ("• Gold Key [3]:", True, (245, 205, 75)),
                (f"  {g_key_st}", False, (100, 230, 150) if has_gold else (175, 170, 165)),
            ]
        else:
            # Tab 2: Observations / Field Notes
            return [
                ("FIELD OBSERVATIONS — THE THRESHOLD OF LIGHT", True, (248, 224, 148)),
                ("Scientific notes on environmental phenomena, illumination, and door mechanisms:", False, (220, 215, 205)),
                ("", False, (0, 0, 0)),
                ("OBSERVATION I: LIGHT PROPAGATION & SHADOW ATTENUATION", True, (140, 210, 255)),
                ("• The lantern projects an optical aura that dissolves ambient shadow fog.", False, (215, 210, 200)),
                ("• Light intensity attenuates with the square of distance from the source.", False, (215, 210, 200)),
                ("• Dark creatures dissipate when touched by direct illumination.", False, (215, 210, 200)),
                ("", False, (0, 0, 0)),
                ("OBSERVATION II: SANCTUM THRESHOLD MECHANISM", True, (255, 200, 120)),
                ("• The heavy stone portal at the forest's edge is locked by ancient tumblers.", False, (215, 210, 200)),
                ("• Press [1], [2], or [3] near the portal to test each collected key.", False, (215, 210, 200)),
                ("• Wrong key insertions harmlessly click without opening; search for the true attuned key.", False, (215, 210, 200)),
                ("", False, (0, 0, 0)),
                ("OBSERVATION III: TEMPLE GEOGRAPHY & ENERGY FLOW", True, (130, 225, 160)),
                ("• The forest floor slopes downward toward deep subterranean chambers.", False, (215, 210, 200)),
                ("• Luminescent flora draw vitality from an ancient underground power conduit.", False, (215, 210, 200)),
                ("• Entering the portal leads deeper into the mountain: Level 2 — The Deepening Dark.", False, (215, 210, 200)),
            ]

    def _build_content_level2(self, inventory: Any, room: Any) -> List[Tuple[str, bool, Tuple[int, int, int]]]:
        clues_list = getattr(inventory, "clues", []) if inventory else []
        has_ins_clue = any(c.get("id") == "inscription_l2" for c in clues_list if isinstance(c, dict))
        ins_read = getattr(room, "inscription", {}).get("read", False) or has_ins_clue

        def _check_mirror(m_id: str) -> bool:
            if not inventory:
                return False
            if hasattr(inventory, "has_mirror") and callable(inventory.has_mirror):
                return inventory.has_mirror(m_id)
            if hasattr(inventory, "has_item") and callable(inventory.has_item):
                return inventory.has_item(m_id)
            return m_id in getattr(inventory, "mirrors", [])

        has_red = _check_mirror("mirror_red")
        has_green = _check_mirror("mirror_green")
        has_blue = _check_mirror("mirror_blue")
        all_mirrors = has_red and has_green and has_blue

        crystals = getattr(room, "crystals", [])
        charged_crystals = sum(1 for c in crystals if getattr(c, "charged", False)) if crystals else 0

        if self.active_tab == 0:
            # Tab 1: Discoveries / Inscriptions
            ins_st = '[DISCOVERED] "White light holds three hidden channels. Each has its own colour and its own power. Find what the light is hiding."' if ins_read else "[UNDISCOVERED] Ancient Inscription carved in the Central Antechamber"

            red_st = "[ACQUIRED] Red Refractor Mirror — Focuses resonant deep spectral frequencies discovered in the ruins" if has_red else "[UNDISCOVERED] First Refractor Mirror — Awaiting discovery in the chambers"
            grn_st = "[ACQUIRED] Green Refractor Mirror — Channels luminous emerald wavelengths through forgotten mechanisms" if has_green else "[UNDISCOVERED] Second Refractor Mirror — Awaiting discovery in the chambers"
            blu_st = "[ACQUIRED] Blue Refractor Mirror — Reflects vibrant azure light across ancient subterranean chasms" if has_blue else "[UNDISCOVERED] Third Refractor Mirror — Awaiting discovery in the chambers"

            red_hdr = "• Red Refractor Mirror:" if has_red else "• Refractor Mirror I:"
            grn_hdr = "• Green Refractor Mirror:" if has_green else "• Refractor Mirror II:"
            blu_hdr = "• Blue Refractor Mirror:" if has_blue else "• Refractor Mirror III:"

            return [
                ("THE ANCIENT INSCRIPTIONS — THE DEEPENING DARK", True, (248, 224, 148)),
                ("Records of spectral light channels and refractor mirrors found in the depths.", False, (220, 215, 205)),
                ("", False, (0, 0, 0)),
                ("THE CENTRAL ANCIENT INSCRIPTION:", True, (255, 215, 120)),
                (f"  {ins_st}", False, (100, 230, 150) if ins_read else (175, 170, 165)),
                ("", False, (0, 0, 0)),
                ("THE THREE REFRACTOR MIRRORS:", True, (130, 225, 160)),
                (red_hdr, True, (245, 120, 110) if has_red else (175, 170, 165)),
                (f"  {red_st}", False, (100, 230, 150) if has_red else (175, 170, 165)),
                (grn_hdr, True, (120, 230, 130) if has_green else (175, 170, 165)),
                (f"  {grn_st}", False, (100, 230, 150) if has_green else (175, 170, 165)),
                (blu_hdr, True, (110, 195, 255) if has_blue else (175, 170, 165)),
                (f"  {blu_st}", False, (100, 230, 150) if has_blue else (175, 170, 165)),
                ("", False, (0, 0, 0)),
                ("ENERGY CRYSTAL STATIONS:", True, (220, 190, 255)),
                (f"• Resonance Crystals Charged: {charged_crystals} of {len(crystals)} energized", False, (215, 210, 200)),
                ("• Recharge stations replenish the lantern battery when standing nearby.", False, (175, 170, 165)),
            ]
        else:
            # Tab 2: Observations / Spectral Notes
            portal_status = "[PORTAL UNLOCKED] All 3 mirrors in place! Approach and press [E] Enter Portal." if all_mirrors else f"[PORTAL SEALED] Requires 3 Refractor Mirrors. Collected: {sum([has_red, has_green, has_blue])}/3."

            return [
                ("SPECTRAL NOTES — OPTICAL CHANNEL SEPARATION", True, (248, 224, 148)),
                ("Laboratory observations on spectral light channels and luminous barriers:", False, (220, 215, 205)),
                ("", False, (0, 0, 0)),
                ("OBSERVATION I: ADDITIVE LIGHT & DIVERSE FREQUENCIES", True, (140, 210, 255)),
                ("• White light holds three hidden channels. Each channel has its own colour and power. Experiment with the lantern to discover them.", False, (215, 210, 200)),
                ("• Certain ancient barriers and forgotten mechanisms respond only to specific resonant light.", False, (215, 210, 200)),
                ("", False, (0, 0, 0)),
                ("OBSERVATION II: WAVELENGTH BARRIERS & SHADOW DYNAMICS", True, (255, 200, 120)),
                ("• Wavelength-sensitive crystal barriers permit passage only when attuned to matching light.", False, (215, 210, 200)),
                ("• Prowling shadow creatures shrink back from illumination; manage battery life carefully.", False, (215, 210, 200)),
                ("• Battery consumption increases when holding isolated spectral channels.", False, (215, 210, 200)),
                ("", False, (0, 0, 0)),
                ("OBSERVATION III: LEVEL EXIT PORTAL REQUIREMENTS", True, (130, 225, 160)),
                (f"• Current Status: {portal_status}", False, (100, 230, 150) if all_mirrors else (245, 140, 120)),
                ("• The ancient portal harnesses the combined optical power of all three spectrum mirrors.", False, (215, 210, 200)),
            ]

    def _build_content_level3(self, inventory: Any, room: Any) -> List[Tuple[str, bool, Tuple[int, int, int]]]:
        chambers = getattr(room, "chambers", [])
        c1_solved = getattr(room, "chamber_1_cleared", False)
        c2_solved = getattr(room, "chamber_2_cleared", False)
        c3_solved = getattr(room, "chamber_3_cleared", False)

        mural_read = getattr(room, "mural_discovered", False)
        headstone_read = getattr(room, "headstone_discovered", False)

        if self.active_tab == 0:
            # Tab 1: Discoveries / Tablets
            mural_st = '[DISCOVERED] "Light reflects true: the angle of departure equals the angle of approach."' if mural_read else "[UNDISCOVERED] Optical Mural Inscription in Chamber 1"
            head_st = '[DISCOVERED] "When the three beams converge upon the Golden Door, the final threshold shall open."' if headstone_read else "[UNDISCOVERED] Carved Monument Inscription in Chamber 2"

            c1_st = "[ACTIVE] Azure laser beam aligned to target sensor" if c1_solved else "[INCOMPLETE] Chamber 1: Route primary beam to the receiver"
            c2_st = "[ACTIVE] Optical splitter balanced across dual sensors" if c2_solved else "[INCOMPLETE] Chamber 2: Divide beam to power dual receivers"
            c3_st = "[ACTIVE] Prism matrix focused upon the grand golden door" if c3_solved else "[INCOMPLETE] Chamber 3: Align prisms to solve the master circuit"

            return [
                ("CHAMBER TABLETS & OPTICAL APPARATUS", True, (248, 224, 148)),
                ("Log of mural readings, mirror alignments, and beam routing circuits in Level 3.", False, (220, 215, 205)),
                ("", False, (0, 0, 0)),
                ("CARVED TABLET INSCRIPTIONS:", True, (255, 215, 120)),
                ("• Optical Mural (Chamber 1):", True, (240, 200, 110)),
                (f"  {mural_st}", False, (100, 230, 150) if mural_read else (175, 170, 165)),
                ("• Carved Monument (Chamber 2):", True, (240, 200, 110)),
                (f"  {head_st}", False, (100, 230, 150) if headstone_read else (175, 170, 165)),
                ("", False, (0, 0, 0)),
                ("CHAMBER BEAM CONDUIT PROGRESSION:", True, (130, 225, 160)),
                ("• Chamber 1 (Single Reflection Law):", True, (140, 210, 255)),
                (f"  {c1_st}", False, (100, 230, 150) if c1_solved else (175, 170, 165)),
                ("• Chamber 2 (Beam Splitter Division):", True, (160, 230, 170)),
                (f"  {c2_st}", False, (100, 230, 150) if c2_solved else (175, 170, 165)),
                ("• Chamber 3 (Compound Prismatic Matrix):", True, (255, 200, 120)),
                (f"  {c3_st}", False, (100, 230, 150) if c3_solved else (175, 170, 165)),
            ]
        else:
            # Tab 2: Observations / Reflection Laws
            return [
                ("THE LAWS OF REFLECTION — OPTICAL PHYSICS", True, (248, 224, 148)),
                ("Empirical rules governing laser beam vectors, prisms, and chamber progression:", False, (220, 215, 205)),
                ("", False, (0, 0, 0)),
                ("LAW I: SPECULAR REFLECTION (θi = θr)", True, (140, 210, 255)),
                ("• The angle of incidence equals the angle of reflection relative to surface normal.", False, (215, 210, 200)),
                ("• Rotating a mirror by 45° alters the reflected beam trajectory by 90°.", False, (215, 210, 200)),
                ("• Stand near a mirror pedestal and press [E] or [R] to adjust its angular alignment.", False, (215, 210, 200)),
                ("", False, (0, 0, 0)),
                ("LAW II: BEAM SPLITTING & RECOMBINATION", True, (255, 200, 120)),
                ("• Semitransparent beam splitters transmit 50% light and reflect 50% at 90°.", False, (215, 210, 200)),
                ("• Both outgoing branches must reach their designated sensors to complete the circuit.", False, (215, 210, 200)),
                ("", False, (0, 0, 0)),
                ("LAW III: THE GRAND GOLDEN DOOR", True, (130, 225, 160)),
                ("• The central portal unlocks only when all three chambers deliver continuous photon energy.", False, (215, 210, 200)),
                ("• Passing through leads to the highest summit: Level 4 — The Ancient Forge.", False, (215, 210, 200)),
            ]

    def _build_content_level4(self, inventory: Any, room: Any) -> List[Tuple[str, bool, Tuple[int, int, int]]]:
        b_relic = getattr(room, "broken_relic_solved", False) if room else False
        m_frag = getattr(room, "memory_fragments_solved", False) if room else False
        a_blue = getattr(room, "ancient_blueprint_solved", False) if room else False
        a_rule = getattr(room, "ancient_rule_discovered", False) if room else False

        relic_st = '[RESTORED] "The Crimson Mirror was shattered; red light cannot focus resonance through any crystal."' if b_relic else "[UNDISCOVERED] Station at Western Alcove"
        mem_st = '[RESTORED] "The Bronze Key fractured; the first rank cannot sustain Crucible resonance."' if m_frag else "[UNDISCOVERED] Station at Eastern Archive"
        blue_st = '[RESTORED] "The sacred blueprint confirms: The Crimson conduit is severed; only Azure and Emerald paths are active."' if a_blue else "[UNDISCOVERED] Station at Southern Dais"
        rule_st = '[DISCOVERED] "A key and crystal must share the same rank. The second path bears blue; the third wears green."' if a_rule else "[UNDISCOVERED] Northern Dais Wall"

        if self.active_tab == 0:
            return [
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
        else:
            return [
                ("TEMPLE ARCHIVES & CHRONICLES OF LIGHT", True, (248, 224, 148)),
                ("Ancient chronicles record the lost history of the Ancient Forge and its sacred fires:", False, (220, 215, 205)),
                ("", False, (0, 0, 0)),
                ("CHRONICLE I: THE ARCHITECTS' CREED", True, (140, 210, 255)),
                ('"Light aligns with its true twin. When Key and Crystal resonate at equal rank,', False, (215, 210, 200)),
                ('the optical mirror focuses the conduit."', False, (215, 210, 200)),
                ("", False, (0, 0, 0)),
                ("CHRONICLE II: THE SHATTERING OF CRIMSON", True, (245, 130, 110)),
                ('"The Crimson Reflector shattered. Its light could no longer focus through any crystal."', False, (230, 205, 195)),
                ("", False, (0, 0, 0)),
                ("CHRONICLE III: THE TWO AWAKENINGS", True, (255, 220, 130)),
                ('"Two distinct paths were laid for future seekers: the quiet path of the Moon,', False, (240, 230, 210)),
                ('and the blazing path of the Sun. Each demands its own attuned metal and mirror color."', False, (240, 230, 210)),
            ]

    def draw(self, surface: pygame.Surface, context: Any = None):
        if not self.is_open:
            return

        # Dim overlay
        dim = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        dim.fill((6, 5, 12, 215))
        surface.blit(dim, (0, 0))

        mx, my = self.x, self.y
        mw, mh = self.width, self.height

        # Main parchment/slate tablet
        tablet = pygame.Surface((mw, mh), pygame.SRCALPHA)
        tablet.fill((20, 17, 28, 252))
        pygame.draw.rect(tablet, (215, 175, 85), (0, 0, mw, mh), width=2, border_radius=8)
        pygame.draw.rect(tablet, (65, 50, 32), (4, 4, mw - 8, mh - 8), width=1, border_radius=6)
        surface.blit(tablet, (mx, my))

        # Corner accents
        c_len = 16
        c_col = (225, 190, 95)
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
        f_tab = pygame.font.SysFont("consolas", 11, bold=True)
        f_body = pygame.font.SysFont("consolas", 11)
        f_bold = pygame.font.SysFont("consolas", 11, bold=True)

        # Header Title
        title_text = self._get_journal_header()
        t_surf = f_title.render(title_text, True, (248, 224, 148))
        tcx = mx + (mw - t_surf.get_width()) // 2
        surface.blit(t_surf, (tcx, my + 14))
        pygame.draw.line(surface, (140, 110, 55), (mx + 35, my + 23), (tcx - 14, my + 23), 1)
        pygame.draw.line(surface, (140, 110, 55), (tcx + t_surf.get_width() + 14, my + 23), (mx + mw - 45, my + 23), 1)

        # Close [X] Button
        close_rect = pygame.Rect(mx + mw - 34, my + 12, 22, 22)
        pygame.draw.rect(surface, (28, 22, 34), close_rect, border_radius=4)
        pygame.draw.rect(surface, (150, 120, 65), close_rect, width=1, border_radius=4)
        x_lbl = f_tab.render("X", True, (240, 215, 140))
        surface.blit(x_lbl, (close_rect.x + (close_rect.width - x_lbl.get_width()) // 2, close_rect.y + 3))

        # Tabs Bar
        tab_titles = self._get_tab_titles()
        tab_w = 200
        tab_spacing = 15
        for i, title in enumerate(tab_titles):
            tx = mx + 35 + i * (tab_w + tab_spacing)
            ty = my + 44
            is_active = (i == self.active_tab)
            t_col = (42, 32, 52) if is_active else (22, 17, 26)
            b_col = (235, 195, 85) if is_active else (70, 56, 40)
            txt_col = (255, 235, 180) if is_active else (160, 148, 130)

            pygame.draw.rect(surface, t_col, (tx, ty, tab_w, 26), border_top_left_radius=4, border_top_right_radius=4)
            pygame.draw.rect(surface, b_col, (tx, ty, tab_w, 26), width=1, border_top_left_radius=4, border_top_right_radius=4)
            if is_active:
                pygame.draw.line(surface, (255, 225, 120), (tx + 2, ty + 25), (tx + tab_w - 2, ty + 25), 2)
                pygame.draw.circle(surface, (245, 215, 110), (tx + 12, ty + 13), 3)

            lbl = f_tab.render(title, True, txt_col)
            surface.blit(lbl, (tx + (tab_w - lbl.get_width()) // 2 + (4 if is_active else 0), ty + 6))

        # Content Plinth
        content_rect = pygame.Rect(mx + 30, my + 74, mw - 60, mh - 108)
        pygame.draw.rect(surface, (13, 10, 16), content_rect, border_radius=6)
        pygame.draw.rect(surface, (90, 72, 48), content_rect, width=1, border_radius=6)

        # Extract context helpers
        inventory = getattr(context, "inventory", None) or getattr(context, "_inventory", None) or context
        room = getattr(context, "room", None) or getattr(context, "level2_room", None) or getattr(context, "level3_room", None) or getattr(context, "level4_room", None) or context

        # Generate content lines
        if self.level_id == "level1":
            raw_items = self._build_content_level1(inventory, room)
        elif self.level_id == "level2":
            raw_items = self._build_content_level2(inventory, room)
        elif self.level_id == "level3":
            raw_items = self._build_content_level3(inventory, room)
        elif self.level_id == "level4":
            raw_items = self._build_content_level4(inventory, room)
        else:
            raw_items = [("JOURNAL NOT AVAILABLE", True, (240, 200, 100))]

        # Word wrap
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

        line_h = 17
        total_content_h = 24 + len(wrapped_lines) * line_h
        visible_h = content_rect.height - 20
        self.max_scroll = max(0, total_content_h - visible_h)
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

        # Render content strictly clipped
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

        # Scrollbar
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

        # Consistent Footer
        foot_txt = "[W/S / ↑/↓] Scroll   |   [J / ESC] Close"
        foot_s = f_body.render(foot_txt, True, (175, 160, 135))
        surface.blit(foot_s, (mx + (mw - foot_s.get_width()) // 2, my + mh - 24))

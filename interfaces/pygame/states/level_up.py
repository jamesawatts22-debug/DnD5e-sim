import os
from interfaces.pygame.states.base_state import BaseState
from interfaces.pygame.ui.menu import Menu
from interfaces.pygame.ui.backgrounds import BackgroundManager
from core.players.leveler import load_player_classes, add_class_level
from core.game_rules.constants import COLOR_BG, COLOR_LIGHT_GRAY, SCREEN_WIDTH

from interfaces.pygame.states.base_state import BaseState
from interfaces.pygame.ui.menu import Menu
from interfaces.pygame.ui.backgrounds import BackgroundManager
from interfaces.pygame.ui.inventory_panel import InventoryPanel
from core.players.leveler import load_player_classes, add_class_level
from core.players.player import load_weapons, load_armor, load_shields, load_trinkets
from core.game_rules.constants import COLOR_BG, COLOR_LIGHT_GRAY, SCREEN_WIDTH, scale_x, scale_y

class LevelUpState(BaseState):
    def __init__(self, game, font, is_dev_mode=False):
        super().__init__(game, font)
        self.is_dev_mode = is_dev_mode
        self.mode = "CLASS_SELECT"

        # Use manager to pick random background
        self.background = BackgroundManager.get_levelup_bg()

        # Load data for inventory panel
        weapons_db = load_weapons().get('weapon_list', {})
        armor_db = load_armor()
        shields_db = load_shields()
        trinkets_db = load_trinkets()
        self.inventory_panel = InventoryPanel(font, weapons_db, armor_db, shields_db, trinkets_db)

        self.refresh_class_menu()

    def refresh_class_menu(self):
        self.class_names = [name.title() for name in load_player_classes().keys()]
        
        from core.players.leveler import get_level_up_benefits
        descriptions = {}
        for name in self.class_names:
            descriptions[name] = get_level_up_benefits(self.game.player, name)

        # 25% transparent means 75% opacity, alpha = 255 * 0.75 = 191
        self.menu = Menu(self.class_names, self.font, bg_color=COLOR_BG, border_color=COLOR_LIGHT_GRAY, alpha=191, width=300, descriptions=descriptions)
        self.active_menu = self.menu

    def on_select(self, option):
        if self.mode == "CLASS_SELECT":
            add_class_level(self.game.player, option.lower())
            
            # If dev mode and not max level, ask to level up again
            if self.is_dev_mode and self.game.player.get('level', 1) < 20:
                self.mode = "AGAIN_PROMPT"
                self.active_menu = Menu(["Yes", "No"], self.font, header="Level up again?")
            else:
                from interfaces.pygame.states.hub import HubState
                self.game.change_state(HubState(self.game, self.font))
                
        elif self.mode == "AGAIN_PROMPT":
            if option == "Yes":
                self.mode = "CLASS_SELECT"
                self.refresh_class_menu()
            else:
                from interfaces.pygame.states.hub import HubState
                self.game.change_state(HubState(self.game, self.font))

    def draw(self, screen):
        # Draw background manually to avoid super().draw() centering the menu
        self.draw_background(screen)

        from interfaces.pygame.ui.panel import draw_text_outlined
        title_text = "Level Up!"
        tw, th = self.font.size(title_text)
        draw_text_outlined(screen, title_text, self.font, (255, 255, 0), (SCREEN_WIDTH // 2) - (tw // 2), 50)

        # Position class selection menu on the left
        if self.active_menu:
            width, height = screen.get_size()
            menu_width = self.active_menu.get_width()
            
            # Left-aligned position (matching Hub)
            menu_x = scale_x(80) + menu_width // 2
            # Offset down slightly from the title
            menu_y = scale_y(150)
            
            self.active_menu.draw(screen, menu_x, menu_y, force_bottom_desc=True)

        # Draw Player Info Panel (on the right)
        self.inventory_panel.draw(screen, self.game.player)
        self.inventory_panel.draw_tooltip(screen)


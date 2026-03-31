import pygame
from .base_state import BaseState
from interfaces.pygame.ui.menu import Menu
from interfaces.pygame.ui.backgrounds import BackgroundManager
from interfaces.pygame.ui.panel import draw_text_outlined
from core.game_rules.score_manager import ScoreManager
from core.game_rules.constants import scale_y, scale_x, COLOR_WHITE, COLOR_GOLD, SCREEN_WIDTH, SCREEN_HEIGHT

class HighScoreState(BaseState):
    def __init__(self, game, font):
        super().__init__(game, font)
        self.background = BackgroundManager.get_rest_bg()
        
        self.high_scores = ScoreManager.load_high_scores()
        self.menu = Menu(["Back"], font, width=150)
        self.active_menu = self.menu

    def on_select(self, option):
        if option == "Back":
            from .title import TitleState
            self.game.change_state(TitleState(self.game, self.font))

    def draw(self, screen):
        self.draw_background(screen)
        width, height = screen.get_size()
        
        # Title
        title_str = "Hall of Valor"
        tw, th = self.font.size(title_str)
        draw_text_outlined(screen, title_str, self.font, COLOR_GOLD, width // 2 - tw // 2, scale_y(50))
        
        # Draw Scores
        start_y = scale_y(150)
        spacing = scale_y(40)
        
        if not self.high_scores:
            msg = "No legends yet..."
            mw, mh = self.font.size(msg)
            draw_text_outlined(screen, msg, self.font, COLOR_WHITE, width // 2 - mw // 2, height // 2)
        else:
            for i, entry in enumerate(self.high_scores):
                rank_str = f"{i+1}."
                name_str = entry['name']
                score_str = str(entry['score'])
                
                # Rank
                draw_text_outlined(screen, rank_str, self.font, COLOR_GOLD, width // 2 - scale_x(250), start_y + i * spacing)
                # Name
                draw_text_outlined(screen, name_str, self.font, COLOR_WHITE, width // 2 - scale_x(200), start_y + i * spacing)
                # Score (Right aligned)
                sw, sh = self.font.size(score_str)
                draw_text_outlined(screen, score_str, self.font, COLOR_GOLD, width // 2 + scale_x(200) - sw, start_y + i * spacing)

        # Menu (Back button)
        if self.active_menu:
            self.active_menu.draw(screen, width // 2, height - scale_y(80))

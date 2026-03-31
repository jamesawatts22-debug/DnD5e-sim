import pygame
import random
from interfaces.pygame.states.base_state import BaseState
from interfaces.pygame.ui.menu import Menu
from interfaces.pygame.ui.dialogue_box import DialogueBox
from interfaces.pygame.ui.backgrounds import BackgroundManager

from interfaces.pygame.ui.panel import Panel, draw_text_outlined
from core.game_rules.score_manager import ScoreManager
from core.game_rules.constants import scale_y, scale_x, COLOR_GOLD, COLOR_WHITE, SCREEN_WIDTH, SCREEN_HEIGHT

class GameOverState(BaseState):
    def __init__(self, game, font, retired=False):
        super().__init__(game, font)
        self.background = BackgroundManager.get_gameover_bg()

        self.retired = retired
        self.menu = Menu(["Play Again", "Quit"], font, width=200)
        self.active_menu = self.menu
        self.dialogue = DialogueBox(self.font)
        self.message_queue = []
        
        # Scoring
        self.total_score, self.score_breakdown = ScoreManager.calculate_score(self.game.player, retired=self.retired)
        ScoreManager.save_high_score(self.game.player.get('name', 'Adventurer'), self.total_score)

        # ======================
        # 🧓 RETIREMENT MESSAGES
        # ======================
        self.retirement_messages = [
            "You retire to a quiet farm. The goats respect you.",
            "You open a tavern. The drinks are terrible, but the stories are great.",
            "You become a legend... mostly exaggerated.",
            "You retire rich! Unfortunately, inflation exists.",
            "You vanish into the wilderness. Probably fine.",
            "You write a memoir. No one believes it.",
            "You settle down... for about a week.",
        ]

        # ======================
        # 💀 DEATH MESSAGES
        # ======================
        self.death_messages = [
            "You have fallen in battle.",
            "Your journey ends here.",
            "The dungeon claims another soul.",
        ]

        # ======================
        # 📢 BUILD MESSAGE QUEUE
        # ======================
        if self.retired:
            msg = random.choice(self.retirement_messages)
            messages = [f"{self.game.player.get('name', 'Hero')} retires...", msg]
        else:
            msg = random.choice(self.death_messages)
            messages = ["GAME OVER", msg]

        if self.retired:
            msg = random.choice(self.retirement_messages)
            self.queue_message(f"{self.game.player.get('name', 'Hero')} retires...")
            self.queue_message(msg)
        else:
            msg = random.choice(self.death_messages)
            self.queue_message("GAME OVER")
            self.queue_message(msg)

        self.start_next_message()
    
    def queue_message(self, text):
        self.message_queue.append(text)

    def start_next_message(self):
        if self.message_queue:
            self.dialogue.set_messages([self.message_queue.pop(0)])

    def on_select(self, option):
        if option == "Play Again":
            from interfaces.pygame.states.title import TitleState
            self.game.player_name = ""
            self.game.change_state(TitleState(self.game, self.font))
        elif option == "Quit":
            pygame.quit()
            exit()

    def update(self, events):
        # Dialogue handling (same as combat)
        if self.dialogue.current_message:
            self.dialogue.update()

            for event in events:
                if event.type == pygame.KEYDOWN:
                    was_typing = self.dialogue.is_typing
                    self.dialogue.handle_event(event)

                    if not was_typing and not self.dialogue.current_message:
                        if self.message_queue:
                            self.start_next_message()

            return

        # After dialogue → allow menu
        super().update(events)

    def draw(self, screen):
        self.draw_background(screen)

        # If dialogue still playing → show it
        if self.dialogue.current_message:
            self.dialogue.draw(screen)
        else:
            # Draw Score Breakdown
            panel_w = 400
            panel_h = 300
            from core.game_rules.constants import BASE_WIDTH, BASE_HEIGHT
            panel = Panel(BASE_WIDTH // 2 - panel_w // 2, 50, panel_w, panel_h, alpha=200)
            rect = panel.draw(screen)
            
            draw_text_outlined(screen, "Final Score Breakdown", self.font, COLOR_GOLD, rect.centerx - self.font.size("Final Score Breakdown")[0]//2, rect.y + scale_y(15))
            
            y_off = rect.y + scale_y(60)
            for label, score in self.score_breakdown.items():
                draw_text_outlined(screen, label, self.font, COLOR_WHITE, rect.x + scale_x(20), y_off)
                score_str = str(score)
                sw, sh = self.font.size(score_str)
                draw_text_outlined(screen, score_str, self.font, COLOR_GOLD, rect.right - scale_x(20) - sw, y_off)
                y_off += scale_y(35)
            
            pygame.draw.line(screen, COLOR_GOLD, (rect.x + 10, y_off), (rect.right - 10, y_off), 2)
            y_off += scale_y(10)
            
            draw_text_outlined(screen, "TOTAL SCORE", self.font, COLOR_GOLD, rect.x + scale_x(20), y_off)
            total_str = str(self.total_score)
            tw, th = self.font.size(total_str)
            draw_text_outlined(screen, total_str, self.font, COLOR_WHITE, rect.right - scale_x(20) - tw, y_off)

            # Draw Menu
            if self.active_menu:
                self.active_menu.draw(screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT - scale_y(150))

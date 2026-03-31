import pygame
import random

class DevTools:
    @staticmethod
    def apply_dev_action(action, game):
        """
        Applies a developer tool action to the game state.
        """
        p = game.player
        
        if action == "1,000 HP":
            p["max_hp"] = 1000
            p["current_hp"] = 1000
            p["hp"] = 1000 # Compat
            return "HP set to 1,000!"

        elif action == "10,000 Gold":
            inv = p.get("inventory_ref", {})
            inv["gold"] = inv.get("gold", 0) + 10000
            return "Added 10,000 Gold!"

        elif action == "Level Up":
            from core.players.leveler import xp_to_next_level
            from interfaces.pygame.states.level_up import LevelUpState
            
            # We don't necessarily need to add XP if we're just forcing the state,
            # but let's keep the logic consistent.
            game.change_state(LevelUpState(game, pygame.font.SysFont("Arial", 32), is_dev_mode=True))
            return "Dev Level Up Triggered!"

        elif action == "Restart Game":
            from interfaces.pygame.states.class_select import ClassSelectState
            game.player = None
            game.change_state(ClassSelectState(game, pygame.font.SysFont("Arial", 32)))
            return "Game Restarted!"

        return None

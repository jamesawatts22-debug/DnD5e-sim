import pygame

SPRITE_SIZE = 128

class EnemySpriteManager:
    def __init__(self):
        self.sheet = pygame.image.load("assets/sprites/enemies.png").convert_alpha()
        self.sprites = {}

        self.load_sprites()

    def load_sprites(self):
        enemy_names = [
            "Slime",
            "Goblin",
            "Skeleton",
            "Orc"
        ]

        for i, name in enumerate(enemy_names):
            rect = pygame.Rect(i * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
            image = self.sheet.subsurface(rect)

            self.sprites[name.lower()] = image

    def get(self, name):
        return self.sprites.get(name.lower())
import pygame

class Obstacle:
    def __init__(self, x, y, radius):
        self.position = pygame.Vector2(x, y)
        self.radius = radius

    def draw(self, screen):
        pygame.draw.circle(screen, (119, 136, 153), (int(self.position.x), int(self.position.y)), self.radius)

class FoodArea:
    def __init__(self, x, y, radius):
        self.position = pygame.Vector2(x, y)
        self.radius = radius

    def draw(self, screen):
        pygame.draw.circle(screen, (154, 205, 50), (int(self.position.x), int(self.position.y)), self.radius, 2)

class HidingSpot:
    def __init__(self, x, y, radius):
        self.position = pygame.Vector2(x, y)
        self.radius = radius

    def draw(self, screen):
        pygame.draw.circle(screen, (210, 180, 140), (int(self.position.x), int(self.position.y)), self.radius, 2)

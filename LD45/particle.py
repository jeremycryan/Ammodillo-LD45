import random
import pygame
from helpers import normalize, random_angle_vec, list_addition

class Particle(object):

    def __init__(self, game, pos):

        self.game = game
        self.x, self.y = pos
        self.max_speed = 12
        self.deccel = 0.04

        self.sprite = pygame.Surface((self.game.c.TILE_SIZE,)*2)
        self.sprite.fill((255, 0, 0))

        self.speed = random.random() * self.max_speed
        self.velocity = random_angle_vec()
        normalize(self.velocity, self.speed)

        self.since_spawn = 0
        self.game.particles.add(self)

    def update(self, dt):
        self.since_spawn += dt

        self.speed *= self.deccel**dt
        normalize(self.velocity, self.speed)

        self.check_arena_bounds()

        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt

    def draw(self):
        camera = self.game.camera
        scale = camera.scale
        size_original = 20
        width = int(size_original * scale)
        scaled = pygame.transform.scale(self.sprite, (width, width))
        x = int((self.x - camera.x) * scale * self.game.c.TILE_SIZE - width / 2 + self.game.c.WINDOW_WIDTH // 2)
        y = int((self.y - camera.y) * scale * self.game.c.TILE_SIZE - width / 2 + self.game.c.WINDOW_HEIGHT // 2)
        self.game.screen.blit(scaled, (x, y))

    def check_arena_bounds(self):
        if not self.game.c.in_arena_bounds([self.x, self.y]):
            direction = [self.x, self.y]
            normalize(direction, -1)
            self.push(*direction)

    def push(self, x, y):
        self.velocity[0] += x
        self.velocity[1] += y

class Feather(Particle):

    def __init__(self, game, pos):

        self.game = game
        self.x, self.y = pos
        self.max_speed = 8
        self.deccel = 0.1

        path = random.choice(["feather_1.png", "feather_2.png", "feather_3.png"])
        self.sprite = pygame.image.load(path)
        self.sprite = pygame.transform.rotate(self.sprite, int(random.random() * 360))

        self.speed = random.random() * self.max_speed
        self.velocity = random_angle_vec()
        normalize(self.velocity, self.speed)

        self.since_spawn = 0
        self.game.particles.add(self)
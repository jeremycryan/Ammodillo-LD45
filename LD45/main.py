import pygame
import sys
from map import Map
from camera import Camera
from player import Player
from enemy import Enemy, Bursty, Chick
from helpers import dist_between_lists
import time
from splash import BulletSpawn


class Game(object):

    def __init__(self):
        pygame.mixer.init(22100, -16, 2, 64)
        pygame.init()

        self.c = Constants()

        self.screen = pygame.display.set_mode(self.c.WINDOW_SIZE)
        pygame.display.set_caption("Ammodillo")

        self.camera = Camera(self)
        self.player = Player(self)
        self.map = Map(self)

        self.reset_things()

        while True:
            self.main()

    def reset_things(self):
        self.enemies = set()
        self.bullets = set()
        self.particles = set()

        self.wave_spawn_gap = 5

        self.waves = [[Chick(self, pos=self.c.CENTER_ARCH)],

                      [Chick(self, pos=self.c.CENTER_ARCH),
                       Chick(self, pos=self.c.LEFT_ARCH),
                       Chick(self, pos=self.c.RIGHT_ARCH)],

                      [Bursty(self, pos=self.c.CENTER_ARCH)],

                      [Chick(self, pos=(self.c.CENTER_ARCH[0], self.c.CENTER_ARCH[1] + 1)),
                       Chick(self, pos=self.c.LEFT_ARCH),
                       Chick(self, pos=self.c.RIGHT_ARCH),
                       Bursty(self, pos=(self.c.CENTER_ARCH[0], self.c.CENTER_ARCH[1] - 1))]]

        self.shade = pygame.Surface(self.c.WINDOW_SIZE).convert()
        self.shade.fill((0, 0, 0))
        self.shade_alpha = 0

    def update_shade(self, dt):
        rate = 100
        end_alpha = 150
        if self.player.dead:
            da = dt * rate
            self.shade_alpha = min(self.shade_alpha + da, end_alpha)
            self.shade.set_alpha(int(self.shade_alpha))

    def main(self):

        then = time.time()
        time.sleep(0.001)

        self.time_without_enemies = 0

        self.enemies_to_destroy = set()
        self.bullets = set()
        self.splashes = set()
        self.splashes_to_destroy = set()

        fpss = [0] * 100

        while True:

            now = time.time()
            dt = now - then
            then = now

            # Measure fps
            fpss.pop()
            fpss.insert(0, 1/dt)
            if time.time()%1 < 0.01:
                print("FPS: %s" % (min(fpss)))

            # Do stuff
            dt = self.camera.update(dt)
            self.check_global_events(dt)
            self.player.update(dt)
            self.update_shade(dt)

            # Draw stuff
            self.screen.fill(self.c.BLACK)
            self.map.draw()
            for particle in self.particles:
                particle.update(dt)
                particle.draw()
            for enemy in self.enemies:
                enemy.update(dt)
                enemy.draw()
            self.player.draw()
            self.enemies -= self.enemies_to_destroy
            for bullet in self.bullets:
                bullet.update(dt)
                bullet.draw()
            dead_bullets = set([b for b in self.bullets if b.since_shoot > b.duration or b.out_of_bounds])
            for dead_bullet in dead_bullets:
                BulletSpawn(self, [dead_bullet.x, dead_bullet.y])
            self.bullets -= dead_bullets
            self.splashes -= self.splashes_to_destroy
            for splash in self.splashes:
                splash.update(dt)
                splash.draw()
            if self.shade_alpha:
                self.screen.blit(self.shade, (0, 0))
            pygame.display.flip()

    def check_global_events(self, dt):
        events = pygame.event.get()
        pygame.event.pump()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == self.player.dodge_key:
                    self.player.dodge()

        if dt > 0.05:
            return 0.05

        if not self.enemies:
            self.time_without_enemies += dt
        if self.time_without_enemies >= self.wave_spawn_gap:
            self.time_without_enemies = 0
            self.enemies |= set(self.waves.pop(0))

        return dt * self.camera.speed


class Constants(object):
    def __init__(self):
        self.WINDOW_WIDTH = 800
        self.WINDOW_HEIGHT = 600
        self.WINDOW_SIZE = (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.BLACK = (0, 0, 0)
        self.TILE_SIZE = 32

        self.CENTER_ARCH = (0, -8)
        self.LEFT_ARCH = (-7, -6)
        self.RIGHT_ARCH = (7, -6)

        self.MAJOR_RADIUS = 12
        self.MINOR_RADIUS = 8

    def in_arena_bounds(self, pos):
        x, y = pos
        thresh = 0.5
        if dist_between_lists(pos, self.CENTER_ARCH) < 2:
            return True
        return x**2/((self.MAJOR_RADIUS - thresh)**2) + y**2/((self.MINOR_RADIUS - thresh)**2) <= 1


if __name__ == "__main__":

    Game()
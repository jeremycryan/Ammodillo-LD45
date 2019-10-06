from sprite_tools import Sprite, SpriteSheet
import pygame
import random

class Mouse(object):

    second_jump_chance = 0.06

    def __init__(self, game, pos):

        self.x, self.y = pos
        self.game = game

        self.sprite = Sprite(fps=4)
        path = random.choice(["mouse.png", "mouse_brown.png"])
        idle = SpriteSheet(path, (2, 1), 2)
        self.sprite.add_animation({"Idle": idle})
        self.sprite.start_animation("Idle")

        self.jumping = False
        self.jump_period = 0.25
        self.jump_height = 1.25
        self.yoff = 0
        self.since_jump = 100
        self.jump_func = lambda x: (-((x - self.jump_period/2)/(self.jump_period/2))**2 + 1) * self.jump_height

        self.w = self.sprite.get_good_frame().get_width()
        self.h = self.sprite.get_good_frame().get_height()

        self.shadow = pygame.image.load("shadow.png").convert()
        self.shadow.set_alpha(80)
        self.shadow.set_colorkey((255, 0, 0))

    def jump(self):
        self.jumping = True
        self.since_jump = 0

    def update(self, dt):
        self.sprite.update(dt)
        self.since_jump += dt

        s2jc = self.second_jump_chance if not self.game.hype() else 1.5

        if not self.jumping:
            chance = s2jc * dt
            if random.random() < chance:
                self.jump()
        else:
            if self.since_jump > self.jump_period:
                self.jumping = False
                self.yoff = 0
            else:
                self.yoff = self.jump_func(self.since_jump)

    def draw(self):
        camera = self.game.camera
        scale = camera.scale
        width = int(self.w * scale)
        height = int(self.h * scale)
        x = int((self.x - camera.x) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_WIDTH//2)
        y = int((self.y - self.yoff - camera.y) * scale * self.game.c.TILE_SIZE - height/2 + self.game.c.WINDOW_HEIGHT//2)
        scaled = pygame.transform.scale(self.sprite.get_good_frame(), (width, height))

        soffset = 30
        shadow = pygame.transform.scale(self.shadow, (int(self.shadow.get_width() * scale), int(self.shadow.get_height() * scale)))
        self.game.screen.blit(shadow, (int(x - 0*scale), int(y + soffset*scale)))

        self.game.screen.blit(scaled, (x, y))
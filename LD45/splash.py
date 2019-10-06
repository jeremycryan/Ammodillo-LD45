from sprite_tools import Sprite, SpriteSheet
import pygame

class Splash(object):

    def __init__(self, game, pos):

        spritesheet_path = "bullet_pop.png"
        splash_sheet = SpriteSheet(spritesheet_path, (8, 1), 8)
        self.sprite = Sprite(12)
        self.sprite.add_animation({"Pop": splash_sheet})
        self.sprite.start_animation("Pop")
        self.x, self.y = pos
        self.game = game
        self.game.splashes.add(self)
        self.width = 28
        self.duration = 0.5
        self.age = 0

    def update(self, dt):
        self.sprite.update(dt)
        self.age += dt
        if self.age >= self.duration:
            self.destroy()

    def destroy(self):
        self.game.splashes_to_destroy.add(self)

    def draw(self):
        if self in self.game.splashes_to_destroy:
            return
        camera = self.game.camera
        scale = camera.scale
        width = int(self.width * scale)
        x = int((self.x - camera.x) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_WIDTH//2)
        y = int((self.y - camera.y) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_HEIGHT//2)
        scaled = pygame.transform.scale(self.sprite.get_good_frame(), (width, width))
        self.game.screen.blit(scaled, (x, y))

class BulletSpawn(Splash):

    def __init__(self, game, pos):
        super().__init__(game, pos)

        spritesheet_path = "bullet_spawn.png"
        splash_sheet = SpriteSheet(spritesheet_path, (8, 1), 8)
        self.sprite = Sprite(16)
        self.sprite.add_animation({"Pop": splash_sheet})
        self.sprite.start_animation("Pop")
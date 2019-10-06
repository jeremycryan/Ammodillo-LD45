import pygame

class Bullet(object):

    def __init__(self, game, pos, velocity):
        sprite_path = "bullet.png"
        bad_sprite_path = "bad_bullet.png"
        self.game = game
        self.sprite = pygame.image.load(sprite_path).convert()
        self.bad_sprite = pygame.image.load(bad_sprite_path).convert()
        self.sprite.set_colorkey((0, 255, 0))
        self.bad_sprite.set_colorkey((0, 255, 0))
        self.x, self.y = pos
        self.velocity = velocity
        self.friendly = False

        self.since_last_shadow = 0
        self.shadow_period = 0.02
        self.since_shoot = 0
        self.duration = 2.0
        self.out_of_bounds = False

        self.hit_radius = 0.35
        self.damage = 1
        self.knockback = 5

        self.last_positions = [pos] * 10

    def draw(self):
        camera = self.game.camera
        scale = camera.scale
        size_original = 20
        width = int(size_original * scale)
        if self.friendly:

            scaled = pygame.transform.scale(self.sprite, (width, width))
        else:
            scaled = pygame.transform.scale(self.bad_sprite, (width, width))

        alpha = 0
        # for i, pos in enumerate(self.last_positions[::-1] + [[self.x, self.y]]):
        #     x = int((pos[0] - camera.x) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_WIDTH//2)
        #     y = int((pos[1] - camera.y) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_HEIGHT//2)
        #     scaled.set_alpha(int(alpha))
        #     alpha += 100/len(self.last_positions)
        #     if pos == [self.x, self.y]:
        #         scaled.set_alpha(255)
        #     self.game.screen.blit(scaled, (x, y))

        x = int((self.x - camera.x) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_WIDTH//2)
        y = int((self.y - camera.y) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_HEIGHT//2)
        self.game.screen.blit(scaled, (x, y))

    def get_caught(self):
        self.last_positions = [[self.x, self.y]] * 10

    def update(self, dt):
        self.since_last_shadow += dt
        self.since_shoot += dt

        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt

        if self.since_last_shadow >= self.shadow_period:
            self.last_positions.pop()
            self.last_positions.insert(0, (self.x, self.y))
            self.since_last_shadow -= self.shadow_period

        if not self.game.c.in_arena_bounds([self.x, self.y]):
            self.out_of_bounds = True

class BasicBullet(Bullet):
    pass
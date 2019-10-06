import pygame
import random
import math
from helpers import normalize, list_subtraction, list_addition, magnitude, dist_between, angle_vec
from bullet import BasicBullet
from splash import Splash
from sprite_tools import Sprite, SpriteSheet
from splash import BulletSpawn
from particle import Feather

class Enemy(object):

    def __init__(self, game):
        sprite_path = "enemy.png"
        self.game = game
        self.x = 2
        self.y = 5
        self.sprite = pygame.image.load(sprite_path)
        self.width = self.sprite.get_width()

        self.deccel = 0.05
        self.velocity = [0, 0]
        self.accel = 10
        self.max_speed = 14

        self.bullet_period = 1
        self.since_last_bullet = -random.random() * self.bullet_period

        self.bullet_type = BasicBullet
        self.bullet_speed = 15
        self.recoil_speed = 5
        self.hit_radius = (self.width/self.game.c.TILE_SIZE)/2

        self.hp = 1

    def draw(self):
        camera = self.game.camera
        scale = camera.scale
        width = int(self.width * scale)
        x = int((self.x - camera.x) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_WIDTH//2)
        y = int((self.y - camera.y) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_HEIGHT//2)
        scaled = pygame.transform.scale(self.sprite, (width, width))
        self.game.screen.blit(scaled, (x, y))

    def deccelerate(self, dt):

        amt = self.deccel ** dt
        self.velocity[0] *= amt
        self.velocity[1] *= amt

    def update(self, dt):
        self.deccelerate(dt)
        self.since_last_bullet += dt
        self.check_bullet_behavior()
        self.move_toward_player(dt)
        self.check_arena_bounds()
        self.move(*self.velocity, dt)
        self.check_bullet_collisions()
        self.check_enemy_collisions()

    def check_bullet_behavior(self):
        if self.since_last_bullet > self.bullet_period:
            self.fire_bullet_at_player()

    def move(self, x, y, dt):
        self.x += x * dt
        self.y += y * dt

    def fire_bullet_at_player(self):
        self.since_last_bullet = 0

        velocity = list_subtraction([self.game.player.x, self.game.player.y], [self.x, self.y])
        normalize(velocity, self.bullet_speed)

        push_vec = velocity[:]
        normalize(push_vec, -self.recoil_speed)
        self.push(*push_vec)
        new_bullet = self.bullet_type(self.game, (self.x, self.y), velocity)
        self.game.bullets.add(self.bullet_type(self.game, (self.x, self.y), velocity))
        BulletSpawn(self.game, (new_bullet.x, new_bullet.y))


    def push(self, x, y):
        self.velocity[0] += x
        self.velocity[1] += y

    def move_toward_player(self, dt):
        diff = list_subtraction([self.game.player.x, self.game.player.y], [self.x, self.y])
        normalize(diff, self.accel*dt)
        self.velocity = list_addition(self.velocity, diff)
        if magnitude(self.velocity) > self.max_speed:
            normalize(self.velocity, self.max_speed)



    def check_bullet_collisions(self):
        ceb = self.colliding_friendly_bullets()
        for item in ceb:
            self.get_hit_by(item)

        self.game.bullets -= ceb

    def check_enemy_collisions(self):
        for item in self.game.enemies:
            if not (self is item) and dist_between(self, item) < self.hit_radius + item.hit_radius:
                direction = list_subtraction([self.x, self.y], [item.x, item.y])
                normalize(direction, 2)
                self.push(*direction)

    def colliding_friendly_bullets(self):
        ceb = set()
        for bullet in self.game.bullets:
            if bullet.friendly:
                dist = (bullet.x - self.x)**2 + (bullet.y - self.y)**2
                if dist < (self.hit_radius + bullet.hit_radius)**2:
                    ceb.add(bullet)
        return ceb

    def get_hit_by(self, bullet):
        self.hp -= bullet.damage
        if self.hp <= 0:
            self.game.enemies_to_destroy.add(self)
        Splash(self.game, [bullet.x, bullet.y])

        impact_amt = bullet.velocity[:]
        normalize(impact_amt, bullet.knockback)
        self.push(*impact_amt)

    def check_arena_bounds(self):
        if not self.game.c.in_arena_bounds([self.x, self.y]):
            direction = [self.x, self.y]
            normalize(direction, -3)
            self.push(*direction)



class Bursty(Enemy):

    def __init__(self, game, pos = (0, 0)):
        super().__init__(game)
        idle_left = SpriteSheet("bird_idle_left.png", (8, 1), 8)
        idle_right = SpriteSheet("bird_idle_left.png", (8, 1), 8)
        idle_right.reverse(1, 0)
        self.sprite = Sprite(12)
        self.sprite.add_animation({"IdleLeft": idle_left,
                                   "IdleRight": idle_right})

        self.sprite.start_animation("IdleLeft")
        self.width = self.sprite.get_good_frame().get_width()
        self.hit_radius = (self.width/self.game.c.TILE_SIZE)*0.3

        self.since_last_bullet = -3

        self.bullet_period = 0.15
        self.reload_time = 2.5
        self.clip = 6
        self.clip_size = self.clip
        self.recoil_speed = 2

        self.next_attack = 0  # 0 is machine gun, 1 is burst

        self.x, self.y = pos
        self.max_speed = 8
        self.accel = 5

        self.hp = 6

    def check_bullet_behavior(self):
        if self.since_last_bullet > self.bullet_period and self.clip and not self.next_attack:
            self.fire_bullet_at_player()
            self.clip -= 1
        elif self.since_last_bullet > self.bullet_period and self.clip and self.next_attack:
            self.clip = 0
            self.fire_radial_bullets()
        if self.clip <= 0:
            self.next_attack = (random.random() < 0.3)
            self.since_last_bullet = -self.reload_time
            self.clip = self.clip_size

    def fire_radial_bullets(self):
        max_angle = math.pi * 2
        n = 24
        for i in range(n):
            angle = i/n * max_angle
            velocity = angle_vec(angle)
            normalize(velocity, 12)
            new_bullet = BasicBullet(self.game, [self.x, self.y], velocity)
            self.game.bullets.add(new_bullet)
        BulletSpawn(self.game, [self.x, self.y])

    def draw(self):
        camera = self.game.camera
        scale = camera.scale
        width = int(self.width * scale)
        x = int((self.x - camera.x) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_WIDTH//2)
        y = int((self.y - camera.y) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_HEIGHT//2)
        scaled = pygame.transform.scale(self.sprite.get_good_frame(), (width, width))
        self.game.screen.blit(scaled, (x, y))

    def move_toward_player(self, dt):
        super().move_toward_player(dt)

    def update(self, dt):
        super().update(dt)
        self.sprite.update(dt)

        thresh = 1
        if self.game.player.x < self.x - thresh and not self.sprite.active_animation == "IdleLeft":
            self.sprite.start_animation("IdleLeft")
        elif self.game.player.x > self.x + thresh and not self.sprite.active_animation == "IdleRight":
            self.sprite.start_animation("IdleRight")

    def get_hit_by(self, bullet):
        super().get_hit_by(bullet)
        if self.hp <= 0:
            for i in range(20):
                Feather(self.game, [self.x, self.y])
        else:
            for i in range(2):
                Feather(self.game, [self.x, self.y])


class Chick(Enemy):

    def __init__(self, game, pos = (0, 0)):
        super().__init__(game)
        idle_right = SpriteSheet("chick_idle_right.png", (6, 1), 6)
        idle_left = SpriteSheet("chick_idle_right.png", (6, 1), 6)
        idle_left.reverse(1, 0)
        self.sprite = Sprite(12)
        self.sprite.add_animation({"IdleLeft": idle_left,
                                   "IdleRight": idle_right})

        self.sprite.start_animation("IdleLeft")
        self.width = self.sprite.get_good_frame().get_width()
        self.hit_radius = (self.width/self.game.c.TILE_SIZE)*0.3

        self.bullet_period = 2
        self.since_last_bullet = -random.random() * self.bullet_period

        self.x, self.y = pos
        self.accel = 8
        self.max_speed = 12

        self.hp = 2

        self.shadow = pygame.image.load("shadow.png").convert()
        self.shadow.set_alpha(80)
        self.shadow.set_colorkey((255, 0, 0))

    def draw(self):
        camera = self.game.camera
        scale = camera.scale
        width = int(self.width * scale)
        x = int((self.x - camera.x) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_WIDTH//2)
        y = int((self.y - camera.y) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_HEIGHT//2)
        scaled = pygame.transform.scale(self.sprite.get_good_frame(), (width, width))

        soffset = 37
        shadow = pygame.transform.scale(self.shadow, (int(self.shadow.get_width() * scale), int(self.shadow.get_height() * scale)))
        self.game.screen.blit(shadow, (int(x + 5*scale), int(y + soffset*scale)))

        self.game.screen.blit(scaled, (x, y))

    def update(self, dt):
        super().update(dt)
        self.sprite.update(dt)

        thresh = 1
        if self.game.player.x < self.x - thresh and not self.sprite.active_animation == "IdleLeft":
            self.sprite.start_animation("IdleLeft")
        elif self.game.player.x > self.x + thresh and not self.sprite.active_animation == "IdleRight":
            self.sprite.start_animation("IdleRight")

    def get_hit_by(self, bullet):
        super().get_hit_by(bullet)
        if self.hp <= 0:
            for i in range(10):
                Feather(self.game, [self.x, self.y])
        else:
            for i in range(2):
                Feather(self.game, [self.x, self.y])
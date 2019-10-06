import pygame
import random
import math
from helpers import normalize, list_subtraction, list_addition, magnitude, dist_between, angle_vec
from bullet import BasicBullet
from splash import Splash
from sprite_tools import Sprite, SpriteSheet
from splash import BulletSpawn
from particle import Feather, Confettus, YouWin

class Enemy(object):

    def __init__(self, game):
        sprite_path = "enemy.png"
        self.game = game
        self.x = 2
        self.y = 5
        self.sprite = pygame.image.load(sprite_path)
        self.width = self.sprite.get_width()

        self.death_sound = pygame.mixer.Sound("bird.wav")
        self.death_sound.set_volume(0.25)

        self.deccel = 0.05
        self.velocity = [0, 0]
        self.accel = 10
        self.max_speed = 15

        self.bullet_period = 1
        self.since_last_bullet = -random.random() * self.bullet_period

        self.bullet_type = BasicBullet
        self.bullet_speed = 14
        self.recoil_speed = 5
        self.hit_radius = (self.width/self.game.c.TILE_SIZE)/2

        self.get_hit_sound = pygame.mixer.Sound("enemy_hit.wav")
        self.get_hit_sound.set_volume(0.15)

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
        self.get_hit_sound.play()
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
            self.death_sound.play()
            for i in range(20):
                Feather(self.game, [self.x, self.y])
        else:
            for i in range(3):
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
        self.since_last_bullet = random.random() * self.bullet_period - self.bullet_period/2

        self.x, self.y = pos
        self.accel = 8
        self.max_speed = 12

        self.hp = 2

        self.shadow = pygame.image.load("shadow.png").convert()
        self.shadow.set_alpha(80)
        self.shadow.set_colorkey((255, 0, 0))

        self.death_sound = pygame.mixer.Sound("chick.wav")
        self.death_sound.set_volume(0.25)

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
            self.death_sound.play()
            for i in range(10):
                Feather(self.game, [self.x, self.y])
        else:
            for i in range(3):
                Feather(self.game, [self.x, self.y])

class KingMouse(Enemy):

    def __init__(self, game):
        super().__init__(game)
        self.game = game

        self.x = 0
        self.y = -15.75

        self.sprite = Sprite(fps=8)
        self.sprite.add_animation({"Idle": SpriteSheet("king_mouse.png", (1, 1), 1)})
        self.sprite.start_animation("Idle")
        self.width = self.sprite.get_good_frame().get_width()

        self.hp = 30
        self.active = False

        self.accel = 9
        self.max_speed = 15
        self.firing_max_speed = 0.5
        self.original_max_speed = self.max_speed

        self.target_x = 0
        self.target_y = 0

        self.hit_radius = 1.25

        self.bullet_period = 0.1
        #self.bullet_speed = 15

        self.follow_player_mode = 0
        self.follow_position_mode = 1
        self.mode = self.follow_player_mode

        self.clip = 100
        self.clip_size = 100
        self.since_last_bullet = -2
        self.sprink_angle = 0
        self.sprink_angle_increase = math.pi * 2 / 32

        self.sprinkler_move = 0
        self.pulsar_move = 1
        self.next_move = self.random_move()

    def random_move(self):
        self.mode = self.follow_player_mode
        self.clip = 100
        return random.choice([self.sprinkler_move, self.pulsar_move])

    def check_bullet_behavior(self):
        if self.next_move == self.sprinkler_move:
            if self.clip and self.since_last_bullet > 0.06:
                self.shoot_bullet_in_direction(self.sprink_angle)
                self.shoot_bullet_in_direction(self.sprink_angle + math.pi)
                if self.clip > 50:
                    self.sprink_angle += self.sprink_angle_increase
                else:
                    self.sprink_angle -= self.sprink_angle_increase
                self.clip -= 1
            elif not self.clip:
                self.since_last_bullet = -3
                self.next_move = self.random_move()
        elif self.next_move == self.pulsar_move:
            self.mode = self.follow_position_mode
            self.target_x, self.target_y = (0, 0)
            if self.clip > 0 and self.since_last_bullet > 0.8:
                for i in range(48):
                    self.since_last_bullet = 0
                    self.shoot_bullet_in_direction(i/48 * math.pi * 2)
                self.clip -= 40
            elif self.clip <= 0:
                self.since_last_bullet = -3
                self.next_move = self.random_move()

    def shoot_bullet_in_direction(self, angle):
        self.since_last_bullet = 0
        velocity = angle_vec(angle)
        normalize(velocity, self.bullet_speed)
        push_vec = velocity[:]
        normalize(push_vec, -self.recoil_speed)
        self.push(*push_vec)
        new_bullet = self.bullet_type(self.game, (self.x, self.y), velocity)
        self.game.bullets.add(self.bullet_type(self.game, (self.x, self.y), velocity))
        BulletSpawn(self.game, (new_bullet.x, new_bullet.y))

    def activate(self):
        self.active = True

    def update(self, dt):
        self.sprite.update(dt)
        if 0 <= self.since_last_bullet < 0.25:
            self.max_speed = self.firing_max_speed
        else:
            self.max_speed = self.original_max_speed

        if not self.active:
            self.move(*self.velocity, dt)
            return

        self.since_last_bullet += dt
        self.deccelerate(dt)
        self.check_bullet_behavior()
        self.move_toward_player(dt)
        self.move_toward_position(dt)
        self.check_arena_bounds()
        self.move(*self.velocity, dt)
        self.check_bullet_collisions()
        self.check_enemy_collisions()

    def move_toward_position(self, dt):
        if self.mode == self.follow_position_mode:
            diff = list_subtraction([self.target_x, self.target_y], [self.x, self.y])
            normalize(diff, self.accel*dt)
            self.velocity = list_addition(self.velocity, diff)
            if magnitude(self.velocity) > self.max_speed:
                normalize(self.velocity, self.max_speed)

    def move_toward_player(self, dt):
        if self.mode == self.follow_player_mode:
            super().move_toward_player(dt)

    def draw(self):
        camera = self.game.camera
        scale = camera.scale
        width = int(self.width * scale)
        x = int((self.x - camera.x) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_WIDTH//2)
        y = int((self.y - camera.y) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_HEIGHT//2)
        scaled = pygame.transform.scale(self.sprite.get_good_frame(), (width, width))
        self.game.screen.blit(scaled, (x, y))

    def get_hit_by(self, bullet):
        super().get_hit_by(bullet)
        if self.hp <= 0:
            #self.death_sound.play()
            for i in range(70):
                Confettus(self.game, [self.x, self.y])
            YouWin(self.game, [self.x, self.y])
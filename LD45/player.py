import pygame
import math
from helpers import normalize, list_subtraction, magnitude, dist_between
from sprite_tools import SpriteSheet, Sprite
from splash import Splash, BulletSpawn
from particle import Feather


class Player(object):

    def __init__(self, game):
        self.game = game

        self.up_key = pygame.K_w
        self.down_key = pygame.K_s
        self.left_key = pygame.K_a
        self.right_key = pygame.K_d
        self.dodge_key = pygame.K_SPACE

        self.velocity = [0, 0]
        self.accel = 150
        self.deccel = 0.003
        self.max_speed = 7
        self.x = 0
        self.y = 0

        self.dodging = False
        self.dodge_sprite = pygame.Surface((32, 32))
        self.dodge_sprite.fill((255, 0, 0))
        self.since_last_dodge = 100
        self.dodge_time = 0.85
        self.dodge_slowdown_time = 0.2
        self.dodge_cooldown = 1.2
        self.min_dodge_threshold = 0.01
        self.dodge_speed = self.max_speed * 2.25

        self.blinking = False
        self.since_blink_start = 100
        self.blink_duration = 0.05

        self.stun_duration = 0.4
        self.since_stun_start = 100

        self.sprite = Sprite(fps=18)
        self.sprite_size = (48, 48)
        self.idle_right = SpriteSheet("player_facing_right.png", (4, 1), 4)
        self.idle_left = SpriteSheet("player_facing_right.png", (4, 1), 4)
        self.idle_left.reverse(1, 0)
        self.dodge_right = SpriteSheet("player_dodging_right.png", (8, 1), 8)
        self.dodge_left = SpriteSheet("player_dodging_right.png", (8, 1), 8)
        self.dodge_left.reverse(1, 0)
        self.run_right = SpriteSheet("player_running_right.png", (4, 1), 4)
        self.run_left = SpriteSheet("player_running_right.png", (4, 1), 4)
        self.run_left.reverse(1, 0)
        self.take_damage_right = SpriteSheet("player_damaged.png", (1, 1), 1)
        self.take_damage_left = SpriteSheet("player_damaged.png", (1, 1), 1)
        self.take_damage_left.reverse(1, 0)
        self.sprite.add_animation({"IdleRight": self.idle_right,
                                   "IdleLeft": self.idle_left,
                                   "DodgingRight": self.dodge_right,
                                   "DodgingLeft": self.dodge_left,
                                   "RunningRight": self.run_right,
                                   "RunningLeft": self.run_left,
                                   "DamageRight": self.take_damage_right,
                                   "DamageLeft": self.take_damage_left})
        self.sprite.start_animation("IdleRight")
        self.ammo_sprite = pygame.image.load("ammo.png")
        self.ammo_full_sprite = pygame.image.load("ammo_full.png")

        self.bullets_collected = []
        self.pocket_size = 6
        self.bullet_cooldown = 0.2
        self.since_last_bullet = 100

        self.default_hit_radius = 0.4
        self.hit_radius = self.default_hit_radius
        self.dodge_hit_radius = 0.65

        self.hp = 3
        self.max_hp = 3
        self.full_heart = pygame.image.load("full_heart.png")
        self.empty_heart = pygame.image.load("empty_heart.png")

        self.shadow = pygame.image.load("shadow.png").convert()
        self.shadow.set_alpha(80)
        self.shadow.set_colorkey((255, 0, 0))

        self.dead = False

        self.hit_by_bullet_sound = pygame.mixer.Sound("hit.wav")

    def die(self):
        for i in range(20):
            self.dead = True
            Feather(self.game, [self.x, self.y])

    def update(self, dt):
        if self.hp <= 0 and not self.dead:
            self.die()
        if self.dead: return
        self.since_stun_start += dt
        self.since_last_dodge += dt
        self.since_last_bullet += dt
        self.since_blink_start += dt
        self.deccelerate(dt)
        self.check_events(dt)
        self.move(*self.velocity, dt)
        self.check_arena_bounds()
        self.since_last_dodge += dt
        self.check_bullet_collisions()
        self.check_enemy_collisions()
        self.update_animation_mode(dt)
        self.update_velocity_if_dodging()


    def dodge(self):
        if self.since_last_dodge < self.dodge_cooldown or self.stunned():
            return
        if self.velocity[0]**2 + self.velocity[1]**2 > self.min_dodge_threshold**2:
            self.sprite.fps = 18
            self.dodging = True
            self.since_last_dodge = 0
            self.hit_radius = self.dodge_hit_radius
            if self.velocity[0] > 0:
                self.sprite.start_animation("DodgingRight")
            else:
                self.sprite.start_animation("DodgingLeft")

    def update_animation_mode(self, dt):
        self.sprite.update(dt)

        if not self.dodging and self.since_blink_start > self.blink_duration:
            self.sprite.fps = 12
            self.blinking = False
            thresh = 1.0
            if self.velocity[0] < 0 and magnitude(self.velocity) > thresh and self.sprite.active_animation != "RunningLeft":
                self.sprite.start_animation("RunningLeft")
            elif self.velocity[0] >= 0 and magnitude(self.velocity) > thresh and self.sprite.active_animation != "RunningRight":
                self.sprite.start_animation("RunningRight")
            elif self.velocity[0] < 0 and magnitude(self.velocity) <= thresh and self.sprite.active_animation != "IdleLeft":
                self.sprite.start_animation("IdleLeft")
            elif self.velocity[0] >= 0 and magnitude(self.velocity) <= thresh and self.sprite.active_animation != "IdleRight":
                self.sprite.start_animation("IdleRight")

        if self.blinking and not self.dodging and self.since_blink_start <= self.blink_duration:
            if not self.sprite.active_animation in ["DamageRight", "DamageLeft"]:
                if self.velocity[0] >= 0:
                    self.sprite.start_animation("DamageRight")
                else:
                    self.sprite.start_animation("DamageLeft")


    def end_dodge(self):
        self.dodging = False
        self.hit_radius = self.default_hit_radius
        self.sprite.start_animation("IdleRight")

    def deccelerate(self, dt):

        amt = self.deccel ** dt
        self.velocity[0] *= amt
        self.velocity[1] *= amt

    def draw(self):
        if self.dead: return
        camera = self.game.camera
        scale = camera.scale
        width = int(self.sprite_size[0] * scale)
        x = int((self.x - camera.x) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_WIDTH//2)
        y = int((self.y - camera.y) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_HEIGHT//2)
        img = self.sprite.get_good_frame()
        sprite = img#self.sprite if not self.dodging else self.dodge_sprite
        scaled = pygame.transform.scale(sprite, (width, width))

        soffset = 37
        shadow = pygame.transform.scale(self.shadow, (int(self.shadow.get_width() * scale), int(self.shadow.get_height() * scale)))
        self.game.screen.blit(shadow, (int(x + 5*scale), int(y + soffset*scale)))

        self.game.screen.blit(scaled, (x, y))

        if len(self.bullets_collected) < self.pocket_size:
            scaled_ammo = pygame.transform.scale(self.ammo_sprite, (int(self.ammo_sprite.get_width() * scale), int(self.ammo_sprite.get_height() * scale)))
        else:
            scaled_ammo = pygame.transform.scale(self.ammo_full_sprite, (int(self.ammo_sprite.get_width() * scale), int(self.ammo_sprite.get_height() * scale)))
        ammo_x = x - (self.game.c.TILE_SIZE*scale)//6
        ammo_y = y + (self.game.c.TILE_SIZE*scale)
        for item in self.bullets_collected:
            self.game.screen.blit(scaled_ammo, (ammo_x, ammo_y))
            ammo_y -= int(5 * scale)

        scaled_full_heart = pygame.transform.scale(self.full_heart, (int(self.full_heart.get_width() * scale), int(self.full_heart.get_height() * scale)))
        scaled_empty_heart = pygame.transform.scale(self.empty_heart, (int(self.empty_heart.get_width() * scale), int(self.empty_heart.get_height() * scale)))
        spacing = 2
        heart_x = x + int((self.game.c.TILE_SIZE*scale)*0.19)
        heart_y = y - (self.game.c.TILE_SIZE*scale)//2
        for i in range(self.max_hp):
            if i < self.hp:
                heart_to_draw = scaled_full_heart
            else:
                heart_to_draw = scaled_empty_heart
            self.game.screen.blit(heart_to_draw, (int(heart_x), int(heart_y)))
            heart_x += (self.full_heart.get_width() + spacing) * scale



    def move(self, x, y, dt):
        self.x += x * dt
        self.y += y * dt

    def stun(self, time=None):
        if not time:
            time = self.stun_duration
        self.since_stun_start = min(self.since_stun_start, -time)

    def stunned(self):
        return self.since_stun_start < 0

    def check_arena_bounds(self):
        if not self.game.c.in_arena_bounds([self.x, self.y]):
            direction = [self.x, self.y]
            normalize(direction, -3)
            self.push(*direction)
            self.stun(time=0.1)

    def check_events(self, dt):
        keys = pygame.key.get_pressed()
        mbuttons = pygame.mouse.get_pressed()

        if not self.dodging and not self.stunned() and not self.dead:
            if keys[self.up_key]:
                self.add_velocity(0, -1, dt)
            if keys[self.down_key]:
                self.add_velocity(0, 1, dt)
            if keys[self.left_key]:
                self.add_velocity(-1, 0, dt)
            if keys[self.right_key]:
                self.add_velocity(1, 0, dt)
            if mbuttons[0]:
                self.shoot_bullet()
        # if keys[pygame.K_UP]:
        #     self.game.camera.target_scale *= 2 ** dt
        # if keys[pygame.K_DOWN]:
        #     self.game.camera.target_scale *= 0.5 ** dt

    def update_velocity_if_dodging(self):
        if self.dodging:

            if self.since_last_dodge > self.dodge_time:
                self.end_dodge()

            r = self.velocity[0] ** 2 + self.velocity[1] ** 2
            if r == 0: return

            if self.since_last_dodge < self.dodge_slowdown_time:
                self.velocity[0] *= self.dodge_speed/(r**0.5)
                self.velocity[1] *= self.dodge_speed/(r**0.5)

    def add_velocity(self, x, y, dt):

        self.velocity[0] += x * dt * self.accel
        self.velocity[1] += y * dt * self.accel

        r = self.velocity[0] ** 2 + self.velocity[1] ** 2

        if r >= self.max_speed ** 2:
            self.velocity[0] *= (self.max_speed**2)/(r)
            self.velocity[1] *= (self.max_speed**2)/(r)

    def push(self, x, y):
        self.velocity[0] += x
        self.velocity[1] += y



    def colliding_enemy_bullets(self):
        ceb = set()
        for bullet in self.game.bullets:
            if not bullet.friendly:
                dist = (bullet.x - self.x)**2 + (bullet.y - self.y)**2
                if dist < (self.hit_radius + bullet.hit_radius)**2:
                    ceb.add(bullet)
        return ceb

    def check_bullet_collisions(self):
        ceb = self.colliding_enemy_bullets()
        pass_through = set()
        if self.dodging:
            for item in ceb:
                if len(self.bullets_collected) < self.pocket_size:
                    self.bullets_collected.append(item)
                    item.friendly = True
                    BulletSpawn(self.game, [item.x, item.y])
                else:
                    pass_through.add(item)

        else:
            for item in ceb:
                self.get_hit_by(item)

        self.game.bullets -= (ceb - pass_through)

    def check_enemy_collisions(self):
        for enemy in self.game.enemies:
            if dist_between(enemy, self) < self.hit_radius + enemy.hit_radius:
                self.get_hit_by_enemy(enemy)

    def get_hit_by_enemy(self, enemy):
        if not self.blinking and not self.dodging and not self.stunned():
            direction = list_subtraction([self.x, self.y], [enemy.x, enemy.y])
            normalize(direction, 20)
            self.push(*direction)
            self.blinking = True
            self.since_blink_start = 0
            Splash(self.game, [self.x, self.y])
            self.stun()

            self.hp -= 1


            self.game.camera.shake(0.25)

    def get_hit_by(self, bullet):
        self.hit_by_bullet_sound.play()
        self.blinking = True
        self.hp -= 1
        self.since_blink_start = 0
        Splash(self.game, [bullet.x, bullet.y])

        impact_amt = bullet.velocity[:]
        normalize(impact_amt, bullet.knockback)
        self.push(*impact_amt)

        self.game.camera.shake(0.25)

    def shoot_bullet(self):
        if self.bullets_collected and self.since_last_bullet > self.bullet_cooldown:
            direction = list_subtraction(self.game.camera.mpos_frame(), [self.x, self.y])
            normalize(direction, 25)
            new_bullet = self.bullets_collected.pop()
            new_bullet.since_shoot = 0
            new_bullet.velocity = direction
            new_bullet.x = self.x
            new_bullet.y = self.y - 0.25
            self.game.bullets.add(new_bullet)
            new_bullet.get_caught()
            self.since_last_bullet = 0
            BulletSpawn(self.game, [new_bullet.x, new_bullet.y])
            self.game.camera.shake(0.1)
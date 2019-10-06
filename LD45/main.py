import pygame
import sys
from map import Map
from camera import Camera
from player import Player
from enemy import Enemy, Bursty, Chick, KingMouse
from helpers import dist_between_lists
import time
from splash import BulletSpawn
from mouse import Mouse
from helpers import magnitude, list_subtraction, normalize
import math


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
            self.title()
            self.main()

    def title(self):
        self.reset_things()

        self.camera.focus_mode = True
        start_y = -12
        self.camera.x = 0
        self.camera.y = start_y
        self.camera.target_x = 0
        self.camera.target_y = start_y
        self.camera.true_x = 0
        self.camera.true_y = start_y

        shady_boi = pygame.Surface(self.c.WINDOW_SIZE).convert()
        shady_boi.fill((0, 0, 0))
        sb_alpha = 255
        sb_rate = 200

        end_loop = False

        then = time.time()
        time.sleep(0.001)

        while True:

            now = time.time()
            dt = now - then
            then = now

            sb_alpha = max(0, sb_alpha - sb_rate * dt)
            shady_boi.set_alpha(sb_alpha)

            events = self.check_for_quit_event()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        end_loop = True

            if end_loop:
                break

            yoff = math.sin(time.time() * 0.85) * 1.0
            self.camera.target_y = start_y + yoff
            self.camera.update(dt)

            self.map.draw()
            for mouse in self.mice:
                mouse.update(dt)
                mouse.draw()
            for king in self.king:
                king.update(dt)
                king.draw()
            self.screen.blit(shady_boi, (0, 0))
            pygame.display.flip()


    def reset_things(self):
        self.enemies = set()
        self.bullets = set()
        self.particles = set()
        self.mice = set()
        self.king = set()
        self.player = Player(self)

        self.reset_flag = False
        self.boss_fight_triggered = False

        for p in self.c.MOUSE_POSITIONS:
            self.mice.add(Mouse(self, p))

        self.wave_spawn_gap = 5
        self.last_hype = 0
        self.king.add(KingMouse(self))

        # self.waves = [[Chick(self, pos=self.c.CENTER_ARCH)]]

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
        rate = 150
        end_alpha = 150
        if self.player.dead and not self.reset_flag:
            da = dt * rate
            self.shade_alpha = min(self.shade_alpha + da, end_alpha)
            self.shade.set_alpha(int(self.shade_alpha))
        if self.reset_flag:
            da = dt * rate
            self.shade_alpha = min(self.shade_alpha + da, 255)
            self.shade.set_alpha(int(self.shade_alpha))

    def main(self):

        then = time.time()
        time.sleep(0.001)

        self.camera.focus_mode = False
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
                pass#print("FPS: %s" % (min(fpss)))

            # Do stuff
            dt = self.camera.update(dt)
            self.check_global_events(dt)
            if self.reset_flag and self.shade_alpha == 255:
                self.reset_flag = False
                break
            self.player.update(dt)
            self.update_shade(dt)

            # Draw stuff
            self.map.draw()
            for particle in self.particles:
                particle.update(dt)
                particle.draw()
            for enemy in self.enemies | self.king:
                enemy.update(dt)
                enemy.draw()
            self.player.draw()
            self.enemies -= self.enemies_to_destroy
            if len(self.enemies_to_destroy):
                self.last_hype = -2
            self.enemies_to_destroy = set()
            for mouse in self.mice:
                mouse.update(dt)
                mouse.draw()
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

    def boss_fight(self):
        self.boss_fight_triggered = True

        king = list(self.king)[0]
        self.player.stun(3)

        then = time.time()
        time.sleep(0.001)
        timer = 0
        self.camera.focus_mode = True
        self.camera.set_target_pos([king.x, king.y])
        while True:
            now = time.time()
            dt = now - then
            then = now

            timer += dt
            self.update_and_draw_things(dt)

            if magnitude(self.player.velocity) < 2:
                diff = list_subtraction([0, 5], [self.player.x, self.player.y])
                normalize(diff, 1)
                self.player.push(*diff)

            if timer > 2.5:
                king.velocity = [0, -((2.5 - timer)**2) * 50]

            if timer > 3.5:
                self.camera.focus_mode = False
                self.player.x = 0
                self.player.y = 5
                self.player.velocity = [0.01, 0]
                break

        timer = 0
        while True:
            now = time.time()
            dt = now - then
            then = now

            timer += dt
            self.update_and_draw_things(dt)
            if timer >= 0.5:
                break

        king.x = 0
        king.y = -30
        king.velocity = [0, 35]

        while True:
            now = time.time()
            dt = now - then
            then = now

            timer += dt
            self.update_and_draw_things(dt)
            if king.y > -0.5:
                king.y = -0.5
                king.velocity = [0, 0]
                self.camera.shake(1.2)
                break

        timer = 0
        while True:
            now = time.time()
            dt = now - then
            then = now

            timer += dt
            self.update_and_draw_things(dt)
            if timer >= 1:
                king.activate()
                break

        self.king = set()
        self.enemies = set([king])
        while True:
            now = time.time()
            dt = now - then
            then = now

            timer += dt
            self.update_and_draw_things(dt)

    def hype(self):
        return self.last_hype < 0

    def check_for_quit_event(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        return events

    def reset(self):
        self.reset_flag = True

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
                if event.key == pygame.K_r or event.key == pygame.K_RETURN:
                    self.reset()
                # if event.key == pygame.K_l:
                #     print("Mouse position: " + str(self.camera.mouse_to_frame(pygame.mouse.get_pos())))

        if not self.enemies:
            self.time_without_enemies += dt
        if self.time_without_enemies >= self.wave_spawn_gap:
            self.time_without_enemies = 0
            if len(self.waves):
                self.enemies |= set(self.waves.pop(0))
                self.player.hp = min(self.player.max_hp, self.player.hp + 1)
            elif not self.boss_fight_triggered:
                self.boss_fight()

        self.last_hype += dt

        if dt > 0.05:
            return 0.05

        return dt * self.camera.speed

    def update_and_draw_things(self, dt):
        # Do stuff
        dt = self.camera.update(dt)
        self.check_global_events(dt)
        self.player.update(dt)
        self.update_shade(dt)

        # Draw stuff
        self.map.draw()
        for particle in self.particles:
            particle.update(dt)
            particle.draw()
        for enemy in self.enemies | self.king:
            enemy.update(dt)
            enemy.draw()
        self.player.draw()
        self.enemies -= self.enemies_to_destroy
        if len(self.enemies_to_destroy):
            self.last_hype = -2
        self.enemies_to_destroy = set()
        for mouse in self.mice:
            mouse.update(dt)
            mouse.draw()
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

        self.MOUSE_POSITIONS = [[-10, -10.8], [-10.7, -10.3], [-14, -10.4], [-13, -11.3],
                                (-15.295831958878974, -6.679783591797069),
                                (-13.153556099845972, -7.660611852804626),
                                (-8.564313608079578, -11.569145797057713),
                                (-7.68811863423953, -12.00706751714673),
                                (-5.860311994992114, -12.753295979399422),
                                (-5.023878403422952, -13.106393435493882),
                                (-4.240823809603149, -13.28352039198839),
                                (-9.451655767632575, -13.257003888314694),
                                (-7.6597095623234885, -13.93723782701557),
                                (-8.521034537919807, -13.307632278408398),
                                (-4.8332897970339435, -14.675879406737524),
                                (-3.6093962062880625, -14.961841104917296),
                                (3.9258206310998283, -14.999332501590994),
                                (2.9231726568030516, -14.903834765944324),
                                (2.074958831097055, -13.6556613785289),
                                (3.4798536791137127, -13.371501361788486),
                                (6.686416452079296, -12.40756455234924),
                                (7.681045518750306, -11.911832282370052),
                                (8.899076437627958, -11.203248931133398),
                                (12.236534219343307, -7.259273010236049),
                                (11.962590892795902, -8.081947882599433),
                                (10.898573145451062, -9.491732583567506),
                                (10.407129710401716, -10.166310031010076),
                                (10.946663442260949, -12.256052395432784),
                                (13.041762356039747, -11.13321458005369),
                                (12.117030429800742, -10.291207652151531),
                                (13.903766639301686, -9.945129118016736),
                                (14.563525291592912, -8.546989037781325),
                                (14.924446880417594, -7.63328885538167),
                                (15.407632742773899, -6.938865189434376),
                                (13.536390235395956, -6.480127384397375)]
        self.MOUSE_POSITIONS = [(i[0], i[1] - 0.25) for i in self.MOUSE_POSITIONS]

    def in_arena_bounds(self, pos):
        x, y = pos
        thresh = 0.5
        if dist_between_lists(pos, self.CENTER_ARCH) < 2:
            return True
        return x**2/((self.MAJOR_RADIUS - thresh)**2) + y**2/((self.MINOR_RADIUS - thresh)**2) <= 1


if __name__ == "__main__":

    Game()
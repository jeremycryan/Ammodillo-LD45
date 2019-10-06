import pygame
import math

class Camera(object):

    def __init__(self, game):
        self.game = game
        self.scale = 1.0
        self.target_scale = 1.0
        self.true_x = 0
        self.true_y = 0
        self.target_x = 0
        self.target_y = 0
        self.x = 0
        self.y = 0
        self.speed = 1.0
        self.tightness = 0.7

        self.since_shake = 0
        self.shake_freq = 36
        self.shake_mag = 0

        self.focus_mode = False

    def mouse_to_frame(self, mpos):
        ppt = self.game.c.TILE_SIZE * self.scale
        mx = mpos[0] - self.game.c.WINDOW_WIDTH/2
        my = mpos[1] - self.game.c.WINDOW_HEIGHT/2
        mxn = mx / ppt + self.x
        myn = my / ppt + self.y
        return mxn, myn

    def mpos_frame(self):
        return self.mouse_to_frame(pygame.mouse.get_pos())

    def update(self, dt):
        self.since_shake += dt
        self.shake_mag *= 0.1**dt
        self.shake_mag = max(0, self.shake_mag - 0.8*dt)

        if not self.focus_mode:

            mx, my = self.mpos_frame()
            px, py = self.game.player.x, self.game.player.y
            tightness = self.tightness
            self.target_x = (mx*(1 - tightness) + px*tightness)
            self.target_y = (my*(1 - tightness) + py*tightness)

        dx = self.target_x - self.true_x
        dy = self.target_y - self.true_y

        p = 2
        self.true_x += p * dx * dt
        self.true_y += p * dy * dt

        xoff, yoff = self.shake_values()
        self.x = self.true_x + xoff
        self.y = self.true_y + yoff

        ds = self.target_scale - self.scale
        p = 5
        self.scale += ds * dt * p

        return dt * self.speed

    def shake_values(self):
        xoff = math.sin(self.since_shake * self.shake_freq) * self.shake_mag
        yoff = math.sin(self.since_shake * self.shake_freq) * self.shake_mag
        return xoff, yoff

    def shake(self, mag):
        self.shake_mag = max(self.shake_mag, mag)

    def is_zoomed(self):
        return abs(self.scale - 1.0) < 0.05

    def set_target_pos(self, pos):
        self.target_x, self.target_y = pos
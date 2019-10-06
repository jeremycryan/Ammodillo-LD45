import pygame


class Map(object):

    def __init__(self, game):

        self.game = game
        width = 1
        height = 1
        self.tiles = [[Tile(self.game, (j, i)) for i in range(width)] for j in range(height)]

    def draw(self):
        for y, row in enumerate(self.tiles):
            for x, item in enumerate(row):
                item.draw(self.game.camera)


class Tile(object):

    def __init__(self, game, pos):
        path = "colosseum.png"
        self.game = game
        self.sprite = pygame.image.load(path)
        self.w, self.h = self.sprite.get_width(), self.sprite.get_height()
        self.y = -1.5
        self.x = 0
        #self.width = self.game.c.TILE_SIZE

    def draw(self, camera):
        scale = camera.scale
        width = int(self.w * scale)
        height = int(self.h * scale)
        x = int((self.x - camera.x) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_WIDTH//2)
        y = int((self.y - camera.y) * scale * self.game.c.TILE_SIZE - width/2 + self.game.c.WINDOW_HEIGHT//2)
        if x + width < 0 or y + width < 0 or x > self.game.c.WINDOW_WIDTH or y > self.game.c.WINDOW_HEIGHT:
            return
        scaled = pygame.transform.scale(self.sprite, (width, height))
        self.game.screen.blit(scaled, (x, y))

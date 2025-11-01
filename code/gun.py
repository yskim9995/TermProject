from pico2d import load_image
import math
import DEFINES
from character import Player

class Gun:
    def __init__(self,x,y , Player):
        self.x = x
        self.y = y
        self.player = Player

        self.image = load_image('resource/Sprites/Guns/AK47.png')

        self.width = 0
        self.height = 0

        self.width = 32
        self.height = 16

        self.scale = [1.0, 1.0]
        self.rotation = 0.0

    def draw(self):
        self.image.rotate_draw(self.rotation, self.x, self.y, self.width*self.scale[0], self.height*self.scale[1]);

    def update(self):

        if self.player.face_dir == - 1:
            # 왼쪽
            self.x = self.player.x - 32
        else:
            self.x = self.player.x + 48

        self.y = self.player.y
        pos = [DEFINES.mouseX - self.x, DEFINES.mouseY - self.y]
        rot = math.atan2(pos[1], pos[0])
        self.rotation = rot

        degree = rot * (180.0 / math.pi) + 90.0
        if 0.0 <= degree <= 180.0:
            self.scale[1] = 3
        else:
            self.scale[1] = -3

        pass

from pico2d import *
import DEFINES
class Background:
    def __init__(self):
        self.images = [load_image('resource/Sprites/Jungle Asset Pack/parallax background/plx-1.png'),
                       load_image('resource/Sprites/Jungle Asset Pack/parallax background/plx-2.png'),
                       load_image('resource/Sprites/Jungle Asset Pack/parallax background/plx-3.png'),
                       load_image('resource/Sprites/Jungle Asset Pack/parallax background/plx-4.png'),
                       load_image('resource/Sprites/Jungle Asset Pack/parallax background/plx-5.png')]

    def update(self,dt):
        pass

    def draw(self):
        for i in range(5):
            self.images[i].draw(DEFINES.SCW / 2, DEFINES.SCH / 2 , DEFINES.SCW, DEFINES.SCH)

        # draw_rectangle(*self.get_bb())# *가 튜플을 풀어 헤칠 수 있음 원래 4개의 튜플이 1개로 오지만 이걸로 4개 각각으로 온다.

    def get_bb(self):
        pass
    def handle_collision(self, group, other):
        # if group == 'grass:ball':
        pass

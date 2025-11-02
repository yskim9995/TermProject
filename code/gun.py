from pico2d import load_image, get_time
import math
import DEFINES
from Bullet import Bullet
import time
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

        self.fire_rate = 0.15
        self._last_fire = 0.0

    def try_fire(self, world_layer):
        # 4-1. 연사 속도 체크
        now = get_time()
        if now - self._last_fire < self.fire_rate:
            return  # 쿨타임 중이면 발사 안 함

        # 4-2. 쿨타임 초기화
        self._last_fire = now

        # 4-3. 총알이 나갈 각도 계산
        angle = self._calc_angle_to_mouse()

        # 4-4. 총알 생성 위치 (총구 위치)
        # 총의 중심에서 각도 방향으로 20픽셀 떨어진 곳(총구)에서 발사
        muzzle_offset = 20.0
        bx = self.x + math.cos(angle) * muzzle_offset
        by = self.y + math.sin(angle) * muzzle_offset

        # 4-5. 총알 생성 및 월드에 추가
        bullet = Bullet(bx, by, angle, owner=self.player, damage=10)
        world_layer.append(bullet)

    # 🌟 5. 마우스까지의 각도를 계산하는 내부 함수
    def _calc_angle_to_mouse(self):
        # 총의 현재 위치에서 마우스 위치까지의 각도(radian) 계산
        dx = DEFINES.mouseX - self.x
        dy = DEFINES.mouseY - self.y
        return math.atan2(dy, dx)

    def draw(self):
        self.image.rotate_draw(self.rotation, self.x, self.y, self.width*self.scale[0], self.height*self.scale[1]);

    def update(self,dt):

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
            self.scale[1] = 2
        else:
            self.scale[1] = -2
        pass

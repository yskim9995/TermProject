from pico2d import load_image, get_time
import math
import DEFINES
from Bullet import Bullet
import time
import game_world
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

        self.visible = True

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
        muzzle_offset = 35.0
        bx = self.x + math.cos(angle) * muzzle_offset
        by = self.y + math.sin(angle) * muzzle_offset

        bullet = Bullet(bx, by, angle, owner=self.player, damage=10)
        game_world.add_object(bullet , 1)
        game_world.addcollide_pairs('enemy:bullet', None, bullet)
        effect = ShootEffect(bx, by, self.rotation, self.scale[1],self.player)
        game_world.add_object(effect, 2)

    # 🌟 5. 마우스까지의 각도를 계산하는 내부 함수
    def _calc_angle_to_mouse(self):
        # 총의 현재 위치에서 마우스 위치까지의 각도(radian) 계산
        dx = DEFINES.mouseX - self.x
        dy = DEFINES.mouseY - self.y
        return math.atan2(dy, dx)

    def draw(self):
        if self.visible :
            self.image.rotate_draw(self.rotation, self.x, self.y, self.width*self.scale[0], self.height*self.scale[1]);

    def update(self,dt):
        self.visible = DEFINES.Gunvisible
        if not self.visible:
            pass
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


class ShootEffect:

    images = None
    LIFETIME = 0.1  # 이펙트가 지속되는 시간 (0.1초)

    def __init__(self, x, y, angle, scale_y, player):
        self.x = x
        self.y = y
        self.angle = angle  # 총의 회전값 (radian)
        self.scale_y = scale_y  # 총의 Y 스케일 (뒤집기용)
        self.spawn_time = get_time()
        self.player = player  #
        self.frame = 0
        # 이미지를 한 번만 로드
        if ShootEffect.images is None:
            try:
                ShootEffect.images = [
                    load_image('resource/Sprites/GunsPack/effect/gunfire_1.png'),
                    load_image('resource/Sprites/GunsPack/effect/gunfire_2.png'),
                    load_image('resource/Sprites/GunsPack/effect/gunfire_3.png')
                ]
            except Exception as e:
                print(f"ShootEffect 이미지 로드 실패: {e}")

        #  총 프레임 수와 각 프레임당 지속시간 계산
        self.total_frames = len(ShootEffect.images)
        self.time_per_frame = ShootEffect.LIFETIME / self.total_frames

    def update(self, dt):
        time_elapsed = get_time() - self.spawn_time

        # 🌟 5. 수명이 다하면 제거
        if time_elapsed > ShootEffect.LIFETIME:
            game_world.remove_object(self)
            return  # 제거된 후에는 아래 코드를 실행하지 않음

        # 🌟 6. 경과 시간에 맞춰 현재 프레임(0, 1, 2)을 계산
        self.frame = int(time_elapsed / self.time_per_frame)

        # 프레임 인덱스가 2를 넘어가지 않도록 방지
        if self.frame >= self.total_frames:
            self.frame = self.total_frames - 1

    def draw(self):
        # 🌟 7. 이펙트 이미지의 원본 크기 (필요시 수정)
        EFFECT_WIDTH = 32
        EFFECT_HEIGHT = 32

        # 🌟 8. update에서 계산된 self.frame에 맞는 이미지를 선택
        image_to_draw = ShootEffect.images[self.frame]

        # 🌟 9. 총(Gun)과 동일한 방식으로 그림
        # self.angle: 총의 회전값
        # self.x, self.y: 총구의 위치
        # self.scale_y: 총의 Y축 스케일 (위/아래 뒤집기)
        image_to_draw.rotate_draw(
            self.angle,
            self.x, self.y,
            EFFECT_WIDTH,
            EFFECT_HEIGHT * self.scale_y
        )

    # (get_bb, handle_collision은 수정할 필요 없음)
    def get_bb(self):
        return 0, 0, 0, 0

    def handle_collision(self, group, other):
        pass

from pico2d import load_image, get_time
import math
import DEFINES
from Bullet import Bullet
import game_world
import server


class Gun:
    def __init__(self, x, y, player):
        self.x = x
        self.y = y
        self.player = player

        try:
            self.image = load_image('resource/Sprites/Guns/AK47.png')
        except:
            self.image = None

        self.width = 32
        self.height = 16
        self.scale = [1.0, 1.0]
        self.rotation = 0.0

        self.fire_rate = 0.15
        self._last_fire = 0.0

    def try_fire(self, world_layer):
        now = get_time()
        if now - self._last_fire < self.fire_rate:
            return

        self._last_fire = now
        angle = self._calc_angle_to_mouse()

        muzzle_offset = 35.0
        bx = self.x + math.cos(angle) * muzzle_offset
        by = self.y + math.sin(angle) * muzzle_offset

        # 총알 생성
        bullet = Bullet(bx, by, angle, owner=self.player, damage=10)
        game_world.add_object(bullet, 1)
        game_world.addcollide_pairs('enemy:bullet', None, bullet)

        # 🌟 이펙트 생성
        effect = ShootEffect(bx, by, self.rotation, self.scale[1], self.player)
        game_world.add_object(effect, 2)

    def _calc_angle_to_mouse(self):
        dx = DEFINES.mouseX - self.x
        dy = DEFINES.mouseY - self.y
        return math.atan2(dy, dx)

    def update(self, dt):
        # 1. 월드 좌표 갱신 (이건 그대로 둠)
        # 플레이어(월드) 위치를 따라감
        if self.player.face_dir == -1:
            self.x = self.player.x - 32
        else:
            self.x = self.player.x + 48
        self.y = self.player.y

        # 2. 각도 계산용 화면 좌표 가져오기 🌟
        # 복잡한 식 대신 함수 호출 한 번이면 끝!
        sx, sy = server.world_to_screen(self.x, self.y)

        # 마우스(화면) - 총(화면) 비교
        pos = [DEFINES.mouseX - sx, DEFINES.mouseY - sy]
        self.rotation = math.atan2(pos[1], pos[0])

        # 상하 반전 로직 (기존 유지)
        degree = self.rotation * (180.0 / math.pi) + 90.0
        if 0.0 <= degree <= 180.0:
            self.scale[1] = 2
        else:
            self.scale[1] = -2

    def draw(self):
        if self.image:
            sx, sy = server.world_to_screen(self.x, self.y)

            self.image.rotate_draw(self.rotation, sx, sy,
                                   selfd.width * self.scale[0],
                                   self.height * self.scale[1])

# 🌟🌟 [수정된 클래스] 여기서 에러가 났었습니다! 🌟🌟
class ShootEffect:
    # 🌟 여러 장의 이미지를 쓰므로 이름이 'images' (복수형) 입니다.
    images = None
    LIFETIME = 0.1

    def __init__(self, x, y, angle, scale_y, player):
        self.x, self.y = x, y
        self.angle = angle
        self.scale_y = scale_y
        self.spawn_time = get_time()
        self.frame = 0

        # 이미지가 로드 안 되어 있으면 로드
        if ShootEffect.images is None:
            ShootEffect.images = [
                load_image('resource/Sprites/GunsPack/effect/gunfire_1.png'),
                load_image('resource/Sprites/GunsPack/effect/gunfire_2.png'),
                load_image('resource/Sprites/GunsPack/effect/gunfire_3.png')
            ]

        self.total_frames = len(ShootEffect.images)
        self.time_per_frame = ShootEffect.LIFETIME / self.total_frames

    def update(self, dt):
        time_elapsed = get_time() - self.spawn_time
        if time_elapsed > ShootEffect.LIFETIME:
            game_world.remove_object(self)
            return

        self.frame = int(time_elapsed / self.time_per_frame)
        if self.frame >= self.total_frames:
            self.frame = self.total_frames - 1

    def draw(self):
        # 🌟🌟 [여기가 핵심] self.image가 아니라 ShootEffect.images[...] 를 써야 합니다! 🌟🌟
        img = ShootEffect.images[self.frame]

        img.rotate_draw(self.angle, self.x, self.y, 32, 32 * self.scale_y)

    def get_bb(self):
        return 0, 0, 0, 0

    def handle_collision(self, group, other):
        pass
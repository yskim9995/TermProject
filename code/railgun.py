from pico2d import *
import math
import DEFINES
import game_world
import game_framework


# from character import Player  <-- 삭제함 (순환 참조 방지)

class Railgun:
    def __init__(self, x, y, player):
        self.x = x
        self.y = y
        self.player = player  # 캐릭터 정보 저장

        self.image = load_image('resource/Sprites/Guns/M24.png')

        self.width = 32
        self.height = 16
        self.scale = [1.0, 1.0]
        self.rotation = 0.0

        # 🌟 [레일건 전용 변수]
        self.is_charging = False
        self.charge_start_time = 0.0
        self.charge_duration = 3.0
        self.charging_effect = None
        self.visible = True
        self.muzzle_x = 0
        self.muzzle_y = 0

    # 🌟 [수정] dt 대신 x, y를 받도록 변경 (Character.py에서 x, y를 줌)
    def update(self, x, y):
        self.visible = DEFINES.Gunvisible
        if not self.visible:
            return

        # 1. 위치 업데이트
        self.x = x
        self.y = y

        # 2. 플레이어 방향에 따른 위치 보정
        if self.player.face_dir == -1:  # 왼쪽
            self.x = self.player.x - 32
        else:  # 오른쪽
            self.x = self.player.x + 48

        self.y = self.player.y

        # 3. 마우스 바라보기 (회전)
        pos = [DEFINES.mouseX - self.x, DEFINES.mouseY - self.y]
        self.rotation = math.atan2(pos[1], pos[0])

        degree = self.rotation * (180.0 / math.pi) + 90.0
        if 0.0 <= degree <= 180.0:
            self.scale[1] = 2  # 정방향
        else:
            self.scale[1] = -2  # 뒤집힘

        # 4. 총구 위치 계산
        muzzle_offset = 35.0
        self.muzzle_x = self.x + math.cos(self.rotation) * muzzle_offset
        self.muzzle_y = self.y + math.sin(self.rotation) * muzzle_offset

        # 5. 차징 로직
        if self.is_charging:
            if self.charging_effect is None:
                self.charging_effect = ChargingEffect(self)
                game_world.add_object(self.charging_effect, 2)

            elapsed_time = get_time() - self.charge_start_time
            if elapsed_time >= self.charge_duration:
                self.fire()
                self.stop_charging()

    def draw(self):
        if self.visible:
            self.image.rotate_draw(self.rotation, self.x, self.y,
                                   self.width * self.scale[0], self.height * self.scale[1])

    def handle_event(self, event):
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            self.start_charging()
        elif event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_LEFT:
            self.stop_charging()

    def start_charging(self):
        if not self.is_charging:
            self.is_charging = True
            self.charge_start_time = get_time()
            print("Charging Started...")

    def stop_charging(self):
        if self.is_charging:
            self.is_charging = False
            if self.charging_effect:
                game_world.remove_object(self.charging_effect)
                self.charging_effect = None
            print("Charging Reset")

    def fire(self):
        print(">>> RAILGUN FIRE! <<<")
        beam = RailBeam(self.muzzle_x, self.muzzle_y, self.rotation, self.player)
        game_world.add_object(beam, 1)
        game_world.addcollide_pairs('enemy:bullet', None, beam)


class ChargingEffect:
    def __init__(self, gun):
        self.gun = gun
        # 이미지가 없으면 오류가 나므로 예외처리 혹은 있는 이미지 사용
        try:
            self.image = load_image('resource/Sprites/GunsPack/effect/gunfire_1.png')
        except:
            self.image = None  # 이미지가 없으면 안 그림

        self.start_time = get_time()
        self.scale = 0.5
        self.rotation = 0

    def update(self, dt):
        self.x = self.gun.muzzle_x
        self.y = self.gun.muzzle_y
        elapsed = get_time() - self.start_time
        self.scale = 0.5 + elapsed * 0.5
        self.rotation = elapsed * 10

    def draw(self):
        if self.image:
            self.image.rotate_draw(self.rotation, self.x, self.y, 30 * self.scale, 30 * self.scale)
        else:
            draw_rectangle(self.x - 5, self.y - 5, self.x + 5, self.y + 5)  # 이미지 없으면 사각형

    def get_bb(self):
        return 0, 0, 0, 0


class RailBeam:
    def __init__(self, x, y, angle, owner):
        self.x, self.y = x, y
        self.angle = angle
        self.owner = owner
        self.spawn_time = get_time()
        self.lifetime = 0.2
        self.length = 1000
        self.end_x = self.x + math.cos(self.angle) * self.length
        self.end_y = self.y + math.sin(self.angle) * self.length

    def update(self, dt):
        if get_time() - self.spawn_time > self.lifetime:
            game_world.remove_object(self)

    def draw(self):
        # 레이저 그리기 (노란색 선)
        draw_line(self.x, self.y, self.end_x, self.end_y)

    def get_bb(self):
        # 충돌 처리를 위한 BB (일단 임시로 0)
        return 0, 0, 0, 0

    def handle_collision(self, group, other):
        pass
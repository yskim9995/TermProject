from pico2d import *
import math
import DEFINES
import game_world


class Railgun:
    def __init__(self, x, y, player):
        self.player = player
        self.x, self.y = x, y

        # 이미지 로드 (없으면 예외처리)
        try:
            self.image = load_image('resource/Sprites/Guns/M24.png')
        except:
            print("Railgun Image Load Failed")
            self.image = None  # 혹은 기본 이미지

        self.width = 32
        self.height = 16
        self.scale = [1.0, 1.0]
        self.rotation = 0.0

        # 차징 관련
        self.is_charging = False
        self.charge_start_time = 0.0
        self.charge_duration = 1.0  # 1초 차징이면 발사 (테스트용)
        self.charging_effect = None

        # 총구 위치
        self.muzzle_x = 0
        self.muzzle_y = 0

    def update(self, dt):
        # 현재 무기가 아니면 로직 수행 X
        if DEFINES.current_weapon_mode != DEFINES.WEAPON_RAILGUN:
            # 차징 중에 무기를 바꾸면 차징 취소
            if self.is_charging:
                self.stop_charging()
            return

        # 1. 위치 및 회전 동기화
        if self.player.face_dir == -1:
            self.x = self.player.x - 32
            self.scale[1] = -2  # 상하 반전
        else:
            self.x = self.player.x + 48
            self.scale[1] = 2

        self.y = self.player.y

        # 마우스 바라보기
        dx = DEFINES.mouseX - self.x
        dy = DEFINES.mouseY - self.y
        self.rotation = math.atan2(dy, dx)

        # 총구 위치 계산
        muzzle_offset = 35.0
        self.muzzle_x = self.x + math.cos(self.rotation) * muzzle_offset
        self.muzzle_y = self.y + math.sin(self.rotation) * muzzle_offset

        # 2. 차징 로직
        if self.is_charging:
            # 이펙트가 없으면 생성
            if self.charging_effect is None:
                self.charging_effect = ChargingEffect(self)
                game_world.add_object(self.charging_effect, 2)

            # 차징 시간 체크
            elapsed = get_time() - self.charge_start_time
            if elapsed >= self.charge_duration:
                self.fire()
                self.stop_charging()

    def draw(self):
        # 현재 무기일 때만 그림
        if DEFINES.current_weapon_mode == DEFINES.WEAPON_RAILGUN and self.image:
            self.image.rotate_draw(self.rotation, self.x, self.y,
                                   self.width * self.scale[0], self.height * self.scale[1])

    def handle_event(self, event):
        # 마우스 누르면 차징 시작
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            self.start_charging()

        # 마우스 떼면 차징 취소
        elif event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_LEFT:
            self.stop_charging()

    def start_charging(self):
        if not self.is_charging:
            self.is_charging = True
            self.charge_start_time = get_time()
            print("Railgun Charging...")

    def stop_charging(self):
        self.is_charging = False
        if self.charging_effect:
            game_world.remove_object(self.charging_effect)
            self.charging_effect = None
            print("Railgun Charge Cancelled")

    def fire(self):
        print(">>> RAILGUN BEAM FIRED! <<<")
        # 빔 생성
        beam = RailBeam(self.muzzle_x, self.muzzle_y, self.rotation, self.player)
        game_world.add_object(beam, 1)
        # 적 충돌 처리 등록
        game_world.addcollide_pairs('enemy:bullet', None, beam)


class ChargingEffect:
    def __init__(self, gun):
        self.gun = gun
        self.image = load_image('resource/Sprites/GunsPack/effect/laygun_a1.png')
        self.start_time = get_time()
        self.scale = 0.5
        self.rotation = 0

    def update(self, dt):
        self.x, self.y = self.gun.muzzle_x, self.gun.muzzle_y
        elapsed = get_time() - self.start_time
        # 점점 커지고 빠르게 회전
        self.scale = 0.5 + elapsed * 1.5
        self.rotation += dt * 10

    def draw(self):
        self.image.rotate_draw(self.rotation, self.x, self.y, 30 * self.scale, 30 * self.scale)

    def get_bb(self): return 0, 0, 0, 0


class RailBeam:
    def __init__(self, x, y, angle, owner):
        self.x, self.y = x, y
        self.angle = angle
        self.owner = owner
        self.damage = 100  # 데미지 설정
        self.spawn_time = get_time()
        self.lifetime = 0.15  # 빔 유지 시간
        self.length = 1600  # 사거리

        self.end_x = self.x + math.cos(self.angle) * self.length
        self.end_y = self.y + math.sin(self.angle) * self.length

    def update(self, dt):
        if get_time() - self.spawn_time > self.lifetime:
            game_world.remove_object(self)

    def draw(self):
        # 빔 그리기 (노란색 선)
        draw_line(self.x, self.y, self.end_x, self.end_y)
        # 충돌 박스 디버그
        if DEFINES.bbvisible:
            draw_rectangle(*self.get_bb())

    def get_bb(self):
        # 🌟 임시 충돌 박스 (빔의 끝부분이 아니라 전체를 덮어야 하는데,
        # AABB 충돌로는 사선 충돌이 어렵습니다.
        # 일단 플레이어 주변과 타겟 지점 일부를 커버하도록 설정)
        return min(self.x, self.end_x) - 10, min(self.y, self.end_y) - 10, \
               max(self.x, self.end_x) + 10, max(self.y, self.end_y) + 10

    def handle_collision(self, group, other):
        pass
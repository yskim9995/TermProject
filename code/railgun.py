from pico2d import *
import math
import DEFINES
import game_world


# -------------------------------------------------------------------------
# 1. 레일건 무기 클래스
# -------------------------------------------------------------------------
class Railgun:
    def __init__(self, x, y, player):
        self.player = player
        self.x, self.y = x, y

        # 레일건 본체 이미지
        try:
            self.image = load_image('resource/Sprites/Guns/M24.png')
        except:
            self.image = None

        self.width = 32
        self.height = 16
        self.scale = [1.0, 1.0]
        self.rotation = 0.0

        # 차징 관련
        self.is_charging = False
        self.charge_start_time = 0.0
        self.charge_duration = 1.0  # 1초 모으면 발사
        self.charging_effect = None

        # 총구 위치
        self.muzzle_x = 0
        self.muzzle_y = 0

    def update(self, dt):
        if DEFINES.current_weapon_mode != DEFINES.WEAPON_RAILGUN:
            if self.is_charging: self.stop_charging()
            return

        # 1. 위치 동기화
        if self.player.face_dir == -1:
            self.x = self.player.x - 32
            self.scale[1] = -2
        else:
            self.x = self.player.x + 48
            self.scale[1] = 2

        self.y = self.player.y

        # 2. 회전 계산
        dx = DEFINES.mouseX - self.x
        dy = DEFINES.mouseY - self.y
        self.rotation = math.atan2(dy, dx)

        # 3. 총구 위치 계산
        muzzle_offset = 35.0
        self.muzzle_x = self.x + math.cos(self.rotation) * muzzle_offset
        self.muzzle_y = self.y + math.sin(self.rotation) * muzzle_offset

        # 4. 차징 로직
        if self.is_charging:
            if self.charging_effect is None:
                self.charging_effect = ChargingEffect(self)
                game_world.add_object(self.charging_effect, 2)

            elapsed = get_time() - self.charge_start_time
            if elapsed >= self.charge_duration:
                self.fire()
                self.stop_charging()

    def draw(self):
        if DEFINES.current_weapon_mode == DEFINES.WEAPON_RAILGUN and self.image:
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

    def stop_charging(self):
        self.is_charging = False
        if self.charging_effect:
            game_world.remove_object(self.charging_effect)
            self.charging_effect = None

    def fire(self):
        # 빔 발사
        beam = RailBeam(self.muzzle_x, self.muzzle_y, self.rotation, self.player)
        game_world.add_object(beam, 2)  # 이펙트 레이어(2) 또는 탄환 레이어(1)

        # 충돌 등록 (적과 충돌 시 RailBeam.handle_collision 호출됨)
        game_world.addcollide_pairs('enemy:bullet', None, beam)


# -------------------------------------------------------------------------
# 2. 차징 이펙트 (8프레임 애니메이션)
# -------------------------------------------------------------------------
class ChargingEffect:
    images = None

    def __init__(self, gun):
        self.gun = gun
        self.frame = 0
        self.frame_time = 0.0

        # 🌟 8장 이미지 로드 (경로를 본인 파일명에 맞게 수정하세요!)
        if ChargingEffect.images is None:
            ChargingEffect.images = []
            for i in range(1, 9):  # 1~8번 이미지
                # 예: resource/Sprites/Railgun/Charge_1.png ...
                # 파일명이 다르다면 직접 수정 필요
                try:
                    ChargingEffect.images.append(load_image(f'resource/Sprites/GunsPack/effect/laygun_a{i}.png'))
                except:
                    print('없음')
                    pass

    def update(self, dt):
        # 위치는 총구 계속 따라다님
        self.x, self.y = self.gun.muzzle_x, self.gun.muzzle_y

        # 애니메이션 속도 (0.1초마다 프레임 변경)
        self.frame_time += dt
        if self.frame_time >= 0.1:
            self.frame = (self.frame + 1) % 8  # 0~7 반복
            self.frame_time = 0

    def draw(self):
        if ChargingEffect.images:
            # 총구 위치에 그리기
            # 회전이 필요하면 rotate_draw 사용, 아니면 그냥 draw
            ChargingEffect.images[self.frame].draw(self.x, self.y)

    def get_bb(self):
        return 0, 0, 0, 0


# -------------------------------------------------------------------------
# 3. 레일건 빔 (2프레임 애니메이션 + 긴 사거리)
# -------------------------------------------------------------------------
#RailBeam.images.append(load_image(f'resource/Sprites/GunsPack/effect/laygun_c{i}.png'))
class RailBeam:
    images = None

    def __init__(self, x, y, angle, owner, damage=100):
        self.x, self.y = x, y
        self.angle = angle  # 🌟 주의: 반드시 '라디안' 값이어야 함 (math.atan2 결과 그대로)
        self.owner = owner
        self.damage = damage
        self.spawn_time = get_time()
        self.lifetime = 0.2
        self.length = 1600  # 사거리
        self.thickness = 50  # 🌟 두께 (그림 크기랑 맞춤)

        self.frame = 0
        self.frame_time = 0.0

        if RailBeam.images is None:
            RailBeam.images = []
            for i in range(1, 3):
                try:
                    RailBeam.images.append(load_image(f'resource/Sprites/GunsPack/effect/laygun_c{i}.png'))
                except:
                    pass

        # 🌟 [최적화] 레일건은 움직이지 않으므로 생성될 때 딱 한 번만 좌표 계산
        self.calculate_position()

    def calculate_position(self):
        # self.angle은 이미 라디안이라고 가정합니다. (math.radians 삭제)

        # 1. 끝점 계산
        self.end_x = self.x + self.length * math.cos(self.angle)
        self.end_y = self.y + self.length * math.sin(self.angle)

        # 2. 중심점 계산
        self.cx = (self.x + self.end_x) / 2
        self.cy = (self.y + self.end_y) / 2

    def update(self, dt):
        if get_time() - self.spawn_time > self.lifetime:
            game_world.remove_object(self)
            return

        self.frame_time += dt
        if self.frame_time >= 0.05:
            self.frame = (self.frame + 1) % 2
            self.frame_time = 0

    def draw(self):
        if not RailBeam.images:
            return

        img = RailBeam.images[self.frame]

        # 🌟 라디안 변환 없이 self.angle 그대로 사용
        # (이미지가 가로로 긴 형태라고 가정)
        img.rotate_draw(self.angle, self.cx, self.cy, self.length, self.thickness)

        # 디버그: 빨간 박스 확인 (이제 그림과 정확히 일치할 것임)
        draw_rectangle(*self.get_bb())

    def get_bb(self):
        # 충돌 박스 크기
        box_width = self.length
        box_height = self.thickness

        # 🌟 여기서도 라디안 변환 없이 그대로 사용
        rad = self.angle

        # 회전된 사각형을 감싸는 큰 AABB 박스 크기 계산
        new_w = abs(box_width * math.cos(rad)) + abs(box_height * math.sin(rad))
        new_h = abs(box_width * math.sin(rad)) + abs(box_height * math.cos(rad))

        return (self.cx - new_w / 2, self.cy - new_h / 2,
                self.cx + new_w / 2, self.cy + new_h / 2)

    # 🌟🌟 [핵심] 2차 정밀 검사 🌟🌟
    # get_bb가 True일 때만 호출해서 진짜 맞았는지 확인하는 함수
    def is_valid_hit(self, target):
        tx, ty = target.x, target.y
        x1, y1 = self.x, self.y
        x2, y2 = self.end_x, self.end_y

        line_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if line_len_sq == 0: return False

        t = ((tx - x1) * (x2 - x1) + (ty - y1) * (y2 - y1)) / line_len_sq
        t = max(0, min(1, t))

        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)

        distance = math.sqrt((tx - closest_x) ** 2 + (ty - closest_y) ** 2)

        # 판정 범위: (레이저 두께 절반) + (적 반지름)
        # 예: 레이저두께 50 -> 절반 25, 적 반지름 20 -> 합 45
        HIT_THRESHOLD = (self.thickness / 2) + 20

        return distance <= HIT_THRESHOLD

    def handle_collision(self, group, other):
        if group == 'enemy:bullet':
            # 여기서 바로 처리하지 않고, main_state 등에서 is_valid_hit를 호출해서 처리해야 함
            pass
# -------------------------------------------------------------------------
# 4. 타격 이펙트 (12프레임, 적 위치 생성)
# -------------------------------------------------------------------------
class RailHitEffect:
    images = None

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.frame = 0
        self.frame_time = 0.0

        # 🌟 12장 이미지 로드
        if RailHitEffect.images is None:
            RailHitEffect.images = []
            for i in range(1, 13):  # 1~12번
                try:
                    RailHitEffect.images.append(load_image(f'resource/Sprites/GunsPack/effect/laygun_b{i}.png'))
                except:
                    pass

    def update(self, dt):
        self.frame_time += dt
        # 속도 조절: 0.05초 * 12프레임 = 약 0.6초 동안 재생
        if self.frame_time >= 0.05:
            self.frame += 1
            self.frame_time = 0

            # 12장 다 보여주면 삭제
            if self.frame >= 12:  # len(images)
                game_world.remove_object(self)

    def draw(self):
        if RailHitEffect.images and self.frame < len(RailHitEffect.images):
            RailHitEffect.images[self.frame].draw(self.x, self.y)

    def get_bb(self):
        return 0, 0, 0, 0

    def handle_collision(self, group, other):
        pass
from pico2d import *
import math
import DEFINES
import game_world
import server  # 🌟 [필수] 서버 모듈 임포트

# -------------------------------------------------------------------------
# 1. 레일건 무기 클래스
# -------------------------------------------------------------------------
class Railgun:
    def __init__(self, x, y, player):
        self.player = player
        self.x, self.y = x, y

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
        self.charge_duration = 1.0
        self.charging_effect = None

        # 총구 위치
        self.muzzle_x = 0
        self.muzzle_y = 0

    def update(self, dt):
        if DEFINES.current_weapon_mode != DEFINES.WEAPON_RAILGUN:
            if self.is_charging: self.stop_charging()
            return

        # 1. 위치 동기화 (월드 좌표)
        if self.player.face_dir == -1:
            self.x = self.player.x - 32
            self.scale[1] = -2
        else:
            self.x = self.player.x + 48
            self.scale[1] = 2

        self.y = self.player.y

        # 2. 회전 계산 (🌟 수정됨: 화면 좌표 기준으로 계산)
        sx, sy = server.world_to_screen(self.x, self.y)
        dx = DEFINES.mouseX - sx
        dy = DEFINES.mouseY - sy
        self.rotation = math.atan2(dy, dx)

        # 3. 총구 위치 계산 (월드 좌표 유지)
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
            # 🌟 [수정] 화면 좌표로 변환해서 그리기
            sx, sy = server.world_to_screen(self.x, self.y)
            self.image.rotate_draw(self.rotation, sx, sy,
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
        game_world.add_object(beam, 2)
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
        # self.x, self.y는 update에서 갱신됨

        if ChargingEffect.images is None:
            ChargingEffect.images = []
            for i in range(1, 9):
                try:
                    ChargingEffect.images.append(load_image(f'resource/Sprites/GunsPack/effect/laygun_a{i}.png'))
                except:
                    pass

    def update(self, dt):
        # 월드 좌표 따라다님
        self.x, self.y = self.gun.muzzle_x, self.gun.muzzle_y

        self.frame_time += dt
        if self.frame_time >= 0.1:
            self.frame = (self.frame + 1) % 8
            self.frame_time = 0

    def draw(self):
        if ChargingEffect.images:
            # 🌟 [수정] 화면 좌표 변환
            sx, sy = server.world_to_screen(self.x, self.y)
            ChargingEffect.images[self.frame].draw(sx, sy)

    def get_bb(self):
        return 0, 0, 0, 0


# -------------------------------------------------------------------------
# 3. 레일건 빔 (2프레임 애니메이션 + 긴 사거리)
# -------------------------------------------------------------------------
class RailBeam:
    images = None

    def __init__(self, x, y, angle, owner, damage=10):
        self.x, self.y = x, y
        self.angle = angle
        self.owner = owner
        self.damage = damage
        self.spawn_time = get_time()
        self.lifetime = 0.2
        self.length = 1600
        self.thickness = 50

        self.frame = 0
        self.frame_time = 0.0

        if RailBeam.images is None:
            RailBeam.images = []
            for i in range(1, 3):
                try:
                    RailBeam.images.append(load_image(f'resource/Sprites/GunsPack/effect/laygun_c{i}.png'))
                except:
                    pass

        self.calculate_position()

    def calculate_position(self):
        # 월드 좌표계 계산
        self.end_x = self.x + self.length * math.cos(self.angle)
        self.end_y = self.y + self.length * math.sin(self.angle)
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

        # 🌟 [수정] 빔의 중심(cx, cy)을 화면 좌표로 변환
        sx, sy = server.world_to_screen(self.cx, self.cy)

        # 변환된 sx, sy에 그리기 (각도는 그대로 사용)
        img.rotate_draw(self.angle, sx, sy, self.length, self.thickness)

        # 디버그 박스 그리기
        if DEFINES.bbvisible:
            # get_bb()는 월드 좌표를 리턴하므로 변환 필요
            l, b, r, t = self.get_bb()
            sl, sb = server.world_to_screen(l, b)
            sr, st = server.world_to_screen(r, t)
            draw_rectangle(sl, sb, sr, st)

    def get_bb(self):
        # 충돌 처리는 월드 좌표계에서 수행하므로 그대로 유지
        box_width = self.length
        box_height = self.thickness
        rad = self.angle

        new_w = abs(box_width * math.cos(rad)) + abs(box_height * math.sin(rad))
        new_h = abs(box_width * math.sin(rad)) + abs(box_height * math.cos(rad))

        return (self.cx - new_w / 2, self.cy - new_h / 2,
                self.cx + new_w / 2, self.cy + new_h / 2)

    def is_valid_hit(self, target):
        # 정밀 충돌 검사 (월드 좌표계 사용 -> 수정 불필요)
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
        HIT_THRESHOLD = (self.thickness / 2) + 20

        return distance <= HIT_THRESHOLD

    def handle_collision(self, group, other):
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

        if RailHitEffect.images is None:
            RailHitEffect.images = []
            for i in range(1, 13):
                try:
                    RailHitEffect.images.append(load_image(f'resource/Sprites/GunsPack/effect/laygun_b{i}.png'))
                except:
                    pass

    def update(self, dt):
        self.frame_time += dt
        if self.frame_time >= 0.05:
            self.frame += 1
            self.frame_time = 0
            if self.frame >= 12:
                game_world.remove_object(self)

    def draw(self):
        if RailHitEffect.images and self.frame < len(RailHitEffect.images):
            # 🌟 [수정] 화면 좌표 변환
            sx, sy = server.world_to_screen(self.x, self.y)
            RailHitEffect.images[self.frame].draw(sx, sy)

    def get_bb(self):
        return 0, 0, 0, 0

    def handle_collision(self, group, other):
        pass
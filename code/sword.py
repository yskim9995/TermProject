from pico2d import *
import game_world
import math
import DEFINES
import server  # 🌟 [필수] 서버 모듈 임포트


# -----------------------------------------------------
# 1. 19프레임짜리 검기 이펙트 클래스
# -----------------------------------------------------
class SwordEffect:
    images = None
    LIFETIME = 0.75
    TOTAL_FRAMES = 12

    def __init__(self, player):
        self.player = player
        self.spawn_time = get_time()
        self.frame = 0
        self.hit_enemies = []
        self.damage = 20

        # 공격 중에는 총을 숨김
        DEFINES.Gunvisible = False

        # 충돌 그룹 등록
        game_world.addcollide_pairs('sword:enemy', self, None)

        self.offset_x = 32
        self.offset_y = 0
        self.EFFECT_WIDTH = 64
        self.EFFECT_HEIGHT = 64

        if SwordEffect.images is None:
            try:
                SwordEffect.images = [
                    load_image(f'resource/Sprites/SwordEffect/scythe_a{i + 1:d}.png')
                    for i in range(SwordEffect.TOTAL_FRAMES)
                ]
            except Exception as e:
                print(f"SwordEffect 이미지 로드 실패: {e}")

        self.time_per_frame = SwordEffect.LIFETIME / SwordEffect.TOTAL_FRAMES

    def update(self, dt):
        time_elapsed = get_time() - self.spawn_time

        if time_elapsed > SwordEffect.LIFETIME:
            game_world.remove_object(self)
            DEFINES.Gunvisible = True
            return

        self.frame = int(time_elapsed / self.time_per_frame)
        if self.frame >= SwordEffect.TOTAL_FRAMES:
            self.frame = SwordEffect.TOTAL_FRAMES - 1

    def draw(self):
        image_to_draw = SwordEffect.images[self.frame]

        flip_str = ''

        # 1. 월드 좌표 기준 위치 계산
        world_x = self.player.x + self.offset_x
        if self.player.face_dir == -1:  # 왼쪽을 볼 때
            flip_str = 'h'
            world_x = self.player.x - self.offset_x

        world_y = self.player.y + self.offset_y

        # 2. 🌟 화면 좌표로 변환 (World -> Screen)
        sx, sy = server.world_to_screen(world_x, world_y)

        # 3. 변환된 좌표(sx, sy)에 그리기
        image_to_draw.composite_draw(
            0,
            flip_str,
            sx, sy,  # 🌟 sx, sy 사용
            self.EFFECT_WIDTH,
            self.EFFECT_HEIGHT
        )

        # 4. 디버그 바운딩 박스 그리기
        if DEFINES.bbvisible:
            # get_bb()는 월드 좌표를 리턴하므로, 그리기 위해 화면 좌표로 변환해야 함
            l, b, r, t = self.get_bb()
            sl, sb = server.world_to_screen(l, b)
            sr, st = server.world_to_screen(r, t)
            draw_rectangle(sl, sb, sr, st)

    def get_bb(self):
        # 🌟 충돌 처리는 월드 좌표계에서 이루어지므로 그대로 둡니다.
        draw_x = self.player.x + self.offset_x
        if self.player.face_dir == -1:
            draw_x = self.player.x - self.offset_x

        draw_y = self.player.y + self.offset_y
        half_w = self.EFFECT_WIDTH / 2
        half_h = self.EFFECT_HEIGHT / 2

        return draw_x - half_w, draw_y - half_h, draw_x + half_w, draw_y + half_h

    def handle_collision(self, group, other):
        if group == 'sword:enemy':
            if other not in self.hit_enemies:
                print('검에 적 맞음(최초 1회)')
                self.hit_enemies.append(other)
                if other.hp > 0:
                    other.hp -= self.damage
                    if hasattr(other, 'state_machine'):
                        other.state_machine.handle_state_event(('HIT', self.player))


# -----------------------------------------------------
# 2. Sword 무기 클래스 (로직만 담당)
# -----------------------------------------------------
class Sword:
    def __init__(self, player):
        self.player = player
        self.attack_rate = 0.8
        self._last_attack_time = 0.0

    def handle_event(self, event):
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            self.try_attack()

    def try_attack(self):
        if DEFINES.current_weapon_mode != DEFINES.WEAPON_SWORD:
            return

        now = get_time()
        if now - self._last_attack_time < self.attack_rate:
            return

        self._last_attack_time = now
        # print("검 공격!")

        # 이펙트 생성 (이펙트가 화면에 그려짐)
        effect = SwordEffect(self.player)
        game_world.add_object(effect, 2)

    def update(self, dt):
        pass

    def draw(self):
        pass
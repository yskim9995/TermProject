from pico2d import *
import game_world
import math
import DEFINES


# -----------------------------------------------------
# 1. 19프레임짜리 검기 이펙트 클래스
# -----------------------------------------------------
class SwordEffect:
    images = None
    LIFETIME = 0.75  # 19프레임 총 재생 시간 (0.75초)
    TOTAL_FRAMES = 12

    def __init__(self, player):
        self.player = player
        self.spawn_time = get_time()
        self.frame = 0
        self.hit_enemies = []  # 이미 맞은 적 리스트
        self.damage = 20

        # 공격 중에는 총을 숨김
        DEFINES.Gunvisible = False

        # 충돌 그룹 등록 (검기 : 적)
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

        # 수명 다하면 제거
        if time_elapsed > SwordEffect.LIFETIME:
            game_world.remove_object(self)
            # 충돌 객체에서도 제거 (game_world에 remove_collision_object 기능이 있다면 사용)
            # 보통 remove_object 하면 자동으로 빠지지만, 명시적 관리가 필요할 수 있음
            # game_world.remove_colision_object(self)

            # 공격 끝났으니 총 다시 보이기
            DEFINES.Gunvisible = True
            return

        self.frame = int(time_elapsed / self.time_per_frame)
        if self.frame >= SwordEffect.TOTAL_FRAMES:
            self.frame = SwordEffect.TOTAL_FRAMES - 1

    def draw(self):
        image_to_draw = SwordEffect.images[self.frame]

        flip_str = ''
        draw_x = self.player.x + self.offset_x

        if self.player.face_dir == -1:  # 왼쪽을 볼 때
            flip_str = 'h'
            draw_x = self.player.x - self.offset_x

        image_to_draw.composite_draw(
            0,
            flip_str,
            draw_x,
            self.player.y + self.offset_y,
            self.EFFECT_WIDTH,
            self.EFFECT_HEIGHT
        )
        if DEFINES.bbvisible:
            draw_rectangle(*self.get_bb())

    def get_bb(self):
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
                    # 적에게 피격 이벤트 전달 (적 코드에 handle_state_event가 있어야 함)
                    if hasattr(other, 'state_machine'):
                        other.state_machine.handle_state_event(('HIT', self.player))


# -----------------------------------------------------
# 2. Sword 무기 클래스
# -----------------------------------------------------
class Sword:
    def __init__(self, player):
        self.player = player
        self.attack_rate = 0.8  # 쿨타임
        self._last_attack_time = 0.0

    # 🌟 [추가됨] Character에서 호출하는 이벤트 핸들러
    def handle_event(self, event):
        # 마우스 왼쪽 클릭 시 공격 시도
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            self.try_attack()

    def try_attack(self):
        # 현재 무기가 검이 아니면 실행 안 함 (이중 체크)
        if DEFINES.current_weapon_mode != DEFINES.WEAPON_SWORD:
            return

        now = get_time()
        if now - self._last_attack_time < self.attack_rate:
            return  # 쿨타임 중

        self._last_attack_time = now
        print("검 공격!")

        # 이펙트 생성
        effect = SwordEffect(self.player)
        game_world.add_object(effect, 2)  # Layer 2 (이펙트 레이어)

    def update(self, dt):
        pass

    def draw(self):
        pass
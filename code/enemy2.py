from pico2d import *
import os
from state_machine import StateMachine  # boy.py와 동일하게 상태 머신 사용
import random
import DEFINES
import game_world
import math
import hpbar
import server



# 적의 상태에 따른 프레임 속도, 이동 속도 등을 정의
ENEMY_SPEED_PPS = 150.0       # 초당 150 픽셀 (기존 5 * 30fps 가정)
ANIMATION_SPEED_FPS = 10.0      # 초당 10 프레임
KNOCKBACK_SPEED_PPS = 150.0   # 넉백 속도 (초당 픽셀)
IDLE_TIMER = 2.0
PATROL_TIMER = 5.0
HIT_DURATION = 0.5
GRAVITY_PPS2 = 2000.0

DETECT_RADIUS = 400.0  # 플레이어 감지 범위 (픽셀)
ATTACK_RANGE = 50.0    # 공격 사정거리 (픽셀)
RUN_SPEED_PPS = 200.0  # 추격 속도는 순찰보다 조금 빠르게
DETECT_Y_LIMIT = 50.0 # 🌟 [추가] 높이 차이가 50픽셀 이내일 때만 감지 (같은 층)


# --- 상태 이벤트 체크 함수 ---
# boy.py의 time_out과 동일한 역할
def time_out(e):
    return e[0] == 'TIME_OUT'
def hit(e): # 🌟 'HIT' 이벤트 정의
    return e[0] == 'HIT'

def recover(e): # 🌟 'RECOVER' 이벤트 정의
    return e[0] == 'RECOVER'

def detect_player(e):
    return e[0] == 'DETECT'

def lost_player(e):
    return e[0] == 'LOST'

def reach_attack_range(e):
    return e[0] == 'ATTACK_RANGE'

def attack_done(e):
    return e[0] == 'ATTACK_DONE'

def dead(e): # 🌟 죽음 이벤트 정의
    return e[0] == 'DEAD'

def give_up(e): # 🌟 추격 포기 이벤트
    return e[0] == 'GIVE_UP'

def arrived(e): # 🌟 집에 도착 이벤트
    return e[0] == 'ARRIVED'

class DeathEffect:
    images = []  # 🌟 여러 프레임의 이미지를 담을 리스트 (클래스 변수)

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frame = 0
        self.frame_time = 0.0
        self.LIFETIME = 1.0  # 이펙트가 유지되는 전체 시간 (애니메이션 길이와 일치하도록 조정)

        # 🌟 이펙트 이미지 로드 (최초 1회만)
        if not DeathEffect.images:
            # 🌟 [중요] 실제 이펙트 이미지 파일들을 로드해주세요!
            # 예시: 4프레임짜리 폭발 이펙트 이미지 파일
            try:
                DeathEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_1.png'))
                DeathEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_2.png'))
                DeathEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_3.png'))
                DeathEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_4.png'))
                DeathEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_5.png'))
                DeathEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_6.png'))
                DeathEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_7.png'))
                DeathEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_8.png'))

                # 더 많은 프레임이 있다면 추가
            except Exception as e:
                print(f"DeathEffect 이미지 로드 실패: {e}. 임시 더미 이미지 사용.")
                # 로드 실패 시 대체 이미지 (디버깅용)
                DeathEffect.images.append(load_image('resource/debug_square.png'))
                DeathEffect.images.append(load_image('resource/debug_square.png'))

    def update(self, dt):
        self.frame_time += dt

        # 🌟 애니메이션 속도 조절 (프레임당 0.15초, 즉 약 6.6 FPS)
        ANIMATION_SPEED = 0.10

        if self.frame_time >= ANIMATION_SPEED:
            self.frame += 1
            self.frame_time = 0.0

            # 모든 프레임을 다 재생했으면 (또는 일정 시간이 지났으면) 객체 삭제
            # images 리스트의 길이를 사용
            if self.frame >= len(DeathEffect.images):
                game_world.remove_object(self)
                return  # 삭제 후 더 이상 업데이트 불필요

        # (선택 사항) 전체 재생 시간이 아니라 일정 시간 후에 사라지게 하려면
        # self.LIFETIME -= dt
        # if self.LIFETIME <= 0:
        #    game_world.remove_object(self)

    def draw(self):
        if self.frame < len(DeathEffect.images):
            img = DeathEffect.images[self.frame]
            sx, sy = server.world_to_screen(self.x, self.y) # 🌟 변환
            img.draw(sx, sy)


class EnemyAttack:
    def __init__(self, x, y, face_dir):
        self.x = x
        self.y = y
        self.face_dir = face_dir
        self.exist_time = 0.0
        self.LIFETIME = 0.2  # 공격 판정이 유지되는 시간 (0.2초)

        # 공격 범위 크기 (조절 가능)
        self.width = 50
        self.height = 50

        # 데미지 (필요하다면)
        self.damage = 10

    def update(self, dt):
        self.exist_time += dt
        # 일정 시간이 지나면 스스로 사라짐
        if self.exist_time >= self.LIFETIME:
            game_world.remove_object(self)

    def draw(self):
        if DEFINES.bbvisible:
            # 🌟 [수정] get_bb()는 월드 좌표를 리턴하므로,
            # 사각형을 그리기 위해 화면 좌표로 변환해야 함.
            # 하지만 draw_rectangle은 (l, b, r, t)를 받으므로 계산이 좀 복잡해집니다.
            # 가장 쉬운 방법: 중심 좌표를 변환해서 사각형 그리기

            sx, sy = server.world_to_screen(self.x, self.y)
            offset_x = 40 * self.face_dir

            # 화면 기준 중심점
            screen_cx = sx + offset_x
            screen_cy = sy

            l = screen_cx - self.width // 2
            b = screen_cy - self.height // 2
            r = screen_cx + self.width // 2
            t = screen_cy + self.height // 2

            draw_rectangle(l, b, r, t)

    def get_bb(self):
        # 적이 보는 방향(face_dir)에 따라 공격 박스를 앞쪽에 생성
        # face_dir이 1이면 오른쪽, -1이면 왼쪽
        offset_x = 40 * self.face_dir

        return (self.x + offset_x - self.width // 2, self.y - self.height // 2,
                self.x + offset_x + self.width // 2, self.y + self.height // 2)

    def handle_collision(self, group, other):
        # 플레이어와 부딪히면, 자기 자신(공격박스)은 할 일을 다 했으니 사라짐
        if group == 'player:enemy_attack':
            game_world.remove_object(self)


# -----------------
# 적(Enemy)의 상태 클래스
# -----------------
class Die:
    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        print("Enemy Died")
        self.enemy.frame = 0
        self.enemy.frame_time = 0.0
        self.enemy.dir = 0  # 죽을 땐 움직이지 않음

        # (선택 사항) 죽는 소리 재생
        # self.enemy.die_sound.play()

    def exit(self, e):
        pass

    def do(self, dt):
        self.enemy.frame_time += dt

        # 죽는 모션 속도 (조금 천천히 0.15초)
        DIE_SPEED = 0.15

        if self.enemy.frame_time >= DIE_SPEED:
            self.enemy.frame_time = 0.0
            self.enemy.frame += 1

            # 🌟 8프레임 애니메이션이 끝나면(0~7번 재생 후 8이 되면)
            if self.enemy.frame >= 8:
                death_effect = DeathEffect(self.enemy.x, self.enemy.y)

                # 이펙트는 보통 가장 위 레이어(레이어 3)에 그립니다.
                game_world.add_object(death_effect, 3)

                # 몬스터 객체는 이제 게임 월드에서 제거
                game_world.remove_object(self.enemy)


                # (선택 사항) 점수 추가 등 게임 로직 처리
                # game_framework.score += 100

    def draw(self):
        FRAME_WIDTH = 32
        FRAME_HEIGHT = 16
        BOTTOM_ROW = 32 * 0
        frame_x = self.enemy.frame * FRAME_WIDTH

        # 🌟 좌표 변환
        sx, sy = server.world_to_screen(self.enemy.x, self.enemy.y)

        if self.enemy.face_dir == 1:
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                sx, sy, # 🌟 sx, sy 사용
                self.enemy.draw_width * self.enemy.scale[0],
                self.enemy.draw_height * self.enemy.scale[1]
            )
        else:
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h',
                sx, sy, # 🌟 sx, sy 사용
                self.enemy.draw_width * self.enemy.scale[0],
                self.enemy.draw_height * self.enemy.scale[1]
            )


class Return:
    """
    원래 스폰 위치(start_x)로 돌아가는 상태
    (모션은 Patrol과 동일하게 걷는 모션 사용)
    """

    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        self.enemy.frame = 0
        self.enemy.frame_time = 0.0
        # 집 방향으로 방향 설정
        if self.enemy.x < self.enemy.start_x:
            self.enemy.dir = 1
            self.enemy.face_dir = 1
        else:
            self.enemy.dir = -1
            self.enemy.face_dir = -1

    def exit(self, e):
        pass

    def do(self, dt):
        self.enemy.frame_time += dt

        # 애니메이션 속도 (Patrol과 동일하게)
        if self.enemy.frame_time >= (1.0 / ANIMATION_SPEED_FPS):
            self.enemy.frame_time = 0.0
            self.enemy.frame = (self.enemy.frame + 1) % 8

        # 이동 로직
        self.enemy.x += self.enemy.dir * RUN_SPEED_PPS * dt

        # 도착 체크
        if abs(self.enemy.x - self.enemy.start_x) < 10:
            self.enemy.x = self.enemy.start_x
            self.enemy.state_machine.handle_state_event(('ARRIVED', None))

    def draw(self):
        FRAME_WIDTH = 32
        FRAME_HEIGHT = 16
        BOTTOM_ROW = 32 * 3

        if self.enemy.frame >= 4 and self.enemy.frame <= 6:
            FRAME_HEIGHT = 30
        frame_x = self.enemy.frame * FRAME_WIDTH
        y_offset = (FRAME_HEIGHT - 16) / 2 * self.enemy.scale[1]

        # 🌟 좌표 변환
        sx, sy = server.world_to_screen(self.enemy.x, self.enemy.y)

        if self.enemy.face_dir == 1:
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                sx, sy + y_offset, # 🌟 sx, sy 사용 (+오프셋)
                self.enemy.draw_width * self.enemy.scale[0],
                FRAME_HEIGHT * self.enemy.scale[1]
            )
        else:
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h',
                sx, sy + y_offset, # 🌟 sx, sy 사용 (+오프셋)
                self.enemy.draw_width * self.enemy.scale[0],
                FRAME_HEIGHT * self.enemy.scale[1]
            )
class Trace:
    """
    플레이어를 발견하고 쫓아가는 상태
    """

    def __init__(self, enemy):
        self.enemy = enemy
        self.trace_timer = 0.0
    def enter(self, e):
        # print('Enemy Detected Player! Start Tracing')
        self.enemy.frame = 0
        self.enemy.frame_time = 0.0
        self.trace_timer = 0.0
        # 🌟 [추가] 상태에 들어오자마자 플레이어를 바라보게 함
        # 공격 후 복귀했을 때 등 뒤에 있는 플레이어를 즉시 쳐다보게 됨
        if self.enemy.target:
            if self.enemy.target.x < self.enemy.x:
                self.enemy.dir = -1
                self.enemy.face_dir = -1
            else:
                self.enemy.dir = 1
                self.enemy.face_dir = 1

    def exit(self, e):
        pass

    def do(self, dt):
        self.enemy.frame_time += dt

        if self.enemy.frame_time >= (1.0 / ANIMATION_SPEED_FPS):
            self.enemy.frame_time = 0.0
        # 프레임 증가 (8은 달리기 모션의 전체 프레임 수)
            self.enemy.frame = (self.enemy.frame + 1) % 4
        self.trace_timer += dt


        if self.trace_timer > 3.0:  # 3초 동안 못 잡으면
            print("놓쳤다! 집으로 가자.")
            self.enemy.state_machine.handle_state_event(('GIVE_UP', None))
            return
        if self.enemy.target:
            self.enemy.dir = 1 if self.enemy.target.x > self.enemy.x else -1
            self.enemy.face_dir = self.enemy.dir
            self.enemy.x += self.enemy.dir * RUN_SPEED_PPS * dt

            # 3. 거리 체크 (공격/놓침)
            import math
            distance = math.sqrt((self.enemy.x - self.enemy.target.x) ** 2 + (self.enemy.y - self.enemy.target.y) ** 2)

            if distance <= ATTACK_RANGE:
                self.enemy.state_machine.handle_state_event(('ATTACK_RANGE', None))
            elif distance > DETECT_RADIUS * 1.5:
                self.enemy.state_machine.handle_state_event(('LOST', None))

        #혹시모르니
        # # 애니메이션 (달리기)
        # if self.enemy.frame_time >= (1.0 / ANIMATION_SPEED_FPS):
        #     self.enemy.frame_time = 0.0
        #     self.enemy.frame = (self.enemy.frame + 1) % 4  # 달리기 프레임 수에 맞게 조절
        #
        # # 🌟 실시간 추격 로직
        # if self.enemy.target:
        #     # 매 프레임마다 플레이어 방향 확인
        #     if self.enemy.target.x < self.enemy.x:
        #         self.enemy.dir = -1
        #         self.enemy.face_dir = -1
        #     else:
        #         self.enemy.dir = 1
        #         self.enemy.face_dir = 1
        #
        #     # 이동 (방향 * 속도 * 시간)
        #     self.enemy.x += self.enemy.dir * RUN_SPEED_PPS * dt

    def draw(self):
        FRAME_WIDTH = 32
        FRAME_HEIGHT = 30
        BOTTOM_ROW = 32 * 4
        start_pixel_x = 32 * 6

        base_height_for_offset = self.enemy.bounding_box_height
        y_offset = (FRAME_HEIGHT - base_height_for_offset) / 2 * self.enemy.scale[1]

        frame_x = start_pixel_x + (self.enemy.frame * FRAME_WIDTH)

        # 🌟 좌표 변환
        sx, sy = server.world_to_screen(self.enemy.x, self.enemy.y)

        if self.enemy.face_dir == 1:
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                sx, sy + y_offset,  # 🌟 sx, sy 사용 (+오프셋)
                    self.enemy.draw_width * self.enemy.scale[0],
                    FRAME_HEIGHT * self.enemy.scale[1]
            )
        else:
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h',
                sx, sy + y_offset,  # 🌟 sx, sy 사용 (+오프셋)
                    self.enemy.draw_width * self.enemy.scale[0],
                    FRAME_HEIGHT * self.enemy.scale[1]
            )


class Attack:
    """
    제자리에서 멈춰 공격하는 상태
    """

    def __init__(self, enemy):
        self.enemy = enemy
        self.attack_timer = 0.0
        self.has_attacked = False  # 🌟 공격 판정을 만들었는지 체크하는 변수

    def enter(self, e):
        # print('Enemy Attacks!')
        self.enemy.dir = 0
        self.enemy.frame = 0
        self.enemy.frame_time = 0.0
        self.attack_timer = 0.0
        self.has_attacked = False  # 🌟 들어올 때 초기화

    def exit(self, e):
        pass

    def do(self, dt):
        self.enemy.frame_time += dt
        ATTACK_FRAME_TIME = 0.2
        # 애니메이션 진행 (예: 8프레임)
        if self.enemy.frame_time >= ATTACK_FRAME_TIME:
            self.enemy.frame_time = 0.0
            self.enemy.frame += 1

            # 🌟 [중요] 특정 프레임(예: 4번째)에 공격 판정 생성
            # has_attacked가 False일 때만 딱 한 번 생성
            if self.enemy.frame == 4 and not self.has_attacked:
                self.spawn_attack()
                self.has_attacked = True  # 생성했다고 표시

            # 애니메이션 종료 체크
            if self.enemy.frame >= 8:
                self.enemy.frame = 0
                self.enemy.state_machine.handle_state_event(('ATTACK_DONE', None))

    def spawn_attack(self):
        # EnemyAttack 객체를 생성해서 game_world에 추가
        # world[2] 레이어에 추가한다고 가정 (총알, 이펙트 레이어)
        attack_hitbox = EnemyAttack(self.enemy.x, self.enemy.y, self.enemy.face_dir)
        game_world.add_object(attack_hitbox, 2)

        # 🌟 충돌 충돌 처리를 위해 game_world의 충돌 그룹에도 추가해야 함
        # (main.py나 play_mode.py에서 add_collision_pair를 한 그룹 이름이어야 함)
        game_world.addcollide_pairs('player:enemy_attack', None, attack_hitbox)

        # 히트박스와 같은 위치(약간 앞)에 이펙트 생성
        offset_x = 40 * self.enemy.face_dir
        effect_x = self.enemy.x + offset_x
        effect_y = self.enemy.y

        effect = AttackEffect(effect_x, effect_y, self.enemy.face_dir)

        # 이펙트는 보통 캐릭터보다 앞(Layer 3)에 그려야 잘 보임
        game_world.add_object(effect, 3)

    def draw(self):
        FRAME_WIDTH = 32
        FRAME_HEIGHT = 16
        BOTTOM_ROW = 32 * 2
        frame_x = self.enemy.frame * FRAME_WIDTH

        # 🌟 좌표 변환
        sx, sy = server.world_to_screen(self.enemy.x, self.enemy.y)

        if self.enemy.face_dir == 1:
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                sx, sy, # 🌟 sx, sy 사용
                self.enemy.draw_width * self.enemy.scale[0],
                self.enemy.draw_height * self.enemy.scale[1]
            )
        else:
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h',
                sx, sy, # 🌟 sx, sy 사용
                self.enemy.draw_width * self.enemy.scale[0],
                self.enemy.draw_height * self.enemy.scale[1]
            )


class AttackEffect:
    images = []  # 🌟 이미지를 담을 리스트

    def __init__(self, x, y, face_dir):
        self.x = x
        self.y = y
        self.face_dir = face_dir
        self.frame = 0
        self.frame_time = 0

        # 🌟 이미지가 로드되지 않았다면 리스트에 추가 (최초 1회만 실행)
        if not AttackEffect.images:
            # 파일 경로를 실제 파일명에 맞게 수정해주세요!
            AttackEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyAttack/crossbow_a7.png'))  # 1번 프레임
            AttackEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyAttack/crossbow_a8.png'))  # 2번 프레임

    def update(self, dt):
        self.frame_time += dt

        # 0.05초마다 다음 장으로 넘어감
        if self.frame_time >= 0.05:
            self.frame += 1
            self.frame_time = 0

            # 2장(0, 1)을 다 보여줬으면(frame이 2가 되면) 객체 삭제
            if self.frame >= 2:
                game_world.remove_object(self)

    def draw(self):
        img = AttackEffect.images[self.frame]
        sx, sy = server.world_to_screen(self.x, self.y) # 🌟 변환
        if self.face_dir == 1:
            img.draw(sx, sy)
        else:
            img.composite_draw(0, 'h', sx, sy, img.w, img.h)


class Hit:
    """
    적이 피격당해 넉백되는 상태
    """
    # 🌟 [!] 피격 애니메이션 정보 (가정)
    HIT_FRAMES = 2  # 피격 애니메이션 프레임 수
    BOTTOM_ROW = 16 * 2  # 피격 애니메이션 Y 위치
    FRAME_WIDTH = 32
    FRAME_HEIGHT = 16

    # 🌟 [!] 피격 설정 (가정)
    KNOCKBACK_SPEED_PPS = 150  # 넉백 속도 (초당 픽셀)
    HIT_DURATION = 0.5  # 피격 상태 지속 시간

    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        # print('Enemy Enters Hit')

        # 1. 충돌 객체 가져오기
        # e가 ('HIT', object) 형태인지 확인
        if len(e) > 1:
            other = e[1]
        else:
            other = None

        # 2. 🌟 [안전한 넉백 방향 계산]
        # 상대방(other)이 있고, x좌표도 가지고 있다면 -> 그 반대로 튕겨남
        if other and hasattr(other, 'x'):
            self.knockback_dir = 1 if self.enemy.x > other.x else -1
        else:
            # 상대방 정보가 없거나(None), x가 없으면(독/함정 등)
            # 그냥 내가 보고 있는 방향의 반대로(뒤로) 밀려남
            self.knockback_dir = -self.enemy.face_dir

        # 3. 타이머 초기화 (기존 코드)
        self.start_time = get_time()
        self.enemy.frame = 0

        # (선택 사항) 살짝 위로 뜸
        self.enemy.vy = 100

    def exit(self, e):
        print('Enemy Exits Hit')

    def do(self,dt):  # 🌟 update에서 dt를 받는다고 가정
        frame_time = get_time() - self.start_time
        self.enemy.frame = int((frame_time * 10) % Hit.HIT_FRAMES)

        # 2. 🌟 넉백 이동 (dt 적용)
        self.enemy.x += self.knockback_dir * KNOCKBACK_SPEED_PPS * dt

        # 3. 상태 복귀 (get_time 기반)
        if get_time() - self.start_time > HIT_DURATION:
            self.enemy.state_machine.handle_state_event(('RECOVER', None))

    def draw(self):
        FRAME_WIDTH = 32
        FRAME_HEIGHT = 16
        BOTTOM_ROW = 32 * 0
        frame_x = self.enemy.frame * FRAME_WIDTH

        # 🌟 좌표 변환
        sx, sy = server.world_to_screen(self.enemy.x, self.enemy.y)

        if self.enemy.face_dir == 1:
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                sx, sy, # 🌟 sx, sy 사용
                self.enemy.draw_width * self.enemy.scale[0],
                self.enemy.draw_height * self.enemy.scale[1]
            )
        else:
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h',
                sx, sy, # 🌟 sx, sy 사용
                self.enemy.draw_width * self.enemy.scale[0],
                self.enemy.draw_height * self.enemy.scale[1]
            )
class Idle:
    """
    적이 제자리에서 대기하는 상태
    """

    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        self.enemy.dir = 0
        self.enemy.frame = 0
        self.enemy.frame_time = 0.0
        self.wait_start_time = get_time()  # 대기 시작 시간
        print('Enemy Enters Idle')

    def exit(self, e):
        print('Enemy Exits Idle')

    def do(self,dt):
        self.enemy.frame_time += dt
        if self.enemy.frame_time >= (1.0 / ANIMATION_SPEED_FPS):
            self.enemy.frame_time = 0.0
            self.enemy.frame = (self.enemy.frame + 1) % 4

        # 2. 상태 변경
        if get_time() - self.wait_start_time > IDLE_TIMER:
            self.enemy.state_machine.handle_state_event(('TIME_OUT', None))




    def draw(self):
        FRAME_WIDTH = 32
        FRAME_HEIGHT = 16
        BOTTOM_ROW = 32 * 4
        frame_x = self.enemy.frame * FRAME_WIDTH

        # 🌟 좌표 변환
        sx, sy = server.world_to_screen(self.enemy.x, self.enemy.y)

        if self.enemy.face_dir == 1:
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                sx, sy, # 🌟 sx, sy 사용
                self.enemy.draw_width * self.enemy.scale[0],
                self.enemy.draw_height * self.enemy.scale[1]
            )
        else:
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h',
                sx, sy, # 🌟 sx, sy 사용
                self.enemy.draw_width * self.enemy.scale[0],
                self.enemy.draw_height * self.enemy.scale[1]
            )

class Patrol:
    def __init__(self, enemy):
        self.enemy = enemy
        self.patrol_range = (enemy.start_x - 100, enemy.start_x + 100)

    def enter(self, e):
        self.enemy.dir = 1
        self.enemy.face_dir = 1
        self.enemy.frame_time = 0.0
        self.wait_start_time = get_time()

    def exit(self, e):
        pass
    def do(self,dt):
        self.enemy.frame_time += dt
        if self.enemy.frame_time >= (1.0 / ANIMATION_SPEED_FPS):
            self.enemy.frame_time = 0.0
            self.enemy.frame = (self.enemy.frame + 1) % 8
        # 2. 이동 (X축)
        self.enemy.x += self.enemy.dir * ENEMY_SPEED_PPS * dt
        # 3. 방향/상태 전환
        if self.enemy.x > self.patrol_range[1]:
            self.enemy.dir = -1
            self.enemy.face_dir = -1
        elif self.enemy.x < self.patrol_range[0]:
            self.enemy.dir = 1
            self.enemy.face_dir = 1
        if get_time() - self.wait_start_time > PATROL_TIMER:
            self.enemy.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        FRAME_WIDTH = 32
        FRAME_HEIGHT = 16
        BOTTOM_ROW = 32 * 3

        if self.enemy.frame >= 4 and self.enemy.frame <= 6:
            FRAME_HEIGHT = 30

        frame_x = self.enemy.frame * FRAME_WIDTH

        # 🌟 좌표 변환
        sx, sy = server.world_to_screen(self.enemy.x, self.enemy.y)

        if self.enemy.face_dir == 1:
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                sx, sy,  # 🌟 sx, sy 사용
                self.enemy.draw_width * self.enemy.scale[0],
                self.enemy.draw_height * self.enemy.scale[1]
            )
        else:
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h',
                sx, sy,  # 🌟 sx, sy 사용
                self.enemy.draw_width * self.enemy.scale[0],
                self.enemy.draw_height * self.enemy.scale[1]
            )



# -----------------
# 메인 Enemy 클래스
# -----------------
# 32 x  16
class AttackPoison:
    def __init__(self, enemy):
        self.enemy = enemy
        self.has_attacked = False

    def enter(self, e):
        self.enemy.dir = 0
        self.enemy.frame = 0
        self.enemy.frame_time = 0.0
        self.has_attacked = False

    def exit(self, e):
        pass

    def do(self, dt):
        self.enemy.frame_time += dt
        ATTACK_FRAME_TIME = 0.2

        if self.enemy.frame_time >= ATTACK_FRAME_TIME:
            self.enemy.frame_time = 0.0
            self.enemy.frame += 1

            # 🌟 4번째 프레임에서 독구름 생성!
            if self.enemy.frame == 4 and not self.has_attacked:
                self.spawn_poison()
                self.has_attacked = True

            # 애니메이션 종료
            if self.enemy.frame >= 8:
                self.enemy.frame = 0
                self.enemy.state_machine.handle_state_event(('ATTACK_DONE', None))

    def spawn_poison(self):
        # 🌟 독구름 생성 위치 (몬스터 발 밑이나 입 앞)
        # 바라보는 방향 앞쪽으로 조금 떨어진 곳
        spawn_x = self.enemy.x + (self.enemy.face_dir * 50)
        spawn_y = self.enemy.y - 20  # 약간 바닥 쪽

        gas = PoisonGas(spawn_x, spawn_y)
        game_world.add_object(gas, 2)  # 이펙트 레이어

        # 🌟 [중요] 충돌 그룹 등록 (플레이어 : 독)
        # main.py에서 이 그룹을 처리해줘야 함!
        game_world.addcollide_pairs('player:poison', None, gas)

    def draw(self):
        # (기존 Attack draw와 동일하게 복사)
        # server.world_to_screen 꼭 사용!
        FRAME_WIDTH = 32
        FRAME_HEIGHT = 16
        BOTTOM_ROW = 32 * 2
        frame_x = self.enemy.frame * FRAME_WIDTH
        sx, sy = server.world_to_screen(self.enemy.x, self.enemy.y)

        if self.enemy.face_dir == 1:
            self.enemy.image.clip_draw(frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT, sx, sy,
                                       self.enemy.draw_width * self.enemy.scale[0],
                                       self.enemy.draw_height * self.enemy.scale[1])
        else:
            self.enemy.image.clip_composite_draw(frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT, 0, 'h', sx, sy,
                                                 self.enemy.draw_width * self.enemy.scale[0],
                                                 self.enemy.draw_height * self.enemy.scale[1])


class PoisonGas:
    image = None

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.lifetime = 1.2  # 3초간 유지
        self.spawn_time = get_time()
        self.damage = 10
        self.scale = 1.0

        # 애니메이션 정보
        self.frame = 0
        self.frame_time = 0.0
        self.total_frames = 10  # 전체 프레임 수 (10개)

        # 🌟 1. 긴 이미지 한 장 로드
        if PoisonGas.image is None:
            # ⚠️ 실제 파일명으로 꼭 수정해주세요! (예: poison_sheet.png)
            try:
                PoisonGas.image = load_image('resource/Sprites/Free Mushrooms/Mush_Poison.png')
            except:
                print("독구름 스프라이트 시트 로드 실패")

        # 🌟 2. 프레임 하나의 크기 계산 (전체 너비 / 10)
        # 이미지가 로드되지 않았을 경우를 대비해 안전장치 추가
        if PoisonGas.image:
            self.sprite_width = PoisonGas.image.w // self.total_frames
            self.sprite_height = PoisonGas.image.h
        else:
            self.sprite_width = 0
            self.sprite_height = 0

    def update(self, dt):
        if get_time() - self.spawn_time > self.lifetime:
            game_world.remove_object(self)
            return

        self.frame_time += dt
        # 0.1초마다 프레임 변경
        if self.frame_time >= 0.1:
            self.frame_time = 0
            self.frame = (self.frame + 1) % self.total_frames

    def draw(self):
        if PoisonGas.image is None: return

        # 🌟🌟 [핵심 수정] 월드 좌표(self.x, self.y) -> 화면 좌표(sx, sy)로 변환
        sx, sy = server.world_to_screen(self.x, self.y)

        left = self.frame * self.sprite_width

        # 🌟 변환된 sx, sy 위치에 그립니다.
        PoisonGas.image.clip_draw(
            left, 0,
            self.sprite_width, self.sprite_height,
            sx, sy,  # 🌟 sx, sy 사용
            64 * self.scale, 64 * self.scale
        )

        if DEFINES.bbvisible:
            # 바운딩 박스를 그릴 때도 변환이 필요할 수 있지만,
            # 보통 get_bb는 월드 좌표를 리턴하고,
            # 충돌 박스 그리는 함수(draw_rectangle)에 넣을 때 변환합니다.

            # 정확하게 그리려면:
            l, b, r, t = self.get_bb()
            sl, sb = server.world_to_screen(l, b)
            sr, st = server.world_to_screen(r, t)
            draw_rectangle(sl, sb, sr, st)

    def get_bb(self):
        size = 40 * self.scale
        return self.x - size, self.y - size, self.x + size, self.y + size

    def handle_collision(self, group, other):
        pass

class Enemy2:
    # 🌟 Boy 클래스에서 배운 대로, 이미지는 클래스 변수로 한 번만 로드
    image = None
    hp_bg_image = None
    hp_fg_image = None
    def __init__(self, x= 400, y=150):

        self.x, self.y = random.randint(400, DEFINES.SCW), 500

        self.start_x = self.x  # 순찰 시작 위치
        self.frame = 0
        self.dir = 0
        self.face_dir = 1
        self.max_hp = 100
        self.hp = self.max_hp

        self.draw_width = 32
        self.draw_height = 16
        self.bounding_box_width = 32
        self.bounding_box_height = 16

        self.scale = [3.0, 3.0]
        self.rotation = 0.0
        self.frame_time = 0.0

        self.vy = 0.0
        self.is_grounded = True  # (처음엔 땅에 있다고 가정)

        self.target = None#타겟 (플레이어) 초기화
        if Enemy2.image is None:
            print("Loading Enemy image...")
            try:
                # 🌟 가정: 'resource' 폴더에 'enemy_animation.png' 파일이 있다고 가정
                Enemy2.image = load_image('resource/Sprites/Free Mushrooms/Mushroom_Spotted.png')
            except Exception as e:
                print(f"Enemy 이미지 로드 실패: {e}")
                # 🌟 로드 실패 시 임시로 Boy 이미지 사용 (크래시 방지)
                Enemy2.image = load_image('resource/cha_test_15.png')

        if not hasattr(Enemy2, 'hp_bar_bg'):
            # 파일 경로를 실제 이미지 파일명으로 수정하세요
            Enemy2.hp_bg_image = load_image('resource/Sprites/Free Mushrooms/btl_gage_hp_back.png')
            Enemy2.hp_fg_image = load_image('resource/Sprites/Free Mushrooms/btl_gage_hp.png')

        # 상태 객체 및 상태 머신 초기화
        self.IDLE = Idle(self)
        self.PATROL = Patrol(self)
        self.HIT = Hit(self)
        self.TRACE = Trace(self)
        self.ATTACK = AttackPoison(self)
        self.DIE = Die(self)
        self.RETURN = Return(self)
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {time_out: self.PATROL, hit: self.HIT, detect_player: self.TRACE, dead: self.DIE},
                self.PATROL: {time_out: self.IDLE, hit: self.HIT, detect_player: self.TRACE, dead: self.DIE},
                self.TRACE: {
                    lost_player: self.PATROL,  # 그냥 놓치면 제자리 순찰
                    give_up: self.RETURN,  # 🌟 시간 초과면 집으로 복귀!
                    reach_attack_range: self.ATTACK,
                    hit: self.HIT,
                    dead: self.DIE
                },
                self.ATTACK: {attack_done: self.TRACE, hit: self.HIT, dead: self.DIE},
                self.HIT: {recover: self.TRACE, dead: self.DIE},
                self.DIE: {},

                # 🌟 Return 상태 연결
                self.RETURN: {
                    arrived: self.PATROL,  # 🌟 도착하면 다시 순찰 시작
                    detect_player: self.TRACE,  # 복귀 중에도 플레이어 보면 다시 추격
                    hit: self.HIT,
                    dead: self.DIE
                }
            }
        )

    def get_bb(self):
        # 1. 스케일이 적용된 '전체' 너비와 높이를 계산
        scaled_w = self.bounding_box_width * self.scale[0]  # 32 * 3.0 = 96
        scaled_h = self.bounding_box_height * self.scale[1]  # 16 * 3.0 = 48

        # 2. '절반' 너비와 높이를 계산
        half_w = scaled_w / 3  # 48
        half_h = scaled_h / 2  # 24

        return self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h

    def update(self,dt):
        # main.py에서 호출될 함수. 상태 머신을 업데이트
        self.y += self.vy * dt
        # 2-2. 땅에 있지 않다면 중력 적용
        if not self.is_grounded:
            self.vy -= GRAVITY_PPS2 * dt

        # 2-3. (중요) 다음 프레임을 위해 "아직 땅이 아님"으로 가정
        self.is_grounded = False

        # 🌟 1. 플레이어 찾기 (만약 target이 설정 안 되어 있다면 game_world에서 찾음)
        if self.target is None:
            # game_world.world[1]에 플레이어가 있다고 가정 (레이어 확인 필요)
            # 안전하게 찾으려면 아래와 같이 순회할 수도 있음
            import game_world
            for obj in game_world.world[1]:
                if hasattr(obj, 'key_map'):  # Player 객체인지 확인하는 꼼수 (class check가 더 좋음)
                    self.target = obj
                    break

        # 🌟 2. 거리 계산 및 이벤트 발생 로직
        if self.target:
            distance = math.sqrt((self.x - self.target.x) ** 2 + (self.y - self.target.y) ** 2)

            dist_y = abs(self.y - self.target.y)

            cur_state = self.state_machine.cur_state

            # --- IDLE / PATROL 상태일 때 감지 로직 ---
            if cur_state in [self.IDLE, self.PATROL, self.RETURN]:
                # 거리도 가깝고(AND) 높이도 비슷해야(AND) 감지!
                if distance <= DETECT_RADIUS and dist_y <= DETECT_Y_LIMIT:
                    self.state_machine.handle_state_event(('DETECT', None))

            # --- TRACE(추격) 상태일 때 포기 로직 ---
            elif cur_state == self.TRACE:
                # 거리가 너무 멀어지거나(OR) 층이 너무 달라지면(OR) 놓침
                # 추격 중에는 조금 더 관대하게 봐줄 수도 있음 (예: 점프 고려해서 Y Limit * 2)
                if distance > DETECT_RADIUS * 1.5 or dist_y > DETECT_Y_LIMIT * 2:
                    self.state_machine.handle_state_event(('LOST', None))

                elif distance <= ATTACK_RANGE:
                    # 공격할 때도 높이가 맞아야 공격하게 하려면 여기에 dist_y 체크 추가
                    if dist_y <= 30:  # 높이가 거의 같을 때만 공격
                        self.state_machine.handle_state_event(('ATTACK_RANGE', None))

            elif cur_state == self.ATTACK:
                # 공격 중에는 보통 거리 체크를 안하거나, 공격이 끝나길 기다림
                pass

        self.state_machine.update(dt)

    def draw_hp(self):
        if Enemy2.hp_bg_image is None or Enemy2.hp_fg_image is None:
            return
        ratio = clamp(0, self.hp / self.max_hp, 1)
        y_offset = 20 * self.scale[1]
        bar_w = 64
        bar_h = 8

        # 🌟 좌표 변환
        sx, sy = server.world_to_screen(self.x, self.y)

        left = sx - (bar_w // 2)
        bottom = sy + y_offset
        Enemy2.hp_bg_image.draw_to_origin(left, bottom, bar_w, bar_h)
        current_w = bar_w * ratio
        Enemy2.hp_fg_image.draw_to_origin(left, bottom, current_w, bar_h)

    def draw(self):
        if DEFINES.bbvisible:
            # 바운딩 박스 그리기용 좌표 변환
            l, b, r, t = self.get_bb()
            sl, sb = server.world_to_screen(l, b)
            sr, st = server.world_to_screen(r, t)
            draw_rectangle(sl, sb, sr, st)

        self.state_machine.draw()
        if self.hp < self.max_hp:
            self.draw_hp()
        # hpbar.draw(self.x, self.y, self.hp, self.max_hp, 70)
    def handle_event(self, event):
        # 이 함수는 main.py의 SDL 이벤트가 아니라,
        # 상태 내부에서 발생하는 이벤트(예: time_out)를 처리하기 위함
        self.state_machine.handle_state_event(event)
    def handle_collision(self, group, other):
        if group == 'enemy:bullet':
            print('몬스터가 총알에 맞음!!!!!!!!!!!!!!!!!!!!!!!')
            self.hp -= other.damage  # (Bullet/SwordEffect에 damage 변수가 있다면)

            if self.hp > 0:
                self.state_machine.handle_state_event(('HIT', other))
            else :
                self.state_machine.handle_state_event(('DEAD', None))
            # print(f"Enemy Hit! HP: {self.hp}")
        elif group == 'player:enemy':
            # print('몬스터가 플레이어에 맞음')
            pass
        elif group == 'sword:enemy':
            # self.hp -= other.damage
            print('소드에 맞음')

            if self.hp > 0:
                self.state_machine.handle_state_event(('HIT', other))
            else:
                self.state_machine.handle_state_event(('DEAD', None))
            pass


        elif group == 'enemy:ground':

            if self.vy <= 0:
                my_bb = self.get_bb()
                my_half_h = (my_bb[3] - my_bb[1]) / 2  # 내 실제 절반 높이
                ground_top_y = other.get_bb()[3]

                self.y = ground_top_y + my_half_h
                self.vy = 0
                self.is_grounded = True




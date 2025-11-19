from pico2d import *
import os
from state_machine import StateMachine  # boy.py와 동일하게 상태 머신 사용
import random
import DEFINES
import game_world
import math
import hpbar



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
        # 디버그 모드일 때만 빨간 네모로 공격 범위 표시
        if DEFINES.bbvisible:
            draw_rectangle(*self.get_bb())

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
class Trace:
    """
    플레이어를 발견하고 쫓아가는 상태
    머리 위에 ! 표시가 뜸
    """

    def __init__(self, enemy):
        self.enemy = enemy
        # ! 표시 이미지 로드 (없으면 생략 가능하지만, 요청하셔서 추가)
        # self.alert_image = load_image('resource/alert.png')
        pass

    def enter(self, e):
        print('Enemy Detected Player! Start Tracing')
        self.enemy.frame = 0
        self.enemy.frame_time = 0.0

    def exit(self, e):
        pass

    def do(self, dt):
        self.enemy.frame_time += dt

        # 1. 애니메이션 (달리기 모션 사용 - Patrol과 같은 Row 3 사용 가정)
        if self.enemy.frame_time >= (1.0 / ANIMATION_SPEED_FPS):
            self.enemy.frame_time = 0.0
            self.enemy.frame = (self.enemy.frame + 1) % 8

        # 2. 플레이어 방향으로 이동
        if self.enemy.target:
            # 플레이어가 왼쪽에 있는지 오른쪽에 있는지 판단
            if self.enemy.target.x < self.enemy.x:
                self.enemy.dir = -1
                self.enemy.face_dir = -1
            else:
                self.enemy.dir = 1
                self.enemy.face_dir = 1

            # 이동 적용
            self.enemy.x += self.enemy.dir * RUN_SPEED_PPS * dt

        # 3. 거리 체크는 Enemy.update에서 수행하여 이벤트를 보냄

    def draw(self):
        FRAME_WIDTH = 32
        FRAME_HEIGHT = 16  # 달리기 동작은 키가 클 수 있음 (Patrol 참고)
        BOTTOM_ROW = 32 * 3  # Patrol과 같은 스프라이트 라인 사용 (Run)

        frame_x = self.enemy.frame * FRAME_WIDTH

        # 캐릭터 그리기
        if self.enemy.face_dir == 1:
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                self.enemy.x, self.enemy.y,
                self.enemy.draw_width * self.enemy.scale[0], self.enemy.draw_height * self.enemy.scale[1]
            )
        else:
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h', self.enemy.x, self.enemy.y,
                self.enemy.draw_width * self.enemy.scale[0], self.enemy.draw_height * self.enemy.scale[1]
            )

        # 🌟 [!] 느낌표 표시 (텍스트로 대체하거나 이미지를 그립니다)
        # 폰트가 없다면 디버그용 네모라도 그립니다.
        # draw_rectangle(self.enemy.x - 10, self.enemy.y + 40, self.enemy.x + 10, self.enemy.y + 60)
        pass


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

        # 애니메이션 진행 (예: 8프레임)
        if self.enemy.frame_time >= 0.1:
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
                self.enemy.state_machine.handle_state_event(('ATTA2CK_DONE', None))

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
        # (기존 draw 코드 유지)
        FRAME_WIDTH = 32
        FRAME_HEIGHT = 16
        BOTTOM_ROW = 32 * 2  # 공격 모션 위치 확인 필요
        frame_x = self.enemy.frame * FRAME_WIDTH

        if self.enemy.face_dir == 1:
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                self.enemy.x, self.enemy.y,
                self.enemy.draw_width * self.enemy.scale[0], self.enemy.draw_height * self.enemy.scale[1]
            )
        else:
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h', self.enemy.x, self.enemy.y,
                self.enemy.draw_width * self.enemy.scale[0], self.enemy.draw_height * self.enemy.scale[1]
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
        # 현재 프레임 번호(0 또는 1)에 해당하는 이미지 가져오기
        img = AttackEffect.images[self.frame]

        if self.face_dir == 1:
            # 오른쪽: 그냥 그리기
            img.draw(self.x, self.y)
        else:
            # 왼쪽: 좌우 반전('h')해서 그리기
            # composite_draw(회전각, 반전, x, y, 너비, 높이)
            img.composite_draw(0, 'h', self.x, self.y, img.w, img.h)


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
        print('Enemy Enters Hit')
        # 1. 충돌 이벤트(e)에서 충돌한 객체(other)를 가져옴
        other = e[1]

        # 2. 넉백 방향 결정 (other의 반대 방향)
        #    other(플레이어/검기)가 왼쪽에 있으면 -> 오른쪽(1)으로 넉백
        self.knockback_dir = 1 if self.enemy.x > other.x else -1

        # 3. 타이머 및 프레임 초기화
        self.start_time = get_time()
        self.enemy.frame = 0

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

        if self.enemy.face_dir == 1:  # 오른쪽
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                self.enemy.x, self.enemy.y,
                self.enemy.draw_width * self.enemy.scale[0], self.enemy.draw_height * self.enemy.scale[1]
            )
        else:  # 왼쪽
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h', self.enemy.x, self.enemy.y,
                self.enemy.draw_width * self.enemy.scale[0], self.enemy.draw_height * self.enemy.scale[1]
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
        # 🌟 수정됨: "위에서 2번째 줄" = 8번째 줄 (0~9)
        BOTTOM_ROW = 32 * 4
        frame_x = self.enemy.frame * FRAME_WIDTH

        if self.enemy.face_dir == 1:  # 오른쪽
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                self.enemy.x, self.enemy.y,
                self.enemy.draw_width * self.enemy.scale[0], self.enemy.draw_height * self.enemy.scale[1]
            )
        else:  # 왼쪽
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h', self.enemy.x, self.enemy.y,
                self.enemy.draw_width * self.enemy.scale[0], self.enemy.draw_height * self.enemy.scale[1]
            )

class Patrol:
    def __init__(self, enemy):
        self.enemy = enemy
        self.patrol_range = (enemy.start_x - 200, enemy.start_x + 200)

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

        if  self.enemy.frame >= 4 and self.enemy.frame <= 6:
            FRAME_HEIGHT = 30
        frame_x = self.enemy.frame * FRAME_WIDTH

        if self.enemy.face_dir == 1:  # 오른쪽
            self.enemy.image.clip_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                self.enemy.x, self.enemy.y,
                self.enemy.draw_width * self.enemy.scale[0], self.enemy.draw_height * self.enemy.scale[1]
            )
        else:  # 왼쪽
            self.enemy.image.clip_composite_draw(
                frame_x, BOTTOM_ROW, FRAME_WIDTH, FRAME_HEIGHT,
                0, 'h', self.enemy.x, self.enemy.y,
                self.enemy.draw_width * self.enemy.scale[0], self.enemy.draw_height * self.enemy.scale[1]
            )



# -----------------
# 메인 Enemy 클래스
# -----------------
# 32 x  16
class Enemy:
    # 🌟 Boy 클래스에서 배운 대로, 이미지는 클래스 변수로 한 번만 로드
    image = None

    def __init__(self, x= 400, y=150):

        self.x, self.y = random.randint(200, DEFINES.SCW), 500

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
        if Enemy.image is None:
            print("Loading Enemy image...")
            try:
                # 🌟 가정: 'resource' 폴더에 'enemy_animation.png' 파일이 있다고 가정
                Enemy.image = load_image('resource/Sprites/Free Mushrooms/Mushroom_Reg.png')
            except Exception as e:
                print(f"Enemy 이미지 로드 실패: {e}")
                # 🌟 로드 실패 시 임시로 Boy 이미지 사용 (크래시 방지)
                Enemy.image = load_image('resource/cha_test_15.png')

        # 상태 객체 및 상태 머신 초기화
        self.IDLE = Idle(self)
        self.PATROL = Patrol(self)
        self.HIT = Hit(self)
        self.TRACE = Trace(self)
        self.ATTACK = Attack(self)
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {
                    time_out: self.PATROL,
                    hit: self.HIT,
                    detect_player: self.TRACE  # Idle 중에도 발견하면 추격
                },
                self.PATROL: {
                    time_out: self.IDLE,
                    hit: self.HIT,
                    detect_player: self.TRACE  # Patrol 중에 발견하면 추격
                },
                self.TRACE: {
                    lost_player: self.PATROL,  # 놓치면 다시 순찰
                    reach_attack_range: self.ATTACK,  # 가까워지면 공격
                    hit: self.HIT
                },
                self.ATTACK: {
                    attack_done: self.TRACE,  # 공격 끝나면 다시 추격(또는 Idle)
                    hit: self.HIT
                },
                self.HIT: {
                    recover: self.TRACE  # 맞고 회복하면 다시 추격 (혹은 Idle)
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

            # 현재 상태 확인
            cur_state = self.state_machine.cur_state

            if cur_state in [self.IDLE, self.PATROL]:
                if distance <= DETECT_RADIUS:
                    self.state_machine.handle_state_event(('DETECT', None))

            elif cur_state == self.TRACE:
                if distance > DETECT_RADIUS * 1.5:  # 추격 포기 범위 (감지보다 좀 더 길게 잡음)
                    self.state_machine.handle_state_event(('LOST', None))
                elif distance <= ATTACK_RANGE:
                    self.state_machine.handle_state_event(('ATTACK_RANGE', None))

            elif cur_state == self.ATTACK:
                # 공격 중에는 보통 거리 체크를 안하거나, 공격이 끝나길 기다림
                pass

        self.state_machine.update(dt)


    def draw(self):
        # main.py에서 호출될 함수. 현재 상태의 draw()를 호출
        if DEFINES.bbvisible:
            draw_rectangle(*self.get_bb())
        self.state_machine.draw()
        # hpbar.draw(self.x, self.y, self.hp, self.max_hp, 70)
    def handle_event(self, event):
        # 이 함수는 main.py의 SDL 이벤트가 아니라,
        # 상태 내부에서 발생하는 이벤트(예: time_out)를 처리하기 위함
        self.state_machine.handle_state_event(event)
    def handle_collision(self, group, other):
        if group == 'enemy:bullet':
            print('몬스터가 총알에 맞음!!!!!!!!!!!!!!!!!!!!!!!')
            self.state_machine.handle_state_event(('HIT', other))
            # self.hp -= other.damage  # (Bullet/SwordEffect에 damage 변수가 있다면)
            # print(f"Enemy Hit! HP: {self.hp}")
        elif group == 'player:enemy':
            print('몬스터가 플레이어에 맞음')
        elif group == 'sword:enemy':
            pass


        elif group == 'enemy:ground':

            if self.vy <= 0:
                my_bb = self.get_bb()
                my_half_h = (my_bb[3] - my_bb[1]) / 2  # 내 실제 절반 높이
                ground_top_y = other.get_bb()[3]

                self.y = ground_top_y + my_half_h
                self.vy = 0
                self.is_grounded = True

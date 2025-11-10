from pico2d import *
import os
from state_machine import StateMachine  # boy.py와 동일하게 상태 머신 사용
import hpbar
# --- 상태 정의 ---
# 적의 상태에 따른 프레임 속도, 이동 속도 등을 정의
ENEMY_SPEED = 5
IDLE_TIMER = 2.0
PATROL_TIMER = 5.0


# --- 상태 이벤트 체크 함수 ---
# boy.py의 time_out과 동일한 역할
def time_out(e):
    return e[0] == 'TIME_OUT'


# -----------------
# 적(Enemy)의 상태 클래스
# -----------------

class Idle:
    """
    적이 제자리에서 대기하는 상태
    """

    def __init__(self, enemy):
        self.enemy = enemy

    def enter(self, e):
        self.enemy.dir = 0
        self.enemy.frame = 0
        self.wait_start_time = get_time()  # 대기 시작 시간
        print('Enemy Enters Idle')

    def exit(self, e):
        print('Enemy Exits Idle')

    def do(self):
        self.enemy.frame = (self.enemy.frame + 1) % 4
        # 일정 시간이 지나면 순찰 상태로 변경
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
        self.wait_start_time = get_time()
        print('패트롤 시작')

    def exit(self, e):
        print('패트롤 나감')

    def do(self):
        # 🌟 수정됨: 프레임 0~7 (총 8개) 반복
        self.enemy.frame = (self.enemy.frame + 1) % 8

        self.enemy.x += self.enemy.dir * ENEMY_SPEED

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
        # 🌟 수정됨: "위에서 2번째 줄" = 8번째 줄 (0~9)
        BOTTOM_ROW = 32 * 3

        if  self.enemy.frame >= 4 and self.enemy.frame <= 6:
            print('asdasd')
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

    def __init__(self, x=400, y=90):
        self.x, self.y = x, y
        self.start_x = x  # 순찰 시작 위치
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

        # 🌟 이미지 로드 (Boy.py와 동일한 'renderer' 오류 방지 패턴)
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
        self.state_machine = StateMachine(
            self.IDLE,  # 시작 상태는 Idle
            {
                # 이벤트: 대상 상태
                self.IDLE: {time_out: self.PATROL},
                self.PATROL: {time_out: self.IDLE}
            }
        )

    def get_bb(self):
        half_w = self.bounding_box_width / 2
        half_h = self.bounding_box_height / 2
        return self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h

    def update(self,dt):
        # main.py에서 호출될 함수. 상태 머신을 업데이트
        self.state_machine.update()


    def draw(self):
        # main.py에서 호출될 함수. 현재 상태의 draw()를 호출
        self.state_machine.draw()
        # hpbar.draw(self.x, self.y, self.hp, self.max_hp, 70)
    def handle_event(self, event):
        # 이 함수는 main.py의 SDL 이벤트가 아니라,
        # 상태 내부에서 발생하는 이벤트(예: time_out)를 처리하기 위함
        self.state_machine.handle_state_event(event)
from pico2d import load_image, get_time
from sdl2 import SDL_KEYDOWN, SDLK_SPACE, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDLK_a
import os
from state_machine import StateMachine  # StateMachine 클래스가 import 되어야 함
import hpbar

# 현재 작업 디렉토리(CWD)를 다시 한번 출력
print("CWD:", os.getcwd())

# 찾으려는 파일의 전체 경로를 출력
test_path = os.path.join(os.getcwd(), 'resource', 'particle', 'eff_sword_atk1_1.png')
print("찾으려는 전체 경로 예시:", test_path)

# 해당 경로에 파일이 실제로 존재하는지 확인
print("파일 존재 여부:", os.path.exists(test_path))
# 🌟 이 결과는 반드시 True가 나와야 합니다.
# ----------------------------------------------------

# 1. 이벤트 체크 함수 (Event Check Functions)
# ----------------------------------------------------

def keyDown_a(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_a


def space_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_SPACE


def time_out(e):
    return e[0] == 'TIME_OUT'


def attack_timeout(e):
    return e[0] == 'ATTACK_TIME_OUT'


def right_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_RIGHT


def right_up(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_RIGHT


def left_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_LEFT


def left_up(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_LEFT


# ----------------------------------------------------
# 2. AttackEffect 클래스 (공격 이펙트 애니메이션)
# ----------------------------------------------------

# 이펙트 이미지 사전 로드
# 🌟 이미지가 'resource' 폴더에 있는지 확인하세요.


EFFECT_IMAGE = [
       load_image('resource/eff_sword_atk1_1.png'),
       load_image('resource/eff_sword_atk1_2.png'),
       load_image('resource/eff_sword_atk1_3.png'),
       load_image('resource/eff_sword_atk1_4.png'),
       load_image('resource/eff_sword_atk1_5.png'),
       load_image('resource/eff_sword_atk1_6.png')
]




class AttackEffect:

    def __init__(self, x, y, face_dir):
        self.x, self.y = x + face_dir * 50, y + 20
        self.face_dir = face_dir
        self.frame = 0
        self.max_frame = len(EFFECT_IMAGE)
        self.start_time = get_time()
        self.frame_per_sec = 24.0
        self.duration = self.max_frame / self.frame_per_sec
        self.bounding_box_width = 260
        self.bounding_box_height = 220

        self.hit_enemies = set()  # 이미 타격한 적을 추적하는 집합
        # 🌟 2. 애니메이션 설정
        self.max_frame = 6  # 총 6개 이미지
        self.frame_per_sec = 12.0  # 1초에 12프레임 (속도 조절)
        # 1회 재생에 걸리는 시간 (예: 6 / 12 = 0.5초)
        self.anim_duration = self.max_frame / self.frame_per_sec

        # 🌟 3. 이펙트 전체 수명 (예: 2초 동안 화면에 유지)
        self.effect_lifetime = 0.5

    def get_bb(self):
        """
        공격 이펙트의 현재 바운딩 박스를 반환합니다.
        """
        half_w = self.bounding_box_width / 2
        half_h = self.bounding_box_height / 2
        return self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h

    def update(self):
        elapsed_time = get_time() - self.start_time

        # 🌟 1. 이펙트 수명 체크
        if elapsed_time > self.effect_lifetime:
            return False  # 2초가 지나면 False를 반환하여 제거

        # 🌟 2. 애니메이션 프레임 반복 재생 (Looping)
        # (전체 경과 시간 % 1회 재생 시간) = 현재 루프의 시간
        current_anim_time = elapsed_time % self.anim_duration
        self.frame = int(current_anim_time * self.frame_per_sec)

        # 프레임이 0~5 범위를 벗어나지 않게 보정
        self.frame = max(0, min(self.frame, self.max_frame - 1))

        return True  # 🌟 수명이 다할 때까지 True 반환 (유지)
    # 339 272
    def draw(self):
        if self.frame < self.max_frame:
            current_image = EFFECT_IMAGE[self.frame]
            draw_w, draw_h = 339, 272  # 이펙트 크기 (예시)

            # TODO: 좌우 반전 로직 필요 (pico2d의 clip_composite_draw 등을 사용해 구현)
            # 여기서는 편의상 draw()를 사용합니다.
            current_image.draw(self.x, self.y, draw_w, draw_h)


# ----------------------------------------------------
# 3. State 클래스들 (상태)
# ----------------------------------------------------


class Jump:
    def __init__(self, boy):
        self.boy = boy
        self.vy = 0.0
        self.gravity = 1.2  # 한 프레임당 감소할 속도량 (튜닝 가능)

    def enter(self, e):
        # 이벤트가 None일 수 있으므로 안전하게 검사
        self.boy.dir = 0
        if e and isinstance(e, tuple) and e[0] == 'INPUT':
            if right_down(e) or left_up(e):
                self.boy.dir = self.boy.face_dir = 1
            elif left_down(e) or right_up(e):
                self.boy.dir = self.boy.face_dir = -1

        # 초기 점프 속도
        self.vy = 18.0
        self.boy.jump_start_time = get_time()

    def exit(self, e):
        pass

    def do(self):
        # 애니메이션 프레임 업데이트
        self.boy.frame = (self.boy.frame + 1) % 8

        # 수평 경계 처리 및 이동
        if self.boy.x < 25:
            self.boy.x = 25
        elif self.boy.x > 1255:
            self.boy.x = 1255
        self.boy.x += self.boy.dir * 5

        # 수직 이동: 위치 갱신 후 중력 적용
        self.boy.y += self.vy
        self.vy -= self.gravity

        # 착지 검사 (Boy 초기 y = 90 에 맞춤)
        ground_y = 90
        if self.boy.y <= ground_y:
            self.boy.y = ground_y
            self.vy = 0.0
            # 착지 시 상태 전환 이벤트 발생
            self.boy.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        # Jump 상태에서도 그리기 메서드 제공 (좌우 반전 처리)
        if self.boy.face_dir == 1:  # right
            self.boy.image.clip_draw(self.boy.frame * 100, 100, 100, 100, self.boy.x, self.boy.y)
        else:  # left
            # clip_composite_draw 사용하여 좌우 반전 ('h' flip)
            self.boy.image.clip_composite_draw(self.boy.frame * 100, 0, 100, 100, 0, 'h', self.boy.x, self.boy.y, 100, 100)

class Run:  # ... (기존 Run 클래스 유지)
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        self.boy.dir = 1
        if right_down(e) or left_up(e):
            self.boy.dir = self.boy.face_dir = 1
        elif left_down(e) or right_up(e):
            self.boy.dir = self.boy.face_dir = -1

    def exit(self, e):
        pass

    def do(self):
        self.boy.frame = (self.boy.frame + 1) % 8
        if (self.boy.x < 25):
            self.boy.x += 5
        elif (self.boy.x > 1255):
            self.boy.x -= 5
        self.boy.x += self.boy.dir * 5

    def draw(self):
        if self.boy.face_dir == 1:  # right
            self.boy.image.clip_draw(self.boy.frame * 100, 100, 100, 100, self.boy.x, self.boy.y)
        else:  # face_dir == -1: # left
            self.boy.image.clip_draw(self.boy.frame * 100, 0, 100, 100, self.boy.x, self.boy.y)


class Sleep:  # ... (기존 Sleep 클래스 유지)
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        self.boy.dir = 0

    def exit(self, e):
        pass

    def do(self):
        self.boy.frame = (self.boy.frame + 1) % 8

    def draw(self):
        if self.boy.face_dir == 1:  # right
            self.boy.image.clip_composite_draw(self.boy.frame * 100, 300, 100, 100, 3.141592 / 2, '', self.boy.x - 25,
                                               self.boy.y - 25, 100, 100)
        else:  # face_dir == -1: # left
            self.boy.image.clip_composite_draw(self.boy.frame * 100, 200, 100, 100, -3.141592 / 2, '', self.boy.x + 25,
                                               self.boy.y - 25, 100, 100)


class Idle:  # ... (기존 Idle 클래스 유지)
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        self.boy.dir = 0
        self.boy.wait_start_time = get_time()

    def exit(self, e):
        pass

    def do(self):
        self.boy.frame = (self.boy.frame + 1) % 8
        if get_time() - self.boy.wait_start_time > 2.0:
            self.boy.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        if self.boy.face_dir == 1:  # right
            self.boy.image.clip_draw(self.boy.frame * 100, 300, 100, 100, self.boy.x, self.boy.y)
        else:  # face_dir == -1: # left
            self.boy.image.clip_draw(self.boy.frame * 100, 200, 100, 100, self.boy.x, self.boy.y)


class Attack:

    def __init__(self, boy):
        self.boy = boy
        self.duration = 0.3  # 공격 애니메이션 지속 시간

    def enter(self, e):
        self.boy.dir = 0
        self.boy.frame = 0
        self.boy.attack_start_time = get_time()

        # 🌟 이펙트 생성 함수 호출
        self.boy.add_attack_effect()

    def exit(self, e):
        pass

    def do(self):
        # 공격 애니메이션 프레임 업데이트 (예: 4프레임짜리 공격 애니메이션 가정)
        # 공격 애니메이션 속도를 빠르게 하기 위해 프레임을 더 자주 업데이트
        self.boy.frame = int((get_time() - self.boy.attack_start_time) * 10) % 8

        # 시간이 지나면 상태 전환 이벤트를 발생
        if get_time() - self.boy.attack_start_time > self.duration:
            self.boy.state_machine.handle_state_event(('ATTACK_TIME_OUT', None))

    def draw(self):
        # 🌟 공격 애니메이션 프레임 그리기 로직 (예: 400 라인이라고 가정)
        if self.boy.face_dir == 1:  # right
            self.boy.image.clip_draw(self.boy.frame * 100, 400, 100, 100, self.boy.x, self.boy.y)
        else:  # face_dir == -1: # left
            self.boy.image.clip_draw(self.boy.frame * 100, 500, 100, 100, self.boy.x, self.boy.y)


# ----------------------------------------------------
# 4. Boy 클래스 (메인 캐릭터)
# ----------------------------------------------------

class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.dir = 0
        self.max_hp = 100
        self.hp = self.max_hp
        self.image = load_image('resource/animation_sheet.png')
        # self.image = load_image('resource/eff_sword_atk1_1.png')

        # 🌟 공격 이펙트 리스트
        self.effects = []

        # 상태 객체 초기화
        self.SLEEP = Sleep(self)
        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.ATTACK = Attack(self)  # ATTACK 상태 추가
        self.JUMP = Jump(self)

        # 상태 머신 정의
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.SLEEP: {space_down : self.JUMP,keyDown_a: self.ATTACK, right_down: self.RUN, left_down: self.RUN, space_down: self.IDLE},
                self.IDLE: {space_down : self.JUMP,keyDown_a: self.ATTACK, right_up: self.RUN, left_up: self.RUN, right_down: self.RUN,
                            left_down: self.RUN, time_out: self.SLEEP},
                self.RUN: {space_down : self.JUMP ,keyDown_a: self.ATTACK, right_down: self.IDLE, left_down: self.IDLE, right_up: self.IDLE,
                           left_up: self.IDLE},
                # self.AutoRun: {keyDown_a: self.ATTACK, right_down: self.RUN, left_down: self.RUN, time_out: self.IDLE},
                self.ATTACK: {attack_timeout: self.IDLE , right_down: self.RUN , left_down: self.RUN}, # ATTACK 상태는 시간이 지나면 IDLE로 복귀
                self.JUMP: {time_out: self.IDLE}
            })

    # 🌟 공격 이펙트 생성 함수
    def add_attack_effect(self):
        new_effect = AttackEffect(self.x, self.y, self.face_dir)
        self.effects.append(new_effect)

    def update(self):
        self.state_machine.update()
        # 🌟 이펙트 업데이트 및 제거
        new_effects = []
        for e in self.effects:
            if e.update():  # e.update()가 True(수명 안 끝남)인 경우에만 유지
                new_effects.append(e)
        self.effects = new_effects

    def draw(self):
        self.state_machine.draw()
        hpbar.draw(self.x,self.y,self.hp, self.max_hp,50)
        # 🌟 이펙트 그리기
        for e in self.effects:
            e.draw()

    def handle_evnet(self, event):
        self.state_machine.handle_state_event(('INPUT', event))
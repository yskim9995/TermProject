from pico2d import *
from sdl2 import SDL_KEYDOWN, SDLK_SPACE, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDLK_a, SDLK_e, SDLK_d, SDLK_w,SDLK_s
import os
import screen_effects
from sword import Sword
from state_machine import StateMachine  # StateMachine 클래스가 import 되어야 함
import hpbar

import game_world
import DEFINES
# ... (파일 경로 체크 부분은 동일) ...

RUN_SPEED_PPS = 300.0  # 초당 300 픽셀
JUMP_POWER_PPS = 700.0 # 점프 초기 속도 (초당)
GRAVITY_PPS2 = 2000.0  # 중력 가속도 (초당)d
ANIMATION_SPEED_FPS = 10.0
# ----------------------------------------------------
# 1. 이벤트 체크 함수 (Event Check Functions)
# ----------------------------------------------------
# ... (keyDown_a, space_down 등 이벤트 함수는 동일) ...
def keyDown_a(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_a

def keyUp_a(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_a

def keyDown_w(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_w

def keyUp_w(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_w


def keyDown_s(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_s

def keyUp_s(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_s


def keyDown_d(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_d

def keyUp_d(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_d


def space_down(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_SPACE


def time_out(e):
    return e[0] == 'TIME_OUT'


def attack_timeout(e):
    return e[0] == 'ATTACK_TIME_OUT'

def move_event(e):
    return e[0] == 'MOVE'

# 🌟 새로운 이벤트: 멈춤
def stop_event(e):
    return e[0] == 'STOP'

# 🌟 새로운 이벤트: 땅에 닿음 (handle_collision에서 사용)
def ground_collision(e):
    return e[0] == 'GROUND_COLLISION'

def hit_event(e):
    return e[0] == 'HIT'


# def right_down(e):
#     return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_RIGHT
#
#
# def right_up(e):
#     return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_RIGHT
#
#
# def left_down(e):
#     return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_LEFT
#
#
# def left_up(e):
#     return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_LEFT
# ----------------------------------------------------
# 2. 상태 클래스 (State Classes)
# ----------------------------------------------------

class Jump:
    def __init__(self, Player):
        self.Player = Player

    def enter(self, e):
        self.Player.vy = JUMP_POWER_PPS
        self.Player.frame = 0
        self.Player.frame_time = 0.0

    def exit(self, e):
        pass

    def do(self, dt):
        # 1. 애니메이션 (JumpImages는 4장)
        self.Player.frame_time += dt
        time_per_frame = 1.0 / ANIMATION_SPEED_FPS

        # 점프 이미지는 보통 반복보다는 상승/하강에 따라 다르지만, 일단 반복재생
        if self.Player.frame_time >= time_per_frame:
            self.Player.frame = (self.Player.frame + 1) % 4  # JumpImages 개수(4)
            self.Player.frame_time -= time_per_frame

        # 2. 이동 로직
        self.Player.x += self.Player.dir * RUN_SPEED_PPS * dt
        self.Player.y += self.Player.vy * dt
        self.Player.vy -= GRAVITY_PPS2 * dt

        self.Player.x = clamp(25, self.Player.x, DEFINES.SCW - 25)

    def draw(self):
        flip_str = 'h' if self.Player.face_dir == -1 else ''

        # 🌟 JumpImages 사용
        self.Player.JumpImages[self.Player.frame].composite_draw(
            self.Player.rotation, flip_str,
            self.Player.x, self.Player.y,
            self.Player.width * self.Player.scale[0],
            self.Player.height * self.Player.scale[1]
        )


class Run:
    def __init__(self, Player):
        self.Player = Player

    def enter(self, e):
        self.Player.frame = 0
        self.Player.frame_time = 0.0

    def exit(self, e):
        pass

    def do(self, dt):
        # 1. 애니메이션 (RunImages는 6장)
        self.Player.frame_time += dt
        time_per_frame = 1.0 / ANIMATION_SPEED_FPS

        if self.Player.frame_time >= time_per_frame:
            self.Player.frame = (self.Player.frame + 1) % 6  # RunImages 개수(6)
            self.Player.frame_time -= time_per_frame

        # 2. 이동 로직
        self.Player.x += self.Player.dir * RUN_SPEED_PPS * dt
        self.Player.y += self.Player.vy * dt
        self.Player.vy -= GRAVITY_PPS2 * dt

        self.Player.x = clamp(25, self.Player.x, DEFINES.SCW - 25)

    def draw(self):
        flip_str = 'h' if self.Player.face_dir == -1 else ''

        # 🌟 RunImages 사용
        self.Player.RunImages[self.Player.frame].composite_draw(
            self.Player.rotation, flip_str,
            self.Player.x, self.Player.y,
            self.Player.width * self.Player.scale[0],
            self.Player.height * self.Player.scale[1]
        )


class Hit:
    def __init__(self, Player):
        self.Player = Player
        self.timer = 0.0

    def enter(self, e):
        self.Player.frame = 0
        self.Player.frame_time = 0.0
        self.timer = 0.0
        # 피격 시 약간 뒤로 밀려나는 효과 (선택 사항)
        self.Player.vy = 200  # 살짝 뜸
        self.Player.x -= self.Player.face_dir * 20  # 뒤로 밀림

    def exit(self, e):
        pass

    def do(self, dt):
        self.timer += dt
        self.Player.frame_time += dt

        # 애니메이션 (HitImages는 2장)
        if self.Player.frame_time >= 0.1:
            self.Player.frame = (self.Player.frame + 1) % 2
            self.Player.frame_time = 0

        # 중력 적용 (밀려나는 느낌)
        self.Player.y += self.Player.vy * dt
        self.Player.vy -= GRAVITY_PPS2 * dt

        # 0.5초 뒤에 다시 IDLE 상태로 복귀 (TIME_OUT 이벤트 발생)
        if self.timer > 0.5:
            self.Player.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        flip_str = 'h' if self.Player.face_dir == -1 else ''

        # 🌟 HitImages 사용
        self.Player.HitImages[self.Player.frame].composite_draw(
            self.Player.rotation, flip_str,
            self.Player.x, self.Player.y,
            self.Player.width * self.Player.scale[0],
            self.Player.height * self.Player.scale[1]
        )



class Idle:
    def __init__(self, Player):
        self.Player = Player

    def enter(self, e):
        self.Player.wait_start_time = get_time()
        self.Player.frame = 0  # 🌟 프레임 0부터 시작
        self.Player.frame_time = 0.0  # 🌟 타이머 초기화
        # self.Player.wait_start_time = get_time()

    def exit(self, e):
        pass

    def do(self,dt):
        self.Player.frame_time += dt

        self.Player.y += self.Player.vy
        self.Player.vy -= self.Player.gravity
        # 🌟 2. 1프레임당 재생 시간 (1.0 / 10.0 = 0.1초)
        time_per_frame = 1.0 / ANIMATION_SPEED_FPS

        # 🌟 3. 누적 시간이 1프레임 시간(0.1초)을 넘었는지 확인
        if self.Player.frame_time >= time_per_frame:
            # 🌟 4. 프레임을 1 증가시키고 타이머 초기화 (넘은 시간은 유지)
            self.Player.frame = (self.Player.frame + 1) % 4  # 8 프레임 반복
            self.Player.frame_time -= time_per_frame

    def draw(self):
        flip_str = ''  # 기본값 (오른쪽, 뒤집지 않음)
        if self.Player.face_dir == -1:  # 왼쪽을 볼 때
            flip_str = 'h'  # 'h' = horizontal flip (좌우 반전)

        # 2. rotate_draw 대신 composite_draw 사용
        self.Player.IdleImages[self.Player.frame].composite_draw(
            self.Player.rotation,  # 1. 회전값 (radian)
            flip_str,  # 2. 반전값 ('' or 'h')
            self.Player.x, self.Player.y,  # 3. 위치 (x, y)
            self.Player.width * self.Player.scale[0],  # 4. 너비 (width)
            self.Player.height * self.Player.scale[1]  # 5. 높이 (height)
        )


# ----------------------------------------------------
# 4. Player 클래스 (메인 캐릭터)
# ----------------------------------------------------

class Player:

    def __init__(self, x, y):
        # self.IdleImages = [load_image('resource/Sprites/Character/char0.png'),
        #                    load_image('resource/Sprites/Character/char1.png'),
        #                    load_image('resource/Sprites/Character/char2.png'),
        #                    load_image('resource/Sprites/Character/char3.png'),
        #                    load_image('resource/Sprites/Character/char4.png'),
        #                    load_image('resource/Sprites/Character/char5.png'),
        #                    load_image('resource/Sprites/Character/char6.png'),
        #                    load_image('resource/Sprites/Character/char7.png'),
        #                    load_image('resource/Sprites/Character/char8.png'),
        #                    load_image('resource/Sprites/Character/char9.png')]


        #아이들
        self.IdleImages = [load_image('resource/Sprites/Character/player/player_idle1.png'),
                           load_image('resource/Sprites/Character/player/player_idle2.png'),
                           load_image('resource/Sprites/Character/player/player_idle3.png'),
                           load_image('resource/Sprites/Character/player/player_idle4.png')]
        #달리기
        self.RunImages = [load_image('resource/Sprites/Character/player/player_run1.png'),
                          load_image('resource/Sprites/Character/player/player_run2.png'),
                          load_image('resource/Sprites/Character/player/player_run3.png'),
                          load_image('resource/Sprites/Character/player/player_run4.png'),
                          load_image('resource/Sprites/Character/player/player_run5.png'),
                          load_image('resource/Sprites/Character/player/player_run6.png')]
        #점프
        self.JumpImages = [load_image('resource/Sprites/Character/player/player_jump1.png'),
                           load_image('resource/Sprites/Character/player/player_jump2.png'),
                           load_image('resource/Sprites/Character/player/player_jump3.png'),
                           load_image('resource/Sprites/Character/player/player_jump4.png')]
        #스턴
        self.stunImages = [load_image('resource/Sprites/Character/player/player_sturn1.png'),
                           load_image('resource/Sprites/Character/player/player_sturn2.png'),
                           load_image('resource/Sprites/Character/player/player_sturn3.png')]

        self.HitImages = [load_image('resource/Sprites/Character/player/player_hit1.png'),
                          load_image('resource/Sprites/Character/player/player_hit2.png')]
        self.frame = 0
        self.face_dir = 1
        self.dir = 0
        self.max_hp = 100
        self.hp = self.max_hp
        self.effects = []
        self.frame_time = 0.0
        self.x = x
        self.y = y

        self.vy = 0.0
        self.gravity = 1.2
        self.hit_time = 0.0
        self.key_map = {'a': 0, 'd': 0}
        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.JUMP = Jump(self)
        self.HIT = Hit(self)

        from gun import Gun

        self.gun = Gun(self.x, self.y, self)
        self.sword = Sword(self)
        # 하드코딩된 16 대신 로드한 이미지의 실제 크기를 사용
        self.width = self.IdleImages[0].w
        self.height = self.IdleImages[0].h

        self.scale = [1.0, 1.0]
        self.rotation = 0.0

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {
                    keyDown_w: self.JUMP,
                    move_event: self.RUN,
                    hit_event: self.HIT  # 피격 당하면 HIT로
                },
                self.RUN: {
                    keyDown_w: self.JUMP,
                    stop_event: self.IDLE,
                    hit_event: self.HIT  # 달리다 맞아도 HIT로
                },
                self.JUMP: {
                    ground_collision: self.IDLE,
                    hit_event: self.HIT  # 점프 중 맞아도 HIT로
                },
                self.HIT: {
                    time_out: self.IDLE,  # 일정 시간 지나면 IDLE로 복귀
                    ground_collision: self.HIT  # 피격 중 땅에 닿으면 처리(선택)
                    # 만약 피격 중 떨어져서 땅에 닿아도 계속 피격 모션 유지하려면 이렇게
                    # 혹은 땅에 닿으면 바로 IDLE로 가려면 ground_collision: self.IDLE
                }
            })
    def update(self,dt):
        if self.hit_time < 0.5:
            self.hit_time+= dt
        # 🌟 3. 'dir'을 매 프레임 'key_map' 기준으로 계산
        new_dir = self.key_map['d'] - self.key_map['a']

        # 방향이 0이 아니게 되었을 때 (정지 -> 움직임)
        if self.state_machine.cur_state == self.IDLE and new_dir != 0:
            self.state_machine.handle_state_event(('MOVE', None))
            # (RUN 상태인데 키가 떼지면 -> 'STOP' 이벤트 전송)
        elif self.state_machine.cur_state == self.RUN and new_dir == 0:
            self.state_machine.handle_state_event(('STOP', None))

        self.dir = new_dir  # 최종 방향 업데이트

        # 'dir'이 0이 아닐 때만 face_dir 업데이트
        if self.dir != 0:
            self.face_dir = self.dir
        self.state_machine.update(dt)
        self.gun.update(dt)
        self.sword.update(dt)


    def draw(self):
        self.state_machine.draw()
        self.gun.draw()
        if DEFINES.bbvisible:
            draw_rectangle(*self.get_bb())

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_a:
                self.key_map['a'] = 1
            elif event.key == SDLK_d:
                self.key_map['d'] = 1
        elif event.type == SDL_KEYUP:
            if event.key == SDLK_a:
                self.key_map['a'] = 0
            elif event.key == SDLK_d:
                self.key_map['d'] = 0
        self.state_machine.handle_state_event(('INPUT', event))

    def fire(self):
        self.gun.try_fire(game_world.world[1])

    def get_bb(self):

        # half_w = self.width / 2
        # half_h = self.height / 2
        # return self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h
        half_w = (self.width * self.scale[0]) / 2
        half_h = (self.height * self.scale[1]) / 2

        # 중심(x,y)에서 절반만큼 빼고 더함
        return self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h

    def handle_collision(self, group, other):
        if group == 'player:enemy':
            # 무적 시간 체크 (연속 피격 방지)
            # if self.hit_time >= 0.5 and self.hp > 0:
            #     self.hit_time = 0
            #     self.hp -= 10
            #     screen_effects.trigger(0.1)
            #     print('플레이어가 몬스터에 충돌')
            #
            #     # 🌟 상태 머신에 HIT 이벤트 전송!
            #     self.state_machine.handle_state_event(('HIT', None))
            pass


        if group == 'player:ground':
            if self.vy <= 0:
                ground_top_y = other.get_bb()[3]
                self.y = ground_top_y + (self.height / 2)
                self.vy = 0

                # JUMP 상태일 때만 착지 처리 (HIT 중에는 튕겨나가는 모션 유지 위해 제외 가능)
                if self.state_machine.cur_state == self.JUMP:
                    self.state_machine.handle_state_event(('GROUND_COLLISION', None))

                # 만약 HIT 상태에서도 땅에 닿으면 바로 걷게 하고 싶다면 아래 주석 해제
                # if self.state_machine.cur_state == self.HIT:
                #     self.state_machine.handle_state_event(('TIME_OUT', None))
        if group == 'player:enemy_attack':
            if self.hit_time >= 0.5:  # 무적 시간 체크
                self.hit_time = 0
                self.hp -= 10  # other.damage를 가져와도 됨
                print("아얏! 몬스터 공격에 맞음")
                self.state_machine.handle_state_event(('HIT', None))  # 플레이어도 HIT 상태로
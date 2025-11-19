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
        self.Player.jump_start_time = get_time()
        self.Player.frame = 0
        self.Player.frame_time = 0.0

    def exit(self, e):
        pass

    def do(self,dt):
        # 1. 애니메이션 (dt 기반)
        self.Player.frame_time += dt
        time_per_frame = 1.0 / ANIMATION_SPEED_FPS
        if self.Player.frame_time >= time_per_frame:
            self.Player.frame = (self.Player.frame + 1) % 8
            self.Player.frame_time -= time_per_frame

        # 2. 🌟 가로 이동 (수정됨)
        self.Player.x += self.Player.dir * RUN_SPEED_PPS * dt

        # 3. 🌟 세로 이동 (수정됨)
        self.Player.y += self.Player.vy * dt
        self.Player.vy -= GRAVITY_PPS2 * dt  # dt 기반 중력

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
        # 🌟 요청에 따라 Jump 상태에서는 그리지 않도록 수정
        pass


class Run:
    def __init__(self, Player):
        self.Player = Player
    def enter(self, e):
        pass
    def exit(self, e):

        pass

    def do(self,dt):
        self.Player.x += self.Player.dir * RUN_SPEED_PPS * dt

        # 3. 세로 이동 (중력)
        self.Player.y += self.Player.vy * dt
        self.Player.vy -= GRAVITY_PPS2 * dt

        # 4. 화면 경계 처리
        self.Player.x = clamp(25, self.Player.x, DEFINES.SCW - 25)

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

        pass



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
            self.Player.frame = (self.Player.frame + 1) % 8  # 8 프레임 반복
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
        self.IdleImages = [load_image('resource/Sprites/Character/char0.png'),
                           load_image('resource/Sprites/Character/char1.png'),
                           load_image('resource/Sprites/Character/char2.png'),
                           load_image('resource/Sprites/Character/char3.png'),
                           load_image('resource/Sprites/Character/char4.png'),
                           load_image('resource/Sprites/Character/char5.png'),
                           load_image('resource/Sprites/Character/char6.png'),
                           load_image('resource/Sprites/Character/char7.png'),
                           load_image('resource/Sprites/Character/char8.png'),
                           load_image('resource/Sprites/Character/char9.png')]

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
                    move_event: self.RUN  # 'MOVE' 이벤트가 오면 RUN
                },
                self.RUN: {
                    keyDown_w: self.JUMP,
                    stop_event: self.IDLE  # 'STOP' 이벤트가 오면 IDLE
                },
                self.JUMP: {
                    ground_collision:self.IDLE
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
        return self.x - self.width  , self.y - self.height , self.x + self.width , self.y + self.height

    def handle_collision(self, group, other):
        if group == 'player:enemy':  # 충돌처리가 왔는데 이게 boy:ball 이 원인이야
            if self.hit_time >= 0.5 and self.hp > 0:
                self.hit_time = 0
                self.hp -= 10
                screen_effects.trigger(0.1)
                print('플레이어가 몬스터에 충돌')
        if group == 'player:ground':
            if self.vy <= 0:

                # 2-2. 땅 위에 정확히 서도록 y 위치 보정
                # (other는 'ground' 객체, [3]은 get_bb()의 top)
                ground_top_y = other.get_bb()[3]
                # (self.height / 2는 get_bb()가 중앙 기준일 때)
                self.y = ground_top_y + (self.height / 2)

                # 2-3. Y속도를 0으로 (낙하 멈춤)
                self.vy = 0

                # 2-4. 'JUMP' 상태였다면 IDLE/RUN으로
                if self.state_machine.cur_state == self.JUMP:
                    self.state_machine.handle_state_event(('GROUND_COLLISION', None))
        pass

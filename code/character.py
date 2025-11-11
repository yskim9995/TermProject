from pico2d import *
from sdl2 import SDL_KEYDOWN, SDLK_SPACE, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDLK_a, SDLK_e, SDLK_d, SDLK_w,SDLK_s
import os

from sword import Sword
from state_machine import StateMachine  # StateMachine 클래스가 import 되어야 함
import hpbar

import game_world

# ... (파일 경로 체크 부분은 동일) ...

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
    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_w


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
        self.vy = 0.0
        self.gravity = 1.2

    def enter(self, e):
        self.Player.dir = 0
        if e and isinstance(e, tuple) and e[0] == 'INPUT':
            pass
            # if right_down(e) or left_up(e):
            #     self.Player.dir = self.Player.face_dir = 1
            # elif left_down(e) or right_up(e):
            #     self.Player.dir = self.Player.face_dir = -1

        self.vy = 18.0
        self.Player.jump_start_time = get_time()

    def exit(self, e):
        pass

    def do(self):
        self.Player.frame = (self.Player.frame + 1) % 8
        if self.Player.x < 0:
            self.Player.x = 16
        elif self.Player.x > 1255:
            self.Player.x = 1255
        self.Player.x += self.Player.dir * 5
        self.Player.y += self.vy
        self.vy -= self.gravity
        ground_y = 90
        if self.Player.y <= ground_y:
            self.Player.y = ground_y
            self.vy = 0.0
            self.Player.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        self.Player.IdleImages[self.Player.frame].rotate_draw(
            self.Player.rotation,
            self.Player.x, self.Player.y,
            self.Player.width * self.Player.scale[0],
            self.Player.height * self.Player.scale[1]
        )

        # 🌟 요청에 따라 Jump 상태에서는 그리지 않도록 수정
        pass


class Run:
    def __init__(self, Player):
        self.Player = Player
    def enter(self, e):
        if keyDown_d(e) or keyUp_a(e):
            self.Player.dir = self.Player.face_dir = 1
        elif keyDown_a(e) or keyUp_d(e):
            self.Player.dir = self.Player.face_dir = -1

    def exit(self, e):

        pass

    def do(self):

        self.Player.frame = (self.Player.frame + 1) % 8
        if self.Player.x < 25:
            self.Player.x += 5
        elif self.Player.x > 1255:
            self.Player.x -= 5

        self.Player.x += self.Player.dir * 5

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
        self.Player.dir = 0
        self.Player.wait_start_time = get_time()

    def exit(self, e):
        pass

    def do(self):
        self.Player.frame = (self.Player.frame + 1) % 8
        # if get_time() - self.Player.wait_start_time > 2.0:
        #     self.Player.state_machine.handle_state_event(('TIME_OUT', None))

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


        # 상태 객체 초기화
        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.JUMP = Jump(self)

        self.x = x
        self.y = y

        from gun import Gun

        self.gun = Gun(self.x, self.y, self)
        self.sword = Sword(self)
        # 🌟 수정됨: 하드코딩된 16 대신 로드한 이미지의 실제 크기를 사용
        self.width = self.IdleImages[0].w
        self.height = self.IdleImages[0].h

        self.scale = [1.0, 1.0]
        self.rotation = 0.0

        self.state_machine = StateMachine(
            self.IDLE,
            {
                # IDLE 상태: '키를 누르면' JUMP 또는 RUN
                self.IDLE: {
                    keyDown_w: self.JUMP,
                    keyDown_a: self.RUN,  # 'a' 누르면 RUN
                    keyDown_d: self.RUN,

                    # 💡 (keyUp 이벤트는 여기서 필요 없습니다)
                },

                # RUN 상태: '키를 떼면' IDLE, '다른 키를 누르면' JUMP
                self.RUN: {
                    keyDown_w: self.JUMP,
                    keyUp_a: self.IDLE,  # 'a' 떼면 IDLE
                    keyUp_d: self.IDLE,  # 'd' 떼면 IDLE
                    keyDown_a: self.RUN,
                    keyDown_d: self.RUN,# 'd' 누르면 RUN
                    # 💡 (keyDown 이벤트는 여기서 IDLE로 가면 안 됩니다)
                },

                # JUMP 상태: 점프가 끝나면(time_out) IDLE
                self.JUMP: {
                    time_out: self.IDLE
                    # 💡 (JUMP 중에는 키 입력으로 상태가 바뀌지 않는 것이 일반적입니다.
                    #    공중 이동은 Jump 상태의 'do' 함수에서 처리해야 합니다.)
                }
            })

    def update(self,dt):
        # 🌟 수정됨: Player.update에서 프레임 관리를 제거 (각 상태가 담당)
        self.state_machine.update()
        self.gun.update(dt)
        self.sword.update(dt)


    def draw(self):
        self.state_machine.draw()
        # hpbar.draw(self.x,self.y,self.hp, self.max_hp,50)
        self.gun.draw()
        draw_rectangle(*self.get_bb())

    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))
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
            print('플레이어가 몬스터에 충돌')
        pass

from pico2d import *
import game_world
import DEFINES

from pico2d import SDL_BUTTON_LMASK, SDL_BUTTON_LEFT
from enemy import *

# Game object class here


def collide(a, b):
    """
    두 객체 a와 b의 바운딩 박스가 겹치는지 확인합니다. (AABB 충돌 검사)
    a와 b는 .get_bb() 함수가 있어야 합니다.
    """
    left_a, bottom_a, right_a, top_a = a.get_bb()
    left_b, bottom_b, right_b, top_b = b.get_bb()

    if left_a > right_b: return False
    if right_a < left_b: return False
    if top_a < bottom_b: return False
    if bottom_a > top_b: return False

    return True

def handle_events():
    global running, player ,mx, my , mouse_state

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        elif event.type == SDL_MOUSEMOTION:
            mx = event.x
            # 🌟 Y좌표 변환: (0, 0)을 왼쪽 위에서 왼쪽 아래로
            my = DEFINES.SCH - 1 - event.y
            DEFINES.mouseX = mx
            DEFINES.mouseY = my

        elif event.type == SDL_MOUSEBUTTONDOWN:
            # 왼쪽 버튼 클릭 시
            if event.button == SDL_BUTTON_LEFT:
                mouse_state = True
                click_x = event.x
                click_y = 900- 1 - event.y
                print(f"Left Click! at ({click_x}, {click_y})")
        elif event.type == SDL_MOUSEBUTTONUP:
            if event.button == SDL_BUTTON_LEFT:
                mouse_state = False
        else:
            if player:
                player.handle_event(event)

def reset_world():
    global player
    player = Player(16, 16)
    game_world.add_object(player, 1)
    game_world.addcollide_pairs('player:enemy',Player,None)

    global enemy

    enemy = Enemy()

    game_world.add_object(enemy,1)


    _gun = Gun(player.x + 16, player.y , player)
    game_world.add_object(_gun, 1)

    player.scale = [3.0, 3.0]
    _gun.scale = [2.0, 2.0]

def update_world(d):
    game_world.update(dt)
    pass


def render_world():
    clear_canvas()
    game_world.render()
    update_canvas()
    pass
    

running = True
mouse_state = False
open_canvas(DEFINES.SCW,DEFINES.SCH)

from character import Player
from gun import Gun

reset_world()
current_time = get_time()
while running:
    # 1. Delta Time (dt) 계산
    new_time = get_time()
    dt = new_time - current_time
    current_time = new_time
    DEFINES.dt = dt

    # 2. 이벤트 처리 (키보드, 마우스 위치)
    handle_events()

    # 🌟 3. '상태' 폴링 (Polling) 및 로직 처리
    # 마우스 왼쪽 버튼이 '눌려있는지' main에서 직접 확인

    if mouse_state:
        player.fire()

    update_world(dt)

    clear_canvas()
    render_world()
    update_canvas()
    delay(0.01)
    # 5. 렌더링

# finalization code
close_canvas()

# 끝!
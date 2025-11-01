from pico2d import *
import game_world
import DEFINES

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
    global running, player ,mx, my

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
                click_x = event.x
                click_y = 900- 1 - event.y
                print(f"Left Click! at ({click_x}, {click_y})")
        else:
            if player:
                player.handle_event(event)

def reset_world():
    global player
    player = Player(16, 16)
    game_world.add_object(player, 1)

    _gun = Gun(player.x + 16, player.y , player)
    game_world.add_object(_gun, 1)

    player.scale = [3.0, 3.0]
    _gun.scale = [3.0, 3.0]

def update_world():
    # 1. 월드 내 모든 객체 업데이트
    game_world.update()

    pass


def render_world():
    clear_canvas()
    game_world.render()
    update_canvas()


    pass
    

running = True

open_canvas(DEFINES.SCW,DEFINES.SCH)

from character import Player
from gun import Gun

reset_world()

# game loop
while running:
    handle_events()
    update_world()
    render_world()
    delay(0.01)
# finalization code
close_canvas()

# 끝!
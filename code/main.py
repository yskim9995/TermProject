from pico2d import *
import game_world
import DEFINES
import screen_effects
from pico2d import SDL_BUTTON_LMASK, SDL_BUTTON_LEFT

from enemy import *

from Background import *
from grass import Grass
from hpbar import Hpbar
# Game object class here

from portal import Portal

def collide(a, b):
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
        #검 공격 시도
        elif event.type == SDL_KEYDOWN and event.key == SDLK_z:
            player.sword.try_attack()


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
    bg =  Background()
    game_world.add_object(bg, 0)


    #지형지물 생성
    for i in range(4):
        long_grass_bar = Grass(240 + 483 * i, 30, 16, 223, 161, 33, scale = 3.0)
        game_world.add_object(long_grass_bar, 0)
        game_world.addcollide_pairs('player:ground', None, long_grass_bar)
        game_world.addcollide_pairs('enemy:ground' , None , long_grass_bar)

    for i in range(4):
        long_grass_bar = Grass(723 + 483 * i, 200, 16, 223, 161, 33, scale = 3.0)
        game_world.add_object(long_grass_bar, 0)
        game_world.addcollide_pairs('player:ground', None, long_grass_bar)
        game_world.addcollide_pairs('enemy:ground' , None , long_grass_bar)


    global player , flash_effect , current_portal

    # 플레이어
    player = Player(16, 90)
    game_world.add_object(player, 1)
    game_world.addcollide_pairs('player:enemy',player,None)
    game_world.addcollide_pairs('player:ground',player,None)
    game_world.addcollide_pairs('player:enemy_attack',player,None)

    player_hp_bar = hpbar.Hpbar(player)
    game_world.add_object(player_hp_bar, 0)

    current_portal = Portal(1500, 100)
    game_world.add_object(current_portal, 1)  # Player와 같은 레이어

    # 🌟 [추가] 충돌 쌍 등록 (플레이어 : 포탈)
    game_world.addcollide_pairs('player:portal', player, current_portal)

    #화면 깜빡임 추가
    flash_obj = screen_effects.load(DEFINES.SCW, DEFINES.SCH)
    game_world.add_object(flash_obj, 3)

    #몬스터 추가
    enemys = [Enemy() for i in range(4)]
    game_world.add_objects(enemys, 1)

    for enemy in enemys:
        game_world.addcollide_pairs('enemy:bullet', enemy, None)
        game_world.addcollide_pairs('player:enemy', None, enemy)
        game_world.addcollide_pairs('sword:enemy' , None , enemy)
        game_world.addcollide_pairs('enemy:ground', enemy, None)

    #
    #     game_world.addcollide_pairs('enemy:bullet', None, bullet)





    _gun = Gun(player.x + 16, player.y , player)
    game_world.add_object(_gun, 1)

    player.scale = [3.0, 3.0]
    _gun.scale = [2.0, 2.0]




def update_world(dt):
    game_world.update(dt)
    game_world.handle_collision()

    if collide(player, current_portal):
        print("플레이어가 포탈에 닿았습니다! 다음 스테이지로!")
        reset_world()  # 🌟 월드를 리셋해서 (마치 새 스테이지인 것처럼) 시작
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
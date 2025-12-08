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
        if player:
            player.handle_event(event)


# 🌟 1. 움직이지 않는 배경/벽만 생성 (최초 1회)
def init_static_objects():
    server.background = Background()
    game_world.add_object(server.background, 0)  # 레이어 0번에 추가

    # 지형지물(Grass) 생성
    # (기존 reset_world에 있던 벽 생성 코드 이동)
    for i in range(7):
        long_grass_bar = Grass(240 + 483 * i, 30, 16, 223, 161, 33, scale=3.0)
        game_world.add_object(long_grass_bar, 0)  # Layer 0: 벽

        # 🌟 [중요] 충돌 그룹 이름만 등록해둠 (대상 객체는 나중에 추가될 때 연결)
        # 여기서는 벽(long_grass_bar)은 변하지 않으니 미리 충돌 그룹에 넣어둠
        # 단, 'player:ground' 같은 쌍은 player가 생길 때 add_collision_pair 해야 함.
        # 하지만 game_world 구조상, 그룹에 객체를 미리 넣어두는 방식이라면 여기서 추가.
        # 보통 add_collision_pair(group, a, b) 방식이라면 여기서 할 필요 없음.
        pass

    for i in range(7):
        long_grass_bar = Grass(723 + 483 * i, 200, 16, 223, 161, 33, scale=3.0)
        game_world.add_object(long_grass_bar, 0)


def reset_stage():
    global player, current_portal

    # 1. 움직이는 객체들 비우기
    game_world.world[1] = []
    game_world.world[2] = []
    game_world.world[3] = []

    # 2. 충돌 정보 초기화
    game_world.clear_collision_pairs()

    # 3. 객체 생성
    player = Player(16, 90)
    import server
    server.player = player
    player.scale = [3.0, 3.0]
    game_world.add_object(player, 1)

    # 포탈
    current_portal = Portal(DEFINES.SCW - 50, 100)
    game_world.add_object(current_portal, 1)

    # 몬스터
    enemys = [Enemy() for i in range(10)]
    game_world.add_objects(enemys, 1)

    # UI
    player_hp_bar = hpbar.Hpbar(player)
    game_world.add_object(player_hp_bar, 0)

    # ------------------------------------------------------
    # 🌟🌟 4. 충돌 쌍 재등록 (최적화됨) 🌟🌟
    # ------------------------------------------------------

    # (1) 벽(Grass) 등록: 벽은 한 번만 훑어서 "나는 땅이야(b)"라고만 등록
    if len(game_world.world) > 0:
        for obj in game_world.world[0]:
            if isinstance(obj, Grass):
                # None, obj -> 나는 충돌의 '오른쪽(당하는 쪽)' 이다
                game_world.addcollide_pairs('player:ground', None, obj)
                game_world.addcollide_pairs('enemy:ground', None, obj)

    # (2) 플레이어 등록
    game_world.addcollide_pairs('player:ground', player, None)
    game_world.addcollide_pairs('player:portal', player, current_portal)
    game_world.addcollide_pairs('player:enemy_attack', player, None)

    # (3) 몬스터 등록: 몬스터 루프는 따로 돌립니다.
    for enemy in enemys:
        game_world.addcollide_pairs('player:enemy', player, enemy)
        game_world.addcollide_pairs('enemy:bullet', enemy, None)
        game_world.addcollide_pairs('sword:enemy', None, enemy)

        # 🌟 여기서 enemy만 등록하면, 위 (1)번에서 등록한 벽들과 자동으로 매칭됨
        game_world.addcollide_pairs('enemy:ground', enemy, None)

    print("Stage Reset Complete.")

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

# reset_world()

init_static_objects()
reset_stage()

current_time = get_time()
while running:
    # 1. 시간 계산
    new_time = get_time()
    dt = new_time - current_time
    current_time = new_time
    DEFINES.dt = dt

    # 2. 이벤트 처리
    handle_events()  # 여기서 player.handle_event()가 호출되어 마우스 상태가 갱신됨

    # 3. 로직 처리
    if collide(player, current_portal):
        print("Next Stage!")
        reset_stage()

    # 🌟 [삭제] 이 줄을 반드시 지우거나 주석 처리하세요!
    # if mouse_state: player.fire()  <-- 이 녀석이 범인입니다.

    # 이제 player.update() 안에서 무기 상태에 따라 알아서 발사합니다.
    update_world(dt)

    clear_canvas()
    render_world()
    update_canvas()
    delay(0.01)
    # 5. 렌더링

# finalization code
close_canvas()

# 끝!
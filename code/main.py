from pico2d import *
import game_world
import DEFINES
import screen_effects
from pico2d import SDL_BUTTON_LMASK, SDL_BUTTON_LEFT

from enemy import *
from enemy2 import *
from boss import *
from Background import *
from grass import Grass
from hpbar import Hpbar
# Game object class here

from portal import Portal

current_stage = 1  # 현재 스테이지 (1부터 시작)


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

    for i in range(5):
        long_grass_bar = Grass(723 + 800 * i, 250, 16, 223, 161, 33, scale=3.0)
        game_world.add_object(long_grass_bar, 0)


def reset_stage():
    global player, current_portal, current_stage, enemys, boss

    # 1. 게임 월드 객체 비우기 (Layer 1: 객체, Layer 2: 투사체 등)
    # Layer 0(배경/바닥)은 init_static_objects에서 한 번만 생성하므로 유지
    game_world.world[1] = []
    game_world.world[2] = []
    game_world.world[3] = []  # 필요하다면 비움

    # 2. 충돌 정보 초기화
    game_world.clear_collision_pairs()

    # 3. 플레이어 생성
    player = Player(16, 90)
    import server
    server.player = player
    player.scale = [3.0, 3.0]
    game_world.add_object(player, 1)

    # UI 생성
    player_hp_bar = hpbar.Hpbar(player)
    game_world.add_object(player_hp_bar, 0)

    # 총 생성
    _gun = Gun(player.x + 16, player.y, player)
    _gun.scale = [2.0, 2.0]
    game_world.add_object(_gun, 1)

    # ------------------------------------------------------
    # 🌟🌟 스테이지별 몬스터 & 포탈 소환 🌟🌟
    # ------------------------------------------------------
    enemys = []
    current_portal = None
    boss = None

    if current_stage == 1:
        print(f"=== STAGE {current_stage} : Enemy 1 ===")
        # Enemy 1 (enemy.py) 5마리 소환
        for i in range(5):
            mob = Enemy(500 + i * 200, 90)  # 바닥 높이에 맞춰 y좌표 조정 (90~100)
            game_world.add_object(mob, 1)
            enemys.append(mob)

        # 🌟 포탈을 맵 끝(보스 위치)에 배치
        current_portal = Portal(2350, 100)
        game_world.add_object(current_portal, 1)

    elif current_stage == 2:
        print(f"=== STAGE {current_stage} : Enemy 2 ===")
        # Enemy 2 (enemy2.py) 5마리 소환
        for i in range(5):
            mob = Enemy2(500 + i * 200, 90)
            game_world.add_object(mob, 1)
            enemys.append(mob)

        # 🌟 포탈을 맵 끝에 배치
        current_portal = Portal(2350, 100)
        game_world.add_object(current_portal, 1)

    elif current_stage == 3:
        print(f"=== STAGE {current_stage} : BOSS FIGHT ===")
        # 잡몹 섞어서 소환
        mob1 = Enemy(500, 90)
        mob2 = Enemy2(700, 90)
        game_world.add_object(mob1, 1);
        enemys.append(mob1)
        game_world.add_object(mob2, 1);
        enemys.append(mob2)

        # 🌟 대망의 보스 소환!
        boss = Boss(2000, 200)
        game_world.add_object(boss, 1)

        # 마지막 스테이지는 포탈 없음 (current_portal = None)

    # ------------------------------------------------------
    # 🌟🌟 충돌 쌍 등록 🌟🌟
    # ------------------------------------------------------

    # (1) 바닥(Grass) 재등록
    if len(game_world.world) > 0:
        for obj in game_world.world[0]:
            if isinstance(obj, Grass):
                game_world.addcollide_pairs('player:ground', None, obj)
                game_world.addcollide_pairs('enemy:ground', None, obj)

    # (2) 플레이어 관련
    game_world.addcollide_pairs('player:ground', player, None)
    game_world.addcollide_pairs('player:enemy_attack', player, None)
    game_world.addcollide_pairs('player:poison', player, None)

    # (3) 포탈 (포탈이 있을 때만)
    if current_portal:
        game_world.addcollide_pairs('player:portal', player, current_portal)

    # (4) 몬스터 (Enemy, Enemy2)
    for enemy in enemys:
        game_world.addcollide_pairs('player:enemy', player, enemy)
        game_world.addcollide_pairs('enemy:bullet', enemy, None)
        game_world.addcollide_pairs('sword:enemy', None, enemy)
        game_world.addcollide_pairs('enemy:ground', enemy, None)

    # (5) 보스 (3스테이지일 때만)
    if boss:
        # 보스도 'enemy' 그룹으로 묶어서 처리
        game_world.addcollide_pairs('player:enemy', player, boss)
        game_world.addcollide_pairs('sword:enemy', None, boss)
        game_world.addcollide_pairs('enemy:bullet', boss, None)
        game_world.addcollide_pairs('enemy:ground', boss, None)  # 보스도 바닥에 서야 함

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

    print("Stage Reset Complete.")


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
    if current_portal and collide(player, current_portal):
        print("Next Stage!")
        current_stage += 1  # 스테이지 번호 증가
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
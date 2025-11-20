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
import random

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


# 🌟 1. 움직이지 않는 배경/벽만 생성 (최초 1회)
def init_static_objects():
    global bg
    bg = Background()
    game_world.add_object(bg, 0)  # Layer 0: 배경

    # 지형지물(Grass) 생성
    # (기존 reset_world에 있던 벽 생성 코드 이동)
    for i in range(4):
        long_grass_bar = Grass(240 + 483 * i, 30, 16, 223, 161, 33, scale=3.0)
        game_world.add_object(long_grass_bar, 0)  # Layer 0: 벽

        # 🌟 [중요] 충돌 그룹 이름만 등록해둠 (대상 객체는 나중에 추가될 때 연결)
        # 여기서는 벽(long_grass_bar)은 변하지 않으니 미리 충돌 그룹에 넣어둠
        # 단, 'player:ground' 같은 쌍은 player가 생길 때 add_collision_pair 해야 함.
        # 하지만 game_world 구조상, 그룹에 객체를 미리 넣어두는 방식이라면 여기서 추가.
        # 보통 add_collision_pair(group, a, b) 방식이라면 여기서 할 필요 없음.
        pass

    # for i in range(4):
    #     long_grass_bar = Grass(723 + 483 * i, 200, 16, 223, 161, 33, scale=3.0)
    #     game_world.add_object(long_grass_bar, 0)


def reset_stage():
    global player, current_portal

    # 1. 움직이는 객체들(Layer 1 이상)만 비우기
    # Layer 0 (배경, 벽)은 건드리지 않음!
    if len(game_world.world) > 1:
        game_world.world[1] = []
    if len(game_world.world) > 2:
        game_world.world[2] = []
    if len(game_world.world) > 3:
        game_world.world[3] = []

    # 🌟🌟 2. 충돌 정보 싹 비우기 🌟🌟
    # 이걸 안 하면 이전 스테이지 몬스터 정보가 남아서 에러 남
    game_world.clear_collision_pairs()

    generated_platforms = []

    # 발판의 대략적인 크기 (스케일 3.0 고려)
    # Grass 생성자: Grass(x, y, 16, 223, 161, 33, scale=3.0)
    # 실제 너비 = 161 * 3.0 = 483, 실제 높이 = 33 * 3.0 = 99
    PLATFORM_WIDTH = 400
    PLATFORM_HEIGHT = 99

    # 🌟 발판 사이에 최소한 이만큼은 떨어져야 한다! (간격)
    MARGIN = 80

    attempts = 0
    max_attempts = 100  # 100번 시도해도 자리 없으면 포기

    # 목표는 5개지만, 공간이 좁으면 들어가는 만큼만 넣음
    while len(generated_platforms) < 5 and attempts < max_attempts:
        attempts += 1

        # 1. 랜덤 위치 뽑기
        # 발판이 맵 밖으로 튀어나가지 않게 범위를 살짝 줄임
        rx = random.randint(200, 1600)
        ry = random.randint(200, 300)

        # 2. 기존 발판들과 거리 체크 (충돌 + 간격)
        is_too_close = False
        for p in generated_platforms:
            # 기존 발판 p의 좌표
            px, py = p.x, p.y

            # 🌟 [핵심] 두 발판 사이의 거리(절댓값)가 (발판크기 + 마진)보다 작으면 겹친 거임
            # X축 거리 체크: (내 너비 절반 + 쟤 너비 절반 + 여유공간)
            # 간단하게: 두 중심점 사이의 거리가 '너비 + 여유'보다 작으면 겹침
            if abs(rx - px) < (PLATFORM_WIDTH + MARGIN) and \
                    abs(ry - py) < (PLATFORM_HEIGHT + MARGIN):
                is_too_close = True
                break  # 겹침 발생! 다시 뽑자

        # 3. 통과했으면 생성
        if not is_too_close:
            new_grass = Grass(rx, ry, 16, 223, 161, 33, scale=3.0)
            game_world.add_object(new_grass, 1)
            generated_platforms.append(new_grass)
            # print(f"발판 {len(generated_platforms)} 생성 완료: {rx}, {ry}")

    # (디버그용) 만약 5개를 다 못 채웠으면 알려줌
    if len(generated_platforms) < 5:
        print(f"공간 부족으로 발판이 {len(generated_platforms)}개만 생성되었습니다.")
    # ------------------------------------------------------
    # 3. 플레이어 생성 및 총 등록
    # ------------------------------------------------------
    player = Player(16, 90)
    player.scale = [3.0, 3.0]
    game_world.add_object(player, 1)
    game_world.add_object(player.gun, 1)  # 플레이어가 가진 총 등록

    # ------------------------------------------------------
    # 4. 포탈 및 몬스터 생성
    # ------------------------------------------------------
    current_portal = Portal(DEFINES.SCW - 50, 100)
    game_world.add_object(current_portal, 1)

    enemys = [Enemy() for i in range(10)]
    game_world.add_objects(enemys, 1)

    # ------------------------------------------------------
    # 5. UI 생성
    # ------------------------------------------------------
    player_hp_bar = hpbar.Hpbar(player)
    game_world.add_object(player_hp_bar, 0)

    # ------------------------------------------------------
    # 6. 충돌 쌍 재등록 (여기가 제일 중요!)
    # ------------------------------------------------------
    all_grounds = []
    if len(game_world.world) > 0:
        all_grounds += [obj for obj in game_world.world[0] if isinstance(obj, Grass)]
    if len(game_world.world) > 1:
        all_grounds += [obj for obj in game_world.world[1] if isinstance(obj, Grass)]

    # 🌟 [디버깅] 실제로 바닥이 몇 개 잡혔는지 확인해보세요 (콘솔 출력)
    print(f"충돌 등록된 바닥 개수: {len(all_grounds)}")

    # 2) 'player:ground' 그룹 등록 (핵심 수정!)
    # 플레이어는 딱 1번만 등록합니다 (그룹의 A 리스트)
    game_world.addcollide_pairs('player:ground', player, None)

    # 바닥들은 루프 돌면서 등록합니다 (그룹의 B 리스트)
    for ground in all_grounds:
        game_world.addcollide_pairs('player:ground', None, ground)

        # 몬스터와 바닥 충돌도 마찬가지로 등록
        for enemy in enemys:
            game_world.addcollide_pairs('enemy:ground', enemy, ground)

    # 3) 나머지 충돌 등록 (기존과 동일)
    for enemy in enemys:
        game_world.addcollide_pairs('player:enemy', player, enemy)
        game_world.addcollide_pairs('enemy:bullet', enemy, None)
        game_world.addcollide_pairs('sword:enemy', None, enemy)
        game_world.addcollide_pairs('player:enemy_attack', player, None)

        # 🌟 몬스터도 바닥에 서야 하므로, 몬스터 그룹(A) 등록
        game_world.addcollide_pairs('enemy:ground', enemy, None)

    # 4) 포탈
    game_world.addcollide_pairs('player:portal', player, current_portal)


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
    # 1. Delta Time (dt) 계산
    new_time = get_time()
    dt = new_time - current_time
    current_time = new_time
    DEFINES.dt = dt

    # 2. 이벤트 처리 (키보드, 마우스 위치)
    handle_events()

    # 🌟 3. '상태' 폴링 (Polling) 및 로직 처리
    # 마우스 왼쪽 버튼이 '눌려있는지' main에서 직접 확인
    if collide(player, current_portal):
        print("Next Stage!")
        reset_stage()  # 🌟 벽은 그대로 두고 플레이어/몬스터만 리셋!
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
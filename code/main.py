from pico2d import *


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
    global running

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        else:
            boy.handle_evnet(event)



def reset_world():
    global world
    global boy

    world = []

    grass = Grass()
    world.append(grass)

    boy = Boy()
    world.append(boy)

    enemy = Enemy(500,90)
    world.append(enemy)


def update_world():
    # 1. 월드 내 모든 객체 업데이트
    for o in world:
        o.update()

    # 2. 충돌 처리
    enemies = [o for o in world if isinstance(o, Enemy)]

    # 2-1: 모든 공격 이펙트와 모든 적을 비교
    for effect in boy.effects:
        for enemy in enemies:

            # 🌟 3. 충돌 발생 여부 확인
            if collide(effect, enemy):

                # 🌟 4. 이 이펙트가 '처음' 타격하는 적인지 확인
                if enemy not in effect.hit_enemies:

                    # 🌟 5. 타격 처리 (처음 맞는 경우)
                    print(f"NEW HIT! Enemy {id(enemy)} HIT!")

                    # 5-1. 적의 HP 감소
                    enemy.hp -= 10  # (예: 10 데미지)

                    # 5-2. 이펙트의 '타격한 적 리스트'에 이 적을 추가 (중복 타격 방지)
                    effect.hit_enemies.add(enemy)

                    # 5-3. 적 사망 처리
                    if enemy.hp <= 0:
                        if enemy in world:
                            world.remove(enemy)


def render_world():
    clear_canvas()
    for o in world:
        o.draw()
    update_canvas()


running = True

open_canvas(1280,720)
from boy import Boy
from grass import Grass
from enemy import Enemy
import hpbar # 🌟 1. HP 바 시스템 임포트
hpbar.load_images()
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
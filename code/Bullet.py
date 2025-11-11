from pico2d import *
import math
import DEFINES
import game_world
class Bullet:
    def __init__(self, x, y, angle, speed=800, owner=None, damage=10):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.owner = owner
        self.damage = damage
        self.image = load_image('resource/Sprites/GunsPack/Bullets/RifleAmmoSmall.png')
        self.alive = True
        self.hit_enemies = set()
        self.bounce_count = 0
    def update(self, dt):
        if not self.alive:
            game_world.remove_object(self)
            game_world.remove_colision_object(self)
        self.x += self.vx * dt
        self.y += self.vy * dt
        # 화면 밖이면 제거 플래그
        if self.x < 0 or self.x > DEFINES.SCW:
            if self.bounce_count == 0:
                self.vx *= -1  # X속도 반전
                self.bounce_count = 1
                # 🌟 화면 밖으로 나가지 않도록 위치 보정
                self.x = 0 if self.x < 0 else DEFINES.SCW
                print('총알 좌/우 1회 튕김')
            elif self.alive:
                print('총알 좌/우 2회 충돌, 삭제')
                self.alive = False
                return  #

            # 상단 경계 (Y)
        if self.y > DEFINES.SCH:
            if self.bounce_count == 0:
                self.vy *= -1  # Y속도 반전
                self.bounce_count = 1
                self.y = DEFINES.SCH  # 위치 보정
                print('총알 상단 1회 튕김')
            elif self.alive:
                print('총알 상단 2회 충돌, 삭제')
                self.alive = False
                return

            # 3. 소멸 영역 (화면 하단 또는 너무 멀리 나간 경우)
        if self.y < -100 or self.x < -100 or self.x > DEFINES.SCW + 100:
            if self.alive:
                print('총알 화면 밖 이탈 (소멸 영역)')
                self.alive = False



    def draw(self):
        if self.alive:
            self.image.draw(self.x, self.y)
            draw_rectangle(*self.get_bb())



    def get_bb(self):
        half = 6
        return self.x - half, self.y - half, self.x + half, self.y + half

    def handle_collision(self, group, other):
        if group == 'enemy:bullet':
            print('총알에 몬스터 맞아서 볼 삭제')
            game_world.remove_object(self)
            game_world.remove_colision_object(self)
        elif group == 'bullet:wall':
            # 1. 첫 번째 바운스인 경우
            if self.bounce_count == 0:
                print('총알 벽에 1회 튕김')
                self.bounce_count = 1  # 횟수 증가

                # 2. AABB 겹침(overlap) 계산으로 튕길 방향 결정
                a_bb = self.get_bb()
                b_bb = other.get_bb()

                # X축 겹침 (좌우 겹침)
                overlap_x = min(a_bb[2], b_bb[2]) - max(a_bb[0], b_bb[0])
                # Y축 겹침 (상하 겹침)
                overlap_y = min(a_bb[3], b_bb[3]) - max(a_bb[1], b_bb[1])

                # 3. 겹친 영역이 더 '좁은' 쪽의 속도를 반전시킴
                if overlap_x < overlap_y:
                    # 좌우로 더 좁게 겹침 -> 좌우 벽에 부딪힘
                    self.vx *= -1
                else:
                    # 상하로 더 좁게 겹침 -> 상하 벽에 부딪힘
                    self.vy *= -1
            # 2. 이미 튕긴 적이 있는 경우 (두 번째 충돌)
            else:
                print('총알이 벽에 두 번째 맞아 삭제됨')
                self.alive = False  # 🌟 총알 제거


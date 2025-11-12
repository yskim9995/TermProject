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

        # 🌟 1. 총알 크기 변수 추가 (예: 24x24)
        self.draw_width = 48
        self.draw_height = 48

    def update(self, dt):
        # 🌟 2. [수정] self.alive가 False이면,
        #    객체를 제거하고 'update'를 즉시 중단(return)합니다.
        if not self.alive:
            game_world.remove_object(self)
            game_world.remove_colision_object(self)
            return  # 👈 중요: 즉시 종료

        self.x += self.vx * dt
        self.y += self.vy * dt

        bounced = False
        if self.x < 0 or self.x > DEFINES.SCW:
            if self.bounce_count == 0:
                self.vx *= -1
                self.bounce_count = 1
                self.x = 0 if self.x < 0 else DEFINES.SCW
                bounced = True
                print('총알 좌/우 1회 튕김')
            elif self.alive:
                print('총알 좌/우 2회 충돌, 삭제')
                self.alive = False
                return

        if self.y > DEFINES.SCH:
            if self.bounce_count == 0:
                self.vy *= -1
                self.bounce_count = 1
                self.y = DEFINES.SCH
                print('총알 상단 1회 튕김')
                bounced = True
            elif self.alive:
                print('총알 상단 2회 충돌, 삭제')
                self.alive = False
                return
        if bounced:
            self.angle = math.atan2(self.vy, self.vx)

        if self.y < -100 or self.x < -100 or self.x > DEFINES.SCW + 100:
            if self.alive:
                print('총알 화면 밖 이탈 (소멸 영역)')
                self.alive = False

    def draw(self):
        if self.alive:
            self.image.rotate_draw(self.angle,
                                   self.x, self.y,
                                   self.draw_width, self.draw_height)

            if DEFINES.bbvisible:
                draw_rectangle(*self.get_bb())

    def get_bb(self):
        # 🌟 4. [수정] 하드코딩된 '6' 대신 변수를 사용합니다.
        half_w = self.draw_width / 4
        half_h = self.draw_height / 4
        return self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h

    def handle_collision(self, group, other):
        # 🌟 5. [수정] 충돌 시 객체를 바로 제거하지 않고,
        #    'self.alive = False' 플래그만 설정합니다. (제거는 update가 담당)

        if group == 'enemy:bullet':
            if self.alive:  # 👈 중복 충돌 방지
                print('총알에 몬스터 맞아서 볼 삭제')
                self.alive = False

        elif group == 'bullet:wall':
            if self.bounce_count == 0:
                print('총알 벽에 1회 튕김')
                self.bounce_count = 1

                a_bb = self.get_bb()
                b_bb = other.get_bb()
                overlap_x = min(a_bb[2], b_bb[2]) - max(a_bb[0], b_bb[0])
                overlap_y = min(a_bb[3], b_bb[3]) - max(a_bb[1], b_bb[1])

                if overlap_x < overlap_y:
                    self.vx *= -1
                else:
                    self.vy *= -1
            else:
                if self.alive:  # 👈 중복 충돌 방지
                    print('총알이 벽에 두 번째 맞아 삭제됨')
                    self.alive = False
from pico2d import *
import math
import DEFINES
import game_world
import server


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
        self.draw_width = 48
        self.draw_height = 48

    def update(self, dt):
        if not self.alive:
            game_world.remove_object(self)
            return

        # 1. 일단 이동 (월드 좌표 기준)
        self.x += self.vx * dt
        self.y += self.vy * dt

        # 2. 현재 화면상에서의 위치(sx, sy) 계산
        #    이 값을 기준으로 화면 밖으로 나갔는지 판별합니다.
        sx, sy = server.world_to_screen(self.x, self.y)

        bounced = False

        # ---------------------------------------------------------
        # 🌟 화면 좌우 경계 판정 (0 ~ DEFINES.SCW)
        # ---------------------------------------------------------
        if sx < 0 or sx > DEFINES.SCW:
            if self.bounce_count == 0:
                self.vx *= -1
                self.bounce_count = 1
                bounced = True
                print('화면 좌우 튕김')

                # [위치 보정] 총알이 화면 밖으로 파고들지 않게 밀어넣기
                # 원리: sx(화면좌표)가 벗어난 만큼 월드좌표(self.x)를 반대로 밈
                if sx < 0:
                    self.x -= sx  # sx가 음수이므로 빼면(+) 안으로 들어옴
                else:
                    self.x -= (sx - DEFINES.SCW)  # 초과분만큼 뺌

            elif self.alive:
                print('화면 좌우 2회 충돌 -> 삭제')
                self.alive = False
                return

        # ---------------------------------------------------------
        # 🌟 화면 상하 경계 판정 (0 ~ DEFINES.SCH)
        # ---------------------------------------------------------
        if sy < 0 or sy > DEFINES.SCH:
            if self.bounce_count == 0:
                self.vy *= -1
                self.bounce_count = 1
                bounced = True
                print('화면 상하 튕김')

                # [위치 보정]
                if sy < 0:
                    self.y -= sy
                else:
                    self.y -= (sy - DEFINES.SCH)

            elif self.alive:
                print('화면 상하 2회 충돌 -> 삭제')
                self.alive = False
                return

        # 튕겼으면 각도 재계산 (이미지 회전용)
        if bounced:
            self.angle = math.atan2(self.vy, self.vx)

        # (안전장치) 혹시 화면 로직이 뚫려서 맵 밖으로 영원히 날아가면 삭제
        # 필요 없으면 지워도 됩니다.
        if self.x < -1000 or self.x > 5000:  # 맵 크기에 따라 대충 크게 잡음
            self.alive = False

    def draw(self):
        if self.alive:
            # 그릴 때도 화면 좌표 변환
            sx, sy = server.world_to_screen(self.x, self.y)

            # 화면 안에 있거나 근처일 때만 그림
            if -50 < sx < DEFINES.SCW + 50 and -50 < sy < DEFINES.SCH + 50:
                self.image.rotate_draw(self.angle, sx, sy, self.draw_width, self.draw_height)

                if DEFINES.bbvisible:
                    # BB 그리기 (디버그)
                    l, b, r, t = self.get_bb()
                    sl, sb = server.world_to_screen(l, b)
                    sr, st = server.world_to_screen(r, t)
                    draw_rectangle(sl, sb, sr, st)

    def get_bb(self):
        half_w = self.draw_width / 4
        half_h = self.draw_height / 4
        return self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h

    def handle_collision(self, group, other):
        if group == 'enemy:bullet':
            if self.alive:
                self.alive = False
        # 벽 충돌(bullet:wall)은 맵상의 장애물(박스 등)과의 충돌일 테니 유지
        elif group == 'bullet:wall':
            # ... 기존 벽 충돌 코드 ...
            pass
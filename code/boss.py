from pico2d import *
import game_world
import server
import random
import math
import DEFINES
from state_machine import StateMachine


# -------------------------------------------------------------------------
# 1. 오로라 이펙트 (Attack 3)
# -------------------------------------------------------------------------
class AuroraEffect:
    image = None

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.lifetime = 1.5  # 1.5초 지속
        self.spawn_time = get_time()
        self.damage = 30  # 데미지
        self.warning_time = 0.5  # 0.5초 동안은 공격 판정 없음 (예고)

        if AuroraEffect.image is None:
            try:
                # 레이저 이미지를 오로라처럼 사용 (세로로 길게)
                AuroraEffect.image = load_image('resource/Sprites/GunsPack/effect/Laser_0.png')
            except:
                pass

    def update(self, dt):
        if get_time() - self.spawn_time > self.lifetime:
            game_world.remove_object(self)

    def draw(self):
        sx, sy = server.world_to_screen(self.x, self.y)

        elapsed = get_time() - self.spawn_time

        # 예고 시간 동안은 투명하게 깜빡임
        if elapsed < self.warning_time:
            if int(elapsed * 20) % 2 == 0:  # 깜빡깜빡
                draw_rectangle(sx - 50, sy - 400, sx + 50, sy + 400)  # 경고 박스
        else:
            # 실제 공격 (이미지 그리기)
            if AuroraEffect.image:
                # 90도 회전해서 세로로 세움, 크기(600x100)
                AuroraEffect.image.rotate_draw(math.pi / 2, sx, sy, 800, 150)

            if DEFINES.bbvisible:
                draw_rectangle(*self.get_bb())

    def get_bb(self):
        # 예고 시간엔 충돌 없음
        if get_time() - self.spawn_time < self.warning_time:
            return 0, 0, 0, 0
        return self.x - 75, self.y - 400, self.x + 75, self.y + 400

    def handle_collision(self, group, other):
        pass


# -------------------------------------------------------------------------
# 2. 보스 독구름 (Attack 2)
# -------------------------------------------------------------------------
class BossPoison:
    image = None

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.lifetime = 5.0  # 5초 지속 (김)
        self.spawn_time = get_time()
        self.damage = 2
        self.scale = 4.0  # 크기 4배

        self.frame = 0
        self.frame_time = 0.0
        self.total_frames = 10

        if BossPoison.image is None:
            try:
                BossPoison.image = load_image('resource/Sprites/GunsPack/effect/poison_sheet.png')
            except:
                pass

        if BossPoison.image:
            self.sprite_width = BossPoison.image.w // self.total_frames
            self.sprite_height = BossPoison.image.h
        else:
            self.sprite_width = 0
            self.sprite_height = 0

    def update(self, dt):
        if get_time() - self.spawn_time > self.lifetime:
            game_world.remove_object(self)
            return

        self.frame_time += dt
        if self.frame_time >= 0.1:
            self.frame_time = 0
            self.frame = (self.frame + 1) % self.total_frames

    def draw(self):
        if BossPoison.image is None: return
        sx, sy = server.world_to_screen(self.x, self.y)
        left = self.frame * self.sprite_width

        BossPoison.image.clip_draw(left, 0, self.sprite_width, self.sprite_height,
                                   sx, sy, 64 * self.scale, 64 * self.scale)

        if DEFINES.bbvisible: draw_rectangle(*self.get_bb())

    def get_bb(self):
        size = 40 * self.scale
        return self.x - size, self.y - size, self.x + size, self.y + size

    def handle_collision(self, group, other):
        pass


# -------------------------------------------------------------------------
# 3. 보스 스매시 (Attack 1 - 근접)
# -------------------------------------------------------------------------
class BossSmash:
    def __init__(self, x, y, face_dir):
        self.x, self.y = x, y
        self.face_dir = face_dir
        self.exist_time = 0.0
        self.LIFETIME = 0.3
        self.damage = 20
        self.width = 200  # 범위 넓음
        self.height = 200

    def update(self, dt):
        self.exist_time += dt
        if self.exist_time >= self.LIFETIME: game_world.remove_object(self)

    def draw(self):
        if DEFINES.bbvisible:
            l, b, r, t = self.get_bb()
            sl, sb = server.world_to_screen(l, b)
            sr, st = server.world_to_screen(r, t)
            draw_rectangle(sl, sb, sr, st)

    def get_bb(self):
        # 보스 앞쪽으로 충돌 박스 생성
        offset_x = 100 * self.face_dir
        return self.x + offset_x - self.width // 2, self.y - self.height // 2, \
               self.x + offset_x + self.width // 2, self.y + self.height // 2

    def handle_collision(self, group, other):
        if group == 'player:enemy_attack': game_world.remove_object(self)


# ... (상단 이펙트 클래스들은 그대로 두세요) ...

# -------------------------------------------------------------------------
# 보스 상태 클래스들 (Enemy1, 2 스타일로 draw 개별 구현)
# -------------------------------------------------------------------------

# 이벤트 정의
def time_out(e): return e[0] == 'TIME_OUT'


def hit(e): return e[0] == 'HIT'


def dead(e): return e[0] == 'DEAD'


def detect_player(e): return e[0] == 'DETECT'


def reach_attack_range(e): return e[0] == 'ATTACK_RANGE'


def attack_1(e): return e[0] == 'ATTACK_1'


def attack_2(e): return e[0] == 'ATTACK_2'


def attack_3(e): return e[0] == 'ATTACK_3'


class Idle:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        self.boss.frame = 0
        self.boss.wait_time = get_time()

    def exit(self, e):
        pass

    def do(self, dt):
        if get_time() - self.boss.wait_time > 0.1:
            self.boss.state_machine.handle_state_event(('DETECT', None))

    # 🌟 Enemy처럼 개별 draw 구현
    def draw(self):
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)

        # 🌟 여기서 사용할 스프라이트 행(Row) 선택 가능
        # 예: 0번째 줄 사용 (32 * 0)
        BOTTOM_ROW = 0
        frame_x = self.boss.frame * 32

        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(frame_x, BOTTOM_ROW, 32, 32, sx, sy, 32 * self.boss.scale[0],
                                      32 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(frame_x, BOTTOM_ROW, 32, 32, 0, 'h', sx, sy, 32 * self.boss.scale[0],
                                                32 * self.boss.scale[1])


class Trace:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        self.boss.frame = 0
        self.frame_time = 0

    def exit(self, e):
        pass

    def do(self, dt):
        # 애니메이션
        self.frame_time += dt
        if self.frame_time >= 0.1:
            self.frame_time = 0
            self.boss.frame = (self.boss.frame + 1) % 8

        # 추격 로직
        if self.boss.target:
            dist = math.sqrt((self.boss.x - self.boss.target.x) ** 2 + (self.boss.y - self.boss.target.y) ** 2)
            self.boss.dir = 1 if self.boss.target.x > self.boss.x else -1
            self.boss.face_dir = self.boss.dir
            self.boss.x += self.boss.dir * self.boss.speed * dt

            if dist <= 200:
                self.boss.state_machine.handle_state_event(('ATTACK_RANGE', None))

    # 🌟 Enemy처럼 개별 draw 구현
    def draw(self):
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)

        # 🌟 이동 모션은 다른 줄을 쓰고 싶다면 여기서 변경 (예: 32 * 1)
        # 지금은 이미지가 한 줄이라 가정하고 0 사용
        BOTTOM_ROW = 0
        frame_x = self.boss.frame * 32

        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(frame_x, BOTTOM_ROW, 32, 32, sx, sy, 32 * self.boss.scale[0],
                                      32 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(frame_x, BOTTOM_ROW, 32, 32, 0, 'h', sx, sy, 32 * self.boss.scale[0],
                                                32 * self.boss.scale[1])


class DecideAttack:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        choice = random.randint(1, 3)
        if choice == 1:
            self.boss.state_machine.handle_state_event(('ATTACK_1', None))
        elif choice == 2:
            self.boss.state_machine.handle_state_event(('ATTACK_2', None))
        else:
            self.boss.state_machine.handle_state_event(('ATTACK_3', None))

    def exit(self, e):
        pass

    def do(self, dt):
        pass

    def draw(self):
        # 결정 순간은 아주 짧으므로 Idle과 동일하게 그림
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        self.boss.image.clip_draw(0, 0, 32, 32, sx, sy, 32 * self.boss.scale[0], 32 * self.boss.scale[1])


class Attack1:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        self.boss.frame = 0
        self.timer = 0
        self.attacked = False

    def exit(self, e):
        pass

    def do(self, dt):
        self.timer += dt
        if self.timer > 0.5 and not self.attacked:
            smash = BossSmash(self.boss.x, self.boss.y, self.boss.face_dir)
            game_world.add_object(smash, 2)
            game_world.addcollide_pairs('player:enemy_attack', None, smash)
            self.attacked = True
        if self.timer > 1.0:
            self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        # 공격 모션이 있다면 행 변경 (예: 32 * 2)
        BOTTOM_ROW = 0
        frame_x = self.boss.frame * 32

        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(frame_x, BOTTOM_ROW, 32, 32, sx, sy, 32 * self.boss.scale[0],
                                      32 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(frame_x, BOTTOM_ROW, 32, 32, 0, 'h', sx, sy, 32 * self.boss.scale[0],
                                                32 * self.boss.scale[1])


class Attack2:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        self.boss.frame = 0
        self.timer = 0
        self.attacked = False

    def exit(self, e):
        pass

    def do(self, dt):
        self.timer += dt
        if self.timer > 0.3 and not self.attacked:
            poison = BossPoison(self.boss.x, self.boss.y)
            game_world.add_object(poison, 2)
            game_world.addcollide_pairs('player:poison', None, poison)
            self.attacked = True
        if self.timer > 1.0:
            self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        # Attack1과 동일 구조 (필요시 모션 변경)
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        BOTTOM_ROW = 0
        frame_x = self.boss.frame * 32
        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(frame_x, BOTTOM_ROW, 32, 32, sx, sy, 32 * self.boss.scale[0],
                                      32 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(frame_x, BOTTOM_ROW, 32, 32, 0, 'h', sx, sy, 32 * self.boss.scale[0],
                                                32 * self.boss.scale[1])


class Attack3:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        self.boss.frame = 0
        self.timer = 0
        self.attacked = False

    def exit(self, e):
        pass

    def do(self, dt):
        self.timer += dt
        if self.timer > 0.5 and not self.attacked:
            target_x = self.boss.target.x if self.boss.target else self.boss.x + 150 * self.boss.face_dir
            aurora = AuroraEffect(target_x, self.boss.y)
            game_world.add_object(aurora, 3)
            game_world.addcollide_pairs('player:enemy_attack', None, aurora)
            self.attacked = True
        if self.timer > 2.0:
            self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        # Attack1과 동일 구조
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        BOTTOM_ROW = 0
        frame_x = self.boss.frame * 32
        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(frame_x, BOTTOM_ROW, 32, 32, sx, sy, 32 * self.boss.scale[0],
                                      32 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(frame_x, BOTTOM_ROW, 32, 32, 0, 'h', sx, sy, 32 * self.boss.scale[0],
                                                32 * self.boss.scale[1])


class Hit:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        self.timer = 0

    def exit(self, e):
        pass

    def do(self, dt):
        self.timer += dt
        if self.timer > 0.2: self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        # 피격 시 보통 0번 프레임 사용
        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(0, 0, 32, 32, sx, sy, 32 * self.boss.scale[0], 32 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(0, 0, 32, 32, 0, 'h', sx, sy, 32 * self.boss.scale[0],
                                                32 * self.boss.scale[1])


class Die:
    def __init__(self, boss): self.boss = boss

    def enter(self, e):
        print("BOSS DEFEATED!")
        game_world.remove_object(self.boss)

    def exit(self, e): pass

    def do(self, dt): pass

    def draw(self): pass


# -------------------------------------------------------------------------
# Boss Main Class
# -------------------------------------------------------------------------
class Boss:
    image = None
    hp_bg = None
    hp_fg = None

    def __init__(self, x=1500, y=150):
        self.x, self.y = x, y
        self.scale = [5.0, 5.0]
        self.speed = 80.0
        self.max_hp = 1000
        self.hp = self.max_hp
        self.face_dir = -1
        self.dir = 0
        self.frame = 0  # 프레임 관리

        self.width = 32
        self.height = 32

        self.target = None

        if Boss.image is None:
            try:
                Boss.image = load_image('resource/Sprites/Free Mushrooms/Mushroom_spike.png')
            except:
                Boss.image = load_image('resource/Sprites/Free Mushrooms/Mushroom_Reg.png')

            Boss.hp_bg = load_image('resource/Sprites/Free Mushrooms/btl_gage_hp_back.png')
            Boss.hp_fg = load_image('resource/Sprites/Free Mushrooms/btl_gage_hp.png')

        self.IDLE = Idle(self)
        self.TRACE = Trace(self)
        self.DECIDE = DecideAttack(self)
        self.ATTACK1 = Attack1(self)
        self.ATTACK2 = Attack2(self)
        self.ATTACK3 = Attack3(self)
        self.HIT = Hit(self)
        self.DIE = Die(self)

        self.state_machine = StateMachine(self.IDLE, {
            self.IDLE: {detect_player: self.TRACE, hit: self.HIT, dead: self.DIE},
            self.TRACE: {reach_attack_range: self.DECIDE, hit: self.HIT, dead: self.DIE},
            self.DECIDE: {attack_1: self.ATTACK1, attack_2: self.ATTACK2, attack_3: self.ATTACK3, hit: self.HIT,
                          dead: self.DIE},
            self.ATTACK1: {time_out: self.TRACE, hit: self.HIT, dead: self.DIE},
            self.ATTACK2: {time_out: self.TRACE, hit: self.HIT, dead: self.DIE},
            self.ATTACK3: {time_out: self.TRACE, hit: self.HIT, dead: self.DIE},
            self.HIT: {time_out: self.TRACE, dead: self.DIE},
            self.DIE: {}
        })

    def update(self, dt):
        if self.target is None:
            if server.player: self.target = server.player
        self.state_machine.update(dt)

    def draw(self):
        self.state_machine.draw()  # 🌟 이제 각 상태의 draw()가 호출됨
        self.draw_hp()
        if DEFINES.bbvisible:
            l, b, r, t = self.get_bb()
            sl, sb = server.world_to_screen(l, b)
            sr, st = server.world_to_screen(r, t)
            draw_rectangle(sl, sb, sr, st)

    # 🌟 draw_generic 함수 삭제함 (이제 각 상태가 직접 그림)

    def draw_hp(self):
        sx, sy = server.world_to_screen(self.x, self.y)
        ratio = clamp(0, self.hp / self.max_hp, 1)
        w, h = 128, 16
        y_off = 60 * self.scale[1]
        Boss.hp_bg.draw_to_origin(sx - w // 2, sy + y_off, w, h)
        Boss.hp_fg.draw_to_origin(sx - w // 2, sy + y_off, w * ratio, h)

    def get_bb(self):
        w = 20 * self.scale[0]
        h = 32 * self.scale[1]
        return self.x - w, self.y - h / 2, self.x + w, self.y + h / 2

    def handle_collision(self, group, other):
        if group == 'enemy:bullet' or group == 'sword:enemy':
            self.hp -= other.damage
            if self.hp > 0:
                self.state_machine.handle_state_event(('HIT', None))
            else:
                self.state_machine.handle_state_event(('DEAD', None))
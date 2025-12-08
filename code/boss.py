from pico2d import *
import game_world
import server
import random
import math
import DEFINES
from state_machine import StateMachine


# 기존 공격 효과들 임포트 (파일명을 맞춰주세요)
# 만약 enemy.py, enemy2.py에 클래스가 있다면 import해서 써도 됩니다.
# 여기서는 보스 전용으로 조금 더 크게 새로 정의했습니다.

# -------------------------------------------------------------------------
# 1. 오로라 이펙트 (보스 전용 필살기)
# -------------------------------------------------------------------------
class AuroraEffect:
    image = None

    def __init__(self, x, y, owner):
        self.x, self.y = x, y
        self.owner = owner
        self.lifetime = 2.0  # 2초간 지속
        self.spawn_time = get_time()
        self.damage = 50  # 강력한 데미지

        # 오로라 이미지가 없으면 임시로 레일건 빔 등을 크게 사용
        if AuroraEffect.image is None:
            try:
                # 🌟 오로라 이미지 (세로로 긴 빔 추천)
                AuroraEffect.image = load_image('resource/Sprites/GunsPack/effect/Laser_0.png')
            except:
                pass

    def update(self, dt):
        if get_time() - self.spawn_time > self.lifetime:
            game_world.remove_object(self)

    def draw(self):
        sx, sy = server.world_to_screen(self.x, self.y)
        # 🌟 거대한 세로 빔 (폭 100, 높이 600)
        # 빔이 위아래로 일렁이게 하려면 random을 섞을 수도 있음
        if AuroraEffect.image:
            # 회전 90도(수직)
            AuroraEffect.image.rotate_draw(math.pi / 2, sx, sy, 600, 150)

        if DEFINES.bbvisible:
            draw_rectangle(*self.get_bb())

    def get_bb(self):
        # 빔의 범위
        return self.x - 75, self.y - 300, self.x + 75, self.y + 300

    def handle_collision(self, group, other):
        pass


# -------------------------------------------------------------------------
# 2. 보스 독구름 (Enemy2보다 더 크고 오래감)
# -------------------------------------------------------------------------
class BossPoison:
    image = None

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.lifetime = 4.0
        self.spawn_time = get_time()
        self.damage = 2
        self.scale = 3.0  # 엄청 큼
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
        BossPoison.image.clip_draw(left, 0, self.sprite_width, self.sprite_height, sx, sy, 64 * self.scale,
                                   64 * self.scale)
        if DEFINES.bbvisible: draw_rectangle(*self.get_bb())

    def get_bb(self):
        size = 40 * self.scale
        return self.x - size, self.y - size, self.x + size, self.y + size

    def handle_collision(self, group, other):
        pass


# -------------------------------------------------------------------------
# 3. 보스 근접 공격 (Enemy1 스타일)
# -------------------------------------------------------------------------
class BossSmash:
    def __init__(self, x, y, face_dir):
        self.x, self.y = x, y
        self.face_dir = face_dir
        self.exist_time = 0.0
        self.LIFETIME = 0.3
        self.damage = 20
        self.width = 150  # 범위 큼
        self.height = 150

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
        offset_x = 80 * self.face_dir
        return self.x + offset_x - self.width // 2, self.y - self.height // 2, self.x + offset_x + self.width // 2, self.y + self.height // 2

    def handle_collision(self, group, other):
        if group == 'player:enemy_attack': game_world.remove_object(self)


# -------------------------------------------------------------------------
# 보스 상태 클래스들
# -------------------------------------------------------------------------
# 이벤트 정의
def time_out(e): return e[0] == 'TIME_OUT'


def hit(e): return e[0] == 'HIT'


def dead(e): return e[0] == 'DEAD'


def detect_player(e): return e[0] == 'DETECT'


def reach_attack_range(e): return e[0] == 'ATTACK_RANGE'


# 공격 타입 이벤트
def attack_1(e): return e[0] == 'ATTACK_1'  # 근접


def attack_2(e): return e[0] == 'ATTACK_2'  # 독


def attack_3(e): return e[0] == 'ATTACK_3'  # 오로라


class Idle:
    def __init__(self, boss): self.boss = boss

    def enter(self, e):
        self.boss.frame = 0
        self.boss.wait_time = get_time()

    def exit(self, e): pass

    def do(self, dt):
        # 보스는 쉬지 않고 플레이어를 찾음
        if get_time() - self.boss.wait_time > 1.0:
            self.boss.state_machine.handle_state_event(('DETECT', None))

    def draw(self): self.boss.draw_generic()


class Trace:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        self.boss.frame = 0

    def exit(self, e):
        pass

    def do(self, dt):
        # 플레이어 추격
        if self.boss.target:
            dist = math.sqrt((self.boss.x - self.boss.target.x) ** 2 + (self.boss.y - self.boss.target.y) ** 2)
            self.boss.dir = 1 if self.boss.target.x > self.boss.x else -1
            self.boss.face_dir = self.boss.dir
            self.boss.x += self.boss.dir * self.boss.speed * dt

            # 공격 범위(150px) 안에 들어오면 패턴 결정
            if dist <= 150:
                self.boss.state_machine.handle_state_event(('ATTACK_RANGE', None))

    def draw(self):
        self.boss.draw_generic()


class DecideAttack:
    # 🌟 어떤 공격을 할지 랜덤으로 고르는 찰나의 순간
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        # 1: 근접, 2: 독, 3: 오로라
        choice = random.randint(1, 3)
        print(f"Boss Chooses Attack {choice}!")
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
        self.boss.draw_generic()


# --- 공격 1: 근접 (Enemy1 스타일) ---
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
        if self.timer > 0.5 and not self.attacked:  # 0.5초 딜레이 후 공격
            smash = BossSmash(self.boss.x, self.boss.y, self.boss.face_dir)
            game_world.add_object(smash, 2)
            game_world.addcollide_pairs('player:enemy_attack', None, smash)
            self.attacked = True

        if self.timer > 1.0:  # 1초 후 복귀
            self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        self.boss.draw_generic()


# --- 공격 2: 독구름 (Enemy2 스타일) ---
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
        if self.timer > 0.5 and not self.attacked:
            poison = BossPoison(self.boss.x, self.boss.y)
            game_world.add_object(poison, 2)
            game_world.addcollide_pairs('player:poison', None, poison)
            self.attacked = True

        if self.timer > 1.0:
            self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        self.boss.draw_generic()


# --- 공격 3: 오로라 (신규 패턴) ---
class Attack3:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        self.boss.frame = 0
        self.timer = 0
        self.attacked = False
        print("Boss Casts Aurora!")

    def exit(self, e):
        pass

    def do(self, dt):
        self.timer += dt
        # 오로라는 시전 시간이 좀 김 (1초 딜레이)
        if self.timer > 1.0 and not self.attacked:
            # 플레이어 위치에 오로라 소환!
            target_x = self.boss.target.x if self.boss.target else self.boss.x + 100 * self.boss.face_dir
            aurora = AuroraEffect(target_x, self.boss.y, self.boss)
            game_world.add_object(aurora, 3)
            game_world.addcollide_pairs('player:enemy_attack', None, aurora)
            self.attacked = True

        if self.timer > 2.0:  # 2초 후 복귀
            self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        self.boss.draw_generic()


class Hit:
    def __init__(self, boss): self.boss = boss

    def enter(self, e): self.timer = 0

    def exit(self, e): pass

    def do(self, dt):
        self.timer += dt
        if self.timer > 0.5: self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self): self.boss.draw_generic()


class Die:
    def __init__(self, boss): self.boss = boss

    def enter(self, e):
        print("BOSS DEFEATED!")
        game_world.remove_object(self.boss)

    def exit(self, e): pass

    def do(self, dt): pass

    def draw(self): pass


# -------------------------------------------------------------------------
# 보스 본체 클래스
# -------------------------------------------------------------------------
class Boss:
    image = None
    hp_bg = None
    hp_fg = None

    def __init__(self, x=1500, y=150):
        self.x, self.y = x, y
        self.scale = [5.0, 5.0]  # 🌟 크기 매우 큼
        self.speed = 100.0  # 이동 속도는 느리게 (위압감)
        self.max_hp = 500  # 체력 많음
        self.hp = self.max_hp
        self.face_dir = -1
        self.dir = 0

        self.width = 32
        self.height = 32

        self.target = None  # 플레이어

        if Boss.image is None:
            # 보스 이미지 (없으면 버섯 확대)
            Boss.image = load_image('resource/Sprites/Free Mushrooms/Mushroom_spike.png')
            Boss.hp_bg = load_image('resource/Sprites/Free Mushrooms/btl_gage_hp_back.png')
            Boss.hp_fg = load_image('resource/Sprites/Free Mushrooms/btl_gage_hp.png')

        self.IDLE = Idle(self)
        self.TRACE = Trace(self)
        self.DECIDE = DecideAttack(self)  # 공격 선택 상태
        self.ATTACK1 = Attack1(self)
        self.ATTACK2 = Attack2(self)
        self.ATTACK3 = Attack3(self)
        self.HIT = Hit(self)
        self.DIE = Die(self)

        self.state_machine = StateMachine(self.IDLE, {
            self.IDLE: {detect_player: self.TRACE, hit: self.HIT, dead: self.DIE},
            self.TRACE: {reach_attack_range: self.DECIDE, hit: self.HIT, dead: self.DIE},

            # 공격 결정 상태에서 랜덤 분기
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
        self.state_machine.draw()
        self.draw_hp()
        if DEFINES.bbvisible:
            l, b, r, t = self.get_bb()
            sl, sb = server.world_to_screen(l, b)
            sr, st = server.world_to_screen(r, t)
            draw_rectangle(sl, sb, sr, st)

    # 상태들에서 공통으로 쓰는 그리기 함수
    def draw_generic(self):
        sx, sy = server.world_to_screen(self.x, self.y)
        # 임시로 프레임 0 고정 (애니메이션이 있다면 self.frame 사용)
        if self.face_dir == 1:
            self.image.clip_draw(0, 0, 32, 32, sx, sy, 32 * self.scale[0], 32 * self.scale[1])
        else:
            self.image.clip_composite_draw(0, 0, 32, 32, 0, 'h', sx, sy, 32 * self.scale[0], 32 * self.scale[1])

    def draw_hp(self):
        sx, sy = server.world_to_screen(self.x, self.y)
        ratio = clamp(0, self.hp / self.max_hp, 1)
        # 보스니까 HP바도 큼
        w, h = 128, 16
        y_off = 50 * self.scale[1]
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
from pico2d import *
import game_world
import server
import random
import math
import DEFINES
from state_machine import StateMachine


class BossPoison:
    image = None

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.lifetime = 4.0  # 4초 지속
        self.spawn_time = get_time()
        self.damage = 10  # 적당한 데미지
        self.scale = 3.0  # 크기 3배

        # 애니메이션 정보
        self.frame = 0
        self.frame_time = 0.0
        self.total_frames = 10

        # 🌟 타격 이펙트 쿨타임 (독구름 안에 있으면 계속 맞는데, 파티클이 너무 많이 생기지 않게 조절)
        self.hit_interval = 0.5
        self.last_hit_time = 0.0

        if BossPoison.image is None:
            try:
                # 🌟 boss.py에 있던 기존 독 이미지 사용 (Enemy와 똑같이 하려면 이미지 경로 변경 가능)
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
        # 수명 체크
        if get_time() - self.spawn_time > self.lifetime:
            game_world.remove_object(self)
            return

        # 애니메이션 (0.1초마다 프레임 변경)
        self.frame_time += dt
        if self.frame_time >= 0.1:
            self.frame_time = 0
            self.frame = (self.frame + 1) % self.total_frames

    def draw(self):
        if BossPoison.image is None: return

        # 🌟 월드 좌표 -> 화면 좌표 변환
        sx, sy = server.world_to_screen(self.x, self.y)
        left = self.frame * self.sprite_width

        BossPoison.image.clip_draw(left, 0, self.sprite_width, self.sprite_height,
                                   sx, sy, 64 * self.scale, 64 * self.scale)

        if DEFINES.bbvisible:
            l, b, r, t = self.get_bb()
            sl, sb = server.world_to_screen(l, b)
            sr, st = server.world_to_screen(r, t)
            draw_rectangle(sl, sb, sr, st)

    def get_bb(self):
        size = 40 * self.scale
        return self.x - size, self.y - size, self.x + size, self.y + size

    def handle_collision(self, group, other):
        # 🌟 플레이어와 충돌 시 파티클 생성 로직
        if group == 'player:poison':
            current_time = get_time()
            # 쿨타임이 지났으면 이펙트 생성
            if current_time - self.last_hit_time > self.hit_interval:
                hit_fx = HitEffect(other.x, other.y)
                game_world.add_object(hit_fx, 3)
                self.last_hit_time = current_time
class HitEffect:
    images = []

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.frame = 0
        self.frame_time = 0

        if not HitEffect.images:
            try:
                # Enemy와 같은 이펙트 이미지 로드
                HitEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_1.png'))
                HitEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_2.png'))
                HitEffect.images.append(load_image('resource/Sprites/Free Mushrooms/EnemyDieEffect/star_eff_3.png'))
            except:
                print("HitEffect 이미지 로드 실패")

    def update(self, dt):
        self.frame_time += dt
        if self.frame_time >= 0.05:
            self.frame += 1
            self.frame_time = 0
            if self.frame >= len(HitEffect.images):
                game_world.remove_object(self)

    def draw(self):
        if self.frame < len(HitEffect.images):
            img = HitEffect.images[self.frame]
            sx, sy = server.world_to_screen(self.x, self.y)
            img.draw(sx, sy, 64, 64)
# -------------------------------------------------------------------------
# 1. 오로라 이펙트 (Attack 3 - 신규 패턴)
# -------------------------------------------------------------------------
class AuroraEffect:
    images = []
    TOTAL_FRAMES = 20  # 초기 로드 시도 횟수
    # 🌟 경로 수정: 0이 채워지지 않은 {d} 사용 (lila_a1.png 형태)
    IMAGE_PATH_TEMPLATE = 'resource/Sprites/Free Mushrooms/enemyaurora/lila_a{:d}.png'

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.lifetime = 2.0
        self.spawn_time = get_time()
        self.damage = 30
        self.warning_time = 0.8

        self.frame = 0
        self.frame_time = 0.0

        if not AuroraEffect.images:
            print(f"Loading {self.TOTAL_FRAMES} Aurora frames...")
            loaded_images = []
            for i in range(1, 21):
                try:
                    # 🌟 수정된 포맷 적용
                    file_path = self.IMAGE_PATH_TEMPLATE.format(i)
                    loaded_images.append(load_image(file_path))
                except Exception as e:
                    print(f"Warning: Failed to load image {file_path}. Skipping: {e}")

            AuroraEffect.images = loaded_images
            # 🌟 안전 장치: 로드된 실제 개수로 프레임 수 확정
            AuroraEffect.TOTAL_FRAMES = len(AuroraEffect.images)

            if not AuroraEffect.images:
                print("Critical Error: No Aurora images were loaded.")
            else:
                print(f"Successfully loaded {AuroraEffect.TOTAL_FRAMES} Aurora frames.")

    def update(self, dt):
        if get_time() - self.spawn_time > self.lifetime:
            game_world.remove_object(self)
            return

        # 경고 시간 후 애니메이션 프레임 업데이트
        if get_time() - self.spawn_time > self.warning_time:
            self.frame_time += dt
            if self.frame_time >= 0.05:
                self.frame_time = 0
                # 🌟 안전하게 로드된 프레임 수로 순환
                self.frame = (self.frame + 1) % self.TOTAL_FRAMES

    def draw(self):
        sx, sy = server.world_to_screen(self.x, self.y)
        elapsed = get_time() - self.spawn_time

        # 예고 시간: 깜빡이는 경고 박스
        if elapsed < self.warning_time:
            if int(elapsed * 20) % 2 == 0:
                draw_rectangle(sx - 40, sy - 400, sx + 40, sy + 400)
        else:
            # 🌟 실제 공격: 개별 이미지 그리기 (안전 참조)
            if AuroraEffect.images:
                # self.frame은 TOTAL_FRAMES를 넘지 않음이 보장됨
                current_image = AuroraEffect.images[self.frame]
                current_image.draw(sx, sy, 200, 200)

            if DEFINES.bbvisible:
                draw_rectangle(*self.get_bb())

    def get_bb(self):
        if get_time() - self.spawn_time < self.warning_time:
            return 0, 0, 0, 0
        return self.x - 70, self.y - 400, self.x + 70, self.y + 400

    def handle_collision(self, group, other):
        pass
# -------------------------------------------------------------------------
# 2. 보스 독구름 (Attack 2 - Enemy2 스타일)
# -------------------------------------------------------------------------
class BossSmash:
    def __init__(self, x, y, face_dir):
        self.x, self.y = x, y
        self.face_dir = face_dir
        self.exist_time = 0.0
        self.LIFETIME = 0.2  # 🌟 적과 동일하게 짧게 설정
        self.damage = 20
        self.width = 100  # 🌟 적과 비슷한 크기로 조정 (필요 시 수정)
        self.height = 100

    def update(self, dt):
        self.exist_time += dt
        if self.exist_time >= self.LIFETIME:
            game_world.remove_object(self)

    def draw(self):
        if DEFINES.bbvisible:
            l, b, r, t = self.get_bb()
            sl, sb = server.world_to_screen(l, b)
            sr, st = server.world_to_screen(r, t)
            draw_rectangle(sl, sb, sr, st)

    def get_bb(self):
        # 🌟 적과 동일한 오프셋 로직 적용
        offset_x = 60 * self.face_dir  # 보스 크기에 맞춰 거리 조절
        return self.x + offset_x - self.width // 2, self.y - self.height // 2, \
               self.x + offset_x + self.width // 2, self.y + self.height // 2

    def handle_collision(self, group, other):
        # 🌟 플레이어와 충돌 시
        if group == 'player:enemy_attack':
            # 1. 파티클(HitEffect) 생성
            hit_fx = HitEffect(other.x, other.y)
            game_world.add_object(hit_fx, 3)

            # 2. 공격 객체 삭제 (한 번만 때리기 위해)
            game_world.remove_object(self)

# -------------------------------------------------------------------------
# 3. 보스 스매시 (Attack 1 - Enemy1 스타일 근접)
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
        offset_x = 100 * self.face_dir
        return self.x + offset_x - self.width // 2, self.y - self.height // 2, \
               self.x + offset_x + self.width // 2, self.y + self.height // 2

    def handle_collision(self, group, other):
        if group == 'player:enemy_attack': game_world.remove_object(self)


# -------------------------------------------------------------------------
# 보스 상태 (State) 클래스들
# -------------------------------------------------------------------------
def time_out(e): return e[0] == 'TIME_OUT'


def hit(e): return e[0] == 'HIT'


def dead(e): return e[0] == 'DEAD'


def detect_player(e): return e[0] == 'DETECT'


def reach_attack_range(e): return e[0] == 'ATTACK_RANGE'


def attack_1(e): return e[0] == 'ATTACK_1'


def attack_2(e): return e[0] == 'ATTACK_2'


def attack_3(e): return e[0] == 'ATTACK_3'


# --- Idle ---
class Idle:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        self.boss.frame = 0
        self.boss.wait_time = get_time()

    def exit(self, e):
        pass

    def do(self, dt):
        # 0.2초 후 바로 추격 시작 (보스는 멍때리지 않음)
        if get_time() - self.boss.wait_time > 0.2:
            self.boss.state_machine.handle_state_event(('DETECT', None))

    def draw(self):
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        # 🌟 기본 대기 모션 (예: 4번째 줄)
        BOTTOM_ROW = 32 * 4
        frame_x = self.boss.frame * 32

        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(frame_x, BOTTOM_ROW, 32, 16, sx, sy, 32 * self.boss.scale[0],
                                      16 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(frame_x, BOTTOM_ROW, 32, 16, 0, 'h', sx, sy, 32 * self.boss.scale[0],
                                                16 * self.boss.scale[1])


# --- Trace (추격) ---
class Trace:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        self.boss.frame = 0
        self.frame_time = 0

    def exit(self, e):
        pass

    def do(self, dt):
        # 애니메이션 (달리기 4프레임)
        self.frame_time += dt
        if self.frame_time >= 0.1:
            self.frame_time = 0
            self.boss.frame = (self.boss.frame + 1) % 4

        # 추격 로직
        if self.boss.target:
            dist = math.sqrt((self.boss.x - self.boss.target.x) ** 2 + (self.boss.y - self.boss.target.y) ** 2)
            self.boss.dir = 1 if self.boss.target.x > self.boss.x else -1
            self.boss.face_dir = self.boss.dir
            self.boss.x += self.boss.dir * self.boss.speed * dt

            # 공격 사거리 (200px)
            if dist <= 200:
                self.boss.state_machine.handle_state_event(('ATTACK_RANGE', None))

    def draw(self):
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        # 🌟 달리기 모션 (예: 4번째 줄, 6번째 칸부터 시작) - Enemy2 Trace 참조
        BOTTOM_ROW = 32 * 4
        start_pixel_x = 32 * 6
        frame_x = start_pixel_x + (self.boss.frame * 32)

        # 높이 보정 (Enemy2 Trace처럼 키가 커지는 모션이라면)
        FRAME_HEIGHT = 30
        y_offset = (FRAME_HEIGHT - 16) / 2 * self.boss.scale[1]

        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(frame_x, BOTTOM_ROW, 32, FRAME_HEIGHT, sx, sy + y_offset, 32 * self.boss.scale[0],
                                      FRAME_HEIGHT * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(frame_x, BOTTOM_ROW, 32, FRAME_HEIGHT, 0, 'h', sx, sy + y_offset,
                                                32 * self.boss.scale[0], FRAME_HEIGHT * self.boss.scale[1])


# --- DecideAttack (공격 선택) ---
class DecideAttack:
    def __init__(self, boss):
        self.boss = boss

    def enter(self, e):
        # 🌟 여기서는 타이머만 초기화하고, 바로 이벤트를 보내지 않습니다.
        self.timer = 0

    def exit(self, e):
        pass

    def do(self, dt):
        self.timer += dt

        # 🌟 0.1초만 기다렸다가 공격 패턴을 결정합니다. (상태 전환 안정성 확보)
        if self.timer > 0.1:
            choice = random.randint(1, 3)
            # print(f"Boss Decides Attack: {choice}") # 디버깅용

            if choice == 1:
                self.boss.state_machine.handle_state_event(('ATTACK_1', None))
            elif choice == 2:
                self.boss.state_machine.handle_state_event(('ATTACK_2', None))
            else:
                self.boss.state_machine.handle_state_event(('ATTACK_3', None))

            # 한 번 결정했으면 타이머 초기화 (혹시 모를 중복 방지)
            self.timer = -999

    def draw(self):
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        self.boss.image.clip_draw(0, 32 * 4, 32, 16, sx, sy, 32 * self.boss.scale[0], 16 * self.boss.scale[1])

# --- Attack 1: 근접 (Enemy1 Attack) ---
class Attack1:
    def __init__(self, boss):
        self.boss = boss
        # self.attacked 변수는 이제 필요 없음 (has_attacked 사용)

    def enter(self, e):
        self.boss.frame = 0
        self.boss.frame_time = 0.0  # 🌟 프레임 타이머 초기화
        self.has_attacked = False  # 🌟 공격 여부 플래그 초기화

    def exit(self, e):
        pass

    def do(self, dt):
        # 🌟 Enemy.py와 완전히 동일한 프레임 로직 사용
        self.boss.frame_time += dt
        ATTACK_FRAME_TIME = 0.15  # 🌟 속도 조절 (적과 맞추거나 보스에 맞게 조절)

        if self.boss.frame_time >= ATTACK_FRAME_TIME:
            self.boss.frame_time = 0.0
            self.boss.frame += 1

            # 🌟 [핵심] 4번째 프레임일 때 공격 판정 생성 (적과 동일)
            if self.boss.frame == 4 and not self.has_attacked:
                self.spawn_attack()
                self.has_attacked = True

            # 8프레임 애니메이션 종료 시
            if self.boss.frame >= 8:
                self.boss.frame = 0
                self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def spawn_attack(self):
        # BossSmash 생성
        smash = BossSmash(self.boss.x, self.boss.y, self.boss.face_dir)
        game_world.add_object(smash, 3)  # 이펙트 레이어 근처
        game_world.addcollide_pairs('player:enemy_attack', None, smash)

    def draw(self):
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        # 🌟 Enemy와 동일한 스프라이트 시트 구조라고 가정 (2번째 줄)
        BOTTOM_ROW = 32 * 2

        # frame은 do()에서 계산되므로 그대로 사용
        frame_x = self.boss.frame * 32

        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(frame_x, BOTTOM_ROW, 32, 16, sx, sy,
                                      32 * self.boss.scale[0], 16 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(frame_x, BOTTOM_ROW, 32, 16, 0, 'h', sx, sy,
                                                32 * self.boss.scale[0], 16 * self.boss.scale[1])
# --- Attack 2: 독구름 (Enemy2 Attack) ---
class Attack2:
    def __init__(self, boss):
        self.boss = boss
        # self.attacked는 이제 has_attacked로 대체

    def enter(self, e):
        self.boss.frame = 0
        self.boss.frame_time = 0.0  # 타이머 초기화
        self.has_attacked = False  # 공격 플래그 초기화

    def exit(self, e):
        pass

    def do(self, dt):
        # 🌟 1. Enemy2와 동일한 프레임 기반 애니메이션 로직
        self.boss.frame_time += dt
        ATTACK_FRAME_TIME = 0.15  # 속도 조절

        if self.boss.frame_time >= ATTACK_FRAME_TIME:
            self.boss.frame_time = 0.0
            self.boss.frame += 1

            # 🌟 2. 4번째 프레임에 독구름 소환 (Enemy2와 동일)
            if self.boss.frame == 4 and not self.has_attacked:
                self.spawn_poison()
                self.has_attacked = True

            # 3. 8프레임 애니메이션 종료 시 상태 전환
            if self.boss.frame >= 8:
                self.boss.frame = 0
                self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def spawn_poison(self):
        # 독구름 객체 생성
        # 보스 발 밑이나 앞쪽에 생성
        spawn_x = self.boss.x + (self.boss.face_dir * 50)
        poison = BossPoison(spawn_x, self.boss.y)

        game_world.add_object(poison, 2)
        # 🌟 충돌 그룹 등록 (반드시 main.py의 add_collision_pair와 이름이 같아야 함)
        game_world.addcollide_pairs('player:poison', None, poison)

    def draw(self):
        # Attack1과 동일하게 그림 (모션 공유)
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        BOTTOM_ROW = 32 * 2  # 2번째 줄
        frame_x = self.boss.frame * 32

        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(frame_x, BOTTOM_ROW, 32, 16, sx, sy,
                                      32 * self.boss.scale[0], 16 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(frame_x, BOTTOM_ROW, 32, 16, 0, 'h', sx, sy,
                                                32 * self.boss.scale[0], 16 * self.boss.scale[1])
# --- Attack 3: 오로라 (신규) ---
class Attack3:
    def __init__(self, boss):
        self.boss = boss
        # 공격 모션 자체의 총 지속 시간
        self.TOTAL_DURATION = 2.0

    def enter(self, e):
        self.boss.frame = 0
        self.timer = 0
        self.attacked = False

        # 🌟 [추가] 공격 시작 시 플레이어를 바라보도록 방향(face_dir) 설정
        if self.boss.target:
            if self.boss.target.x > self.boss.x:
                self.boss.face_dir = 1  # 오른쪽
            else:
                self.boss.face_dir = -1  # 왼쪽
        self.boss.dir = self.boss.face_dir
    def exit(self, e):
        pass

    def do(self, dt):
        self.timer += dt

        # 0.5초 딜레이 후 오로라 소환 (기존 Attack3 로직)
        if self.timer > 0.5 and not self.attacked:
            # 플레이어 위치에 오로라 소환
            target_x = self.boss.target.x if self.boss.target else self.boss.x + 150 * self.boss.face_dir
            # AuroraEffect는 이제 20프레임 애니메이션을 자체적으로 재생합니다.
            aurora = AuroraEffect(target_x, self.boss.y)
            game_world.add_object(aurora, 3)
            game_world.addcollide_pairs('player:enemy_attack', None, aurora)
            self.attacked = True

        # 총 지속 시간 초과 시 상태 전이
        if self.timer > self.TOTAL_DURATION:
            self.boss.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        sx, sy = server.world_to_screen(self.boss.x, self.boss.y)
        BOTTOM_ROW = 32 * 2
        frame_idx = int(self.timer * 8) % 8
        frame_x = frame_idx * 32

        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(frame_x, BOTTOM_ROW, 32, 16, sx, sy, 32 * self.boss.scale[0],
                                      16 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(frame_x, BOTTOM_ROW, 32, 16, 0, 'h', sx, sy, 32 * self.boss.scale[0],
                                                16 * self.boss.scale[1])

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
        # 피격: 맨 아랫줄(0번 줄) 0번 프레임
        if self.boss.face_dir == 1:
            self.boss.image.clip_draw(0, 0, 32, 16, sx, sy, 32 * self.boss.scale[0], 16 * self.boss.scale[1])
        else:
            self.boss.image.clip_composite_draw(0, 0, 32, 16, 0, 'h', sx, sy, 32 * self.boss.scale[0],
                                                16 * self.boss.scale[1])


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
        self.scale = [8.0, 8.0]
        self.speed = 80.0
        self.max_hp = 1000
        self.hp = self.max_hp
        self.face_dir = -1
        self.dir = 0
        self.frame = 0

        self.width = 32
        self.height = 32

        self.target = None

        if Boss.image is None:
            # Enemy2와 같은 이미지를 쓴다고 가정 (Mushroom_Spotted.png)
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

            # 패턴 분기
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
            if server.player:
                self.target = server.player
            # 2. 그래도 없으면 game_world 직접 뒤져서 찾기
            else:
                for layer in game_world.world:
                    for obj in layer:
                        # 이름이나 속성으로 플레이어 찾기 (본인 코드에 맞게)
                        if hasattr(obj, 'handle_event') and hasattr(obj, 'hp'):
                            self.target = obj
                            server.player = obj # 찾았으면 서버에도 등록
                            break

        self.state_machine.update(dt)

    def draw(self):
        self.state_machine.draw()
        self.draw_hp()
        if DEFINES.bbvisible:
            l, b, r, t = self.get_bb()
            sl, sb = server.world_to_screen(l, b)
            sr, st = server.world_to_screen(r, t)
            draw_rectangle(sl, sb, sr, st)

    def draw_hp(self):
        sx, sy = server.world_to_screen(self.x, self.y)
        ratio = clamp(0, self.hp / self.max_hp, 1)
        w, h = 128, 16

        y_off = 20 * self.scale[1]

        Boss.hp_bg.draw_to_origin(sx - w // 2, sy + y_off, w, h)
        Boss.hp_fg.draw_to_origin(sx - w // 2, sy + y_off, w * ratio, h)

    def get_bb(self):
        # 1. 좌우 너비
        half_width = 60

        # 2. 머리 높이
        top_height = 90

        # 🌟 [수정] 발 높이 (값을 키울수록 보스가 위로 올라갑니다)
        # 현재 110에서 -> 150 정도로 올려보세요.
        # (만약 여전히 낮으면 160, 170으로 계속 키우시면 됩니다)
        bottom_height = 150

        return self.x - half_width, self.y - bottom_height, self.x + half_width, self.y + top_height

    def handle_collision(self, group, other):
        if group == 'enemy:bullet' or group == 'sword:enemy':
            self.hp -= other.damage
            if self.hp > 0:
                self.state_machine.handle_state_event(('HIT', None))
            else:
                self.state_machine.handle_state_event(('DEAD', None))
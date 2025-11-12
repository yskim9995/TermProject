from pico2d import *
import game_world
import math

import DEFINES

# -----------------------------------------------------
# 1. 19프레임짜리 검기 이펙트 클래스
# -----------------------------------------------------
class SwordEffect:
    images = None
    LIFETIME = 0.75  #  19프레임 총 재생 시간 (0.75초, 19 * ~0.04초)
    TOTAL_FRAMES = 12

    def __init__(self, player):
        self.player = player  # 이펙트가 따라다닐 플레이어
        self.spawn_time = get_time()
        self.frame = 0
        self.hit_enemies = [] # 이미 맞은 적 리스트
        DEFINES.Gunvisible = False
        game_world.addcollide_pairs('sword:enemy', self, None )
        # 🌟 이펙트가 그려질 위치 오프셋 (플레이어 중심 기준)
        self.offset_x = 32  # (오른쪽으로 32px)
        self.offset_y = 0  # (y는 동일)

        # 🌟 이펙트 스프라이트 원본 크기 (수정 필요)
        self.EFFECT_WIDTH = 64
        self.EFFECT_HEIGHT = 64


        # 이미지를 한 번만 로드
        if SwordEffect.images is None:
            try:
                # (파일 이름 패턴에 맞게 수정하세요)
                SwordEffect.images = [
                    load_image(f'resource/Sprites/SwordEffect/scythe_a{i + 1:d}.png')
                    for i in range(SwordEffect.TOTAL_FRAMES)
                ]
            except Exception as e:
                print(f"SwordEffect 이미지 로드 실패: {e}")

        self.time_per_frame = SwordEffect.LIFETIME / SwordEffect.TOTAL_FRAMES

    def update(self, dt):
        time_elapsed = get_time() - self.spawn_time

        # 1. 수명이 다하면 제거
        if time_elapsed > SwordEffect.LIFETIME:
            game_world.remove_object(self)
            game_world.remove_colision_object(self)
            DEFINES.Gunvisible = True
            return

        # 2. 시간에 맞춰 현재 프레임(0~18) 계산
        self.frame = int(time_elapsed / self.time_per_frame)
        if self.frame >= SwordEffect.TOTAL_FRAMES:
            self.frame = SwordEffect.TOTAL_FRAMES - 1

    def draw(self):
        image_to_draw = SwordEffect.images[self.frame]

        flip_str = ''
        draw_x = self.player.x + self.offset_x

        if self.player.face_dir == -1:  # 왼쪽을 볼 때
            flip_str = 'h'  # 좌우 반전
            draw_x = self.player.x - self.offset_x  # 오프셋도 반전

        # 플레이어 위치를 기준으로 이펙트를 그림
        image_to_draw.composite_draw(
            0,  # 회전 없음 (필요하면 self.player.rotation 등 사용)
            flip_str,
            draw_x,
            self.player.y + self.offset_y,
            self.EFFECT_WIDTH,
            self.EFFECT_HEIGHT
        )
        if DEFINES.bbvisible:
            draw_rectangle(*self.get_bb())

    # (충돌 처리가 필요 없는 빈 함수들)
    def get_bb(self):

        draw_x = self.player.x + self.offset_x
        if self.player.face_dir == -1:  # 왼쪽을 볼 때
            draw_x = self.player.x - self.offset_x

        # 2. 이펙트의 중심 y좌표 계산
        draw_y = self.player.y + self.offset_y

        # 3. 이펙트의 '절반' 너비와 높이 계산
        half_w = self.EFFECT_WIDTH / 2
        half_h = self.EFFECT_HEIGHT / 2

        # 4. 중심 좌표와 절반 크기를 이용해 바운딩 박스 반환
        return draw_x - half_w, draw_y - half_h, draw_x + half_w, draw_y + half_h

    def handle_collision(self, group, other):
        if group == 'sword:enemy':
            if other not in self.hit_enemies:
                print('검에 적 맞음(최초 1 회)')
                self.hit_enemies.append(other)
                if other.hp > 0:
                    other.state_machine.handle_state_event(('HIT', self.player))

class Sword:
    def __init__(self, player):
        self.player = player
        self.attack_rate = 0.8  # 공격 쿨타임 (이펙트 시간보다 약간 길게)
        self._last_attack_time = 0.0

        # (만약 플레이어가 검을 들고 있는 이미지를 그린다면 여기에 load_image)

    def try_attack(self):
        now = get_time()
        # 1. 공격 쿨타임 체크
        if now - self._last_attack_time < self.attack_rate:
            return

        # 2. 쿨타임 초기화
        self._last_attack_time = now

        # 3. 이펙트 생성
        print("검 공격!")
        effect = SwordEffect(self.player)
        game_world.add_object(effect, 2)

    def update(self, dt):
        # (만약 검이 플레이어를 따라다녀야 한다면 여기에 로직 추가)
        pass

    def draw(self):
        # (만약 검을 차고 있는 모습을 그린다면 여기에 draw 로직 추가)
        pass
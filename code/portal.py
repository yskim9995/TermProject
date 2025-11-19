from pico2d import *
import game_world
import DEFINES


class Portal:
    images = []  # 🌟 이미지 3장을 담을 리스트

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.active = True
        self.frame = 0
        self.frame_time = 0.0

        # 🌟 이미지 3장 로드 (최초 1회)
        if not Portal.images:
            # 파일명이 portal_0.png, portal_1.png, portal_2.png 라고 가정
            # 만약 파일명이 다르다면 직접 append 하세요.
                # 예: resource/portal_1.png ~ 3.png 형태라면 경로 수정 필요
                # 여기서는 portal1.png, portal2.png, portal3.png로 가정
            Portal.images.append(load_image('resource/Sprites/Portal/blowgun_a1.png'))
            Portal.images.append(load_image('resource/Sprites/Portal/blowgun_a2.png'))
            Portal.images.append(load_image('resource/Sprites/Portal/blowgun_a3.png'))

    def update(self, dt):
        # 애니메이션 속도 조절 (0.2초마다 프레임 변경)
        self.frame_time += dt
        if self.frame_time >= 0.3:
            self.frame_time = 0
            self.frame = (self.frame + 1) % 3  # 0, 1, 2 반복

    def draw(self):
        if self.active:
            # 현재 프레임 그리기
            Portal.images[self.frame].draw(self.x, self.y)

            if DEFINES.bbvisible:
                draw_rectangle(*self.get_bb())

    def get_bb(self):
        # 충돌 박스 크기 (이미지 크기에 맞춰 적당히 조절)
        return self.x - 30, self.y - 50, self.x + 30, self.y + 50

    def handle_collision(self, group, other):
        pass  # 충돌 처리는 main에서 수행
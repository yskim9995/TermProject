from pico2d import *
import game_world
import DEFINES
import server  # 🌟 [필수] 서버 모듈 임포트 (카메라 변환용)

class Portal:
    images = []

    def __init__(self, x=3200, y=150): # 🌟 기본 위치를 맵 끝(예: 3200)으로 설정 (필요시 수정)
        self.x, self.y = x, y
        self.active = True
        self.frame = 0
        self.frame_time = 0.0

        if not Portal.images:
            try:
                # 리소스 경로 확인 필수
                Portal.images.append(load_image('resource/Sprites/Portal/blowgun_a1.png'))
                Portal.images.append(load_image('resource/Sprites/Portal/blowgun_a2.png'))
                Portal.images.append(load_image('resource/Sprites/Portal/blowgun_a3.png'))
            except Exception as e:
                print(f"Portal 이미지 로드 실패: {e}")

    def update(self, dt):
        self.frame_time += dt
        if self.frame_time >= 0.3:
            self.frame_time = 0
            self.frame = (self.frame + 1) % 3

    def draw(self):
        if self.active:
            # 🌟 [핵심 수정] 월드 좌표(self.x) -> 화면 좌표(sx) 변환
            sx, sy = server.world_to_screen(self.x, self.y)

            # 변환된 좌표에 그리기
            if 0 <= self.frame < len(Portal.images):
                Portal.images[self.frame].draw(sx, sy)

            # 디버그 박스 그리기
            if DEFINES.bbvisible:
                # get_bb는 월드 좌표를 주므로 화면 좌표로 변환 필요
                l, b, r, t = self.get_bb()
                sl, sb = server.world_to_screen(l, b)
                sr, st = server.world_to_screen(r, t)
                draw_rectangle(sl, sb, sr, st)

    def get_bb(self):
        # 🌟 충돌 박스는 '월드 좌표' 기준이어야 함 (수정 X)
        return self.x - 30, self.y - 50, self.x + 30, self.y + 50

    def handle_collision(self, group, other):
        pass
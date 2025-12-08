from pico2d import *
import server  # server.player와 연동하기 위해 필요


class Background:
    def __init__(self):
        # 5장의 레이어 이미지 로드
        self.images = [
            load_image('resource/Sprites/Jungle Asset Pack/parallax background/plx-1.png'),
            load_image('resource/Sprites/Jungle Asset Pack/parallax background/plx-2.png'),
            load_image('resource/Sprites/Jungle Asset Pack/parallax background/plx-3.png'),
            load_image('resource/Sprites/Jungle Asset Pack/parallax background/plx-4.png'),
            load_image('resource/Sprites/Jungle Asset Pack/parallax background/plx-5.png')
        ]

        # 이미지 하나의 크기 (모든 plx 이미지가 크기가 같다고 가정)
        self.w = self.images[0].w
        self.h = self.images[0].h

        # 화면 크기
        self.cw = get_canvas_width()
        self.ch = get_canvas_height()

        # 🌟 전체 맵의 길이 설정 (예: 화면 3개 분량인 2400픽셀)
        # 이 숫자를 늘리면 맵이 더 길어집니다.
        self.map_width = 2400
        self.map_height = self.ch  # 높이는 화면 높이와 같다고 가정

        # 카메라 위치
        self.window_left = 0
        self.window_bottom = 0

    def update(self, dt):

        print("배경 업데이트 실행 중!")
        # 플레이어가 생성되기 전엔 업데이트 건너뜀
        if server.player is None:
            return

        # 🌟 [교수님 코드 로직] 카메라 이동 계산
        # 플레이어 위치(server.player.x)를 중심으로 카메라를 잡음
        self.window_left = clamp(0, int(server.player.x) - self.cw // 2, self.map_width - self.cw)
        self.window_bottom = clamp(0, int(server.player.y) - self.ch // 2, self.map_height - self.ch)
        print(f"Player: {server.player.x}, Camera: {self.window_left}")

    def draw(self):
        # 🌟 [핵심] 타일링 (옆으로 이어 붙여 그리기)

        # 1. 화면을 채우기 위해 가로로 이미지가 몇 장 필요한가? (여유분 +1)
        tiles_needed = (self.cw // self.w) + 2

        # 2. 스크롤에 따른 오프셋 계산 (이미지 너비로 나눈 나머지)
        x_start = int(self.window_left) % int(self.w)

        # 5장의 레이어를 모두 그림
        for layer_index in range(5):
            img = self.images[layer_index]

            # 필요한 타일 개수만큼 옆으로 반복해서 그림
            for i in range(tiles_needed):
                # 그릴 x좌표 계산: (순서 * 너비) - (스크롤 밀림 정도)
                sx = (i * self.w) - x_start

                # y좌표는 0 (세로 스크롤이 없다면)
                sy = 0

                # draw_to_origin: 왼쪽 아래가 (0,0) 기준
                # sx, sy 위치에, 원본 크기(self.w)와 화면 높이(self.ch)만큼 그림
                img.draw_to_origin(sx, sy, self.w, self.ch)

    def get_bb(self):
        pass

    def handle_collision(self, group, other):
        pass
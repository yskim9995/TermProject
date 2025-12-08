from pico2d import *
import DEFINES
import server  # 🌟 server 모듈에 background 객체가 있다고 가정 (혹은 전역 변수)


class Grass:
    TILESET_HEIGHT = 368

    def __init__(self, x, y, clip_x, clip_y_in_file, clip_width, clip_height, scale):
        self.x = x  # 🌟 이것은 맵 전체에서의 절대 위치 (World Coordinate)
        self.y = y
        self.scale = scale
        self.tileset_image = load_image('resource/Sprites/Jungle Asset Pack/jungle tileset/jungletileset.png')

        self.clip_x = clip_x
        self.clip_width = clip_width
        self.clip_height = clip_height
        self.clip_y = Grass.TILESET_HEIGHT - (clip_y_in_file + clip_height)

    def update(self, dt):
        pass
        # 잔디 자체는 움직이지 않지만, 그리는 위치가 카메라에 따라 달라짐

    def draw(self):
        scaled_draw_width = self.clip_width * self.scale
        scaled_draw_height = self.clip_height * self.scale

        # 🌟 [수정 포인트] 월드 좌표(self.x)에서 카메라 위치(background.window_left)를 빼야 함
        # server.background가 없으면 카메라 변수가 있는 곳을 참조하세요.
        screen_x = self.x - server.background.window_left
        screen_y = self.y - server.background.window_bottom

        self.tileset_image.clip_draw(
            self.clip_x, self.clip_y,
            self.clip_width, self.clip_height,
            screen_x, screen_y,  # 🌟 변환된 화면 좌표 사용
            scaled_draw_width, scaled_draw_height
        )

        # 바운딩 박스 그리기 (디버그용)
        if DEFINES.bbvisible:
            # BB를 그릴 때도 화면 좌표 기준으로 그려야 눈에 보이는 위치와 맞음
            sx, sy = screen_x, screen_y
            half_w = scaled_draw_width / 2
            half_h = scaled_draw_height / 2
            draw_rectangle(sx - half_w, sy - half_h, sx + half_w, sy + half_h)

    def get_bb(self):
        # 🌟 충돌 처리는 보통 '월드 좌표(절대 위치)' 기준으로 계산합니다.
        # (충돌 검사 로직이 화면 좌표 기준인지 월드 좌표 기준인지에 따라 다르지만, 보통 월드 좌표를 씁니다.)
        scaled_width = self.clip_width * self.scale
        scaled_height = self.clip_height * self.scale

        half_width = scaled_width / 2
        half_height = scaled_height / 2
        return self.x - half_width, self.y - half_height, \
               self.x + half_width, self.y + half_height

    def handle_collision(self, group, other):
        pass
from pico2d import *
import DEFINES
import server


class Grass:
    TILESET_HEIGHT = 368
    # 🌟 [핵심 1] 클래스 변수로 선언 (모든 Grass 객체가 이 이미지 하나를 공유함)
    tileset_image = None

    def __init__(self, x, y, clip_x, clip_y_in_file, clip_width, clip_height, scale):
        self.x = x
        self.y = y
        self.scale = scale

        # 🌟 [핵심 2] 이미지가 로드되지 않았을 때만(최초 1회) 로딩!
        # self.tileset_image 가 아니라 Grass.tileset_image에 저장합니다.
        if Grass.tileset_image is None:
            Grass.tileset_image = load_image('resource/Sprites/Jungle Asset Pack/jungle tileset/jungletileset.png')

        self.clip_x = clip_x
        self.clip_width = clip_width
        self.clip_height = clip_height
        self.clip_y = Grass.TILESET_HEIGHT - (clip_y_in_file + clip_height)

    def update(self, dt):
        pass

    def draw(self):
        # 화면 좌표 변환
        sx, sy = server.world_to_screen(self.x, self.y)

        # 🌟 [핵심 3] 화면 밖으로 나간 벽은 그리지 않음 (최적화)
        # 화면 좌우 여유분(200px)을 두고 검사
        if sx < -200 or sx > DEFINES.SCW + 200:
            return

        scaled_draw_width = self.clip_width * self.scale
        scaled_draw_height = self.clip_height * self.scale

        # self.tileset_image 대신 Grass.tileset_image 사용
        Grass.tileset_image.clip_draw(
            self.clip_x, self.clip_y,
            self.clip_width, self.clip_height,
            sx, sy,
            scaled_draw_width, scaled_draw_height
        )

        if DEFINES.bbvisible:
            half_w = scaled_draw_width / 2
            half_h = scaled_draw_height / 2
            draw_rectangle(sx - half_w, sy - half_h, sx + half_w, sy + half_h)

    def get_bb(self):
        scaled_width = self.clip_width * self.scale
        scaled_height = self.clip_height * self.scale
        half_width = scaled_width / 2
        half_height = scaled_height / 2
        return self.x - half_width, self.y - half_height, \
               self.x + half_width, self.y + half_height

    def handle_collision(self, group, other):
        pass
from pico2d import *
# self.image = load_image('resource/Sprites/Jungle Asset Pack/jungle tileset/jungle tileset.png')
class Grass:
    tileset_image = None


    # 🌟🌟🌟 타일셋의 실제 높이 (clip_draw Y좌표 계산용) 🌟🌟🌟
    TILESET_HEIGHT = 368  # 768 * 368 이므로 높이는 368

    def __init__(self, x, y, clip_x, clip_y_in_file, clip_width, clip_height , scale):
        self.x = x
        self.y = y
        self.scale = scale
        self.tileset_image = load_image('resource/Sprites/Jungle Asset Pack/jungle tileset/jungletileset.png')
        # 🌟 타일셋에서 잘라낼 정보 저장
        self.clip_x = clip_x
        self.clip_width = clip_width
        self.clip_height = clip_height

        # 🌟 clip_draw의 Y좌표는 '아래'를 기준으로 하므로 변환 필요
        # (원본 이미지의 Y는 위에서부터)
        # TILESET_HEIGHT - (원본 이미지 Y좌표 + 잘라낼 높이)
        self.clip_y = Grass.TILESET_HEIGHT - (clip_y_in_file + clip_height)

    def update(self,dt):
        pass  # 잔디는 움직이지 않으므로 비워둠

    def draw(self):
        scaled_draw_width = self.clip_width * self.scale
        scaled_draw_height = self.clip_height * self.scale

        # 🌟 3. clip_draw의 8인자 버전을 사용하여 스케일 적용
        self.tileset_image.clip_draw(
            self.clip_x, self.clip_y,
            self.clip_width, self.clip_height,
            self.x, self.y,
            scaled_draw_width, scaled_draw_height  # 🌟 스케일된 크기로 그리기
        )

        # 바운딩 박스 그리기 (디버그용)
        draw_rectangle(*self.get_bb())

    def get_bb(self):
        # 🌟 현재 잔디 객체의 x, y, width, height를 기반으로 바운딩 박스 계산
        scaled_width = self.clip_width * self.scale
        scaled_height = self.clip_height * self.scale

        half_width = scaled_width / 2
        half_height = scaled_height / 2
        return self.x - half_width, self.y - half_height, \
               self.x + half_width, self.y + half_height

    def handle_collision(self, group, other):
        pass  # 충돌 처리가 필요하면 여기에 구현
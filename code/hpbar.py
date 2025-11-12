from pico2d import load_image


class Hpbar:
    # 1. HP 바 이미지를 한 번만 로드
    background_image = None
    fill_image = None

    # 2. HP바 원본 크기 (로드 후 저장됨)
    original_width = 0
    original_height = 0

    def __init__(self, owner_player):
        """
        Player의 HP를 추적하는 HP바 객체를 생성합니다.
        :param owner_player: HP를 추적할 Player 객체
        """
        # 3. HP를 가져올 '주인' (Player)을 저장
        self.owner = owner_player

        # 4. 이미지를 클래스 변수로 한 번만 로드
        if Hpbar.background_image is None:
            Hpbar.background_image = load_image('resource/Sprites/Ui/health bar/empty golden health bar 1.png')
        if Hpbar.fill_image is None:
            Hpbar.fill_image = load_image('resource/Sprites/Ui/health bar/golden health bar 1.png')

        # 5. 원본 크기 저장
        if Hpbar.background_image:
            Hpbar.original_width = Hpbar.background_image.w
            Hpbar.original_height = Hpbar.background_image.h

    def update(self, dt):
        # 6. update는 game_world에 의해 호출되지만,
        #    HP바는 Player의 HP를 draw 시점에만 읽어가면 되므로
        #    여기서는 할 일이 없습니다.
        pass

    def draw(self):
        # 7. 그리기 직전에 주인의 HP를 가져옴
        hp = self.owner.hp
        max_hp = self.owner.max_hp

        # 8. HP 바를 그릴 고정 위치 및 크기 정의
        SCALE = 3.0
        # (pico2d (0,0)은 좌하단. 1600x900 창이라고 가정)
        DRAW_X = 100  # 화면 왼쪽에서 250px
        DRAW_Y = 850  # 화면 아래에서 850px (좌상단)

        # 9. 스케일된 크기
        scaled_w = Hpbar.original_width * SCALE
        scaled_h = Hpbar.original_height * SCALE

        # 10. HP 백분율
        hp_percentage = max(0, min(1, hp / max_hp))

        # 11. 배경 그리기
        Hpbar.background_image.draw(DRAW_X, DRAW_Y, scaled_w, scaled_h)

        # 12. 채움 그리기 (클리핑)
        clip_w = int(Hpbar.original_width * hp_percentage)
        draw_w = int(clip_w * SCALE)
        offset = (draw_w - scaled_w) / 2
        draw_fill_x = DRAW_X + offset

        Hpbar.fill_image.clip_draw(
            0, 0,
            clip_w, Hpbar.original_height,
            draw_fill_x, DRAW_Y,
            draw_w, scaled_h
        )

    # (game_world가 요구하는 빈 함수들)
    def get_bb(self):
        return 0, 0, 0, 0

    def handle_collision(self, group, other):
        pass
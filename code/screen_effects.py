from pico2d import load_image, get_time

# --- 이 모듈이 관리할 싱글톤(Singleton) 객체 ---
_instance = None  # game_world에 추가될 ScreenFlash 객체 자체


# --- Player가 호출할 공용 함수 ---

def trigger(duration=0.1):
    """
    Player가 이 함수를 호출하여 깜빡임을 발동시킵니다.
    """
    if _instance:
        _instance.trigger_flash(duration)
    else:
        print("ERROR: ScreenFlash 객체가 game_world에 없습니다.")


def load(screen_width, screen_height):
    """
    main.py에서 이 함수를 호출하여 객체를 생성하고,
    생성된 객체를 game_world에 추가해야 합니다.
    """
    global _instance
    if _instance is None:
        _instance = ScreenFlash(screen_width, screen_height)
    return _instance


# --- game_world가 관리할 실제 클래스 ---

class ScreenFlash:
    image = None  # 1x1 흰색 픽셀

    def __init__(self, screen_width, screen_height):
        if ScreenFlash.image is None:
            # 🌟 'resource/white_pixel.png' 경로에 1x1 흰색 픽셀이 있어야 합니다.
            ScreenFlash.image = load_image('resource/Sprites/Ui/white_pixel.png')

        self.sw = screen_width
        self.sh = screen_height
        self.timer = 0.0
        self.duration = 0.1
        print("ScreenFlash 객체 생성됨 (game_world에 추가 대기)")

    def trigger_flash(self, duration):
        # 🌟 trigger() 함수를 통해 호출됨
        self.timer = duration
        self.duration = duration

    def update(self, dt):
        # 🌟 game_world가 매 프레임 호출
        if self.timer > 0:
            self.timer = max(0.0, self.timer - dt)

    def draw(self):
        # 🌟 game_world가 매 프레임 호출
        if self.timer > 0:
            # 1. 투명도 계산 (최대 50% -> 0%)
            opacity = (self.timer / self.duration) * 0.5
            ScreenFlash.image.opacify(opacity)

            # 2. 1x1 흰색 이미지를 화면 전체 크기로 늘려서 그림
            ScreenFlash.image.draw(self.sw / 2, self.sh / 2, self.sw, self.sh)

            # 3. 다음 프레임을 위해 투명도 복구
            ScreenFlash.image.opacify(1.0)

    # (game_world가 요구하는 빈 함수들)
    def get_bb(self):
        return 0, 0, 0, 0

    def handle_collision(self, group, other):
        pass
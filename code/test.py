import pico2d

# 스프라이트 시트 이미지 파일 이름
SPRITE_SHEET_NAME = 'resource/atran/atlas.png'
class Character:
    def __init__(self):
        self.image = pico2d.load_image(SPRITE_SHEET_NAME)

        # --- 추정된 스프라이트 프레임 정의 (수동 조정 필요!) ---

        # 1. 달리기/걷기 애니메이션 (왼쪽 세로줄, 대략적인 추정)
        # (left_x, bottom_y, width, height)
        # y 좌표는 대략 80픽셀 단위로 내려간다고 가정
        self.run_frames = [
            (0, 800, 40, 70),  # 첫 번째 프레임
            (0, 720, 40, 70),  # 두 번째 프레임
            (0, 640, 40, 70),
            (0, 560, 40, 70),
            (0, 480, 40, 70),
            (0, 400, 40, 70),
            (0, 320, 40, 70),
            (0, 240, 40, 70),
            (0, 160, 40, 70),
            (0, 80, 40, 70),
            (0, 0, 40, 70),    # 마지막 프레임 (이 줄의)
            # 다른 달리기 프레임이 다른 위치에 있다면 여기에 추가
            # 예: (100, 800, 40, 70), (100, 720, 40, 70), ...
        ]
        self.run_frame_index = 0

        # 2. 낙하산 애니메이션 (가장 아래줄, 대략적인 추정)
        # (left_x, bottom_y, width, height)
        # x 좌표는 대략 100픽셀 단위로 이동
        self.parachute_frames = [
            (0, 0, 100, 100),
            (100, 0, 100, 100),
            (200, 0, 100, 100),
            (300, 0, 100, 100),
            (400, 0, 100, 100),
            (500, 0, 100, 100),
            (600, 0, 100, 100),
            (700, 0, 100, 100),
        ]
        self.parachute_frame_index = 0

        # 초기 위치
        self.x, self.y = 400, 300

    def update(self):
        # 애니메이션 프레임 업데이트 로직
        self.run_frame_index = (self.run_frame_index + 1) % len(self.run_frames)
        self.parachute_frame_index = (self.parachute_frame_index + 1) % len(self.parachute_frames)

    def draw_run(self):
        # 현재 달리기 프레임 그리기
        current_frame_data = self.run_frames[self.run_frame_index]
        lx, by, w, h = current_frame_data
        self.image.clip_draw(lx, by, w, h, self.x, self.y)

    def draw_parachute(self):
        # 현재 낙하산 프레임 그리기
        current_frame_data = self.parachute_frames[self.parachute_frame_index]
        lx, by, w, h = current_frame_data
        self.image.clip_draw(lx, by, w, h, self.x + 50, self.y + 50) # 낙하산은 캐릭터보다 크게 조정

# --- pico2d 메인 루프 예시 ---
def handle_events():
    global running
    events = pico2d.get_events()
    for event in events:
        if event.type == pico2d.SDL_QUIT:
            running = False
        elif event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            running = False

def main():
    global running
    pico2d.open_canvas()

    character = Character()
    running = True

    while running:
        handle_events()
        character.update()

        pico2d.clear_canvas()
        character.draw_run()      # 달리기 애니메이션 그리기
        # character.draw_parachute() # 낙하산 애니메이션 그리기 (필요할 때 주석 해제)
        pico2d.update_canvas()

        pico2d.delay(0.1) # 0.1초마다 프레임 업데이트

    pico2d.close_canvas()

if __name__ == '__main__':
    main()
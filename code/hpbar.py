from pico2d import load_image

# 1. HP 바 이미지를 한 번만 로드하기 위한 전역 변수
background_image = None
fill_image = None


def load_images():
    """
    HP 바 시스템에 필요한 이미지들을 로드합니다.
    이 함수는 main.py에서 open_canvas() 호출 직후에 한 번만 호출되어야 합니다.
    """
    global background_image, fill_image

    if background_image is None:
        background_image = load_image('resource/Sprites/Ui/btl_gage_hp_back.png')
    if fill_image is None:
        fill_image = load_image('resource/btl_gage_hp.png')


def draw(x, y, hp, max_hp, bar_height_offset):
    """
    지정된 x, y 위치에 HP 바를 그립니다.
    (x, y)는 캐릭터의 중심 위치입니다.

    :param x: 캐릭터의 x 중심
    :param y: 캐릭터의 y 중심
    :param hp: 현재 HP
    :param max_hp: 최대 HP
    :param bar_height_offset: 캐릭터 y 위치에서 얼마나 높이 띄울지 (예: 50)
    """
    if background_image is None or fill_image is None:
        # 이미지가 로드되지 않았다면 아무것도 그리지 않음
        return

    # 1. HP 백분율 계산
    hp_percentage = max(0, min(1, hp / max_hp))

    # 2. HP에 따라 채워질 너비 계산
    fill_width = int(fill_image.w * hp_percentage)

    # 3. HP 바를 그릴 y 위치 계산
    draw_y = y + bar_height_offset

    # 4. HP 바 배경 그리기
    background_image.draw(x, draw_y)

    # 5. HP 바 채움 그리기 (clip_draw 사용)
    #    (왼쪽 정렬을 위해 x 좌표를 살짝 보정합니다)
    bar_center_x_offset = (fill_width - fill_image.w) / 2

    fill_image.clip_draw(
        0, 0,  # left, bottom (원본 이미지에서 자를 위치)
        fill_width, fill_image.h,  # width, height (원본 이미지에서 자를 크기)
        x + bar_center_x_offset, draw_y  # x, y (화면에 그릴 위치)
    )
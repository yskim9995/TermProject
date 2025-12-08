player = None
background = None


def world_to_screen(world_x, world_y):
    # 배경이 없으면 그냥 원래 좌표 반환 (에러 방지)
    if background is None:
        return world_x, world_y

    screen_x = world_x - background.window_left
    screen_y = world_y - background.window_bottom
    return screen_x, screen_y
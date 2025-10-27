from pico2d import load_image


class Grass:
    def __init__(self):
        self.image = load_image('resource/back.png')

    def draw(self):
        self.image.draw(1280/2, 720/2)

    def update(self):
        pass

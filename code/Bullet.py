from pico2d import load_image
import math

class Bullet:
    def __init__(self, x, y, angle, speed=800, owner=None, damage=10):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.owner = owner
        self.damage = damage
        self.image = load_image('resource/Sprites/GunsPack/Bullets/RifleAmmoSmall.png')
        self.alive = True
        self.hit_enemies = set()

    def update(self, dt):
        if not self.alive:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        # 화면 밖이면 제거 플래그
        if self.x < -100 or self.x > 2000 or self.y < -100 or self.y > 2000:
            self.alive = False

    def draw(self):
        if self.alive:
            self.image.draw(self.x, self.y)

    def get_bb(self):
        half = 6
        return (self.x - half, self.y - half, self.x + half, self.y + half)
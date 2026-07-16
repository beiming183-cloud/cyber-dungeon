import pygame
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE


# ==================== 系统模块 ====================
class Camera:
    def __init__(self):
        self.offset = pygame.math.Vector2(0, 0)
        self.shake_timer = 0

    def update(self, target):
        # 平滑跟随
        self.offset.x += (target.rect.centerx - SCREEN_WIDTH // 2 - self.offset.x) * 0.1
        self.offset.y += (target.rect.centery - SCREEN_HEIGHT // 2 - self.offset.y) * 0.1

        # 震动
        if self.shake_timer > 0:
            self.offset.x += random.randint(-5, 5)
            self.offset.y += random.randint(-5, 5)
            self.shake_timer -= 1

    def apply(self, x, y):
        return int(x - self.offset.x), int(y - self.offset.y)

    def apply_rect(self, rect):
        return pygame.Rect(rect.x - self.offset.x, rect.y - self.offset.y, rect.width, rect.height)

    def shake(self, intensity=10):
        self.shake_timer = intensity


class DungeonGenerator:
    """简单的地牢生成器"""

    def generate(self, w, h):
        tiles = [[1] * w for _ in range(h)]  # 1=Wall, 0=Floor
        rooms = []

        for _ in range(20):
            rw = random.randint(6, 12)
            rh = random.randint(6, 12)
            rx = random.randint(1, w - rw - 1)
            ry = random.randint(1, h - rh - 1)

            new_room = pygame.Rect(rx, ry, rw, rh)

            # 挖空房间
            for y in range(new_room.top, new_room.bottom):
                for x in range(new_room.left, new_room.right):
                    tiles[y][x] = 0

            if rooms:
                # 连接到上一个房间
                prev = rooms[-1]
                self.carve_tunnel(tiles, prev.center, new_room.center)

            rooms.append(new_room)

        return tiles, rooms

    def carve_tunnel(self, tiles, p1, p2):
        x1, y1 = int(p1[0]), int(p1[1])
        x2, y2 = int(p2[0]), int(p2[1])

        # 水平走廊
        start, end = min(x1, x2), max(x1, x2)
        for x in range(start, end + 1):
            tiles[y1][x] = 0
            tiles[y1 + 1][x] = 0

        # 垂直走廊
        start, end = min(y1, y2), max(y1, y2)
        for y in range(start, end + 1):
            tiles[y][x2] = 0
            tiles[y][x2 + 1] = 0







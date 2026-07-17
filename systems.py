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
    """Generate a readable west-to-east main route with optional side rooms."""

    def generate(self, w, h):
        tiles = [[1] * w for _ in range(h)]  # 1=Wall, 0=Floor
        main_rooms = []
        route_count = 18
        previous_y = random.randint(9, h - 10)

        # The critical path always advances east. Vertical movement changes
        # gradually so the player reads it as a route instead of random noise.
        for index in range(route_count):
            rw = random.randint(7, 10)
            rh = random.randint(7, 10)
            center_x = int(5 + index * ((w - 10) / (route_count - 1)))
            if index:
                previous_y = max(6, min(h - 7, previous_y + random.randint(-7, 7)))
            rx = max(1, min(w - rw - 1, center_x - rw // 2))
            ry = max(1, min(h - rh - 1, previous_y - rh // 2))
            room = pygame.Rect(rx, ry, rw, rh)
            self.carve_room(tiles, room)
            if main_rooms:
                self.carve_tunnel(tiles, main_rooms[-1].center, room.center)
            main_rooms.append(room)

        branch_rooms = []
        for _ in range(24):
            anchor = random.choice(main_rooms[1:-1])
            rw = random.randint(6, 9)
            rh = random.randint(6, 9)
            side = random.choice((-1, 1))
            center_x = anchor.centerx + random.randint(-5, 5)
            center_y = anchor.centery + side * random.randint(9, 15)
            rx = max(1, min(w - rw - 1, center_x - rw // 2))
            ry = max(1, min(h - rh - 1, center_y - rh // 2))
            room = pygame.Rect(rx, ry, rw, rh)
            self.carve_room(tiles, room)
            self.carve_tunnel(tiles, anchor.center, room.center)
            branch_rooms.append(room)

        self.main_rooms = main_rooms
        self.route_points = [room.center for room in main_rooms]
        return tiles, main_rooms + branch_rooms

    @staticmethod
    def carve_room(tiles, room):
        for y in range(room.top, room.bottom):
            for x in range(room.left, room.right):
                tiles[y][x] = 0

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







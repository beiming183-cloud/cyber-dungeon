import pygame
import random
import math
from config import TILE_SIZE, FONT_ICON, WHITE, YELLOW, NEON_BLUE


# ==================== 视觉特效系统 ====================
class VisualUtils:
    """处理图像生成的工厂类"""

    @staticmethod
    def create_emoji_surface(emoji, color, size=TILE_SIZE):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        try:
            # 尝试渲染Emoji
            text = FONT_ICON.render(emoji, True, color)
            rect = text.get_rect(center=(size // 2, size // 2))
            surf.blit(text, rect)
        except:
            # 失败则画圆
            pygame.draw.circle(surf, color, (size // 2, size // 2), size // 3)
        return surf

    @staticmethod
    def draw_magic_circle(surface, x, y, color, radius, angle):
        """绘制旋转的魔法阵 - 增强版"""
        cx, cy = int(x), int(y)

        # 多层魔法阵
        for i, r in enumerate([radius, radius * 0.7, radius * 0.4]):
            alpha = 255 - i * 50
            # 外圈
            s = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color[:3], alpha), (int(r) + 5, int(r) + 5), int(r), 2)

            # 内接旋转多边形
            sides = 6 if i == 0 else 4
            points = []
            for j in range(sides):
                theta = math.radians(angle + i * 30 + j * (360 / sides))
                px = r + 5 + math.cos(theta) * r
                py = r + 5 + math.sin(theta) * r
                points.append((px, py))
            pygame.draw.lines(s, (*color[:3], alpha), True, points, 2)

            surface.blit(s, (cx - r - 5, cy - r - 5))

        # 中心发光点
        s = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color[:3], 200), (5, 5), 3)
        surface.blit(s, (cx - 5, cy - 5))

    @staticmethod
    def draw_aura(surface, x, y, color, radius, pulse):
        """绘制能量光环"""
        cx, cy = int(x), int(y)
        for i in range(3):
            r = radius + pulse + i * 5
            alpha = 100 - i * 30
            s = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color[:3], alpha), (int(r) + 10, int(r) + 10), int(r), 1)
            surface.blit(s, (cx - r - 10, cy - r - 10))


class Particle:
    def __init__(self, x, y, color, particle_type='normal'):
        self.x, self.y = x, y
        self.color = color
        self.particle_type = particle_type

        if particle_type == 'spark':
            # 火花粒子 - 快速飞溅
            self.vx = random.uniform(-5, 5)
            self.vy = random.uniform(-5, 5)
            self.life = random.randint(15, 30)
            self.size = random.randint(3, 6)
        elif particle_type == 'smoke':
            # 烟雾粒子 - 缓慢上升
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(-3, -1)
            self.life = random.randint(40, 60)
            self.size = random.randint(4, 8)
        elif particle_type == 'energy':
            # 能量粒子 - 螺旋运动
            self.angle = random.uniform(0, math.pi * 2)
            self.angular_speed = random.uniform(0.1, 0.3)
            self.radius = random.uniform(5, 20)
            self.vx = 0
            self.vy = 0
            self.life = random.randint(30, 50)
            self.size = random.randint(2, 4)
        else:
            # 普通粒子
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(-2, 2)
            self.life = random.randint(20, 40)
            self.size = random.randint(2, 5)

        self.max_life = self.life
        self.start_x, self.start_y = x, y

    def update(self):
        if self.particle_type == 'energy':
            # 螺旋运动
            self.angle += self.angular_speed
            self.radius += 0.5
            self.x = self.start_x + math.cos(self.angle) * self.radius
            self.y = self.start_y + math.sin(self.angle) * self.radius
        else:
            self.x += self.vx
            self.y += self.vy

        self.life -= 1
        self.size = max(0, self.size - 0.1)
        return self.life > 0

    def draw(self, surface, camera):
        pos = camera.apply(self.x, self.y)
        alpha = int(255 * (self.life / self.max_life))

        if self.particle_type == 'spark':
            # 火花 - 亮色闪烁
            s = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color[:3], alpha), (6, 6), int(self.size))
            pygame.draw.circle(s, (255, 255, 255, alpha // 2), (6, 6), int(self.size // 2))
            surface.blit(s, (pos[0] - 6, pos[1] - 6))
        elif self.particle_type == 'smoke':
            # 烟雾 - 半透明扩散
            s = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color[:3], alpha // 2), (8, 8), int(self.size))
            surface.blit(s, (pos[0] - 8, pos[1] - 8))
        elif self.particle_type == 'energy':
            # 能量 - 发光点
            s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color[:3], alpha), (5, 5), int(self.size))
            pygame.draw.circle(s, (255, 255, 255, alpha), (5, 5), 1)
            surface.blit(s, (pos[0] - 5, pos[1] - 5))
        else:
            # 普通粒子
            s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color[:3], alpha), (5, 5), int(self.size))
            surface.blit(s, (pos[0] - 5, pos[1] - 5))











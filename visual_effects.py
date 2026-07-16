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
    def create_character_icon(character_type, color, size=88):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        line = max(2, size // 28)
        pygame.draw.circle(surf, (*color[:3], 24), (center, center), size // 2 - 5)
        pygame.draw.circle(surf, color, (center, center), size // 2 - 8, line)

        if character_type == 'cyber_mage':
            pygame.draw.circle(surf, color, (center, center), size // 5, line)
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                inner = (center + math.cos(rad) * size * 0.18, center + math.sin(rad) * size * 0.18)
                outer = (center + math.cos(rad) * size * 0.34, center + math.sin(rad) * size * 0.34)
                pygame.draw.line(surf, color, inner, outer, line)
        elif character_type == 'mech_ranger':
            pygame.draw.circle(surf, color, (center, center), size // 4, line)
            pygame.draw.circle(surf, WHITE, (center, center), size // 12, line)
            pygame.draw.line(surf, color, (center, 12), (center, center - size // 4), line)
            pygame.draw.line(surf, color, (center, center + size // 4), (center, size - 12), line)
            pygame.draw.line(surf, color, (12, center), (center - size // 4, center), line)
            pygame.draw.line(surf, color, (center + size // 4, center), (size - 12, center), line)
        elif character_type == 'bio_berserker':
            pygame.draw.line(surf, color, (24, size - 20), (size - 24, 20), line + 2)
            pygame.draw.line(surf, color, (20, 24), (size - 20, size - 24), line + 2)
            pygame.draw.circle(surf, WHITE, (center, center), size // 10, line)
        elif character_type == 'shadow_assassin':
            points = [(center, 14), (size - 18, center), (center, size - 14), (18, center)]
            pygame.draw.polygon(surf, color, points, line)
            pygame.draw.line(surf, color, (center, 22), (center, size - 22), line)
            pygame.draw.circle(surf, WHITE, (center, center), size // 13)
        else:
            shield = [
                (center, 14),
                (size - 18, 26),
                (size - 24, size - 30),
                (center, size - 12),
                (24, size - 30),
                (18, 26),
            ]
            pygame.draw.polygon(surf, color, shield, line)
            pygame.draw.line(surf, WHITE, (center, 26), (center, size - 30), line)
            pygame.draw.line(surf, WHITE, (center - 14, center), (center + 14, center), line)
        return surf

    @staticmethod
    def create_talent_icon(talent_type, color, size=76):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        line = max(2, size // 25)
        pygame.draw.circle(surf, (*color[:3], 28), (center, center), center - 4)
        if talent_type == 'combat':
            pygame.draw.line(surf, color, (20, size - 18), (size - 18, 18), line + 2)
            pygame.draw.line(surf, color, (18, 18), (size - 20, size - 18), line + 2)
            pygame.draw.circle(surf, WHITE, (center, center), 5)
        elif talent_type == 'survival':
            shield = [(center, 10), (size - 16, 22), (size - 22, size - 24), (center, size - 10), (22, size - 24), (16, 22)]
            pygame.draw.polygon(surf, color, shield, line)
            pygame.draw.line(surf, WHITE, (center, 22), (center, size - 24), line)
        else:
            pygame.draw.circle(surf, color, (center, center), center - 12, line)
            pygame.draw.polygon(surf, WHITE, [(center, 16), (center + 7, center), (center, size - 16), (center - 7, center)])
        return surf

    @staticmethod
    def create_skill_icon(skill_id, color, size=48):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        line = max(2, size // 18)
        skill_id = str(skill_id or '').lower()
        pygame.draw.circle(surf, (*color[:3], 30), (c, c), c - 3)

        if any(key in skill_id for key in ('shield', 'guard', 'armor', 'defense')):
            points = [(c, 6), (size - 8, 13), (size - 12, size - 14), (c, size - 5), (12, size - 14), (8, 13)]
            pygame.draw.polygon(surf, color, points, line)
        elif any(key in skill_id for key in ('lightning', 'thunder', 'emp')):
            points = [(c + 3, 4), (11, c + 2), (c - 2, c + 2), (c - 6, size - 4), (size - 10, c - 5), (c + 3, c - 5)]
            pygame.draw.polygon(surf, color, points)
        elif any(key in skill_id for key in ('fire', 'pyro', 'meteor', 'explosion')):
            points = [(c, 5), (size - 10, c + 7), (c, size - 5), (10, c + 7)]
            pygame.draw.polygon(surf, color, points)
            pygame.draw.circle(surf, WHITE, (c, c + 7), max(3, size // 10))
        elif any(key in skill_id for key in ('ice', 'frost', 'freeze')):
            for angle in range(0, 180, 45):
                rad = math.radians(angle)
                dx, dy = math.cos(rad) * (c - 7), math.sin(rad) * (c - 7)
                pygame.draw.line(surf, color, (c - dx, c - dy), (c + dx, c + dy), line)
            pygame.draw.circle(surf, WHITE, (c, c), max(2, size // 12))
        elif any(key in skill_id for key in ('gravity', 'orb')):
            pygame.draw.circle(surf, color, (c, c), c - 7, line)
            pygame.draw.circle(surf, color, (c, c), c // 2, line)
            pygame.draw.circle(surf, WHITE, (c, c), max(2, size // 12))
        elif any(key in skill_id for key in ('auto', 'rapid', 'sniper', 'arrow', 'missile')):
            pygame.draw.circle(surf, color, (c, c), c - 9, line)
            pygame.draw.line(surf, color, (c, 3), (c, size - 3), line)
            pygame.draw.line(surf, color, (3, c), (size - 3, c), line)
            pygame.draw.circle(surf, WHITE, (c, c), max(2, size // 12))
        elif any(key in skill_id for key in ('heal', 'holy', 'immortal')):
            pygame.draw.line(surf, color, (c, 8), (c, size - 8), line + 1)
            pygame.draw.line(surf, color, (8, c), (size - 8, c), line + 1)
        elif any(key in skill_id for key in ('decoy', 'shadow', 'clone')):
            pygame.draw.polygon(surf, color, [(c, 5), (size - 7, c), (c, size - 5), (7, c)], line)
            pygame.draw.polygon(surf, WHITE, [(c, 13), (size - 15, c), (c, size - 13), (15, c)], line)
        elif 'boomerang' in skill_id:
            pygame.draw.arc(surf, color, (7, 7, size - 14, size - 14), math.radians(20), math.radians(300), line + 1)
            pygame.draw.polygon(surf, color, [(size - 13, 8), (size - 5, 16), (size - 18, 18)])
        else:
            points = [(c, 5), (size - 7, c // 2), (size - 7, size - c // 2), (c, size - 5), (7, size - c // 2), (7, c // 2)]
            pygame.draw.polygon(surf, color, points, line)
            pygame.draw.circle(surf, WHITE, (c, c), max(2, size // 12))
        return surf

    @staticmethod
    def create_enemy_icon(kind, color, size=40, elite=False):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        line = max(2, size // 18)
        kind = str(kind)

        if kind == 'dragon':
            wing = [(c, c), (3, 9), (8, c + 9), (c - 6, c + 4)]
            pygame.draw.polygon(surf, (*color[:3], 150), wing)
            pygame.draw.polygon(surf, (*color[:3], 150), [(size - x, y) for x, y in wing])
            head = [(c, 5), (size - 12, c - 2), (c + 10, size - 8), (c, size - 3), (c - 10, size - 8), (12, c - 2)]
            pygame.draw.polygon(surf, color, head)
            pygame.draw.polygon(surf, WHITE, head, line)
            pygame.draw.polygon(surf, color, [(c - 9, 9), (c - 18, 1), (c - 14, 16)])
            pygame.draw.polygon(surf, color, [(c + 9, 9), (c + 18, 1), (c + 14, 16)])
            pygame.draw.circle(surf, UI_ACCENT if 'UI_ACCENT' in globals() else YELLOW, (c - 6, c - 3), max(2, size // 20))
            pygame.draw.circle(surf, UI_ACCENT if 'UI_ACCENT' in globals() else YELLOW, (c + 6, c - 3), max(2, size // 20))
        elif kind == 'slime':
            pygame.draw.ellipse(surf, color, (5, c - 3, size - 10, c + 1))
            pygame.draw.circle(surf, WHITE, (c - 6, c + 2), max(2, size // 14))
            pygame.draw.circle(surf, WHITE, (c + 6, c + 2), max(2, size // 14))
        elif kind == 'bat':
            pygame.draw.polygon(surf, color, [(c, 8), (4, c - 5), (10, size - 7), (c, c + 5), (size - 10, size - 7), (size - 4, c - 5)])
            pygame.draw.circle(surf, WHITE, (c, c), max(2, size // 12))
        elif kind == 'spider':
            pygame.draw.circle(surf, color, (c, c), c // 3)
            for offset in (-9, -3, 3, 9):
                pygame.draw.line(surf, color, (c + offset // 2, c), (4 if offset < 0 else size - 4, c + offset), line)
        elif kind == 'skeleton':
            pygame.draw.circle(surf, color, (c, c - 4), c - 8, line)
            pygame.draw.circle(surf, WHITE, (c - 6, c - 5), 3)
            pygame.draw.circle(surf, WHITE, (c + 6, c - 5), 3)
            pygame.draw.line(surf, color, (c - 8, c + 8), (c + 8, c + 8), line)
        elif kind == 'ghost':
            points = [(c, 5), (size - 7, c), (size - 9, size - 7), (c + 5, size - 13), (c, size - 7), (c - 5, size - 13), (9, size - 7), (7, c)]
            pygame.draw.polygon(surf, color, points, line)
            pygame.draw.circle(surf, WHITE, (c - 6, c - 4), 3)
            pygame.draw.circle(surf, WHITE, (c + 6, c - 4), 3)
        else:
            pygame.draw.polygon(surf, color, [(c, 4), (size - 5, c), (c, size - 4), (5, c)])
            pygame.draw.circle(surf, WHITE, (c - 6, c), 3)
            pygame.draw.circle(surf, WHITE, (c + 6, c), 3)

        if elite:
            pygame.draw.circle(surf, YELLOW, (c, c), c - 2, line)
        return surf

    @staticmethod
    def create_item_icon(item_type, color, size=40):
        return VisualUtils.create_skill_icon(item_type, color, size)

    @staticmethod
    def create_weapon_icon(char_type, color, size=32):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        pygame.draw.line(surf, color, (c, 3), (c, size - 6), max(3, size // 8))
        pygame.draw.polygon(surf, WHITE, [(c, 1), (c - 6, 9), (c + 6, 9)])
        pygame.draw.line(surf, color, (c - 8, size - 8), (c + 8, size - 8), 3)
        return surf

    @staticmethod
    def create_chest_icon(color, size=50):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        body = pygame.Rect(5, size // 3, size - 10, size // 2)
        pygame.draw.rect(surf, (70, 45, 24), body, border_radius=4)
        pygame.draw.rect(surf, color, body, 3, border_radius=4)
        pygame.draw.arc(surf, color, (8, 5, size - 16, size // 2), math.pi, math.pi * 2, 4)
        lock = pygame.Rect(size // 2 - 4, size // 2, 8, 12)
        pygame.draw.rect(surf, WHITE, lock, border_radius=2)
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











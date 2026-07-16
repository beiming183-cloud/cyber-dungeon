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
        line = max(1, size // 28)
        armor = (8, 12, 22)
        armor_hi = (28, 36, 52)
        energy = tuple(min(255, channel + 70) for channel in color[:3])

        def p(x, y):
            return (int(size * x / 100), int(size * y / 100))

        def poly(points, fill, width=0):
            pygame.draw.polygon(surf, fill, [p(x, y) for x, y in points], width)

        # Every hero owns a different silhouette. The dark armor makes the neon
        # read as powered seams instead of a recolored wireframe.
        if character_type == 'cyber_mage':
            poly([(18, 80), (25, 43), (38, 27), (50, 18), (62, 27), (75, 43), (82, 80), (64, 92), (36, 92)], armor)
            poly([(29, 43), (38, 24), (50, 10), (62, 24), (71, 43), (61, 38), (50, 43), (39, 38)], color)
            poly([(35, 43), (50, 31), (65, 43), (60, 58), (40, 58)], armor_hi)
            pygame.draw.line(surf, energy, p(39, 47), p(61, 47), line + 1)
            poly([(22, 48), (10, 39), (14, 66), (27, 72)], armor_hi)
            poly([(78, 48), (90, 39), (86, 66), (73, 72)], armor_hi)
            pygame.draw.circle(surf, color, p(50, 70), max(2, size // 10), line)
            pygame.draw.circle(surf, WHITE, p(50, 70), max(1, size // 28))
            pygame.draw.line(surf, color, p(29, 60), p(19, 86), line)
            pygame.draw.line(surf, color, p(71, 60), p(81, 86), line)
        elif character_type == 'mech_ranger':
            poly([(18, 83), (22, 43), (34, 30), (38, 14), (57, 8), (72, 25), (76, 48), (84, 84), (61, 92), (37, 92)], armor)
            poly([(31, 31), (39, 16), (58, 12), (70, 28), (64, 50), (38, 50)], armor_hi)
            poly([(37, 31), (66, 27), (61, 40), (41, 42)], energy)
            pygame.draw.line(surf, WHITE, p(42, 34), p(60, 31), line)
            pygame.draw.line(surf, color, p(57, 10), p(74, 2), line + 1)
            pygame.draw.circle(surf, energy, p(76, 2), max(1, size // 25))
            poly([(17, 48), (5, 53), (7, 70), (25, 67)], armor_hi)
            poly([(75, 45), (94, 39), (96, 52), (78, 58)], armor_hi)
            pygame.draw.rect(surf, color, pygame.Rect(*p(78, 42), max(2, size // 6), max(2, size // 16)))
            pygame.draw.circle(surf, color, p(50, 68), max(2, size // 11), line)
            pygame.draw.line(surf, color, p(31, 73), p(21, 91), line + 1)
            pygame.draw.line(surf, color, p(68, 73), p(79, 91), line + 1)
        elif character_type == 'bio_berserker':
            poly([(5, 82), (12, 42), (27, 27), (34, 12), (46, 23), (54, 23), (66, 12), (73, 27), (88, 42), (95, 82), (69, 94), (31, 94)], armor)
            poly([(19, 42), (4, 34), (9, 65), (30, 63)], color)
            poly([(81, 42), (96, 34), (91, 65), (70, 63)], color)
            poly([(31, 31), (38, 18), (50, 28), (62, 18), (69, 31), (63, 51), (37, 51)], armor_hi)
            poly([(38, 37), (46, 33), (46, 42), (38, 42)], energy)
            poly([(62, 37), (54, 33), (54, 42), (62, 42)], energy)
            pygame.draw.line(surf, color, p(42, 52), p(35, 76), line + 2)
            pygame.draw.line(surf, color, p(58, 52), p(65, 76), line + 2)
            pygame.draw.circle(surf, energy, p(50, 70), max(2, size // 9))
            pygame.draw.circle(surf, armor, p(50, 70), max(1, size // 18))
            poly([(15, 68), (4, 82), (25, 78)], energy)
            poly([(85, 68), (96, 82), (75, 78)], energy)
        elif character_type == 'shadow_assassin':
            poly([(16, 86), (23, 46), (34, 27), (50, 7), (66, 27), (77, 46), (84, 86), (62, 94), (38, 94)], armor)
            poly([(24, 43), (50, 6), (76, 43), (63, 34), (50, 43), (37, 34)], color)
            poly([(31, 42), (50, 28), (69, 42), (61, 55), (39, 55)], armor_hi)
            poly([(36, 43), (47, 39), (45, 47), (35, 47)], energy)
            poly([(64, 43), (53, 39), (55, 47), (65, 47)], energy)
            pygame.draw.line(surf, color, p(30, 58), p(13, 83), line + 1)
            pygame.draw.line(surf, color, p(70, 58), p(87, 83), line + 1)
            poly([(25, 69), (8, 91), (36, 79)], armor_hi)
            poly([(75, 69), (92, 91), (64, 79)], armor_hi)
            pygame.draw.line(surf, energy, p(40, 67), p(60, 67), line)
        else:  # holy_knight
            poly([(10, 84), (17, 42), (31, 31), (34, 14), (50, 3), (66, 14), (69, 31), (83, 42), (90, 84), (66, 95), (34, 95)], armor)
            poly([(34, 17), (50, 5), (66, 17), (62, 50), (38, 50)], armor_hi)
            poly([(47, 10), (53, 10), (55, 37), (50, 47), (45, 37)], color)
            pygame.draw.line(surf, WHITE, p(39, 34), p(61, 34), line + 1)
            poly([(18, 39), (3, 49), (8, 73), (31, 65)], color)
            poly([(82, 39), (97, 49), (92, 73), (69, 65)], color)
            poly([(33, 57), (50, 66), (67, 57), (63, 86), (50, 94), (37, 86)], armor_hi)
            pygame.draw.line(surf, color, p(50, 64), p(50, 87), line + 1)
            pygame.draw.line(surf, color, p(40, 75), p(60, 75), line + 1)
            pygame.draw.circle(surf, WHITE, p(50, 75), max(1, size // 30))
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
        line = max(1, size // 22)
        skill_id = str(skill_id or '').lower()
        ink = color[:3]
        bright = tuple(min(255, channel + 80) for channel in ink)
        dark = (8, 11, 20)

        def p(x, y):
            return (int(size * x / 100), int(size * y / 100))

        def poly(points, fill=ink, width=0):
            pygame.draw.polygon(surf, fill, [p(x, y) for x, y in points], width)

        def path(points, fill=ink, width=line, closed=False):
            pygame.draw.lines(surf, fill, closed, [p(x, y) for x, y in points], width)

        def circle(x, y, radius, fill=ink, width=0):
            pygame.draw.circle(surf, fill, p(x, y), max(1, int(size * radius / 100)), width)

        # A restrained hex frame unifies the UI while every glyph below is
        # authored for one mechanic. No skill shares a recolored base mark.
        poly([(50, 3), (89, 25), (89, 75), (50, 97), (11, 75), (11, 25)], (*ink, 24))

        if skill_id == 'basic_cyber_mage':
            circle(50, 50, 21, ink, line)
            circle(50, 50, 8, WHITE)
            for angle in (0, 120, 240):
                rad = math.radians(angle)
                path([(50 + math.cos(rad) * 20, 50 + math.sin(rad) * 20),
                      (50 + math.cos(rad) * 42, 50 + math.sin(rad) * 42)], bright, line)
        elif skill_id == 'basic_mech_ranger':
            poly([(7, 39), (70, 39), (94, 50), (70, 61), (7, 61)], ink)
            path([(14, 50), (82, 50)], WHITE, line)
            poly([(27, 25), (57, 25), (66, 39), (22, 39)], bright)
        elif skill_id == 'basic_bio_berserker':
            pygame.draw.arc(surf, ink, pygame.Rect(p(5, 5), p(90, 90)), .25, 3.0, line + 3)
            poly([(8, 59), (3, 28), (32, 43)], bright)
            path([(27, 74), (77, 24)], WHITE, line + 1)
        elif skill_id == 'basic_shadow_assassin':
            poly([(7, 75), (70, 12), (94, 6), (84, 31), (29, 89)], ink)
            path([(17, 77), (80, 17)], WHITE, line)
            path([(5, 43), (36, 43)], bright, line)
        elif skill_id == 'basic_holy_knight':
            poly([(43, 4), (57, 4), (62, 67), (50, 94), (38, 67)], bright)
            path([(50, 12), (50, 82)], WHITE, line)
            poly([(18, 41), (82, 41), (71, 57), (29, 57)], ink)
        elif skill_id == 'pyro_orb':
            poly([(12, 73), (38, 55), (28, 49), (57, 37), (50, 27), (82, 32), (68, 45), (88, 51), (62, 58), (68, 71), (43, 65)], ink)
            circle(58, 49, 13, bright)
            circle(61, 46, 5, WHITE)
        elif skill_id == 'frost_spear':
            poly([(14, 82), (39, 45), (45, 18), (55, 3), (61, 26), (57, 47), (86, 17), (63, 58), (48, 61)], bright)
            path([(17, 84), (83, 18)], WHITE, line)
            path([(33, 64), (21, 55), (40, 55)], ink, line)
        elif skill_id == 'thunder_chain_storm':
            poly([(17, 42), (27, 20), (47, 18), (58, 7), (76, 20), (86, 42), (72, 52), (29, 52)], ink)
            poly([(32, 48), (20, 77), (36, 72), (29, 96), (54, 62), (40, 66)], bright)
            poly([(57, 48), (49, 74), (62, 70), (58, 94), (82, 61), (68, 66)], WHITE)
            path([(16, 35), (7, 23)], bright, line)
            path([(85, 35), (95, 21)], bright, line)
        elif skill_id == 'chain_lightning':
            poly([(56, 4), (22, 48), (47, 45), (35, 94), (82, 36), (56, 40)], ink)
            path([(18, 22), (36, 31), (46, 17)], bright, line)
            circle(17, 21, 5, WHITE)
            circle(47, 16, 5, WHITE)
            circle(82, 75, 5, WHITE)
            path([(62, 59), (80, 74)], bright, line)
        elif skill_id == 'shadow_nova':
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                path([(50 + math.cos(rad) * 22, 50 + math.sin(rad) * 22),
                      (50 + math.cos(rad) * 44, 50 + math.sin(rad) * 44)], ink, line + 1)
            circle(50, 50, 25, ink)
            circle(58, 43, 22, dark)
            circle(42, 58, 5, WHITE)
        elif skill_id == 'holy_beam':
            poly([(44, 4), (56, 4), (61, 74), (50, 96), (39, 74)], bright)
            poly([(39, 35), (7, 50), (38, 58), (50, 47)], ink)
            poly([(61, 35), (93, 50), (62, 58), (50, 47)], ink)
            path([(50, 10), (50, 84)], WHITE, line)
        elif skill_id == 'rapid_fire':
            for offset in (28, 50, 72):
                poly([(14, offset - 7), (59, offset - 7), (72, offset), (59, offset + 7), (14, offset + 7)], ink)
            poly([(71, 18), (94, 50), (71, 82), (78, 50)], bright)
        elif skill_id == 'scatter_arrow':
            for end_y in (12, 31, 50, 69, 88):
                path([(14, 50), (79, end_y)], ink, line)
                poly([(79, end_y), (68, end_y - 6), (68, end_y + 6)], bright)
            circle(13, 50, 6, WHITE)
        elif skill_id == 'tracking_missile':
            poly([(20, 78), (34, 35), (65, 12), (84, 16), (88, 35), (65, 66)], ink)
            poly([(32, 58), (13, 91), (46, 72)], bright)
            circle(67, 31, 8, WHITE, line)
            pygame.draw.arc(surf, bright, pygame.Rect(*p(43, 7), int(size * .52), int(size * .52)), 0, math.pi * 1.5, line)
        elif skill_id == 'emp_blast':
            circle(50, 50, 11, WHITE)
            for radius in (25, 40):
                pygame.draw.arc(surf, ink, pygame.Rect(p(50-radius, 50-radius), p(radius*2, radius*2)), .25, 2.65, line)
                pygame.draw.arc(surf, ink, pygame.Rect(p(50-radius, 50-radius), p(radius*2, radius*2)), 3.4, 5.8, line)
            poly([(50, 17), (42, 49), (54, 46), (47, 82), (66, 40), (54, 44)], bright)
        elif skill_id == 'sniper_round':
            circle(50, 50, 33, ink, line)
            circle(50, 50, 9, WHITE, line)
            path([(50, 3), (50, 30)], bright, line)
            path([(50, 70), (50, 97)], bright, line)
            path([(3, 50), (30, 50)], bright, line)
            path([(70, 50), (97, 50)], bright, line)
            poly([(18, 79), (67, 30), (82, 18), (71, 36), (29, 86)], ink)
        elif skill_id == 'cyclone_slash':
            pygame.draw.arc(surf, ink, pygame.Rect(p(8, 8), p(84, 84)), .2, 3.0, line + 2)
            pygame.draw.arc(surf, bright, pygame.Rect(p(18, 18), p(64, 64)), 3.35, 6.1, line + 2)
            poly([(8, 54), (4, 28), (28, 39)], ink)
            poly([(92, 46), (96, 72), (72, 61)], bright)
        elif skill_id == 'earth_shock':
            poly([(32, 11), (68, 11), (79, 38), (65, 57), (35, 57), (21, 38)], ink)
            path([(50, 54), (40, 71), (50, 79), (38, 96)], bright, line + 1)
            path([(32, 61), (15, 75), (31, 80)], ink, line)
            path([(68, 61), (85, 75), (69, 80)], ink, line)
        elif skill_id == 'blood_rage':
            poly([(50, 91), (12, 48), (17, 21), (40, 17), (50, 32), (60, 17), (83, 21), (88, 48)], ink)
            poly([(26, 28), (40, 49), (34, 65)], WHITE)
            poly([(74, 28), (60, 49), (66, 65)], WHITE)
            path([(50, 32), (43, 52), (55, 59), (47, 80)], bright, line)
        elif skill_id == 'berserk_charge':
            poly([(5, 50), (41, 15), (41, 35), (76, 35), (95, 50), (76, 65), (41, 65), (41, 85)], ink)
            poly([(52, 25), (67, 8), (61, 38)], bright)
            poly([(52, 75), (67, 92), (61, 62)], bright)
            path([(14, 50), (83, 50)], WHITE, line)
        elif skill_id == 'bio_explosion':
            circle(50, 50, 10, WHITE)
            for angle in (0, 120, 240):
                rad = math.radians(angle)
                x, y = 50 + math.cos(rad) * 27, 50 + math.sin(rad) * 27
                circle(x, y, 13, ink, line)
                path([(50 + math.cos(rad) * 10, 50 + math.sin(rad) * 10), (x, y)], bright, line)
            circle(50, 50, 42, bright, line)
        elif skill_id == 'shadow_dash':
            poly([(8, 76), (69, 15), (92, 9), (82, 32), (28, 88)], ink)
            path([(5, 43), (39, 43)], bright, line)
            path([(9, 58), (31, 58)], bright, line)
            path([(19, 72), (27, 72)], WHITE, line)
        elif skill_id == 'assassinate':
            circle(50, 50, 35, ink, line)
            circle(50, 50, 7, WHITE)
            poly([(13, 84), (62, 35), (83, 17), (68, 42), (25, 91)], bright)
            poly([(87, 84), (38, 35), (17, 17), (32, 42), (75, 91)], ink, line)
        elif skill_id == 'mirror_clone':
            for offset in (-17, 17):
                x = 50 + offset
                poly([(x, 10), (x + 16, 27), (x + 12, 70), (x, 90), (x - 12, 70), (x - 16, 27)], ink if offset < 0 else bright, line)
                path([(x - 7, 40), (x + 7, 40)], WHITE, line)
            path([(50, 16), (50, 85)], dark, line + 1)
        elif skill_id == 'poison_edge':
            poly([(17, 88), (43, 50), (65, 9), (73, 18), (57, 58), (30, 93)], ink)
            path([(30, 74), (63, 21)], WHITE, line)
            circle(72, 63, 7, bright)
            circle(82, 78, 5, bright)
            circle(60, 83, 4, bright)
        elif skill_id == 'shadow_storm':
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                x, y = 50 + math.cos(rad) * 31, 50 + math.sin(rad) * 31
                tip_x, tip_y = 50 + math.cos(rad + .38) * 45, 50 + math.sin(rad + .38) * 45
                poly([(x, y), (tip_x, tip_y), (50 + math.cos(rad) * 18, 50 + math.sin(rad) * 18)], ink)
            circle(50, 50, 12, dark)
            circle(50, 50, 5, WHITE)
        elif skill_id == 'shield_bash':
            poly([(50, 5), (84, 20), (78, 68), (50, 94), (22, 68), (16, 20)], ink, line)
            poly([(50, 17), (69, 28), (65, 61), (50, 77), (35, 61), (31, 28)], dark)
            path([(50, 22), (50, 70)], bright, line + 1)
            path([(27, 48), (73, 48)], bright, line + 1)
            path([(84, 25), (97, 16)], WHITE, line)
            path([(87, 48), (99, 48)], WHITE, line)
        elif skill_id == 'smite':
            poly([(20, 18), (65, 18), (76, 31), (62, 45), (17, 45), (8, 32)], ink)
            poly([(40, 42), (54, 42), (62, 92), (45, 96)], bright)
            poly([(74, 8), (55, 54), (69, 51), (58, 91), (91, 42), (73, 47)], WHITE)
        elif skill_id == 'healing_wave':
            poly([(50, 84), (17, 52), (18, 29), (37, 22), (50, 37), (63, 22), (82, 29), (83, 52)], ink)
            path([(8, 57), (28, 57), (36, 43), (47, 68), (58, 45), (65, 57), (92, 57)], WHITE, line + 1)
            path([(22, 77), (36, 77), (43, 68)], bright, line)
            path([(78, 77), (64, 77), (57, 68)], bright, line)
        elif skill_id == 'judgement':
            poly([(43, 5), (57, 5), (60, 60), (50, 86), (40, 60)], bright)
            poly([(27, 23), (73, 23), (66, 35), (34, 35)], ink)
            path([(20, 91), (50, 78), (80, 91)], ink, line + 1)
            circle(50, 58, 7, WHITE)
        elif skill_id == 'guardian_aura':
            circle(50, 50, 25, bright, line)
            circle(50, 50, 9, WHITE)
            poly([(36, 42), (7, 21), (17, 54), (40, 64)], ink)
            poly([(64, 42), (93, 21), (83, 54), (60, 64)], ink)
            path([(50, 5), (50, 28)], WHITE, line)
            path([(50, 72), (50, 95)], WHITE, line)
        elif skill_id == 'shield':
            poly([(50, 5), (85, 21), (76, 71), (50, 95), (24, 71), (15, 21)], ink, line + 1)
            poly([(50, 20), (69, 30), (64, 63), (50, 77), (36, 63), (31, 30)], dark)
            poly([(50, 28), (58, 45), (75, 50), (58, 55), (50, 73), (42, 55), (25, 50), (42, 45)], bright)
        elif skill_id == 'orbs':
            circle(50, 50, 14, WHITE)
            pygame.draw.ellipse(surf, ink, pygame.Rect(p(7, 29), p(86, 42)), line)
            pygame.draw.ellipse(surf, bright, pygame.Rect(p(29, 7), p(42, 86)), line)
            circle(13, 50, 7, ink)
            circle(73, 22, 7, bright)
            circle(62, 82, 7, ink)
        elif skill_id == 'auto_attack':
            poly([(50, 10), (77, 26), (77, 60), (50, 78), (23, 60), (23, 26)], ink, line)
            circle(50, 44, 16, dark)
            circle(50, 44, 7, WHITE)
            path([(50, 3), (50, 26)], bright, line)
            poly([(42, 78), (50, 96), (58, 78)], bright)
        elif skill_id == 'freeze_mine':
            circle(50, 58, 29, ink, line)
            for angle in range(0, 180, 45):
                rad = math.radians(angle)
                path([(50-math.cos(rad)*19, 58-math.sin(rad)*19), (50+math.cos(rad)*19, 58+math.sin(rad)*19)], bright, line)
            poly([(43, 28), (47, 7), (63, 7), (57, 30)], ink)
            circle(50, 58, 5, WHITE)
        elif skill_id == 'boomerang':
            poly([(8, 73), (37, 17), (49, 11), (42, 49), (61, 68), (89, 55), (79, 82), (57, 91), (36, 64)], ink)
            path([(17, 72), (39, 27), (36, 55), (59, 79), (81, 64)], WHITE, line)
        elif skill_id == 'decoy':
            poly([(50, 8), (72, 31), (67, 72), (50, 94), (33, 72), (28, 31)], ink, line)
            path([(38, 42), (46, 38), (46, 48), (38, 48)], bright, line)
            path([(62, 42), (54, 38), (54, 48), (62, 48)], bright, line)
            path([(16, 20), (16, 80)], ink, line)
            path([(84, 20), (84, 80)], ink, line)
            path([(8, 29), (8, 71)], bright, line)
            path([(92, 29), (92, 71)], bright, line)
        elif skill_id == 'gravity_field':
            circle(50, 50, 42, ink, line)
            pygame.draw.arc(surf, bright, pygame.Rect(p(14, 28), p(72, 44)), .2, 4.8, line + 2)
            pygame.draw.arc(surf, WHITE, pygame.Rect(p(27, 12), p(46, 76)), 1.1, 5.5, line)
            circle(50, 50, 15, dark)
            circle(46, 46, 4, WHITE)
        elif skill_id == 'immortal_heart':
            poly([(50, 91), (13, 51), (17, 23), (39, 17), (50, 33), (61, 17), (83, 23), (87, 51)], ink)
            path([(17, 54), (33, 54), (42, 37), (51, 70), (60, 48), (68, 54), (86, 54)], WHITE, line + 1)
            circle(50, 54, 35, bright, line)
        elif skill_id == 'bounce_shield':
            poly([(50, 6), (84, 23), (77, 71), (50, 94), (23, 71), (16, 23)], ink, line)
            poly([(50, 23), (68, 33), (64, 61), (50, 75), (36, 61), (32, 33)], dark)
            path([(28, 54), (39, 42), (50, 58), (62, 39), (73, 50)], bright, line + 1)
            poly([(74, 50), (63, 47), (70, 60)], WHITE)
        elif any(key in skill_id for key in ('health', 'heal')):
            path([(50, 14), (50, 86)], ink, line + 2)
            path([(14, 50), (86, 50)], ink, line + 2)
            circle(50, 50, 9, WHITE)
        elif any(key in skill_id for key in ('ice', 'frost', 'freeze')):
            for angle in range(0, 180, 45):
                rad = math.radians(angle)
                path([(50-math.cos(rad)*35, 50-math.sin(rad)*35), (50+math.cos(rad)*35, 50+math.sin(rad)*35)], ink, line)
            circle(50, 50, 6, WHITE)
        elif any(key in skill_id for key in ('lightning', 'thunder', 'emp')):
            poly([(57, 4), (21, 51), (46, 47), (35, 96), (82, 38), (56, 42)], ink)
        else:
            poly([(50, 7), (90, 50), (50, 93), (10, 50)], ink, line + 1)
            circle(50, 50, 9, WHITE)
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
        line = max(1, size // 12)
        bright = tuple(min(255, channel + 80) for channel in color[:3])

        def p(x, y):
            return (int(size * x / 100), int(size * y / 100))

        def poly(points, fill=color):
            pygame.draw.polygon(surf, fill, [p(x, y) for x, y in points])

        if char_type == 'cyber_mage':
            pygame.draw.line(surf, color, p(50, 18), p(50, 94), line + 1)
            poly([(50, 2), (67, 20), (50, 37), (33, 20)], bright)
            pygame.draw.circle(surf, WHITE, p(50, 20), max(1, size // 12))
            pygame.draw.arc(surf, color, pygame.Rect(p(16, 5), p(68, 50)), 0, math.pi, line)
            pygame.draw.line(surf, bright, p(35, 80), p(65, 80), line)
        elif char_type == 'mech_ranger':
            poly([(18, 20), (70, 20), (92, 40), (69, 52), (42, 52), (32, 78), (17, 78), (22, 52), (8, 45)], (18, 26, 35))
            pygame.draw.line(surf, color, p(25, 31), p(86, 36), line + 1)
            pygame.draw.rect(surf, bright, pygame.Rect(p(31, 54), p(22, 12)))
            pygame.draw.circle(surf, WHITE, p(71, 35), max(1, size // 14))
        elif char_type == 'bio_berserker':
            pygame.draw.line(surf, color, p(50, 42), p(50, 96), line + 2)
            poly([(48, 5), (90, 22), (72, 54), (50, 45), (28, 54), (10, 22)], color)
            poly([(50, 13), (75, 24), (63, 38), (50, 33), (37, 38), (25, 24)], (30, 12, 18))
            pygame.draw.line(surf, WHITE, p(18, 22), p(82, 22), line)
            pygame.draw.line(surf, bright, p(30, 78), p(70, 78), line + 1)
        elif char_type == 'shadow_assassin':
            poly([(16, 90), (38, 28), (53, 5), (60, 17), (48, 41), (29, 95)], color)
            poly([(84, 90), (62, 28), (47, 5), (40, 17), (52, 41), (71, 95)], bright)
            pygame.draw.line(surf, WHITE, p(28, 73), p(49, 24), line)
            pygame.draw.line(surf, WHITE, p(72, 73), p(51, 24), line)
        else:
            poly([(50, 1), (67, 24), (58, 69), (50, 91), (42, 69), (33, 24)], bright)
            pygame.draw.line(surf, WHITE, p(50, 8), p(50, 77), line)
            poly([(14, 60), (42, 53), (50, 63), (58, 53), (86, 60), (58, 72), (42, 72)], color)
            pygame.draw.circle(surf, color, p(50, 89), max(2, size // 9), line)
        return surf

    @staticmethod
    def draw_character_fx(surface, x, y, char_type, color, angle, pulse):
        """Draw a role-specific animated field behind the player."""
        fx = pygame.Surface((120, 120), pygame.SRCALPHA)
        c = 60
        phase = math.radians(angle)
        wave = math.sin(math.radians(pulse))
        bright = tuple(min(255, channel + 70) for channel in color[:3])

        if char_type == 'cyber_mage':
            for radius, offset in ((34, 0), (45, 30)):
                points = []
                for index in range(6):
                    theta = phase * (1 if radius == 34 else -0.7) + math.radians(index * 60 + offset)
                    points.append((c + math.cos(theta) * radius, c + math.sin(theta) * radius))
                pygame.draw.lines(fx, (*color[:3], 95), True, points, 2)
            for index in range(3):
                theta = -phase * 1.3 + math.radians(index * 120)
                px, py = c + math.cos(theta) * 48, c + math.sin(theta) * 48
                pygame.draw.circle(fx, (*bright, 180), (int(px), int(py)), 3)
        elif char_type == 'mech_ranger':
            sweep = phase % (math.pi * 2)
            end = (c + math.cos(sweep) * 52, c + math.sin(sweep) * 52)
            pygame.draw.polygon(fx, (*color[:3], 22), [(c, c), end,
                                (c + math.cos(sweep + .35) * 52, c + math.sin(sweep + .35) * 52)])
            pygame.draw.line(fx, (*bright, 150), (c, c), end, 2)
            pygame.draw.circle(fx, (*color[:3], 110), (c, c), int(39 + wave * 3), 1)
            for theta in (0, math.pi / 2, math.pi, math.pi * 1.5):
                pygame.draw.line(fx, (*color[:3], 120),
                                 (c + math.cos(theta) * 34, c + math.sin(theta) * 34),
                                 (c + math.cos(theta) * 47, c + math.sin(theta) * 47), 2)
        elif char_type == 'bio_berserker':
            radius = int(39 + wave * 6)
            points = []
            for index in range(8):
                theta = math.radians(index * 45)
                r = radius if index % 2 == 0 else radius - 9
                points.append((c + math.cos(theta) * r, c + math.sin(theta) * r))
            pygame.draw.lines(fx, (*color[:3], 130), True, points, 3)
            for px in (35, 85):
                length = int(9 + abs(wave) * 10)
                pygame.draw.polygon(fx, (*bright, 110), [(px - 5, 83), (px + 5, 83), (px, 83 + length)])
        elif char_type == 'shadow_assassin':
            for offset, alpha in ((0, 150), (10, 80), (20, 40)):
                shift = int(math.sin(phase * 2 + offset) * 5)
                pygame.draw.line(fx, (*color[:3], alpha), (20 + offset, 84 + shift), (78 + offset, 26 + shift), 2)
            diamond = [(c, 17), (103, c), (c, 103), (17, c)]
            pygame.draw.lines(fx, (*bright, 70), True, diamond, 1)
        else:
            pygame.draw.arc(fx, (*bright, 150), pygame.Rect(18, 13, 84, 34), 0, math.pi * 2, 3)
            radius = int(42 + wave * 3)
            for theta in (0, math.pi / 2, math.pi, math.pi * 1.5):
                px, py = c + math.cos(theta) * radius, c + math.sin(theta) * radius
                plate = pygame.Rect(0, 0, 15, 7)
                plate.center = (int(px), int(py))
                pygame.draw.rect(fx, (*color[:3], 130), plate, border_radius=2)
            pygame.draw.circle(fx, (*color[:3], 75), (c, c), radius, 2)

        surface.blit(fx, (int(x) - c, int(y) - c))

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











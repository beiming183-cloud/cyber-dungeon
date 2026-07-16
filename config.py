import pygame

# ==================== 基础配置 ====================
pygame.init()

# 屏幕设置
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
TILE_SIZE = 48
FPS = 60

# 颜色定义 (补全了GRAY，并使用了更赛博朋克的配色)
BLACK = (10, 10, 16)
WHITE = (240, 240, 255)
GRAY = (128, 128, 128)  # 修复报错的关键
DARK_GRAY = (40, 40, 50)
RED = (255, 60, 60)
GREEN = (46, 204, 113)
BLUE = (52, 152, 219)
YELLOW = (241, 196, 15)
ORANGE = (230, 126, 34)
PURPLE = (155, 89, 182)
CYAN = (0, 255, 255)
NEON_BLUE = (0, 200, 255)
UI_BG = (20, 20, 30, 220)

# Unified interface palette. Bright colors are reserved for state and emphasis.
UI_PANEL = (12, 16, 26, 238)
UI_PANEL_ALT = (17, 23, 36, 238)
UI_BORDER = (55, 70, 92)
UI_MUTED = (145, 156, 178)
UI_PRIMARY = NEON_BLUE
UI_ACCENT = (255, 196, 64)
UI_DANGER = (255, 78, 96)


# 字体加载器
def get_font(size):
    font_names = ["microsoftyahei", "simhei", "kaiti", "arial"]
    for name in font_names:
        try:
            return pygame.font.SysFont(name, size)
        except:
            continue
    return pygame.font.Font(None, size)


FONT_S = get_font(20)
FONT_M = get_font(28)
FONT_L = get_font(60)
FONT_ICON = get_font(40)  # 专门用于渲染Emoji图标
FONT_XS = get_font(16)
FONT_CARD = get_font(24)
FONT_TITLE = get_font(52)
FONT_HERO = get_font(72)



import pygame

from config import (
    FONT_XS,
    UI_ACCENT,
    UI_BORDER,
    UI_MUTED,
    UI_PANEL,
    UI_PANEL_ALT,
    UI_PRIMARY,
    WHITE,
)


def draw_grid_background(surface, time_value=0.0):
    surface.fill((6, 8, 15))
    grid = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    offset = int(time_value * 8) % 64
    for x in range(-64 + offset, surface.get_width(), 64):
        pygame.draw.line(grid, (18, 42, 62, 55), (x, 0), (x, surface.get_height()))
    for y in range(-64 + offset, surface.get_height(), 64):
        pygame.draw.line(grid, (18, 42, 62, 38), (0, y), (surface.get_width(), y))
    surface.blit(grid, (0, 0))


def draw_panel(surface, rect, accent=None, selected=False, fill=None, radius=8):
    rect = pygame.Rect(rect)
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel_fill = fill or (UI_PANEL_ALT if selected else UI_PANEL)
    pygame.draw.rect(panel, panel_fill, panel.get_rect(), border_radius=radius)
    border = accent if selected and accent else UI_BORDER
    pygame.draw.rect(panel, border, panel.get_rect(), 2 if selected else 1, border_radius=radius)
    if selected and accent:
        pygame.draw.rect(panel, accent, (0, 0, rect.width, 4), border_radius=radius)
        glow = pygame.Surface((rect.width, 10), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*accent[:3], 38), glow.get_rect())
        panel.blit(glow, (0, 0))
    surface.blit(panel, rect.topleft)
    return rect


def draw_corner_brackets(surface, rect, color=UI_PRIMARY, length=26, width=2):
    rect = pygame.Rect(rect)
    corners = [
        ((rect.left, rect.top + length), (rect.left, rect.top), (rect.left + length, rect.top)),
        ((rect.right - length, rect.top), (rect.right, rect.top), (rect.right, rect.top + length)),
        ((rect.left, rect.bottom - length), (rect.left, rect.bottom), (rect.left + length, rect.bottom)),
        ((rect.right - length, rect.bottom), (rect.right, rect.bottom), (rect.right, rect.bottom - length)),
    ]
    for points in corners:
        pygame.draw.lines(surface, color, False, points, width)


def wrap_text(text, font, max_width):
    lines = []
    for paragraph in str(text).split("\n"):
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and font.size(candidate)[0] > max_width:
                lines.append(current)
                current = char
            else:
                current = candidate
        lines.append(current)
    return lines or [""]


def draw_wrapped_text(surface, text, font, color, rect, line_gap=4, align="center", max_lines=None):
    rect = pygame.Rect(rect)
    lines = wrap_text(text, font, rect.width)
    if max_lines:
        lines = lines[:max_lines]
    line_height = font.get_linesize() + line_gap
    y = rect.top
    for line in lines:
        rendered = font.render(line, True, color)
        if align == "left":
            x = rect.left
        else:
            x = rect.centerx - rendered.get_width() // 2
        surface.blit(rendered, (x, y))
        y += line_height
    return y


def draw_keycap(surface, label, center, active=False):
    text = FONT_XS.render(str(label), True, WHITE if active else UI_MUTED)
    width = max(30, text.get_width() + 14)
    rect = pygame.Rect(0, 0, width, 28)
    rect.center = center
    pygame.draw.rect(surface, (25, 34, 50), rect, border_radius=6)
    pygame.draw.rect(surface, UI_ACCENT if active else UI_BORDER, rect, 1, border_radius=6)
    surface.blit(text, text.get_rect(center=rect.center))
    return rect


def draw_button(surface, rect, label, font, active=True, pulse=0.0):
    rect = pygame.Rect(rect)
    accent = UI_ACCENT if active else UI_BORDER
    draw_panel(surface, rect, accent=accent, selected=active, fill=(18, 25, 36, 242))
    if active and pulse:
        glow = pygame.Surface(rect.size, pygame.SRCALPHA)
        alpha = int(18 + 20 * pulse)
        pygame.draw.rect(glow, (*accent[:3], alpha), glow.get_rect(), border_radius=8)
        surface.blit(glow, rect.topleft)
    text = font.render(label, True, WHITE if active else UI_MUTED)
    surface.blit(text, text.get_rect(center=rect.center))
    return rect

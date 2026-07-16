import pygame
import random
import math
from config import *
from visual_effects import VisualUtils


class Mine:
    """冰冻地雷"""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.rect = pygame.Rect(x - 15, y - 15, 30, 30)
        self.trigger_radius = 80
        self.exploded = False
        self.explosion_timer = 0
        self.freeze_duration = 120  # 2秒 (60fps * 2)
        self.damage = 40
        self.life = 600  # 10秒后自动消失 (60fps * 10)
        
    def update(self, enemies):
        # 地雷自动消失
        self.life -= 1
        if self.life <= 0:
            return False  # 地雷消失
        
        if self.exploded:
            self.explosion_timer += 1
            return self.explosion_timer < 30  # 爆炸动画持续30帧
        
        # 检查是否有敌人靠近
        for enemy in enemies:
            if enemy.alive:
                dist = math.hypot(enemy.rect.centerx - self.x, enemy.rect.centery - self.y)
                if dist < self.trigger_radius:
                    # 触发爆炸
                    self.explode(enemies)
                    return True
        return True
    
    def explode(self, enemies):
        self.exploded = True
        # 对范围内的敌人造成伤害和冰冻
        for enemy in enemies:
            if enemy.alive:
                dist = math.hypot(enemy.rect.centerx - self.x, enemy.rect.centery - self.y)
                if dist < self.trigger_radius:
                    enemy.take_damage(self.damage)
                    if not hasattr(enemy, 'frozen_timer'):
                        enemy.frozen_timer = 0
                    enemy.frozen_timer = self.freeze_duration  # 冰冻2秒
    
    def draw(self, surface, camera):
        cx, cy = camera.apply(self.x, self.y)
        if self.exploded:
            # 爆炸效果
            radius = 30 + self.explosion_timer * 2
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            alpha = 200 - self.explosion_timer * 5
            pygame.draw.circle(s, (*NEON_BLUE[:3], alpha), (radius, radius), radius)
            surface.blit(s, (cx - radius, cy - radius))
        else:
            # 地雷图标
            icon = VisualUtils.create_emoji_surface("💣", NEON_BLUE, 30)
            surface.blit(icon, (cx - 15, cy - 15))
            # 触发范围指示
            s = pygame.Surface((self.trigger_radius * 2, self.trigger_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*NEON_BLUE[:3], 30), (self.trigger_radius, self.trigger_radius), self.trigger_radius, 2)
            surface.blit(s, (cx - self.trigger_radius, cy - self.trigger_radius))


class Decoy:
    """分身幻影"""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.rect = pygame.Rect(x - 24, y - 24, 48, 48)
        self.life = 300  # 5秒 (60fps * 5)
        self.max_life = 300
        self.alpha = 200
        self.pulse = 0
        self.attraction_radius = 400  # 吸引敌人的范围
        
    def update(self):
        self.life -= 1
        self.pulse = (self.pulse + 2) % 360
        self.alpha = int(200 * (self.life / self.max_life))
        return self.life > 0
    
    def explode(self, enemies):
        """分身消失时爆炸"""
        explosion_radius = 100
        for enemy in enemies:
            if enemy.alive:
                dist = math.hypot(enemy.rect.centerx - self.x, enemy.rect.centery - self.y)
                if dist < explosion_radius:
                    enemy.take_damage(60)
    
    def draw(self, surface, camera):
        cx, cy = camera.apply(self.x, self.y)
        # 半透明的玩家图标
        s = pygame.Surface((48, 48), pygame.SRCALPHA)
        # 绘制分身轮廓（紫色半透明）
        color = (*PURPLE[:3], self.alpha)
        pygame.draw.circle(s, color, (24, 24), 20)
        surface.blit(s, (cx - 24, cy - 24))
        
        # 吸引范围指示
        s = pygame.Surface((self.attraction_radius * 2, self.attraction_radius * 2), pygame.SRCALPHA)
        pulse = 50 + math.sin(math.radians(self.pulse)) * 20
        pygame.draw.circle(s, (*PURPLE[:3], int(pulse)), (self.attraction_radius, self.attraction_radius), self.attraction_radius, 2)
        surface.blit(s, (cx - self.attraction_radius, cy - self.attraction_radius))


class GravityField:
    """重力领域"""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.rect = pygame.Rect(x - 100, y - 100, 200, 200)
        self.radius = 150
        self.life = 300  # 5秒
        self.max_life = 300
        self.pull_strength = 2.0
        self.pulse = 0
        
    def update(self):
        self.life -= 1
        self.pulse = (self.pulse + 3) % 360
        return self.life > 0
    
    def apply_gravity(self, enemy):
        """对敌人施加重力"""
        dx = self.x - enemy.rect.centerx
        dy = self.y - enemy.rect.centery
        dist = math.hypot(dx, dy)
        
        if dist > 0 and dist < self.radius:
            # 计算拉力方向
            pull_x = (dx / dist) * self.pull_strength
            pull_y = (dy / dist) * self.pull_strength
            # 应用拉力
            enemy.vx += pull_x * 0.3
            enemy.vy += pull_y * 0.3
            # 限制速度
            max_speed = enemy.speed * 0.5  # 重力场内速度减半
            speed = math.hypot(enemy.vx, enemy.vy)
            if speed > max_speed:
                enemy.vx = (enemy.vx / speed) * max_speed
                enemy.vy = (enemy.vy / speed) * max_speed
    
    def draw(self, surface, camera):
        cx, cy = camera.apply(self.x, self.y)
        # 重力场效果
        pulse_radius = self.radius + math.sin(math.radians(self.pulse)) * 10
        alpha = int(100 * (self.life / self.max_life))
        
        s = pygame.Surface((int(pulse_radius * 2), int(pulse_radius * 2)), pygame.SRCALPHA)
        # 绘制多个同心圆
        blue_color = BLUE if isinstance(BLUE, tuple) else (52, 152, 219)
        for i in range(3):
            r = pulse_radius - i * 20
            a = max(0, alpha - i * 20)
            if r > 0:
                pygame.draw.circle(s, (*blue_color[:3], int(a)), (int(pulse_radius), int(pulse_radius)), int(r), 2)
        surface.blit(s, (cx - pulse_radius, cy - pulse_radius))
        
        # 中心点
        pygame.draw.circle(surface, blue_color, (int(cx), int(cy)), 5)


class PoisonField:
    """生化毒雾"""
    def __init__(self, x, y, radius=160, duration=240, damage=6):
        self.x = x
        self.y = y
        self.radius = radius
        self.life = duration
        self.max_life = duration
        self.damage = damage
        self.tick = 0
        self.slow_factor = 0.6
    
    def update(self, enemies):
        self.life -= 1
        self.tick += 1
        if self.tick % 20 == 0:
            for enemy in enemies:
                if enemy.alive:
                    dist = math.hypot(enemy.rect.centerx - self.x, enemy.rect.centery - self.y)
                    if dist <= self.radius:
                        enemy.take_damage(self.damage)
                        enemy.poison_timer = max(getattr(enemy, 'poison_timer', 0), 90)
                        enemy.poison_damage = max(getattr(enemy, 'poison_damage', 0), self.damage // 2)
                        enemy.slow_timer = max(getattr(enemy, 'slow_timer', 0), 60)
                        enemy.slow_factor = min(getattr(enemy, 'slow_factor', 0.7), self.slow_factor)
        return self.life > 0
    
    def draw(self, surface, camera):
        cx, cy = camera.apply(self.x, self.y)
        alpha = int(120 * (self.life / self.max_life))
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 255, 100, alpha), (self.radius, self.radius), self.radius)
        pygame.draw.circle(s, (50, 200, 50, max(0, alpha - 40)), (self.radius, self.radius), int(self.radius * 0.7))
        surface.blit(s, (cx - self.radius, cy - self.radius))


import pygame
import random
import math
from config import *
from visual_effects import VisualUtils, Particle


# ==================== 游戏实体 ====================
class Entity:
    def __init__(self, x, y, size=32):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = WHITE
        self.vx = 0
        self.vy = 0
        self.speed = 0
        self.hp = 100
        self.max_hp = 100
        self.alive = True
        self.image = None
        self.hurt_timer = 0

    def move(self, tiles):
        """更稳健的物理移动系统"""
        # X轴移动
        self.rect.x += self.vx
        hit_list = self.get_collisions(tiles)
        for tile in hit_list:
            if self.vx > 0:  # 向右撞墙
                self.rect.right = tile.left
            elif self.vx < 0:  # 向左撞墙
                self.rect.left = tile.right

        # Y轴移动
        self.rect.y += self.vy
        hit_list = self.get_collisions(tiles)
        for tile in hit_list:
            if self.vy > 0:  # 向下撞墙
                self.rect.bottom = tile.top
            elif self.vy < 0:  # 向上撞墙
                self.rect.top = tile.bottom

    def get_collisions(self, tiles):
        hits = []
        # 优化：只检查周围的墙壁，而不是遍历全图
        grid_x = int(self.rect.centerx // TILE_SIZE)
        grid_y = int(self.rect.centery // TILE_SIZE)

        for y in range(grid_y - 2, grid_y + 3):
            for x in range(grid_x - 2, grid_x + 3):
                if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
                    if tiles[y][x] == 1:  # 1是墙
                        wall_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        if self.rect.colliderect(wall_rect):
                            hits.append(wall_rect)
        return hits

    def take_damage(self, amount):
        # 玩家无敌状态判断
        if hasattr(self, 'is_invincible') and self.is_invincible:
            return  # 无敌状态下不受伤害
        
        # 生化狂战士的近战伤害减免（只对玩家生效）
        if hasattr(self, 'char_type') and self.char_type == "bio_berserker":
            amount = int(amount * 0.85)  # 减免15%

        # 天赋和装备提供的通用伤害减免（只对玩家生效）
        if hasattr(self, 'damage_reduction'):
            amount = int(amount * (1 - max(0.0, min(0.75, self.damage_reduction))))

        # 如果有防护盾，减少伤害（只对玩家生效）
        if hasattr(self, 'passive_skills') and 'shield' in self.passive_skills and \
                self.passive_skills['shield']['level'] > 0:
            shield_level = self.passive_skills['shield']['level']
            reduction = self.available_passives['shield']['reduction'][shield_level]
            amount = int(amount * (1 - reduction))

        self.hp -= amount
        self.hurt_timer = 10
        if self.hp <= 0: 
            self.alive = False
            # 玩家生命系统
            if hasattr(self, 'lives') and self.lives > 1:
                self.lives -= 1
                self.hp = self.max_hp
                self.alive = True
                self.is_invincible = True
                self.invincible_timer = 180  # 死亡复活后3秒无敌

    def apply_vampirism(self, damage_dealt):
        """应用吸血效果"""
        if self.char_type == "bio_berserker":
            heal_amount = int(damage_dealt * 0.05)  # 5%吸血
            if heal_amount > 0:
                self.hp = min(self.max_hp, self.hp + heal_amount)
                return heal_amount
        return 0


class Player(Entity):
    def __init__(self, x, y, char_type="cyber_mage", talent=None):
        super().__init__(x, y, size=32)
        self.char_type = char_type
        self.talent = talent
        # 初始化移动状态属性（支持中文键盘输入）
        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False
        self.sprint = False

        # 根据角色类型设置属性
        self._setup_character()

        # RPG属性
        self.level = 1
        self.exp = 0
        self.exp_max = 100
        self.coins = 0

        # 初始被动技能（天赋相关）- 在 _setup_character() 中已初始化，这里不需要重复
        # self.passive_skills = {}  # 已在 _setup_character() 中初始化
        
        # 无敌系统
        self.invincible_timer = 300  # 开局5秒无敌（60fps * 5 = 300帧）
        self.lives = 1  # 初始生命数
        self.is_invincible = True  # 开局无敌标志

        # 角色专属被动
        self.character_passive = self._get_character_passive()

        # 应用天赋效果（必须在 _setup_character() 之后调用，因为需要 available_passives）
        if self.talent:
            self._apply_talent()

    def _setup_character(self):
        """根据角色类型设置基础属性和技能"""
        if self.char_type == "cyber_mage":  # 赛博法师（原角色）
            self.color = CYAN
            self.speed = 5
            self.max_hp = 100
            self.hp = 100
            self.image = VisualUtils.create_character_icon(self.char_type, CYAN, 48)
            self.weapon_img = VisualUtils.create_weapon_icon(self.char_type, YELLOW, 32)
            # 技能CD和伤害调整
            self.skills = [
                {"key": "1", "name": "爆裂火球", "cd": 30, "cur": 0, "color": ORANGE, "icon": "🔥", "type": "pyro_orb",
                 "behavior": "projectile", "damage": 60, "speed": 12, "life": 80,
                 "effects": {"burn": {"damage": 5, "duration": 180}, "area": {"radius": 80, "damage": 25}}},
                {"key": "2", "name": "极寒冰矛", "cd": 55, "cur": 0, "color": NEON_BLUE, "icon": "❄️", "type": "frost_spear",
                 "behavior": "projectile", "damage": 45, "speed": 16, "life": 90,
                 "effects": {"freeze": {"duration": 90}}},
                {"key": "3", "name": "雷霆万钧", "cd": 85, "cur": 0, "color": PURPLE, "icon": "⚡", "type": "chain_lightning", "visual_id": "thunder_chain_storm",
                 "behavior": "projectile", "damage": 50, "speed": 20, "life": 100},
                {"key": "4", "name": "暗影新星", "cd": 110, "cur": 0, "color": (100, 50, 150), "icon": "💀",
                 "type": "shadow_nova", "behavior": "area", "radius": 180, "damage": 55, "center": "player",
                 "effects": {"slow": {"factor": 0.5, "duration": 90}}},
                {"key": "5", "name": "圣光裁决", "cd": 140, "cur": 0, "color": YELLOW, "icon": "✨", "type": "holy_beam",
                 "behavior": "beam", "damage": 80, "width": 50,
                 "effects": {"heal_player": {"amount": 15}}}
            ]
        elif self.char_type == "mech_ranger":  # 机械游侠
            self.color = GREEN
            self.speed = 7
            self.max_hp = 80
            self.hp = 80
            self.image = VisualUtils.create_character_icon(self.char_type, GREEN, 48)
            self.weapon_img = VisualUtils.create_weapon_icon(self.char_type, GREEN, 32)
            # 技能CD和伤害调整
            self.skills = [
                {"key": "1", "name": "速射突袭", "cd": 24, "cur": 0, "color": GREEN, "icon": "🔫", "type": "rapid_fire",
                 "behavior": "projectile", "damage": 35, "speed": 20, "life": 70, "multi_count": 3},
                {"key": "2", "name": "散射箭雨", "cd": 55, "cur": 0, "color": GREEN, "icon": "🏹", "type": "scatter_arrow",
                 "behavior": "projectile", "damage": 28, "speed": 18, "life": 70, "multi_count": 5, "spread": 25},
                {"key": "3", "name": "追踪导弹", "cd": 95, "cur": 0, "color": RED, "icon": "🚀", "type": "tracking_missile",
                 "behavior": "projectile", "damage": 70, "speed": 12, "life": 160, "homing": True,
                 "effects": {"area": {"radius": 70, "damage": 30}}},
                {"key": "4", "name": "EMP冲击", "cd": 130, "cur": 0, "color": YELLOW, "icon": "🌩️", "type": "emp_blast",
                 "behavior": "area", "radius": 220, "damage": 25, "effects": {"stun": {"duration": 60}}},
                {"key": "5", "name": "终结狙击", "cd": 160, "cur": 0, "color": BLUE, "icon": "🎯", "type": "sniper_round",
                 "behavior": "beam", "damage": 140, "width": 25, "pierce": True}
            ]
        elif self.char_type == "bio_berserker":  # 生化狂战士
            self.color = RED
            self.speed = 4
            self.max_hp = 150
            self.hp = 150
            self.image = VisualUtils.create_character_icon(self.char_type, RED, 48)
            self.weapon_img = VisualUtils.create_weapon_icon(self.char_type, RED, 32)
            # 技能CD和伤害调整
            self.skills = [
                {"key": "1", "name": "旋风斩", "cd": 32, "cur": 0, "color": RED, "icon": "🌀", "type": "cyclone_slash",
                 "behavior": "area", "radius": 150, "damage": 70, "center": "player"},
                {"key": "2", "name": "地面猛击", "cd": 70, "cur": 0, "color": ORANGE, "icon": "💥", "type": "earth_shock",
                 "behavior": "line", "range": 320, "width": 70, "damage": 85,
                 "effects": {"stun": {"duration": 45}}},
                {"key": "3", "name": "鲜血渴望", "cd": 110, "cur": 0, "color": RED, "icon": "❤️", "type": "blood_rage",
                 "behavior": "buff", "duration": 600, "damage_bonus": 0.35, "lifesteal_bonus": 0.1},
                {"key": "4", "name": "狂怒冲锋", "cd": 120, "cur": 0, "color": ORANGE, "icon": "🏃", "type": "berserk_charge",
                 "behavior": "dash", "distance": 240, "damage": 80, "width": 70},
                {"key": "5", "name": "生化爆发", "cd": 150, "cur": 0, "color": PURPLE, "icon": "🧬", "type": "bio_explosion",
                 "behavior": "spawn_field", "radius": 170, "damage": 25, "duration": 360}
            ]
        elif self.char_type == "shadow_assassin":  # 暗影刺客
            self.color = (100, 50, 150)
            self.speed = 8
            self.max_hp = 90
            self.hp = 90
            self.image = VisualUtils.create_character_icon(self.char_type, (100, 50, 150), 48)
            self.weapon_img = VisualUtils.create_weapon_icon(self.char_type, (150, 100, 200), 32)
            # 技能CD和伤害调整
            self.skills = [
                {"key": "1", "name": "暗影突袭", "cd": 28, "cur": 0, "color": (100, 50, 150), "icon": "💨", "type": "shadow_dash",
                 "behavior": "dash", "distance": 260, "damage": 75, "width": 60},
                {"key": "2", "name": "致命一击", "cd": 60, "cur": 0, "color": PURPLE, "icon": "⚔️", "type": "assassinate",
                 "behavior": "target_strike", "damage": 150},
                {"key": "3", "name": "影分身", "cd": 85, "cur": 0, "color": (100, 50, 150), "icon": "👥", "type": "mirror_clone",
                 "behavior": "spawn_clone", "count": 2},
                {"key": "4", "name": "毒刃暗袭", "cd": 95, "cur": 0, "color": GREEN, "icon": "☠️", "type": "poison_edge",
                 "behavior": "projectile", "damage": 55, "speed": 18, "life": 90,
                 "effects": {"poison": {"damage": 6, "duration": 240}}},
                {"key": "5", "name": "暗影风暴", "cd": 135, "cur": 0, "color": PURPLE, "icon": "💥", "type": "shadow_storm",
                 "behavior": "radial_projectiles", "projectile_count": 12, "damage": 45, "speed": 14, "life": 70}
            ]
        elif self.char_type == "holy_knight":  # 圣光骑士
            self.color = YELLOW
            self.speed = 4.5
            self.max_hp = 180
            self.hp = 180
            self.image = VisualUtils.create_character_icon(self.char_type, YELLOW, 48)
            self.weapon_img = VisualUtils.create_weapon_icon(self.char_type, YELLOW, 32)
            # 技能CD和伤害调整
            self.skills = [
                {"key": "1", "name": "圣盾猛击", "cd": 38, "cur": 0, "color": YELLOW, "icon": "🛡️", "type": "shield_bash",
                 "behavior": "dash", "distance": 180, "damage": 60, "width": 80,
                 "effects": {"stun": {"duration": 45}}},
                {"key": "2", "name": "神圣打击", "cd": 60, "cur": 0, "color": YELLOW, "icon": "✨", "type": "smite",
                 "behavior": "area", "radius": 160, "damage": 85},
                {"key": "3", "name": "治愈之光", "cd": 85, "cur": 0, "color": GREEN, "icon": "💚", "type": "healing_wave",
                 "behavior": "heal", "heal_amount": 80, "regen": 10},
                {"key": "4", "name": "裁决之光", "cd": 115, "cur": 0, "color": YELLOW, "icon": "⚡", "type": "judgement",
                 "behavior": "beam", "damage": 120, "width": 60,
                 "effects": {"burn": {"damage": 4, "duration": 120}}},
                {"key": "5", "name": "神圣守护", "cd": 150, "cur": 0, "color": YELLOW, "icon": "🌟", "type": "guardian_aura",
                 "behavior": "buff_invincibility", "duration": 240}
            ]

        # 初始化其他属性
        self.magic_angle = 0
        self.aura_pulse = 0
        self.energy_waves = []

        # 被动技能系统
        self.passive_skills = {}
        # 可用被动技能列表
        self.available_passives = {
            "shield": {"name": "防护盾", "icon": "🛡️", "color": (200, 150, 255), "level": 0, "max_level": 5,
                       "desc": "减少受到的伤害", "reduction": [0.0, 0.35, 0.55, 0.7, 0.8, 0.9]},
            "orbs": {"name": "环绕光球", "icon": "⚪", "color": YELLOW, "level": 0, "max_level": 5,
                     "desc": "围绕自身旋转的光球攻击敌人", "count": [0, 1, 2, 3, 4, 6]},  # 光球数量随等级增加
            "auto_attack": {"name": "自动攻击", "icon": "🎯", "color": RED, "level": 0, "max_level": 5,
                            "desc": "自动向敌人发射攻击", "count": [0, 1, 2, 3, 4, 5], "cd": [0, 120, 100, 80, 60, 45]},
            "chain_lightning": {"name": "连锁闪电", "icon": "⚡", "color": PURPLE, "level": 0, "max_level": 5,
                               "desc": "发射闪电球，在敌人之间弹跳", "damage": [0, 30, 40, 50, 60, 70], "cd": [0, 120, 110, 100, 90, 80]},
            "freeze_mine": {"name": "冰冻地雷", "icon": "💣", "color": NEON_BLUE, "level": 0, "max_level": 5,
                           "desc": "放置地雷，爆炸时冻结敌人2秒", "damage": [0, 25, 35, 45, 55, 65], "cd": [0, 90, 80, 70, 60, 50]},
            "boomerang": {"name": "吸血飞刃", "icon": "🗡️", "color": RED, "level": 0, "max_level": 5,
                         "desc": "投掷回旋飞刃，造成伤害并回血", "damage": [0, 28, 35, 42, 50, 58], "cd": [0, 100, 90, 80, 70, 60], "lifesteal": [0, 0.1, 0.12, 0.15, 0.18, 0.2]},
            "decoy": {"name": "分身幻影", "icon": "👥", "color": (150, 100, 200), "level": 0, "max_level": 5,
                     "desc": "创造分身吸引敌人，5秒后爆炸", "damage": [0, 20, 30, 40, 50, 60], "cd": [0, 150, 140, 130, 120, 110]},
            "gravity_field": {"name": "重力领域", "icon": "🌀", "color": (100, 100, 255), "level": 0, "max_level": 5,
                             "desc": "在鼠标位置创造重力场，拉动敌人", "damage": [0, 10, 15, 20, 25, 30], "cd": [0, 180, 170, 160, 150, 140]},
            "immortal_heart": {"name": "无敌之心", "icon": "❤️", "color": (255, 100, 150), "level": 0, "max_level": 2,
                              "desc": "每级增加一条命", "extra_lives": [0, 1, 2]},
            "bounce_shield": {"name": "弹性防护罩", "icon": "🛡️", "color": (100, 200, 255), "level": 0, "max_level": 5,
                             "desc": "间断性出现的防护罩，可以将怪弹开", "duration": [0, 60, 90, 120, 150, 180], "cd": [0, 180, 150, 120, 90, 30]}
        }

        # 生命回复系统
        self.regen_timer = 0
        self.regen_interval = 180
        self.regen_amount = 2

        # 环绕光球列表
        self.orbs = []
        self.orb_angle = 0

        # 自动攻击计时器
        self.auto_attack_timer = 0
        
        # 移动拖尾效果
        self.trail = []  # 存储移动轨迹点
        self.trail_max_length = 15  # 拖尾最大长度（缩短到15，保持淡淡的效果）
        
        # 被动技能CD计时器（用于后5个技能）
        self.passive_skill_cooldowns = {
            'chain_lightning': 0,
            'freeze_mine': 0,
            'boomerang': 0,
            'decoy': 0,
            'gravity_field': 0,
            'bounce_shield': 0
        }
        
        # 弹性防护罩状态
        self.bounce_shield_active = False
        self.bounce_shield_timer = 0
        # 主动技能增益状态
        self.blood_rage_timer = 0
        self.guardian_aura_timer = 0
        self.damage_buff = 0.0
        self.blood_rage_bonus = 0.0

    def _get_character_passive(self):
        """获取角色专属被动技能"""
        if self.char_type == "cyber_mage":
            return {"name": "元素亲和", "desc": "技能伤害+10%，技能CD减少5%"}
        elif self.char_type == "mech_ranger":
            return {"name": "速射", "desc": "普攻CD减少30%，普攻可发射2颗弹丸"}
        elif self.char_type == "bio_berserker":
            return {"name": "吸血", "desc": "攻击恢复5%伤害值的血量"}
        elif self.char_type == "shadow_assassin":
            return {"name": "暗影之力", "desc": "暴击率+15%，移动速度+10%"}
        elif self.char_type == "holy_knight":
            return {"name": "圣光庇护", "desc": "防御力+20%，生命回复+1/秒"}
        return None

    def _apply_talent(self):
        """应用具有明确构筑方向的初始天赋。"""
        # 确保 available_passives 已初始化
        if not hasattr(self, 'available_passives') or not self.available_passives:
            return
        
        if self.talent == 'combat':
            skill_id = 'auto_attack'
            self.passive_skills[skill_id] = {'level': 1, 'name': self.available_passives[skill_id]['name']}
            self.damage_buff = 0.08
            print("[天赋] 火力协议：自动攻击 Lv.1，伤害+8%")
        elif self.talent == 'survival':
            skill_id = 'shield'
            self.passive_skills[skill_id] = {'level': 1, 'name': self.available_passives[skill_id]['name']}
            self.damage_reduction = 0.12
            self.max_hp = int(self.max_hp * 1.15)
            self.hp = self.max_hp
            print("[天赋] 稳态装甲：防护盾 Lv.1，生命+15%，减伤12%")
        elif self.talent == 'exploration':
            skill_id = 'orbs'
            self.passive_skills[skill_id] = {'level': 1, 'name': self.available_passives[skill_id]['name']}
            self.coin_bonus = 0.25
            self.exp_bonus = 0.10
            self.extra_chests = 1
            print("[天赋] 寻宝协议：环绕光球 Lv.1，额外宝箱+1，金币+25%")
    
    def apply_immortal_heart(self):
        """应用无敌之心技能效果"""
        if 'immortal_heart' in self.passive_skills:
            level = self.passive_skills['immortal_heart']['level']
            if level > 0 and 'immortal_heart' in self.available_passives:
                extra_lives = self.available_passives['immortal_heart']['extra_lives'][level]
                self.lives = 1 + extra_lives  # 基础1条命 + 技能增加的命

    def update(self, tiles, particles):
        # 更新无敌计时器
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.is_invincible = False
        if self.guardian_aura_timer > 0:
            self.guardian_aura_timer -= 1
            if self.guardian_aura_timer <= 0 and self.invincible_timer <= 0:
                self.is_invincible = False
        if self.blood_rage_timer > 0:
            self.blood_rage_timer -= 1
            if self.blood_rage_timer <= 0:
                self.damage_buff = 0.0
                self.blood_rage_bonus = 0.0
        
        # 应用无敌之心效果
        self.apply_immortal_heart()
        
        # 输入处理 - 使用事件系统记录的移动状态
        self.vx = 0
        self.vy = 0

        # 根据状态设置移动速度
        if self.move_up: self.vy = -self.speed
        if self.move_down: self.vy = self.speed
        if self.move_left: self.vx = -self.speed
        if self.move_right: self.vx = self.speed

        # 冲刺
        if self.sprint:
            self.vx *= 1.5
            self.vy *= 1.5
            # 冲刺残影粒子 - 根据角色类型变化
            if self.char_type == "cyber_mage":
                if random.random() < 0.7:
                    particles.append(Particle(self.rect.centerx, self.rect.centery, CYAN, 'energy'))
                    particles.append(Particle(self.rect.centerx, self.rect.centery, NEON_BLUE, 'spark'))
            elif self.char_type == "mech_ranger":
                if random.random() < 0.7:
                    particles.append(Particle(self.rect.centerx, self.rect.centery, GREEN, 'spark'))
                    particles.append(Particle(self.rect.centerx, self.rect.centery, (0, 150, 0), 'normal'))
            elif self.char_type == "bio_berserker":
                if random.random() < 0.7:
                    particles.append(Particle(self.rect.centerx, self.rect.centery, RED, 'spark'))
                    particles.append(Particle(self.rect.centerx, self.rect.centery, (150, 0, 0), 'smoke'))

        # 执行移动
        old_x, old_y = self.rect.centerx, self.rect.centery
        self.move(tiles)
        
        # 记录移动轨迹（只有在移动时才记录）
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > 0:
            # 根据速度调整拖尾长度（速度越快拖尾越长，但保持较短）
            dynamic_trail_length = min(15, int(speed * 2) + 8)  # 最大15个点，更短
            
            self.trail.append((self.rect.centerx, self.rect.centery))
            if len(self.trail) > dynamic_trail_length:
                self.trail.pop(0)
        else:
            # 不移动时，拖尾逐渐消失
            if len(self.trail) > 0:
                self.trail.pop(0)

        # 更新技能冷却
        for s in self.skills:
            if s['cur'] > 0: s['cur'] -= 1

        self.magic_angle = (self.magic_angle + 2) % 360
        self.aura_pulse = (self.aura_pulse + 3) % 360
        if self.hurt_timer > 0: self.hurt_timer -= 1

        # 更新能量波动
        self.energy_waves = [(r + 2, life - 1) for r, life in self.energy_waves if life > 0]

        # 生命回复
        self.regen_timer += 1
        if self.regen_timer >= self.regen_interval:
            self.regen_timer = 0
            if self.hp < self.max_hp:
                self.hp = min(self.max_hp, self.hp + self.regen_amount)

        # 更新环绕光球 - 光球持续存在，不会消失
        if 'orbs' in self.passive_skills and self.passive_skills['orbs']['level'] > 0:
            orb_level = self.passive_skills['orbs']['level']
            orb_count = self.available_passives['orbs']['count'][orb_level]
            
            # 根据等级计算半径和转速 - 升级后范围变大，转速变快
            base_radius = 40
            radius_per_level = 12  # 每级增加12像素半径
            base_speed = 2
            speed_per_level = 0.8  # 每级增加0.8转速
            current_radius = base_radius + orb_level * radius_per_level
            current_speed = base_speed + orb_level * speed_per_level
            
            if len(self.orbs) < orb_count:
                # 创建新的光球
                for i in range(len(self.orbs), orb_count):
                    angle_step = 360 / orb_count
                    self.orbs.append({
                        'angle': i * angle_step,
                        'radius': current_radius,
                        'speed': current_speed
                    })
            elif len(self.orbs) > orb_count:
                self.orbs = self.orbs[:orb_count]
            
            # 更新所有光球的半径和速度（升级时动态调整）
            for orb in self.orbs:
                orb['radius'] = current_radius
                orb['speed'] = current_speed

            # 更新光球角度和冷却时间 - 转速随等级增加
            self.orb_angle = (self.orb_angle + 2 + orb_level * 0.5) % 360
            for orb in self.orbs:
                orb['angle'] = (orb['angle'] + orb['speed']) % 360
                # 更新冷却时间
                if 'hit_cooldown' in orb and orb['hit_cooldown'] > 0:
                    orb['hit_cooldown'] -= 1

        # 更新自动攻击计时器
        if 'auto_attack' in self.passive_skills and self.passive_skills['auto_attack']['level'] > 0:
            self.auto_attack_timer += 1
        

    def draw(self, surface, camera):
        cx, cy = camera.apply_rect(self.rect).center

        # 1. 每个职业使用独立的动态场域，不再共用同一套魔法阵。
        VisualUtils.draw_character_fx(
            surface, cx, cy, self.char_type, self.color, self.magic_angle, self.aura_pulse
        )

        # 绘制能量波动圈
        for r, life in self.energy_waves:
            alpha = int(255 * (life / 30))
            s = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color[:3], alpha), (int(r) + 10, int(r) + 10), int(r), 2)
            surface.blit(s, (cx - r - 10, cy - r - 10))

        # 3. 绘制淡淡的移动拖尾痕迹
        if len(self.trail) > 1:
            for i, (tx, ty) in enumerate(self.trail[:-1]):
                trail_cam = camera.apply(tx, ty)
                progress = i / len(self.trail)
                # 淡淡的透明度，越旧越淡
                alpha = int(60 * (1 - progress))  # 最大60透明度，非常淡
                size = max(2, int(8 * (1 - progress)))  # 最大8像素，很小
                
                # 根据角色类型使用不同颜色，但都很淡
                if self.char_type == "cyber_mage":
                    trail_color = CYAN
                elif self.char_type == "mech_ranger":
                    trail_color = ORANGE
                elif self.char_type == "bio_berserker":
                    trail_color = RED
                elif self.char_type == "shadow_assassin":
                    trail_color = PURPLE
                elif self.char_type == "holy_knight":
                    trail_color = YELLOW
                else:
                    trail_color = self.color
                
                # 只绘制淡淡的小点，不要连线
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*trail_color[:3], alpha), (size, size), size)
                surface.blit(s, (trail_cam[0] - size, trail_cam[1] - size))

        # 3. 绘制人物 - 带发光效果
        img_rect = self.image.get_rect(center=(cx, cy))

        # 人物发光轮廓
        glow_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color[:3], 50), (30, 30), 25)
        surface.blit(glow_surf, (cx - 30, cy - 30))

        if self.hurt_timer > 0:
            # 受伤变白效果
            mask = pygame.mask.from_surface(self.image)
            white_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
            surface.blit(white_surf, img_rect)
        else:
            surface.blit(self.image, img_rect)

        # 4. 绘制跟随鼠标的武器 - 增强版
        mx, my = pygame.mouse.get_pos()
        dx, dy = mx - cx, my - cy
        angle = math.degrees(math.atan2(-dy, dx)) - 90

        # 武器在人物身边旋转，带发光
        orbit_dist = 30
        rads = math.radians(-angle - 90)
        wx = cx + math.cos(rads) * orbit_dist
        wy = cy + math.sin(rads) * orbit_dist

        # 武器发光
        weapon_glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(weapon_glow, (*YELLOW[:3], 100), (20, 20), 15)
        surface.blit(weapon_glow, (wx - 20, wy - 20))

        rot_weapon = pygame.transform.rotate(self.weapon_img, angle)
        w_rect = rot_weapon.get_rect(center=(wx, wy))
        surface.blit(rot_weapon, w_rect)

        # 5. 绘制防护盾 - 淡紫色，更明显
        if 'shield' in self.passive_skills and self.passive_skills['shield']['level'] > 0:
            shield_level = self.passive_skills['shield']['level']
            shield_color = self.available_passives['shield']['color']  # 淡紫色 (200, 150, 255)
            # 增加护盾半径和透明度 - 提高透明度使其更明显
            shield_radius = 35 + shield_level * 5
            alpha = 150 + shield_level * 20  # 提高基础透明度，使其更明显
            s = pygame.Surface((shield_radius * 2 + 20, shield_radius * 2 + 20), pygame.SRCALPHA)
            # 绘制护盾圈，使用淡紫色
            pygame.draw.circle(s, (*shield_color[:3], alpha), (int(shield_radius) + 10, int(shield_radius) + 10),
                               int(shield_radius), 4)  # 增加线条宽度
            # 添加外层发光效果
            glow_alpha = int(alpha * 0.4)
            pygame.draw.circle(s, (*shield_color[:3], glow_alpha), (int(shield_radius) + 10, int(shield_radius) + 10),
                               int(shield_radius) + 5, 2)
            surface.blit(s, (cx - shield_radius - 10, cy - shield_radius - 10))

        # 6. 绘制环绕光球 - 光球持续存在，不会消失
        if 'orbs' in self.passive_skills and self.passive_skills['orbs']['level'] > 0:
            orb_color = self.available_passives['orbs']['color']
            for orb in self.orbs:
                orb_x = cx + math.cos(math.radians(orb['angle'] + self.orb_angle)) * orb['radius']
                orb_y = cy + math.sin(math.radians(orb['angle'] + self.orb_angle)) * orb['radius']
                # 光球发光效果 - 根据半径大小调整
                glow_size = max(20, int(6 + orb['radius'] * 0.1))
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*orb_color[:3], 150), (glow_size, glow_size), glow_size - 2)
                surface.blit(glow_surf, (orb_x - glow_size, orb_y - glow_size))
                # 光球本体 - 大小稍微增大
                pygame.draw.circle(surface, orb_color, (int(orb_x), int(orb_y)), 7)
                pygame.draw.circle(surface, WHITE, (int(orb_x), int(orb_y)), 4)

        # 7. 绘制弹性防护罩
        if self.bounce_shield_active:
            shield_level = self.passive_skills.get('bounce_shield', {}).get('level', 0)
            if shield_level > 0:
                shield_color = self.available_passives['bounce_shield']['color']
                shield_radius = 40 + shield_level * 5
                # 脉冲效果
                pulse = math.sin(pygame.time.get_ticks() * 0.01) * 5
                current_radius = shield_radius + pulse
                alpha = 180
                s = pygame.Surface((int(current_radius * 2 + 20), int(current_radius * 2 + 20)), pygame.SRCALPHA)
                # 绘制多层防护罩
                for i in range(3):
                    r = current_radius - i * 5
                    a = max(0, alpha - i * 40)
                    pygame.draw.circle(s, (*shield_color[:3], int(a)), (int(current_radius) + 10, int(current_radius) + 10), int(r), 3)
                surface.blit(s, (cx - current_radius - 10, cy - current_radius - 10))
                
                # 能量波纹
                for i in range(2):
                    wave_radius = current_radius + i * 10
                    wave_alpha = int(100 * (1 - abs(pygame.time.get_ticks() * 0.005 % 1 - 0.5) * 2))
                    wave_surf = pygame.Surface((int(wave_radius * 2), int(wave_radius * 2)), pygame.SRCALPHA)
                    pygame.draw.circle(wave_surf, (*shield_color[:3], wave_alpha), (int(wave_radius), int(wave_radius)), int(wave_radius), 2)
                    surface.blit(wave_surf, (cx - wave_radius, cy - wave_radius))


class Enemy(Entity):
    def __init__(self, x, y, kind, is_elite=False):
        super().__init__(x, y, size=40)
        cfgs = {
            'goblin': ('👹', RED, 1.5, 80, 10, 'normal'),  # 降低速度，增加血量
            'slime': ('🦠', GREEN, 1.0, 100, 8, 'slow'),  # 降低速度，增加血量
            'bat': ('🦇', PURPLE, 2.0, 60, 12, 'fast'),  # 降低速度，增加血量
            'skeleton': ('💀', (150, 150, 150), 1.2, 90, 15, 'normal'),  # 降低速度，增加血量
            'demon': ('😈', (200, 0, 100), 1.8, 120, 20, 'aggressive'),  # 降低速度，增加血量
            'ghost': ('👻', (150, 150, 255), 2.2, 70, 10, 'fast'),  # 降低速度，增加血量
            'dragon': ('🐉', (255, 100, 0), 1.5, 100, 30, 'boss'),  # 降低速度
            'spider': ('🕷️', (100, 50, 150), 2.0, 85, 12, 'normal')  # 降低速度，增加血量
        }
        icon, color, speed, hp, damage, behavior = cfgs.get(kind, cfgs['goblin'])
        self.kind = kind
        self.is_elite = is_elite  # 精英怪标记
        self.is_wave_enemy = False

        # 精英怪增强
        if is_elite:
            hp = int(hp * 2.5)
            damage = int(damage * 1.5)
            speed = speed * 1.2
            color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))
            size = 50
            self.is_golden_boss = True  # 标记为金色Boss
        else:
            self.is_golden_boss = False

        self.color = color
        self.speed = speed
        self.hp = self.max_hp = hp
        if kind == 'dragon':
            center = self.rect.center
            self.rect.size = (96, 96)
            self.rect.center = center
        icon_size = 96 if kind == 'dragon' else 50 if is_elite else 40
        self.image = VisualUtils.create_enemy_icon(kind, color, icon_size, is_elite)
        self.damage = damage
        self.behavior = behavior
        self.anim_frame = 0  # 动画帧
        self.pulse = 0  # 脉冲效果
        self.trail = []  # 移动轨迹
        self.frozen_timer = 0  # 冰冻计时器
        self.particle_timer = 0  # 粒子效果计时器
        self.idle_float = 0  # 悬浮动画
        # 状态效果
        self.burn_timer = 0
        self.burn_damage = 0
        self.burn_tick = 0
        self.poison_timer = 0
        self.poison_damage = 0
        self.poison_tick = 0
        self.stun_timer = 0
        self.slow_timer = 0
        self.slow_factor = 0.6
        self.boss_phase = 1
        self.boss_attack_timer = 0
        self.boss_dash_timer = 0

    def ai_move(self, target, tiles):
        # 增强的AI行为
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if self.stun_timer > 0:
            self.stun_timer -= 1
            self.vx = 0
            self.vy = 0
        elif 0 < dist < 600:
            if self.behavior == 'aggressive':
                # 激进型 - 稍微更快
                speed_mult = 1.1
            elif self.behavior == 'fast':
                # 快速型 - 稍微更快
                speed_mult = 1.05
            elif self.behavior == 'slow':
                # 缓慢型 - 更低速度
                speed_mult = 0.6
            elif self.behavior == 'boss':
                health_ratio = self.hp / max(1, self.max_hp)
                self.boss_phase = 1 if health_ratio > 0.66 else 2 if health_ratio > 0.33 else 3
                self.boss_attack_timer += 1
                if self.boss_attack_timer >= max(120, 250 - self.boss_phase * 35):
                    self.boss_attack_timer = 0
                    self.boss_dash_timer = 26

                if self.boss_phase == 1 and dist > 100:
                    speed_mult = 0.82
                    predict_x = target.rect.centerx + target.vx * 10
                    predict_y = target.rect.centery + target.vy * 10
                    dx = predict_x - self.rect.centerx
                    dy = predict_y - self.rect.centery
                    dist = math.hypot(dx, dy)
                elif self.boss_phase == 2:
                    speed_mult = 1.0
                    dx, dy = dx - dy * 0.55, dy + dx * 0.55
                    dist = math.hypot(dx, dy)
                else:
                    speed_mult = 1.28

                if self.boss_dash_timer > 0:
                    self.boss_dash_timer -= 1
                    speed_mult *= 1.85
            else:
                speed_mult = 0.8  # 普通敌人也降低速度

            slow_mult = 1.0
            if self.slow_timer > 0:
                self.slow_timer -= 1
                slow_mult *= self.slow_factor
            else:
                self.slow_factor = 0.6

            self.vx = (dx / dist) * self.speed * speed_mult * slow_mult
            self.vy = (dy / dist) * self.speed * speed_mult * slow_mult
        else:
            self.vx = self.vy = 0

        # 记录轨迹
        if self.vx != 0 or self.vy != 0:
            self.trail.append((self.rect.centerx, self.rect.centery))
            if len(self.trail) > 5:
                self.trail.pop(0)

        # 如果被冰冻，移动速度降低
        if self.frozen_timer > 0:
            self.vx *= 0.1
            self.vy *= 0.1
            self.frozen_timer -= 1
        
        # 持续性状态效果
        if self.burn_timer > 0:
            self.burn_timer -= 1
            self.burn_tick += 1
            if self.burn_tick >= 30:
                self.take_damage(max(1, self.burn_damage))
                self.burn_tick = 0
        if self.poison_timer > 0:
            self.poison_timer -= 1
            self.poison_tick += 1
            if self.poison_tick >= 45:
                self.take_damage(max(1, self.poison_damage))
                self.poison_tick = 0
        
        self.move(tiles)
        self.anim_frame = (self.anim_frame + 1) % 60
        self.pulse = (self.pulse + 2) % 360
        self.particle_timer += 1
        self.idle_float = (self.idle_float + 1) % 120
        if self.hurt_timer > 0: self.hurt_timer -= 1

    def draw(self, surface, camera):
        pos = camera.apply_rect(self.rect)
        cx, cy = pos.center
        
        # 根据敌人类型添加特殊效果
        float_offset = math.sin(math.radians(self.idle_float * 3)) * 2 if self.kind in ['ghost', 'bat'] else 0
        
        # 史莱姆 - 添加波纹效果
        if self.kind == 'slime':
            wave_radius = 35 + math.sin(math.radians(self.pulse * 2)) * 3
            wave_surf = pygame.Surface((int(wave_radius * 2), int(wave_radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(wave_surf, (*GREEN[:3], 50), (int(wave_radius), int(wave_radius)), int(wave_radius), 2)
            surface.blit(wave_surf, (cx - wave_radius, cy - wave_radius))
        
        # 幽灵 - 添加半透明光晕
        if self.kind == 'ghost':
            ghost_glow = pygame.Surface((55, 55), pygame.SRCALPHA)
            for i in range(3):
                r = 25 - i * 3
                a = 30 - i * 10
                pygame.draw.circle(ghost_glow, (*self.color[:3], a), (27, 27), r)
            surface.blit(ghost_glow, (cx - 27, cy - 27 + float_offset))
        
        # 恶魔 - 添加火焰效果
        if self.kind == 'demon':
            flame_height = 8 + math.sin(math.radians(self.pulse * 3)) * 3
            for i in range(3):
                flame_y = cy + 20 + i * 3 + float_offset
                flame_width = 6 - i * 1.5
                flame_color = (ORANGE if i == 0 else RED if i == 1 else YELLOW)
                pygame.draw.ellipse(surface, flame_color, 
                                   (cx - flame_width, flame_y - flame_height, flame_width * 2, flame_height * 2))
        
        # 蜘蛛 - 添加蛛网效果
        if self.kind == 'spider':
            web_radius = 30 + math.sin(math.radians(self.pulse)) * 2
            web_surf = pygame.Surface((int(web_radius * 2), int(web_radius * 2)), pygame.SRCALPHA)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                end_x = web_radius + math.cos(rad) * web_radius * 0.7
                end_y = web_radius + math.sin(rad) * web_radius * 0.7
                pygame.draw.line(web_surf, (*self.color[:3], 40), (web_radius, web_radius), (end_x, end_y), 1)
            surface.blit(web_surf, (cx - web_radius, cy - web_radius))
        
        # 蝙蝠 - 添加翅膀动画
        if self.kind == 'bat':
            wing_angle = math.sin(math.radians(self.pulse * 4)) * 15
            # 绘制翅膀效果
            wing_surf = pygame.Surface((50, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(wing_surf, (*self.color[:3], 100), (0, 5, 20, 20))
            pygame.draw.ellipse(wing_surf, (*self.color[:3], 100), (30, 5, 20, 20))
            rot_wing = pygame.transform.rotate(wing_surf, wing_angle)
            wing_rect = rot_wing.get_rect(center=(cx, cy + float_offset))
            surface.blit(rot_wing, wing_rect)
        
        # 骷髅 - 添加骨光效果
        if self.kind == 'skeleton':
            bone_glow = pygame.Surface((45, 45), pygame.SRCALPHA)
            pygame.draw.circle(bone_glow, (*WHITE[:3], 40), (22, 22), 22)
            surface.blit(bone_glow, (cx - 22, cy - 22))
        
        # 哥布林 - 添加武器光效
        if self.kind == 'goblin':
            weapon_x = cx + math.cos(math.radians(self.pulse)) * 15
            weapon_y = cy + math.sin(math.radians(self.pulse)) * 10
            pygame.draw.circle(surface, ORANGE, (int(weapon_x), int(weapon_y)), 3)

        # 绘制移动轨迹（快速敌人）
        if self.behavior == 'fast' and len(self.trail) > 1:
            for i, (tx, ty) in enumerate(self.trail):
                trail_pos = camera.apply(tx, ty)
                alpha = int(100 * (i / len(self.trail)))
                s = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color[:3], alpha), (4, 4), 2)
                surface.blit(s, (trail_pos[0] - 4, trail_pos[1] - 4))

        # Boss和精英怪特殊效果
        if self.behavior == 'boss' or self.is_elite:
            # Boss/精英怪光环
            pulse_radius = 3 + math.sin(math.radians(self.pulse)) * 2
            aura_radius = 58 if self.behavior == 'boss' else 25
            VisualUtils.draw_aura(surface, cx, cy, self.color, aura_radius, pulse_radius)
            if self.behavior == 'boss':
                phase_color = YELLOW if self.boss_phase == 1 else ORANGE if self.boss_phase == 2 else RED
                phase_radius = 48 + self.boss_phase * 7 + math.sin(math.radians(self.pulse * 3)) * 4
                pygame.draw.circle(surface, phase_color, (cx, cy), int(phase_radius), 2 + self.boss_phase // 2)

            # 精英怪标记 - 金色Boss特殊标记
            if self.is_elite:
                if hasattr(self, 'is_golden_boss') and self.is_golden_boss:
                    # 金色Boss - 金色光环和标记
                    golden_glow = pygame.Surface((60, 60), pygame.SRCALPHA)
                    pygame.draw.circle(golden_glow, (*YELLOW[:3], 150), (30, 30), 30)
                    surface.blit(golden_glow, (cx - 30, cy - 30))
                    crown = [(cx - 14, cy - 35), (cx - 8, cy - 45), (cx, cy - 37), (cx + 8, cy - 45), (cx + 14, cy - 35)]
                    pygame.draw.lines(surface, YELLOW, False, crown, 3)
                else:
                    elite_text = FONT_S.render("★", True, YELLOW)
                    surface.blit(elite_text, (cx - 10, cy - 30))

        # 绘制血条 - Boss和受伤的敌人总是显示血条
        if self.behavior == 'boss' or self.hp < self.max_hp:
            bar_x = pos.x
            bar_y = pos.y - 12
            fill = self.hp / self.max_hp
            
            # Boss血条更厚
            bar_height = 8 if self.behavior == 'boss' else 5
            bar_width = pos.width * 1.5 if self.behavior == 'boss' else pos.width

            # 血条背景
            pygame.draw.rect(surface, BLACK, (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), border_radius=3)
            pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=2)

            # 血条填充
            health_color = GREEN if fill > 0.5 else YELLOW if fill > 0.25 else RED
            pygame.draw.rect(surface, health_color, (bar_x, bar_y, bar_width * fill, bar_height), border_radius=2)

            # 血条边框
            pygame.draw.rect(surface, WHITE, (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), 1, border_radius=3)
            
            # Boss显示血量数值
            if self.behavior == 'boss':
                hp_text = FONT_S.render(f"{int(self.hp)}/{int(self.max_hp)}", True, WHITE)
                hp_text_rect = hp_text.get_rect(center=(bar_x + bar_width // 2, bar_y - 15))
                surface.blit(hp_text, hp_text_rect)

        # 绘制本体 - 增强版
        # 敌人发光效果
        if self.behavior == 'boss':
            glow_size = 112
        elif self.behavior == 'aggressive':
            glow_size = 45
        else:
            glow_size = 40

        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        alpha = 80 if self.hurt_timer > 0 else 40
        pygame.draw.circle(glow_surf, (*self.color[:3], alpha), (glow_size // 2, glow_size // 2), glow_size // 2 - 5)
        surface.blit(glow_surf, (cx - glow_size // 2, cy - glow_size // 2 + float_offset))

        # 动画缩放效果
        scale = 1.0
        if self.behavior == 'boss':
            scale = 1.0 + math.sin(math.radians(self.pulse * 2)) * 0.1
        elif self.kind == 'slime':
            # 史莱姆有弹跳动画
            scale = 1.0 + math.sin(math.radians(self.pulse * 3)) * 0.15

        # 应用悬浮偏移
        draw_pos = pygame.Rect(pos.x, pos.y + float_offset, pos.width, pos.height)
        
        if scale != 1.0:
            scaled_img = pygame.transform.scale(self.image, (int(pos.width * scale), int(pos.height * scale)))
            scaled_rect = scaled_img.get_rect(center=(cx, cy + float_offset))
            if self.hurt_timer > 0:
                surface.blit(scaled_img, scaled_rect, special_flags=pygame.BLEND_ADD)
            else:
                surface.blit(scaled_img, scaled_rect)
        else:
            if self.hurt_timer > 0:
                surface.blit(self.image, draw_pos, special_flags=pygame.BLEND_ADD)
            else:
                surface.blit(self.image, draw_pos)


class Item:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.item_type = item_type
        self.rect = pygame.Rect(x - 20, y - 20, 40, 40)
        self.pulse = 0
        self.bob_offset = 0
        self.creation_time = pygame.time.get_ticks()
        self.lifetime = 15000  # 15秒后消失

        # 道具配置
        self.config = {
            'health_potion': {
                'name': '治疗药水',
                'icon': '🧪',
                'color': GREEN,
                'effect': lambda player: self._heal(player)
            },
            'mana_potion': {
                'name': '能量药水',
                'icon': '⚡',
                'color': BLUE,
                'effect': lambda player: self._restore_mana(player)
            },
            'damage_boost': {
                'name': '攻击强化',
                'icon': '⚔️',
                'color': RED,
                'effect': lambda player: self._boost_damage(player)
            },
            'defense_boost': {
                'name': '防御强化',
                'icon': '🛡️',
                'color': YELLOW,
                'effect': lambda player: self._boost_defense(player)
            },
            'exp_orb': {
                'name': '经验球',
                'icon': '✨',
                'color': PURPLE,
                'effect': lambda player: self._give_exp(player)
            }
        }

    def _heal(self, player):
        heal_amount = player.max_hp * 0.3  # 恢复30%最大生命值
        player.hp = min(player.max_hp, player.hp + heal_amount)
        return f"恢复 {int(heal_amount)} 生命值"

    def _restore_mana(self, player):
        # 检查并设置能量相关属性的默认值
        if not hasattr(player, 'max_energy'):
            player.max_energy = 100
        if not hasattr(player, 'energy'):
            player.energy = 50

        restore_amount = player.max_energy * 0.4  # 恢复40%最大能量
        player.energy = min(player.max_energy, player.energy + restore_amount)
        return f"恢复 {int(restore_amount)} 能量"

    def _boost_damage(self, player):
        # 提升20%伤害，持续30秒
        if not hasattr(player, 'damage_boost'):
            player.damage_boost = 1.0
        player.damage_boost *= 1.2
        player.damage_boost_timer = 1800  # 30秒 (60fps)
        return "伤害提升20%，持续30秒"

    def _boost_defense(self, player):
        # 提升25%防御力，持续30秒
        if not hasattr(player, 'defense_boost'):
            player.defense_boost = 1.0
        player.defense_boost *= 1.25
        player.defense_boost_timer = 1800  # 30秒 (60fps)
        return "防御提升25%，持续30秒"

    def _give_exp(self, player):
        exp_amount = 50
        player.exp += exp_amount
        return f"获得 {exp_amount} 经验值"

    def update(self):
        # 脉冲动画
        self.pulse = (self.pulse + 0.05) % (2 * math.pi)
        # 上下浮动效果
        self.bob_offset = math.sin(self.pulse) * 5
        # 检查是否过期
        if pygame.time.get_ticks() - self.creation_time > self.lifetime:
            return False  # 道具过期
        return True

    def draw(self, surface, camera):
        # 获取相机偏移后的位置
        cx, cy = camera.apply(self.x, self.y + self.bob_offset)

        # 处理类型别名
        item_type = self.item_type
        if item_type == 'mana':
            item_type = 'mana_potion'  # 将'mana'映射到'mana_potion'
        elif item_type == 'health':
            item_type = 'health_potion'  # 将'health'映射到'health_potion'
        elif item_type not in self.config:
            item_type = 'exp_orb'  # 默认为经验球

        # 发光效果
        glow_size = 30 + 5 * math.sin(self.pulse)
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        color = self.config[item_type]['color']
        pygame.draw.circle(glow_surf, (*color[:3], 100), (glow_size, glow_size), glow_size)
        surface.blit(glow_surf, (cx - glow_size, cy - glow_size))

        # 绘制图标
        icon_surf = VisualUtils.create_item_icon(item_type, color, 40)
        surface.blit(icon_surf, (cx - 20, cy - 20))

    def apply_effect(self, player):
        # 处理类型别名
        item_type = self.item_type
        if item_type == 'mana':
            item_type = 'mana_potion'  # 将'mana'映射到'mana_potion'
        elif item_type == 'health':
            item_type = 'health_potion'  # 将'health'映射到'health_potion'
        elif item_type not in self.config:
            item_type = 'exp_orb'  # 默认为经验球
        return self.config[item_type]['effect'](player)


class TreasureChest:
    """宝箱"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x - 30, y - 30, 60, 60)
        self.pulse = 0
        self.bob_offset = 0
        self.opened = False
        self.reward_type = 'coins'
        
    def update(self):
        # 脉冲动画
        self.pulse = (self.pulse + 0.05) % (2 * math.pi)
        # 上下浮动效果
        self.bob_offset = math.sin(self.pulse) * 5
        return True
    
    def draw(self, surface, camera):
        # 获取相机偏移后的位置
        cx, cy = camera.apply(self.x, self.y + self.bob_offset)
        
        # 发光效果 - 金色
        glow_size = 40 + 8 * math.sin(self.pulse)
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*YELLOW[:3], 150), (glow_size, glow_size), glow_size)
        surface.blit(glow_surf, (cx - glow_size, cy - glow_size))
        
        # 绘制宝箱图标
        icon_surf = VisualUtils.create_chest_icon(YELLOW, 50)
        surface.blit(icon_surf, (cx - 25, cy - 25))
        
        # 绘制闪光效果
        if not self.opened:
            flash_size = 30 + 5 * math.sin(self.pulse * 2)
            flash_surf = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (*WHITE[:3], 100), (flash_size, flash_size), flash_size // 2)
            surface.blit(flash_surf, (cx - flash_size, cy - flash_size))


class Projectile:
    def __init__(self, x, y, tx, ty, skill_data, char_type="cyber_mage"):
        self.rect = pygame.Rect(x, y, 20, 20)
        angle = math.atan2(ty - y, tx - x)
        self.angle = angle
        self.skill_type = skill_data.get('type', 'normal')
        self.char_type = char_type  # 角色类型

        self.effects = skill_data.get('effects', {})
        self.pierce = skill_data.get('pierce', False)
        self.pierce_limit = skill_data.get('pierce_count', 1 if not self.pierce else skill_data.get('pierce_count', 3))
        self.targets_hit = 0
        self.homing = skill_data.get('homing', False)
        self.target_enemy = skill_data.get('target_enemy')

        self.damage = skill_data.get('damage')
        speed = skill_data.get('speed')
        self.life = skill_data.get('life', 60)

        # 不同技能类型的速度和伤害
        if self.damage is None or speed is None:
            if self.skill_type == 'fire':
                speed = 12
                self.damage = 30
                self.life = 50
            elif self.skill_type == 'ice':
                speed = 15
                self.damage = 25
                self.life = 70
            elif self.skill_type == 'lightning':
                speed = 18
                self.damage = 40
                self.life = 60
            elif self.skill_type == 'shadow':
                speed = 10
                self.damage = 35
                self.life = 80
            elif self.skill_type == 'holy':
                speed = 14
                self.damage = 45
                self.life = 65
            elif self.skill_type == 'chain_lightning':
                speed = 20
                self.damage = 35
                self.life = 100
                self.bounce_count = 4
                self.hit_enemies = []
            elif self.skill_type == 'boomerang':
                speed = 15
                self.damage = 30
                self.life = 150
                self.max_distance = 300
                self.traveled_distance = 0
                self.start_x, self.start_y = x, y
                self.returning = False
            else:
                speed = 10
                self.damage = 25
                self.life = 60
        elif self.skill_type == 'chain_lightning':
            self.bounce_count = skill_data.get('bounce_count', 4)
            self.hit_enemies = []
        elif self.skill_type == 'boomerang':
            self.max_distance = skill_data.get('max_distance', 300)
            self.traveled_distance = 0
            self.start_x, self.start_y = x, y
            self.returning = False

        # 根据角色类型调整速度和伤害
        if char_type == "cyber_mage":
            # 赛博法师：技能伤害+10%
            self.damage = int(self.damage * 1.1)
        elif char_type == "mech_ranger":
            # 机械游侠：子弹速度+20%
            speed *= 1.2
        elif char_type == "bio_berserker":
            # 生化狂战士：近战技能范围更大
            if self.skill_type in ['slash', 'smash', 'charge']:
                self.rect.width *= 1.5
                self.rect.height *= 1.5

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = skill_data['color']
        self.trail = []  # 轨迹
        self.rotation = 0  # 旋转角度
        self.pulse = 0  # 脉冲

        # 子弹图像
        self.image = VisualUtils.create_skill_icon(skill_data.get('visual_id', self.skill_type), self.color, 24)

    def update(self):
        # 记录轨迹
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 8:
            self.trail.pop(0)

        # 回旋飞刃特殊逻辑
        if self.skill_type == 'boomerang':
            if not self.returning:
                # 飞出阶段
                self.rect.x += self.vx
                self.rect.y += self.vy
                dist = math.hypot(self.rect.centerx - self.start_x, self.rect.centery - self.start_y)
                if dist >= self.max_distance:
                    self.returning = True
            else:
                # 返回阶段
                dx = self.start_x - self.rect.centerx
                dy = self.start_y - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 0:
                    self.vx = (dx / dist) * 15
                    self.vy = (dy / dist) * 15
                self.rect.x += self.vx
                self.rect.y += self.vy
                # 回到起点附近就消失
                if dist < 30:
                    self.life = 0
        else:
            self.rect.x += self.vx
            self.rect.y += self.vy
            if self.homing and self.target_enemy and self.target_enemy.alive:
                dx = self.target_enemy.rect.centerx - self.rect.centerx
                dy = self.target_enemy.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 0:
                    speed = math.hypot(self.vx, self.vy)
                    self.vx = (dx / dist) * speed
                    self.vy = (dy / dist) * speed
        
        self.life -= 1
        self.rotation = (self.rotation + 5) % 360
        self.pulse = (self.pulse + 4) % 360
        return self.life > 0

    def draw(self, surface, camera):
        pos = camera.apply_rect(self.rect)
        cx, cy = pos.center
        angle_deg = math.degrees(self.angle)

        # 绘制轨迹
        if len(self.trail) > 1:
            for i, (tx, ty) in enumerate(self.trail[:-1]):
                trail_pos = camera.apply(tx, ty)
                alpha = int(150 * (i / len(self.trail)))
                size = max(2, int(5 * (i / len(self.trail))))
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color[:3], alpha), (size, size), size)
                surface.blit(s, (trail_pos[0] - size, trail_pos[1] - size))

        # 根据技能类型绘制不同形状
        if self.skill_type == 'bullet':
            # 子弹 - 圆形
            pygame.draw.circle(surface, self.color, (int(cx), int(cy)), 6)
            pygame.draw.circle(surface, WHITE, (int(cx), int(cy)), 3)
        elif self.skill_type == 'arrow':
            # 箭 - 箭头形状
            arrow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            points = [(15, 10), (5, 5), (5, 15)]  # 箭头三角形
            pygame.draw.polygon(arrow_surf, self.color, points)
            pygame.draw.polygon(arrow_surf, WHITE, points, 1)
            # 箭杆
            pygame.draw.line(arrow_surf, self.color, (5, 10), (0, 10), 2)
            rot_arrow = pygame.transform.rotate(arrow_surf, -angle_deg)
            arrow_rect = rot_arrow.get_rect(center=(cx, cy))
            surface.blit(rot_arrow, arrow_rect)
        elif self.skill_type == 'missile':
            # 导弹 - 长条形带尾翼
            missile_surf = pygame.Surface((30, 12), pygame.SRCALPHA)
            # 主体
            pygame.draw.ellipse(missile_surf, self.color, (0, 2, 25, 8))
            # 头部
            pygame.draw.circle(missile_surf, WHITE, (25, 6), 4)
            # 尾翼
            pygame.draw.polygon(missile_surf, self.color, [(0, 2), (0, 10), (-5, 6)])
            rot_missile = pygame.transform.rotate(missile_surf, -angle_deg)
            missile_rect = rot_missile.get_rect(center=(cx, cy))
            surface.blit(rot_missile, missile_rect)
        elif self.skill_type == 'sniper':
            # 狙击弹 - 细长线
            end_x = cx + math.cos(self.angle) * 15
            end_y = cy + math.sin(self.angle) * 15
            pygame.draw.line(surface, self.color, (cx, cy), (end_x, end_y), 3)
            pygame.draw.circle(surface, WHITE, (int(end_x), int(end_y)), 2)
        elif self.skill_type == 'fire':
            # 火焰 - 多层发光圆形
            for i in range(3):
                r = 12 + i * 3
                alpha = 100 - i * 30
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color[:3], alpha), (r, r), r)
                surface.blit(s, (cx - r, cy - r))
        elif self.skill_type == 'ice':
            # 冰箭 - 箭头形状带冰晶
            arrow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            points = [(15, 10), (5, 5), (5, 15)]
            pygame.draw.polygon(arrow_surf, self.color, points)
            pygame.draw.polygon(arrow_surf, WHITE, points, 1)
            pygame.draw.line(arrow_surf, self.color, (5, 10), (0, 10), 2)
            # 冰晶效果
            for i in range(4):
                theta = math.radians(self.rotation + i * 90)
                px = 10 + math.cos(theta) * 8
                py = 10 + math.sin(theta) * 8
                pygame.draw.circle(arrow_surf, (255, 255, 255, 200), (int(px), int(py)), 2)
            rot_arrow = pygame.transform.rotate(arrow_surf, -angle_deg)
            arrow_rect = rot_arrow.get_rect(center=(cx, cy))
            surface.blit(rot_arrow, arrow_rect)
        elif self.skill_type == 'lightning':
            # 闪电 - 电光效果
            for i in range(5):
                r = 8 + i * 2
                alpha = 120 - i * 20
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color[:3], alpha), (r, r), r)
                surface.blit(s, (cx - r, cy - r))
            # 闪电分支
            for i in range(4):
                theta = math.radians(self.rotation + i * 90)
                end_x = cx + math.cos(theta) * 15
                end_y = cy + math.sin(theta) * 15
                pygame.draw.line(surface, (*self.color[:3], 200), (cx, cy), (end_x, end_y), 2)
        elif self.skill_type == 'shadow':
            # 暗影 - 暗色漩涡
            s = pygame.Surface((30, 30), pygame.SRCALPHA)
            for i in range(3):
                r = 10 - i * 2
                alpha = 100 - i * 30
                pygame.draw.circle(s, (*self.color[:3], alpha), (15, 15), r)
            surface.blit(s, (cx - 15, cy - 15))
        elif self.skill_type == 'holy':
            # 圣光 - 十字光效
            s = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color[:3], 150), (15, 15), 12)
            # 十字
            pygame.draw.line(s, (255, 255, 255, 200), (15, 5), (15, 25), 3)
            pygame.draw.line(s, (255, 255, 255, 200), (5, 15), (25, 15), 3)
            surface.blit(s, (cx - 15, cy - 15))
        elif self.skill_type == 'pyro_orb':
            for i in range(3):
                r = 14 + i * 4
                alpha = 110 - i * 30
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color[:3], alpha), (r, r), r)
                surface.blit(s, (cx - r, cy - r))
        elif self.skill_type == 'frost_spear':
            spear = pygame.Surface((12, 40), pygame.SRCALPHA)
            pygame.draw.polygon(spear, self.color, [(6, 0), (12, 20), (6, 40), (0, 20)])
            rot = pygame.transform.rotate(spear, -angle_deg + 90)
            rect = rot.get_rect(center=(cx, cy))
            surface.blit(rot, rect)
        elif self.skill_type == 'tracking_missile':
            missile_surf = pygame.Surface((30, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(missile_surf, self.color, (0, 2, 25, 10))
            pygame.draw.polygon(missile_surf, self.color, [(0, 1), (0, 13), (-6, 7)])
            rot = pygame.transform.rotate(missile_surf, -angle_deg)
            rect = rot.get_rect(center=(cx, cy))
            surface.blit(rot, rect)
        elif self.skill_type == 'poison_edge':
            dagger = pygame.Surface((8, 30), pygame.SRCALPHA)
            pygame.draw.polygon(dagger, self.color, [(4, 0), (8, 20), (4, 30), (0, 20)])
            rot = pygame.transform.rotate(dagger, -angle_deg + 90)
            rect = rot.get_rect(center=(cx, cy))
            surface.blit(rot, rect)
        elif self.skill_type == 'slash':
            # 斩击 - 弧形
            arc_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.arc(arc_surf, self.color, (0, 0, 30, 30), 0, math.pi, 3)
            rot_arc = pygame.transform.rotate(arc_surf, -angle_deg)
            arc_rect = rot_arc.get_rect(center=(cx, cy))
            surface.blit(rot_arc, arc_rect)
        elif self.skill_type == 'smash':
            # 猛击 - 大圆形冲击波
            for i in range(2):
                r = 15 + i * 5
                alpha = 150 - i * 50
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color[:3], alpha), (r, r), r, 2)
                surface.blit(s, (cx - r, cy - r))
        elif self.skill_type == 'charge':
            # 冲锋 - 长条形
            charge_surf = pygame.Surface((40, 15), pygame.SRCALPHA)
            pygame.draw.ellipse(charge_surf, self.color, (0, 0, 40, 15))
            pygame.draw.circle(charge_surf, WHITE, (35, 7), 5)
            rot_charge = pygame.transform.rotate(charge_surf, -angle_deg)
            charge_rect = rot_charge.get_rect(center=(cx, cy))
            surface.blit(rot_charge, charge_rect)
        elif self.skill_type == 'electric':
            # 电磁脉冲 - 圆形带波纹
            for i in range(3):
                r = 10 + i * 4
                alpha = 120 - i * 30
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color[:3], alpha), (r, r), r, 2)
                surface.blit(s, (cx - r, cy - r))
        elif self.skill_type == 'chain_lightning':
            # 连锁闪电 - 闪电球
            for i in range(4):
                r = 8 + i * 2
                alpha = 100 - i * 20
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color[:3], alpha), (r, r), r)
                surface.blit(s, (cx - r, cy - r))
        elif self.skill_type == 'boomerang':
            # 回旋飞刃 - 月牙形
            boomerang_surf = pygame.Surface((25, 25), pygame.SRCALPHA)
            # 月牙形状
            pygame.draw.arc(boomerang_surf, self.color, (0, 0, 25, 25), 0, math.pi * 2, 4)
            pygame.draw.arc(boomerang_surf, self.color, (5, 5, 15, 15), 0, math.pi * 2, 4)
            rot_boomerang = pygame.transform.rotate(boomerang_surf, self.rotation * 2)
            boomerang_rect = rot_boomerang.get_rect(center=(cx, cy))
            surface.blit(rot_boomerang, boomerang_rect)
        else:
            # 默认 - 圆形
            pygame.draw.circle(surface, self.color, (int(cx), int(cy)), 6)
            pygame.draw.circle(surface, WHITE, (int(cx), int(cy)), 3)

import os
import pygame
import random
import math
import sys
from config import *
from entities import Player, Enemy, Item, Projectile, TreasureChest
from systems import Camera, DungeonGenerator
from visual_effects import VisualUtils, Particle
from skill_entities import Mine, Decoy, GravityField, PoisonField
from ui_components import (
    draw_button,
    draw_corner_brackets,
    draw_grid_background,
    draw_keycap,
    draw_panel,
    draw_wrapped_text,
)


# ==================== 游戏主控 ====================
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cyber Dungeon - 修复增强版")
        self.clock = pygame.time.Clock()
        self.camera = Camera()
        self.state = "MENU"  # MENU, CHAR_SELECT, TALENT_SELECT, GAME, GAMEOVER, SHOP
        self.particles = []
        self.items = []  # 道具列表
        self.skill_selection_active = False  # 技能选择界面
        self.skill_selection_options = []  # 技能选择选项
        self.skill_selection_index = 0
        self.skill_editor_active = False  # 技能编辑器界面（后门）
        self.skill_editor_selected_index = 0  # 当前选中的技能索引
        self.game_paused = False  # 游戏暂停状态
        self.game_time = 0  # 游戏时间（帧数）
        self.enemy_spawn_timer = 0  # 怪物生成计时器
        self.enemy_spawn_interval = 300  # 初始生成间隔（5秒）
        self.manual_lines = self._load_manual_text()
        self.manual_scroll = 0
        
        # 地图和Boss系统
        self.current_map = 1  # 当前地图编号
        self.boss_spawned = False  # Boss是否已生成
        self.boss_defeated = False  # Boss是否被击败
        self.enemies_killed_this_map = 0  # 当前地图击杀数
        self.map_enemy_count = 0  # 当前地图敌人总数
        
        # 商店系统
        self.shop_active = False  # 商店是否激活
        self.shop_selected_index = 0  # 商店选中项
        self.golden_bosses_killed = 0  # 金色Boss击杀数
        self.golden_bosses_required = 5  # 需要击败的金色Boss数量才能打开商店（降低频率）
        self.shop_upgrades = {}  # 商店购买记录（每关重置）
        self.treasure_chests = []  # 宝箱列表
        self.shop_available = False  # 商店是否可用（是否已拾取宝箱）
        self.player_pos_before_shop = None  # 进入商店前的玩家位置
        
        # 游戏速度系统
        self.game_speed = 1.0  # 游戏速度倍数（1.0 = 正常速度，2.0 = 2倍速）

        # 成就系统
        self.achievements = {
            'first_kill': {'name': '初次击杀', 'desc': '击败第一个敌人', 'completed': False, 'reward': 50},
            'kill_50_enemies': {'name': '杀戮成瘾', 'desc': '击败50个敌人', 'completed': False, 'reward': 200},
            'kill_100_enemies': {'name': '屠魔大师', 'desc': '击败100个敌人', 'completed': False, 'reward': 500},
            'elite_hunter': {'name': '精英猎手', 'desc': '击败10个精英怪', 'completed': False, 'reward': 300},
            'collect_1000_coins': {'name': '财富积累', 'desc': '收集1000枚金币', 'completed': False, 'reward': 100},
            'reach_level_10': {'name': '等级提升', 'desc': '玩家等级达到10级', 'completed': False, 'reward': 250},
            'survive_5_minutes': {'name': '坚持到底', 'desc': '生存5分钟', 'completed': False, 'reward': 150},
            'use_20_skills': {'name': '技能大师', 'desc': '使用技能20次', 'completed': False, 'reward': 150}
        }
        self.total_kills = 0  # 总击杀数
        self.total_elite_kills = 0  # 精英怪击杀数
        self.total_skill_uses = 0  # 技能使用次数
        self.new_achievements = []
        self.feedback_messages = []
        self.upgrade_charge = 0
        self.upgrade_charge_required = 2
        self.skill_choices_made = 0
        self.chests_opened = 0
        self.objective_chests_total = 0
        self.boss_wave = False

        # 波次挑战模式
        self.wave_mode = True  # 默认启用波次模式
        self.current_wave = 0
        self.wave_enemies_count = 0  # 本波敌人总数
        self.wave_enemies_killed = 0  # 本波已击杀敌人数量
        self.wave_cooldown = 0  # 波次间隔冷却时间
        self.wave_cooldown_max = 300  # 波次间隔5秒，给探索和观察留出空间
        self.wave_active = False  # 当前波次是否激活

        # 角色选择相关
        self.char_options = [
            {
                'type': 'cyber_mage',
                'name': '赛博法师',
                'emoji': '🧙‍♂️',
                'color': BLUE,
                'desc': '元素亲和: 技能伤害+10%, CD-5%'
            },
            {
                'type': 'mech_ranger',
                'name': '机械游侠',
                'emoji': '🏹',
                'color': GREEN,
                'desc': '速射: 普攻CD-30%, 双发子弹'
            },
            {
                'type': 'bio_berserker',
                'name': '生化狂战士',
                'emoji': '🔪',
                'color': RED,
                'desc': '吸血: 攻击恢复5%伤害值血量'
            },
            {
                'type': 'shadow_assassin',
                'name': '暗影刺客',
                'emoji': '🥷',
                'color': (100, 50, 150),
                'desc': '暗影之力: 暴击率+15%, 移动速度+10%'
            },
            {
                'type': 'holy_knight',
                'name': '圣光骑士',
                'emoji': '🛡️',
                'color': YELLOW,
                'desc': '圣光庇护: 防御力+20%, 生命回复+1/秒'
            }
        ]
        self.selected_char = 'cyber_mage'  # 默认选择赛博法师
        self.char_selection_index = 0

        # 初始天赋选择相关
        self.talent_options = [
            {
                'type': 'combat',
                'name': '战斗天赋',
                'emoji': '⚔️',
                'color': ORANGE,
                'desc': '初始：自动攻击\n全局伤害 +8%\n适合主动进攻'
            },
            {
                'type': 'survival',
                'name': '生存天赋',
                'emoji': '🛡️',
                'color': BLUE,
                'desc': '初始：防护盾\n最大生命 +15%\n受到伤害 -12%'
            },
            {
                'type': 'exploration',
                'name': '探索天赋',
                'emoji': '💰',
                'color': YELLOW,
                'desc': '初始：环绕光球\n额外宝箱 +1\n金币收益 +25%'
            }
        ]
        self.selected_talent = 'combat'  # 默认选择战斗天赋
        self.talent_selection_index = 0

    def init_game_world(self, map_num=None):
        if map_num is not None:
            self.current_map = map_num
        else:
            self.current_map = 1
            
        gen = DungeonGenerator()
        self.map_w, self.map_h = 60, 60
        self.tiles, self.rooms = gen.generate(self.map_w, self.map_h)

        start_pos = self.rooms[0].center
        # 如果是新地图，保持玩家属性；如果是第一张地图，创建新玩家
        if not hasattr(self, 'player') or self.current_map == 1:
            self.player = Player(start_pos[0] * TILE_SIZE, start_pos[1] * TILE_SIZE, self.selected_char,
                                 self.selected_talent)
        else:
            # 新地图，保持玩家属性但重置位置
            self.player.rect.x = start_pos[0] * TILE_SIZE
            self.player.rect.y = start_pos[1] * TILE_SIZE

        self.enemies = []
        self.projectiles = []
        self.combat_effects = []
        self.items = []  # 重置道具列表
        self.mines = []  # 地雷列表
        self.decoys = []  # 分身列表
        self.gravity_fields = []  # 重力场列表
        self.poison_fields = []  # 毒雾场列表
        self.treasure_chests = []  # 重置宝箱列表
        self.game_time = 0
        self.enemy_spawn_timer = 0
        self.boss_spawned = False
        self.boss_defeated = False
        self.enemies_killed_this_map = 0
        self.golden_bosses_killed = 0  # 重置金色Boss计数
        self.shop_upgrades = {}  # 重置商店购买记录
        self.shop_available = False  # 重置商店可用状态
        self.shop_active = False  # 重置商店激活状态
        self.player_pos_before_shop = None  # 重置位置保存
        self.player_pos_before_skill_selection = None  # 重置技能选择位置保存
        self.feedback_messages = []
        self.upgrade_charge = 0
        self.upgrade_charge_required = 2
        self.skill_choices_made = 0
        self.chests_opened = 0
        
        # 重置波次状态
        self.wave_active = False
        self.wave_enemies_count = 0
        self.wave_enemies_killed = 0
        self.current_wave = 0
        self.prepare_next_wave(immediate=False)
        
        # 根据地图编号调整敌人数量和强度
        map_multiplier = 1.0 + (self.current_map - 1) * 0.5  # 每张地图增加50%强度
        # 房间内只保留少量游荡敌人，主要压力由波次逐渐建立。
        enemy_types = ['goblin', 'slime', 'bat']
        if self.current_map > 1:
            enemy_types.extend(['skeleton', 'ghost', 'spider'])
        self.map_enemy_count = 0
        ambient_enemy_limit = 2 + max(0, self.current_map - 1) * 2

        for room in self.rooms[1:]:
            if self.map_enemy_count >= ambient_enemy_limit:
                break
            if random.random() < min(0.42, 0.18 + self.current_map * 0.05):
                kind = random.choice(enemy_types)
                enemy_count = 1 if self.current_map == 1 else random.randint(1, 2)
                    
                for _ in range(enemy_count):
                    if self.map_enemy_count >= ambient_enemy_limit:
                        break
                    ex = (room.x + random.randint(1, room.width - 1)) * TILE_SIZE
                    ey = (room.y + random.randint(1, room.height - 1)) * TILE_SIZE
                    is_elite = random.random() < (0.02 if self.current_map == 1 else 0.06)
                    enemy = Enemy(ex, ey, kind, is_elite)
                    
                    # 根据地图编号增强敌人
                    enemy.hp = int(enemy.hp * map_multiplier)
                    enemy.max_hp = enemy.hp
                    enemy.damage = int(enemy.damage * map_multiplier)
                    if self.current_map > 1:
                        enemy.speed *= (1.0 + (self.current_map - 1) * 0.1)
                    
                    self.enemies.append(enemy)
                    self.map_enemy_count += 1

        self.spawn_exploration_chests()
        self.add_feedback("跟随指引寻找能量宝箱，首波将在数秒后抵达", UI_PRIMARY, 300)

    def spawn_exploration_chests(self):
        """在远离出生点的房间放置探索目标。"""
        if len(self.rooms) <= 1:
            return
        start = self.rooms[0].center
        candidates = sorted(
            self.rooms[1:],
            key=lambda room: abs(room.centerx - start[0]) + abs(room.centery - start[1]),
            reverse=True,
        )
        chest_count = min(len(candidates), 3 + getattr(self.player, 'extra_chests', 0))
        pool = candidates[:max(chest_count * 2, chest_count)]
        selected_rooms = random.sample(pool, chest_count) if len(pool) >= chest_count else pool
        for index, room in enumerate(selected_rooms):
            chest = TreasureChest(room.centerx * TILE_SIZE, room.centery * TILE_SIZE)
            chest.reward_type = ('coins', 'recovery', 'charge')[index % 3]
            self.treasure_chests.append(chest)
        self.objective_chests_total = len(self.treasure_chests)

    def add_feedback(self, text, color=WHITE, duration=150):
        self.feedback_messages.append({'text': text, 'color': color, 'timer': duration})
        self.feedback_messages = self.feedback_messages[-4:]

    def gain_upgrade_charge(self, amount, reason):
        if self.skill_selection_active:
            return
        self.upgrade_charge += amount
        self.add_feedback(f"构筑能量 +{amount}  {reason}", UI_ACCENT, 150)
        if self.upgrade_charge >= self.upgrade_charge_required:
            self.show_skill_selection()

    def handle_input(self):
        """处理玩家输入"""
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # 技能编辑器按键处理（优先级最高）
            if event.type == pygame.KEYDOWN and self.skill_editor_active and self.state == "GAME":
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.skill_editor_selected_index = max(0, self.skill_editor_selected_index - 1)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    if hasattr(self, 'player') and self.player:
                        skill_list = list(self.player.available_passives.keys())
                        self.skill_editor_selected_index = min(len(skill_list) - 1, self.skill_editor_selected_index + 1)
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.adjust_skill_level(-1)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.adjust_skill_level(1)
                elif event.key == pygame.K_ESCAPE:
                    self.skill_editor_active = False
                # 阻止编辑器激活时的其他按键事件
                continue
            
            # 处理移动相关的键盘事件（支持中文键盘）- 只在游戏状态下处理，且编辑器未激活
            if self.state == "GAME" and not self.skill_editor_active and not self.skill_selection_active and hasattr(self, 'player') and self.player:
                if event.type == pygame.KEYDOWN:
                    # 向上移动
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        self.player.move_up = True
                    # 向下移动
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        self.player.move_down = True
                    # 向左移动
                    elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        self.player.move_left = True
                    # 向右移动
                    elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.player.move_right = True
                    # 冲刺
                    elif event.key == pygame.K_LSHIFT:
                        self.player.sprint = True

                elif event.type == pygame.KEYUP:
                    # 停止向上移动
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        self.player.move_up = False
                    # 停止向下移动
                    if event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        self.player.move_down = False
                    # 停止向左移动
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        self.player.move_left = False
                    # 停止向右移动
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.player.move_right = False
                    # 停止冲刺
                    if event.key == pygame.K_LSHIFT:
                        self.player.sprint = False

            if event.type == pygame.KEYDOWN:
                if self.state == "MANUAL":
                    if event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                        self.state = "MENU"
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        max_scroll = max(0, len(self.manual_lines) - 22)
                        self.manual_scroll = min(max_scroll, self.manual_scroll + 1)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.manual_scroll = max(0, self.manual_scroll - 1)
                    continue
                # 主菜单和游戏结束状态
                if event.key == pygame.K_SPACE:
                    if self.state == "MENU":
                        self.state = "CHAR_SELECT"
                    elif self.state == "GAMEOVER":
                        self.state = "CHAR_SELECT"
                    elif self.state == "CHAR_SELECT":
                        self.state = "TALENT_SELECT"
                    elif self.state == "TALENT_SELECT" and self.selected_talent:
                        # 天赋选择完成后进入游戏
                        self.init_game_world()
                        self.state = "GAME"

                # 角色选择状态 - 键盘选择
                elif self.state == "CHAR_SELECT":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.char_selection_index = (self.char_selection_index - 1) % len(self.char_options)
                        self.selected_char = self.char_options[self.char_selection_index]['type']
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.char_selection_index = (self.char_selection_index + 1) % len(self.char_options)
                        self.selected_char = self.char_options[self.char_selection_index]['type']
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.state = "TALENT_SELECT"
                    elif pygame.K_1 <= event.key <= pygame.K_5:
                        self.char_selection_index = event.key - pygame.K_1
                        self.selected_char = self.char_options[self.char_selection_index]['type']
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"

                # 天赋选择状态
                elif self.state == "TALENT_SELECT":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.talent_selection_index = (self.talent_selection_index - 1) % len(self.talent_options)
                        self.selected_talent = self.talent_options[self.talent_selection_index]['type']
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.talent_selection_index = (self.talent_selection_index + 1) % len(self.talent_options)
                        self.selected_talent = self.talent_options[self.talent_selection_index]['type']
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.init_game_world()
                        self.state = "GAME"
                    elif pygame.K_1 <= event.key <= pygame.K_3:
                        self.talent_selection_index = event.key - pygame.K_1
                        self.selected_talent = self.talent_options[self.talent_selection_index]['type']
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "CHAR_SELECT"

                # 菜单状态下查看说明书
                if self.state == "MENU" and event.key == pygame.K_h:
                    self.state = "MANUAL"
                    self.manual_scroll = 0
                    continue

                # 游戏状态下的键盘输入
                elif self.state == "GAME":
                    # 暂停功能：按P键暂停/继续
                    if event.key == pygame.K_p:
                        self.game_paused = not self.game_paused
                        continue
                    # 后门功能：按Ctrl+K打开技能编辑器（优先级最高）
                    if event.key == pygame.K_k and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self.skill_editor_active = not self.skill_editor_active
                        self.skill_editor_selected_index = 0
                        continue  # 阻止其他按键处理
                    # 商店界面处理 - 按B打开/关闭商店（优先级较高，在其他逻辑之前）
                    if event.key == pygame.K_b:
                        # 如果有可用商店（宝箱已拾取），切换商店状态
                        if self.shop_available:
                            if not self.shop_active:
                                # 打开商店时保存玩家位置
                                self.player_pos_before_shop = (self.player.rect.x, self.player.rect.y)
                                self.shop_active = True
                            else:
                                # 关闭商店时恢复玩家位置
                                if self.player_pos_before_shop:
                                    self.player.rect.x, self.player.rect.y = self.player_pos_before_shop
                                    self.player_pos_before_shop = None
                                self.shop_active = False
                                # 更新相机到玩家位置
                                self.camera.update(self.player)
                            continue  # 阻止其他按键处理
                    
                    if self.shop_active:
                        if event.key == pygame.K_UP or event.key == pygame.K_w:
                            self.shop_selected_index = max(0, self.shop_selected_index - 1)
                        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            self.shop_selected_index = min(7, self.shop_selected_index + 1)
                        elif event.key == pygame.K_RETURN:  # 只用回车购买
                            self.buy_shop_item(self.shop_selected_index)
                        elif event.key == pygame.K_ESCAPE or event.key == pygame.K_b:
                            # 关闭商店时恢复玩家位置
                            if self.player_pos_before_shop:
                                self.player.rect.x, self.player.rect.y = self.player_pos_before_shop
                                self.player_pos_before_shop = None
                            self.shop_active = False
                            # 更新相机到玩家位置
                            self.camera.update(self.player)
                        continue
                    
                    # 后门：Ctrl+C 增加金币
                    if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self.player.coins += 1000
                        print(f"金币已增加1000，当前金币: {self.player.coins}")
                        continue
                    
                    # 2倍速切换：Ctrl+T
                    if event.key == pygame.K_t and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        if self.game_speed == 1.0:
                            self.game_speed = 2.0
                            print("游戏速度：2倍速")
                        else:
                            self.game_speed = 1.0
                            print("游戏速度：正常速度")
                        continue
                    
                    # 技能释放（编辑器未激活且未暂停时）
                    if not self.skill_selection_active and not self.skill_editor_active and not self.game_paused:
                        if event.key == pygame.K_1: self.use_skill(0)
                        if event.key == pygame.K_2: self.use_skill(1)
                        if event.key == pygame.K_3: self.use_skill(2)
                        if event.key == pygame.K_4: self.use_skill(3)
                        if event.key == pygame.K_5: self.use_skill(4)
                        # 后门功能：按Ctrl+L直接获得顶级技能
                        elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            # 1. 获得所有顶级被动技能
                            for skill_id, skill_data in self.player.available_passives.items():
                                self.player.passive_skills[skill_id] = {
                                    'level': skill_data['max_level'],
                                    'name': skill_data['name']
                                }

                            # 2. 获得所有顶级主动技能（填充到技能栏）
                            # 确保技能栏有5个技能
                            skill_types = ['fireball', 'ice_shard', 'lightning_bolt', 'meteor', 'heal']
                            for i, skill_type in enumerate(skill_types):
                                if i < len(self.player.skills):
                                    self.player.skills[i] = {
                                        'name': skill_type.replace('_', ' ').title(),
                                        'icon': '✨',
                                        'color': CYAN,
                                        'damage': 999,
                                        'range': 500,
                                        'aoe': 150,
                                        'cd': 60,  # 1秒冷却
                                        'cur': 0,
                                        'key': str(i + 1),
                                        'type': skill_type
                                    }

                            # 3. 给玩家大量资源
                            self.player.max_hp = self.player.hp = 9999
                            self.player.coins = 99999
                            self.player.exp = 99999
                            self.player.level = 99

                            # 4. 视觉反馈 - 添加大量粒子效果
                            for _ in range(100):
                                x = random.randint(0, SCREEN_WIDTH)
                                y = random.randint(0, SCREEN_HEIGHT)
                                color = random.choice([YELLOW, GREEN, BLUE, PURPLE])
                                self.particles.append(Particle(x, y, color, 'spark'))

                            # 5. 屏幕抖动
                            self.camera.shake(intensity=20)

                            # 6. 添加成就提示样式的消息
                            cheat_achievement = {
                                'name': '开发者模式已激活',
                                'desc': '获得所有顶级技能和资源',
                                'reward': 0
                            }
                            self.new_achievements.append(cheat_achievement)

                            # 7. 添加控制台提示
                            print("后门激活：已获得所有顶级技能和资源！")
                        # 返回主菜单
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "MENU"

                    # 技能选择界面
                    elif self.skill_selection_active:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            self.skill_selection_index = (self.skill_selection_index - 1) % len(self.skill_selection_options)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.skill_selection_index = (self.skill_selection_index + 1) % len(self.skill_selection_options)
                        elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                            self.select_skill(self.skill_selection_index)
                        elif event.key == pygame.K_1 and len(self.skill_selection_options) > 0:
                            self.select_skill(0)
                        elif event.key == pygame.K_2 and len(self.skill_selection_options) > 1:
                            self.select_skill(1)
                        elif event.key == pygame.K_3 and len(self.skill_selection_options) > 2:
                            self.select_skill(2)

            # 鼠标点击事件（独立处理）
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 角色选择状态 - 鼠标点击选择角色
                if self.state == "CHAR_SELECT":
                    mx, my = event.pos
                    for i, char in enumerate(self.char_options):
                        box_rect = self.get_character_card_rect(i)
                        if box_rect.collidepoint(mx, my):
                            self.char_selection_index = i
                            self.selected_char = char['type']
                            self.state = "TALENT_SELECT"
                            break  # 找到匹配的角色后退出循环 event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 左键点击
                if self.state == "TALENT_SELECT":
                    mx, my = event.pos
                    for i, talent in enumerate(self.talent_options):
                        option_rect = self.get_talent_card_rect(i)
                        if option_rect.collidepoint(mx, my):
                            self.talent_selection_index = i
                            self.selected_talent = talent['type']
                    start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 180, 735, 360, 60)
                    if start_rect.collidepoint(mx, my) and self.selected_talent:
                        self.init_game_world()
                        self.state = "GAME"
                    # 检查是否点击了返回按钮区域
                    back_rect = pygame.Rect(50, SCREEN_HEIGHT - 80, 150, 40)
                    if back_rect.collidepoint(mx, my):
                        self.state = "CHAR_SELECT"

        # 鼠标持续攻击
        if self.state == "GAME" and pygame.mouse.get_pressed()[0]:
            # 简单的普通攻击逻辑(利用0号技能的CD)
            if hasattr(self, 'player') and self.player and len(self.player.skills) > 0 and self.player.skills[0][
                'cur'] == 0:
                self.use_skill(0, force_basic=True)
        
        # 使用get_pressed()检测按键状态，支持中文输入法下的wasd移动（编辑器未激活且未暂停且商店未激活且技能选择未激活时）
        if self.state == "GAME" and not self.game_paused and not self.skill_editor_active and not self.shop_active and not self.skill_selection_active:
            if hasattr(self, 'player') and self.player:
                keys = pygame.key.get_pressed()
                self.player.move_up = keys[pygame.K_w] or keys[pygame.K_UP]
                self.player.move_down = keys[pygame.K_s] or keys[pygame.K_DOWN]
                self.player.move_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
                self.player.move_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
                self.player.sprint = keys[pygame.K_LSHIFT]

    def check_achievements(self):
        """检查并解锁成就"""
        # 检查击杀相关成就
        if self.total_kills == 1 and not self.achievements['first_kill']['completed']:
            self.unlock_achievement('first_kill')
        if self.total_kills >= 50 and not self.achievements['kill_50_enemies']['completed']:
            self.unlock_achievement('kill_50_enemies')
        if self.total_kills >= 100 and not self.achievements['kill_100_enemies']['completed']:
            self.unlock_achievement('kill_100_enemies')

        # 检查精英怪击杀成就
        if self.total_elite_kills >= 10 and not self.achievements['elite_hunter']['completed']:
            self.unlock_achievement('elite_hunter')

        # 检查金币收集成就
        if hasattr(self.player, 'coins') and self.player.coins >= 1000 and not self.achievements['collect_1000_coins'][
            'completed']:
            self.unlock_achievement('collect_1000_coins')

        # 检查等级成就
        if hasattr(self.player, 'level') and self.player.level >= 10 and not self.achievements['reach_level_10'][
            'completed']:
            self.unlock_achievement('reach_level_10')

        # 检查生存时间成就（5分钟 = 300秒 = 18000帧）
        if self.game_time >= 18000 and not self.achievements['survive_5_minutes']['completed']:
            self.unlock_achievement('survive_5_minutes')

        # 检查技能使用成就
        if self.total_skill_uses >= 20 and not self.achievements['use_20_skills']['completed']:
            self.unlock_achievement('use_20_skills')

    def unlock_achievement(self, achievement_id):
        """解锁成就并给予奖励"""
        if achievement_id in self.achievements and not self.achievements[achievement_id]['completed']:
            self.achievements[achievement_id]['completed'] = True
            self.new_achievements.append(self.achievements[achievement_id])
            # 给予金币奖励
            if hasattr(self.player, 'coins'):
                self.player.coins += self.achievements[achievement_id]['reward']
            # 添加特效
            for _ in range(20):
                self.particles.append(Particle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, YELLOW, 'spark'))

    def prepare_next_wave(self, immediate=False):
        """准备下一波敌人"""
        self.current_wave += 1
        self.wave_cooldown = 0 if immediate else self.wave_cooldown_max
        self.wave_active = False
        self.wave_enemies_count = 0
        self.wave_enemies_killed = 0

        self.boss_wave = self.current_wave % 5 == 0
        # 前几波保持小规模，之后以强度和组合变化为主。
        base_enemies = 1 if self.boss_wave else min(11, 3 + int((self.current_wave - 1) * 0.75))

        enemy_types = ['goblin', 'slime', 'bat', 'skeleton', 'demon', 'ghost', 'spider']
        # 高波次增加更强的敌人
        if self.current_wave >= 4:
            enemy_types.extend(['demon', 'ghost', 'skeleton'])  # 增加更强敌人出现频率
        if self.current_wave >= 8:
            enemy_types.extend(['demon', 'ghost'])  # 进一步增加强力敌人

        # 计算这一波的敌人总数
        self.wave_enemies_count = base_enemies

        # 给玩家一些准备时间的提示特效
        for _ in range(50):
            self.particles.append(Particle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, ORANGE, 'energy'))

    def spawn_wave_enemies(self):
        """生成一波敌人"""
        if not self.wave_active:
            self.wave_active = True

            enemy_types = ['goblin', 'slime', 'bat', 'skeleton', 'demon', 'ghost', 'spider']
            elite_chance = min(0.16, 0.02 + self.current_wave * 0.012)

            target_count = max(1, self.wave_enemies_count)
            spawned = 0
            attempts = 0
            max_attempts = target_count * 10

            # 生成所有敌人
            while spawned < target_count and attempts < max_attempts:
                attempts += 1
                # 在玩家周围随机位置生成
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(400, 700)  # 更远的生成距离
                spawn_x = self.player.rect.centerx + math.cos(angle) * distance
                spawn_y = self.player.rect.centery + math.sin(angle) * distance

                # 确保生成在地图内
                spawn_x = max(TILE_SIZE, min(self.map_w * TILE_SIZE - TILE_SIZE, spawn_x))
                spawn_y = max(TILE_SIZE, min(self.map_h * TILE_SIZE - TILE_SIZE, spawn_y))

                # 检查是否在墙内
                grid_x = int(spawn_x // TILE_SIZE)
                grid_y = int(spawn_y // TILE_SIZE)
                if 0 <= grid_y < len(self.tiles) and 0 <= grid_x < len(self.tiles[0]) and self.tiles[grid_y][grid_x] == 0:
                    kind = 'dragon' if self.boss_wave and spawned == 0 else random.choice(enemy_types)
                    is_elite = False if kind == 'dragon' else random.random() < elite_chance
                    enemy = Enemy(spawn_x, spawn_y, kind, is_elite)
                    enemy.is_wave_enemy = True

                    if kind == 'dragon':
                        boss_scale = 1.0 + (self.current_wave // 5 - 1) * 0.35 + (self.current_map - 1) * 0.4
                        enemy.hp = int(700 * boss_scale)
                        enemy.max_hp = enemy.hp
                        enemy.damage = int(28 * boss_scale)
                        enemy.speed = 1.25 + min(0.45, self.current_wave * 0.02)
                        self.boss_spawned = True
                        self.add_feedback("警告：深渊龙王已苏醒", UI_DANGER, 240)

                    # 波次越高，敌人越强
                    if self.current_wave > 1 and kind != 'dragon':
                        enemy.hp = int(enemy.hp * (1 + (self.current_wave - 1) * 0.15))
                        enemy.damage = int(enemy.damage * (1 + (self.current_wave - 1) * 0.12))

                        if self.current_wave > 5:
                            enemy.speed *= 1.05
                            if not hasattr(enemy, 'defense'):
                                enemy.defense = 0
                            enemy.defense = int(enemy.defense * 1.05)

                        if is_elite:
                            enemy.hp = int(enemy.hp * 1.5)
                            enemy.damage = int(enemy.damage * 1.2)
                            enemy.speed *= 1.1

                    self.enemies.append(enemy)
                    spawned += 1

            # 如果由于障碍导致没有生成敌人，直接进入下一波
            if spawned == 0:
                fallback_kind = 'dragon' if self.boss_wave else random.choice(enemy_types)
                fallback_enemy = Enemy(self.player.rect.centerx + 220, self.player.rect.centery, fallback_kind, False)
                fallback_enemy.is_wave_enemy = True
                if fallback_kind == 'dragon':
                    boss_scale = 1.0 + (self.current_wave // 5 - 1) * 0.35 + (self.current_map - 1) * 0.4
                    fallback_enemy.hp = int(700 * boss_scale)
                    fallback_enemy.damage = int(28 * boss_scale)
                    fallback_enemy.max_hp = fallback_enemy.hp
                    self.boss_spawned = True
                    self.add_feedback("警告：深渊龙王已苏醒", UI_DANGER, 240)
                elif self.current_wave > 1:
                    fallback_enemy.hp = int(fallback_enemy.hp * (1 + (self.current_wave - 1) * 0.15))
                    fallback_enemy.damage = int(fallback_enemy.damage * (1 + (self.current_wave - 1) * 0.12))
                    fallback_enemy.max_hp = fallback_enemy.hp
                self.enemies.append(fallback_enemy)
                spawned = 1

            self.wave_enemies_count = spawned
            self.wave_enemies_killed = 0

    def use_skill(self, idx, force_basic=False):
        # 安全检查
        if not hasattr(self, 'player') or not self.player:
            return
        if idx < 0 or idx >= len(self.player.skills):
            return
        skill = self.player.skills[idx]
        if skill['cur'] == 0 or force_basic:
            if not force_basic:
                # 赛博法师的CD减少5%
                cd = skill['cd']
                if self.player.char_type == "cyber_mage":
                    cd = int(cd * 0.95)
                skill['cur'] = cd  # 触发冷却
            else:
                # 普通攻击冷却
                basic_cd = 15
                if self.player.char_type == "mech_ranger":
                    basic_cd = int(basic_cd * 0.7)  # 游侠的普攻CD减少30%
                self.player.skills[0]['cur'] = basic_cd

            mx, my = pygame.mouse.get_pos()
            # 计算世界坐标
            world_x = mx + self.camera.offset.x
            world_y = my + self.camera.offset.y

            handled = False
            behavior = skill.get('behavior', 'projectile')
            if behavior != 'projectile':
                handled = self.handle_active_skill(skill, world_x, world_y)

            if not handled:
                self.fire_projectile(skill, world_x, world_y, force_basic=force_basic)

            if not force_basic:
                self.total_skill_uses += 1
                self.player.energy_waves.append((0, 30))

    def handle_active_skill(self, skill, world_x, world_y):
        behavior = skill.get('behavior', 'projectile')
        skill_type = skill.get('type', 'normal')

        # 兼容旧的特殊类型
        if behavior == 'projectile':
            if skill_type == 'freeze_mine':
                self.mines.append(Mine(world_x, world_y))
                return True
            if skill_type == 'decoy':
                self.decoys.append(Decoy(self.player.rect.centerx, self.player.rect.centery))
                return True
            if skill_type == 'gravity_field':
                self.gravity_fields.append(GravityField(world_x, world_y))
                return True
            return False

        if behavior == 'area':
            center = skill.get('center', 'cursor')
            cx, cy = (world_x, world_y) if center == 'cursor' else self.player.rect.center
            radius = skill.get('radius', 150)
            damage = skill.get('damage', 50)
            self.add_combat_effect('area', skill.get('color', WHITE), (cx, cy), radius=radius, width=5, duration=24)
            self.deal_area_damage(cx, cy, radius, damage, skill.get('effects'))
            self.camera.shake(5)
            return True

        if behavior == 'beam':
            start_x, start_y = self.player.rect.center
            dx, dy = world_x - start_x, world_y - start_y
            dist = math.hypot(dx, dy) or 1
            length = skill.get('range', 600)
            end_x = start_x + (dx / dist) * length
            end_y = start_y + (dy / dist) * length
            self.add_combat_effect('beam', skill.get('color', WHITE), (start_x, start_y), (end_x, end_y),
                                   width=max(4, skill.get('width', 40) // 5), duration=16)
            self.deal_line_damage(start_x, start_y, end_x, end_y, skill.get('width', 40),
                                  skill.get('damage', 80), skill.get('effects'))
            self.camera.shake(6)
            return True

        if behavior == 'line':
            start_x, start_y = self.player.rect.center
            dx, dy = world_x - start_x, world_y - start_y
            dist = math.hypot(dx, dy) or 1
            length = skill.get('range', 400)
            end_x = start_x + (dx / dist) * length
            end_y = start_y + (dy / dist) * length
            self.add_combat_effect('line', skill.get('color', WHITE), (start_x, start_y), (end_x, end_y),
                                   width=max(4, skill.get('width', 80) // 8), duration=18)
            self.deal_line_damage(start_x, start_y, end_x, end_y, skill.get('width', 80),
                                  skill.get('damage', 70), skill.get('effects'))
            self.camera.shake(4)
            return True

        if behavior == 'buff':
            self.player.blood_rage_timer = skill.get('duration', 480)
            self.player.damage_buff = skill.get('damage_bonus', 0.0)
            self.player.blood_rage_bonus = skill.get('lifesteal_bonus', 0.0)
            self.add_combat_effect('aura', skill.get('color', RED), self.player.rect.center,
                                   radius=90, width=6, duration=30)
            self.camera.shake(3)
            return True

        if behavior == 'buff_invincibility':
            self.player.guardian_aura_timer = skill.get('duration', 240)
            self.player.is_invincible = True
            self.add_combat_effect('aura', skill.get('color', YELLOW), self.player.rect.center,
                                   radius=110, width=7, duration=36)
            self.camera.shake(4)
            return True

        if behavior == 'dash':
            self.perform_dash(skill, world_x, world_y)
            return True

        if behavior == 'spawn_field':
            radius = skill.get('radius', 150)
            duration = skill.get('duration', 300)
            damage = skill.get('damage', 10)
            self.add_combat_effect('area', skill.get('color', PURPLE), (world_x, world_y),
                                   radius=radius, width=5, duration=26)
            self.spawn_poison_field(world_x, world_y, radius, duration, damage)
            return True

        if behavior == 'target_strike':
            self.perform_assassinate(skill)
            return True

        if behavior == 'spawn_clone':
            self.add_combat_effect('aura', skill.get('color', PURPLE), self.player.rect.center,
                                   radius=75, width=4, duration=20)
            self.spawn_shadow_clones(skill.get('count', 1))
            return True

        if behavior == 'radial_projectiles':
            self.launch_radial_projectiles(skill)
            return True

        if behavior == 'heal':
            heal_amount = skill.get('heal_amount', 60)
            self.player.hp = min(self.player.max_hp, self.player.hp + heal_amount)
            regen = skill.get('regen', 0)
            if regen:
                self.player.hp = min(self.player.max_hp, self.player.hp + regen)
            self.add_combat_effect('heal', skill.get('color', GREEN), self.player.rect.center,
                                   radius=85, width=5, duration=30)
            self.camera.shake(2)
            return True

        return False

    def fire_projectile(self, skill, target_x, target_y, force_basic=False):
        projectile_skill = dict(skill)
        projectile_skill['effects'] = dict(skill.get('effects', {}))
        if force_basic:
            basic_damage = {
                'cyber_mage': 24,
                'mech_ranger': 18,
                'bio_berserker': 32,
                'shadow_assassin': 27,
                'holy_knight': 22,
            }
            projectile_skill.update({
                'type': 'basic_shot',
                'visual_id': 'basic_' + self.player.char_type,
                'damage': basic_damage.get(self.player.char_type, 22),
                'speed': 19,
                'life': 70,
                'effects': {},
                'multi_count': 1,
                'spread': 6,
                'homing': False,
                'pierce': False,
            })
        dx = target_x - self.player.rect.centerx
        dy = target_y - self.player.rect.centery
        aim_dist = math.hypot(dx, dy) or 1
        muzzle_end = (
            self.player.rect.centerx + dx / aim_dist * 44,
            self.player.rect.centery + dy / aim_dist * 44,
        )
        self.add_combat_effect('muzzle', projectile_skill.get('color', self.player.color),
                               self.player.rect.center, muzzle_end, width=4 if force_basic else 6,
                               duration=8 if force_basic else 12)
        if projectile_skill.get('homing'):
            target = self.get_nearest_enemy()
            if target:
                projectile_skill['target_enemy'] = target

        multi_count = max(1, projectile_skill.get('multi_count', 1))
        spread = projectile_skill.get('spread', 12)
        if multi_count > 1:
            dx = target_x - self.player.rect.centerx
            dy = target_y - self.player.rect.centery
            base_angle = math.atan2(dy, dx)
            angle_step = math.radians(spread)
            start_angle = base_angle - angle_step * (multi_count - 1) / 2
            distance = math.hypot(dx, dy) or 1
            for i in range(multi_count):
                angle = start_angle + i * angle_step
                new_x = self.player.rect.centerx + math.cos(angle) * distance
                new_y = self.player.rect.centery + math.sin(angle) * distance
                config = dict(projectile_skill)
                self.projectiles.append(Projectile(
                    self.player.rect.centerx,
                    self.player.rect.centery,
                    new_x, new_y,
                    config,
                    self.player.char_type
                ))
        else:
            self.projectiles.append(Projectile(
                self.player.rect.centerx,
                self.player.rect.centery,
                target_x, target_y,
                projectile_skill,
                self.player.char_type
            ))
        if self.player.char_type == "mech_ranger" and force_basic and multi_count == 1:
            angle_offset = math.radians(random.uniform(-5, 5))
            dx = target_x - self.player.rect.centerx
            dy = target_y - self.player.rect.centery
            distance = math.hypot(dx, dy) or 1
            new_dx = math.cos(math.atan2(dy, dx) + angle_offset) * distance
            new_dy = math.sin(math.atan2(dy, dx) + angle_offset) * distance
            new_target_x = self.player.rect.centerx + new_dx
            new_target_y = self.player.rect.centery + new_dy
            config = dict(projectile_skill)
            self.projectiles.append(Projectile(
                self.player.rect.centerx,
                self.player.rect.centery,
                new_target_x, new_target_y,
                config,
                self.player.char_type
            ))

    def get_nearest_enemy(self):
        alive_enemies = [e for e in self.enemies if e.alive]
        if not alive_enemies:
            return None
        return min(alive_enemies, key=lambda e: math.hypot(e.rect.centerx - self.player.rect.centerx,
                                                          e.rect.centery - self.player.rect.centery))

    def add_combat_effect(self, kind, color, start, end=None, radius=0, width=4, duration=18):
        self.combat_effects.append({
            'kind': kind,
            'color': color[:3],
            'start': (float(start[0]), float(start[1])),
            'end': (float(end[0]), float(end[1])) if end else None,
            'radius': float(radius),
            'width': int(width),
            'life': int(duration),
            'max_life': int(duration),
        })
        self.combat_effects = self.combat_effects[-80:]

    def update_combat_effects(self):
        for effect in self.combat_effects:
            effect['life'] -= 1
        self.combat_effects = [effect for effect in self.combat_effects if effect['life'] > 0]

    def draw_combat_effects(self):
        if not self.combat_effects:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for effect in self.combat_effects:
            life_ratio = effect['life'] / max(1, effect['max_life'])
            progress = 1.0 - life_ratio
            alpha = max(20, int(230 * life_ratio))
            color = (*effect['color'], alpha)
            sx, sy = self.camera.apply(*effect['start'])
            start = (int(sx), int(sy))
            kind = effect['kind']

            if kind in ('beam', 'line', 'dash', 'muzzle') and effect['end']:
                ex, ey = self.camera.apply(*effect['end'])
                end = (int(ex), int(ey))
                width = max(1, int(effect['width'] * life_ratio))
                if kind == 'beam':
                    pygame.draw.line(overlay, (*effect['color'], max(20, alpha // 3)), start, end, width + 18)
                    pygame.draw.line(overlay, color, start, end, width + 8)
                    pygame.draw.line(overlay, (255, 255, 255, alpha), start, end, max(2, width))
                elif kind == 'dash':
                    pygame.draw.line(overlay, color, start, end, width + 8)
                    pygame.draw.line(overlay, (255, 255, 255, alpha), start, end, max(1, width // 2))
                elif kind == 'muzzle':
                    pygame.draw.line(overlay, color, start, end, width + 3)
                    pygame.draw.circle(overlay, (255, 255, 255, alpha), start, max(2, width + 1))
                else:
                    pygame.draw.line(overlay, color, start, end, width + 4)
                    for step in (0.2, 0.45, 0.7):
                        px = int(start[0] + (end[0] - start[0]) * step)
                        py = int(start[1] + (end[1] - start[1]) * step)
                        pygame.draw.circle(overlay, (255, 255, 255, alpha), (px, py), max(1, width // 2))
            elif kind in ('area', 'aura', 'heal'):
                radius = max(4, int(effect['radius'] * (0.35 + progress * 0.65)))
                pygame.draw.circle(overlay, color, start, radius, max(2, effect['width']))
                pygame.draw.circle(overlay, (*effect['color'], max(15, alpha // 3)), start, max(3, radius - 8), 2)
                if kind == 'heal':
                    pygame.draw.line(overlay, (255, 255, 255, alpha), (start[0], start[1] - 13), (start[0], start[1] + 13), 4)
                    pygame.draw.line(overlay, (255, 255, 255, alpha), (start[0] - 13, start[1]), (start[0] + 13, start[1]), 4)
            else:  # hit / wall impact
                radius = max(3, int(8 + progress * 18))
                pygame.draw.circle(overlay, color, start, radius, 2)
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    inner = (start[0] + int(math.cos(rad) * 4), start[1] + int(math.sin(rad) * 4))
                    outer = (start[0] + int(math.cos(rad) * radius), start[1] + int(math.sin(rad) * radius))
                    pygame.draw.line(overlay, color, inner, outer, 2)
        self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_ADD)

    def rect_hits_wall(self, rect):
        left = int(rect.left // TILE_SIZE)
        right = int((rect.right - 1) // TILE_SIZE)
        top = int(rect.top // TILE_SIZE)
        bottom = int((rect.bottom - 1) // TILE_SIZE)
        for tile_y in range(top, bottom + 1):
            for tile_x in range(left, right + 1):
                if tile_x < 0 or tile_y < 0 or tile_x >= self.map_w or tile_y >= self.map_h:
                    return True
                if self.tiles[tile_y][tile_x] == 1:
                    return True
        return False

    def deal_area_damage(self, cx, cy, radius, damage, effects=None):
        for enemy in self.enemies:
            if enemy.alive:
                dist = math.hypot(enemy.rect.centerx - cx, enemy.rect.centery - cy)
                if dist <= radius:
                    self.apply_damage_to_enemy(enemy, damage, effects)

    def deal_line_damage(self, start_x, start_y, end_x, end_y, width, damage, effects=None):
        for enemy in self.enemies:
            if enemy.alive:
                d = self._distance_point_to_segment(enemy.rect.centerx, enemy.rect.centery,
                                                    start_x, start_y, end_x, end_y)
                if d <= width:
                    self.apply_damage_to_enemy(enemy, damage, effects)

    def _distance_point_to_segment(self, px, py, x1, y1, x2, y2):
        line_mag = math.hypot(x2 - x1, y2 - y1)
        if line_mag == 0:
            return math.hypot(px - x1, py - y1)
        u = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_mag ** 2)))
        ix = x1 + u * (x2 - x1)
        iy = y1 + u * (y2 - y1)
        return math.hypot(px - ix, py - iy)

    def apply_damage_to_enemy(self, enemy, damage, effects=None):
        if not enemy.alive:
            return
        dmg_bonus = 1.0 + getattr(self.player, 'damage_buff', 0.0)
        final_damage = int(damage * dmg_bonus)
        enemy.take_damage(final_damage)
        self.add_combat_effect('hit', getattr(enemy, 'color', WHITE), enemy.rect.center,
                               radius=24, width=3, duration=11)
        if self.player.char_type == "bio_berserker":
            lifesteal = self.player.apply_vampirism(final_damage)
            bonus = getattr(self.player, 'blood_rage_bonus', 0.0)
            lifesteal += int(final_damage * bonus)
            if lifesteal > 0:
                self.player.hp = min(self.player.max_hp, self.player.hp + lifesteal)
        if effects:
            for effect_name, data in effects.items():
                if effect_name == 'area':
                    self.deal_area_damage(enemy.rect.centerx, enemy.rect.centery,
                                          data.get('radius', 60), data.get('damage', 10))
                elif effect_name == 'heal_player':
                    self.player.hp = min(self.player.max_hp, self.player.hp + data.get('amount', 10))
                else:
                    self.apply_status_to_enemy(enemy, effect_name, data)

    def apply_status_to_enemy(self, enemy, effect_name, data):
        if effect_name == 'burn':
            enemy.burn_timer = data.get('duration', 120)
            enemy.burn_damage = data.get('damage', 4)
        elif effect_name == 'freeze':
            enemy.frozen_timer = data.get('duration', 60)
        elif effect_name == 'slow':
            enemy.slow_timer = data.get('duration', 60)
            enemy.slow_factor = min(enemy.slow_factor, data.get('factor', 0.6))
        elif effect_name == 'stun':
            enemy.stun_timer = data.get('duration', 45)
        elif effect_name == 'poison':
            enemy.poison_timer = data.get('duration', 120)
            enemy.poison_damage = data.get('damage', 4)

    def perform_dash(self, skill, world_x, world_y):
        start_x, start_y = self.player.rect.center
        dx, dy = world_x - start_x, world_y - start_y
        dist = math.hypot(dx, dy) or 1
        dash_distance = skill.get('distance', 220)
        direction_x, direction_y = dx / dist, dy / dist
        end_x, end_y = start_x, start_y
        # Sweep the complete dash path in four-pixel increments. The last free
        # position becomes the destination, so dashes stop at walls.
        steps = max(1, int(math.ceil(dash_distance / 4.0)))
        for step in range(1, steps + 1):
            travel = min(dash_distance, step * 4.0)
            candidate = self.player.rect.copy()
            candidate.center = (
                int(start_x + direction_x * travel),
                int(start_y + direction_y * travel),
            )
            if self.rect_hits_wall(candidate):
                break
            end_x, end_y = candidate.center
        width = skill.get('width', 60)
        damage = skill.get('damage', 60)
        self.deal_line_damage(start_x, start_y, end_x, end_y, width, damage, skill.get('effects'))
        self.add_combat_effect('dash', skill.get('color', self.player.color), (start_x, start_y), (end_x, end_y),
                               width=max(5, width // 7), duration=18)
        self.player.rect.center = (int(end_x), int(end_y))
        self.camera.shake(4)

    def spawn_poison_field(self, x, y, radius, duration, damage):
        field = PoisonField(x, y, radius=radius, duration=duration, damage=damage)
        self.poison_fields.append(field)

    def launch_radial_projectiles(self, skill):
        count = skill.get('projectile_count', 8)
        distance = skill.get('range', 400)
        for i in range(count):
            angle = (2 * math.pi / count) * i
            target_x = self.player.rect.centerx + math.cos(angle) * distance
            target_y = self.player.rect.centery + math.sin(angle) * distance
            config = dict(skill)
            config['effects'] = dict(skill.get('effects', {}))
            self.projectiles.append(Projectile(
                self.player.rect.centerx,
                self.player.rect.centery,
                target_x, target_y,
                config,
                self.player.char_type
            ))

    def spawn_shadow_clones(self, count):
        for i in range(count):
            offset = (i - (count - 1) / 2) * 60
            clone = Decoy(self.player.rect.centerx + offset, self.player.rect.centery)
            clone.life += 90
            self.decoys.append(clone)

    def perform_assassinate(self, skill):
        target = self.get_nearest_enemy()
        if not target:
            return
        start = self.player.rect.center
        damage = skill.get('damage', 150)
        self.apply_damage_to_enemy(target, damage, skill.get('effects'))
        destination = start
        for offset_x, offset_y in ((36, -36), (-36, -36), (36, 36), (-36, 36), (0, -52), (0, 52)):
            candidate = self.player.rect.copy()
            candidate.center = (target.rect.centerx + offset_x, target.rect.centery + offset_y)
            if not self.rect_hits_wall(candidate):
                destination = candidate.center
                break
        self.add_combat_effect('dash', skill.get('color', PURPLE), start, target.rect.center,
                               width=7, duration=15)
        self.player.rect.center = destination
        self.camera.shake(6)

    def update(self):
        for message in self.feedback_messages:
            message['timer'] -= 1
        self.feedback_messages = [message for message in self.feedback_messages if message['timer'] > 0]

        # 技能选择或商店激活时，暂停游戏逻辑更新（但敌人和玩家都不更新）
        if self.state == "GAME" and not self.game_paused and not self.skill_selection_active and not self.skill_editor_active:
            # 根据游戏速度更新
            update_count = int(self.game_speed) if self.game_speed >= 1.0 else 1
            for _ in range(update_count):
                self.game_time += 1
                self.update_combat_effects()
                # 商店激活时，不更新玩家（保持位置不变，但需要清理拖尾）
                if not self.shop_active:
                    self.player.update(self.tiles, self.particles)
                    self.camera.update(self.player)
                else:
                    # 商店激活时，只清理玩家的移动状态，不更新位置
                    # 清除移动状态，避免拖尾继续生成
                    if hasattr(self.player, 'move_up'):
                        self.player.move_up = False
                        self.player.move_down = False
                        self.player.move_left = False
                        self.player.move_right = False
                        self.player.sprint = False
                        self.player.vx = 0
                        self.player.vy = 0
                    # 不更新相机，保持商店打开时的视角
            
            # 只执行一次游戏逻辑更新（避免重复）
            # 自动攻击系统
            if 'auto_attack' in self.player.passive_skills and self.player.passive_skills['auto_attack']['level'] > 0:
                level = self.player.passive_skills['auto_attack']['level']
                attack_count = self.player.available_passives['auto_attack']['count'][level]
                attack_cd = self.player.available_passives['auto_attack']['cd'][level]

                if self.player.auto_attack_timer >= attack_cd:
                    self.player.auto_attack_timer = 0
                    # 找到最近的敌人
                    nearest_enemies = sorted(
                        [e for e in self.enemies if e.alive],
                        key=lambda e: math.hypot(
                            e.rect.centerx - self.player.rect.centerx,
                            e.rect.centery - self.player.rect.centery
                        )
                    )[:attack_count]

                    for enemy in nearest_enemies:
                        # 使用第一个技能作为自动攻击
                        skill = self.player.skills[0]
                        self.projectiles.append(Projectile(
                            self.player.rect.centerx,
                            self.player.rect.centery,
                            enemy.rect.centerx,
                            enemy.rect.centery,
                            skill,
                            self.player.char_type
                        ))

                        # 机械游侠的自动攻击也有双发效果
                        if self.player.char_type == "mech_ranger":
                            # 创建第二颗子弹，稍微偏离角度
                            angle_offset = random.uniform(-5, 5)
                            rad_offset = math.radians(angle_offset)
                            dx, dy = enemy.rect.centerx - self.player.rect.centerx, enemy.rect.centery - self.player.rect.centery
                            distance = math.sqrt(dx * dx + dy * dy)
                            if distance > 0:
                                new_dx = math.cos(math.atan2(dy, dx) + rad_offset) * distance
                                new_dy = math.sin(math.atan2(dy, dx) + rad_offset) * distance
                                new_enemy_x = self.player.rect.centerx + new_dx
                                new_enemy_y = self.player.rect.centery + new_dy

                                self.projectiles.append(Projectile(
                                    self.player.rect.centerx,
                                    self.player.rect.centery,
                                    new_enemy_x, new_enemy_y,
                                    skill,
                                    self.player.char_type
                                ))
            
            # 被动技能自动触发系统（后5个技能 + 弹性防护罩）
            passive_skill_types = ['chain_lightning', 'freeze_mine', 'boomerang', 'decoy', 'gravity_field', 'bounce_shield']
            for skill_type in passive_skill_types:
                if skill_type in self.player.passive_skills and self.player.passive_skills[skill_type]['level'] > 0:
                    level = self.player.passive_skills[skill_type]['level']
                    skill_data = self.player.available_passives[skill_type]
                    cd = skill_data['cd'][level]
                    
                    # 更新CD
                    if self.player.passive_skill_cooldowns[skill_type] > 0:
                        self.player.passive_skill_cooldowns[skill_type] -= 1
                    else:
                        # CD结束，自动触发技能
                        # 对于弹性防护罩，如果已经在激活状态，不重复触发
                        if skill_type == 'bounce_shield' and self.player.bounce_shield_active:
                            continue
                        
                        # 有敌人时才触发（弹性防护罩除外）
                        should_trigger = True
                        if skill_type != 'bounce_shield':
                            if len([e for e in self.enemies if e.alive]) == 0:
                                should_trigger = False
                        
                        if should_trigger:
                            mx, my = pygame.mouse.get_pos()
                            world_x = mx + self.camera.offset.x
                            world_y = my + self.camera.offset.y
                            
                            # 创建技能数据
                            skill_info = {
                                'type': skill_type,
                                'color': skill_data['color'],
                                'icon': skill_data['icon'],
                                'damage_multiplier': 1.0
                            }
                            
                            if skill_type == 'chain_lightning':
                                # 连锁闪电 - 向最近的敌人发射
                                nearest = min([e for e in self.enemies if e.alive],
                                             key=lambda e: math.hypot(e.rect.centerx - self.player.rect.centerx,
                                                                      e.rect.centery - self.player.rect.centery),
                                             default=None)
                                if nearest:
                                    p = Projectile(self.player.rect.centerx, self.player.rect.centery,
                                                   nearest.rect.centerx, nearest.rect.centery,
                                                   skill_info, self.player.char_type)
                                    p.damage = skill_data['damage'][level]
                                    p.bounce_count = 4
                                    p.hit_enemies = []
                                    self.projectiles.append(p)
                            elif skill_type == 'freeze_mine':
                                # 冰冻地雷 - 在玩家前方放置
                                dx = world_x - self.player.rect.centerx
                                dy = world_y - self.player.rect.centery
                                dist = math.hypot(dx, dy)
                                if dist > 0:
                                    mx = self.player.rect.centerx + (dx / dist) * 100
                                    my = self.player.rect.centery + (dy / dist) * 100
                                    mine = Mine(mx, my)
                                    mine.damage = skill_data['damage'][level]
                                    self.mines.append(mine)
                            elif skill_type == 'boomerang':
                                # 吸血飞刃 - 向鼠标方向投掷
                                p = Projectile(self.player.rect.centerx, self.player.rect.centery,
                                               world_x, world_y, skill_info, self.player.char_type)
                                p.damage = skill_data['damage'][level]
                                p.max_distance = 300
                                p.traveled_distance = 0
                                p.start_x, p.start_y = self.player.rect.centerx, self.player.rect.centery
                                p.returning = False
                                self.projectiles.append(p)
                            elif skill_type == 'decoy':
                                # 分身幻影 - 在玩家位置创建
                                decoy = Decoy(self.player.rect.centerx, self.player.rect.centery)
                                self.decoys.append(decoy)
                            elif skill_type == 'gravity_field':
                                # 重力领域 - 在最近的敌人位置自动创建
                                nearest = min([e for e in self.enemies if e.alive],
                                             key=lambda e: math.hypot(e.rect.centerx - self.player.rect.centerx,
                                                                      e.rect.centery - self.player.rect.centery),
                                             default=None)
                                if nearest:
                                    field = GravityField(nearest.rect.centerx, nearest.rect.centery)
                                    field.life = 300  # 5秒（60fps * 5）
                                    field.max_life = 300
                                    self.gravity_fields.append(field)
                            elif skill_type == 'bounce_shield':
                                # 弹性防护罩 - 激活防护罩
                                self.player.bounce_shield_active = True
                                self.player.bounce_shield_timer = skill_data['duration'][level]
                            
                            # 重置CD
                            self.player.passive_skill_cooldowns[skill_type] = cd

            # 环绕光球碰撞检测
            if 'orbs' in self.player.passive_skills and self.player.passive_skills['orbs']['level'] > 0:
                for orb in self.player.orbs:
                    orb_x = self.player.rect.centerx + math.cos(math.radians(orb['angle'] + self.player.orb_angle)) * \
                            orb['radius']
                    orb_y = self.player.rect.centery + math.sin(math.radians(orb['angle'] + self.player.orb_angle)) * \
                            orb['radius']
                    orb_rect = pygame.Rect(orb_x - 6, orb_y - 6, 12, 12)

                    for e in self.enemies:
                        if e.alive and orb_rect.colliderect(e.rect):
                            # 伤害不是特别高，但升级后增加 - 基础伤害较低
                            orb_level = self.player.passive_skills['orbs']['level']
                            damage = 5 + orb_level * 1.5  # 基础5点，每级+1.5
                            e.take_damage(int(damage))
                            self.particles.append(Particle(e.rect.centerx, e.rect.centery, YELLOW, 'spark'))
                            # 光球不会消失，使用短暂冷却避免过度伤害
                            if 'hit_cooldown' not in orb or orb['hit_cooldown'] == 0:
                                orb['hit_cooldown'] = 30  # 30帧冷却时间
                                break  # 每个光球一次只攻击一个敌人

            # 更新地雷
            for mine in self.mines[:]:
                if not mine.update(self.enemies):
                    # 地雷爆炸，添加粒子效果
                    for _ in range(20):
                        self.particles.append(Particle(mine.x, mine.y, NEON_BLUE, 'spark'))
                    self.mines.remove(mine)
            
            # 更新分身
            for decoy in self.decoys[:]:
                if not decoy.update():
                    # 分身消失时爆炸
                    decoy.explode(self.enemies)
                    for _ in range(30):
                        self.particles.append(Particle(decoy.x, decoy.y, PURPLE, 'spark'))
                    self.decoys.remove(decoy)
            
            # 更新重力场
            for field in self.gravity_fields[:]:
                if not field.update():
                    self.gravity_fields.remove(field)
            # 更新毒雾场
            for field in self.poison_fields[:]:
                if not field.update(self.enemies):
                    self.poison_fields.remove(field)
            
            # 更新弹性防护罩
            if self.player.bounce_shield_active:
                self.player.bounce_shield_timer -= 1
                if self.player.bounce_shield_timer <= 0:
                    self.player.bounce_shield_active = False
            
            # 更新敌人 - 优先攻击分身（商店激活时暂停敌人更新）
            elite_killed = False
            for e in self.enemies[:]:
                if e.alive:
                    # 商店激活时，敌人不移动和更新
                    if not self.shop_active:
                        # 如果有分身，优先攻击分身
                        target = self.player
                        if self.decoys:
                            # 找到最近的分身
                            nearest_decoy = min(self.decoys, 
                                              key=lambda d: math.hypot(e.rect.centerx - d.x, e.rect.centery - d.y))
                            decoy_dist = math.hypot(e.rect.centerx - nearest_decoy.x, e.rect.centery - nearest_decoy.y)
                            player_dist = math.hypot(e.rect.centerx - self.player.rect.centerx, 
                                                    e.rect.centery - self.player.rect.centery)
                            if decoy_dist < player_dist + 50:  # 分身优先吸引范围
                                # 创建一个临时目标对象用于AI
                                class TempTarget:
                                    def __init__(self, x, y):
                                        self.rect = pygame.Rect(x - 16, y - 16, 32, 32)
                                        self.vx = 0
                                        self.vy = 0
                                target = TempTarget(nearest_decoy.x, nearest_decoy.y)
                        
                        e.ai_move(target, self.tiles)
                        
                        # 应用重力场效果
                        for field in self.gravity_fields:
                            field.apply_gravity(e)
                        
                        # 弹性防护罩：弹开敌人
                        if self.player.bounce_shield_active and e.rect.colliderect(self.player.rect):
                            # 计算弹开方向
                            dx = e.rect.centerx - self.player.rect.centerx
                            dy = e.rect.centery - self.player.rect.centery
                            dist = math.hypot(dx, dy)
                            if dist > 0:
                                # 弹开力度
                                bounce_strength = 15
                                e.vx += (dx / dist) * bounce_strength
                                e.vy += (dy / dist) * bounce_strength
                                # 限制速度
                                max_speed = e.speed * 3
                                speed = math.hypot(e.vx, e.vy)
                                if speed > max_speed:
                                    e.vx = (e.vx / speed) * max_speed
                                    e.vy = (e.vy / speed) * max_speed
                                # 粒子效果
                                for _ in range(5):
                                    self.particles.append(Particle(e.rect.centerx, e.rect.centery, (100, 200, 255), 'spark'))
                        
                        # 碰撞伤害（只有防护罩不激活时才受伤）
                        if e.rect.colliderect(self.player.rect) and self.player.hurt_timer == 0 and not self.player.bounce_shield_active:
                            old_hp = self.player.hp
                            self.player.take_damage(e.damage)
                            # 只有实际受到伤害时才播放效果
                            if self.player.hp < old_hp:
                                self.camera.shake(10)
                                self.particles.append(Particle(self.player.rect.centerx, self.player.rect.centery, RED))
                else:
                    # 检查是否是精英怪（金色Boss）
                    if e.is_elite:
                        elite_killed = True
                        self.total_elite_kills += 1
                        # 检查是否是金色Boss
                        if hasattr(e, 'is_golden_boss') and e.is_golden_boss:
                            self.golden_bosses_killed += 1
                            self.player.coins += 40 * self.current_map
                        # 精英怪掉落随机道具
                        if random.random() < 0.7:  # 70%概率掉落道具
                            item_types = ['health', 'mana', 'damage_boost', 'defense_boost', 'exp_orb']
                            item_type = random.choice(item_types)
                            self.items.append(Item(e.rect.centerx, e.rect.centery, item_type))
                    # 检查是否是Boss
                    if e.kind == 'dragon':
                        self.boss_defeated = True
                        self.player.coins += 180 * self.current_map
                        self.player.exp += 120 * self.current_map
                        boss_chest = TreasureChest(e.rect.centerx, e.rect.centery)
                        boss_chest.reward_type = 'boss'
                        self.treasure_chests.append(boss_chest)
                        self.gain_upgrade_charge(2, "Boss 击破")
                        self.add_feedback("Boss 已击破，战利品宝箱已出现", UI_ACCENT, 240)
                    
                    self.enemies.remove(e)
                    self.total_kills += 1  # 增加总击杀数
                    self.enemies_killed_this_map += 1  # 当前地图击杀数
                    # 增加波次内击杀计数
                    if self.wave_mode and self.wave_active and getattr(e, 'is_wave_enemy', False):
                        self.wave_enemies_killed += 1
                    
                    # 检查是否所有敌人（包括Boss）都被击败
                    if len([e for e in self.enemies if e.alive]) == 0:
                        if not self.wave_mode and self.enemies_killed_this_map >= self.map_enemy_count * 0.8:
                            # 击败80%的敌人后生成Boss
                            if not self.boss_spawned:
                                # 在随机房间生成Boss
                                if len(self.rooms) > 1:
                                    boss_room = random.choice(self.rooms[1:])
                                    boss_x = (boss_room.x + boss_room.width // 2) * TILE_SIZE
                                    boss_y = (boss_room.y + boss_room.height // 2) * TILE_SIZE
                                    boss = Enemy(boss_x, boss_y, 'dragon', False)
                                    # Boss根据地图增强 - 血量更厚
                                    map_multiplier = 1.0 + (self.current_map - 1) * 0.5
                                    boss.hp = int(boss.hp * map_multiplier * 5)  # Boss血量大幅增加
                                    boss.max_hp = boss.hp
                                    boss.damage = int(boss.damage * map_multiplier * 2)  # Boss伤害更高
                                    boss.speed *= 1.2  # Boss速度稍快
                                    self.enemies.append(boss)
                                    self.boss_spawned = True
                                    self.map_enemy_count += 1
                    # 基础掉落
                    base_coins = random.randint(5, 15) * (2 if e.is_elite else 1)
                    base_exp = 20 * (2 if e.is_elite else 1)

                    # 应用探索天赋加成
                    coins = int(base_coins * (1 + getattr(self.player, 'coin_bonus', 0.0)))
                    exp = int(base_exp * (1 + getattr(self.player, 'exp_bonus', 0.0)))

                    self.player.coins += coins
                    self.player.exp += exp

            # 精英怪提供构筑能量，积满后才触发技能选择。
            if elite_killed:
                self.gain_upgrade_charge(1, "精英击破")

            # 更新道具
            for item in self.items[:]:
                # 使用update方法的返回值来判断道具是否过期
                if not item.update():
                    self.items.remove(item)
                # 检查玩家与道具的碰撞
                elif item.rect.colliderect(self.player.rect):
                    result = item.apply_effect(self.player)
                    if result:
                        self.add_feedback(result, UI_PRIMARY, 140)
                    self.items.remove(item)
            
            # 更新宝箱
            for chest in self.treasure_chests[:]:
                chest.update()
                # 检查玩家与宝箱的碰撞
                if chest.rect.colliderect(self.player.rect) and not chest.opened:
                    chest.opened = True
                    reward_type = getattr(chest, 'reward_type', 'coins')
                    if reward_type == 'recovery':
                        heal = int(self.player.max_hp * 0.35)
                        self.player.hp = min(self.player.max_hp, self.player.hp + heal)
                        reward_text = f"恢复生命 {heal}"
                    elif reward_type == 'charge':
                        self.gain_upgrade_charge(1, "探索宝箱")
                        reward_text = "获得 1 点构筑能量"
                    elif reward_type == 'boss':
                        reward = 220 * self.current_map
                        self.player.coins += reward
                        self.gain_upgrade_charge(1, "Boss 战利品")
                        reward_text = f"Boss 战利品：金币 {reward}"
                    else:
                        reward = 80 * self.current_map
                        self.player.coins += reward
                        reward_text = f"获得金币 {reward}"
                    self.chests_opened += 1
                    self.shop_available = True
                    self.add_feedback(f"宝箱开启：{reward_text}", UI_ACCENT, 210)
                    self.treasure_chests.remove(chest)

            # 检查成就
            self.check_achievements()

            # 波次系统逻辑
            if self.wave_mode:
                # 波间倒计时是真实的探索和喘息时间。
                if not self.wave_active and self.wave_enemies_count > 0:
                    if self.wave_cooldown > 0:
                        self.wave_cooldown -= 1
                    else:
                        self.spawn_wave_enemies()

                # 检查是否完成当前波次
                if self.wave_active and self.wave_enemies_killed >= self.wave_enemies_count:
                    # 波次完成奖励
                    wave_reward = 35 + 15 * self.current_wave
                    self.player.coins += wave_reward
                    self.player.exp += 20 + 10 * self.current_wave
                    self.add_feedback(f"波次完成：金币 +{wave_reward}", GREEN, 180)
                    if self.current_wave % 2 == 0 and not self.boss_wave:
                        self.gain_upgrade_charge(1, "连续作战")

                    # 添加完成特效
                    for _ in range(30):
                        self.particles.append(Particle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, GREEN, 'spark'))

                    # 准备下一波
                    self.prepare_next_wave(immediate=False)
            else:
                # 原始的怪物生成系统 - 随时间生成
                self.enemy_spawn_timer += 1
                if self.enemy_spawn_timer >= self.enemy_spawn_interval:
                    self.enemy_spawn_timer = 0
                    # 生成速度随时间加快（进一步提升刷怪频率）
                    # 随时间逐渐接近15帧一次刷怪（≈0.25秒），初始间隔也降低
                    self.enemy_spawn_interval = max(15, 180 - int(self.game_time / 600))
                    self.spawn_regular_enemies()

                # 当所有怪物被清理后，立即刷新下一波
                if not self.enemies and not self.shop_active and not self.skill_selection_active:
                    self.spawn_regular_enemies()

            # 更新投射物
            for p in self.projectiles[:]:
                if not p.update():
                    self.projectiles.remove(p)
                    continue

                # Projectiles now collide with dungeon geometry instead of
                # flying through walls and damaging unseen enemies.
                if self.rect_hits_wall(p.rect):
                    self.add_combat_effect('wall', p.color, p.rect.center, radius=20, width=3, duration=10)
                    self.projectiles.remove(p)
                    continue

                # 击中判定 - 增强特效
                hit_enemy = None
                for e in self.enemies:
                    if e.alive and p.rect.colliderect(e.rect):
                        # 连锁闪电特殊处理
                        if p.skill_type == 'chain_lightning':
                            if not hasattr(p, 'hit_enemies'):
                                p.hit_enemies = []
                            if e not in p.hit_enemies:  # 只对未击中的敌人造成伤害
                                self.apply_damage_to_enemy(e, p.damage, p.effects)
                                p.hit_enemies.append(e)
                                hit_enemy = e
                                
                                # 如果还有弹跳次数，寻找下一个敌人
                                if hasattr(p, 'bounce_count') and p.bounce_count > 0 and len(p.hit_enemies) < len(self.enemies):
                                    p.bounce_count -= 1
                                    # 寻找最近的未击中敌人
                                    nearest = None
                                    min_dist = float('inf')
                                    for other_e in self.enemies:
                                        if other_e.alive and other_e not in p.hit_enemies:
                                            dist = math.hypot(other_e.rect.centerx - e.rect.centerx, 
                                                            other_e.rect.centery - e.rect.centery)
                                            if dist < min_dist and dist < 300:  # 最大弹跳距离
                                                min_dist = dist
                                                nearest = other_e
                                    if nearest:
                                        # 调整方向到下一个敌人
                                        angle = math.atan2(nearest.rect.centery - e.rect.centery,
                                                         nearest.rect.centerx - e.rect.centerx)
                                        speed = math.hypot(p.vx, p.vy)
                                        p.vx = math.cos(angle) * speed
                                        p.vy = math.sin(angle) * speed
                                        p.life = 60  # 重置生命周期
                                else:
                                    p.life = 0  # 弹跳结束，销毁子弹
                        # 回旋飞刃特殊处理（返回时也能造成伤害）
                        elif p.skill_type == 'boomerang':
                            if not hasattr(p, 'hit_enemies'):
                                p.hit_enemies = []
                            # 飞出和返回都能造成伤害，但同一敌人有冷却
                            if e not in p.hit_enemies or (p.returning and hasattr(p, 'return_hit_cooldown') and p.return_hit_cooldown <= 0):
                                self.apply_damage_to_enemy(e, p.damage, p.effects)
                                if not hasattr(p, 'hit_enemies'):
                                    p.hit_enemies = []
                                if e not in p.hit_enemies:
                                    p.hit_enemies.append(e)
                                if p.returning:
                                    if not hasattr(p, 'return_hit_cooldown'):
                                        p.return_hit_cooldown = 10
                                    else:
                                        p.return_hit_cooldown = 10
                                hit_enemy = e
                        else:
                            # 普通技能
                            self.apply_damage_to_enemy(e, p.damage, p.effects)
                            hit_enemy = e
                            
                            # 爆炸特效
                            skill_type = p.skill_type
                            if skill_type == 'fire':
                                # 火焰爆炸
                                for _ in range(15):
                                    self.particles.append(Particle(
                                        e.rect.centerx, e.rect.centery,
                                        p.color, 'spark'
                                    ))
                            elif skill_type == 'ice':
                                # 冰霜爆炸
                                for _ in range(10):
                                    self.particles.append(Particle(
                                        e.rect.centerx, e.rect.centery,
                                        p.color, 'energy'
                                    ))
                            elif skill_type == 'lightning':
                                # 闪电链效果
                                for _ in range(20):
                                    self.particles.append(Particle(
                                        e.rect.centerx, e.rect.centery,
                                        p.color, 'spark'
                                    ))
                            else:
                                for _ in range(8):
                                    self.particles.append(Particle(
                                        e.rect.centerx, e.rect.centery,
                                        p.color, 'spark'
                                    ))
                            
                            self.camera.shake(3)
                            if p.skill_type not in ['chain_lightning', 'boomerang']:
                                if p.pierce:
                                    p.targets_hit += 1
                                    if p.targets_hit >= p.pierce_limit:
                                        p.life = 0
                                        break
                                else:
                                    p.life = 0  # 销毁子弹
                                    break
                
                # 连锁闪电和回旋飞刃的特效
                if hit_enemy:
                    skill_type = p.skill_type
                    if skill_type == 'chain_lightning':
                        for _ in range(15):
                            self.particles.append(Particle(
                                hit_enemy.rect.centerx, hit_enemy.rect.centery,
                                p.color, 'spark'
                            ))
                        self.camera.shake(2)
                    elif skill_type == 'boomerang':
                        for _ in range(8):
                            self.particles.append(Particle(
                                hit_enemy.rect.centerx, hit_enemy.rect.centery,
                                p.color, 'spark'
                            ))
                        # 回旋飞刃击中时给玩家回血
                        heal = int(p.damage * 0.1)
                        if heal > 0:
                            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
                
                # 回旋飞刃返回时的冷却更新
                if p.skill_type == 'boomerang' and hasattr(p, 'return_hit_cooldown'):
                    if p.return_hit_cooldown > 0:
                        p.return_hit_cooldown -= 1

            # 粒子
            self.particles = [p for p in self.particles if p.update()]

            if not self.player.alive:
                self.state = "GAMEOVER"

    def show_skill_selection(self):
        """显示技能选择界面"""
        # 保存玩家位置（如果还没有保存）
        if self.player_pos_before_skill_selection is None:
            self.player_pos_before_skill_selection = (self.player.rect.x, self.player.rect.y)
        self.skill_selection_active = True
        self.skill_selection_index = 0

        # 统计已拥有的被动技能数量（排除0级的）
        owned_skills_count = sum(1 for skill_id in self.player.passive_skills 
                                if self.player.passive_skills[skill_id]['level'] > 0)
        
        # 获取可升级的技能和未获得的技能
        available_skills = []
        upgradeable_skills = []

        # 如果已经拥有5个或更多技能，只显示已拥有的可升级技能
        if owned_skills_count >= 5:
            # 只显示已拥有的可升级技能
            for skill_id in self.player.passive_skills:
                if self.player.passive_skills[skill_id]['level'] > 0:
                    skill_data = self.player.available_passives.get(skill_id)
                    if skill_data and self.player.passive_skills[skill_id]['level'] < skill_data['max_level']:
                        upgradeable_skills.append(skill_id)
        else:
            # 正常显示所有可升级和新技能
            for skill_id, skill_data in self.player.available_passives.items():
                if skill_id in self.player.passive_skills:
                    # 已拥有，检查是否可以升级
                    if self.player.passive_skills[skill_id]['level'] < skill_data['max_level']:
                        upgradeable_skills.append(skill_id)
                else:
                    # 未拥有
                    available_skills.append(skill_id)

        # 如果没有任何可供选择/升级的技能，直接关闭界面避免卡住
        if not upgradeable_skills and (owned_skills_count >= 5 or not available_skills):
            self.skill_selection_active = False
            self.skill_selection_options = []
            if self.player_pos_before_skill_selection:
                self.player.rect.x, self.player.rect.y = self.player_pos_before_skill_selection
                self.player_pos_before_skill_selection = None
            return

        # 创建选择选项（最多3个）
        self.skill_selection_options = []
        random.shuffle(upgradeable_skills)

        # 优先显示可升级的技能
        for skill_id in upgradeable_skills[:2]:
            skill_data = self.player.available_passives[skill_id]
            current_level = self.player.passive_skills[skill_id]['level']
            self.skill_selection_options.append({
                'type': 'upgrade',
                'skill_id': skill_id,
                'name': skill_data['name'],
                'icon': skill_data['icon'],
                'color': skill_data['color'],
                'desc': f"升级到 Lv.{current_level + 1}",
                'current_level': current_level
            })

        # 如果还没有5个技能，添加新技能选项 - 随机抽取
        if owned_skills_count < 5:
            random.shuffle(available_skills)  # 随机打乱
            remaining_slots = 5 - owned_skills_count
            for skill_id in available_skills[:min(3 - len(self.skill_selection_options), remaining_slots)]:
                skill_data = self.player.available_passives[skill_id]
                self.skill_selection_options.append({
                    'type': 'new',
                    'skill_id': skill_id,
                    'name': skill_data['name'],
                    'icon': skill_data['icon'],
                    'color': skill_data['color'],
                    'desc': skill_data['desc']
                })

        # 如果选项不足3个，用升级选项填充
        while len(self.skill_selection_options) < 3 and len(upgradeable_skills) > len(
                [o for o in self.skill_selection_options if o['type'] == 'upgrade']):
            remaining = [s for s in upgradeable_skills if
                         s not in [o['skill_id'] for o in self.skill_selection_options if o['type'] == 'upgrade']]
            if remaining:
                skill_id = remaining[0]
                skill_data = self.player.available_passives[skill_id]
                current_level = self.player.passive_skills[skill_id]['level']
                self.skill_selection_options.append({
                    'type': 'upgrade',
                    'skill_id': skill_id,
                    'name': skill_data['name'],
                    'icon': skill_data['icon'],
                    'color': skill_data['color'],
                    'desc': f"升级到 Lv.{current_level + 1}",
                    'current_level': current_level
                })
            else:
                break

    def spawn_regular_enemies(self):
        """普通模式下刷怪（支持无限刷怪）"""
        if not hasattr(self, 'player') or not self.player:
            return

        enemy_types = ['goblin', 'slime', 'bat', 'skeleton', 'demon', 'ghost', 'spider']

        # 普通模式同样采用缓慢爬坡，避免一次刷出十几只怪。
        base_spawn = 1 + int(self.game_time / 1800)
        map_bonus = max(0, self.current_map - 1)
        spawn_count = min(6, base_spawn + map_bonus)

        for _ in range(spawn_count):
            # 在玩家周围随机位置生成
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(400, 600)
            spawn_x = self.player.rect.centerx + math.cos(angle) * distance
            spawn_y = self.player.rect.centery + math.sin(angle) * distance

            # 确保生成在地图内
            spawn_x = max(TILE_SIZE, min(self.map_w * TILE_SIZE - TILE_SIZE, spawn_x))
            spawn_y = max(TILE_SIZE, min(self.map_h * TILE_SIZE - TILE_SIZE, spawn_y))

            # 检查是否在墙内
            grid_x = int(spawn_x // TILE_SIZE)
            grid_y = int(spawn_y // TILE_SIZE)
            if 0 <= grid_y < len(self.tiles) and 0 <= grid_x < len(self.tiles[0]):
                if self.tiles[grid_y][grid_x] == 0:  # 地板
                    kind = random.choice(enemy_types)
                    # 随时间增加精英怪概率，随地图增加
                    base_elite_chance = 0.02 + self.game_time / 72000
                    map_elite_bonus = (self.current_map - 1) * 0.025
                    elite_chance = min(0.16, base_elite_chance + map_elite_bonus)
                    is_elite = random.random() < elite_chance
                    enemy = Enemy(spawn_x, spawn_y, kind, is_elite)
                    # 根据地图增强
                    map_multiplier = 1.0 + (self.current_map - 1) * 0.5
                    enemy.hp = int(enemy.hp * map_multiplier)
                    enemy.max_hp = enemy.hp
                    enemy.damage = int(enemy.damage * map_multiplier)
                    self.enemies.append(enemy)

    def select_skill(self, index):
        """选择技能"""
        if 0 <= index < len(self.skill_selection_options):
            option = self.skill_selection_options[index]
            skill_id = option['skill_id']
            
            # 检查是否已经拥有5个技能
            owned_skills_count = sum(1 for sid in self.player.passive_skills 
                                    if self.player.passive_skills[sid]['level'] > 0)
            
            if option['type'] == 'new':
                # 如果已经拥有5个技能，不允许添加新技能
                if owned_skills_count >= 5:
                    return
                # 获得新技能
                self.player.passive_skills[skill_id] = {
                    'level': 1,
                    'name': option['name']
                }
            elif option['type'] == 'upgrade':
                # 升级技能
                self.player.passive_skills[skill_id]['level'] += 1

            self.upgrade_charge = max(0, self.upgrade_charge - self.upgrade_charge_required)
            self.skill_choices_made += 1
            self.upgrade_charge_required = min(5, 2 + self.skill_choices_made // 2)
            self.add_feedback(f"构筑完成：{option['name']}", option['color'], 180)

            self.skill_selection_active = False
            self.skill_selection_options = []
            # 恢复玩家位置
            if self.player_pos_before_skill_selection:
                self.player.rect.x, self.player.rect.y = self.player_pos_before_skill_selection
                self.player_pos_before_skill_selection = None
    
    def adjust_skill_level(self, change):
        """调整选中技能的等级（后门功能）"""
        if not hasattr(self, 'player') or not self.player:
            return
        
        skill_list = list(self.player.available_passives.keys())
        if 0 <= self.skill_editor_selected_index < len(skill_list):
            skill_id = skill_list[self.skill_editor_selected_index]
            skill_data = self.player.available_passives[skill_id]
            max_level = skill_data['max_level']
            
            # 如果技能不存在，先创建它
            if skill_id not in self.player.passive_skills:
                self.player.passive_skills[skill_id] = {
                    'level': 0,
                    'name': skill_data['name']
                }
            
            # 调整等级
            current_level = self.player.passive_skills[skill_id]['level']
            new_level = max(0, min(max_level, current_level + change))
            self.player.passive_skills[skill_id]['level'] = new_level
            
            # 如果等级为0，可以选择移除技能（可选）
            if new_level == 0 and change < 0:
                # 保留技能但等级为0，或者完全移除
                # del self.player.passive_skills[skill_id]
                pass

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == "GAME":
            self.draw_world()
            self.draw_ui()

            # 显示新解锁的成就提示
            self.draw_new_achievements()

            if self.skill_selection_active:
                self.draw_skill_selection()
            
            # 技能编辑器界面（后门）
            if self.skill_editor_active:
                self.draw_skill_editor()
            
            # 商店界面
            if self.shop_active:
                self.draw_shop()
            
            # 暂停界面
            if self.game_paused:
                self.draw_pause_menu()
        elif self.state == "MENU":
            self.draw_menu()
        elif self.state == "GAMEOVER":
            self.draw_gameover()
        elif self.state == "CHAR_SELECT":
            self.draw_char_selection()
        elif self.state == "TALENT_SELECT":
            self.draw_talent_selection()
        elif self.state == "MANUAL":
            self.draw_manual()

        pygame.display.flip()

    def draw_new_achievements(self):
        """显示新解锁的成就提示"""
        # 简单处理：保留最新的2个成就提示
        if len(self.new_achievements) > 2:
            self.new_achievements = self.new_achievements[-2:]

        # 绘制成就提示
        for i, achievement in enumerate(self.new_achievements):
            # 成就提示背景
            surf = pygame.Surface((350, 80), pygame.SRCALPHA)
            surf.fill((30, 30, 50, 230))
            pygame.draw.rect(surf, YELLOW, (0, 0, 350, 80), 2)

            # 成就名称
            name_text = FONT_M.render(achievement['name'], True, YELLOW)
            surf.blit(name_text, (20, 15))

            # 成就描述和奖励
            desc_text = FONT_S.render(f"{achievement['desc']} +{achievement['reward']}金币", True, WHITE)
            surf.blit(desc_text, (20, 45))

            # 绘制到屏幕右侧，向上堆叠
            x = SCREEN_WIDTH - 370
            y = 100 + i * 100
            self.screen.blit(surf, (x, y))

            # 添加发光效果
            aura_surf = pygame.Surface((370, 100), pygame.SRCALPHA)
            pygame.draw.rect(aura_surf, (*YELLOW[:3], 30), (0, 0, 370, 100), 4)
            self.screen.blit(aura_surf, (x - 10, y - 10))

    def draw_skill_selection(self):
        """绘制技能选择界面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((3, 5, 10, 225))
        self.screen.blit(overlay, (0, 0))

        title = FONT_TITLE.render("选择构筑升级", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 116)))
        charge = FONT_XS.render(
            f"构筑能量已充满  ·  第 {self.skill_choices_made + 1} 次选择",
            True,
            UI_ACCENT,
        )
        self.screen.blit(charge, charge.get_rect(center=(SCREEN_WIDTH // 2, 168)))

        option_width = 330
        option_height = 300
        spacing = 36
        total_width = len(self.skill_selection_options) * option_width + (
                    len(self.skill_selection_options) - 1) * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2

        for i, option in enumerate(self.skill_selection_options):
            x = start_x + i * (option_width + spacing)
            y = 245
            selected = i == self.skill_selection_index
            option_rect = pygame.Rect(x, y, option_width, option_height)
            draw_panel(self.screen, option_rect, option['color'], selected)

            draw_keycap(self.screen, str(i + 1), (x + 34, y + 32), selected)
            status = "升级" if option['type'] == 'upgrade' else "新技能"
            status_text = FONT_XS.render(status.upper(), True, option['color'])
            self.screen.blit(status_text, (option_rect.right - status_text.get_width() - 20, y + 24))

            icon_surf = VisualUtils.create_skill_icon(option['skill_id'], option['color'], 72)
            self.screen.blit(icon_surf, icon_surf.get_rect(center=(option_rect.centerx, y + 96)))

            name_text = FONT_CARD.render(option['name'], True, option['color'])
            name_rect = name_text.get_rect(center=(option_rect.centerx, y + 160))
            self.screen.blit(name_text, name_rect)

            draw_wrapped_text(
                self.screen,
                option['desc'],
                FONT_XS,
                WHITE,
                (x + 28, y + 198, option_width - 56, 60),
                line_gap=7,
                max_lines=3,
            )

            if option['type'] == 'upgrade':
                level_text = FONT_XS.render(
                    f"Lv.{option['current_level']}  →  Lv.{option['current_level'] + 1}",
                    True,
                    UI_MUTED,
                )
                level_rect = level_text.get_rect(center=(option_rect.centerx, option_rect.bottom - 28))
                self.screen.blit(level_text, level_rect)

        hint = FONT_XS.render("← / → 或 A / D 切换    SPACE / ENTER 确认    1-3 快速选择", True, UI_MUTED)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, 640))
        self.screen.blit(hint, hint_rect)
    
    def draw_skill_editor(self):
        """绘制技能编辑器界面（后门功能）"""
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        
        # 标题
        title = FONT_L.render("技能编辑器 (后门)", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)
        
        if not hasattr(self, 'player') or not self.player:
            error_text = FONT_M.render("玩家未初始化", True, RED)
            error_rect = error_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(error_text, error_rect)
            return
        
        # 技能列表
        skill_list = list(self.player.available_passives.keys())
        panel_width = 600
        panel_height = 400
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = 150
        
        # 背景面板
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, UI_BG, panel_surf.get_rect(), border_radius=15)
        pygame.draw.rect(panel_surf, YELLOW, panel_surf.get_rect(), 3, border_radius=15)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        
        # 绘制每个技能
        item_height = 60
        start_y = panel_y + 20
        visible_count = min(6, len(skill_list))  # 最多显示6个
        
        for i in range(visible_count):
            if i >= len(skill_list):
                break
            
            skill_id = skill_list[i]
            skill_data = self.player.available_passives[skill_id]
            current_level = 0
            if skill_id in self.player.passive_skills:
                current_level = self.player.passive_skills[skill_id]['level']
            max_level = skill_data['max_level']
            
            y_pos = start_y + i * item_height
            is_selected = (i == self.skill_editor_selected_index)
            
            # 选中高亮
            if is_selected:
                highlight = pygame.Surface((panel_width - 40, item_height - 10), pygame.SRCALPHA)
                highlight.fill((*YELLOW[:3], 50))
                self.screen.blit(highlight, (panel_x + 20, y_pos))
            
            # 技能图标
            icon_surf = VisualUtils.create_skill_icon(skill_id, skill_data['color'], 40)
            self.screen.blit(icon_surf, (panel_x + 30, y_pos + 10))
            
            # 技能名称和等级
            name_text = FONT_M.render(skill_data['name'], True, skill_data['color'])
            self.screen.blit(name_text, (panel_x + 80, y_pos + 10))
            
            level_text = FONT_S.render(f"Lv.{current_level}/{max_level}", True, WHITE)
            self.screen.blit(level_text, (panel_x + 80, y_pos + 35))
            
            # 等级调整按钮
            if is_selected:
                # 减少按钮
                if current_level > 0:
                    minus_text = FONT_M.render("◄", True, RED)
                    self.screen.blit(minus_text, (panel_x + panel_width - 150, y_pos + 15))
                
                # 增加按钮
                if current_level < max_level:
                    plus_text = FONT_M.render("►", True, GREEN)
                    self.screen.blit(plus_text, (panel_x + panel_width - 100, y_pos + 15))
        
        # 操作提示
        hint_y = panel_y + panel_height + 20
        hint1 = FONT_S.render("↑↓ 选择技能  ◄► 调整等级  ESC 关闭", True, WHITE)
        hint1_rect = hint1.get_rect(center=(SCREEN_WIDTH // 2, hint_y))
        self.screen.blit(hint1, hint1_rect)
        
        hint2 = FONT_S.render("Ctrl+K 打开/关闭编辑器", True, GRAY)
        hint2_rect = hint2.get_rect(center=(SCREEN_WIDTH // 2, hint_y + 30))
        self.screen.blit(hint2, hint2_rect)
    
    def buy_shop_item(self, index):
        """购买商店物品"""
        if not hasattr(self, 'player') or not self.player:
            return
        
        shop_items = [
            {'name': '增加血量上限 +20', 'price': 1000, 'type': 'max_hp', 'value': 20},
            {'name': '增加防御力 +5', 'price': 1000, 'type': 'defense', 'value': 5},
            {'name': '减少技能1 CD -0.1秒', 'price': 1500, 'type': 'skill_cd', 'skill_idx': 0, 'value': -6},
            {'name': '减少技能2 CD -0.1秒', 'price': 1500, 'type': 'skill_cd', 'skill_idx': 1, 'value': -6},
            {'name': '减少技能3 CD -0.1秒', 'price': 1500, 'type': 'skill_cd', 'skill_idx': 2, 'value': -6},
            {'name': '减少技能4 CD -0.1秒', 'price': 1500, 'type': 'skill_cd', 'skill_idx': 3, 'value': -6},
            {'name': '减少技能5 CD -0.1秒', 'price': 1500, 'type': 'skill_cd', 'skill_idx': 4, 'value': -6},
            {'name': '技能1多发 +1', 'price': 2000, 'type': 'skill_multi', 'skill_idx': 0, 'value': 1},
        ]
        
        if 0 <= index < len(shop_items):
            item = shop_items[index]
            # 检查是否已购买（每关只能购买一次）
            item_key = f"{item['type']}_{item.get('skill_idx', '')}"
            if item_key in self.shop_upgrades:
                return  # 本关已购买，不能重复购买
            
            if self.player.coins >= item['price']:
                self.player.coins -= item['price']
                self.shop_upgrades[item_key] = True  # 记录购买
                
                if item['type'] == 'max_hp':
                    self.player.max_hp += item['value']
                    self.player.hp += item['value']
                elif item['type'] == 'defense':
                    if not hasattr(self.player, 'defense'):
                        self.player.defense = 0
                    self.player.defense += item['value']
                elif item['type'] == 'skill_cd':
                    skill_idx = item['skill_idx']
                    if skill_idx < len(self.player.skills):
                        # CD减少0.1秒（6帧，因为60fps）
                        self.player.skills[skill_idx]['cd'] = max(5, self.player.skills[skill_idx]['cd'] + item['value'])
                elif item['type'] == 'skill_multi':
                    skill_idx = item['skill_idx']
                    if skill_idx < len(self.player.skills):
                        if 'multi_count' not in self.player.skills[skill_idx]:
                            self.player.skills[skill_idx]['multi_count'] = 1
                        self.player.skills[skill_idx]['multi_count'] += item['value']
    
    def draw_shop(self):
        """绘制商店界面"""
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # 商店标题
        title = FONT_L.render(f"商店 - 地图 {self.current_map}", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # 金币显示
        coin_text = FONT_M.render(f"金币: {self.player.coins}", True, YELLOW)
        coin_rect = coin_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(coin_text, coin_rect)
        
        # 商店物品列表（必须与buy_shop_item中的列表一致）
        shop_items = [
            {'name': '增加血量上限 +20', 'price': 1000, 'icon': '❤️'},
            {'name': '增加防御力 +5', 'price': 1000, 'icon': '🛡️'},
            {'name': '减少技能1 CD -0.1秒', 'price': 1500, 'icon': '⚡'},
            {'name': '减少技能2 CD -0.1秒', 'price': 1500, 'icon': '⚡'},
            {'name': '减少技能3 CD -0.1秒', 'price': 1500, 'icon': '⚡'},
            {'name': '减少技能4 CD -0.1秒', 'price': 1500, 'icon': '⚡'},
            {'name': '减少技能5 CD -0.1秒', 'price': 1500, 'icon': '⚡'},
            {'name': '技能1多发 +1', 'price': 2000, 'icon': '🎯'},
        ]
        
        start_y = 150
        item_height = 60
        panel_width = 600
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        
        for i, item in enumerate(shop_items):
            y_pos = start_y + i * item_height
            is_selected = (i == self.shop_selected_index)
            
            # 选中高亮
            if is_selected:
                highlight = pygame.Surface((panel_width, item_height - 10), pygame.SRCALPHA)
                highlight.fill((*YELLOW[:3], 50))
                self.screen.blit(highlight, (panel_x, y_pos))
            
            # 物品图标
            icon_surf = VisualUtils.create_skill_icon(item.get('type', item['name']), YELLOW, 40)
            self.screen.blit(icon_surf, (panel_x + 20, y_pos + 10))
            
            # 物品名称
            name_text = FONT_M.render(item['name'], True, WHITE)
            self.screen.blit(name_text, (panel_x + 80, y_pos + 10))
            
            # 价格和购买状态
            item_key = f"{shop_items[i].get('type', '')}_{shop_items[i].get('skill_idx', '')}"
            if item_key in self.shop_upgrades:
                price_text = FONT_S.render("已购买", True, GREEN)
            else:
                price_text = FONT_S.render(f"{item['price']} 金币", True, YELLOW if self.player.coins >= item['price'] else RED)
            self.screen.blit(price_text, (panel_x + panel_width - 150, y_pos + 20))
        
        # 操作提示
        hint_y = start_y + len(shop_items) * item_height + 20
        hint1 = FONT_S.render("↑↓ 选择  ENTER 购买  B或ESC 关闭商店", True, WHITE)
        hint1_rect = hint1.get_rect(center=(SCREEN_WIDTH // 2, hint_y))
        self.screen.blit(hint1, hint1_rect)
        
        hint2 = FONT_S.render("Ctrl+T 切换2倍速  |  每关商店提升会重置", True, GRAY)
        hint2_rect = hint2.get_rect(center=(SCREEN_WIDTH // 2, hint_y + 30))
        self.screen.blit(hint2, hint2_rect)
        
        # 如果商店可用但未激活，显示提示
        if self.shop_available and not self.shop_active:
            shop_hint = FONT_S.render("按 [B] 打开商店", True, YELLOW)
            shop_hint_rect = shop_hint.get_rect(center=(SCREEN_WIDTH // 2, hint_y + 60))
            self.screen.blit(shop_hint, shop_hint_rect)
    
    def draw_manual(self):
        """绘制游戏说明书"""
        self.screen.fill((8, 10, 25))
        title = FONT_L.render("游戏说明书", True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 60)))
        
        hint = FONT_S.render("↑↓滚动 · 空格/ESC返回菜单", True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 110)))
        
        lines_per_page = 22
        y = 150
        for i in range(lines_per_page):
            idx = self.manual_scroll + i
            if idx >= len(self.manual_lines):
                break
            text = self.manual_lines[idx]
            line_surface = FONT_S.render(text, True, WHITE)
            self.screen.blit(line_surface, (80, y))
            y += 24
        
        if len(self.manual_lines) > lines_per_page:
            progress = (self.manual_scroll + lines_per_page) / len(self.manual_lines)
            bar_height = 200
            scroll_rect = pygame.Rect(SCREEN_WIDTH - 60, 150, 4, bar_height)
            pygame.draw.rect(self.screen, (60, 60, 80), scroll_rect)
            thumb_height = max(20, int(bar_height * (lines_per_page / len(self.manual_lines))))
            thumb_y = 150 + int((bar_height - thumb_height) * progress)
            pygame.draw.rect(self.screen, YELLOW, (SCREEN_WIDTH - 62, thumb_y, 8, thumb_height))
    
    def _load_manual_text(self):
        manual_path = os.path.join(os.path.dirname(__file__), "游戏使用说明书.txt")
        if os.path.exists(manual_path):
            try:
                with open(manual_path, "r", encoding="utf-8") as f:
                    return [line.strip('\n') for line in f]
            except Exception:
                pass
        return ["未找到说明书文件 (游戏使用说明书.txt)", "请确认文件与游戏在同一目录"]
    
    def draw_pause_menu(self):
        """绘制暂停菜单"""
        if not hasattr(self, 'player') or not self.player:
            return
            
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # 暂停标题
        title = FONT_L.render("游戏暂停", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # 显示所有主动技能
        y_offset = 120
        skill_title = FONT_M.render("主动技能:", True, WHITE)
        self.screen.blit(skill_title, (50, y_offset))
        y_offset += 40
        
        for skill in self.player.skills:
            skill_y = y_offset
            # 技能图标
            icon_surf = VisualUtils.create_skill_icon(skill.get('visual_id', skill.get('type', skill.get('name'))), skill.get('color', WHITE), 30)
            self.screen.blit(icon_surf, (60, skill_y))
            
            # 技能名称和按键
            name_text = FONT_S.render(f"[{skill.get('key', '?')}] {skill.get('name', '未知')}", True, skill.get('color', WHITE))
            self.screen.blit(name_text, (100, skill_y + 5))
            
            # 冷却时间
            cd_text = FONT_S.render(f"CD: {skill.get('cd', 0) // 60}s", True, GRAY)
            self.screen.blit(cd_text, (300, skill_y + 5))
            
            y_offset += 35
        
        # 显示所有被动技能
        y_offset += 20
        passive_title = FONT_M.render("被动技能:", True, WHITE)
        self.screen.blit(passive_title, (50, y_offset))
        y_offset += 40
        
        for skill_id, skill_data in self.player.available_passives.items():
            if skill_id in self.player.passive_skills:
                level = self.player.passive_skills[skill_id]['level']
                if level > 0:
                    skill_y = y_offset
                    # 技能图标
                    icon_surf = VisualUtils.create_skill_icon(skill_id, skill_data.get('color', WHITE), 30)
                    self.screen.blit(icon_surf, (60, skill_y))
                    
                    # 技能名称和等级
                    name_text = FONT_S.render(f"{skill_data.get('name', '未知')} Lv.{level}", True, skill_data.get('color', WHITE))
                    self.screen.blit(name_text, (100, skill_y + 5))
                    
                    # 技能描述
                    desc_text = FONT_S.render(skill_data.get('desc', ''), True, GRAY)
                    self.screen.blit(desc_text, (300, skill_y + 5))
                    
                    y_offset += 35
        
        # 提示文字
        hint = FONT_M.render("按 [P] 继续游戏", True, WHITE)
        hint.set_alpha(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 255)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        self.screen.blit(hint, hint_rect)
        
        # 2倍速提示
        speed_hint = FONT_S.render("Ctrl+T 切换2倍速", True, GRAY)
        speed_hint_rect = speed_hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(speed_hint, speed_hint_rect)

    def draw_world(self):
        # 绘制可视范围内的地图
        start_col = max(0, int(self.camera.offset.x // TILE_SIZE))
        end_col = min(self.map_w, int((self.camera.offset.x + SCREEN_WIDTH) // TILE_SIZE) + 1)
        start_row = max(0, int(self.camera.offset.y // TILE_SIZE))
        end_row = min(self.map_h, int((self.camera.offset.y + SCREEN_HEIGHT) // TILE_SIZE) + 1)

        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                x, y = c * TILE_SIZE, r * TILE_SIZE
                pos = self.camera.apply(x, y)

                if self.tiles[r][c] == 1:  # 墙
                    pygame.draw.rect(self.screen, DARK_GRAY, (*pos, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(self.screen, (60, 60, 70), (*pos, TILE_SIZE, TILE_SIZE), 1)
                else:  # 地板
                    color = (25, 25, 35) if (r + c) % 2 == 0 else (20, 20, 30)
                    pygame.draw.rect(self.screen, color, (*pos, TILE_SIZE, TILE_SIZE))

        # 实体绘制
        for e in self.enemies: e.draw(self.screen, self.camera)
        for item in self.items: item.draw(self.screen, self.camera)  # 绘制道具
        for chest in self.treasure_chests: chest.draw(self.screen, self.camera)  # 绘制宝箱
        for mine in self.mines: mine.draw(self.screen, self.camera)  # 绘制地雷
        for field in self.gravity_fields: field.draw(self.screen, self.camera)  # 绘制重力场
        for field in self.poison_fields: field.draw(self.screen, self.camera)  # 绘制毒雾场
        self.player.draw(self.screen, self.camera)
        for decoy in self.decoys: decoy.draw(self.screen, self.camera)  # 绘制分身
        for p in self.projectiles: p.draw(self.screen, self.camera)
        self.draw_combat_effects()
        for p in self.particles: p.draw(self.screen, self.camera)

    def draw_ui(self):
        # 安全检查
        if not hasattr(self, 'player') or not self.player:
            return
            
        # 波次信息显示（如果启用了波次模式）
        if self.wave_mode:
            panel_w, panel_h = 320, 78
            x = (SCREEN_WIDTH - panel_w) // 2
            y = 16
            draw_panel(self.screen, (x, y, panel_w, panel_h), UI_PRIMARY, False)

            wave_text = FONT_CARD.render(f"波次 {self.current_wave}", True, UI_ACCENT)
            self.screen.blit(wave_text, (x + 18, y + 11))
            kill_text = FONT_XS.render(f"{self.wave_enemies_killed} / {self.wave_enemies_count}", True, WHITE)
            self.screen.blit(kill_text, (x + panel_w - kill_text.get_width() - 18, y + 17))

            bar_bg = pygame.Rect(x + 18, y + 50, panel_w - 36, 10)
            pygame.draw.rect(self.screen, (35, 43, 58), bar_bg, border_radius=5)

            # 进度条填充
            if self.wave_enemies_count > 0:
                progress = min(1.0, self.wave_enemies_killed / self.wave_enemies_count)
                bar_width = int((panel_w - 36) * progress)
                bar_fill = pygame.Rect(x + 18, y + 50, bar_width, 10)
                pygame.draw.rect(self.screen, GREEN, bar_fill, border_radius=5)

            # 倒计时
            if self.wave_cooldown > 0:
                countdown_text = FONT_XS.render(f"下一波 {int(self.wave_cooldown / 60)}s", True, ORANGE)
                self.screen.blit(countdown_text, countdown_text.get_rect(center=(x + panel_w // 2, y + 68)))

        # 1. 技能栏 - 调整为10个技能（分两行显示）
        if not hasattr(self, 'player') or not self.player or not hasattr(self.player, 'skills'):
            return
        
        num_skills = min(len(self.player.skills), 10)  # 最多显示10个
        skills_per_row = max(1, num_skills)
        num_rows = 1
        
        # 计算面板尺寸 - 确保适配屏幕
        panel_w = min(940, max(420, num_skills * 86 + 36))
        skill_item_w = (panel_w - 36) // skills_per_row
        item_height = 72
        panel_h = 106
        
        # 计算位置 - 确保在屏幕底部可见区域
        x = (SCREEN_WIDTH - panel_w) // 2
        y = SCREEN_HEIGHT - panel_h - 14

        # 背景板
        if num_skills:
            draw_panel(self.screen, (x, y, panel_w, panel_h), UI_PRIMARY, False)

        # 绘制每个技能 - 增强版UI（支持10个技能，分两行）
        for i, skill in enumerate(self.player.skills):
            if i >= 10:  # 最多显示10个技能
                break
                
            row = i // skills_per_row
            col = i % skills_per_row
            bx = x + 18 + col * skill_item_w + (skill_item_w - 50) // 2
            by = y + 24 + row * item_height
            
            # 确保技能图标在屏幕内
            if by < 0 or by > SCREEN_HEIGHT - 50:
                continue  # 跳过超出屏幕的技能

            # 技能图标框 - 带发光效果
            color = skill.get('color', WHITE)
            if skill.get('cur', 0) > 0:
                color = GRAY  # 冷却中变灰
                # 冷却遮罩
                s_cd = pygame.Surface((50, 50), pygame.SRCALPHA)
                cd_ratio = min(1.0, skill['cur'] / max(1, skill.get('cd', 1)))
                fill_height = int(50 * cd_ratio)
                pygame.draw.rect(s_cd, (0, 0, 0, 150), (0, 0, 50, fill_height))
                self.screen.blit(s_cd, (bx, by))
            else:
                # 可用时发光
                glow_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.01 + i))
                alpha = int(80 * pulse)
                color_tuple = color[:3] if isinstance(color, (list, tuple)) and len(color) >= 3 else WHITE[:3]
                pygame.draw.circle(glow_surf, (*color_tuple, alpha), (30, 30), 25)
                self.screen.blit(glow_surf, (bx - 5, by - 5))

            pygame.draw.rect(self.screen, DARK_GRAY, (bx, by, 50, 50), border_radius=8)
            color_tuple = color[:3] if isinstance(color, (list, tuple)) and len(color) >= 3 else WHITE[:3]
            pygame.draw.rect(self.screen, color_tuple, (bx, by, 50, 50), 3, border_radius=8)

            # 技能名称和按键
            skill_name = skill.get('name', '未知')
            skill_key = skill.get('key', str(i + 1))
            skill_icon = skill.get('icon', '•')
            
            try:
                name_surf = FONT_XS.render(skill_name, True, color_tuple)
                key_surf = FONT_XS.render(str(skill_key), True, WHITE)
                
                # 技能图标
                icon_surf = VisualUtils.create_skill_icon(skill.get('visual_id', skill.get('type', skill_name)), color_tuple, 40)
                self.screen.blit(icon_surf, (bx + 5, by + 5))

                # 文字信息 - 调整位置确保在屏幕内
                key_y = max(5, by - 18)  # 按键显示在上方，确保不超出屏幕
                if key_y < SCREEN_HEIGHT:  # 确保在屏幕内
                    self.screen.blit(key_surf, (bx + 2, key_y))
                
                # 名称显示在图标下方，确保不超出面板和屏幕
                name_y = by + 56
                if name_y < SCREEN_HEIGHT - 5 and name_y < y + panel_h:  # 确保在面板和屏幕内
                    # 限制名称宽度，避免超出
                    max_name_width = skill_item_w - 10
                    if name_surf.get_width() > max_name_width:
                        # 如果名称太长，使用省略号
                        name_surf = FONT_XS.render(skill_name[:5] + '...', True, color_tuple)
                    self.screen.blit(name_surf, name_surf.get_rect(center=(bx + 25, name_y + 8)))

                # 冷却数字
                if skill.get('cur', 0) > 0:
                    cd_seconds = max(1, int(skill['cur'] / 60) + 1)
                    cd_txt = FONT_M.render(str(cd_seconds), True, WHITE)
                    self.screen.blit(cd_txt, (bx + 15, by + 10))
            except Exception as e:
                # 如果渲染出错，跳过这个技能但不崩溃
                print(f"技能渲染错误: {e}")
                continue

        # 2. 左上角状态
        info_rect = pygame.Rect(14, 14, 284, 112)
        draw_panel(self.screen, info_rect, self.player.color, False)
        hp_label = FONT_XS.render("生命值", True, UI_MUTED)
        hp_value = FONT_XS.render(f"{max(0, int(self.player.hp))} / {int(self.player.max_hp)}", True, WHITE)
        self.screen.blit(hp_label, (info_rect.left + 16, info_rect.top + 13))
        self.screen.blit(hp_value, (info_rect.right - hp_value.get_width() - 16, info_rect.top + 13))

        hp_bg = pygame.Rect(info_rect.left + 16, info_rect.top + 41, info_rect.width - 32, 12)
        pygame.draw.rect(self.screen, (42, 47, 58), hp_bg, border_radius=6)
        hp_ratio = max(0.0, min(1.0, self.player.hp / max(1, self.player.max_hp)))
        hp_fill = pygame.Rect(hp_bg.x, hp_bg.y, int(hp_bg.width * hp_ratio), hp_bg.height)
        if hp_fill.width:
            pygame.draw.rect(self.screen, UI_DANGER, hp_fill, border_radius=6)

        coin_text = FONT_XS.render(f"金币  {self.player.coins}", True, UI_ACCENT)
        time_text = FONT_XS.render(f"时间  {int(self.game_time / 60)}s", True, WHITE)
        self.screen.blit(coin_text, (info_rect.left + 16, info_rect.top + 72))
        self.screen.blit(time_text, (info_rect.right - time_text.get_width() - 16, info_rect.top + 72))

        status_parts = []
        if hasattr(self.player, 'lives') and self.player.lives > 1:
            status_parts.append(f"生命 {self.player.lives}")
        if hasattr(self.player, 'is_invincible') and self.player.is_invincible:
            status_parts.append(f"无敌 {int(self.player.invincible_timer / 60)}s")
        if hasattr(self, 'game_speed') and self.game_speed > 1.0:
            status_parts.append(f"{self.game_speed}x")
        if status_parts:
            status_text = FONT_XS.render("  |  ".join(status_parts), True, UI_PRIMARY)
            self.screen.blit(status_text, (info_rect.left + 16, info_rect.bottom + 8))

        if hasattr(self, 'shop_available') and self.shop_available and not self.shop_active:
            shop_hint = FONT_XS.render("B  打开商店", True, UI_ACCENT)
            self.screen.blit(shop_hint, (info_rect.left + 16, info_rect.bottom + 34))

        charge_rect = pygame.Rect(14, 132, 284, 46)
        draw_panel(self.screen, charge_rect, UI_ACCENT, False)
        charge_label = FONT_XS.render("构筑能量", True, UI_MUTED)
        charge_value = FONT_XS.render(f"{self.upgrade_charge} / {self.upgrade_charge_required}", True, UI_ACCENT)
        self.screen.blit(charge_label, (charge_rect.left + 12, charge_rect.top + 6))
        self.screen.blit(charge_value, (charge_rect.right - charge_value.get_width() - 12, charge_rect.top + 6))
        charge_bg = pygame.Rect(charge_rect.left + 12, charge_rect.bottom - 12, charge_rect.width - 24, 5)
        pygame.draw.rect(self.screen, (45, 48, 58), charge_bg, border_radius=3)
        charge_ratio = min(1.0, self.upgrade_charge / max(1, self.upgrade_charge_required))
        pygame.draw.rect(self.screen, UI_ACCENT, (charge_bg.x, charge_bg.y, int(charge_bg.width * charge_ratio), 5), border_radius=3)

        # 3. 角色专属被动显示
        if self.player.character_passive:
            passive_rect = pygame.Rect(SCREEN_WIDTH - 258, 14, 244, 42)
            draw_panel(self.screen, passive_rect, self.player.color, True)
            name_text = FONT_XS.render(self.player.character_passive['name'], True, self.player.color)
            self.screen.blit(name_text, name_text.get_rect(center=passive_rect.center))

        # 4. 其他被动技能显示（右上角）
        if self.player.passive_skills:
            passive_y = 68
            for skill_id, skill_info in self.player.passive_skills.items():
                # 只显示存在于available_passives中的技能，避免KeyError
                if skill_id in self.player.available_passives:
                    skill_data = self.player.available_passives[skill_id]
                    level = skill_info['level']
                    defensive = any(token in skill_id for token in ('shield', 'health', 'defense', 'armor'))
                    icon_type = 'survival' if defensive else 'combat'
                    icon_surf = VisualUtils.create_talent_icon(icon_type, skill_data['color'], 30)
                    slot_rect = pygame.Rect(SCREEN_WIDTH - 112, passive_y, 98, 34)
                    draw_panel(self.screen, slot_rect, skill_data['color'], False)
                    self.screen.blit(icon_surf, (slot_rect.left + 6, slot_rect.top + 2))
                    level_text = FONT_XS.render(f"Lv.{level}", True, skill_data['color'])
                    self.screen.blit(level_text, (slot_rect.left + 42, slot_rect.top + 8))
                    passive_y += 40

        self.draw_objective_guidance()
        self.draw_feedback_messages()

    def draw_objective_guidance(self):
        boss = next((enemy for enemy in self.enemies if enemy.alive and enemy.behavior == 'boss'), None)
        objective_y = 106
        if boss:
            bar_rect = pygame.Rect(SCREEN_WIDTH // 2 - 280, objective_y, 560, 42)
            draw_panel(self.screen, bar_rect, UI_DANGER, True)
            label = FONT_XS.render("深渊龙王", True, UI_DANGER)
            value = FONT_XS.render(f"{int(boss.hp)} / {int(boss.max_hp)}", True, WHITE)
            self.screen.blit(label, (bar_rect.left + 14, bar_rect.top + 7))
            self.screen.blit(value, (bar_rect.right - value.get_width() - 14, bar_rect.top + 7))
            hp_bg = pygame.Rect(bar_rect.left + 14, bar_rect.bottom - 11, bar_rect.width - 28, 5)
            pygame.draw.rect(self.screen, (50, 38, 45), hp_bg, border_radius=3)
            ratio = max(0.0, min(1.0, boss.hp / max(1, boss.max_hp)))
            pygame.draw.rect(self.screen, UI_DANGER, (hp_bg.x, hp_bg.y, int(hp_bg.width * ratio), 5), border_radius=3)
            objective_y += 50

        nearest = None
        if self.treasure_chests:
            nearest = min(
                self.treasure_chests,
                key=lambda chest: math.hypot(chest.x - self.player.rect.centerx, chest.y - self.player.rect.centery),
            )

        if nearest:
            dx = nearest.x - self.player.rect.centerx
            dy = nearest.y - self.player.rect.centery
            distance = max(1, int(math.hypot(dx, dy) / TILE_SIZE))
            angle = math.atan2(dy, dx)
            arrow_center = (SCREEN_WIDTH // 2 - 176, objective_y + 21)
            tip = (arrow_center[0] + math.cos(angle) * 11, arrow_center[1] + math.sin(angle) * 11)
            left = (arrow_center[0] + math.cos(angle + 2.5) * 8, arrow_center[1] + math.sin(angle + 2.5) * 8)
            right = (arrow_center[0] + math.cos(angle - 2.5) * 8, arrow_center[1] + math.sin(angle - 2.5) * 8)
            guide_rect = pygame.Rect(SCREEN_WIDTH // 2 - 205, objective_y, 410, 42)
            draw_panel(self.screen, guide_rect, UI_PRIMARY, False)
            pygame.draw.polygon(self.screen, UI_PRIMARY, [tip, left, right])
            remaining = len(self.treasure_chests)
            guide = FONT_XS.render(f"探索目标：能量宝箱  {distance} 格  ·  剩余 {remaining}", True, WHITE)
            self.screen.blit(guide, (guide_rect.left + 50, guide_rect.top + 11))
        elif self.wave_cooldown > 0:
            guide_rect = pygame.Rect(SCREEN_WIDTH // 2 - 180, objective_y, 360, 42)
            draw_panel(self.screen, guide_rect, UI_PRIMARY, False)
            guide = FONT_XS.render("探索完成，准备迎接下一波", True, WHITE)
            self.screen.blit(guide, guide.get_rect(center=guide_rect.center))

    def draw_feedback_messages(self):
        y = 190
        for message in self.feedback_messages[-3:]:
            alpha = min(255, message['timer'] * 4)
            text = FONT_XS.render(message['text'], True, message['color'])
            text.set_alpha(alpha)
            rect = pygame.Rect(14, y, min(420, text.get_width() + 28), 34)
            draw_panel(self.screen, rect, message['color'], False)
            self.screen.blit(text, (rect.left + 14, rect.top + 8))
            y += 40

    def draw_menu(self):
        time = pygame.time.get_ticks() * 0.001
        draw_grid_background(self.screen, time)

        # Keep the original starfield and meteors, but lower their contrast so UI stays legible.
        for i in range(70):
            x = (time * 12 + i * 53.7) % SCREEN_WIDTH
            y = (time * 8 + i * 31.9) % SCREEN_HEIGHT
            brightness = int(70 + 70 * abs(math.sin(time * 1.4 + i * 0.17)))
            pygame.draw.circle(self.screen, (brightness, brightness, brightness + 18), (int(x), int(y)), 1)

        for i in range(3):
            meteor_x = (time * 76 + i * SCREEN_WIDTH / 3) % (SCREEN_WIDTH + 120)
            meteor_y = (time * 54 + i * 220) % SCREEN_HEIGHT
            meteor_color = [CYAN, PURPLE, NEON_BLUE][i]
            for j in range(4):
                trail_x = meteor_x - j * 18
                trail_y = meteor_y - j * 12
                alpha = 130 - j * 28
                if 0 <= trail_x <= SCREEN_WIDTH and 0 <= trail_y <= SCREEN_HEIGHT:
                    s = pygame.Surface((8, 8), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*meteor_color[:3], alpha), (4, 4), max(1, 3 - j // 2))
                    self.screen.blit(s, (int(trail_x), int(trail_y)))

        draw_corner_brackets(self.screen, (54, 50, SCREEN_WIDTH - 108, SCREEN_HEIGHT - 100), UI_PRIMARY, 34, 2)

        protocol = FONT_XS.render("ROGUELITE COMBAT PROTOCOL // ONLINE", True, UI_MUTED)
        self.screen.blit(protocol, protocol.get_rect(center=(SCREEN_WIDTH // 2, 205)))

        title = FONT_HERO.render("赛博地牢", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 300))
        glow = pygame.Surface((title_rect.width + 80, title_rect.height + 36), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*UI_PRIMARY[:3], 24), glow.get_rect(), border_radius=8)
        self.screen.blit(glow, glow.get_rect(center=title_rect.center))
        self.screen.blit(title, title_rect)
        pygame.draw.line(self.screen, UI_PRIMARY, (title_rect.left, title_rect.bottom + 12), (title_rect.right, title_rect.bottom + 12), 2)

        subtitle = FONT_CARD.render("CYBER DUNGEON", True, UI_PRIMARY)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 385)))

        pulse = (math.sin(time * 3) + 1) * 0.5
        start_rect = pygame.Rect(0, 0, 360, 66)
        start_rect.center = (SCREEN_WIDTH // 2, 650)
        draw_button(self.screen, start_rect, "开始游戏", FONT_M, True, pulse)
        draw_keycap(self.screen, "SPACE", (SCREEN_WIDTH // 2, 712), True)

        manual = FONT_XS.render("H  游戏说明", True, UI_MUTED)
        self.screen.blit(manual, manual.get_rect(center=(SCREEN_WIDTH // 2, 770)))

    def draw_gameover(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        txt = FONT_L.render("GAME OVER", True, RED)
        self.screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH // 2, 300)))

        restart = FONT_M.render("按 [空格] 重新选择角色", True, WHITE)
        self.screen.blit(restart, restart.get_rect(center=(SCREEN_WIDTH // 2, 400)))

        menu_text = FONT_M.render("按 [ESC] 返回主菜单", True, WHITE)
        menu_text_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(menu_text, menu_text_rect)

    def get_character_card_rect(self, index):
        return pygame.Rect(100 + index * 284, 220, 264, 440)

    def get_talent_card_rect(self, index):
        return pygame.Rect(290 + index * 350, 250, 320, 400)

    def draw_char_selection(self):
        time = pygame.time.get_ticks() * 0.001
        draw_grid_background(self.screen, time)
        draw_corner_brackets(self.screen, (48, 44, SCREEN_WIDTH - 96, SCREEN_HEIGHT - 88), UI_PRIMARY, 28, 2)

        title = FONT_TITLE.render("选择作战角色", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 90)))
        subtitle = FONT_XS.render("SELECT COMBAT FRAME // 1-5 快速选择", True, UI_MUTED)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 142)))

        for i, char in enumerate(self.char_options):
            box_rect = self.get_character_card_rect(i)
            selected = char['type'] == self.selected_char
            draw_panel(self.screen, box_rect, char['color'], selected)

            index_text = FONT_XS.render(f"0{i + 1}", True, char['color'] if selected else UI_MUTED)
            self.screen.blit(index_text, (box_rect.left + 16, box_rect.top + 18))
            if selected:
                status = FONT_XS.render("READY", True, char['color'])
                self.screen.blit(status, (box_rect.right - status.get_width() - 16, box_rect.top + 18))

            icon = VisualUtils.create_character_icon(char['type'], char['color'], 112)
            self.screen.blit(icon, icon.get_rect(center=(box_rect.centerx, box_rect.top + 112)))

            name = FONT_CARD.render(char['name'], True, char['color'])
            self.screen.blit(name, name.get_rect(center=(box_rect.centerx, box_rect.top + 190)))

            if ':' in char['desc']:
                trait, detail = char['desc'].split(':', 1)
            else:
                trait, detail = "核心特性", char['desc']
            trait_text = FONT_XS.render(trait.strip().upper(), True, UI_MUTED)
            self.screen.blit(trait_text, trait_text.get_rect(center=(box_rect.centerx, box_rect.top + 232)))
            draw_wrapped_text(
                self.screen,
                detail.strip(),
                FONT_XS,
                WHITE,
                (box_rect.left + 20, box_rect.top + 266, box_rect.width - 40, 82),
                line_gap=7,
                max_lines=3,
            )
            draw_keycap(self.screen, str(i + 1), (box_rect.centerx, box_rect.bottom - 38), selected)

        back = FONT_XS.render("ESC  返回主菜单", True, UI_MUTED)
        self.screen.blit(back, (72, 828))
        hint = FONT_XS.render("← / → 或 A / D 选择    SPACE / ENTER 确认    1-5 快速定位", True, UI_MUTED)
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 828)))

    def draw_talent_selection(self):
        time = pygame.time.get_ticks() * 0.001
        draw_grid_background(self.screen, time)
        draw_corner_brackets(self.screen, (48, 44, SCREEN_WIDTH - 96, SCREEN_HEIGHT - 88), UI_PRIMARY, 28, 2)

        title = FONT_TITLE.render("选择初始天赋", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 90)))
        subtitle = FONT_XS.render("INITIAL AUGMENT // 为本局确定成长方向", True, UI_MUTED)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 142)))

        for i, talent in enumerate(self.talent_options):
            box_rect = self.get_talent_card_rect(i)
            selected = talent['type'] == self.selected_talent
            draw_panel(self.screen, box_rect, talent['color'], selected)

            icon = VisualUtils.create_talent_icon(talent['type'], talent['color'], 82)
            self.screen.blit(icon, icon.get_rect(center=(box_rect.centerx, box_rect.top + 92)))
            name = FONT_CARD.render(talent['name'], True, talent['color'])
            self.screen.blit(name, name.get_rect(center=(box_rect.centerx, box_rect.top + 170)))

            pygame.draw.line(
                self.screen,
                UI_BORDER,
                (box_rect.left + 34, box_rect.top + 208),
                (box_rect.right - 34, box_rect.top + 208),
                1,
            )
            draw_wrapped_text(
                self.screen,
                talent['desc'],
                FONT_XS,
                WHITE,
                (box_rect.left + 30, box_rect.top + 238, box_rect.width - 60, 92),
                line_gap=8,
                max_lines=4,
            )
            draw_keycap(self.screen, str(i + 1), (box_rect.centerx, box_rect.bottom - 36), selected)

        start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 180, 735, 360, 60)
        draw_button(self.screen, start_rect, "进入地牢", FONT_M, bool(self.selected_talent), 0.35)
        draw_keycap(self.screen, "SPACE", (SCREEN_WIDTH // 2, 814), bool(self.selected_talent))
        back = FONT_XS.render("ESC  返回角色选择", True, UI_MUTED)
        self.screen.blit(back, (72, 828))

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            # 根据游戏速度调整FPS
            target_fps = int(FPS * self.game_speed)
            self.clock.tick(target_fps)

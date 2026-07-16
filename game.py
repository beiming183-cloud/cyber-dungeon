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

        # 波次挑战模式
        self.wave_mode = True  # 默认启用波次模式
        self.current_wave = 0
        self.wave_enemies_count = 0  # 本波敌人总数
        self.wave_enemies_killed = 0  # 本波已击杀敌人数量
        self.wave_cooldown = 0  # 波次间隔冷却时间
        self.wave_cooldown_max = 180  # 波次间隔3秒（60fps × 3）
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

        # 初始天赋选择相关
        self.talent_options = [
            {
                'type': 'combat',
                'name': '战斗天赋',
                'emoji': '⚔️',
                'color': ORANGE,
                'desc': '随机获得一个被动技能'
            },
            {
                'type': 'survival',
                'name': '生存天赋',
                'emoji': '🛡️',
                'color': BLUE,
                'desc': '随机获得一个被动技能\n受到伤害减少20%'
            },
            {
                'type': 'exploration',
                'name': '探索天赋',
                'emoji': '💰',
                'color': YELLOW,
                'desc': '随机获得一个被动技能\n金币掉落率+50%\n经验值+20%'
            }
        ]
        self.selected_talent = 'combat'  # 默认选择战斗天赋

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
        
        # 重置波次状态
        self.wave_active = False
        self.wave_enemies_count = 0
        self.wave_enemies_killed = 0
        self.current_wave = 0
        self.prepare_next_wave(immediate=True)
        
        # 根据地图编号调整敌人数量和强度
        map_multiplier = 1.0 + (self.current_map - 1) * 0.5  # 每张地图增加50%强度
        base_enemy_count = 5 + self.current_map * 2  # 基础敌人数量随地图增加
        
        # 在其他房间生成敌人 - 更多种类
        enemy_types = ['goblin', 'slime', 'bat', 'skeleton', 'demon', 'ghost', 'spider']
        boss_room = random.choice(self.rooms[1:]) if len(self.rooms) > 1 else None
        self.map_enemy_count = 0

        for room in self.rooms[1:]:
            if random.random() < 0.7:
                # 随机选择敌人类型
                if room == boss_room and not self.boss_spawned:
                    # Boss房间 - 只在最后生成Boss
                    kind = 'dragon'
                    self.boss_spawned = True
                else:
                    kind = random.choice(enemy_types)

                # 每个房间可能生成多个敌人，随地图增加
                if kind == 'dragon':
                    enemy_count = 1
                else:
                    enemy_count = random.randint(1, 2 + self.current_map // 2)
                    
                for _ in range(enemy_count):
                    ex = (room.x + random.randint(1, room.width - 1)) * TILE_SIZE
                    ey = (room.y + random.randint(1, room.height - 1)) * TILE_SIZE
                    # 10%概率生成精英怪
                    is_elite = random.random() < 0.1
                    enemy = Enemy(ex, ey, kind, is_elite)
                    
                    # 根据地图编号增强敌人
                    enemy.hp = int(enemy.hp * map_multiplier)
                    enemy.max_hp = enemy.hp
                    enemy.damage = int(enemy.damage * map_multiplier)
                    if self.current_map > 1:
                        enemy.speed *= (1.0 + (self.current_map - 1) * 0.1)
                    
                    self.enemies.append(enemy)
                    self.map_enemy_count += 1

        # 开局立即生成第一波敌人
        if self.wave_mode:
            self.spawn_wave_enemies()

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
            if self.state == "GAME" and not self.skill_editor_active and hasattr(self, 'player') and self.player:
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
                    elif self.state == "TALENT_SELECT" and self.selected_talent:
                        # 天赋选择完成后进入游戏
                        self.init_game_world()
                        self.state = "GAME"

                # 角色选择状态 - 键盘选择
                elif self.state == "CHAR_SELECT":
                    if event.key == pygame.K_1:
                        self.selected_char = 'cyber_mage'
                        self.state = "TALENT_SELECT"
                    elif event.key == pygame.K_2:
                        self.selected_char = 'mech_ranger'
                        self.state = "TALENT_SELECT"
                    elif event.key == pygame.K_3:
                        self.selected_char = 'bio_berserker'
                        self.state = "TALENT_SELECT"
                    elif event.key == pygame.K_4:
                        self.selected_char = 'shadow_assassin'
                        self.state = "TALENT_SELECT"
                    elif event.key == pygame.K_5:
                        self.selected_char = 'holy_knight'
                        self.state = "TALENT_SELECT"
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"

                # 天赋选择状态
                elif self.state == "TALENT_SELECT":
                    # 键盘选择
                    if event.key == pygame.K_1:
                        self.selected_talent = 'combat'
                    elif event.key == pygame.K_2:
                        self.selected_talent = 'survival'
                    elif event.key == pygame.K_3:
                        self.selected_talent = 'exploration'
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
                        if event.key == pygame.K_1 and len(self.skill_selection_options) > 0:
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
                        if i < 3:
                            # 上排3个角色
                            x = SCREEN_WIDTH // 2 + (i - 1) * 280
                            y = SCREEN_HEIGHT // 2 - 80
                        else:
                            # 下排2个角色
                            x = SCREEN_WIDTH // 2 + (i - 3.5) * 280
                            y = SCREEN_HEIGHT // 2 + 150
                        box_width, box_height = 250, 280
                        box_rect = pygame.Rect(x - box_width // 2, y - box_height // 2, box_width, box_height)
                        if box_rect.collidepoint(mx, my):
                            self.selected_char = char['type']
                            self.state = "TALENT_SELECT"
                            break  # 找到匹配的角色后退出循环 event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 左键点击
                if self.state == "TALENT_SELECT":
                    mx, my = pygame.mouse.get_pos()
                    # 检查是否点击了天赋选项
                    option_height = 80
                    option_y = SCREEN_HEIGHT // 2 - option_height
                    for i, talent in enumerate(['combat', 'survival', 'exploration']):
                        option_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, option_y + i * 100, 600, option_height)
                        if option_rect.collidepoint(mx, my):
                            self.selected_talent = talent
                    # 检查是否点击了开始游戏按钮区域
                    start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 150, 300, 60)
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

        # 根据波次计算敌人数量和强度（减少数量增长，增加强度）
        base_enemies = 5 + int(self.current_wave * 1.2)  # 减少敌人数量增长
        elite_chance = min(0.5, 0.05 + self.current_wave * 0.04)  # 增加精英怪概率

        enemy_types = ['goblin', 'slime', 'bat', 'skeleton', 'demon', 'ghost', 'spider']
        # 高波次增加更强的敌人
        if self.current_wave >= 3:  # 提前引入更强敌人
            enemy_types.extend(['demon', 'ghost', 'skeleton'])  # 增加更强敌人出现频率
        if self.current_wave >= 7:  # 更高级波次增加更多精英敌人
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
            elite_chance = min(0.3, 0.05 + self.current_wave * 0.02)

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
                    kind = random.choice(enemy_types)
                    is_elite = random.random() < elite_chance
                    enemy = Enemy(spawn_x, spawn_y, kind, is_elite)

                    # 波次越高，敌人越强
                    if self.current_wave > 1:
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
                fallback_enemy = Enemy(self.player.rect.centerx + 80, self.player.rect.centery, random.choice(enemy_types), False)
                if self.current_wave > 1:
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
            self.deal_line_damage(start_x, start_y, end_x, end_y, skill.get('width', 80),
                                  skill.get('damage', 70), skill.get('effects'))
            self.camera.shake(4)
            return True

        if behavior == 'buff':
            self.player.blood_rage_timer = skill.get('duration', 480)
            self.player.damage_buff = skill.get('damage_bonus', 0.0)
            self.player.blood_rage_bonus = skill.get('lifesteal_bonus', 0.0)
            self.camera.shake(3)
            return True

        if behavior == 'buff_invincibility':
            self.player.guardian_aura_timer = skill.get('duration', 240)
            self.player.is_invincible = True
            self.camera.shake(4)
            return True

        if behavior == 'dash':
            self.perform_dash(skill, world_x, world_y)
            return True

        if behavior == 'spawn_field':
            radius = skill.get('radius', 150)
            duration = skill.get('duration', 300)
            damage = skill.get('damage', 10)
            self.spawn_poison_field(world_x, world_y, radius, duration, damage)
            return True

        if behavior == 'target_strike':
            self.perform_assassinate(skill)
            return True

        if behavior == 'spawn_clone':
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
            self.camera.shake(2)
            return True

        return False

    def fire_projectile(self, skill, target_x, target_y, force_basic=False):
        projectile_skill = dict(skill)
        projectile_skill['effects'] = dict(skill.get('effects', {}))
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
        end_x = start_x + (dx / dist) * dash_distance
        end_y = start_y + (dy / dist) * dash_distance
        width = skill.get('width', 60)
        damage = skill.get('damage', 60)
        self.deal_line_damage(start_x, start_y, end_x, end_y, width, damage, skill.get('effects'))
        self.player.rect.centerx = int(max(TILE_SIZE, min(self.map_w * TILE_SIZE - TILE_SIZE, end_x)))
        self.player.rect.centery = int(max(TILE_SIZE, min(self.map_h * TILE_SIZE - TILE_SIZE, end_y)))
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
        damage = skill.get('damage', 150)
        self.apply_damage_to_enemy(target, damage, skill.get('effects'))
        self.player.rect.centerx = target.rect.centerx + 30
        self.player.rect.centery = target.rect.centery - 30
        self.camera.shake(6)

    def update(self):
        # 技能选择或商店激活时，暂停游戏逻辑更新（但敌人和玩家都不更新）
        if self.state == "GAME" and not self.game_paused and not self.skill_selection_active and not self.skill_editor_active:
            # 根据游戏速度更新
            update_count = int(self.game_speed) if self.game_speed >= 1.0 else 1
            for _ in range(update_count):
                self.game_time += 1
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
                            # 金色Boss掉落更多奖励
                            self.player.coins += 200 * self.current_map
                            self.player.exp += 100 * self.current_map
                            # 金色Boss死亡后掉落宝箱（不需要再检查数量，直接掉落）
                            chest = TreasureChest(e.rect.centerx, e.rect.centery)
                            self.treasure_chests.append(chest)
                        # 精英怪掉落随机道具
                        if random.random() < 0.7:  # 70%概率掉落道具
                            item_types = ['health', 'mana', 'damage_boost', 'defense_boost', 'exp_orb']
                            item_type = random.choice(item_types)
                            self.items.append(Item(e.rect.centerx, e.rect.centery, item_type))
                    # 检查是否是Boss
                    if e.kind == 'dragon':
                        self.boss_defeated = True
                        # Boss掉落大量金币和经验
                        self.player.coins += 500 * self.current_map
                        self.player.exp += 200 * self.current_map
                    
                    self.enemies.remove(e)
                    self.total_kills += 1  # 增加总击杀数
                    self.enemies_killed_this_map += 1  # 当前地图击杀数
                    # 增加波次内击杀计数
                    if self.wave_mode and self.wave_active:
                        self.wave_enemies_killed += 1
                    
                    # 检查是否所有敌人（包括Boss）都被击败
                    if len([e for e in self.enemies if e.alive]) == 0:
                        if self.boss_defeated:
                            # Boss被击败，如果商店未开启则开启商店
                            if not self.shop_active:
                                self.shop_active = True
                        elif self.enemies_killed_this_map >= self.map_enemy_count * 0.8:
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
                    if hasattr(self.player, 'talent') and self.player.talent == "exploration":
                        coins = int(base_coins * 1.5)  # 50%额外金币
                        exp = int(base_exp * 1.2)  # 20%额外经验
                    else:
                        coins = base_coins
                        exp = base_exp

                    self.player.coins += coins
                    self.player.exp += exp

            # 精英怪死亡，触发技能选择（检查是否所有技能都满级）
            if elite_killed:
                # 检查是否还有可以升级的技能
                has_upgradeable = False
                for skill_id, skill_data in self.player.available_passives.items():
                    if skill_id in self.player.passive_skills:
                        if self.player.passive_skills[skill_id]['level'] < skill_data['max_level']:
                            has_upgradeable = True
                            break
                    else:
                        has_upgradeable = True
                        break
                
                # 只有当有可升级技能时才显示选择界面
                if has_upgradeable:
                    self.show_skill_selection()

            # 更新道具
            for item in self.items[:]:
                # 使用update方法的返回值来判断道具是否过期
                if not item.update():
                    self.items.remove(item)
                # 检查玩家与道具的碰撞
                elif item.rect.colliderect(self.player.rect):
                    item.apply_effect(self.player)
                    self.items.remove(item)
            
            # 更新宝箱
            for chest in self.treasure_chests[:]:
                chest.update()
                # 检查玩家与宝箱的碰撞
                if chest.rect.colliderect(self.player.rect) and not chest.opened:
                    chest.opened = True
                    # 标记商店可用，但不强制进入
                    self.shop_available = True
                    self.treasure_chests.remove(chest)

            # 检查成就
            self.check_achievements()

            # 波次系统逻辑
            if self.wave_mode:
                # 如果当前没有激活波次但已经准备好数据，立即生成新一波
                if not self.wave_active and self.wave_enemies_count > 0:
                    self.spawn_wave_enemies()

                # 检查是否完成当前波次
                if self.wave_active and self.wave_enemies_killed >= self.wave_enemies_count:
                    # 波次完成奖励
                    wave_reward = 100 * self.current_wave
                    self.player.coins += wave_reward
                    self.player.exp += 50 * self.current_wave

                    # 添加完成特效
                    for _ in range(30):
                        self.particles.append(Particle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, GREEN, 'spark'))

                    # 准备下一波
                    self.prepare_next_wave(immediate=True)
                    self.spawn_wave_enemies()
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

        # 随时间增加数量，并且随地图增加（无上限增长，初始也更高）
        base_spawn = 8 + int(self.game_time / 400)  # 时间增速显著提升
        map_bonus = max(0, (self.current_map - 1) * 5)  # 每张地图额外+5
        spawn_count = max(10, base_spawn + map_bonus)  # 至少10只，随后无上限增长

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
                    base_elite_chance = 0.05 + self.game_time / 18000
                    map_elite_bonus = (self.current_map - 1) * 0.05
                    elite_chance = min(0.4, base_elite_chance + map_elite_bonus)
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
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # 标题
        title = FONT_L.render("选择技能升级", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # 绘制选项
        option_width = 300
        option_height = 200
        spacing = 50
        total_width = len(self.skill_selection_options) * option_width + (
                    len(self.skill_selection_options) - 1) * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2

        for i, option in enumerate(self.skill_selection_options):
            x = start_x + i * (option_width + spacing)
            y = SCREEN_HEIGHT // 2 - option_height // 2

            # 选项背景
            option_surf = pygame.Surface((option_width, option_height), pygame.SRCALPHA)
            pygame.draw.rect(option_surf, UI_BG, option_surf.get_rect(), border_radius=15)
            pygame.draw.rect(option_surf, option['color'], option_surf.get_rect(), 3, border_radius=15)
            self.screen.blit(option_surf, (x, y))

            # 按键提示
            key_text = FONT_M.render(f"[{i + 1}]", True, WHITE)
            self.screen.blit(key_text, (x + 20, y + 20))

            # 技能图标
            icon_surf = VisualUtils.create_emoji_surface(option['icon'], option['color'], 60)
            self.screen.blit(icon_surf, (x + option_width // 2 - 30, y + 50))

            # 技能名称
            name_text = FONT_M.render(option['name'], True, option['color'])
            name_rect = name_text.get_rect(center=(x + option_width // 2, y + 120))
            self.screen.blit(name_text, name_rect)

            # 描述
            desc_text = FONT_S.render(option['desc'], True, WHITE)
            desc_rect = desc_text.get_rect(center=(x + option_width // 2, y + 160))
            self.screen.blit(desc_text, desc_rect)

            # 如果是升级，显示当前等级
            if option['type'] == 'upgrade':
                level_text = FONT_S.render(f"当前: Lv.{option['current_level']}", True, GRAY)
                level_rect = level_text.get_rect(center=(x + option_width // 2, y + 180))
                self.screen.blit(level_text, level_rect)

        # 提示文字
        hint = FONT_S.render("按数字键选择技能", True, WHITE)
        hint.set_alpha(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 255)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
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
            icon_surf = VisualUtils.create_emoji_surface(skill_data['icon'], skill_data['color'], 40)
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
            icon_surf = VisualUtils.create_emoji_surface(item['icon'], YELLOW, 40)
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
            icon_surf = VisualUtils.create_emoji_surface(skill.get('icon', '•'), skill.get('color', WHITE), 30)
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
                    icon_surf = VisualUtils.create_emoji_surface(skill_data.get('icon', '•'), skill_data.get('color', WHITE), 30)
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
        for p in self.particles: p.draw(self.screen, self.camera)

    def draw_ui(self):
        # 安全检查
        if not hasattr(self, 'player') or not self.player:
            return
            
        # 波次信息显示（如果启用了波次模式）
        if self.wave_mode:
            panel_w, panel_h = 350, 100
            x = SCREEN_WIDTH - panel_w - 20
            y = 20

            # 背景板
            s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            pygame.draw.rect(s, UI_BG, s.get_rect(), border_radius=15)
            pygame.draw.rect(s, WHITE, s.get_rect(), 2, border_radius=15)
            self.screen.blit(s, (x, y))

            # 波次标题
            wave_text = FONT_M.render(f"波次 {self.current_wave}", True, YELLOW)
            self.screen.blit(wave_text, (x + 20, y + 15))

            # 进度条背景
            bar_bg = pygame.Rect(x + 20, y + 50, panel_w - 40, 20)
            pygame.draw.rect(self.screen, DARK_GRAY, bar_bg, border_radius=10)

            # 进度条填充
            if self.wave_enemies_count > 0:
                progress = min(1.0, self.wave_enemies_killed / self.wave_enemies_count)
                bar_width = int((panel_w - 40) * progress)
                bar_fill = pygame.Rect(x + 20, y + 50, bar_width, 20)
                pygame.draw.rect(self.screen, GREEN, bar_fill, border_radius=10)

            # 击杀统计
            kill_text = FONT_S.render(f"{self.wave_enemies_killed}/{self.wave_enemies_count}", True, WHITE)
            text_x = x + (panel_w - kill_text.get_width()) // 2
            self.screen.blit(kill_text, (text_x, y + 45))

            # 倒计时
            if self.wave_cooldown > 0:
                countdown_text = FONT_S.render(f"下一波: {int(self.wave_cooldown / 60)}s", True, ORANGE)
                self.screen.blit(countdown_text, (x + 20, y + 75))

        # 1. 技能栏 - 调整为10个技能（分两行显示）
        if not hasattr(self, 'player') or not self.player or not hasattr(self.player, 'skills'):
            return
        
        skills_per_row = 5
        num_skills = min(len(self.player.skills), 10)  # 最多显示10个
        num_rows = (num_skills + skills_per_row - 1) // skills_per_row
        
        # 计算面板尺寸 - 确保适配屏幕
        max_panel_w = min(1080, SCREEN_WIDTH - 40)
        panel_w = max_panel_w
        skill_item_w = (panel_w - 40) // skills_per_row  # 每个技能的宽度
        item_height = 85  # 每个技能的高度（包括间距）
        panel_h = item_height * num_rows + 20  # 总高度
        
        # 计算位置 - 确保在屏幕底部可见区域
        x = max(10, (SCREEN_WIDTH - panel_w) // 2)
        y = SCREEN_HEIGHT - panel_h - 20  # 从底部向上计算，留出20像素边距

        # 背景板
        s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(s, UI_BG, s.get_rect(), border_radius=15)
        pygame.draw.rect(s, WHITE, s.get_rect(), 2, border_radius=15)
        self.screen.blit(s, (x, y))

        # 绘制每个技能 - 增强版UI（支持10个技能，分两行）
        for i, skill in enumerate(self.player.skills):
            if i >= 10:  # 最多显示10个技能
                break
                
            row = i // skills_per_row
            col = i % skills_per_row
            bx = x + 20 + col * skill_item_w
            by = y + 15 + row * item_height
            
            # 确保技能图标在屏幕内
            if by < 0 or by > SCREEN_HEIGHT - 100:
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
                name_surf = FONT_S.render(skill_name, True, color_tuple)
                key_surf = FONT_S.render(f"[{skill_key}]", True, WHITE)
                
                # 技能图标
                icon_surf = VisualUtils.create_emoji_surface(skill_icon, color_tuple, 40)
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
                        name_surf = FONT_S.render(skill_name[:6] + '...', True, color_tuple)
                    self.screen.blit(name_surf, (bx - 5, name_y))

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
        info_surf = pygame.Surface((200, 120), pygame.SRCALPHA)
        pygame.draw.rect(info_surf, UI_BG, info_surf.get_rect(), border_radius=10)
        self.screen.blit(info_surf, (10, 10))

        # 显示生命数（如果有无敌之心）
        lives_text = ""
        if hasattr(self.player, 'lives') and self.player.lives > 1:
            lives_text = FONT_S.render(f"生命: {self.player.lives}", True, (255, 100, 150))
            self.screen.blit(lives_text, (25, 20))
            y_offset = 50
        else:
            y_offset = 20
        
        hp_text = FONT_S.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, RED)
        coin_text = FONT_S.render(f"金币: {self.player.coins}", True, YELLOW)
        time_text = FONT_S.render(f"时间: {int(self.game_time / 60)}s", True, WHITE)
        
        # 显示无敌状态
        if hasattr(self.player, 'is_invincible') and self.player.is_invincible:
            inv_text = FONT_S.render(f"无敌: {int(self.player.invincible_timer / 60)}s", True, YELLOW)
            self.screen.blit(inv_text, (25, y_offset))
            y_offset += 30
        
        # 显示游戏速度
        if hasattr(self, 'game_speed') and self.game_speed > 1.0:
            speed_text = FONT_S.render(f"速度: {self.game_speed}x", True, ORANGE)
            self.screen.blit(speed_text, (25, y_offset))
            y_offset += 30

        self.screen.blit(hp_text, (25, y_offset))
        self.screen.blit(coin_text, (25, y_offset + 30))
        self.screen.blit(time_text, (25, y_offset + 60))
        
        # 显示商店可用提示（如果商店可用但未激活）
        if hasattr(self, 'shop_available') and self.shop_available and not self.shop_active:
            shop_hint_y = y_offset + 90
            shop_hint = FONT_S.render("按 [B] 打开商店", True, YELLOW)
            # 闪烁效果
            shop_hint.set_alpha(int(150 + 105 * abs(math.sin(pygame.time.get_ticks() * 0.005))))
            self.screen.blit(shop_hint, (25, shop_hint_y))

        # 3. 角色专属被动显示
        if self.player.character_passive:
            passive_surf = pygame.Surface((200, 35), pygame.SRCALPHA)
            passive_surf.fill(UI_BG)
            pygame.draw.rect(passive_surf, self.player.color, passive_surf.get_rect(), 2)
            self.screen.blit(passive_surf, (SCREEN_WIDTH - 210, 10))

            name_text = FONT_S.render(self.player.character_passive['name'], True, self.player.color)
            self.screen.blit(name_text, (SCREEN_WIDTH - 200, 15))

        # 4. 其他被动技能显示（右上角）
        if self.player.passive_skills:
            passive_y = 55
            for skill_id, skill_info in self.player.passive_skills.items():
                # 只显示存在于available_passives中的技能，避免KeyError
                if skill_id in self.player.available_passives:
                    skill_data = self.player.available_passives[skill_id]
                    level = skill_info['level']
                    icon_surf = VisualUtils.create_emoji_surface(skill_data['icon'], skill_data['color'], 30)
                    self.screen.blit(icon_surf, (SCREEN_WIDTH - 100, passive_y))
                    level_text = FONT_S.render(f"Lv.{level}", True, skill_data['color'])
                    self.screen.blit(level_text, (SCREEN_WIDTH - 70, passive_y + 5))
                    passive_y += 35

    def draw_menu(self):
        # 美化的动态背景 - 渐变星空效果
        self.screen.fill((5, 5, 15))  # 深蓝黑色背景
        
        # 星空粒子效果
        time = pygame.time.get_ticks() * 0.001
        for i in range(100):
            x = (time * 20 + i * 37.3) % SCREEN_WIDTH
            y = (time * 15 + i * 23.7) % SCREEN_HEIGHT
            brightness = int(100 + 155 * abs(math.sin(time * 2 + i * 0.1)))
            size = 1 + int(2 * abs(math.sin(time + i * 0.05)))
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (int(x), int(y)), size)
        
        # 彩色流星效果
        for i in range(3):
            meteor_x = (time * 100 + i * SCREEN_WIDTH / 3) % (SCREEN_WIDTH + 100)
            meteor_y = (time * 80 + i * 200) % SCREEN_HEIGHT
            meteor_color = [CYAN, PURPLE, NEON_BLUE][i]
            for j in range(5):
                trail_x = meteor_x - j * 20
                trail_y = meteor_y - j * 15
                alpha = 255 - j * 40
                if 0 <= trail_x <= SCREEN_WIDTH and 0 <= trail_y <= SCREEN_HEIGHT:
                    s = pygame.Surface((10, 10), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*meteor_color[:3], alpha), (5, 5), 5 - j)
                    self.screen.blit(s, (int(trail_x), int(trail_y)))

        # 标题 - 更华丽的效果
        title_text = "✨ 赛博地牢 ✨"
        title = FONT_L.render(title_text, True, NEON_BLUE)
        
        # 标题发光效果
        glow_radius = 3 + math.sin(time * 3) * 2
        glow_surf = pygame.Surface((title.get_width() + 20, title.get_height() + 20), pygame.SRCALPHA)
        for i in range(3):
            r = glow_radius + i * 2
            a = 50 - i * 15
            glow_title = FONT_L.render(title_text, True, (*NEON_BLUE[:3], a))
            glow_surf.blit(glow_title, (10 + i, 10 + i))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(glow_surf, (title_rect.x - 10, title_rect.y - 10))
        self.screen.blit(title, title_rect)
        
        # 副标题
        subtitle = FONT_M.render("Cyber Dungeon", True, CYAN)
        subtitle.set_alpha(int(150 + 105 * abs(math.sin(time * 2))))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 340))
        self.screen.blit(subtitle, subtitle_rect)

        # 提示文字 - 闪烁效果
        tip = FONT_M.render("按 [空格] 开始游戏", True, YELLOW)
        tip.set_alpha(int(150 + 105 * abs(math.sin(time * 3))))
        tip_rect = tip.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150))
        
        # 提示文字背景高亮
        highlight = pygame.Surface((tip.get_width() + 40, tip.get_height() + 20), pygame.SRCALPHA)
        highlight.fill((*YELLOW[:3], 30))
        highlight_rect = highlight.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150))
        self.screen.blit(highlight, highlight_rect)
        self.screen.blit(tip, tip_rect)
        
        manual_tip = FONT_S.render("按 [H] 查看游戏说明书", True, WHITE)
        manual_tip_rect = manual_tip.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 110))
        self.screen.blit(manual_tip, manual_tip_rect)
        
        # 装饰性边框
        border_color = (NEON_BLUE[0], NEON_BLUE[1], NEON_BLUE[2], 100)
        pygame.draw.rect(self.screen, border_color, (50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100), 3)

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

    def draw_char_selection(self):
        # 绘制背景
        self.screen.fill(BLACK)
        for i in range(50):
            rx = (pygame.time.get_ticks() * 0.1 + i * 100) % SCREEN_WIDTH
            ry = (i * 50) % SCREEN_HEIGHT
            pygame.draw.circle(self.screen, (20, 20, 40), (rx, ry), 2)

        # 绘制标题
        title = FONT_L.render("选择角色", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        # 绘制角色选项（5个角色，分两行显示：上排3个，下排2个）
        for i, char in enumerate(self.char_options):
            if i < 3:
                # 上排3个角色
                x = SCREEN_WIDTH // 2 + (i - 1) * 280
                y = SCREEN_HEIGHT // 2 - 80
            else:
                # 下排2个角色
                x = SCREEN_WIDTH // 2 + (i - 3.5) * 280
                y = SCREEN_HEIGHT // 2 + 150

            # 绘制角色框
            box_width, box_height = 250, 280
            box_rect = pygame.Rect(x - box_width // 2, y - box_height // 2, box_width, box_height)

            # 高亮选中的角色
            if char['type'] == self.selected_char:
                pygame.draw.rect(self.screen, char['color'], box_rect, 3)
                # 绘制选中指示
                select_text = FONT_M.render("选中", True, char['color'])
                select_rect = select_text.get_rect(topleft=(x - box_width // 2 + 10, y - box_height // 2 + 10))
                self.screen.blit(select_text, select_rect)
            else:
                pygame.draw.rect(self.screen, DARK_GRAY, box_rect, 2)

            # 绘制角色图标
            icon_surf = VisualUtils.create_emoji_surface(char['emoji'], char['color'], 100)
            icon_rect = icon_surf.get_rect(center=(x, y - 60))
            self.screen.blit(icon_surf, icon_rect)

            # 绘制角色名称
            name_text = FONT_M.render(char['name'], True, char['color'])
            name_rect = name_text.get_rect(center=(x, y + 20))
            self.screen.blit(name_text, name_rect)

            # 绘制角色描述
            desc_text = FONT_S.render(char['desc'], True, WHITE)
            desc_rect = desc_text.get_rect(center=(x, y + 60))
            self.screen.blit(desc_text, desc_rect)

            # 绘制按键提示
            key_text = FONT_S.render(f"按 {i + 1} 选择", True, WHITE)
            key_rect = key_text.get_rect(center=(x, y + 110))
            self.screen.blit(key_text, key_rect)

        # 绘制返回菜单提示
        back_text = FONT_M.render("按 [ESC] 返回主菜单", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        self.screen.blit(back_text, back_rect)

    def draw_talent_selection(self):
        # 绘制背景
        self.screen.fill(BLACK)
        for i in range(50):
            rx = (pygame.time.get_ticks() * 0.1 + i * 100) % SCREEN_WIDTH
            ry = (i * 50) % SCREEN_HEIGHT
            pygame.draw.circle(self.screen, (20, 20, 40), (rx, ry), 2)

        # 绘制标题
        title = FONT_L.render("选择初始天赋", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        # 绘制天赋选项
        for i, talent in enumerate(self.talent_options):
            x = SCREEN_WIDTH // 2 + (i - 1) * 300
            y = SCREEN_HEIGHT // 2

            # 绘制天赋框
            box_width, box_height = 250, 220
            box_rect = pygame.Rect(x - box_width // 2, y - box_height // 2, box_width, box_height)

            # 高亮选中的天赋
            if talent['type'] == self.selected_talent:
                pygame.draw.rect(self.screen, talent['color'], box_rect, 3)
                # 绘制选中指示
                select_text = FONT_M.render("选中", True, talent['color'])
                select_rect = select_text.get_rect(topleft=(x - box_width // 2 + 10, y - box_height // 2 + 10))
                self.screen.blit(select_text, select_rect)
            else:
                pygame.draw.rect(self.screen, DARK_GRAY, box_rect, 2)

            # 绘制天赋图标
            icon_surf = VisualUtils.create_emoji_surface(talent['emoji'], talent['color'], 80)
            icon_rect = icon_surf.get_rect(center=(x, y - 30))
            self.screen.blit(icon_surf, icon_rect)

            # 绘制天赋名称
            name_text = FONT_M.render(talent['name'], True, talent['color'])
            name_rect = name_text.get_rect(center=(x, y + 30))
            self.screen.blit(name_text, name_rect)

            # 绘制天赋描述（支持多行）
            desc_lines = talent['desc'].split('\n')
            desc_y = y + 55
            for line in desc_lines:
                desc_text = FONT_S.render(line, True, WHITE)
                desc_rect = desc_text.get_rect(center=(x, desc_y))
                self.screen.blit(desc_text, desc_rect)
                desc_y += 20

            # 绘制按键提示
            key_text = FONT_S.render(f"按 {i + 1} 选择", True, WHITE)
            key_rect = key_text.get_rect(center=(x, y + 100))
            self.screen.blit(key_text, key_rect)

        # 绘制开始游戏提示
        start_text = FONT_M.render("按 [空格] 开始游戏", True, WHITE)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        self.screen.blit(start_text, start_rect)

        # 绘制返回提示
        back_text = FONT_S.render("按 [ESC] 返回角色选择", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        self.screen.blit(back_text, back_rect)

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            # 根据游戏速度调整FPS
            target_fps = int(FPS * self.game_speed)
            self.clock.tick(target_fps)


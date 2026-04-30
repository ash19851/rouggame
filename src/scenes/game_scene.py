"""游戏主场景 - 核心游玩逻辑：世界创建、战斗、拾取、升级、房间切换和关卡过渡。"""

import math, random
import pygame
from src.scenes.base_scene import BaseScene
from src.core.engine import VIRTUAL_W, VIRTUAL_H
from src.core.isometric import world_to_iso, get_screen_center
from src.core.event_bus import EventBus
from src.core.camera import Camera
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.collision import Collider
from src.ecs.components.render import Sprite
from src.ecs.components.player import Player
from src.ecs.components.health import Health
from src.ecs.components.combat import Combat
from src.ecs.components.motion import Motion
from src.world.tilemap import Tilemap
from src.world.room import Room
from src.world.map_manager import MapManager
from src.systems.render_system import RenderSystem
from src.systems.input_system import InputSystem
from src.systems.movement_system import MovementSystem
from src.systems.collision_system import CollisionSystem
from src.systems.attack_system import AttackSystem
from src.systems.combat_system import CombatSystem
from src.systems.ai_system import AISystem
from src.systems.pickup_system import PickupSystem
from src.systems.upgrade_system import UpgradeSystem
from src.systems.particle_system import ParticleSystem
from src.systems.door_system import DoorSystem
from src.systems.equipment_system import EquipmentSystem
from src.systems.trap_system import TrapSystem
from src.systems.status_system import StatusSystem
from src.systems.boss_system import BossSystem
from src.systems.damage_number_system import DamageNumberSystem
from src.systems.sound_system import SoundSystem
from src.entities.player_factory import create_player
from src.entities.enemy_factory import create_enemy
from src.entities.pickup_factory import create_pickup
from src.data.equipment_store import load_equipment
from src.data.equipment_defs import EQUIPMENT_DEFS, RARITY_WEIGHTS
from src.data.config_loader import BALANCE, UPGRADE_CHOICES, UPGRADE_CARDS_SHOWN, RARITY_COLORS
from src.entities.boss_factory import create_boss
from src.entities.particle_factory import emit_boss_death_burst, emit_death_dissolve, emit_ambient_dust
from src.ecs.components.equipment import Equipment
from src.ecs.components.weapon_pattern import WeaponPattern
from src.ecs.components.boss import Boss, BossMinion
from src.ui.hp_bar import draw_hp_bar
from src.ui.xp_bar import draw_xp_bar
from src.ui.upgrade_card import UpgradeCard
from src.ui.text_renderer import draw_text, draw_text_right
from src.ui.equipment_hud import draw_equipment_hud, draw_equipment_toast
from src.ui.minimap import render_minimap
from src.core.keyboard import is_key_down


class GameScene(BaseScene):
    """游戏主场景，管理核心游戏循环。

    负责世界创建与销毁、房间过渡、敌人波次生成、
    升级系统覆盖层、装备/背包系统等全部游戏逻辑。
    """

    @property
    def _total_stages(self) -> int:
        """总关卡数（从配置读取）。"""
        return BALANCE["stages"]["total_stages"]

    def __init__(self, engine, sound_manager=None):
        self.engine = engine
        self.sound_manager = sound_manager
        self.world: World | None = None
        self.event_bus = EventBus()
        self.camera = Camera(VIRTUAL_W, VIRTUAL_H)
        # 初始化所有 ECS 系统
        self.render_system = RenderSystem(self.camera)
        self.input_system = InputSystem(self.camera)
        self.movement_system = MovementSystem()
        self.collision_system = CollisionSystem()
        self.attack_system = AttackSystem(self.event_bus)
        self.combat_system = CombatSystem(self.event_bus)
        self.ai_system = AISystem()
        self.pickup_system = PickupSystem(self.event_bus)
        self.upgrade_system = UpgradeSystem(self.event_bus)
        self.particle_system = ParticleSystem(self.event_bus)
        self.door_system = DoorSystem(self.event_bus)
        self.equipment_system = EquipmentSystem(self.event_bus)
        self.trap_system = TrapSystem()
        self.status_system = StatusSystem()
        self.boss_system = BossSystem(self.event_bus)
        self.damage_number_system = DamageNumberSystem(self.camera)
        self.sound_system = None
        self.tilemap: Tilemap | None = None
        self.room: Room | None = None
        self.map_manager: MapManager | None = None
        self._player_eid: int = -1
        self._kills: int = 0
        self._stage: int = 1
        self._stage_mult: float = 1.0
        # 升级覆盖层状态
        self._upgrade_overlay: bool = False
        self._upgrade_cards: list[UpgradeCard] = []
        self._transitioning: bool = False         # 玩家死亡过渡
        self._stage_transitioning: bool = False   # 关卡过渡
        self._mouse_held: bool = False            # 鼠标按住攻击
        # 敌人波次生成状态
        self._enemy_spawn_timer: float = 0.0
        self._room_enemies_alive: int = 0
        self._room_enemies_to_spawn: int = 0
        self._room_enemies_spawned: int = 0
        self._spawn_failures: int = 0
        self._flash_timer: float = 0.0           # 房间切换闪光
        self._flash_color: tuple = (255, 255, 255)  # 闪光颜色
        self._death_delay: float = 0.0           # 玩家死亡延迟计时
        self._room_cleared: bool = False         # 当前房间是否已清空
        self._door_puzzling: bool = False        # 门谜题进行中
        self._dust_timer: float = 0.0            # 环境微尘计时器
        # Tab 键冷却，防止背包开关抖动
        self._tab_cooldown: float = 0.0
        self._tab_released: bool = True
        self._loaded_equipment: dict = {}
        self._boss_eid: int = -1       # 当前 Boss 实体 ID（-1 表示无 Boss）

    def on_enter(self, state_machine, **data):
        """进入游戏场景，初始化世界和第一关。"""
        self.state_machine = state_machine
        self._kills = 0
        self._stage = 1
        self._stage_mult = 1.0
        self._transitioning = False
        self._stage_transitioning = False
        self._flash_timer = 0.0
        self._room_cleared = False
        self._loaded_equipment = load_equipment()
        self._setup_event_listeners()
        self._create_world()
        self.map_manager = MapManager(
            room_count=BALANCE["stages"]["rooms_per_stage"], stage=self._stage)
        self._enter_room()

    def on_exit(self):
        """退出场景，清理所有事件监听。"""
        self.event_bus.clear()

    def on_resume(self):
        """从其他场景返回时重置鼠标和 Tab 状态。"""
        self._mouse_held = False
        self._tab_cooldown = 0.25
        self._tab_released = False

    def _setup_event_listeners(self):
        """注册所有游戏事件监听器。"""
        self.event_bus.subscribe("PLAYER_DIED", self._on_player_died)
        self.event_bus.subscribe("ENTITY_DIED", self._on_enemy_died)
        self.event_bus.subscribe("XP_GAINED", self._on_xp_gained)
        self.event_bus.subscribe("UPGRADE_READY", self._on_upgrade_ready)
        self.event_bus.subscribe("DOOR_APPROACHED", self._on_door_approached)
        self.event_bus.subscribe("INVENTORY_FULL", self._on_inventory_full)
        self.event_bus.subscribe("BOSS_DIED", self._on_boss_died)
        # 屏幕震动
        self.event_bus.subscribe("PLAYER_HIT", self._on_player_hit_shake)
        self.event_bus.subscribe("BOSS_DIED", self._on_boss_died_shake)
        self.event_bus.subscribe("BOSS_GROUND_SLAM", self._on_ground_slam_shake)
        self.event_bus.subscribe("BOSS_ENRAGE", self._on_enrage_shake)

    def _create_world(self):
        """创建 ECS 世界并注册所有系统。"""
        self.world = World()
        systems = [
            self.input_system,
            self.ai_system,
            self.movement_system,
            self.collision_system,
            self.attack_system,
            self.combat_system,
            self.pickup_system,
            self.equipment_system,
            self.upgrade_system,
            self.trap_system,
            self.status_system,
            self.boss_system,
            self.particle_system,
            self.damage_number_system,
            self.door_system,
        ]
        if self.sound_manager is not None:
            self.sound_system = SoundSystem(self.event_bus, self.sound_manager)
            systems.append(self.sound_system)
        for s in systems:
            self.world.add_system(s)

    def _enter_room(self):
        """初始化新房间：创建瓦片地图、生成玩家和敌人。"""
        self.room = self.map_manager.create_room()
        self.tilemap = self.room.tilemap

        self.collision_system.set_tilemap(self.tilemap)
        self.collision_system.doors_open = False
        self.door_system.set_tilemap(self.tilemap)
        self.door_system.reset_door()
        self.trap_system.set_tilemap(self.tilemap)

        self._room_cleared = False
        self._room_enemies_alive = 0
        # 从房间配置的怪物数量范围中随机取值
        self._room_enemies_to_spawn = random.randint(*self.room.monster_count)
        self._room_enemies_spawned = 0
        self._spawn_failures = 0
        self._enemy_spawn_timer = BALANCE["enemy_spawn"]["initial_delay"]

        if self._player_eid == -1 or self._player_eid not in self.world.entities:
            self._spawn_player()

        # 对新玩家应用已加载的装备
        if self._loaded_equipment:
            self.equipment_system.init_player_equipment(
                self.world, self._player_eid, self._loaded_equipment)
            self._loaded_equipment = {}

        # 将玩家重新定位到房间出生点
        pt = self.world.get_component(self._player_eid, Transform)
        if pt:
            pt.x = self.room.spawn_x
            pt.y = self.room.spawn_y

        self._spawn_initial_enemies()
        # 环境微尘粒子
        room_w = self.tilemap.width * self.tilemap.tile_size
        room_h = self.tilemap.height * self.tilemap.tile_size
        emit_ambient_dust(self.world, room_w, room_h)
        self._dust_timer = random.uniform(3.0, 5.0)
        # Boss 房间：在中央生成 Boss
        self._boss_eid = -1
        if self.room.is_boss_room:
            self._spawn_boss()
        self.event_bus.emit("NEW_ROOM", room_index=self.map_manager.current_index)

    def _spawn_player(self):
        """在房间出生点创建玩家实体。"""
        self._player_eid = create_player(self.world, self.room.spawn_x, self.room.spawn_y)

    def _spawn_initial_enemies(self):
        """进入房间时立即生成首批敌人（按比例）。"""
        initial = max(3, int(self._room_enemies_to_spawn
                           * BALANCE["enemy_spawn"]["spawn_initial_fraction"]))
        for _ in range(initial):
            self._spawn_one_enemy()

    def _spawn_boss(self):
        """在房间中央生成 Boss。"""
        cx = self.tilemap.width * self.tilemap.tile_size / 2
        cy = self.tilemap.height * self.tilemap.tile_size / 2
        encounter_level = self.map_manager.get_encounter_level()
        self._boss_eid = create_boss(
            self.world, encounter_level, cx, cy,
            self.map_manager.difficulty_mult,
        )
        self._room_enemies_alive += 1

    def _spawn_one_enemy(self):
        """在房间随机可行走位置生成一个敌人。最多尝试 50 次。"""
        if self._room_enemies_spawned >= self._room_enemies_to_spawn:
            return
        if not self.room or not self.tilemap:
            return

        pool = self.room.monster_pool
        etype = random.choice(pool) if pool else "skeleton"

        # 随机尝试瓦片位置，避开墙体和玩家出生点
        for _attempt in range(50):
            tx = random.randint(3, self.tilemap.width - 4)
            ty = random.randint(3, self.tilemap.height - 4)
            if not self.tilemap.is_wall(tx, ty):
                wx, wy = self.tilemap.tile_to_world_center(tx, ty)
                px = self.room.spawn_x
                py = self.room.spawn_y
                # 确保敌人不在玩家出生点附近生成
                if math.sqrt((wx - px) ** 2 + (wy - py) ** 2) > BALANCE["enemy_spawn"]["min_spawn_distance"]:
                    create_enemy(self.world, etype, wx, wy, self.map_manager.difficulty_mult)
                    self._room_enemies_alive += 1
                    self._room_enemies_spawned += 1
                    return

        self._spawn_failures += 1

    def handle_events(self, events: list[pygame.event.Event]):
        """处理事件：升级覆盖层优先，否则传递鼠标攻击和输入事件。"""
        if self._upgrade_overlay:
            self._handle_upgrade_events(events)
            return

        for event in events:
            if event.type == pygame.QUIT:
                self.engine.running = False
                return

        self.input_system.set_events(events)

        # 鼠标按住攻击检测
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._mouse_held = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._mouse_held = False

        self.attack_system.set_attacking(self._mouse_held)

    def _handle_upgrade_events(self, events: list[pygame.event.Event]):
        """处理升级选择覆盖层中的点击事件。"""
        for event in events:
            for card in self._upgrade_cards:
                card.handle_event(event)
                if card.is_clicked(event):
                    self.upgrade_system.apply_upgrade(self.world, card.stat_key)
                    self._upgrade_overlay = False
                    self._upgrade_cards.clear()
                    # 升级时播放粒子爆发效果
                    pt = self.world.get_component(self._player_eid, Transform)
                    if pt:
                        self.particle_system.emit_upgrade_burst(self.world, pt.x, pt.y)
                    return

    def _on_player_died(self, event_type: str, data: dict):
        """玩家死亡事件处理：发射死亡粒子，延迟后进入结算。"""
        if self._transitioning:
            return
        pt = self.world.get_component(self._player_eid, Transform)
        if pt:
            from src.entities.particle_factory import emit_player_death_burst
            emit_player_death_burst(self.world, pt.x, pt.y)
        self._death_delay = 0.7
        self._flash_timer = 0.7
        self._flash_color = (255, 40, 30)
        self._transitioning = True

    def _on_door_approached(self, event_type: str, data: dict):
        """靠近门时：弹出谜题覆盖层场景。"""
        if self._door_puzzling:
            return
        self._door_puzzling = True

        # 难度随房间推进递增
        difficulty = self.map_manager.current_index // 2 if self.map_manager else 0

        from src.scenes.door_puzzle_scene import DoorPuzzleScene
        self.state_machine.push(
            DoorPuzzleScene(self.engine),
            difficulty=difficulty,
            callback=self._on_door_puzzle_done,
        )

    def _on_door_puzzle_done(self, success: bool):
        """门谜题结果回调。

        成功：回复 5 点生命。
        失败：扣除 15% 最大生命值（至少留 1 点）。
        """
        self._door_puzzling = False
        self.state_machine.pop()

        ph = self.world.get_component(self._player_eid, Health)
        if success:
            if ph:
                ph.current = min(ph.max, ph.current + 5)
        else:
            if ph:
                penalty = max(1, int(ph.max * 0.15))
                ph.current = max(1, ph.current - penalty)

        self.door_system.reset_door()
        self._do_room_transition()

    def _on_inventory_full(self, event_type: str, data: dict):
        """背包满时：将装备生成为可拾取掉落物。"""
        equipment_id = data.get("equipment_id", "")
        x = data.get("x", 0)
        y = data.get("y", 0)
        create_pickup(self.world, "equipment", 0, x, y, equipment_id=equipment_id)

    def _on_boss_died(self, event_type: str, data: dict):
        """Boss 死亡事件回调：预留，主要逻辑已在 _on_enemy_died 中处理。"""
        pass

    def _on_player_hit_shake(self, event_type: str, data: dict):
        self.camera.shake(4.0, 0.15)

    def _on_boss_died_shake(self, event_type: str, data: dict):
        self.camera.shake(10.0, 0.45)

    def _on_ground_slam_shake(self, event_type: str, data: dict):
        self.camera.shake(6.0, 0.3)

    def _on_enrage_shake(self, event_type: str, data: dict):
        self.camera.shake(5.0, 0.25)

    def _open_inventory(self):
        """打开背包场景覆盖层。"""
        from src.scenes.inventory_scene import InventoryScene
        self.state_machine.push(
            InventoryScene(self.engine),
            world=self.world,
            player_eid=self._player_eid,
            equipment_system=self.equipment_system,
        )

    def _on_enemy_died(self, event_type: str, data: dict):
        """敌人死亡处理：增加击杀数、掉落经验和可能的掉落物。Boss 有专属掉落。"""
        self._kills += 1
        self._room_enemies_alive -= 1

        eid = data.get("entity")
        pos = data.get("position", (0, 0))

        # 检查是否为 Boss 或 Boss 召唤物
        is_boss = eid is not None and self.world.has_component(eid, Boss)
        is_boss_minion = eid is not None and self.world.has_component(eid, BossMinion)

        if eid is not None:
            spr = self.world.get_component(eid, Sprite)
            sprite_color: tuple = (200, 180, 150)
            if spr:
                if spr.surface is None:
                    sprite_color = spr.color
                elif hasattr(spr.surface, 'get_at'):
                    sprite_color = spr.surface.get_at((spr.surface.get_width() // 2, spr.surface.get_height() // 2))[:3]
            emit_death_dissolve(self.world, pos[0], pos[1], sprite_color)
            self.world.destroy_entity(eid)

        drops_cfg = BALANCE["drops"]

        if is_boss:
            # Boss 专属：大爆炸粒子、3x XP、生命包、高稀有度装备
            emit_boss_death_burst(self.world, pos[0], pos[1])
            create_pickup(self.world, "xp",
                          random.randint(drops_cfg["xp_min"] * 3, drops_cfg["xp_max"] * 3),
                          pos[0], pos[1])
            create_pickup(self.world, "health", drops_cfg["health_amount"] * 2,
                          pos[0] + random.uniform(-10, 10), pos[1] + random.uniform(-10, 10))
            # Boss 掉落保底稀有+装备
            boss_rarity = random.choices(["rare", "epic"], weights=[30, 70])[0]
            boss_items = [eid for eid, edef in EQUIPMENT_DEFS.items()
                          if edef["rarity"] == boss_rarity]
            if boss_items:
                create_pickup(self.world, "equipment", 0,
                              pos[0] + random.uniform(-10, 10),
                              pos[1] + random.uniform(-10, 10),
                              equipment_id=random.choice(boss_items))
            # 清理所有 Boss 召唤物
            for meid in list(self.world.entities):
                if self.world.has_component(meid, BossMinion):
                    self._room_enemies_alive -= 1
                    self.world.destroy_entity(meid)
            self._boss_eid = -1
            self.event_bus.emit("BOSS_DIED", entity=eid)
            # Boss 房间立即清空
            if self.room and self.room.is_boss_room:
                self._room_enemies_alive = 0
        elif is_boss_minion:
            # Boss 召唤物不掉落
            pass
        else:
            # 普通敌人掉落
            create_pickup(self.world, "xp",
                          random.randint(drops_cfg["xp_min"], drops_cfg["xp_max"]),
                          pos[0], pos[1])
            if random.random() < drops_cfg["health_chance"]:
                create_pickup(self.world, "health", drops_cfg["health_amount"],
                              pos[0] + random.uniform(-5, 5), pos[1] + random.uniform(-5, 5))
            if random.random() < drops_cfg["equipment_chance"]:
                items_by_rarity: dict[str, list[str]] = {"common": [], "rare": [], "epic": []}
                for eq_id, eq_def in EQUIPMENT_DEFS.items():
                    items_by_rarity[eq_def["rarity"]].append(eq_id)
                rarity = random.choices(
                    ["common", "rare", "epic"],
                    weights=[RARITY_WEIGHTS["common"], RARITY_WEIGHTS["rare"], RARITY_WEIGHTS["epic"]],
                )[0]
                if items_by_rarity[rarity]:
                    eq_id = random.choice(items_by_rarity[rarity])
                    create_pickup(self.world, "equipment", 0,
                                  pos[0] + random.uniform(-5, 5),
                                  pos[1] + random.uniform(-5, 5),
                                  equipment_id=eq_id)

        self._check_room_cleared()

    def _check_room_cleared(self):
        """检查房间是否已清空（所有敌人死亡或生成失败次数过多）。"""
        if self._room_cleared:
            return
        # 房间清空条件：无存活敌人且已生成全部或失败过多次
        if self._room_enemies_alive <= 0 and (
                self._room_enemies_spawned >= self._room_enemies_to_spawn
                or self._spawn_failures >= 3):
            self._room_cleared = True
            self.room.cleared = True
            self.collision_system.doors_open = True
            self.event_bus.emit("ROOM_CLEARED", room_index=self.map_manager.current_index)

    def _on_xp_gained(self, event_type: str, data: dict):
        """经验获取事件（由 UpgradeSystem 处理升级逻辑）。"""
        pass

    def _on_upgrade_ready(self, event_type: str, data: dict):
        """升级就绪：显示升级覆盖层。"""
        self._upgrade_overlay = True
        self._create_upgrade_cards()

    def _create_upgrade_cards(self):
        """从配置中随机抽取升级选项卡片并居中排列。"""
        self._upgrade_cards.clear()

        choices = [(c["label"], c["desc"], c["key"]) for c in UPGRADE_CHOICES]
        selected = random.sample(choices, min(UPGRADE_CARDS_SHOWN, len(choices)))

        # 计算卡片总宽度并居中排列
        total_w = len(selected) * (UpgradeCard.WIDTH + UpgradeCard.GAP) - UpgradeCard.GAP
        start_x = VIRTUAL_W / 2 - total_w / 2 + UpgradeCard.WIDTH / 2

        for i, (label, desc, key) in enumerate(selected):
            x = start_x + i * (UpgradeCard.WIDTH + UpgradeCard.GAP)
            self._upgrade_cards.append(UpgradeCard(label, desc, key, x, VIRTUAL_H / 2))

    def update(self, dt: float):
        """主游戏循环更新：生成敌人、更新系统和相机。"""
        if self._transitioning:
            self._death_delay -= dt
            self.camera.update(dt)
            self.particle_system.update(self.world, dt)
            if self._death_delay <= 0:
                self._do_game_over()
            return

        if self._stage_transitioning:
            return

        if self._upgrade_overlay:
            self.particle_system.update(self.world, dt)
            return

        # 过渡闪光或门谜题进行中时暂停大部分逻辑
        if self._flash_timer > 0 or self._door_puzzling:
            self._flash_timer -= dt
            self.world.update(dt)
            return

        # Tab 键轮询（冷却 + 释放闸门，防止一次按键反复触发）
        if self._tab_cooldown > 0:
            self._tab_cooldown -= dt
        else:
            tab_pressed = is_key_down(pygame.K_TAB)
            if not tab_pressed:
                self._tab_released = True
            elif self._tab_released:
                self._open_inventory()
                self._tab_cooldown = 0.3
                self._tab_released = False

        # 随时间分批生成敌人
        self._enemy_spawn_timer -= dt
        if self._enemy_spawn_timer <= 0 and self._room_enemies_spawned < self._room_enemies_to_spawn:
            self._spawn_one_enemy()
            self._enemy_spawn_timer = random.uniform(
                BALANCE["enemy_spawn"]["wave_interval_min"],
                BALANCE["enemy_spawn"]["wave_interval_max"])

        self.world.update(dt)

        # 环境微尘定时补充
        if not self._room_cleared:
            self._dust_timer -= dt
            if self._dust_timer <= 0:
                rw = self.tilemap.width * self.tilemap.tile_size
                rh = self.tilemap.height * self.tilemap.tile_size
                emit_ambient_dust(self.world, rw, rh)
                self._dust_timer = random.uniform(3.0, 5.0)

        # 相机跟随玩家
        pt = self.world.get_component(self._player_eid, Transform)
        if pt:
            self.camera.follow(pt.x, pt.y)
        self.camera.update(dt)

    def _do_room_transition(self):
        """保存玩家状态，推进到下一个房间或触发关卡过渡。"""
        self.door_system.reset_door()

        # 最后一个房间：进入关卡过渡或胜利结算
        if self.map_manager.is_last_room:
            if self._stage < self._total_stages:
                self._start_stage_transition()
            else:
                self._do_game_over(victory=True)
            return

        self.map_manager.advance()

        # 保存玩家核心属性
        player_state = self._save_player_state()

        # 销毁所有非玩家实体
        for eid in list(self.world.entities):
            if eid != self._player_eid:
                self.world.destroy_entity(eid)

        # 立即刷新以确保新实体获得干净的 ID
        self.world._flush_destroyed()

        # 进入新房间
        self._enter_room()

        # 恢复玩家属性
        self._restore_player_state(player_state)

        # 房间切换闪光效果
        self._flash_timer = 0.12
        self._flash_color = (255, 255, 255)

    def _start_stage_transition(self):
        """推入关卡过渡覆盖层，暂停游戏逻辑。"""
        from src.scenes.stage_transition_scene import StageTransitionScene
        self._stage_transitioning = True
        self.state_machine.push(
            StageTransitionScene(self.engine),
            stage_cleared=self._stage,
            total_stages=self._total_stages,
            next_stage=self._stage + 1,
            callback=self._on_stage_transition_done,
        )

    def _on_stage_transition_done(self, next_stage: int):
        """关卡过渡完成回调。

        执行操作：完全恢复生命 → 保存/恢复玩家状态 →
        重新加载装备文件（仓库场景可能修改了配置）→ 进入新关卡。
        """
        self._stage_transitioning = False
        self._stage = next_stage

        # 过渡后完全回复生命
        ph = self.world.get_component(self._player_eid, Health)
        if ph:
            ph.current = ph.max

        # 保存玩家状态
        player_state = self._save_player_state()

        # 重新加载装备（仓库场景可能修改了 equipment.json）
        self._loaded_equipment = load_equipment()

        # 销毁所有非玩家实体
        for eid in list(self.world.entities):
            if eid != self._player_eid:
                self.world.destroy_entity(eid)
        self.world._flush_destroyed()

        # 为下一关创建新的地图管理器
        self.map_manager = MapManager(
            room_count=BALANCE["stages"]["rooms_per_stage"], stage=self._stage)

        # 进入新关卡第一个房间
        self._enter_room()

        # 恢复玩家状态
        self._restore_player_state(player_state)

        # 加载装备（仓库场景可能已修改装备文件）
        if self._loaded_equipment:
            # 先移除当前装备属性，避免叠加
            eq = self.world.get_component(self._player_eid, Equipment)
            if eq:
                for slot, item in eq.items.items():
                    self.equipment_system._apply_stats(self.world, item, reverse=True)
                    if slot == "weapon":
                        self.equipment_system._set_pattern(self.world, "normal")
                eq.items.clear()
            # 再从文件加载
            self.equipment_system.init_player_equipment(
                self.world, self._player_eid, self._loaded_equipment)
            self._loaded_equipment = {}

        # 过渡闪光效果
        self._flash_timer = 0.12
        self._flash_color = (255, 255, 255)

    def _save_player_state(self) -> dict:
        """保存当前玩家的核心属性（生命、经验、等级等）到字典。"""
        ph = self.world.get_component(self._player_eid, Health)
        pp = self.world.get_component(self._player_eid, Player)
        pc = self.world.get_component(self._player_eid, Combat)
        pm = self.world.get_component(self._player_eid, Motion)

        return {
            "hp_current": ph.current if ph else 100,
            "hp_max": ph.max if ph else 100,
            "xp": pp.xp if pp else 0,
            "xp_to_level": pp.xp_to_level if pp else 30,
            "level": pp.level if pp else 1,
            "damage": pc.damage if pc else 10,
            "attack_speed": pc.attack_speed if pc else 1.2,
            "speed": pm.speed if pm else 140.0,
        }

    def _restore_player_state(self, state: dict):
        """从字典恢复玩家属性（房间/关卡过渡后）。"""
        ph = self.world.get_component(self._player_eid, Health)
        pp = self.world.get_component(self._player_eid, Player)
        pc = self.world.get_component(self._player_eid, Combat)
        pm = self.world.get_component(self._player_eid, Motion)

        if ph:
            ph.current = state["hp_current"]
            ph.max = state["hp_max"]
        if pp:
            pp.xp = state["xp"]
            pp.xp_to_level = state["xp_to_level"]
            pp.level = state["level"]
        if pc:
            pc.damage = state["damage"]
            pc.attack_speed = state["attack_speed"]
        if pm:
            pm.speed = state["speed"]

    def _do_game_over(self, victory: bool = False):
        """切换到游戏结束场景并传递结算数据。"""
        from src.scenes.game_over_scene import GameOverScene
        pp = self.world.get_component(self._player_eid, Player)
        stats = {
            "level": pp.level if pp else 1,
            "kills": self._kills,
            "stage": self._stage,
            "victory": victory,
        }
        self.state_machine.switch(GameOverScene(self.engine), stats=stats)

    def render(self, surface: pygame.Surface):
        """渲染游戏画面：瓦片地图、实体、敌人血条、小地图、UI 和升级覆盖层。"""
        surface.fill((10, 10, 15))

        if self.tilemap:
            self.tilemap.render(surface, self.camera.offset, doors_open=self._room_cleared)

        self.render_system.render_to(self.world, surface, 0)
        self._render_enemy_hp_bars(surface)
        self._render_boss_hp_bar(surface)
        self._render_minimap(surface)
        self._render_ui(surface)

        if self._upgrade_overlay:
            self._render_upgrade_overlay(surface)

        # 房间过渡闪光效果
        if self._flash_timer > 0:
            alpha = int(255 * min(1.0, self._flash_timer / 0.12))
            flash = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
            c = self._flash_color if self._flash_color else (255, 255, 255)
            flash.fill((*c, alpha))
            surface.blit(flash, (0, 0))

    def _render_enemy_hp_bars(self, surface: pygame.Surface):
        """在敌人头顶绘制小型血条。颜色根据血量比例变化（绿→黄→红）。"""
        if not self.world:
            return
        ox, oy = self.camera.offset
        cx, cy = get_screen_center()
        # 查询所有有变换、碰撞体和生命的实体
        enemies = self.world.query(Transform, Collider, Health)
        for eid in enemies:
            if self.world.has_component(eid, Player):
                continue
            t = self.world.get_component(eid, Transform)
            c = self.world.get_component(eid, Collider)
            h = self.world.get_component(eid, Health)
            if not h.alive:
                continue

            # 从世界坐标转换到等距屏幕坐标
            sx, sy = world_to_iso(t.x, t.y, ox, oy, cx, cy)

            bar_w = max(c.width, 20)
            bar_h = 4
            bar_x = sx - bar_w / 2
            bar_y = sy - c.height / 2 - 14

            # 背景
            pygame.draw.rect(surface, (30, 10, 10), (bar_x, bar_y, bar_w, bar_h))
            # 填充部分，颜色随血量变化
            if h.max > 0:
                fill_w = int(bar_w * h.current / h.max)
                ratio = h.current / h.max
                if ratio > 0.5:
                    color = (80, 180, 60)
                elif ratio > 0.25:
                    color = (220, 180, 40)
                else:
                    color = (220, 60, 40)
                pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, bar_h))
            # 边框
            pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h), 1)

    def _render_boss_hp_bar(self, surface: pygame.Surface):
        """Boss 生命条：屏幕顶部居中，金色边框。"""
        if not self.world:
            return
        bosses = self.world.query(Boss, Health)
        if not bosses:
            return

        boss_cfg = BALANCE.get("boss", {})
        bar_w = boss_cfg.get("hp_bar_width", 200)
        bar_h = boss_cfg.get("hp_bar_height", 12)
        bar_y = boss_cfg.get("hp_bar_y", 8)

        for eid in bosses:
            h = self.world.get_component(eid, Health)
            b = self.world.get_component(eid, Boss)
            if h is None or not h.alive:
                continue

            bar_x = VIRTUAL_W / 2 - bar_w / 2

            # 背景
            pygame.draw.rect(surface, (40, 10, 10), (bar_x, bar_y, bar_w, bar_h))
            # 血量填充
            if h.max > 0:
                ratio = h.current / h.max
                fill_w = int(bar_w * ratio)
                if ratio > 0.5:
                    color = (220, 180, 40)
                elif ratio > 0.25:
                    color = (220, 140, 30)
                else:
                    color = (220, 60, 40)
                # 狂暴时加入红色脉冲
                if b.enraged:
                    color = (255, 40, 30)
                pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, bar_h))
            # 金色边框
            pygame.draw.rect(surface, (200, 160, 20), (bar_x, bar_y, bar_w, bar_h), 2)
            # Boss 名称
            nametag = f"{b.show_name}  Lv.{b.encounter_level}"
            if b.enraged:
                nametag += " [狂暴]"
            draw_text(surface, nametag, VIRTUAL_W / 2, bar_y - 2,
                      size=12, color=(255, 220, 100), center=True)
            # HP 数字
            hp_text = f"{h.current}/{h.max}"
            draw_text(surface, hp_text, VIRTUAL_W / 2, bar_y + bar_h + 2,
                      size=10, color=(200, 200, 200), center=True)

    def _render_minimap(self, surface: pygame.Surface):
        """渲染小地图，显示当前房间的玩家位置和敌人位置。"""
        if not self.world or not self.tilemap:
            return

        pt = self.world.get_component(self._player_eid, Transform)
        player_pos = (pt.x, pt.y) if pt else None

        enemies = self.world.query(Transform, Collider, Health)
        enemy_positions = []
        for eid in enemies:
            if not self.world.has_component(eid, Player):
                et = self.world.get_component(eid, Transform)
                eh = self.world.get_component(eid, Health)
                if et and eh and eh.alive:
                    enemy_positions.append((et.x, et.y))

        render_minimap(surface, self.tilemap, player_pos, enemy_positions,
                       self._room_cleared, VIRTUAL_W, VIRTUAL_H)

    def _render_ui(self, surface: pygame.Surface):
        """渲染所有 UI 元素：血条、经验条、关卡计数、击杀数、瞄准线、冷却条和装备 HUD。"""
        ph = self.world.get_component(self._player_eid, Health)
        pp = self.world.get_component(self._player_eid, Player)

        # 血条
        if ph:
            draw_hp_bar(surface, 10, 10, 140, 14, ph.current, ph.max)
            draw_text(surface, f"{ph.current}/{ph.max}", 155, 11, size=12, color=(200, 200, 200))

        # 经验条
        if pp:
            draw_xp_bar(surface, 10, 28, 140, 8, pp.xp, pp.xp_to_level, pp.level)

        # 关卡和房间计数
        if self.map_manager:
            room_num = self.map_manager.current_index + 1
            total = self.map_manager.room_count
            draw_text(surface, f"第 {self._stage} 关 — 房间 {room_num}/{total}",
                      VIRTUAL_W / 2, 10, size=15, color=(200, 200, 200), center=True)


        # 房间清空提示（脉冲闪烁）
        if self._room_cleared:
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 500)
            c = int(180 * pulse)
            draw_text(surface, "房间已清空！寻找门", VIRTUAL_W / 2, VIRTUAL_H - 16,
                      size=14, color=(c, int(220 * pulse), c // 2),
                      center=True)

        # 击杀计数
        draw_text_right(surface, f"击杀: {self._kills}", VIRTUAL_W - 10, 10,
                        size=13, color=(180, 180, 200))

        # 瞄准线（等距投影）
        if ph and ph.alive:
            pt = self.world.get_component(self._player_eid, Transform)
            pc = self.world.get_component(self._player_eid, Combat)
            pp2 = self.world.get_component(self._player_eid, Player)
            if pt and pp2:
                ox, oy = self.camera.offset
                cx, cy = get_screen_center()
                sx, sy = world_to_iso(pt.x, pt.y, ox, oy, cx, cy)
                # 瞄准线终点（前方 30px 世界空间）
                aim_wx = pt.x + pp2.aim_x * 30
                aim_wy = pt.y + pp2.aim_y * 30
                ex, ey = world_to_iso(aim_wx, aim_wy, ox, oy, cx, cy)
                pygame.draw.line(surface, (255, 255, 255, 100), (sx, sy), (ex, ey), 2)
                # 攻击范围指示点
                dot_r = 3
                range_dist = pc.range if pc else 200.0
                dot_wx = pt.x + pp2.aim_x * range_dist
                dot_wy = pt.y + pp2.aim_y * range_dist
                dot_x, dot_y = world_to_iso(dot_wx, dot_wy, ox, oy, cx, cy)
                pygame.draw.circle(surface, (255, 200, 80), (int(dot_x), int(dot_y)), dot_r)

        # 冷却进度条
        pc2 = self.world.get_component(self._player_eid, Combat)
        if pc2:
            cooldown_pct = max(0, 1.0 - pc2.cooldown * pc2.attack_speed)
            bar_x, bar_y = 10, 44
            bar_w, bar_h = 80, 5
            pygame.draw.rect(surface, (30, 30, 50), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (180, 180, 80), (bar_x, bar_y, int(bar_w * cooldown_pct), bar_h))

        # 装备 HUD
        eq = self.world.get_component(self._player_eid, Equipment)
        wp = self.world.get_component(self._player_eid, WeaponPattern)
        pattern = wp.pattern if wp else ""
        if eq:
            draw_equipment_hud(surface, eq.items, VIRTUAL_W, VIRTUAL_H, pattern)
        # 装备提示（获得新装备时闪烁显示）
        if self.equipment_system._toast_timer > 0:
            draw_equipment_toast(
                surface,
                self.equipment_system._toast_text,
                self.equipment_system._toast_color,
                self.equipment_system.toast_alpha,
                VIRTUAL_W, VIRTUAL_H,
            )

    def _render_upgrade_overlay(self, surface: pygame.Surface):
        """渲染升级选择覆盖层（半透明背景 + 卡片选项）。"""
        dim = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        surface.blit(dim, (0, 0))

        draw_text(surface, "升级！", VIRTUAL_W / 2, VIRTUAL_H / 2 - 50,
                  size=28, color=(255, 215, 0), center=True, shadow=True)
        draw_text(surface, "选择一个升级", VIRTUAL_W / 2, VIRTUAL_H / 2 - 25,
                  size=14, color=(200, 200, 200), center=True)

        for card in self._upgrade_cards:
            card.render(surface)

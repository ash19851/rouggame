"""程序化像素精灵图集 —— 所有精灵在启动时通过像素定义生成，无需外部图片文件。

精灵通过紧凑的字符串像素定义生成，每个字符代表一种颜色。颜色映射表将字符映射为 RGB 元组。
"""

import pygame

# 精灵缓存: key -> pygame.Surface
_cache: dict[str, pygame.Surface] = {}

# ── 调色板 ────────────────────────────────────────────────────────────────
C_TRANSPARENT = (0, 0, 0, 0)
C_OUTLINE = (25, 25, 40)         # 通用描边色
# 玩家
C_PLAYER_BODY = (80, 160, 255)   # 玩家主体蓝色
C_PLAYER_HL = (120, 200, 255)    # 玩家高光蓝
C_PLAYER_SH = (40, 120, 200)     # 玩家阴影蓝
C_PLAYER_CORE = (0, 240, 255)    # 玩家核心青色发光
C_PLAYER_VISOR = (200, 210, 230) # 玩家护目镜浅灰
# 骷髅
C_BONE = (210, 190, 170)         # 骨骼亮色
C_BONE_HL = (235, 220, 200)      # 骨骼高光
C_BONE_DARK = (150, 130, 110)    # 骨骼暗色
# 史莱姆
C_SLIME = (100, 220, 100)        # 史莱姆绿色
C_SLIME_DARK = (60, 170, 60)     # 史莱姆暗绿
C_SLIME_HL = (180, 255, 180)     # 史莱姆高光
C_SLIME_SH = (40, 130, 40)       # 史莱姆阴影
# 弓箭手
C_ARCHER_BODY = (140, 200, 100)  # 弓箭手身体
C_ARCHER_HL = (180, 230, 130)    # 弓箭手高光
C_ARCHER_SH = (60, 120, 40)      # 弓箭手阴影
C_ARCHER_HAT = (80, 140, 50)     # 弓箭手帽子
# 幽灵
C_GHOST = (200, 210, 240)        # 幽灵主体
C_GHOST_HL = (235, 240, 255)     # 幽灵高光白
C_GHOST_SH = (150, 160, 190)     # 幽灵阴影
C_GHOST_EYE = (60, 60, 80)       # 幽灵眼睛
# 树精
C_SPRIGGAN = (180, 130, 80)      # 树精主体
C_SPRIGGAN_HL = (210, 160, 100)  # 树精高光
C_SPRIGGAN_SH = (120, 90, 50)    # 树精阴影
C_SPRIGGAN_EYE = (255, 200, 50)  # 树精发光眼睛
# 掉落物
C_XP_GREEN = (100, 255, 100)     # 经验球绿色
C_HP_RED = (255, 100, 100)       # 生命药水红色
C_EQUIP_GOLD = (255, 215, 0)     # 装备掉落金色
# Boss 颜色
C_BOSS_KNIGHT_ARMOR = (60, 20, 20)     # 骑士暗红铠甲
C_BOSS_KNIGHT_HORN = (220, 200, 180)   # 骑士角高光
C_BOSS_KNIGHT_SKIN = (140, 120, 100)   # 骑士肤色
C_BOSS_LICH_ROBE = (80, 40, 160)       # 巫妖紫袍
C_BOSS_LICH_GLOW = (180, 140, 255)     # 巫妖发光
C_BOSS_LICH_CROWN = (200, 180, 100)    # 巫妖王冠
C_BOSS_DRAGON_SCALE = (50, 55, 70)     # 龙鳞暗色
C_BOSS_DRAGON_EYE = (255, 200, 50)     # 龙眼火焰
C_BOSS_DRAGON_WING = (70, 40, 50)      # 龙翼膜


def _make_surface(w: int, h: int, pixels: list[str], color_map: dict[str, tuple]) -> pygame.Surface:
    """从紧凑字符串像素定义构建 Surface。

    参数:
        w: 精灵宽度（像素）
        h: 精灵高度（像素）
        pixels: 字符串列表，每行一个字符串，每个字符对应一个像素的颜色键
        color_map: 颜色键（字符串中的字符）到 RGB/RGBA 元组的映射

    返回:
        生成的带透明通道的 pygame.Surface
    """
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill(C_TRANSPARENT)
    for y, row in enumerate(pixels):
        for x, ch in enumerate(row):
            if ch in color_map:
                surf.set_at((x, y), color_map[ch])
    return surf


# ── 精灵定义 ────────────────────────────────────────────────────────────────
# 每个精灵用字符串像素网格定义，字符含义见各自的 color_map。
# 行尾注释是设计标注（如 "helmet", "visor" 等），帮助理解像素结构。

def _player() -> pygame.Surface:
    """玩家精灵: 12x16，蓝色机甲战士，带肩甲和能量核心。"""
    pixels = [
        "....####....",  # 0  头盔顶
        "...#HHHH#...",  # 1  头盔高光
        "..#HBBBBH#..",  # 2  额头
        "..#BCCCCB#..",  # 3  护目镜→能量核心（C=青色）
        "..#BBBBBB#..",  # 4  面部
        "...#BBBB#...",  # 5  下巴
        "....####....",  # 6  脖子
        "..##HBBH##..",  # 7  肩甲（H=高光）
        "..#BBBBBB#..",  # 8  躯干上
        "..#BBCBB#..",  # 9  胸核心（C=青色发光）
        "..#BBBBBB#..",  # 10 躯干下
        "...#SSSS#...",  # 11 腰带（S=暗色）
        "...#H....H#..",  # 12 腿部高光边缘
        "...#B....B#..",  # 13 腿部
        "..#S......S#.",  # 14 小腿阴影
        "..#S......S#.",  # 15 靴子
    ]
    return _make_surface(12, 16, pixels, {
        "#": C_OUTLINE, "B": C_PLAYER_BODY, "H": C_PLAYER_HL,
        "S": C_PLAYER_SH, "C": C_PLAYER_CORE,
    })


def _skeleton() -> pygame.Surface:
    """骷髅精灵: 12x16，白色骨骼形象，带肋骨和眼窝发光。"""
    pixels = [
        "....####....",  # 0  头骨顶
        "...#HHHH#...",  # 1  头顶高光
        "..#H#WW#H#..",  # 2  眼窝（#=空洞,W=骨白）
        "..#HWWDWH#..",  # 3  面部骨板
        "...#W##W#...",  # 4  下颌
        "....####....",  # 5  脖子
        "....#DD#....",  # 6  肋骨上（D=暗骨）
        "...#D..D#...",  # 7  肋骨空隙
        "...#D..D#...",  # 8  肋骨
        "....#DD#....",  # 9  胸骨
        ".....##.....",  # 10 脊柱
        "....#WW#....",  # 11 骨盆
        "....#..#....",  # 12
        "...#W..W#...",  # 13 腿骨
        "...#....#...",  # 14
        "..#D....D#..",  # 15 脚骨阴影
    ]
    return _make_surface(12, 16, pixels, {
        "#": C_OUTLINE, "W": C_BONE, "H": C_BONE_HL, "D": C_BONE_DARK,
    })


def _slime() -> pygame.Surface:
    """史莱姆精灵: 10x8，绿色弹跳果冻，带半透明核心和高光。"""
    pixels = [
        "...####...",  # 0
        "..#gggg#..",  # 1
        ".#gHHHHg#.",  # 2  高光环
        ".#gHggHg#.",  # 3  主体+内部高光点
        ".#gggggg#.",  # 4
        "..#gSSg#..",  # 5  底部阴影
        "...#SS#...",  # 6  阴影底
        "....##....",  # 7
    ]
    return _make_surface(10, 8, pixels, {
        "#": C_OUTLINE, "g": C_SLIME, "H": C_SLIME_HL, "S": C_SLIME_SH,
    })


def _archer() -> pygame.Surface:
    """弓箭手精灵: 12x16，绿色兜帽、长弓和箭袋。"""
    pixels = [
        "....####....",  # 0  兜帽顶
        "...#TTAAT#..",  # 1  兜帽（T=帽子暗绿）
        "..#AAAAAA#..",  # 2  头
        "..#AAGGAA#..",  # 3  眼睛（G=浅灰）
        "..#AA##AA#..",  # 4  面部兜帽阴影
        "...#AAAA#...",  # 5  下巴
        "....####....",  # 6  脖子
        "..#......##.",  # 7  持弓手臂伸展
        "..#LL#...#.L",  # 8  身体（L=高光绿）
        "..#LL#..#..L",  # 9  弓+身体
        "..#SS#.#...L",  # 10 弓弦+身体阴影（S=阴影）
        "...#SSSB...L",  # 11 腰带箭袋（B=木色）
        "...#....#...",  # 12 腿
        "...#L...L#..",  # 13 腿高光
        "...#....#...",  # 14
        "..#S....S#..",  # 15 靴阴影
    ]
    return _make_surface(12, 16, pixels, {
        "#": C_OUTLINE, "A": C_ARCHER_BODY, "T": C_ARCHER_HAT,
        "L": C_ARCHER_HL, "S": C_ARCHER_SH, "G": C_PLAYER_VISOR,
        "B": (120, 80, 40),  # 弓/箭袋木色
    })


def _ghost() -> pygame.Surface:
    """幽灵精灵: 12x13，白色半透明形象，带内部渐变和波浪底部。"""
    pixels = [
        "....####....",  # 0
        "...#HHHH#...",  # 1  头顶高光
        "..#HEEHHE#..",  # 2  大眼（E=深色,H=高光）
        "..#WWWWWW#..",  # 3  主体
        "..#WSSWWW#..",  # 4  内部阴影渐变
        "...#WWWW#...",  # 5
        "....#WW#....",  # 6
        "...#HHWW#...",  # 7  高光上身
        "..#WW..SW#..",  # 8
        ".#HW....WS#.",  # 9  波浪+高光阴影
        ".#W......S#.",  # 10
        ".#S.#..#.S#.",  # 11 底部波浪（S=暗色）
        ".#..#..#..#.",  # 12
    ]
    return _make_surface(12, 13, pixels, {
        "#": C_OUTLINE, "W": C_GHOST, "H": C_GHOST_HL,
        "S": C_GHOST_SH, "E": C_GHOST_EYE,
    })


def _spriggan() -> pygame.Surface:
    """树精精灵: 12x15，棕色树皮纹理，金色发光眼，枝条手臂。"""
    pixels = [
        "....####....",  # 0  头顶枝条
        "...#HHSS#...",  # 1  头顶（H=高光,S=主体）
        "..#SSEESS#..",  # 2  发光金眼（E=金色）
        "..#SHDDHS#..",  # 3  树皮纹理（H=纹路亮,D=纹路暗）
        "...#SSSS#...",  # 4  头部
        "....####....",  # 5  脖子
        "....#SS#....",  # 6  躯干
        "...#HSDH#...",  # 7  躯干树皮纹理
        "..#SH..HS#..",  # 8  枝条手臂伸展
        "...#SSSS#...",  # 9  躯干下
        "....#DS#....",  # 10 腰部（D=暗色）
        "....#SS#....",  # 11
        "...#H..H#...",  # 12 腿高光
        "...#S..S#...",  # 13 腿
        "..#D....D#..",  # 14 脚根阴影
    ]
    return _make_surface(12, 15, pixels, {
        "#": C_OUTLINE, "S": C_SPRIGGAN, "H": C_SPRIGGAN_HL,
        "D": C_SPRIGGAN_SH, "E": C_SPRIGGAN_EYE,
    })


def _projectile(color: tuple[int, int, int], size: int) -> pygame.Surface:
    """动态生成投射物精灵：三层同心圆（光晕+核心+高亮中心）。

    参数:
        color: 基础颜色，光晕和中心会在基础色上加亮
        size: 精灵尺寸（像素）
    """
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill(C_TRANSPARENT)
    cx = size // 2
    r, g, b = color
    # 外层光晕（基础色 +100）
    glow = (min(255, r + 100), min(255, g + 100), min(255, b + 100))
    pygame.draw.circle(surf, glow, (cx, cx), size // 2)
    # 中层核心（基础色）
    pygame.draw.circle(surf, color, (cx, cx), max(1, size // 2 - 1))
    # 内层高亮中心（基础色 +180）
    hot = (min(255, r + 180), min(255, g + 180), min(255, b + 180))
    pygame.draw.circle(surf, hot, (cx, cx), max(1, size // 4))
    return surf


def _xp_orb() -> pygame.Surface:
    """经验球精灵: 6x6 菱形绿色宝石。"""
    surf = pygame.Surface((6, 6), pygame.SRCALPHA)
    surf.fill(C_TRANSPARENT)
    # 曼哈顿距离 <=2 的像素构成菱形
    for y in range(6):
        for x in range(6):
            if abs(x - 3) + abs(y - 3) <= 2:
                surf.set_at((x, y), C_XP_GREEN)
    surf.set_at((3, 2), (200, 255, 200))  # 高光点
    return surf


def _health_pickup() -> pygame.Surface:
    """生命药水精灵: 6x6 红色十字形状。"""
    surf = pygame.Surface((6, 6), pygame.SRCALPHA)
    surf.fill(C_TRANSPARENT)
    # 十字形: 中间列3行 + 中间行3列
    for y in range(6):
        for x in range(6):
            if (abs(x - 3) <= 1 and y in (1, 2, 3, 4)) or (abs(y - 3) <= 1 and x in (1, 2, 3, 4)):
                surf.set_at((x, y), C_HP_RED)
    surf.set_at((3, 3), (255, 200, 200))  # 中心高光
    return surf


def _equipment_pickup() -> pygame.Surface:
    """装备掉落物精灵: 8x8 金色菱形（拾取提示）。"""
    surf = pygame.Surface((8, 8), pygame.SRCALPHA)
    surf.fill(C_TRANSPARENT)
    # 曼哈顿距离 <=3 的像素构成菱形
    for y in range(8):
        for x in range(8):
            if abs(x - 4) + abs(y - 4) <= 3:
                surf.set_at((x, y), C_EQUIP_GOLD)
    surf.set_at((4, 3), (255, 240, 180))  # 高光点
    return surf


# ── 装备图标精灵 (8x8) ──────────────────────────────────────────────────────
# 以下为装备槽位对应的图标精灵

def _icon_sword() -> pygame.Surface:
    """剑图标: 8x8，银白色十字剑形。"""
    pixels = [
        "...#....",  # 剑尖
        "..###...",  # 护手
        "...#....",  # 剑柄
        "...#....",
        "...#....",
        "...#....",
        "..###...",  # 护手底
        "..###...",  # 剑柄尾
    ]
    return _make_surface(8, 8, pixels, {"#": (180, 200, 220)})


def _icon_bow() -> pygame.Surface:
    """弓图标: 8x8，棕色双弧弓形。"""
    pixels = [
        ".#....#.",  # 弓臂上端
        "..#..#..",
        "...#....",  # 弓弦
        "..##.#..",
        "...#....",  # 弓弦
        "..#..#..",
        ".#....#.",  # 弓臂下端
        "........",
    ]
    return _make_surface(8, 8, pixels, {"#": (180, 160, 120)})


def _icon_staff() -> pygame.Surface:
    """法杖图标: 8x8，紫色长杆。"""
    pixels = [
        "...##...",  # 杖头
        "....#...",
        "....#...",  # 杖杆
        "....#...",
        "....#...",
        "....#...",
        "....#...",
        "...###..",  # 杖底
    ]
    return _make_surface(8, 8, pixels, {"#": (160, 120, 200)})


def _icon_armor() -> pygame.Surface:
    """护甲图标: 8x8，灰色胸甲形状。"""
    pixels = [
        "..####..",
        ".##..##.",
        ".##..##.",
        ".######.",
        ".######.",
        ".######.",
        "..####..",
        "........",
    ]
    return _make_surface(8, 8, pixels, {"#": (180, 180, 190)})


def _icon_ring() -> pygame.Surface:
    """戒指图标: 8x8，金色圆环。"""
    pixels = [
        "........",
        "..####..",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        ".##..##.",
        "..####..",
        "........",
    ]
    return _make_surface(8, 8, pixels, {"#": (255, 215, 0)})


def _icon_orb() -> pygame.Surface:
    """宝珠图标: 8x8，蓝色实心圆。"""
    pixels = [
        "...##...",
        "..####..",
        ".######.",
        ".######.",
        ".######.",
        ".######.",
        "..####..",
        "...##...",
    ]
    return _make_surface(8, 8, pixels, {"#": (100, 180, 255)})


# ── 攻击模式图标 (10x10) ────────────────────────────────────────────────────

def _pattern_normal() -> pygame.Surface:
    """普通攻击模式图标: 右上方向箭头。"""
    pixels = [
        "..........",
        "...#......",  # 箭头尖
        "...##.....",
        "...###....",
        "...####...",  # 箭头底部
        "...###....",
        "...##.....",
        "...#......",
        "..........",
        "..........",
    ]
    return _make_surface(10, 10, pixels, {"#": (220, 220, 100)})


def _pattern_scatter() -> pygame.Surface:
    """散射模式图标: 四角扩散形状。"""
    pixels = [
        "..........",
        "...#...#..",
        "...#...#..",
        "..##..##..",
        "..#######.",  # 中心汇聚
        "..##..##..",
        "...#...#..",
        "...#...#..",
        "..........",
        "..........",
    ]
    return _make_surface(10, 10, pixels, {"#": (255, 180, 80)})


def _pattern_orbital() -> pygame.Surface:
    """轨道模式图标: 环形+中心点。"""
    pixels = [
        "..........",
        "...####...",
        "..#....#..",
        ".#......#.",
        ".#..#.#.#.",  # 中心星球 + 轨道
        ".#......#.",
        "..#....#..",
        "...####...",
        "..........",
        "..........",
    ]
    return _make_surface(10, 10, pixels, {"#": (100, 200, 255)})


def _pattern_wave() -> pygame.Surface:
    """波模式图标: 波纹扩散形状。"""
    pixels = [
        "..........",
        "...#...#..",
        "..#.#.#.#.",
        ".#.......#",
        "#.........",  # 波源
        ".#.......#",
        "..#.#.#.#.",
        "...#...#..",
        "..........",
        "..........",
    ]
    return _make_surface(10, 10, pixels, {"#": (160, 120, 220)})


def _pattern_impact() -> pygame.Surface:
    """冲击散射模式图标: 中心向外四散。"""
    pixels = [
        "..........",
        "....#.....",
        "...#.#....",
        "..#...#...",
        ".#..#..#..",  # 中心冲击点，向四角扩散
        "..#...#...",
        "...#.#....",
        "....#.....",
        "..........",
        "..........",
    ]
    return _make_surface(10, 10, pixels, {"#": (255, 130, 80)})


# ── Boss 精灵 ──────────────────────────────────────────────────────────────

def _boss_knight() -> pygame.Surface:
    """Boss 骑士精灵: 24x28，暗红重甲、角盔、大剑。"""
    pixels = [
        "........##....##........",  # 0  角尖
        "........###..###........",  # 1  双角
        "........########........",  # 2  头盔顶
        ".......#RRRRRRRR#.......",  # 3
        ".......#RRRHHHRR#.......",  # 4  护目镜缝（H=亮色）
        ".......#RRRRRRRR#.......",  # 5  头盔面
        ".......#RRR##RRR#.......",  # 6  下颌
        "........########........",  # 7  颈甲
        ".......##RRRRRR##.......",  # 8  肩甲左
        "......##RRRRRRRR##......",  # 9  肩甲展开
        "......#RRRSSSSRRR#......",  # 10 胸甲（S=肤色）
        "......#RRRSSSSRRR#......",  # 11
        "......#RRRRRRRRRR#......",  # 12 胸甲下
        ".......##RRRRRR##.......",  # 13 腰
        "........#RRRRRR#........",  # 14
        "........#RRRRRR#........",  # 15 腿甲
        ".......#RRRRRRRR#.......",  # 16
        ".......#RR....RR#.......",  # 17 腿分开
        ".......#R......R#.......",  # 18
        ".......#R......R#.......",  # 19
        ".......#R......R#.......",  # 20
        "......##R......R##......",  # 21
        "......#RR......RR#......",  # 22 靴
        ".....##RR......RR##.....",  # 23
        "....##RRR......RRR##....",  # 24
    ]
    return _make_surface(24, 25, pixels, {
        "#": C_OUTLINE, "R": C_BOSS_KNIGHT_ARMOR,
        "H": C_BOSS_KNIGHT_HORN, "S": C_BOSS_KNIGHT_SKIN,
    })


def _boss_lich() -> pygame.Surface:
    """Boss 巫妖精灵: 24x28，浮空紫袍、王冠、发光双手。"""
    pixels = [
        ".........#YY#.........",  # 0  王冠尖
        "........#######........",  # 1  王冠
        "........#PPPPP#........",  # 2  头
        ".......#PGGGGP#.......",  # 3  发光眼（G=亮紫）
        ".......#PPPPP#........",  # 4
        "........#####.........",  # 5  颈
        "......##PPPPP##.......",  # 6  肩
        ".....##PPPPPPP##......",  # 7  袍展开
        "....#PPPPPPPPP#.......",  # 8
        "....#PPPGPGPPP#.......",  # 9  双手发光
        "....#PPPPPPPPP#.......",  # 10
        ".....#PPPPPPP#........",  # 11
        ".....#PPPPPPP#........",  # 12 袍身
        "......#PPPPP#.........",  # 13
        "......#PPPPP#.........",  # 14
        "......#PPPPP#.........",  # 15
        ".....#PPP PPP#........",  # 16 袍分叉
        "....#PPP...PPP#.......",  # 17
        "...#PPP.....PPP#......",  # 18
        "..#PPP.......PPP#.....",  # 19 袍底飘动
        ".#PPP.........#.......",  # 20
        "#PPP..........#.......",  # 21
        ".#P...........#.......",  # 22
        "..#...........#.......",  # 23
    ]
    return _make_surface(24, 24, pixels, {
        "#": C_OUTLINE, "P": C_BOSS_LICH_ROBE,
        "G": C_BOSS_LICH_GLOW, "Y": C_BOSS_LICH_CROWN,
    })


def _boss_dragon() -> pygame.Surface:
    """Boss 龙精灵: 32x33，展开双翼、尖尾、喷火口。"""
    pixels = [
        "............##................",  # 0  翼尖
        "...........###................",  # 1
        "..........#WWW#...............",  # 2  翼膜（W=深翼色）
        ".........#WWWWW#..............",  # 3
        "........#WWW#WWW#.....###.....",  # 4
        ".......#WWW#.#WWW#...#####....",  # 5
        "......#WWW#...#WWW#.##DDD##...",  # 6  龙鳞身开始（D=鳞色）
        ".....#WWW#.....#WWW##DDD##....",  # 7
        "......#W#.......#W##DDD##.....",  # 8
        ".......#.........##DDD##......",  # 9
        ".......##.......##DDD##.......",  # 10
        "........##.....##DDD##........",  # 11
        ".........##...##DDD##.........",  # 12
        "..........##.##DDD##..........",  # 13 身体
        "...........#####DD##..........",  # 14
        "..........#DDDDDDD#....##.....",  # 15 龙头
        ".........#DDDDEDDD#..####.....",  # 16 龙眼（E=金色）
        "........#DDDDDDDDD#.####......",  # 17
        "........#DDDDDDDDD###.........",  # 18 喷火口
        "........#DDDDDDDDD#...........",  # 19
        ".........#DDDDDDD#............",  # 20 颈
        "..........#DDDDD#.............",  # 21
        "...........#DDD#..............",  # 22
        "............#D#...............",  # 23 身体
        "............#D#...............",  # 24
        "...........##D##..............",  # 25
        "..........#DDDDD#.............",  # 26
        "........##DDD.DDD##...........",  # 27 腿
        ".......#DDD.....#DD#..........",  # 28
        "......#DDD.......#D#..........",  # 29
        "......#DD.........#D#.........",  # 30
        "......#D..........#D#.........",  # 31 尾
        "......#............##.........",  # 32
    ]
    return _make_surface(32, 33, pixels, {
        "#": C_OUTLINE, "D": C_BOSS_DRAGON_SCALE,
        "W": C_BOSS_DRAGON_WING, "E": C_BOSS_DRAGON_EYE,
    })


# 自定义精灵键列表（从 PNG 加载的）
_custom_keys: list[str] = []


def _load_custom_sprites():
    """从 assets/sprites/ 目录加载 PNG 文件到精灵缓存。"""
    global _custom_keys
    import os
    sprite_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sprites")
    if not os.path.isdir(sprite_dir):
        return
    for filename in os.listdir(sprite_dir):
        if filename.lower().endswith(".png"):
            key = os.path.splitext(filename)[0]
            path = os.path.join(sprite_dir, filename)
            try:
                img = pygame.image.load(path).convert_alpha()
                _cache[key] = img
                _custom_keys.append(key)
            except pygame.error:
                pass


# ── 公共接口 ─────────────────────────────────────────────────────────────────

def init_sprites():
    """初始化所有精灵：生成程序化精灵并加载自定义 PNG。在 pygame.init() 之后调用一次。"""
    global _cache
    _cache = {
        "player": _player(),
        "skeleton": _skeleton(),
        "slime": _slime(),
        "archer": _archer(),
        "ghost": _ghost(),
        "spriggan": _spriggan(),
        "xp": _xp_orb(),
        "health": _health_pickup(),
        "equipment": _equipment_pickup(),
        "icon_sword": _icon_sword(),
        "icon_bow": _icon_bow(),
        "icon_staff": _icon_staff(),
        "icon_armor": _icon_armor(),
        "icon_ring": _icon_ring(),
        "icon_orb": _icon_orb(),
        "pattern_normal": _pattern_normal(),
        "pattern_scatter": _pattern_scatter(),
        "pattern_orbital": _pattern_orbital(),
        "pattern_wave": _pattern_wave(),
        "pattern_impact": _pattern_impact(),
        "boss_knight": _boss_knight(),
        "boss_lich": _boss_lich(),
        "boss_dragon": _boss_dragon(),
    }

    # Load custom PNG sprites from assets/sprites/
    _load_custom_sprites()


def get_player_sprite() -> pygame.Surface:
    """获取玩家精灵 surface。"""
    return _cache["player"]


def get_enemy_sprite(enemy_type: str) -> pygame.Surface | None:
    """根据敌人类型获取精灵，不存在则返回 None。"""
    return _cache.get(enemy_type)


def get_pickup_sprite(pickup_type: str) -> pygame.Surface | None:
    """根据掉落物类型获取精灵（xp/health/equipment）。"""
    return _cache.get(pickup_type)


def get_projectile_sprite(color: tuple[int, int, int], size: int) -> pygame.Surface:
    """获取或动态生成投射物精灵（按颜色+尺寸缓存）。"""
    key = f"proj_{color}_{size}"
    if key not in _cache:
        _cache[key] = _projectile(color, size)
    return _cache[key]


def get_sprite(key: str) -> pygame.Surface | None:
    """通用的精灵缓存查找接口。"""
    return _cache.get(key)


def list_enemy_sprites() -> list[str]:
    """返回所有敌人精灵的键列表（按名称排序）。"""
    enemy_keys = ["skeleton", "slime", "archer", "ghost", "spriggan"]
    return [k for k in enemy_keys if k in _cache]


def list_all_sprites() -> list[str]:
    """返回所有精灵的键列表（排除动态生成的投射物）。"""
    return sorted(k for k in _cache if not k.startswith("proj_"))


def list_icon_sprites() -> list[str]:
    """返回所有装备图标精灵的键列表。"""
    return sorted(k for k in _cache if k.startswith("icon_"))


def list_pattern_sprites() -> list[str]:
    """返回所有攻击模式图标精灵的键列表。"""
    return sorted(k for k in _cache if k.startswith("pattern_"))


def list_custom_sprites() -> list[str]:
    """返回从 PNG 文件加载的自定义精灵键列表。"""
    return sorted(_custom_keys)

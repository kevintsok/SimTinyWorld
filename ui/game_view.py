"""
Game View - 游戏主视图

负责渲染地图、智能体位置、对话气泡等游戏元素。
"""

import pygame
import math
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from ui.fonts import get_font


# MBTI 颜色映射
MBTI_COLORS = {
    'INTJ': (128, 0, 128),    # 紫色
    'INTP': (100, 100, 180),   # 蓝紫色
    'ENTJ': (200, 0, 0),       # 深红色
    'ENTP': (255, 100, 50),    # 橙红色
    'INFJ': (0, 100, 100),     # 青色
    'INFP': (0, 150, 150),     # 浅青色
    'ENFJ': (0, 128, 0),       # 绿色
    'ENFP': (100, 200, 100),   # 浅绿色
    'ISTJ': (0, 0, 128),       # 深蓝色
    'ISTP': (50, 50, 150),     # 海军蓝
    'ESTJ': (128, 64, 0),      # 棕色
    'ESTP': (180, 100, 50),    # 浅棕色
    'ISFJ': (100, 50, 100),    # 灰紫色
    'ISFP': (150, 100, 150),    # 淡紫色
    'ESFJ': (200, 150, 100),    # 桃色
    'ESFP': (255, 150, 150),    # 粉红色
}

# E/I 形状: E用三角形指向右边，I用圆形
E_SHAPE = 'triangle'  # 外向
I_SHAPE = 'circle'   # 内向

# 位置类型图标颜色
LOCATION_COLORS = {
    "公司": (100, 149, 237),   # 矢车菊蓝
    "公园": (60, 179, 113),    # 中等海洋绿
    "学校": (255, 165, 0),     # 橙色
    "医院": (220, 20, 60),     # 猩红色
    "餐厅": (218, 165, 32),   # 金菊黄
    "商场": (186, 85, 211),    # 中等兰花紫
    "图书馆": (139, 69, 19),   # 马鞍棕色
    "健身房": (50, 205, 50),   # 石灰绿
    "咖啡厅": (210, 180, 140), # 秘鲁香槟
    "银行": (255, 215, 0),     # 金色
    "电影院": (188, 143, 143), # 浅玫瑰棕色
    "超市": (255, 140, 0),     # 深橙色
    "default": (100, 100, 100), # 灰色
}


@dataclass
class AgentVisual:
    """智能体视觉数据"""
    id: str
    name: str
    mbti: str
    position: Tuple[float, float]
    target_position: Optional[Tuple[float, float]] = None
    start_position: Optional[Tuple[float, float]] = None
    move_start_time: float = 0
    move_duration: float = 1.0
    color: Tuple[int, int, int] = (200, 200, 200)
    mood_value: float = 0.0
    mood_desc: str = "平静"
    status: str = "空闲"
    is_talking: bool = False
    current_dialog: str = ""
    dialog_end_time: float = 0
    # 新增：更多属性
    wealth: Dict[str, float] = None  # 时间、社交、健康、精神、金钱
    recent_memories: List[str] = None  # 近期记忆
    long_term_memory_count: int = 0
    short_term_memory_count: int = 0
    personality_traits: List[str] = None  # 性格特点
    core_values: List[str] = None  # 核心价值观

    def __post_init__(self):
        if self.wealth is None:
            self.wealth = {"time": 0, "social": 0, "health": 0.5, "mental": 0.5, "money": 0}
        if self.recent_memories is None:
            self.recent_memories = []
        if self.personality_traits is None:
            self.personality_traits = []
        if self.core_values is None:
            self.core_values = []


@dataclass
class LocationVisual:
    """位置视觉数据"""
    name: str
    position: Tuple[int, int]
    type: str
    description: str
    agents: Set[str] = None

    def __post_init__(self):
        if self.agents is None:
            self.agents = set()


class DialogBubble:
    """对话气泡"""
    def __init__(self, agent_name: str, text: str, position: Tuple[float, float],
                 agent_color: Tuple[int, int, int], duration: float = 3.0):
        self.agent_name = agent_name
        self.text = text
        self.position = position
        self.agent_color = agent_color
        self.create_time = time.time()
        self.duration = duration
        self.opacity = 255

    @property
    def end_time(self) -> float:
        return self.create_time + self.duration

    @property
    def is_expired(self) -> bool:
        return time.time() > self.end_time

    def update(self):
        """更新气泡状态"""
        remaining = self.end_time - time.time()
        if remaining < 0.5:
            self.opacity = int(255 * (remaining / 0.5))
        if remaining < 0:
            self.opacity = 0


class GameView:
    """游戏主视图"""

    def __init__(self, width: int = 1000, height: int = 700):
        """初始化游戏视图

        Args:
            width: 窗口宽度
            height: 窗口高度
        """
        pygame.init()
        self.width = width
        self.height = height

        # 创建窗口
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("智能体模拟世界 - 游戏视图")

        # 加载字体
        self.font = get_font(14)
        self.font_large = get_font(18)
        self.font_title = get_font(24)

        # 时钟
        self.clock = pygame.time.Clock()

        # 数据
        self.agents: Dict[str, AgentVisual] = {}
        self.locations: Dict[str, LocationVisual] = {}
        self.dialogs: List[DialogBubble] = []
        self.connections: Dict[str, List[Tuple[str, int]]] = {}  # location -> [(connected_location, distance), ...]

        # 动画
        self.camera_offset = [0, 0]
        self.is_dragging = False
        self.last_mouse_pos = (0, 0)

        # 地图区域 (左侧)
        self.map_rect = pygame.Rect(0, 0, int(width * 0.65), height)

        # 信息面板区域 (右侧)
        self.panel_rect = pygame.Rect(int(width * 0.65), 0, int(width * 0.35), height)

        # 颜色
        self.bg_color = (30, 33, 40)
        self.map_bg_color = (35, 38, 45)
        self.panel_bg_color = (40, 44, 52)
        self.grid_color = (50, 54, 62)

    def set_locations(self, locations: Dict[str, dict], connections: Dict[str, List[Tuple[str, int]]]):
        """设置位置数据

        Args:
            locations: {name: {type, description, position (x, y)}}
            connections: {location: [(connected_location, distance), ...]}
        """
        self.locations.clear()
        for name, info in locations.items():
            pos = info.get('position', (0, 0))
            self.locations[name] = LocationVisual(
                name=name,
                position=pos,
                type=info.get('type', '默认'),
                description=info.get('description', '')
            )
        self.connections = connections

    def add_agent(self, agent_id: str, name: str, mbti: str, location: str,
                  mood_value: float = 0.0, mood_desc: str = "平静", status: str = "空闲",
                  wealth: Dict[str, float] = None, recent_memories: List[str] = None,
                  personality_traits: List[str] = None, core_values: List[str] = None,
                  long_term_memory_count: int = 0, short_term_memory_count: int = 0):
        """添加智能体

        Args:
            agent_id: 智能体ID
            name: 名称
            mbti: MBTI类型
            location: 当前位置
            mood_value: 心情值 (-1 到 1)
            mood_desc: 心情描述
            status: 当前状态
            wealth: 财富字典
            recent_memories: 近期记忆列表
            personality_traits: 性格特点列表
            core_values: 核心价值观列表
            long_term_memory_count: 长期记忆数量
            short_term_memory_count: 短期记忆数量
        """
        # 获取位置坐标
        loc = self.locations.get(location)
        if loc:
            pos = loc.position
        else:
            pos = (400, 300)

        # 确定颜色
        color = MBTI_COLORS.get(mbti, (200, 200, 200))

        self.agents[agent_id] = AgentVisual(
            id=agent_id,
            name=name,
            mbti=mbti,
            position=pos,
            color=color,
            mood_value=mood_value,
            mood_desc=mood_desc,
            status=status,
            wealth=wealth or {"time": 0, "social": 0, "health": 0.5, "mental": 0.5, "money": 0},
            recent_memories=recent_memories or [],
            personality_traits=personality_traits or [],
            core_values=core_values or [],
            long_term_memory_count=long_term_memory_count,
            short_term_memory_count=short_term_memory_count
        )

        # 更新位置中的智能体列表
        if location in self.locations:
            self.locations[location].agents.add(agent_id)

    def move_agent(self, agent_id: str, from_location: str, to_location: str, duration: float = 1.0):
        """移动智能体

        Args:
            agent_id: 智能体ID
            from_location: 起始位置
            to_location: 目标位置
            duration: 移动时间（秒）
        """
        if agent_id not in self.agents:
            return

        from_loc = self.locations.get(from_location)
        to_loc = self.locations.get(to_location)

        if not from_loc or not to_loc:
            return

        agent = self.agents[agent_id]
        agent.target_position = to_loc.position
        agent.start_position = agent.position
        agent.move_start_time = time.time()
        agent.move_duration = duration

        # 更新位置中的智能体列表
        from_loc.agents.discard(agent_id)
        to_loc.agents.add(agent_id)

    def update_agent_mood(self, agent_id: str, mood_value: float, mood_desc: str = None):
        """更新智能体心情"""
        if agent_id in self.agents:
            self.agents[agent_id].mood_value = mood_value
            if mood_desc:
                self.agents[agent_id].mood_desc = mood_desc

    def update_agent_info(self, agent_id: str, status: str = None, wealth: Dict[str, float] = None,
                         recent_memories: List[str] = None, long_term_memory_count: int = None,
                         short_term_memory_count: int = None):
        """更新智能体详细信息"""
        if agent_id not in self.agents:
            return
        agent = self.agents[agent_id]
        if status is not None:
            agent.status = status
        if wealth is not None:
            agent.wealth = wealth
        if recent_memories is not None:
            agent.recent_memories = recent_memories
        if long_term_memory_count is not None:
            agent.long_term_memory_count = long_term_memory_count
        if short_term_memory_count is not None:
            agent.short_term_memory_count = short_term_memory_count

    def show_dialog(self, agent_id: str, text: str, duration: float = 3.0):
        """显示对话气泡

        Args:
            agent_id: 智能体ID
            text: 对话内容
            duration: 显示时长
        """
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]
        bubble = DialogBubble(
            agent_name=agent.name,
            text=text,
            position=agent.position,
            agent_color=agent.color,
            duration=duration
        )
        self.dialogs.append(bubble)
        agent.is_talking = True
        agent.current_dialog = text
        agent.dialog_end_time = time.time() + duration

    def get_agent_shape(self, mbti: str) -> str:
        """获取E/I形状"""
        if mbti and mbti[0] in ('E', 'e'):
            return E_SHAPE
        return I_SHAPE

    def _ease_out_quad(self, t: float) -> float:
        """缓动函数"""
        return 1 - (1 - t) * (1 - t)

    def update(self):
        """更新视图状态"""
        current_time = time.time()

        # 更新智能体位置动画
        for agent in self.agents.values():
            if agent.target_position and agent.start_position:
                elapsed = current_time - agent.move_start_time
                progress = min(1.0, elapsed / agent.move_duration)

                if progress < 1.0:
                    eased = self._ease_out_quad(progress)
                    start_x, start_y = agent.start_position
                    target_x, target_y = agent.target_position
                    agent.position = (
                        start_x + (target_x - start_x) * eased,
                        start_y + (target_y - start_y) * eased
                    )
                else:
                    agent.position = agent.target_position
                    agent.target_position = None
                    agent.start_position = None

            # 更新对话状态
            if agent.is_talking and current_time > agent.dialog_end_time:
                agent.is_talking = False
                agent.current_dialog = ""

        # 更新对话框
        self.dialogs = [d for d in self.dialogs if not d.is_expired]
        for dialog in self.dialogs:
            dialog.position = dialog.position  # 保持跟随
            dialog.update()

    def draw_map(self, surface: pygame.Surface):
        """绘制地图区域"""
        # 背景
        pygame.draw.rect(surface, self.map_bg_color, self.map_rect)

        # 绘制网格
        grid_size = 50
        for x in range(0, self.map_rect.width, grid_size):
            pygame.draw.line(surface, self.grid_color,
                           (x + self.map_rect.x, self.map_rect.y),
                           (x + self.map_rect.x, self.map_rect.bottom), 1)
        for y in range(0, self.map_rect.height, grid_size):
            pygame.draw.line(surface, self.grid_color,
                           (self.map_rect.x, y + self.map_rect.y),
                           (self.map_rect.right, y + self.map_rect.y), 1)

        # 绘制连接
        drawn_connections: Set[Tuple[str, str]] = set()
        for loc_name, connections in self.connections.items():
            loc = self.locations.get(loc_name)
            if not loc:
                continue
            pos1 = loc.position

            for conn_loc, distance in connections:
                # 避免重复绘制
                if (loc_name, conn_loc) in drawn_connections or (conn_loc, loc_name) in drawn_connections:
                    continue
                drawn_connections.add((loc_name, conn_loc))

                conn = self.locations.get(conn_loc)
                if not conn:
                    continue
                pos2 = conn.position

                # 绘制连接线
                pygame.draw.line(surface, (80, 84, 92), pos1, pos2, 3)

                # 绘制距离
                mid_x, mid_y = (pos1[0] + pos2[0]) // 2, (pos1[1] + pos2[1]) // 2
                dist_text = self.font.render(str(distance), True, (150, 150, 150))
                surface.blit(dist_text, (mid_x - 10, mid_y - 10))

        # 绘制位置
        for loc in self.locations.values():
            self._draw_location(surface, loc)

        # 绘制智能体
        for agent in self.agents.values():
            self._draw_agent(surface, agent)

        # 绘制对话气泡
        for dialog in self.dialogs:
            self._draw_dialog(surface, dialog)

    def _draw_location(self, surface: pygame.Surface, loc: LocationVisual):
        """绘制位置"""
        x, y = loc.position
        loc_type = loc.type

        # 获取颜色
        color = LOCATION_COLORS.get(loc_type, LOCATION_COLORS['default'])

        # 绘制建筑图标
        size = 30
        # 主体
        pygame.draw.rect(surface, color, (x - size//2, y - size//2, size, size), border_radius=5)

        # 房顶
        roof_points = [
            (x - size//2 - 3, y - size//2),
            (x + size//2 + 3, y - size//2),
            (x, y - size//2 - 15)
        ]
        pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in color), roof_points)

        # 绘制位置名称
        name_text = self.font.render(loc.name, True, (220, 220, 220))
        name_rect = name_text.get_rect(center=(x, y + size//2 + 15))
        surface.blit(name_text, name_rect)

        # 绘制智能体数量
        if loc.agents:
            count_text = self.font.render(f"({len(loc.agents)})", True, (180, 180, 180))
            count_rect = count_text.get_rect(center=(x, y + size//2 + 30))
            surface.blit(count_text, count_rect)

    def _draw_agent(self, surface: pygame.Surface, agent: AgentVisual):
        """绘制智能体"""
        x, y = agent.position
        shape = self.get_agent_shape(agent.mbti)
        base_color = agent.color

        # 心情光晕
        mood_alpha = int(abs(agent.mood_value) * 100)
        if agent.mood_value > 0:
            mood_color = (100, 255, 100)
        else:
            mood_color = (255, 100, 100)
        pygame.draw.circle(surface, mood_color + (mood_alpha,),
                          (int(x), int(y)), 20, 2)

        # 主体
        if shape == E_SHAPE:
            # 外向型 - 三角形
            points = [
                (x + 12, y),
                (x - 8, y - 10),
                (x - 8, y + 10)
            ]
            pygame.draw.polygon(surface, base_color, points)
        else:
            # 内向型 - 圆形
            pygame.draw.circle(surface, base_color, (int(x), int(y)), 12)

        # 名字标签
        name_text = self.font.render(agent.name, True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(x, y - 25))
        surface.blit(name_text, name_rect)

        # MBTI标签
        mbti_text = self.font.render(agent.mbti, True, (180, 180, 180))
        mbti_rect = mbti_text.get_rect(center=(x, y + 25))
        surface.blit(mbti_text, mbti_rect)

    def _draw_dialog(self, surface: pygame.Surface, dialog: DialogBubble):
        """绘制对话气泡"""
        x, y = dialog.position

        # 对话框尺寸
        box_width = 180
        box_height = 60
        box_x = int(x - box_width // 2)
        box_y = int(y - 80)

        # 背景
        dialog_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(dialog_surface, (255, 255, 255, int(240 * dialog.opacity / 255)),
                        (0, 0, box_width, box_height), border_radius=8)
        pygame.draw.rect(dialog_surface, dialog.agent_color + (int(200 * dialog.opacity / 255),),
                        (0, 0, box_width, box_height), 2, border_radius=8)

        # 名称
        name_color = (50, 50, 50) if dialog.opacity > 200 else (100, 100, 100)
        name_text = self.font.render(dialog.agent_name + ":", True, name_color)
        dialog_surface.blit(name_text, (8, 8))

        # 文字（分行）
        words = dialog.text.split(' ')
        lines = []
        line = ""
        for word in words:
            test_line = line + word + " "
            if self.font.size(test_line)[0] < box_width - 20:
                line = test_line
            else:
                lines.append(line)
                line = word + " "
        if line:
            lines.append(line)

        text_color = (30, 30, 30) if dialog.opacity > 200 else (80, 80, 80)
        for i, l in enumerate(lines[:2]):
            text = self.font.render(l, True, text_color)
            dialog_surface.blit(text, (8, 28 + i * 18))

        # 三角指向
        triangle_points = [
            (x, y - 5),
            (x - 8, box_y + box_height),
            (x + 8, box_y + box_height)
        ]
        pygame.draw.polygon(dialog_surface, (255, 255, 255, int(240 * dialog.opacity / 255)), triangle_points)

        surface.blit(dialog_surface, (box_x, box_y))

    def draw_panel(self, surface: pygame.Surface, selected_agent_id: Optional[str] = None):
        """绘制右侧信息面板"""
        # 背景
        pygame.draw.rect(surface, self.panel_bg_color, self.panel_rect)

        # 标题
        title = self.font_title.render("信息面板", True, (255, 255, 255))
        surface.blit(title, (self.panel_rect.x + 20, 20))

        # 绘制分隔线
        pygame.draw.line(surface, (60, 64, 72),
                        (self.panel_rect.x, 60),
                        (self.panel_rect.right, 60), 2)

        # 绘制智能体列表
        y_offset = 80
        list_title = self.font_large.render("智能体列表", True, (200, 200, 200))
        surface.blit(list_title, (self.panel_rect.x + 20, y_offset))
        y_offset += 30

        for agent in self.agents.values():
            is_selected = agent.id == selected_agent_id
            bg_color = (60, 70, 80) if is_selected else (50, 54, 62)

            # 智能体条目背景
            agent_rect = pygame.Rect(self.panel_rect.x + 15, y_offset,
                                    self.panel_rect.width - 30, 50)
            pygame.draw.rect(surface, bg_color, agent_rect, border_radius=5)

            # 颜色标记
            pygame.draw.rect(surface, agent.color, (agent_rect.x, agent_rect.y,
                            5, agent_rect.height), border_radius=2)

            # 名称和MBTI
            name_text = self.font.render(agent.name, True, (255, 255, 255))
            surface.blit(name_text, (agent_rect.x + 15, agent_rect.y + 8))

            mbti_text = self.font.render(agent.mbti, True, (180, 180, 180))
            surface.blit(mbti_text, (agent_rect.x + 15, agent_rect.y + 28))

            # 位置
            loc_name = "未知"
            for loc in self.locations.values():
                if agent.id in loc.agents:
                    loc_name = loc.name
                    break
            loc_text = self.font.render(loc_name, True, (150, 150, 150))
            surface.blit(loc_text, (agent_rect.right - 80, agent_rect.y + 18))

            y_offset += 55

        # 绘制选中智能体详情
        if selected_agent_id and selected_agent_id in self.agents:
            agent = self.agents[selected_agent_id]
            self._draw_agent_detail(surface, agent)

    def _draw_agent_detail(self, surface: pygame.Surface, agent: AgentVisual):
        """绘制智能体详情"""
        y_offset = 350
        panel_width = self.panel_rect.width - 40

        # 分隔线
        pygame.draw.line(surface, (60, 64, 72),
                        (self.panel_rect.x, y_offset),
                        (self.panel_rect.right, y_offset), 2)
        y_offset += 15

        # 标题
        title = self.font_large.render(f"详情: {agent.name}", True, (255, 255, 255))
        surface.blit(title, (self.panel_rect.x + 20, y_offset))
        y_offset += 35

        # ===== 基本信息 =====
        info_items = [
            ("MBTI", agent.mbti),
            ("状态", agent.status),
            ("心情", f"{agent.mood_desc} ({agent.mood_value:.2f})"),
        ]

        for label, value in info_items:
            label_text = self.font.render(f"{label}:", True, (150, 150, 150))
            value_text = self.font.render(str(value), True, (220, 220, 220))
            surface.blit(label_text, (self.panel_rect.x + 25, y_offset))
            surface.blit(value_text, (self.panel_rect.x + 90, y_offset))
            y_offset += 22

        # ===== 性格特点 =====
        if agent.personality_traits:
            y_offset += 5
            traits_label = self.font.render("性格:", True, (150, 150, 150))
            surface.blit(traits_label, (self.panel_rect.x + 25, y_offset))
            y_offset += 18
            traits_text = ", ".join(agent.personality_traits[:4])
            traits_surface = self.font.render(traits_text, True, (200, 200, 220))
            surface.blit(traits_surface, (self.panel_rect.x + 25, y_offset))
            y_offset += 20

        # ===== 心情条 =====
        y_offset += 5
        mood_label = self.font.render("心情:", True, (150, 150, 150))
        surface.blit(mood_label, (self.panel_rect.x + 25, y_offset))
        y_offset += 18

        bar_width = panel_width
        bar_height = 12
        bar_x = self.panel_rect.x + 25
        bar_y = y_offset

        pygame.draw.rect(surface, (60, 64, 72), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
        fill_width = int((agent.mood_value + 1) / 2 * bar_width)
        if agent.mood_value >= 0:
            pygame.draw.rect(surface, (100, 200, 100), (bar_x, bar_y, fill_width, bar_height), border_radius=3)
        else:
            pygame.draw.rect(surface, (200, 100, 100), (bar_x + bar_width - fill_width, bar_y, fill_width, bar_height), border_radius=3)
        y_offset += 20

        # ===== 财富状态 =====
        y_offset += 8
        wealth_label = self.font_large.render("财富状态", True, (200, 200, 200))
        surface.blit(wealth_label, (self.panel_rect.x + 20, y_offset))
        y_offset += 22

        wealth_items = [
            ("时间", agent.wealth.get("time", 0), (100, 180, 255)),
            ("社交", agent.wealth.get("social", 0), (100, 200, 150)),
            ("健康", agent.wealth.get("health", 0.5), (255, 150, 100)),
            ("精神", agent.wealth.get("mental", 0.5), (180, 100, 255)),
            ("金钱", agent.wealth.get("money", 0), (255, 215, 0)),
        ]

        for w_name, w_value, w_color in wealth_items:
            # 标签
            w_label = self.font.render(f"{w_name}:", True, (150, 150, 150))
            surface.blit(w_label, (self.panel_rect.x + 25, y_offset))

            # 进度条
            bar_x = self.panel_rect.x + 80
            bar_width = panel_width - 80
            bar_height = 10

            pygame.draw.rect(surface, (50, 54, 62), (bar_x, y_offset, bar_width, bar_height), border_radius=2)

            if w_name == "金钱":
                # 金钱特殊处理，显示具体数值
                money_text = self.font.render(f"¥{int(w_value):,}", True, w_color)
                surface.blit(money_text, (bar_x + bar_width + 5, y_offset - 2))
            else:
                # 进度
                fill_width = int((w_value + 1) / 2 * (bar_width - 40))
                if w_value >= 0:
                    pygame.draw.rect(surface, w_color, (bar_x, y_offset, max(0, fill_width), bar_height), border_radius=2)
                else:
                    pygame.draw.rect(surface, (150, 80, 80), (bar_x + bar_width//2 - max(0, -fill_width), y_offset, max(0, -fill_width), bar_height), border_radius=2)

                # 数值
                value_text = self.font.render(f"{w_value:.2f}", True, (180, 180, 180))
                surface.blit(value_text, (bar_x + bar_width - 35, y_offset))

            y_offset += 20

        # ===== 记忆统计 =====
        y_offset += 8
        memory_label = self.font_large.render("记忆", True, (200, 200, 200))
        surface.blit(memory_label, (self.panel_rect.x + 20, y_offset))
        y_offset += 22

        mem_items = [
            ("短期记忆", agent.short_term_memory_count, (255, 180, 100)),
            ("长期记忆", agent.long_term_memory_count, (100, 180, 255)),
        ]
        for m_name, m_count, m_color in mem_items:
            m_label = self.font.render(f"{m_name}:", True, (150, 150, 150))
            surface.blit(m_label, (self.panel_rect.x + 25, y_offset))
            count_text = self.font.render(str(m_count), True, m_color)
            surface.blit(count_text, (self.panel_rect.x + 110, y_offset))
            y_offset += 20

        # ===== 近期记忆预览 =====
        if agent.recent_memories:
            y_offset += 8
            recent_label = self.font_large.render("近期记忆", True, (200, 200, 200))
            surface.blit(recent_label, (self.panel_rect.x + 20, y_offset))
            y_offset += 22

            for i, memory in enumerate(agent.recent_memories[:3]):
                # 记忆条目背景
                mem_rect = pygame.Rect(self.panel_rect.x + 25, y_offset,
                                      panel_width, 35)
                pygame.draw.rect(surface, (50, 54, 62), mem_rect, border_radius=3)

                # 记忆内容
                if len(memory) > 35:
                    memory = memory[:35] + "..."
                mem_text = self.font.render(memory, True, (180, 180, 180))
                surface.blit(mem_text, (mem_rect.x + 8, mem_rect.y + 8))
                y_offset += 40

        # ===== 当前对话 =====
        if agent.current_dialog:
            y_offset += 10
            dialog_label = self.font_large.render("当前对话", True, (200, 200, 200))
            surface.blit(dialog_label, (self.panel_rect.x + 20, y_offset))
            y_offset += 22

            # 对话框
            dialog_rect = pygame.Rect(self.panel_rect.x + 25, y_offset,
                                      panel_width, 50)
            pygame.draw.rect(surface, (50, 54, 62), dialog_rect, border_radius=5)
            pygame.draw.rect(surface, agent.color, dialog_rect, 2, border_radius=5)

            # 对话文字
            words = agent.current_dialog.split(' ')
            lines = []
            line = ""
            for word in words:
                test_line = line + word + " "
                if self.font.size(test_line)[0] < dialog_rect.width - 20:
                    line = test_line
                else:
                    lines.append(line)
                    line = word + " "
            if line:
                lines.append(line)

            for i, l in enumerate(lines[:2]):
                text = self.font.render(l, True, (220, 220, 220))
                surface.blit(text, (dialog_rect.x + 10, dialog_rect.y + 10 + i * 18))

    def draw_control_bar(self, surface: pygame.Surface, is_paused: bool, speed: float):
        """绘制底部控制栏"""
        bar_height = 60
        bar_rect = pygame.Rect(0, self.height - bar_height, self.width, bar_height)

        # 背景
        pygame.draw.rect(surface, (35, 38, 45), bar_rect)

        # 分隔线
        pygame.draw.line(surface, (60, 64, 72),
                        (0, bar_rect.top),
                        (bar_rect.right, bar_rect.top), 2)

        # 返回按钮 (左上角)
        btn_width = 100
        btn_height = 35
        btn_x = 15
        btn_y = bar_rect.y + (bar_height - btn_height) // 2

        return_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(surface, (150, 80, 80), return_rect, border_radius=5)
        return_text = self.font.render("返回", True, (255, 255, 255))
        return_rect_center = return_text.get_rect(center=return_rect.center)
        surface.blit(return_text, return_rect_center)

        # 播放/暂停按钮
        pause_btn_x = btn_x + btn_width + 20
        pause_rect = pygame.Rect(pause_btn_x, btn_y, 80, btn_height)
        pygame.draw.rect(surface, (70, 130, 180), pause_rect, border_radius=5)
        pause_text = self.font.render("暂停" if not is_paused else "播放", True, (255, 255, 255))
        pause_rect_center = pause_text.get_rect(center=pause_rect.center)
        surface.blit(pause_text, pause_rect_center)

        # 速度按钮
        speed_x = pause_btn_x + 100
        for i, (spd, label) in enumerate([(1.0, "1x"), (2.0, "2x"), (4.0, "4x")]):
            spd_rect = pygame.Rect(speed_x + i * 70, btn_y, 60, btn_height)
            is_active = abs(speed - spd) < 0.1
            color = (70, 130, 180) if is_active else (60, 64, 72)
            pygame.draw.rect(surface, color, spd_rect, border_radius=5)
            spd_text = self.font.render(label, True, (255, 255, 255))
            spd_rect_center = spd_text.get_rect(center=spd_rect.center)
            surface.blit(spd_text, spd_rect_center)

        # 单步按钮
        step_x = speed_x + 230
        step_rect = pygame.Rect(step_x, btn_y, 80, btn_height)
        pygame.draw.rect(surface, (80, 100, 80), step_rect, border_radius=5)
        step_text = self.font.render("单步", True, (255, 255, 255))
        step_rect_center = step_text.get_rect(center=step_rect.center)
        surface.blit(step_text, step_rect_center)

        # 统计信息
        stats_text = self.font.render(
            f"智能体: {len(self.agents)} | 位置: {len(self.locations)}",
            True, (180, 180, 180)
        )
        surface.blit(stats_text, (self.width - 250, bar_rect.y + 20))

    def draw(self, selected_agent_id: Optional[str] = None,
             is_paused: bool = False, speed: float = 1.0):
        """绘制整个视图"""
        # 清屏
        self.screen.fill(self.bg_color)

        # 绘制地图
        self.draw_map(self.screen)

        # 绘制信息面板
        self.draw_panel(self.screen, selected_agent_id)

        # 绘制控制栏
        self.draw_control_bar(self.screen, is_paused, speed)

        # 更新显示
        pygame.display.flip()

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """处理事件，返回可选的操作类型"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # 检查控制栏按钮
                bar_height = 60
                bar_rect = pygame.Rect(0, self.height - bar_height, self.width, bar_height)

                if bar_rect.collidepoint(event.pos):
                    return self._handle_control_click(event.pos)

                # 检查信息面板中的智能体列表点击
                panel_y = 110
                for agent in self.agents.values():
                    agent_rect = pygame.Rect(self.panel_rect.x + 15, panel_y,
                                           self.panel_rect.width - 30, 50)
                    if agent_rect.collidepoint(event.pos):
                        return f"select:{agent.id}"
                    panel_y += 55

        elif event.type == pygame.MOUSEMOTION:
            if event.buttons[0]:  # 左键拖动
                dx = event.pos[0] - self.last_mouse_pos[0]
                dy = event.pos[1] - self.last_mouse_pos[1]
                self.camera_offset[0] += dx
                self.camera_offset[1] += dy
            self.last_mouse_pos = event.pos

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                return "toggle_pause"
            elif event.key == pygame.K_1:
                return "speed:1.0"
            elif event.key == pygame.K_2:
                return "speed:2.0"
            elif event.key == pygame.K_3:
                return "speed:4.0"
            elif event.key == pygame.K_s:
                return "step"

        return None

    def _handle_control_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """处理控制栏点击"""
        bar_height = 60
        bar_rect = pygame.Rect(0, self.height - bar_height, self.width, bar_height)
        btn_y = bar_rect.y + (bar_height - 35) // 2

        # 返回按钮 (最左边)
        return_rect = pygame.Rect(15, btn_y, 100, 35)
        if return_rect.collidepoint(pos):
            return "return_to_menu"

        # 播放/暂停按钮
        pause_rect = pygame.Rect(135, btn_y, 80, 35)
        if pause_rect.collidepoint(pos):
            return "toggle_pause"

        # 速度按钮
        speed_x = 235
        for spd, label in [(1.0, "1x"), (2.0, "2x"), (4.0, "4x")]:
            spd_rect = pygame.Rect(speed_x, btn_y, 60, 35)
            if spd_rect.collidepoint(pos):
                return f"speed:{spd}"
            speed_x += 70

        # 单步按钮
        step_rect = pygame.Rect(speed_x + 30, btn_y, 80, 35)
        if step_rect.collidepoint(pos):
            return "step"

        return None

    def get_clicked_agent(self, pos: Tuple[int, int]) -> Optional[str]:
        """获取点击位置下的智能体ID"""
        for agent in self.agents.values():
            dx = agent.position[0] - pos[0]
            dy = agent.position[1] - pos[1]
            if dx*dx + dy*dy < 400:  # 20像素半径
                return agent.id
        return None

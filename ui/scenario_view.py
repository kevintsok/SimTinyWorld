"""
Scenario View - 场景视图

继承自GameView的核心渲染逻辑，新增智能体详情开关功能，
允许用户在基本信息模式和完整详情模式之间切换。

主要功能:
- 地图渲染（位置、智能体、连接线）
- 对话气泡
- 时间线
- 控制栏（播放/暂停/速度/单步/返回）
- 信息面板（含智能体详情开关）
- 智能体详情折叠/展开
"""

import pygame
import math
import time
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass
from ui.fonts import get_font
from ui.components import TextBox

# 复用 game_view 中的常量
from ui.game_view import (
    MBTI_COLORS,
    ERA_THEMES,
    LOCATION_COLORS,
    LOCATION_ICONS,
    E_SHAPE,
    I_SHAPE,
    AgentVisual,
    LocationVisual,
    DialogBubble,
)


@dataclass
class ScenarioViewInterface:
    """场景视图回调接口

    用于ScenarioView与外部系统通信的接口定义。
    """
    on_agent_selected: Callable[[str], None] = None           # 智能体被选中
    on_agent_detail_toggle: Callable[[bool], None] = None     # 详情显示状态变化
    on_return_to_menu: Callable[[], None] = None              # 返回主菜单
    on_simulation_control: Callable[[str, Any], None] = None   # 模拟控制（暂停/速度等）
    on_save_session: Callable[[], bool] = None                 # 保存当前Session
    on_load_session: Callable[[], None] = None                # 加载Session


class ScenarioView:
    """场景视图 - 继承GameView核心功能并增强详情显示控制"""

    def __init__(self, width: int = 1000, height: int = 700,
                 interface: ScenarioViewInterface = None,
                 screen: pygame.Surface = None):
        """初始化场景视图

        Args:
            width: 窗口宽度
            height: 窗口高度
            interface: 回调接口，用于与外部系统通信
            screen: pygame surface，如果不传则使用display.get_surface()
        """
        pygame.init()
        self.width = width
        self.height = height
        self.interface = interface or ScenarioViewInterface()

        # 使用传入的screen或获取当前display的surface
        if screen is None:
            self.screen = pygame.display.get_surface()
        else:
            self.screen = screen

        # 加载字体
        self.font = get_font(14)
        self.font_large = get_font(18)
        self.font_title = get_font(24)
        self.small_font = get_font(12)  # 表格用小字体

        # 时钟
        self.clock = pygame.time.Clock()

        # 数据
        self.agents: Dict[str, AgentVisual] = {}
        self.locations: Dict[str, LocationVisual] = {}
        self.dialogs: List[DialogBubble] = []
        self.connections: Dict[str, List[Tuple[str, int]]] = {}

        # 动画
        self.camera_offset = [0, 0]
        self.is_dragging = False
        self.last_mouse_pos = (0, 0)

        # 地图区域 (左侧)
        self.map_rect = pygame.Rect(0, 0, int(width * 0.65), height)

        # 信息面板区域 (右侧)
        self.panel_rect = pygame.Rect(int(width * 0.65), 0, int(width * 0.35), height)

        self.show_agent_details: bool = True
        self.selected_agent_id: Optional[str] = None
        self.detail_collapse_offset: float = 0.0
        self.detail_collapse_target: float = 0.0
        self.detail_collapse_speed: float = 0.15
        self.detail_scroll_offset: int = 0
        self.detail_content_height: int = 0

        self.detail_toggle_rect: Optional[pygame.Rect] = None

        # 时代主题
        self.current_era = "default"
        self._apply_era_theme("default")

        # 场景信息
        self.scenario_name = "智能体模拟"
        self.scenario_description = ""
        self.scenario_goals: List[str] = []
        self.scenario_type = "dialogue"

        # 时间线
        self.current_day = 1
        self.current_round = 1
        self.max_rounds = 10
        self.total_dialogue_count = 0  # 累计对话次数
        self.events: List[Dict[str, Any]] = []
        self.triggered_events: Set[int] = set()
        self.event_notifications: List[Dict[str, Any]] = []

        # 顶部信息栏高度
        self.header_height = 50

        # ===== 每日交互轮数输入框 =====
        self.interact_rounds: int = 5  # 默认每日5轮交互
        interact_rounds_rect = pygame.Rect(
            self.width - 380,  # x position (left of stats)
            self.height - 45,  # y position in control bar
            80, 30
        )
        self.interact_rounds_input = TextBox(interact_rounds_rect, "", max_length=3)
        self.interact_rounds_input.text = str(self.interact_rounds)  # 设置初始值

    def _on_end_today_clicked(self):
        """结束今天按钮点击处理"""
        if self.interface.on_simulation_control:
            self.interface.on_simulation_control("end_day", None)

    def get_interact_rounds(self) -> int:
        """获取每日交互轮数"""
        text = self.interact_rounds_input.text.strip()
        if text.isdigit() and int(text) > 0:
            return int(text)
        return self.interact_rounds

    def set_interact_rounds(self, rounds: int):
        """设置每日交互轮数"""
        self.interact_rounds = max(1, rounds)
        self.interact_rounds_input.text = str(self.interact_rounds)

    def _apply_era_theme(self, era: str):
        """应用时代主题配色"""
        theme = ERA_THEMES.get(era, ERA_THEMES["default"])
        self.current_era = era
        self.bg_color = theme["bg"]
        self.map_bg_color = theme["map_bg"]
        self.panel_bg_color = theme["panel_bg"]
        self.grid_color = theme["grid"]
        self.accent_color = theme["accent"]
        self.primary_color = theme["primary"]

    def set_scenario_info(self, name: str, description: str = "", goals: List[str] = None,
                         scenario_type: str = "dialogue", era: str = "default",
                         max_rounds: int = 10):
        """设置场景信息"""
        self.scenario_name = name
        self.scenario_description = description
        self.scenario_goals = goals or []
        self.scenario_type = scenario_type
        self.max_rounds = max_rounds
        self.current_round = 1
        self._apply_era_theme(era)

    def add_event(self, round_num: int, content: str, participants: List[str] = None):
        """添加事件到时间线"""
        self.events.append({
            "round": round_num,
            "content": content,
            "participants": participants or []
        })

    def set_round(self, round_num: int):
        """设置当前轮数"""
        self.current_round = round_num

    def set_day(self, day: int):
        """设置当前天数"""
        self.current_day = day

    def set_total_dialogue_count(self, count: int):
        """设置累计对话次数"""
        self.total_dialogue_count = count

    def trigger_event(self, event_index: int) -> Optional[Dict[str, Any]]:
        """触发事件"""
        if event_index in self.triggered_events:
            return None

        if event_index < len(self.events):
            event = self.events[event_index]
            self.triggered_events.add(event_index)
            self.event_notifications.append({
                "content": event["content"],
                "start_time": time.time(),
                "duration": 4.0
            })
            return event
        return None

    def update_events(self):
        """更新事件通知"""
        current_time = time.time()
        self.event_notifications = [
            n for n in self.event_notifications
            if current_time - n["start_time"] < n["duration"]
        ]

    def set_locations(self, locations: Dict[str, dict], connections: Dict[str, List[Tuple[str, int]]]):
        """设置位置数据"""
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
                  long_term_memory_count: int = 0, short_term_memory_count: int = 0,
                  short_term_memories: List[str] = None, long_term_memories: List[str] = None,
                  role: str = "", era: str = "", goals: List[str] = None,
                  historical_name: str = ""):
        """添加智能体"""
        loc = self.locations.get(location)
        pos = loc.position if loc else (400, 300)
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
            wealth=wealth if wealth is not None else {"time": 0, "social": 0, "health": 0.5, "mental": 0.5, "money": 0},
            recent_memories=recent_memories or [],
            personality_traits=personality_traits or [],
            core_values=core_values or [],
            long_term_memory_count=long_term_memory_count,
            short_term_memory_count=short_term_memory_count,
            short_term_memories=short_term_memories or [],
            long_term_memories=long_term_memories or [],
            role=role,
            era=era,
            goals=goals or [],
            historical_name=historical_name or name
        )

        if location in self.locations:
            self.locations[location].agents.add(agent_id)

    def move_agent(self, agent_id: str, from_location: str, to_location: str, duration: float = 1.0):
        """移动智能体"""
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
                         short_term_memory_count: int = None,
                         short_term_memories: List[str] = None, long_term_memories: List[str] = None):
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
        if short_term_memories is not None:
            agent.short_term_memories = short_term_memories
        if long_term_memories is not None:
            agent.long_term_memories = long_term_memories

    def show_dialog(self, agent_id: str, text: str, duration: float = 3.0):
        """显示对话气泡"""
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

    def _ease_in_out_quad(self, t: float) -> float:
        """缓入缓出函数"""
        if t < 0.5:
            return 2 * t * t
        return 1 - pow(-2 * t + 2, 2) / 2

    def update(self):
        """更新视图状态"""
        self.update_events()

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

            if agent.is_talking and current_time > agent.dialog_end_time:
                agent.is_talking = False
                agent.current_dialog = ""

        # 更新对话框
        self.dialogs = [d for d in self.dialogs if not d.is_expired]
        for dialog in self.dialogs:
            dialog.update()

        # 更新详情折叠动画
        self._update_collapse_animation()

    def _update_collapse_animation(self):
        """更新详情折叠动画"""
        if abs(self.detail_collapse_offset - self.detail_collapse_target) > 0.01:
            # 动画方向
            if self.detail_collapse_offset < self.detail_collapse_target:
                self.detail_collapse_offset = min(
                    self.detail_collapse_target,
                    self.detail_collapse_offset + self.detail_collapse_speed
                )
            else:
                self.detail_collapse_offset = max(
                    self.detail_collapse_target,
                    self.detail_collapse_offset - self.detail_collapse_speed
                )

    def set_agent_selected(self, agent_id: Optional[str]):
        """设置选中的智能体"""
        self.selected_agent_id = agent_id
        if self.interface.on_agent_selected and agent_id:
            self.interface.on_agent_selected(agent_id)

    def toggle_agent_details(self):
        """切换智能体详情显示状态"""
        self.show_agent_details = not self.show_agent_details
        # 设置折叠动画目标
        self.detail_collapse_target = 1.0 if not self.show_agent_details else 0.0
        if self.interface.on_agent_detail_toggle:
            self.interface.on_agent_detail_toggle(self.show_agent_details)

    def set_agent_details_visible(self, visible: bool):
        """设置智能体详情是否显示"""
        if self.show_agent_details != visible:
            self.show_agent_details = visible
            self.detail_collapse_target = 0.0 if visible else 1.0
            if self.interface.on_agent_detail_toggle:
                self.interface.on_agent_detail_toggle(visible)

    def draw_map(self, surface: pygame.Surface):
        """绘制地图区域"""
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
                if (loc_name, conn_loc) in drawn_connections or (conn_loc, loc_name) in drawn_connections:
                    continue
                drawn_connections.add((loc_name, conn_loc))

                conn = self.locations.get(conn_loc)
                if not conn:
                    continue
                pos2 = conn.position

                pygame.draw.line(surface, (80, 84, 92), pos1, pos2, 3)

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
        icon_type = LOCATION_ICONS.get(loc_type, "default")

        color = LOCATION_COLORS.get(loc_type, LOCATION_COLORS.get('default'))
        dark_color = tuple(max(0, c - 40) for c in color)
        size = 32

        # 根据图标类型绘制（复用GameView逻辑）
        if icon_type == "palace":
            pygame.draw.rect(surface, color, (x - size//2, y - size//3, size, size//2), border_radius=2)
            roof_points = [
                (x - size//2 - 5, y - size//3),
                (x + size//2 + 5, y - size//3),
                (x, y - size - 10)
            ]
            pygame.draw.polygon(surface, dark_color, roof_points)
            for i in range(3):
                pygame.draw.rect(surface, dark_color, (x - size//2 + i*5, y + size//3 + i*3, size - i*10, 3))

        elif icon_type == "temple":
            pygame.draw.rect(surface, color, (x - size//2, y - size//2, size, size), border_radius=2)
            roof_points = [
                (x - size//2 - 3, y - size//2),
                (x + size//2 + 3, y - size//2),
                (x, y - size - 5)
            ]
            pygame.draw.polygon(surface, dark_color, roof_points)
            for col_x in [x - 12, x, x + 12]:
                pygame.draw.rect(surface, (200, 200, 200), (col_x - 2, y - size//3, 4, size//2))

        elif icon_type == "castle":
            pygame.draw.rect(surface, color, (x - size//2, y - size//3, size, size//2 + size//3))
            pygame.draw.polygon(surface, dark_color, [
                (x - size//2 - 3, y - size//3),
                (x + size//2 + 3, y - size//3),
                (x, y - size - 5)
            ])
            pygame.draw.line(surface, (255, 200, 100), (x, y - size - 5), (x, y - size - 20), 2)
            pygame.draw.polygon(surface, (200, 50, 50), [(x, y - size - 20), (x + 10, y - size - 15), (x, y - size - 10)])

        elif icon_type == "market":
            pygame.draw.rect(surface, color, (x - size//2, y, size, size//3), border_radius=2)
            roof_points = [
                (x - size//2 - 5, y),
                (x + size//2 + 5, y),
                (x, y - size//2)
            ]
            pygame.draw.polygon(surface, dark_color, roof_points)

        elif icon_type == "wall":
            pygame.draw.rect(surface, color, (x - size//2, y - size//3, size, size//2))
            for i in range(5):
                pygame.draw.rect(surface, dark_color, (x - size//2 + i*8, y - size//2, 6, 8))

        elif icon_type == "battlefield":
            pygame.draw.rect(surface, color, (x - size//2, y - size//4, size, size//2), border_radius=3)
            pygame.draw.line(surface, (200, 200, 200), (x - 10, y - 10), (x + 10, y + 10), 3)
            pygame.draw.line(surface, (200, 200, 200), (x + 10, y - 10), (x - 10, y + 10), 3)

        elif icon_type == "port":
            pygame.draw.rect(surface, color, (x - size//2, y - size//4, size, size//2), border_radius=2)
            pygame.draw.circle(surface, (200, 200, 200), (x, y - 5), 6, 2)
            pygame.draw.line(surface, (200, 200, 200), (x, y), (x, y + 12), 2)
            pygame.draw.line(surface, (200, 200, 200), (x - 6, y + 10), (x + 6, y + 10), 2)

        elif icon_type == "mansion":
            pygame.draw.rect(surface, color, (x - size//2, y - size//3, size, size//2 + size//6))
            roof_points = [
                (x - size//2 - 2, y - size//3),
                (x + size//2 + 2, y - size//3),
                (x, y - size - 3)
            ]
            pygame.draw.polygon(surface, dark_color, roof_points)

        elif icon_type == "cross":
            pygame.draw.rect(surface, color, (x - size//2, y - size//4, size, size//2), border_radius=2)
            pygame.draw.rect(surface, (255, 255, 255), (x - 3, y - size//2, 6, size))

        elif icon_type == "tree":
            pygame.draw.circle(surface, (60, 179, 113), (x, y - 5), size//3)
            pygame.draw.rect(surface, (139, 90, 43), (x - 4, y, 8, size//3))

        elif icon_type == "building":
            pygame.draw.rect(surface, color, (x - size//2, y - size//3, size, size//2 + size//3), border_radius=2)
            for wx in [x - 8, x, x + 8]:
                pygame.draw.rect(surface, (200, 220, 255), (wx - 3, y - size//4, 6, 8))

        else:
            pygame.draw.rect(surface, color, (x - size//2, y - size//3, size, size//2 + size//6), border_radius=3)
            roof_points = [
                (x - size//2 - 2, y - size//3),
                (x + size//2 + 2, y - size//3),
                (x, y - size - 5)
            ]
            pygame.draw.polygon(surface, dark_color, roof_points)

        # 绘制位置名称
        name_text = self.font.render(loc.name, True, (220, 220, 220))
        name_rect = name_text.get_rect(center=(x, y + size//2 + 18))
        surface.blit(name_text, name_rect)

        if loc.agents:
            count_text = self.font.render(f"({len(loc.agents)})", True, (180, 180, 180))
            count_rect = count_text.get_rect(center=(x, y + size//2 + 33))
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
            points = [
                (x + 12, y),
                (x - 8, y - 10),
                (x - 8, y + 10)
            ]
            pygame.draw.polygon(surface, base_color, points)
        else:
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

        box_width = 180
        box_height = 60
        box_x = int(x - box_width // 2)
        box_y = int(y - 80)

        dialog_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(dialog_surface, (255, 255, 255, int(240 * dialog.opacity / 255)),
                        (0, 0, box_width, box_height), border_radius=8)
        pygame.draw.rect(dialog_surface, dialog.agent_color + (int(200 * dialog.opacity / 255),),
                        (0, 0, box_width, box_height), 2, border_radius=8)

        name_color = (50, 50, 50) if dialog.opacity > 200 else (100, 100, 100)
        name_text = self.font.render(dialog.agent_name + ":", True, name_color)
        dialog_surface.blit(name_text, (8, 8))

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

        triangle_points = [
            (x, y - 5),
            (x - 8, box_y + box_height),
            (x + 8, box_y + box_height)
        ]
        pygame.draw.polygon(dialog_surface, (255, 255, 255, int(240 * dialog.opacity / 255)), triangle_points)

        surface.blit(dialog_surface, (box_x, box_y))

    def draw_header(self, surface: pygame.Surface):
        """绘制顶部场景信息栏"""
        header_rect = pygame.Rect(0, 0, self.width, self.header_height)

        pygame.draw.rect(surface, self.panel_bg_color, header_rect)

        pygame.draw.line(surface, self.accent_color,
                        (0, header_rect.bottom - 1),
                        (header_rect.right, header_rect.bottom - 1), 2)

        name_text = self.font_title.render(self.scenario_name, True, (255, 255, 255))
        surface.blit(name_text, (20, 12))

        type_labels = {
            "dialogue": "对话",
            "debate": "辩论",
            "cooperation": "协作",
            "emergency": "突发事件",
            "daily_life": "日常生活"
        }
        type_text = self.font.render(f"[{type_labels.get(self.scenario_type, self.scenario_type)}]", True, self.accent_color)
        surface.blit(type_text, (name_text.get_width() + 30, 18))

        # 统计信息显示在右上角（进度条上方，不被详情面板挡住）
        stats_text = self.font.render(
            f"第{self.current_day}天 | 轮数:{self.current_round}/{self.interact_rounds} | 对话:{self.total_dialogue_count} | 智能体:{len(self.agents)}",
            True, (180, 180, 180)
        )
        # 放在右上角，但不超过详情面板的边界
        panel_left = self.panel_rect.x - 10  # 详情面板左边
        stats_rect = stats_text.get_rect(right=panel_left, top=8)
        surface.blit(stats_text, stats_rect)

        round_text = self.font.render(f"第 {self.current_round} / {self.max_rounds} 轮", True, (200, 200, 200))
        round_rect = round_text.get_rect(right=self.width - 20, centery=self.header_height // 2)
        surface.blit(round_text, round_rect)

        progress_width = 150
        progress_x = round_rect.left - progress_width - 20
        progress_y = self.header_height // 2 - 5

        pygame.draw.rect(surface, (60, 64, 72), (progress_x, progress_y, progress_width, 10), border_radius=3)
        fill_width = int(self.current_round / self.max_rounds * progress_width)
        pygame.draw.rect(surface, self.accent_color, (progress_x, progress_y, fill_width, 10), border_radius=3)

    def draw_timeline(self, surface: pygame.Surface):
        """绘制时间线面板"""
        timeline_height = 60
        timeline_rect = pygame.Rect(0, self.header_height, self.map_rect.width, timeline_height)

        pygame.draw.rect(surface, self.map_bg_color, timeline_rect)
        pygame.draw.line(surface, self.grid_color,
                        (0, timeline_rect.bottom),
                        (timeline_rect.right, timeline_rect.bottom), 1)

        label = self.font.render("时间线:", True, (150, 150, 150))
        surface.blit(label, (15, timeline_rect.y + 8))

        node_y = timeline_rect.y + 35
        node_spacing = min(80, (timeline_rect.width - 100) // max(self.max_rounds, 1))
        start_x = 80

        for i in range(1, self.max_rounds + 1):
            node_x = start_x + (i - 1) * node_spacing

            is_past = i < self.current_round
            is_current = i == self.current_round
            is_future = i > self.current_round

            if is_past:
                color = self.accent_color
            elif is_current:
                color = (255, 255, 255)
            else:
                color = (80, 80, 80)

            pygame.draw.circle(surface, color, (node_x, node_y), 8)

            if is_current:
                pygame.draw.circle(surface, self.accent_color, (node_x, node_y), 12, 2)

            round_num = self.font.render(str(i), True, (200, 200, 200) if is_future else (50, 50, 50))
            round_rect = round_num.get_rect(center=(node_x, node_y + 20))
            surface.blit(round_num, round_rect)

            has_event = any(e.get("round") == i for e in self.events)
            if has_event:
                event_color = (255, 200, 100) if is_past or is_current else (100, 100, 100)
                pygame.draw.circle(surface, event_color, (node_x, node_y), 4)

        for i in range(1, self.max_rounds):
            x1 = start_x + (i - 1) * node_spacing
            x2 = start_x + i * node_spacing
            is_past = i < self.current_round
            line_color = self.accent_color if is_past else (60, 60, 60)
            pygame.draw.line(surface, line_color, (x1 + 8, node_y), (x2 - 8, node_y), 2)

    def draw_event_notifications(self, surface: pygame.Surface):
        """绘制事件通知弹窗"""
        for i, notif in enumerate(self.event_notifications):
            elapsed = time.time() - notif["start_time"]
            fade_start = notif["duration"] - 1.0

            if elapsed > fade_start:
                alpha = int(255 * (notif["duration"] - elapsed))
            else:
                alpha = 255
            alpha = max(0, min(255, alpha))

            box_width = 400
            box_height = 60
            box_x = (self.width - box_width) // 2
            box_y = 80 + i * 70

            notif_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            pygame.draw.rect(notif_surface, (40, 44, 52, alpha),
                           (0, 0, box_width, box_height), border_radius=8)
            pygame.draw.rect(notif_surface, (self.accent_color[0], self.accent_color[1], self.accent_color[2], alpha),
                           (0, 0, box_width, box_height), 2, border_radius=8)

            event_text = self.font_large.render(notif["content"], True, (255, 255, 255))
            event_rect = event_text.get_rect(center=(box_width // 2, box_height // 2))
            notif_surface.blit(event_text, event_rect)

            surface.blit(notif_surface, (box_x, box_y))

    def draw_panel(self, surface: pygame.Surface):
        """绘制右侧信息面板（含详情开关）"""
        # 背景
        pygame.draw.rect(surface, self.panel_bg_color, self.panel_rect)

        # 标题
        title = self.font_title.render("信息面板", True, (255, 255, 255))
        surface.blit(title, (self.panel_rect.x + 20, 20))

        # 分隔线
        pygame.draw.line(surface, (60, 64, 72),
                        (self.panel_rect.x, 60),
                        (self.panel_rect.right, 60), 2)

        # ===== 绘制详情开关按钮 =====
        self._draw_detail_toggle(surface)

        # 绘制智能体列表（固定高度，不与详情区域重叠）
        list_height = 200  # 智能体列表最大高度
        self._draw_agent_list(surface, max_height=list_height)

        # 绘制选中智能体详情（根据开关状态）
        if self.selected_agent_id and self.selected_agent_id in self.agents:
            agent = self.agents[self.selected_agent_id]
            # 根据开关状态绘制对应版本的详情
            if self.show_agent_details:
                self._draw_agent_detail(surface, agent)
            else:
                self._draw_agent_detail_compact(surface, agent)

    def _draw_detail_toggle(self, surface: pygame.Surface):
        """绘制详情开关按钮"""
        y_offset = 70

        # 开关容器背景
        toggle_bg_rect = pygame.Rect(self.panel_rect.x + 15, y_offset,
                                     self.panel_rect.width - 30, 35)
        pygame.draw.rect(surface, (50, 54, 62), toggle_bg_rect, border_radius=5)

        # 开关标签
        label_text = self.font.render("显示详情:", True, (180, 180, 180))
        surface.blit(label_text, (toggle_bg_rect.x + 10, toggle_bg_rect.y + 8))

        # 开关按钮
        toggle_width = 50
        toggle_height = 22
        toggle_x = toggle_bg_rect.right - toggle_width - 10
        toggle_y = toggle_bg_rect.y + (35 - toggle_height) // 2

        # 开关背景
        bg_color = (70, 130, 180) if self.show_agent_details else (80, 80, 80)
        pygame.draw.rect(surface, bg_color, (toggle_x, toggle_y, toggle_width, toggle_height), border_radius=11)

        # 开关滑块
        knob_x = toggle_x + toggle_width - 4 - 16 if self.show_agent_details else toggle_x + 4
        pygame.draw.circle(surface, (255, 255, 255), (knob_x + 10, toggle_y + toggle_height // 2), 9)

        # 保存开关区域供点击检测
        self.detail_toggle_rect = pygame.Rect(toggle_x, toggle_y, toggle_width, toggle_height)

        # 状态文字
        status_text = "开" if self.show_agent_details else "关"
        status_color = (255, 255, 255) if self.show_agent_details else (150, 150, 150)
        status_surface = self.font.render(status_text, True, status_color)
        # 在开关旁边显示
        surface.blit(status_surface, (toggle_x - 30, toggle_y + 2))

    def _draw_agent_list(self, surface: pygame.Surface, max_height: int = 200) -> int:
        """绘制智能体列表（表格形式）

        Args:
            surface: 绘制表面
            max_height: 列表区域最大高度
        """
        y_offset = 115

        # 列配置：名称、MBTI、心情、财富(时间)、财富(社交)、体力、位置
        # 每列宽度
        col_widths = [80, 50, 50, 55, 55, 50, 60]  # 总和约等于panel宽度
        col_names = ["名称", "MBTI", "心情", "时间", "社交", "体力", "位置"]

        # 表头背景
        header_rect = pygame.Rect(self.panel_rect.x + 10, y_offset,
                                 self.panel_rect.width - 20, 25)
        pygame.draw.rect(surface, (40, 44, 52), header_rect, border_radius=3)

        # 绘制表头
        x_offset = self.panel_rect.x + 15
        for i, col_name in enumerate(col_names):
            col_text = self.small_font.render(col_name, True, (180, 180, 180))
            surface.blit(col_text, (x_offset, y_offset + 6))
            x_offset += col_widths[i]

        y_offset += 28

        # 绘制每个智能体行
        for agent in self.agents.values():
            is_selected = agent.id == self.selected_agent_id
            row_height = 28
            bg_color = (50, 60, 75) if is_selected else (45, 50, 58)

            # 行背景
            row_rect = pygame.Rect(self.panel_rect.x + 10, y_offset,
                                  self.panel_rect.width - 20, row_height)
            pygame.draw.rect(surface, bg_color, row_rect)
            if is_selected:
                pygame.draw.rect(surface, self.accent_color, row_rect, 1, border_radius=2)

            # 获取位置
            loc_name = "未知"
            for loc in self.locations.values():
                if agent.id in loc.agents:
                    loc_name = loc.name
                    if len(loc_name) > 5:
                        loc_name = loc_name[:5] + ".."
                    break

            # 获取心情emoji
            mood_emoji = self._get_mood_emoji(agent.mood_value)

            # 格式化数据
            row_data = [
                agent.name[:6] if len(agent.name) > 6 else agent.name,
                agent.mbti,
                mood_emoji,
                f"{agent.wealth.get('time', 0):.0f}",
                f"{agent.wealth.get('social', 0):.0f}",
                f"{agent.wealth.get('health', 0.5):.0%}"[:4],
                loc_name
            ]

            # 绘制单元格
            x_offset = self.panel_rect.x + 15
            for i, cell_data in enumerate(row_data):
                cell_text = self.small_font.render(str(cell_data), True, (220, 220, 220))
                surface.blit(cell_text, (x_offset, y_offset + 7))
                x_offset += col_widths[i]

            y_offset += row_height

            # 检查是否超出最大高度
            if y_offset > 115 + max_height - 30:
                break

        return y_offset

    def _get_mood_emoji(self, mood_value: float) -> str:
        """根据心情值返回简单表情"""
        if mood_value > 0.5:
            return "开心"
        elif mood_value > 0.1:
            return "愉快"
        elif mood_value > -0.1:
            return "平静"
        elif mood_value > -0.5:
            return "沮丧"
        else:
            return "悲伤"

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """文字自动换行

        Args:
            text: 要换行的文字
            max_width: 最大宽度（像素）

        Returns:
            换行后的文字列表
        """
        if not text:
            return [""]

        lines = []
        words = text.split()
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_width = self.font.size(test_line)[0]
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
                # 如果单个词就超过宽度，强制换行
                if self.font.size(word)[0] > max_width:
                    # 尝试按字符拆分
                    sub_line = ""
                    for char in word:
                        sub_test = sub_line + char
                        if self.font.size(sub_test)[0] > max_width:
                            if sub_line:
                                lines.append(sub_line)
                            sub_line = char
                        else:
                            sub_line = sub_test
                    current_line = sub_line

        if current_line:
            lines.append(current_line)

        return lines if lines else [""]

    def _draw_agent_detail(self, surface: pygame.Surface, agent: AgentVisual):
        """绘制智能体详情（列形式展示）

        选中智能体时，在详情区域以列形式展示其各项状态指标。
        """
        # 详情区域从智能体表格下方开始
        detail_start_y = 360  # 表格结束位置
        content_start_y = detail_start_y + 30  # 内容区域开始位置（标题下方）
        panel_width = self.panel_rect.width - 40
        panel_x = self.panel_rect.x + 20
        detail_height = self.height - detail_start_y - 60  # 底部留60给控制栏

        # 先绘制分隔线和标题（不滚动，在裁剪区域外）
        pygame.draw.line(surface, (60, 64, 72),
                        (self.panel_rect.x, detail_start_y - 5),
                        (self.panel_rect.right, detail_start_y - 5), 2)

        title = self.font_large.render(f"详情: {agent.name}", True, (255, 255, 255))
        surface.blit(title, (panel_x, detail_start_y))

        # 创建内容区域的裁剪区域（从内容开始位置向下）
        original_clip = surface.get_clip()
        content_clip_rect = pygame.Rect(self.panel_rect.x, content_start_y, self.panel_rect.width, detail_height - 30)
        surface.set_clip(content_clip_rect)

        # 应用滚动偏移 - 内容向上滚动（offset增加，内容y减小）
        y_offset = content_start_y - self.detail_scroll_offset

        # ===== 状态指标列表面（3列布局）=====
        # 第1列：基本信息
        col1_x = panel_x
        col2_x = panel_x + 110
        col3_x = panel_x + 220

        # 基本信息列
        basic_items = [
            ("MBTI", agent.mbti),
            ("状态", agent.status),
            ("心情", f"{agent.mood_value:.2f}"),
        ]
        for label, value in basic_items:
            label_text = self.font.render(f"{label}:", True, (150, 150, 150))
            value_text = self.font.render(str(value), True, (220, 220, 220))
            surface.blit(label_text, (col1_x, y_offset))
            surface.blit(value_text, (col1_x + 55, y_offset))
            y_offset += 22

        y_offset += 10

        # ===== 财富状态（横向进度条形式）=====
        wealth_label = self.font.render("财富状态", True, self.accent_color)
        surface.blit(wealth_label, (panel_x, y_offset))
        y_offset += 22

        # 财富指标：时间、社交、健康、精神、金钱
        wealth_items = [
            ("时间", agent.wealth.get("time", 0), (100, 180, 255)),
            ("社交", agent.wealth.get("social", 0), (100, 200, 150)),
            ("健康", agent.wealth.get("health", 0.5), (255, 150, 100)),
            ("精神", agent.wealth.get("mental", 0.5), (180, 100, 255)),
            ("金钱", agent.wealth.get("money", 0), (255, 215, 0)),
        ]

        bar_max_width = 280
        for w_name, w_value, w_color in wealth_items:
            # 标签
            w_label = self.font.render(f"{w_name}:", True, (150, 150, 150))
            surface.blit(w_label, (col1_x, y_offset))

            # 进度条
            bar_width = bar_max_width
            bar_height = 8
            bar_x = col1_x + 45

            pygame.draw.rect(surface, (50, 54, 62), (bar_x, y_offset + 4, bar_width, bar_height), border_radius=2)

            if w_name == "金钱":
                # 金钱显示数值
                money_text = self.font.render(f"¥{int(w_value):,}", True, w_color)
                surface.blit(money_text, (bar_x + bar_width + 5, y_offset))
            else:
                # 进度
                fill_width = int((w_value + 1) / 2 * bar_width) if w_value >= 0 else 0
                if fill_width > 0:
                    pygame.draw.rect(surface, w_color, (bar_x, y_offset + 4, max(0, fill_width), bar_height), border_radius=2)
                value_text = self.font.render(f"{w_value:.1f}", True, (180, 180, 180))
                surface.blit(value_text, (bar_x + bar_width + 5, y_offset))

            y_offset += 22

        y_offset += 10

        # ===== 短期记忆 =====
        if hasattr(agent, 'short_term_memories') and agent.short_term_memories:
            short_label = self.font.render(f"短期记忆 ({len(agent.short_term_memories)}):", True, (255, 180, 100))
            surface.blit(short_label, (panel_x, y_offset))
            y_offset += 18
            for mem in agent.short_term_memories[:5]:  # 最多显示5条
                # 使用换行函数处理长文本
                wrapped_lines = self._wrap_text(mem, panel_width - 30)
                for i, line in enumerate(wrapped_lines):
                    prefix = "  • " if i == 0 else "    "  # 只有第一行加"•"
                    mem_surface = self.font.render(f"{prefix}{line}", True, (200, 200, 200))
                    surface.blit(mem_surface, (panel_x, y_offset))
                    y_offset += 16
        else:
            short_label = self.font.render("短期记忆 (0):", True, (255, 180, 100))
            surface.blit(short_label, (panel_x, y_offset))
            y_offset += 18

        y_offset += 5

        # ===== 长期记忆 =====
        if hasattr(agent, 'long_term_memories') and agent.long_term_memories:
            long_label = self.font.render(f"长期记忆 ({len(agent.long_term_memories)}):", True, (100, 180, 255))
            surface.blit(long_label, (panel_x, y_offset))
            y_offset += 18
            for mem in agent.long_term_memories[:5]:  # 最多显示5条
                # 使用换行函数处理长文本
                wrapped_lines = self._wrap_text(mem, panel_width - 30)
                for i, line in enumerate(wrapped_lines):
                    prefix = "  • " if i == 0 else "    "  # 只有第一行加"•"
                    mem_surface = self.font.render(f"{prefix}{line}", True, (200, 200, 200))
                    surface.blit(mem_surface, (panel_x, y_offset))
                    y_offset += 16
        else:
            long_label = self.font.render("长期记忆 (0):", True, (100, 180, 255))
            surface.blit(long_label, (panel_x, y_offset))
            y_offset += 18

        y_offset += 10

        # ===== 性格与价值观 =====
        if agent.personality_traits:
            traits_label = self.font.render("性格:", True, (150, 150, 150))
            surface.blit(traits_label, (panel_x, y_offset))
            y_offset += 18
            traits_text = ", ".join(agent.personality_traits[:3])
            # 使用换行函数处理长文本
            wrapped_lines = self._wrap_text(traits_text, panel_width - 30)
            for line in wrapped_lines:
                traits_surface = self.font.render(line, True, (200, 200, 220))
                surface.blit(traits_surface, (panel_x, y_offset))
                y_offset += 16

        if agent.core_values:
            values_label = self.font.render("价值观:", True, (150, 150, 150))
            surface.blit(values_label, (panel_x, y_offset))
            y_offset += 18
            values_text = ", ".join(agent.core_values[:3])
            # 使用换行函数处理长文本
            wrapped_lines = self._wrap_text(values_text, panel_width - 30)
            for line in wrapped_lines:
                values_surface = self.font.render(line, True, (200, 200, 220))
                surface.blit(values_surface, (panel_x, y_offset))
                y_offset += 16

        # ===== 目标 =====
        if agent.goals:
            goals_label = self.font.render("目标:", True, self.accent_color)
            surface.blit(goals_label, (panel_x, y_offset))
            y_offset += 18
            for i, goal in enumerate(agent.goals[:2]):
                # 使用换行函数处理长文本
                wrapped_lines = self._wrap_text(goal, panel_width - 30)
                for j, line in enumerate(wrapped_lines):
                    prefix = "• " if j == 0 else "  "  # 只有第一行加"•"
                    goal_text = self.font.render(f"{prefix}{line}", True, (200, 200, 180))
                    surface.blit(goal_text, (panel_x, y_offset))
                    y_offset += 16

        # ===== 当前对话 =====
        if agent.current_dialog:
            y_offset += 5
            dialog_label = self.font.render("对话:", True, self.accent_color)
            surface.blit(dialog_label, (panel_x, y_offset))
            y_offset += 18

            dialog_rect = pygame.Rect(panel_x, y_offset, panel_width, 35)
            pygame.draw.rect(surface, (50, 54, 62), dialog_rect, border_radius=3)

            if len(agent.current_dialog) > 40:
                dialog_text = agent.current_dialog[:40] + "..."
            else:
                dialog_text = agent.current_dialog
            text_surface = self.font.render(dialog_text, True, (200, 200, 200))
            surface.blit(text_surface, (panel_x + 8, y_offset + 10))

        # 保存内容总高度（从内容区域开始计算）
        self.detail_content_height = y_offset - content_start_y

        # 恢复原始裁剪区域
        surface.set_clip(original_clip)

        # 绘制滚动条（在内容区域内）
        content_area_height = detail_height - 30  # 内容区域高度
        max_scroll = max(0, self.detail_content_height - content_area_height)
        if max_scroll > 0:
            # 滚动条
            scrollbar_x = self.panel_rect.right - 15
            scrollbar_top = content_start_y
            scrollbar_height = content_area_height

            # 滚动条背景
            pygame.draw.rect(surface, (60, 64, 72),
                          (scrollbar_x, scrollbar_top, 6, scrollbar_height), border_radius=3)

            # 滚动条滑块
            visible_ratio = content_area_height / self.detail_content_height
            thumb_height = max(20, int(scrollbar_height * visible_ratio))
            # offset=0时thumb在顶部，offset=max_scroll时thumb在底部
            scroll_ratio = self.detail_scroll_offset / max_scroll if max_scroll > 0 else 0
            thumb_y = scrollbar_top + int(scroll_ratio * (scrollbar_height - thumb_height))

            pygame.draw.rect(surface, (100, 120, 150),
                          (scrollbar_x, thumb_y, 6, thumb_height), border_radius=3)

    def _draw_agent_detail_compact(self, surface: pygame.Surface, agent: AgentVisual):
        """绘制智能体详情（简洁版 - 开关关闭时显示）"""
        detail_start_y = 360
        panel_width = self.panel_rect.width - 40
        panel_x = self.panel_rect.x + 20

        # 分隔线
        pygame.draw.line(surface, (60, 64, 72),
                        (self.panel_rect.x, detail_start_y - 5),
                        (self.panel_rect.right, detail_start_y - 5), 2)

        # 标题
        title = self.font_large.render(f"{agent.name}", True, (255, 255, 255))
        surface.blit(title, (panel_x, detail_start_y))
        y_offset = detail_start_y + 30

        # 简洁信息：MBTI、心情、位置
        info_text = f"MBTI: {agent.mbti} | 心情: {agent.mood_desc}"
        info_surface = self.font.render(info_text, True, (180, 180, 180))
        surface.blit(info_surface, (panel_x, y_offset))
        y_offset += 22

        # 位置
        loc_name = "未知"
        for loc in self.locations.values():
            if agent.id in loc.agents:
                loc_name = loc.name
                break
        loc_text = self.font.render(f"位置: {loc_name}", True, (150, 150, 150))
        surface.blit(loc_text, (panel_x, y_offset))

    def draw_control_bar(self, surface: pygame.Surface, is_paused: bool, speed: float):
        """绘制底部控制栏"""
        bar_height = 60
        bar_rect = pygame.Rect(0, self.height - bar_height, self.width, bar_height)

        pygame.draw.rect(surface, (35, 38, 45), bar_rect)

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

        # 结束今天按钮
        end_today_x = step_x + 90
        end_today_rect = pygame.Rect(end_today_x, btn_y, 90, btn_height)
        pygame.draw.rect(surface, (80, 100, 140), end_today_rect, border_radius=5)
        end_today_text = self.font.render("结束今天", True, (255, 255, 255))
        end_today_rect_center = end_today_text.get_rect(center=end_today_rect.center)
        surface.blit(end_today_text, end_today_rect_center)

        # 保存Session按钮
        save_session_x = end_today_x + 100
        self.save_session_rect = pygame.Rect(save_session_x, btn_y, 90, btn_height)
        pygame.draw.rect(surface, (100, 80, 150), self.save_session_rect, border_radius=5)
        save_text = self.font.render("保存", True, (255, 255, 255))
        save_rect_center = save_text.get_rect(center=self.save_session_rect.center)
        surface.blit(save_text, save_rect_center)

        # 加载Session按钮
        load_session_x = save_session_x + 100
        self.load_session_rect = pygame.Rect(load_session_x, btn_y, 90, btn_height)
        pygame.draw.rect(surface, (80, 120, 160), self.load_session_rect, border_radius=5)
        load_text = self.font.render("加载", True, (255, 255, 255))
        load_rect_center = load_text.get_rect(center=self.load_session_rect.center)
        surface.blit(load_text, load_rect_center)

        # 统计信息（显示天数、轮数、对话次数、智能体数）- 移到顶部显示
        # 在这里不再绘制，会在头部信息栏显示

    def draw(self, selected_agent_id: Optional[str] = None,
             is_paused: bool = False, speed: float = 1.0):
        """绘制整个视图"""
        # 更新选中智能体ID
        if selected_agent_id is not None:
            self.selected_agent_id = selected_agent_id

        # 清屏
        self.screen.fill(self.bg_color)

        # 绘制顶部信息栏
        self.draw_header(self.screen)

        # 绘制时间线
        self.draw_timeline(self.screen)

        # 调整地图区域
        adjusted_map_rect = pygame.Rect(
            0,
            self.header_height + 60,
            int(self.width * 0.65),
            self.height - self.header_height - 60 - 60
        )
        old_map_rect = self.map_rect
        self.map_rect = adjusted_map_rect

        # 绘制地图
        self.draw_map(self.screen)

        # 恢复原始map_rect
        self.map_rect = old_map_rect

        # 绘制事件通知
        self.draw_event_notifications(self.screen)

        # 绘制信息面板
        self.draw_panel(self.screen)

        # 绘制控制栏
        self.draw_control_bar(self.screen, is_paused, speed)

        # 更新显示
        pygame.display.flip()

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """处理事件，返回可选的操作类型"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos

                # 检查详情开关按钮 - 精确区域检测
                # 开关容器: (panel_rect.x + 15, 70) 到 (panel_rect.right - 15, 105)
                toggle_x = self.panel_rect.x + 15
                toggle_y = 70
                toggle_w = self.panel_rect.width - 30
                toggle_h = 35

                if (toggle_x <= mouse_pos[0] <= toggle_x + toggle_w and
                    toggle_y <= mouse_pos[1] <= toggle_y + toggle_h):
                    self.toggle_agent_details()
                    return "toggle_details"

                # 检查每日交互轮数输入框
                if self.interact_rounds_input.rect.collidepoint(mouse_pos):
                    self.interact_rounds_input.handle_event(event)
                    return None

                # 检查控制栏按钮
                bar_height = 60
                bar_rect = pygame.Rect(0, self.height - bar_height, self.width, bar_height)

                if bar_rect.collidepoint(mouse_pos):
                    return self._handle_control_click(mouse_pos)

                # 检查信息面板中的智能体列表点击
                # 表格从 y=143 开始（115 + 28表头），每行28像素
                if self.panel_rect.x < mouse_pos[0] < self.panel_rect.right:
                    table_start_y = 143  # 表头下方开始
                    if 143 <= mouse_pos[1] <= 343:  # 智能体表格区域（约7行）
                        index = (mouse_pos[1] - table_start_y) // 28
                        agents_list = list(self.agents.values())
                        if 0 <= index < len(agents_list):
                            agent = agents_list[index]
                            self.set_agent_selected(agent.id)
                            return f"select:{agent.id}"

        elif event.type == pygame.MOUSEMOTION:
            if event.buttons[0]:
                dx = event.pos[0] - self.last_mouse_pos[0]
                dy = event.pos[1] - self.last_mouse_pos[1]
                self.camera_offset[0] += dx
                self.camera_offset[1] += dy
            self.last_mouse_pos = event.pos

        elif event.type == pygame.MOUSEWHEEL:
            # 详情面板滚动 - MOUSEWHEEL事件没有pos属性，需用pygame.mouse.get_pos()
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if self.panel_rect.x < mouse_x < self.panel_rect.right:
                # 计算最大滚动偏移
                detail_height = self.height - 360 - 60  # 可视区域高度
                max_scroll = max(0, self.detail_content_height - detail_height + 50)
                # 向下滚动(event.y > 0)时增加offset，内容向上滚动
                self.detail_scroll_offset += event.y * 30
                self.detail_scroll_offset = max(0, min(self.detail_scroll_offset, max_scroll))

        elif event.type == pygame.KEYDOWN:
            # 如果每日交互轮数输入框处于激活状态，传递按键事件
            if self.interact_rounds_input.is_active:
                if self.interact_rounds_input.handle_event(event):
                    return None

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

        # 返回按钮
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

        # 结束今天按钮
        end_today_x = speed_x + 120  # step_x + 90 = (speed_x + 230) + 90
        end_today_rect = pygame.Rect(end_today_x, btn_y, 90, 35)
        if end_today_rect.collidepoint(pos):
            return "end_day"

        # 保存Session按钮
        if hasattr(self, 'save_session_rect') and self.save_session_rect.collidepoint(pos):
            if self.interface.on_save_session:
                self.interface.on_save_session()
            return "save_session"

        # 加载Session按钮
        if hasattr(self, 'load_session_rect') and self.load_session_rect.collidepoint(pos):
            if self.interface.on_load_session:
                self.interface.on_load_session()
            return "load_session"

        return None

    def get_clicked_agent(self, pos: Tuple[int, int]) -> Optional[str]:
        """获取点击位置下的智能体ID"""
        for agent in self.agents.values():
            dx = agent.position[0] - pos[0]
            dy = agent.position[1] - pos[1]
            if dx*dx + dy*dy < 400:
                return agent.id
        return None

    # ==================== 序列化支持 ====================

    def to_dict(self) -> Dict[str, Any]:
        """将场景视图状态序列化为字典

        Returns:
            Dict: 包含视图状态的字典
        """
        return {
            "current_day": self.current_day,
            "current_round": self.current_round,
            "max_rounds": self.max_rounds,
            "total_dialogue_count": self.total_dialogue_count,
            "interact_rounds": self.interact_rounds,
            "show_agent_details": self.show_agent_details,
            "selected_agent_id": self.selected_agent_id,
            "scenario_name": self.scenario_name,
            "scenario_type": self.scenario_type,
            "scenario_description": self.scenario_description,
            "scenario_goals": self.scenario_goals,
            "current_era": self.current_era,
            # 位置和连接数据需要从外部传入，这里只存储位置名称
            "locations": {
                name: {
                    "position": loc.position,
                    "type": loc.type,
                    "description": loc.description
                }
                for name, loc in self.locations.items()
            },
            "connections": self.connections,
            "events": self.events,
        }

    def from_dict(self, data: Dict[str, Any]):
        """从字典恢复场景视图状态

        Args:
            data: 包含视图状态的字典
        """
        self.current_day = data.get("current_day", 1)
        self.current_round = data.get("current_round", 1)
        self.max_rounds = data.get("max_rounds", 10)
        self.total_dialogue_count = data.get("total_dialogue_count", 0)
        self.interact_rounds = data.get("interact_rounds", 5)
        self.show_agent_details = data.get("show_agent_details", True)
        self.selected_agent_id = data.get("selected_agent_id")
        self.scenario_name = data.get("scenario_name", "智能体模拟")
        self.scenario_type = data.get("scenario_type", "dialogue")
        self.scenario_description = data.get("scenario_description", "")
        self.scenario_goals = data.get("scenario_goals", [])
        self.current_era = data.get("current_era", "default")
        self.events = data.get("events", [])

        # 恢复位置数据
        locations_data = data.get("locations", {})
        self.locations.clear()
        for name, info in locations_data.items():
            self.locations[name] = LocationVisual(
                name=name,
                position=tuple(info.get("position", (0, 0))),
                type=info.get("type", "默认"),
                description=info.get("description", "")
            )

        # 恢复连接数据
        self.connections = data.get("connections", {})

        # 更新每日交互轮数显示
        self.interact_rounds_input.text = str(self.interact_rounds)

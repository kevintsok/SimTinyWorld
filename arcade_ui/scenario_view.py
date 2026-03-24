"""
ScenarioView - 场景视图 (Arcade版本)

基于arcade库的UI组件实现，包含:
- 顶部信息栏 - scenario name, day, round, dialogue count, agent count
- 时间线 - round progress nodes
- 地图区域 (65% left) - locations, agents, connections, dialog bubbles
- 右侧面板 (35% right) - agent list table + detail panel
- 底部控制栏 - Return, Play/Pause, Speed (1x/2x/4x), Step, End Day, Save, Load

使用components.py中的组件: Button, Panel, TextBox, ProgressBar, Label, COLORS
"""

import arcade
import math
import time
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field

# Import from components
from arcade_ui.components import Button, Panel, TextBox, ProgressBar, Label, COLORS, draw_rectangle_filled, draw_rectangle_outline

# ============================================================================
# Constants (reused from game_view.py)
# ============================================================================

# MBTI colors
MBTI_COLORS = {
    'INTJ': (128, 0, 128),
    'INTP': (100, 100, 180),
    'ENTJ': (200, 0, 0),
    'ENTP': (255, 100, 50),
    'INFJ': (0, 100, 100),
    'INFP': (0, 150, 150),
    'ENFJ': (0, 128, 0),
    'ENFP': (100, 200, 100),
    'ISTJ': (0, 0, 128),
    'ISTP': (50, 50, 150),
    'ESTJ': (128, 64, 0),
    'ESTP': (180, 100, 50),
    'ISFJ': (100, 50, 100),
    'ISFP': (150, 100, 150),
    'ESFJ': (200, 150, 100),
    'ESFP': (255, 150, 150),
}

# E/I shapes
E_SHAPE = 'triangle'
I_SHAPE = 'circle'

# Era theme colors
ERA_THEMES = {
    "ancient": {
        "name": "古代",
        "bg": (45, 38, 30),
        "map_bg": (50, 43, 35),
        "panel_bg": (55, 48, 40),
        "grid": (70, 62, 50),
        "accent": (200, 160, 80),
        "primary": (180, 140, 60),
    },
    "medieval": {
        "name": "中世纪",
        "bg": (35, 32, 40),
        "map_bg": (40, 36, 48),
        "panel_bg": (45, 40, 52),
        "grid": (60, 54, 68),
        "accent": (140, 120, 180),
        "primary": (120, 100, 160),
    },
    "early_modern": {
        "name": "近代",
        "bg": (38, 36, 42),
        "map_bg": (42, 40, 48),
        "panel_bg": (48, 44, 52),
        "grid": (65, 60, 70),
        "accent": (180, 100, 100),
        "primary": (160, 80, 80),
    },
    "modern": {
        "name": "现代",
        "bg": (30, 33, 40),
        "map_bg": (35, 38, 45),
        "panel_bg": (40, 44, 52),
        "grid": (50, 54, 62),
        "accent": (100, 149, 237),
        "primary": (80, 130, 200),
    },
    "default": {
        "name": "默认",
        "bg": (30, 33, 40),
        "map_bg": (35, 38, 45),
        "panel_bg": (40, 44, 52),
        "grid": (50, 54, 62),
        "accent": (100, 149, 237),
        "primary": (80, 130, 200),
    }
}

# Location colors
LOCATION_COLORS = {
    "公司": (100, 149, 237),
    "公园": (60, 179, 113),
    "学校": (255, 165, 0),
    "医院": (220, 20, 60),
    "餐厅": (218, 165, 32),
    "商场": (186, 85, 211),
    "图书馆": (139, 69, 19),
    "健身房": (50, 205, 50),
    "咖啡厅": (210, 180, 140),
    "银行": (255, 215, 0),
    "宫殿": (180, 140, 60),
    "神殿": (200, 180, 100),
    "城墙": (139, 119, 101),
    "战场": (180, 60, 60),
    "市场": (210, 180, 140),
    "港口": (64, 224, 208),
    "城堡": (105, 105, 105),
    "default": (100, 100, 100),
}

# Location icon types
LOCATION_ICONS = {
    "宫殿": "palace",
    "神殿": "temple",
    "城墙": "wall",
    "战场": "battlefield",
    "市场": "market",
    "港口": "port",
    "城堡": "castle",
    "医院": "cross",
    "公园": "tree",
    "公司": "building",
    "default": "default",
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ScenarioViewInterface:
    """场景视图回调接口"""
    on_agent_selected: Callable[[str], None] = None
    on_agent_detail_toggle: Callable[[bool], None] = None
    on_return_to_menu: Callable[[], None] = None
    on_simulation_control: Callable[[str, Any], None] = None
    on_save_session: Callable[[], bool] = None
    on_load_session: Callable[[], None] = None


@dataclass
class AgentVisual:
    """智能体视觉数据"""
    id: str = ""
    name: str = ""
    mbti: str = ""
    position: Tuple[float, float] = (0, 0)
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
    wealth: Dict[str, float] = field(default_factory=lambda: {"time": 0, "social": 0, "health": 0.5, "mental": 0.5, "money": 0})
    recent_memories: List[str] = field(default_factory=list)
    long_term_memory_count: int = 0
    short_term_memory_count: int = 0
    short_term_memories: List[str] = field(default_factory=list)
    long_term_memories: List[str] = field(default_factory=list)
    personality_traits: List[str] = field(default_factory=list)
    core_values: List[str] = field(default_factory=list)
    role: str = ""
    era: str = ""
    goals: List[str] = field(default_factory=list)
    historical_name: str = ""


@dataclass
class LocationVisual:
    """位置视觉数据"""
    name: str = ""
    position: Tuple[int, int] = (0, 0)
    type: str = "默认"
    description: str = ""
    agents: Set[str] = field(default_factory=set)


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


# ============================================================================
# ScenarioView (不是arcade.Window的子类，而是一个可嵌入的视图组件)
# ============================================================================

class ScenarioView:
    """场景视图组件 - 可嵌入到arcade.Window中使用"""

    def __init__(self, width: int = 1000, height: int = 700,
                 interface: ScenarioViewInterface = None):
        """初始化场景视图

        Args:
            width: 窗口宽度
            height: 窗口高度
            interface: 回调接口
        """
        self.width = width
        self.height = height
        self.interface = interface or ScenarioViewInterface()

        # 数据
        self.agents: Dict[str, AgentVisual] = {}
        self.locations: Dict[str, LocationVisual] = {}
        self.dialogs: List[DialogBubble] = []
        self.connections: Dict[str, List[Tuple[str, int]]] = {}
        # 缓存：智能体ID -> 位置名称（避免每帧O(agents×locations)查找）
        self._agent_location_cache: Dict[str, str] = {}

        # 动画
        self.camera_offset = [0, 0]
        self.is_dragging = False
        self.last_mouse_pos = (0, 0)

        # 布局区域
        self.map_width = int(width * 0.65)
        self.panel_width = width - self.map_width

        # 面板状态
        self.show_agent_details: bool = True
        self.selected_agent_id: Optional[str] = None
        self.detail_scroll_offset: int = 0
        self.detail_content_height: int = 0

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
        self.total_dialogue_count = 0
        self.interact_rounds: int = 5
        self.events: List[Dict[str, Any]] = []
        self.triggered_events: Set[int] = set()
        self.event_notifications: List[Dict[str, Any]] = []

        # 布局常量
        self.header_height = 50
        self.timeline_height = 60
        self.control_bar_height = 50

        # 加载状态
        self.loading_text: str = ""

        # 控制状态
        self.is_paused = False
        self.speed = 1.0

        # 初始化UI组件
        self._init_ui_components()

    def _init_ui_components(self):
        """初始化UI组件"""
        # 顶部信息栏
        self.header_label = Label(20, self.height - 30, self.scenario_name, COLORS["text"], 20)

        # 详情开关区域
        self.detail_toggle_rect = None

        # 智能体列表
        self.agent_list_panel = Panel(
            self.panel_width - 30, 200,
            self.panel_width - 20, 200,
            title="智能体列表", visible=True
        )

        # 详情面板
        self.detail_panel = Panel(
            self.panel_width - 30, 50,
            self.panel_width - 20, 150,
            title="详情", visible=True
        )

        # 控制栏按钮
        btn_y = 10
        btn_height = 30

        self.return_btn = Button(15, btn_y, 80, btn_height, "返回",
                                lambda: self._handle_callback("return_to_menu"),
                                color=(150, 80, 80), hover_color=(180, 100, 100))

        self.play_pause_btn = Button(110, btn_y, 70, btn_height, "暂停",
                                    self._on_play_pause_clicked,
                                    color=COLORS["button"])

        self.speed_1x_btn = Button(195, btn_y, 50, btn_height, "1x",
                                   lambda: self._on_speed_clicked(1.0),
                                   color=(70, 130, 180) if abs(self.speed - 1.0) < 0.1 else COLORS["input_bg"])
        self.speed_2x_btn = Button(250, btn_y, 50, btn_height, "2x",
                                   lambda: self._on_speed_clicked(2.0),
                                   color=(70, 130, 180) if abs(self.speed - 2.0) < 0.1 else COLORS["input_bg"])
        self.speed_4x_btn = Button(305, btn_y, 50, btn_height, "4x",
                                   lambda: self._on_speed_clicked(4.0),
                                   color=(70, 130, 180) if abs(self.speed - 4.0) < 0.1 else COLORS["input_bg"])

        self.step_btn = Button(370, btn_y, 60, btn_height, "单步",
                              self._on_step_clicked,
                              color=(80, 100, 80))

        self.end_day_btn = Button(445, btn_y, 80, btn_height, "结束今天",
                                 self._on_end_day_clicked,
                                 color=(80, 100, 140))

        self.save_btn = Button(540, btn_y, 70, btn_height, "保存",
                              self._on_save_clicked,
                              color=(100, 80, 150))

        self.load_btn = Button(620, btn_y, 70, btn_height, "加载",
                              self._on_load_clicked,
                              color=(80, 120, 160))

    def _handle_callback(self, action: str):
        """处理回调"""
        if action == "return_to_menu" and self.interface.on_return_to_menu:
            self.interface.on_return_to_menu()
        elif action == "toggle_pause":
            self._on_play_pause_clicked()
        elif action == "speed_1x":
            self._on_speed_clicked(1.0)
        elif action == "speed_2x":
            self._on_speed_clicked(2.0)
        elif action == "speed_4x":
            self._on_speed_clicked(4.0)
        elif action == "step":
            self._on_step_clicked()
        elif action == "end_day":
            self._on_end_day_clicked()
        elif action == "save":
            self._on_save_clicked()
        elif action == "load":
            self._on_load_clicked()

    def _on_play_pause_clicked(self):
        self.is_paused = not self.is_paused
        self.play_pause_btn.text = "播放" if self.is_paused else "暂停"
        if self.interface.on_simulation_control:
            self.interface.on_simulation_control("pause" if self.is_paused else "resume", None)

    def _on_speed_clicked(self, speed: float):
        self.speed = speed
        self.speed_1x_btn.color = (70, 130, 180) if abs(self.speed - 1.0) < 0.1 else COLORS["input_bg"]
        self.speed_2x_btn.color = (70, 130, 180) if abs(self.speed - 2.0) < 0.1 else COLORS["input_bg"]
        self.speed_4x_btn.color = (70, 130, 180) if abs(self.speed - 4.0) < 0.1 else COLORS["input_bg"]
        if self.interface.on_simulation_control:
            self.interface.on_simulation_control("speed", speed)

    def _on_step_clicked(self):
        if self.interface.on_simulation_control:
            self.interface.on_simulation_control("step", None)

    def _on_end_day_clicked(self):
        if self.interface.on_simulation_control:
            self.interface.on_simulation_control("end_day", None)

    def _on_save_clicked(self):
        if self.interface.on_save_session:
            self.interface.on_save_session()

    def _on_load_clicked(self):
        if self.interface.on_load_session:
            self.interface.on_load_session()

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

    # ========================================================================
    # Public API
    # ========================================================================

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
        # 限制事件列表大小，防止内存无限增长
        if len(self.events) > 100:
            self.events = self.events[-100:]

    def set_round(self, round_num: int):
        """设置当前轮数"""
        self.current_round = round_num

    def set_day(self, day: int):
        """设置当前天数"""
        self.current_day = day

    def set_total_dialogue_count(self, count: int):
        """设置累计对话次数"""
        self.total_dialogue_count = count

    def set_interact_rounds(self, rounds: int):
        """设置每日交互轮数"""
        self.interact_rounds = max(1, rounds)

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
            self._agent_location_cache[agent_id] = location

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
        self._agent_location_cache[agent_id] = to_location

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
        # 限制对话列表大小，防止内存无限增长
        if len(self.dialogs) > 100:
            self.dialogs = self.dialogs[-100:]
        agent.is_talking = True
        agent.current_dialog = text
        agent.dialog_end_time = time.time() + duration

    def set_agent_selected(self, agent_id: Optional[str]):
        """设置选中的智能体"""
        self.selected_agent_id = agent_id
        if self.interface.on_agent_selected and agent_id:
            self.interface.on_agent_selected(agent_id)

    def toggle_agent_details(self):
        """切换智能体详情显示"""
        self.show_agent_details = not self.show_agent_details
        if self.interface.on_agent_detail_toggle:
            self.interface.on_agent_detail_toggle(self.show_agent_details)

    def set_agent_details_visible(self, visible: bool):
        """设置智能体详情是否显示"""
        if self.show_agent_details != visible:
            self.show_agent_details = visible
            if self.interface.on_agent_detail_toggle:
                self.interface.on_agent_detail_toggle(visible)

    def get_agent_shape(self, mbti: str) -> str:
        """获取E/I形状"""
        if mbti and mbti[0] in ('E', 'e'):
            return E_SHAPE
        return I_SHAPE

    def _ease_out_quad(self, t: float) -> float:
        """缓动函数"""
        return 1 - (1 - t) * (1 - t)

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
            # 限制通知列表大小，防止内存无限增长
            if len(self.event_notifications) > 50:
                self.event_notifications = self.event_notifications[-50:]
            return event
        return None

    def set_loading_text(self, text: str):
        """设置加载状态文本"""
        self.loading_text = text

    def clear_loading_text(self):
        """清除加载状态文本"""
        self.loading_text = ""

    # ========================================================================
    # Update Loop
    # ========================================================================

    def update(self):
        """更新视图状态"""
        self._update_event_notifications()

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

    def _update_event_notifications(self):
        """更新事件通知"""
        current_time = time.time()
        self.event_notifications = [
            n for n in self.event_notifications
            if current_time - n["start_time"] < n["duration"]
        ]

    # ========================================================================
    # Draw Methods
    # ========================================================================

    def draw(self):
        """绘制整个视图"""
        # 清屏
        draw_rectangle_filled(
            self.width // 2, self.height // 2,
            self.width, self.height,
            self.bg_color
        )

        # 如果正在加载，显示加载覆盖层
        if self.loading_text:
            self._draw_loading_overlay()
            return

        # 绘制各区域
        self._draw_header()
        self._draw_timeline()
        self._draw_map()
        self._draw_panel()
        self._draw_control_bar()
        self._draw_event_notifications()

    def _draw_header(self):
        """绘制顶部信息栏"""
        # 背景
        draw_rectangle_filled(
            self.width // 2, self.height - self.header_height // 2,
            self.width, self.header_height,
            self.panel_bg_color
        )

        # 底部边框线
        arcade.draw_line(
            0, self.height - self.header_height,
            self.width, self.height - self.header_height,
            self.accent_color, 2
        )

        # 场景名称
        arcade.draw_text(
            self.scenario_name,
            20, self.height - 35,
            COLORS["text"], 20,
            anchor_y="center", font_name="arial"
        )

        # 场景类型
        type_labels = {
            "dialogue": "对话", "debate": "辩论", "cooperation": "协作",
            "emergency": "突发事件", "daily_life": "日常生活"
        }
        type_text = f"[{type_labels.get(self.scenario_type, self.scenario_type)}]"
        arcade.draw_text(
            type_text,
            20 + len(self.scenario_name) * 12 + 10, self.height - 35,
            self.accent_color, 14,
            anchor_y="center", font_name="arial"
        )

        # 统计信息 (右上角)
        panel_left = self.map_width - 10
        stats = f"第{self.current_day}天 | 轮数:{self.current_round}/{self.interact_rounds} | 对话:{self.total_dialogue_count} | 智能体:{len(self.agents)}"
        arcade.draw_text(
            stats,
            panel_left - 300, self.height - 35,
            COLORS["text_secondary"], 14,
            anchor_y="center", font_name="arial"
        )

        # 轮数进度 (右侧)
        round_text = f"第 {self.current_round} / {self.max_rounds} 轮"
        arcade.draw_text(
            round_text,
            self.width - 150, self.height - 35,
            COLORS["text"], 14,
            anchor_y="center", font_name="arial"
        )

        # 进度条
        progress_width = 100
        progress_x = self.width - 260
        progress_y = self.height - 38

        draw_rectangle_filled(
            progress_x + progress_width // 2, progress_y,
            progress_width, 10,
            COLORS["input_bg"]
        )
        fill_width = int(self.current_round / self.max_rounds * progress_width)
        if fill_width > 0:
            draw_rectangle_filled(
                progress_x + fill_width // 2, progress_y,
                fill_width, 10,
                self.accent_color
            )

    def _draw_timeline(self):
        """绘制时间线面板"""
        timeline_y = self.height - self.header_height - self.timeline_height

        # 背景
        draw_rectangle_filled(
            self.map_width // 2,
            timeline_y + self.timeline_height // 2,
            self.map_width, self.timeline_height,
            self.map_bg_color
        )

        # 底部边框线
        arcade.draw_line(
            0, timeline_y,
            self.map_width, timeline_y,
            self.grid_color, 1
        )

        # 标签
        arcade.draw_text(
            "时间线:",
            15, timeline_y + self.timeline_height - 20,
            COLORS["text_secondary"], 12,
            anchor_y="center", font_name="arial"
        )

        # 时间线节点
        node_y = timeline_y + 30
        node_spacing = min(60, (self.map_width - 100) // max(self.max_rounds, 1))
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

            # 节点圆圈
            arcade.draw_circle_filled(node_x, node_y, 8, color)

            if is_current:
                arcade.draw_circle_outline(node_x, node_y, 12, self.accent_color, 2)

            # 轮数文字
            text_color = (50, 50, 50) if not is_future else (200, 200, 200)
            arcade.draw_text(
                str(i),
                node_x, node_y + 20,
                text_color, 10,
                anchor_x="center", anchor_y="center", font_name="arial"
            )

            # 事件指示器
            has_event = any(e.get("round") == i for e in self.events)
            if has_event:
                event_color = (255, 200, 100) if (is_past or is_current) else (100, 100, 100)
                arcade.draw_circle_filled(node_x, node_y, 4, event_color)

        # 连接线
        for i in range(1, self.max_rounds):
            x1 = start_x + (i - 1) * node_spacing
            x2 = start_x + i * node_spacing
            is_past = i < self.current_round
            line_color = self.accent_color if is_past else (60, 60, 60)
            arcade.draw_line(x1 + 8, node_y, x2 - 8, node_y, line_color, 2)

    def _draw_map(self):
        """绘制地图区域"""
        map_top = self.height - self.header_height - self.timeline_height
        map_bottom = self.control_bar_height
        map_height = map_top - map_bottom

        # 背景
        draw_rectangle_filled(
            self.map_width // 2, map_bottom + map_height // 2,
            self.map_width, map_height,
            self.map_bg_color
        )

        # 网格
        grid_size = 50
        for x in range(0, self.map_width + 1, grid_size):
            arcade.draw_line(x, map_bottom, x, map_top, self.grid_color, 1)
        for y in range(int(map_bottom), int(map_top) + 1, grid_size):
            arcade.draw_line(0, y, self.map_width, y, self.grid_color, 1)

        # 绘制连接线
        self._draw_connections()

        # 绘制位置
        for loc in self.locations.values():
            self._draw_location(loc)

        # 绘制智能体
        for agent in self.agents.values():
            self._draw_agent(agent)

        # 绘制对话气泡
        for dialog in self.dialogs:
            self._draw_dialog(dialog)

    def _draw_connections(self):
        """绘制连接线"""
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

                arcade.draw_line(pos1[0], pos1[1], pos2[0], pos2[1], (80, 84, 92), 3)

                # 距离标签
                mid_x, mid_y = (pos1[0] + pos2[0]) // 2, (pos1[1] + pos2[1]) // 2
                arcade.draw_text(
                    str(distance),
                    mid_x - 10, mid_y - 10,
                    (150, 150, 150), 10,
                    font_name="arial"
                )

    def _draw_location(self, loc: LocationVisual):
        """绘制位置"""
        x, y = loc.position
        loc_type = loc.type
        icon_type = LOCATION_ICONS.get(loc_type, "default")
        color = LOCATION_COLORS.get(loc_type, LOCATION_COLORS.get('default', (100, 100, 100)))
        dark_color = tuple(max(0, c - 40) for c in color)
        size = 32

        # 根据图标类型绘制
        if icon_type == "palace":
            draw_rectangle_filled(x, y - size//6, size, size//2, color)
            arcade.draw_polygon_filled(
                [(x - size//2 - 5, y - size//3), (x + size//2 + 5, y - size//3), (x, y - size - 10)],
                dark_color
            )
            for i in range(3):
                draw_rectangle_filled(
                    x - size//2 + i*5 + 10, y + size//3 + i*3,
                    size - i*10, 3, dark_color
                )

        elif icon_type == "temple":
            draw_rectangle_filled(x, y, size, size, color)
            arcade.draw_polygon_filled(
                [(x - size//2 - 3, y - size//2), (x + size//2 + 3, y - size//2), (x, y - size - 5)],
                dark_color
            )
            for col_x in [x - 12, x, x + 12]:
                draw_rectangle_filled(col_x, y, 4, size//2, (200, 200, 200))

        elif icon_type == "castle":
            draw_rectangle_filled(x, y + size//6, size, size//2 + size//3, color)
            arcade.draw_polygon_filled(
                [(x - size//2 - 3, y - size//3), (x + size//2 + 3, y - size//3), (x, y - size - 5)],
                dark_color
            )
            arcade.draw_line(x, y - size - 5, x, y - size - 20, (255, 200, 100), 2)
            arcade.draw_triangle_filled(x, y - size - 20, x + 10, y - size - 15, x, y - size - 10, (200, 50, 50))

        elif icon_type == "market":
            draw_rectangle_filled(x, y + size//6, size, size//3, color)
            arcade.draw_polygon_filled(
                [(x - size//2 - 5, y + size//6), (x + size//2 + 5, y + size//6), (x, y - size//2 + size//6)],
                dark_color
            )

        elif icon_type == "wall":
            draw_rectangle_filled(x, y + size//6, size, size//2, color)
            for i in range(5):
                draw_rectangle_filled(
                    x - size//2 + i*8 + 4, y - size//2 + 4,
                    6, 8, dark_color
                )

        elif icon_type == "battlefield":
            draw_rectangle_filled(x, y, size, size//2, color)
            arcade.draw_line(x - 10, y - 10, x + 10, y + 10, (200, 200, 200), 3)
            arcade.draw_line(x + 10, y - 10, x - 10, y + 10, (200, 200, 200), 3)

        elif icon_type == "port":
            draw_rectangle_filled(x, y, size, size//2, color)
            arcade.draw_circle_outline(x, y - 5, 6, (200, 200, 200), 2)
            arcade.draw_line(x, y, x, y + 12, (200, 200, 200), 2)
            arcade.draw_line(x - 6, y + 10, x + 6, y + 10, (200, 200, 200), 2)

        elif icon_type == "cross":
            draw_rectangle_filled(x, y, size, size//2, color)
            draw_rectangle_filled(x, y - size//4, 6, size, (255, 255, 255))

        elif icon_type == "tree":
            arcade.draw_circle_filled(x, y - 5, size//3, (60, 179, 113))
            draw_rectangle_filled(x, y + size//6, 8, size//3, (139, 90, 43))

        elif icon_type == "building":
            draw_rectangle_filled(x, y + size//6, size, size//2 + size//3, color)
            for wx in [x - 8, x, x + 8]:
                draw_rectangle_filled(wx, y - size//4, 6, 8, (200, 220, 255))

        else:
            draw_rectangle_filled(x, y + size//6, size, size//2 + size//6, color)
            arcade.draw_polygon_filled(
                [(x - size//2 - 2, y - size//3), (x + size//2 + 2, y - size//3), (x, y - size - 5)],
                dark_color
            )

        # 位置名称
        arcade.draw_text(
            loc.name,
            x - len(loc.name) * 4, y + size//2 + 8,
            (220, 220, 220), 12,
            font_name="arial"
        )

        # 智能体数量
        if loc.agents:
            count_text = f"({len(loc.agents)})"
            arcade.draw_text(
                count_text,
                x - len(count_text) * 3, y + size//2 + 23,
                (180, 180, 180), 10,
                font_name="arial"
            )

    def _draw_agent(self, agent: AgentVisual):
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

        arcade.draw_circle_outline(x, y, 20, mood_color + (mood_alpha,), 2)

        # 主体形状
        if shape == E_SHAPE:
            arcade.draw_triangle_filled(x + 12, y, x - 8, y - 10, x - 8, y + 10, base_color)
        else:
            arcade.draw_circle_filled(x, y, 12, base_color)

        # 名字标签
        arcade.draw_text(
            agent.name,
            x - len(agent.name) * 4, y - 25,
            (255, 255, 255), 11,
            font_name="arial"
        )

        # MBTI标签
        arcade.draw_text(
            agent.mbti,
            x - len(agent.mbti) * 3, y + 20,
            (180, 180, 180), 9,
            font_name="arial"
        )

    def _draw_dialog(self, dialog: DialogBubble):
        """绘制对话气泡"""
        x, y = dialog.position

        box_width = 180
        box_height = 60
        box_x = x - box_width // 2
        box_y = y - 80

        alpha = int(240 * dialog.opacity / 255)
        bg_color = (255, 255, 255)

        # 背景
        draw_rectangle_filled(x, y - 40, box_width, box_height, bg_color)

        # 边框
        draw_rectangle_outline(x, y - 40, box_width, box_height, dialog.agent_color, 2)

        # 名称
        name_color = (50, 50, 50) if dialog.opacity > 200 else (100, 100, 100)
        arcade.draw_text(
            f"{dialog.agent_name}:",
            box_x + 8, box_y + box_height - 18,
            name_color, 11,
            font_name="arial"
        )

        # 文字分行
        words = dialog.text.split(' ')
        lines = []
        line = ""
        for word in words:
            test_line = line + word + " "
            if len(test_line) * 6 < box_width - 20:
                line = test_line
            else:
                lines.append(line)
                line = word + " "
        if line:
            lines.append(line)

        text_color = (30, 30, 30) if dialog.opacity > 200 else (80, 80, 80)
        for i, l in enumerate(lines[:2]):
            arcade.draw_text(
                l,
                box_x + 8, box_y + box_height - 35 - i * 16,
                text_color, 10,
                font_name="arial"
            )

        # 三角指向
        arcade.draw_triangle_filled(x, y - 5, x - 8, box_y + box_height, x + 8, box_y + box_height, bg_color)

    def _draw_panel(self):
        """绘制右侧信息面板"""
        panel_x = self.map_width

        # 背景
        draw_rectangle_filled(
            panel_x + self.panel_width // 2, self.height // 2,
            self.panel_width, self.height - self.header_height - self.control_bar_height,
            self.panel_bg_color
        )

        # 标题
        arcade.draw_text(
            "信息面板",
            panel_x + 20, self.height - 80,
            COLORS["text"], 18,
            font_name="arial"
        )

        # 分隔线
        arcade.draw_line(
            panel_x, self.height - 90,
            self.width, self.height - 90,
            (60, 64, 72), 2
        )

        # 详情开关
        self._draw_detail_toggle(panel_x)

        # 智能体列表
        self._draw_agent_list(panel_x)

        # 选中智能体详情
        if self.selected_agent_id and self.selected_agent_id in self.agents:
            agent = self.agents[self.selected_agent_id]
            if self.show_agent_details:
                self._draw_agent_detail(panel_x, agent)
            else:
                self._draw_agent_detail_compact(panel_x, agent)

    def _draw_detail_toggle(self, panel_x: int):
        """绘制详情开关"""
        y_offset = self.height - 125

        # 开关容器背景
        draw_rectangle_filled(
            panel_x + self.panel_width // 2, y_offset + 17,
            self.panel_width - 30, 35,
            (50, 54, 62)
        )

        # 标签
        arcade.draw_text(
            "显示详情:",
            panel_x + 25, y_offset + 12,
            (180, 180, 180), 12,
            anchor_y="center", font_name="arial"
        )

        # 开关按钮
        toggle_width = 50
        toggle_height = 22
        toggle_x = panel_x + self.panel_width - toggle_width - 35
        toggle_y = y_offset + 6

        bg_color = (70, 130, 180) if self.show_agent_details else (80, 80, 80)
        draw_rectangle_filled(
            toggle_x + toggle_width // 2, toggle_y + toggle_height // 2,
            toggle_width, toggle_height,
            bg_color
        )

        # 滑块
        knob_x = toggle_x + 8 if not self.show_agent_details else toggle_x + toggle_width - 8
        arcade.draw_circle_filled(knob_x, toggle_y + toggle_height // 2, 9, (255, 255, 255))

        # 状态文字
        status_text = "开" if self.show_agent_details else "关"
        status_color = (255, 255, 255) if self.show_agent_details else (150, 150, 150)
        arcade.draw_text(
            status_text,
            toggle_x - 25, toggle_y + toggle_height // 2,
            status_color, 12,
            anchor_y="center", font_name="arial"
        )

        # 保存开关区域供点击检测 (left, bottom, width, height)
        self.detail_toggle_rect = (panel_x + 15, y_offset, self.panel_width - 30, 35)

    def _draw_agent_list(self, panel_x: int):
        """绘制智能体列表"""
        y_offset = self.height - 165

        # 列配置
        col_widths = [70, 45, 45, 50, 50, 40, 50]
        col_names = ["名称", "MBTI", "心情", "时间", "社交", "体力", "位置"]

        # 表头背景
        draw_rectangle_filled(
            panel_x + self.panel_width // 2, y_offset + 10,
            self.panel_width - 20, 25,
            (40, 44, 52)
        )

        # 表头文字
        x_offset = panel_x + 15
        for i, col_name in enumerate(col_names):
            arcade.draw_text(
                col_name,
                x_offset, y_offset + 5,
                (180, 180, 180), 10,
                anchor_y="center", font_name="arial"
            )
            x_offset += col_widths[i]

        y_offset += 30

        # 智能体行
        row_height = 28
        for agent in self.agents.values():
            is_selected = agent.id == self.selected_agent_id
            bg_color = (50, 60, 75) if is_selected else (45, 50, 58)

            # 行背景
            draw_rectangle_filled(
                panel_x + self.panel_width // 2, y_offset + row_height // 2,
                self.panel_width - 20, row_height,
                bg_color
            )

            if is_selected:
                draw_rectangle_outline(
                    panel_x + self.panel_width // 2, y_offset + row_height // 2,
                    self.panel_width - 20, row_height,
                    self.accent_color, 1
                )

            # 获取位置（使用缓存，O(1)）
            loc_name = self._agent_location_cache.get(agent.id, "未知")
            if len(loc_name) > 5:
                loc_name = loc_name[:5] + ".."

            # 心情文本
            mood_text = self._get_mood_text(agent.mood_value)

            # 行数据
            row_data = [
                agent.name[:6] if len(agent.name) > 6 else agent.name,
                agent.mbti,
                mood_text,
                f"{agent.wealth.get('time', 0):.0f}",
                f"{agent.wealth.get('social', 0):.0f}",
                f"{agent.wealth.get('health', 0.5):.0%}"[:4],
                loc_name
            ]

            # 绘制单元格
            x_offset = panel_x + 15
            for i, cell_data in enumerate(row_data):
                arcade.draw_text(
                    str(cell_data),
                    x_offset, y_offset + row_height // 2,
                    (220, 220, 220), 10,
                    anchor_y="center", font_name="arial"
                )
                x_offset += col_widths[i]

            y_offset += row_height

            if y_offset > self.height - 280:
                break

    def _get_mood_text(self, mood_value: float) -> str:
        """根据心情值返回文本"""
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
        """文字自动换行"""
        if not text:
            return [""]
        lines = []
        words = text.split()
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if len(test_line) * 6 <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines if lines else [""]

    def _draw_agent_detail(self, panel_x: int, agent: AgentVisual):
        """绘制智能体详情（完整版）"""
        detail_start_y = self.height - 340
        panel_width = self.panel_width - 40
        panel_content_x = panel_x + 20

        # 分隔线
        arcade.draw_line(
            panel_x, detail_start_y,
            self.width, detail_start_y,
            (60, 64, 72), 2
        )

        # 标题
        arcade.draw_text(
            f"详情: {agent.name}",
            panel_content_x, detail_start_y + 10,
            COLORS["text"], 14,
            font_name="arial"
        )

        y_offset = detail_start_y + 35

        # 基本信息
        basic_items = [
            ("MBTI", agent.mbti),
            ("状态", agent.status),
            ("心情", f"{agent.mood_value:.2f}"),
        ]

        for label, value in basic_items:
            arcade.draw_text(
                f"{label}:",
                panel_content_x, y_offset,
                (150, 150, 150), 12,
                font_name="arial"
            )
            arcade.draw_text(
                str(value),
                panel_content_x + 55, y_offset,
                (220, 220, 220), 12,
                font_name="arial"
            )
            y_offset += 18

        y_offset += 10

        # 财富状态
        arcade.draw_text(
            "财富状态",
            panel_content_x, y_offset,
            self.accent_color, 12,
            font_name="arial"
        )
        y_offset += 20

        wealth_items = [
            ("时间", agent.wealth.get("time", 0), (100, 180, 255)),
            ("社交", agent.wealth.get("social", 0), (100, 200, 150)),
            ("健康", agent.wealth.get("health", 0.5), (255, 150, 100)),
            ("精神", agent.wealth.get("mental", 0.5), (180, 100, 255)),
            ("金钱", agent.wealth.get("money", 0), (255, 215, 0)),
        ]

        bar_max_width = 180
        for w_name, w_value, w_color in wealth_items:
            arcade.draw_text(
                f"{w_name}:",
                panel_content_x, y_offset,
                (150, 150, 150), 11,
                font_name="arial"
            )

            bar_x = panel_content_x + 45
            bar_width = bar_max_width
            bar_height = 8

            draw_rectangle_filled(
                bar_x + bar_width // 2, y_offset + 4,
                bar_width, bar_height,
                (50, 54, 62)
            )

            if w_name == "金钱":
                arcade.draw_text(
                    f"¥{int(w_value):,}",
                    bar_x + bar_width + 5, y_offset,
                    w_color, 10,
                    font_name="arial"
                )
            else:
                fill_width = int((w_value + 1) / 2 * bar_width) if w_value >= 0 else 0
                if fill_width > 0:
                    draw_rectangle_filled(
                        bar_x + fill_width // 2, y_offset + 4,
                        max(0, fill_width), bar_height,
                        w_color
                    )
                arcade.draw_text(
                    f"{w_value:.1f}",
                    bar_x + bar_width + 5, y_offset,
                    (180, 180, 180), 10,
                    font_name="arial"
                )

            y_offset += 20

        y_offset += 10

        # 短期记忆
        if agent.short_term_memories:
            arcade.draw_text(
                f"短期记忆 ({len(agent.short_term_memories)}):",
                panel_content_x, y_offset,
                (255, 180, 100), 11,
                font_name="arial"
            )
            y_offset += 16
            for mem in agent.short_term_memories[:3]:
                mem_text = mem[:30] + "..." if len(mem) > 30 else mem
                arcade.draw_text(
                    f"• {mem_text}",
                    panel_content_x, y_offset,
                    (200, 200, 200), 10,
                    font_name="arial"
                )
                y_offset += 14

        y_offset += 5

        # 长期记忆
        if agent.long_term_memories:
            arcade.draw_text(
                f"长期记忆 ({len(agent.long_term_memories)}):",
                panel_content_x, y_offset,
                (100, 180, 255), 11,
                font_name="arial"
            )
            y_offset += 16
            for mem in agent.long_term_memories[:3]:
                mem_text = mem[:30] + "..." if len(mem) > 30 else mem
                arcade.draw_text(
                    f"• {mem_text}",
                    panel_content_x, y_offset,
                    (200, 200, 200), 10,
                    font_name="arial"
                )
                y_offset += 14

        y_offset += 10

        # 性格与价值观
        if agent.personality_traits:
            arcade.draw_text(
                "性格:",
                panel_content_x, y_offset,
                (150, 150, 150), 11,
                font_name="arial"
            )
            y_offset += 16
            traits_text = ", ".join(agent.personality_traits[:3])
            arcade.draw_text(
                traits_text,
                panel_content_x, y_offset,
                (200, 200, 220), 10,
                font_name="arial"
            )
            y_offset += 14

        # 当前对话
        if agent.current_dialog:
            y_offset += 8
            arcade.draw_text(
                "对话:",
                panel_content_x, y_offset,
                self.accent_color, 11,
                font_name="arial"
            )
            y_offset += 16

            draw_rectangle_filled(
                panel_content_x + panel_width // 2, y_offset + 12,
                panel_width, 30,
                (50, 54, 62)
            )

            dialog_text = agent.current_dialog[:40] + "..." if len(agent.current_dialog) > 40 else agent.current_dialog
            arcade.draw_text(
                dialog_text,
                panel_content_x + 8, y_offset + 12,
                (200, 200, 200), 10,
                font_name="arial"
            )

    def _draw_agent_detail_compact(self, panel_x: int, agent: AgentVisual):
        """绘制智能体详情（简洁版）"""
        detail_start_y = self.height - 340
        panel_content_x = panel_x + 20

        # 分隔线
        arcade.draw_line(
            panel_x, detail_start_y,
            self.width, detail_start_y,
            (60, 64, 72), 2
        )

        # 标题
        arcade.draw_text(
            agent.name,
            panel_content_x, detail_start_y + 10,
            COLORS["text"], 14,
            font_name="arial"
        )

        y_offset = detail_start_y + 35

        # 简洁信息
        info_text = f"MBTI: {agent.mbti} | 心情: {agent.mood_desc}"
        arcade.draw_text(
            info_text,
            panel_content_x, y_offset,
            (180, 180, 180), 12,
            font_name="arial"
        )
        y_offset += 20

        # 位置（使用缓存，O(1)）
        loc_name = self._agent_location_cache.get(agent.id, "未知")
        arcade.draw_text(
            f"位置: {loc_name}",
            panel_content_x, y_offset,
            (150, 150, 150), 12,
            font_name="arial"
        )

    def _draw_control_bar(self):
        """绘制底部控制栏"""
        # 背景
        draw_rectangle_filled(
            self.width // 2, self.control_bar_height // 2,
            self.width, self.control_bar_height,
            (35, 38, 45)
        )

        # 顶部边框线
        arcade.draw_line(
            0, self.control_bar_height,
            self.width, self.control_bar_height,
            (60, 64, 72), 2
        )

        # 绘制按钮
        self.return_btn.draw()
        self.play_pause_btn.draw()
        self.speed_1x_btn.draw()
        self.speed_2x_btn.draw()
        self.speed_4x_btn.draw()
        self.step_btn.draw()
        self.end_day_btn.draw()
        self.save_btn.draw()
        self.load_btn.draw()

    def _draw_event_notifications(self):
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
            box_y = self.height - 150 - i * 70

            # 背景
            draw_rectangle_filled(
                box_x + box_width // 2, box_y + box_height // 2,
                box_width, box_height,
                (40, 44, 52)
            )

            # 边框
            draw_rectangle_outline(
                box_x + box_width // 2, box_y + box_height // 2,
                box_width, box_height,
                self.accent_color,
                2
            )

            # 文字
            arcade.draw_text(
                notif["content"],
                box_x + box_width // 2, box_y + box_height // 2,
                (255, 255, 255, alpha), 14,
                anchor_x="center", anchor_y="center", font_name="arial"
            )

    def _draw_loading_overlay(self):
        """绘制加载覆盖层"""
        # 半透明黑色背景
        draw_rectangle_filled(
            self.width // 2, self.height // 2,
            self.width, self.height,
            (0, 0, 0, 180)
        )

        # 加载文本
        lines = self.loading_text.split('\n')
        total_height = len(lines) * 30
        start_y = (self.height - total_height) // 2

        for i, line in enumerate(lines):
            arcade.draw_text(
                line,
                self.width // 2, start_y + i * 30,
                (255, 255, 255), 16,
                anchor_x="center", anchor_y="center", font_name="arial"
            )

    # ========================================================================
    # Event Handling
    # ========================================================================

    def handle_event(self, event: dict) -> Optional[str]:
        """处理事件的通用入口

        Args:
            event: 事件字典，包含 type, x, y, button 等

        Returns:
            Optional[str]: 操作类型
        """
        event_type = event.get("type")
        if event_type == "mouse_press":
            return self.handle_mouse_press(
                event.get("x", 0),
                event.get("y", 0),
                event.get("button", arcade.MOUSE_BUTTON_LEFT)
            )
        elif event_type == "key_press":
            return self.handle_key_press(
                event.get("key", 0),
                event.get("modifiers", 0)
            )
        return None

    def handle_mouse_press(self, x: float, y: float, button: int = arcade.MOUSE_BUTTON_LEFT) -> Optional[str]:
        """处理鼠标点击事件

        Returns:
            Optional[str]: 操作类型，如 "return_to_menu", "toggle_pause", "select:agent_id" 等
        """
        if button != arcade.MOUSE_BUTTON_LEFT:
            return None

        # 检查详情开关
        if self.detail_toggle_rect:
            left, bottom, width, height = self.detail_toggle_rect
            if left <= x <= left + width and bottom <= y <= bottom + height:
                self.toggle_agent_details()
                return "toggle_details"

        # 检查控制栏按钮
        if y < self.control_bar_height:
            if self.return_btn.handle_mouse_press(x, y, button):
                return "return_to_menu"
            if self.play_pause_btn.handle_mouse_press(x, y, button):
                return "toggle_pause"
            if self.speed_1x_btn.handle_mouse_press(x, y, button):
                self._on_speed_clicked(1.0)
                return "speed:1.0"
            if self.speed_2x_btn.handle_mouse_press(x, y, button):
                self._on_speed_clicked(2.0)
                return "speed:2.0"
            if self.speed_4x_btn.handle_mouse_press(x, y, button):
                self._on_speed_clicked(4.0)
                return "speed:4.0"
            if self.step_btn.handle_mouse_press(x, y, button):
                return "step"
            if self.end_day_btn.handle_mouse_press(x, y, button):
                return "end_day"
            if self.save_btn.handle_mouse_press(x, y, button):
                return "save_session"
            if self.load_btn.handle_mouse_press(x, y, button):
                return "load_session"

        # 检查智能体列表点击
        panel_x = self.map_width
        if panel_x < x < self.width:
            table_start_y = self.height - 165
            if table_start_y <= y <= table_start_y + 200:
                index = int((y - table_start_y - 25) // 28)
                agents_list = list(self.agents.values())
                if 0 <= index < len(agents_list):
                    agent = agents_list[index]
                    self.set_agent_selected(agent.id)
                    return f"select:{agent.id}"

        # 检查时间线节点点击
        if (self.height - self.header_height - self.timeline_height <= y <= self.height - self.header_height and
                x < self.map_width):
            node_y = self.height - self.header_height - 35
            node_spacing = min(60, (self.map_width - 100) // max(self.max_rounds, 1))
            start_x = 80
            for i in range(1, self.max_rounds + 1):
                node_x = start_x + (i - 1) * node_spacing
                if abs(x - node_x) < 15 and abs(y - node_y) < 15:
                    self.set_round(i)
                    return f"round:{i}"

        # 检查地图上的智能体点击
        if x < self.map_width:
            map_top = self.height - self.header_height - self.timeline_height
            map_bottom = self.control_bar_height
            if map_bottom < y < map_top:
                clicked = self._get_clicked_agent(x, y)
                if clicked:
                    self.set_agent_selected(clicked)
                    return f"select:{clicked}"

        return None

    def handle_key_press(self, key: int, modifiers: int = 0) -> Optional[str]:
        """处理键盘按键

        Returns:
            Optional[str]: 操作类型
        """
        if key == arcade.key.SPACE:
            self._on_play_pause_clicked()
            return "toggle_pause"
        elif key == arcade.key.KEY_1:
            self._on_speed_clicked(1.0)
            return "speed:1.0"
        elif key == arcade.key.KEY_2:
            self._on_speed_clicked(2.0)
            return "speed:2.0"
        elif key == arcade.key.KEY_3:
            self._on_speed_clicked(4.0)
            return "speed:4.0"
        elif key == arcade.key.S:
            self._on_step_clicked()
            return "step"

        return None

    def handle_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """处理鼠标滚轮事件"""
        panel_x = self.map_width
        if panel_x < x < self.width:
            # 计算最大滚动偏移
            detail_height = self.height - 340 - 60
            max_scroll = max(0, self.detail_content_height - detail_height + 50)
            self.detail_scroll_offset += scroll_y * 30
            self.detail_scroll_offset = max(0, min(self.detail_scroll_offset, max_scroll))

    def _get_clicked_agent(self, x: float, y: float) -> Optional[str]:
        """获取点击位置下的智能体ID"""
        for agent in self.agents.values():
            dx = agent.position[0] - x
            dy = agent.position[1] - y
            if dx*dx + dy*dy < 400:  # 20像素半径
                return agent.id
        return None

    # ========================================================================
    # Serialization
    # ========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """将场景视图状态序列化为字典"""
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
        """从字典恢复场景视图状态"""
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
        events = data.get("events", [])
        # 应用上限防止内存无限增长（与add_event保持一致）
        if len(events) > 100:
            events = events[-100:]
        self.events = events

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

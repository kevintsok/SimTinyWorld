"""
MainView - 主界面模块 (Arcade版本)

提供主界面的交互界面，包括：
- 场景选择
- 智能体管理
- 快速开始
"""

import arcade
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass

from arcade_ui.components import Button, Panel, TextBox, Dropdown, COLORS, draw_rectangle_filled, draw_rectangle_outline


@dataclass
class MainViewInterface:
    """主视图回调接口"""
    on_scenario_selected: Callable[[str, dict], None] = None
    on_agent_created: Callable[[dict], None] = None
    on_agent_imported: Callable[[dict], None] = None
    on_quick_start: Callable[[dict], None] = None
    on_session_clicked: Callable[[], None] = None


class MainView:
    """主界面视图 (Arcade版本)

    提供三个主选项的垂直布局 + 右侧面板设计：
    - 左侧：三个大按钮（场景、智能体、快速开始）
    - 右侧：根据选择显示对应内容
    """

    BACKGROUND_COLOR = (30, 33, 40)
    PANEL_COLOR = (40, 44, 52)
    BUTTON_COLOR = (70, 130, 180)
    BUTTON_HOVER_COLOR = (100, 160, 210)
    TEXT_COLOR = (255, 255, 255)
    ACCENT_COLOR = (100, 160, 210)
    BORDER_COLOR = (60, 64, 72)

    AVAILABLE_SCENARIOS = [
        ("daily_life", "日常生活", "日常生活的社交互动场景"),
        ("emergency", "突发事件", "社会突发事件的应急场景"),
        ("debate", "观点辩论", "观点阐述与辩论场景"),
    ]

    MBTI_TYPES = [
        "INTJ", "INTP", "ENTJ", "ENTP",
        "INFJ", "INFP", "ENFJ", "ENFP",
        "ISTJ", "ISFJ", "ESTJ", "ESFJ",
        "ISTP", "ISFP", "ESTP", "ESFP"
    ]

    GENDER_OPTIONS = ["男", "女"]

    def __init__(self, window: arcade.Window, rect_x: float, rect_y: float,
                 rect_width: float, rect_height: float,
                 interface: Optional[MainViewInterface] = None):
        """初始化主界面

        Args:
            window: arcade窗口对象
            rect_x: 主界面区域X
            rect_y: 主界面区域Y
            rect_width: 主界面宽度
            rect_height: 主界面高度
            interface: 回调接口
        """
        self.window = window
        self.rect_x = rect_x
        self.rect_y = rect_y
        self.rect_width = rect_width
        self.rect_height = rect_height
        self.interface = interface or MainViewInterface()

        # 当前选中的主选项
        self.current_selection: Optional[str] = None

        # 左侧按钮区域
        button_width = 180
        button_height = 80
        button_margin = 20
        left_x = self.rect_x + 30
        top_y = self.rect_y + 80

        # 三个主按钮
        self.scenario_button = Button(
            left_x, top_y, button_width, button_height,
            "场景",
            lambda: self._on_main_button_clicked("scenario"),
            self.BUTTON_COLOR,
            self.BUTTON_HOVER_COLOR,
        )

        self.agent_button = Button(
            left_x, top_y + button_height + button_margin, button_width, button_height,
            "智能体",
            lambda: self._on_main_button_clicked("agent"),
            self.BUTTON_COLOR,
            self.BUTTON_HOVER_COLOR,
        )

        self.quickstart_button = Button(
            left_x, top_y + (button_height + button_margin) * 2, button_width, button_height,
            "快速开始",
            lambda: self._on_main_button_clicked("quickstart"),
            (80, 160, 100),
            (100, 180, 120),
        )

        # Session按钮
        self.session_button = Button(
            left_x, top_y + (button_height + button_margin) * 3, button_width, button_height,
            "Session",
            self._on_session_clicked,
            (120, 100, 160),
            (140, 120, 180),
        )

        # 右侧面板区域
        panel_x = self.rect_x + 250
        panel_width = self.rect_width - 280
        panel_height = self.rect_height - 100
        self.detail_panel = Panel(
            panel_x, top_y, panel_width, panel_height,
            title="",
            background_color=self.PANEL_COLOR,
            border_color=self.BORDER_COLOR,
        )

        # 初始化子面板
        self._init_scenario_panel()
        self._init_agent_panel()
        self._init_quickstart_panel()

        # 底部确认按钮
        confirm_button_width = 160
        confirm_button_height = 45
        self.confirm_button = Button(
            self.rect_x + self.rect_width - confirm_button_width - 30,
            self.rect_y + 20,
            confirm_button_width,
            confirm_button_height,
            "启动模拟",
            self._on_confirm_clicked,
            (80, 160, 100),
            (100, 180, 120),
        )

        # 追踪鼠标位置
        self.mouse_x = 0
        self.mouse_y = 0

        # 快速开始说明
        self.quickstart_info = [
            "快速开始将使用默认配置启动模拟：",
            "",
            "场景: 日常生活 (daily_life)",
            "智能体数量: 5",
            "模拟轮次: 5",
            "LLM引擎: Qwen (默认)",
            "",
            "所有智能体将由系统随机生成。",
            "",
            "点击下方「启动模拟」按钮即可开始。",
        ]

    def _init_scenario_panel(self):
        """初始化场景选择面板"""
        panel_x = self.detail_panel.x + 20
        panel_y = self.detail_panel.y + 50
        panel_width = self.detail_panel.width - 40
        item_height = 60
        item_margin = 10

        # 场景选项按钮
        self.scenario_buttons: List[Button] = []
        self.selected_scenario: Optional[str] = None

        for i, (scenario_id, scenario_name, scenario_desc) in enumerate(
                self.AVAILABLE_SCENARIOS):
            btn = Button(
                panel_x, panel_y + i * (item_height + item_margin),
                panel_width, item_height,
                scenario_name,
                lambda sid=scenario_id: self._on_scenario_selected(sid),
                (50, 54, 62),
                (70, 74, 82),
            )
            self.scenario_buttons.append(btn)

        # 场景详情区域
        detail_y = panel_y + len(self.AVAILABLE_SCENARIOS) * (item_height + item_margin) + 20
        self.scenario_detail_panel = Panel(
            panel_x, detail_y, panel_width, 200,
            title="场景详情",
            background_color=(50, 54, 62),
            border_color=self.BORDER_COLOR,
        )
        self.scenario_detail_text = ""

        # 场景参数配置
        config_y = detail_y + 230
        self.scenario_config_panel = Panel(
            panel_x, config_y, panel_width, 200,
            title="场景配置",
            background_color=(50, 54, 62),
            border_color=self.BORDER_COLOR,
        )

        # 场景配置输入框
        config_label_width = 100
        input_width = panel_width - config_label_width - 20
        input_height = 30

        # 场景配置输入框 - 位置会在绘制时计算
        self.agent_count_input = TextBox(
            panel_x + config_label_width, 0,
            input_width, input_height,
            "智能体数量 (默认5)",
            10
        )

        self.round_count_input = TextBox(
            panel_x + config_label_width, 0,
            input_width, input_height,
            "轮次数量 (默认5)",
            10
        )

        # 突发事件输入框
        self.emergency_topic_input = TextBox(
            panel_x + config_label_width, 0,
            input_width, input_height,
            "请输入突发事件描述",
            100
        )

        # 观点辩论输入框
        self.debate_topic_input = TextBox(
            panel_x + config_label_width, 0,
            input_width, input_height,
            "请输入辩论观点",
            100
        )

    def _init_agent_panel(self):
        """初始化智能体管理面板"""
        panel_x = self.detail_panel.x + 20
        panel_y = self.detail_panel.y + 50
        panel_width = self.detail_panel.width - 40
        input_height = 35
        input_margin = 10

        label_width = 80
        input_width = (panel_width - label_width - 30) // 2

        # 姓名
        y = panel_y
        self.agent_name_input = TextBox(
            panel_x + label_width, y, input_width, input_height,
            "姓名", 20
        )

        # 性别下拉框
        self.agent_gender_dropdown = Dropdown(
            panel_x + label_width + input_width + 10, y,
            input_width, input_height,
            self.GENDER_OPTIONS, ""
        )

        # 年龄
        y += input_height + input_margin
        self.agent_age_input = TextBox(
            panel_x + label_width, y, input_width, input_height,
            "年龄", 3
        )

        # MBTI下拉框
        self.agent_mbti_dropdown = Dropdown(
            panel_x + label_width + input_width + 10, y,
            input_width, input_height,
            self.MBTI_TYPES, ""
        )

        # 职业
        y += input_height + input_margin
        self.agent_occupation_input = TextBox(
            panel_x + label_width, y, panel_width - label_width, input_height,
            "职业", 50
        )

        # 背景
        y += input_height + input_margin
        self.agent_background_input = TextBox(
            panel_x + label_width, y, panel_width - label_width, input_height * 2,
            "背景描述 (可选)", 200
        )

        # 操作按钮
        y += input_height * 2 + 30
        button_width = 120
        button_height = 40
        button_margin = 20

        self.create_agent_button = Button(
            panel_x, y, button_width, button_height,
            "创建智能体",
            self._on_create_agent,
            (80, 160, 100),
            (100, 180, 120),
        )

        self.import_agent_button = Button(
            panel_x + button_width + button_margin, y, button_width, button_height,
            "导入智能体",
            self._on_import_agent,
            self.BUTTON_COLOR,
            self.BUTTON_HOVER_COLOR,
        )

        # 已创建智能体列表
        y += button_height + 30
        self.agent_list_panel = Panel(
            panel_x, y, panel_width, 180,
            title="已创建的智能体",
            background_color=(50, 54, 62),
            border_color=self.BORDER_COLOR,
        )
        self.created_agents: List[dict] = []

        # 清除按钮
        self.clear_agents_button = Button(
            panel_x + panel_width - 100, y + 35, 90, 30,
            "清空列表",
            self._on_clear_agents,
            (160, 80, 80),
            (180, 100, 100),
        )

    def _init_quickstart_panel(self):
        """初始化快速开始面板"""
        pass

    def _on_main_button_clicked(self, selection: str):
        """主按钮点击处理"""
        self.current_selection = selection
        if selection == "scenario":
            self.detail_panel.title = "场景选择"
        elif selection == "agent":
            self.detail_panel.title = "智能体管理"
        elif selection == "quickstart":
            self.detail_panel.title = "快速开始"
        elif selection == "session":
            self.detail_panel.title = "Session管理"

    def _on_session_clicked(self):
        """Session按钮点击"""
        self.current_selection = "session"
        self.detail_panel.title = "Session管理"
        if self.interface.on_session_clicked:
            self.interface.on_session_clicked()

    def _on_scenario_selected(self, scenario_id: str):
        """场景选项点击处理"""
        self.selected_scenario = scenario_id

        scenario_name, scenario_desc = "", ""
        for sid, name, desc in self.AVAILABLE_SCENARIOS:
            if sid == scenario_id:
                scenario_name, scenario_desc = name, desc
                break

        self.scenario_detail_text = f"当前选择: {scenario_name}\n\n{scenario_desc}"

        if self.interface.on_scenario_selected:
            self.interface.on_scenario_selected(scenario_id, self._get_scenario_config())

    def _get_scenario_config(self) -> dict:
        """获取场景配置"""
        agent_count_text = self.agent_count_input.text.strip()
        round_count_text = self.round_count_input.text.strip()

        config = {}
        if agent_count_text and agent_count_text.isdigit():
            config["num_agents"] = int(agent_count_text)
        if round_count_text and round_count_text.isdigit():
            config["num_rounds"] = int(round_count_text)

        if self.selected_scenario == "emergency":
            emergency_topic = self.emergency_topic_input.text.strip()
            if emergency_topic:
                config["emergency_topic"] = emergency_topic
        elif self.selected_scenario == "debate":
            debate_topic = self.debate_topic_input.text.strip()
            if debate_topic:
                config["debate_topic"] = debate_topic

        return config

    def _on_create_agent(self):
        """创建智能体"""
        name = self.agent_name_input.text.strip()
        if not name:
            return

        agent_data = {
            "name": name,
            "gender": self.agent_gender_dropdown.options[
                self.agent_gender_dropdown.selected_index
            ],
            "age": self.agent_age_input.text.strip() or "30",
            "mbti": self.agent_mbti_dropdown.options[
                self.agent_mbti_dropdown.selected_index
            ],
            "occupation": self.agent_occupation_input.text.strip() or "未知",
            "background": self.agent_background_input.text.strip(),
        }

        self.created_agents.append(agent_data)

        # 清空输入框
        self.agent_name_input.text = ""
        self.agent_age_input.text = ""
        self.agent_occupation_input.text = ""
        self.agent_background_input.text = ""
        # 重置下拉框
        self.agent_gender_dropdown.selected_index = 0
        self.agent_mbti_dropdown.selected_index = 0

        if self.interface.on_agent_created:
            self.interface.on_agent_created(agent_data)

    def _on_import_agent(self):
        """导入智能体"""
        if self.interface.on_agent_imported:
            self.interface.on_agent_imported({})

    def _on_clear_agents(self):
        """清空智能体列表"""
        self.created_agents = []

    def _on_confirm_clicked(self):
        """确认按钮点击"""
        config = {}

        if self.current_selection == "scenario" and self.selected_scenario:
            config["scenario_type"] = self.selected_scenario
            config.update(self._get_scenario_config())
        elif self.current_selection == "agent":
            config["scenario_type"] = "daily_life"
            config["custom_agents"] = self.created_agents.copy()
        elif self.current_selection == "quickstart":
            config["quick_start"] = True
            config["scenario_type"] = "daily_life"
        else:
            config["quick_start"] = True
            config["scenario_type"] = "daily_life"

        if self.interface.on_quick_start:
            self.interface.on_quick_start(config)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """处理鼠标移动事件"""
        self.mouse_x = x
        self.mouse_y = y

        # 更新按钮悬停状态
        self.scenario_button.is_hovered = self.scenario_button.contains_point(x, y)
        self.agent_button.is_hovered = self.agent_button.contains_point(x, y)
        self.quickstart_button.is_hovered = self.quickstart_button.contains_point(x, y)
        self.session_button.is_hovered = self.session_button.contains_point(x, y)
        self.confirm_button.is_hovered = self.confirm_button.contains_point(x, y)

        if self.current_selection == "scenario":
            for btn in self.scenario_buttons:
                btn.is_hovered = btn.contains_point(x, y)
        elif self.current_selection == "agent":
            self.create_agent_button.is_hovered = self.create_agent_button.contains_point(x, y)
            self.import_agent_button.is_hovered = self.import_agent_button.contains_point(x, y)
            self.clear_agents_button.is_hovered = self.clear_agents_button.contains_point(x, y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """处理鼠标点击事件"""
        # 处理主按钮
        if self.scenario_button.contains_point(x, y):
            self.scenario_button.callback()
            return
        if self.agent_button.contains_point(x, y):
            self.agent_button.callback()
            return
        if self.quickstart_button.contains_point(x, y):
            self.quickstart_button.callback()
            return
        if self.session_button.contains_point(x, y):
            self.session_button.callback()
            return

        # 根据当前选择处理详情面板
        if self.current_selection == "scenario":
            for btn in self.scenario_buttons:
                if btn.contains_point(x, y):
                    btn.callback()
                    return

        elif self.current_selection == "agent":
            if self.create_agent_button.contains_point(x, y):
                self.create_agent_button.callback()
                return
            if self.import_agent_button.contains_point(x, y):
                self.import_agent_button.callback()
                return
            if self.clear_agents_button.contains_point(x, y):
                self.clear_agents_button.callback()
                return

        # 处理确认按钮
        if self.confirm_button.contains_point(x, y):
            self.confirm_button.callback()

    def draw(self):
        """绘制主界面"""
        # 绘制背景
        draw_rectangle_filled(
            self.rect_x + self.rect_width / 2,
            self.rect_y + self.rect_height / 2,
            self.rect_width, self.rect_height,
            self.BACKGROUND_COLOR
        )

        # 绘制标题
        arcade.draw_text(
            "多智能体社会模拟",
            self.rect_x + self.rect_width / 2,
            self.rect_y + self.rect_height - 30,
            self.TEXT_COLOR,
            28,
            anchor_x="center", anchor_y="center"
        )

        # 绘制分隔线
        divider_x = self.rect_x + 220
        arcade.draw_line(
            divider_x, self.rect_y + 20,
            divider_x, self.rect_y + self.rect_height - 20,
            self.BORDER_COLOR, 2
        )

        # 绘制主按钮
        self._draw_main_buttons()

        # 绘制详情面板
        if self.current_selection:
            self.detail_panel.draw()
            self._draw_detail_content()

        # 绘制确认按钮
        if self.current_selection:
            self.confirm_button.draw()

    def _draw_main_buttons(self):
        """绘制主按钮"""
        self.scenario_button.draw()
        self.agent_button.draw()
        self.quickstart_button.draw()
        self.session_button.draw()

        # 绘制选中边框
        is_selected_scenario = self.current_selection == "scenario"
        is_selected_agent = self.current_selection == "agent"
        is_selected_quickstart = self.current_selection == "quickstart"
        is_selected_session = self.current_selection == "session"

        if is_selected_scenario:
            self._draw_selected_border(self.scenario_button)
        if is_selected_agent:
            self._draw_selected_border(self.agent_button)
        if is_selected_quickstart:
            self._draw_selected_border(self.quickstart_button)
        if is_selected_session:
            self._draw_selected_border(self.session_button)

    def _draw_selected_border(self, button: Button):
        """绘制选中边框"""
        draw_rectangle_outline(
            button.x + button.width / 2, button.y + button.height / 2,
            button.width + 6, button.height + 6,
            self.ACCENT_COLOR, 3
        )

    def _draw_detail_content(self):
        """绘制详情内容"""
        if self.current_selection == "scenario":
            self._draw_scenario_content()
        elif self.current_selection == "agent":
            self._draw_agent_content()
        elif self.current_selection == "quickstart":
            self._draw_quickstart_content()

    def _draw_scenario_content(self):
        """绘制场景选择内容"""
        # 绘制场景选择按钮
        for i, btn in enumerate(self.scenario_buttons):
            btn.draw()

        # 绘制场景详情
        if self.scenario_detail_text:
            self.scenario_detail_panel.draw()
            lines = self.scenario_detail_text.split("\n")
            y_offset = self.scenario_detail_panel.y + self.scenario_detail_panel.height - 40
            for line in lines:
                arcade.draw_text(
                    line,
                    self.scenario_detail_panel.x + 15, y_offset,
                    self.TEXT_COLOR,
                    16,
                    anchor_x="left", anchor_y="center"
                )
                y_offset -= 25

        # 绘制配置输入
        self.scenario_config_panel.draw()
        config_y = self.scenario_config_panel.y + self.scenario_config_panel.height - 40
        input_height = 30
        label_width = 90
        input_x = self.scenario_config_panel.x + label_width + 10
        input_width = self.scenario_config_panel.width - label_width - 30

        # 智能体数量标签
        arcade.draw_text(
            "智能体数量:",
            self.scenario_config_panel.x + 10, config_y,
            self.TEXT_COLOR, 16,
            anchor_x="left", anchor_y="center"
        )
        self.agent_count_input.x = input_x
        self.agent_count_input.y = config_y - input_height / 2
        self.agent_count_input.width = input_width
        self.agent_count_input.height = input_height
        self.agent_count_input.draw()

        # 轮次数量标签
        config_y -= 40
        arcade.draw_text(
            "模拟轮次:",
            self.scenario_config_panel.x + 10, config_y,
            self.TEXT_COLOR, 16,
            anchor_x="left", anchor_y="center"
        )
        self.round_count_input.x = input_x
        self.round_count_input.y = config_y - input_height / 2
        self.round_count_input.width = input_width
        self.round_count_input.height = input_height
        self.round_count_input.draw()

        # 根据场景类型显示额外输入框
        config_y -= 40
        if self.selected_scenario == "emergency":
            arcade.draw_text(
                "突发事件:",
                self.scenario_config_panel.x + 10, config_y,
                self.TEXT_COLOR, 16,
                anchor_x="left", anchor_y="center"
            )
            self.emergency_topic_input.x = input_x
            self.emergency_topic_input.y = config_y - input_height / 2
            self.emergency_topic_input.width = input_width
            self.emergency_topic_input.height = input_height
            self.emergency_topic_input.draw()
        elif self.selected_scenario == "debate":
            arcade.draw_text(
                "辩论观点:",
                self.scenario_config_panel.x + 10, config_y,
                self.TEXT_COLOR, 16,
                anchor_x="left", anchor_y="center"
            )
            self.debate_topic_input.x = input_x
            self.debate_topic_input.y = config_y - input_height / 2
            self.debate_topic_input.width = input_width
            self.debate_topic_input.height = input_height
            self.debate_topic_input.draw()

    def _draw_agent_content(self):
        """绘制智能体管理内容"""
        panel_x = self.detail_panel.x + 20
        panel_y = self.detail_panel.y + 50
        input_height = 35
        input_margin = 10
        label_width = 80

        y = panel_y

        # 姓名标签
        arcade.draw_text(
            "姓名:",
            panel_x, y + 8,
            self.TEXT_COLOR, 16,
            anchor_x="left", anchor_y="center"
        )
        self.agent_name_input.draw()

        # 性别标签
        arcade.draw_text(
            "性别:",
            panel_x + (self.detail_panel.width - 40) // 2 + 10, y + 8,
            self.TEXT_COLOR, 16,
            anchor_x="left", anchor_y="center"
        )

        y += input_height + input_margin
        self.agent_gender_dropdown.draw()

        # 年龄标签
        arcade.draw_text(
            "年龄:",
            panel_x, y + 8,
            self.TEXT_COLOR, 16,
            anchor_x="left", anchor_y="center"
        )
        self.agent_age_input.draw()

        # MBTI标签
        arcade.draw_text(
            "MBTI:",
            panel_x + (self.detail_panel.width - 40) // 2 + 10, y + 8,
            self.TEXT_COLOR, 16,
            anchor_x="left", anchor_y="center"
        )

        y += input_height + input_margin
        self.agent_mbti_dropdown.draw()

        # 职业标签
        y += input_height + input_margin
        arcade.draw_text(
            "职业:",
            panel_x, y + 8,
            self.TEXT_COLOR, 16,
            anchor_x="left", anchor_y="center"
        )
        self.agent_occupation_input.draw()

        # 背景标签
        y += input_height + input_margin
        arcade.draw_text(
            "背景:",
            panel_x, y + 8,
            self.TEXT_COLOR, 16,
            anchor_x="left", anchor_y="center"
        )
        self.agent_background_input.draw()

        # 绘制操作按钮
        y += input_height * 2 + 30
        self.create_agent_button.y = y
        self.import_agent_button.y = y
        self.create_agent_button.draw()
        self.import_agent_button.draw()

        # 绘制智能体列表
        y += 50
        self.agent_list_panel.y = y
        self.agent_list_panel.draw()

        # 绘制列表内容
        list_y = self.agent_list_panel.y + self.agent_list_panel.height - 40
        for i, agent in enumerate(self.created_agents[-6:]):
            agent_text = f"{agent['name']} | {agent['gender']} | {agent['age']}岁 | {agent['mbti']}"
            if agent.get('occupation'):
                agent_text += f" | {agent['occupation']}"
            arcade.draw_text(
                agent_text,
                self.agent_list_panel.x + 15, list_y,
                self.TEXT_COLOR, 14,
                anchor_x="left", anchor_y="center"
            )
            list_y -= 22

        # 绘制清空按钮
        self.clear_agents_button.y = self.agent_list_panel.y + 35
        self.clear_agents_button.draw()

        # 显示数量统计
        count_text = f"共 {len(self.created_agents)} 个智能体"
        arcade.draw_text(
            count_text,
            self.agent_list_panel.x + 15,
            self.agent_list_panel.y + 10,
            (180, 180, 180), 14,
            anchor_x="left", anchor_y="center"
        )

    def _draw_quickstart_content(self):
        """绘制快速开始内容"""
        panel_x = self.detail_panel.x + 20
        panel_y = self.detail_panel.y + 50

        for i, line in enumerate(self.quickstart_info):
            text_color = (180, 180, 180) if i > 0 and line else self.TEXT_COLOR
            arcade.draw_text(
                line,
                panel_x, panel_y + i * 30,
                text_color, 16,
                anchor_x="left", anchor_y="center"
            )

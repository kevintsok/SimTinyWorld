"""
MainView - 主界面模块

提供主界面的交互界面，包括：
- 场景选择
- 智能体管理
- 快速开始
"""

import pygame
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass

from ui.components import Button, Panel, TextBox, Dropdown
from ui.fonts import get_font


@dataclass
class MainViewInterface:
    """主视图回调接口"""
    on_scenario_selected: Callable[[str, dict], None] = None
    on_agent_created: Callable[[dict], None] = None
    on_agent_imported: Callable[[dict], None] = None
    on_quick_start: Callable[[dict], None] = None


class MainView:
    """主界面视图

    提供三个主选项的垂直布局 + 右侧面板设计：
    - 左侧：三个大按钮（场景、智能体、快速开始）
    - 右侧：根据选择显示对应内容
    """

    # 配色方案
    BACKGROUND_COLOR = (30, 33, 40)
    PANEL_COLOR = (40, 44, 52)
    BUTTON_COLOR = (70, 130, 180)
    BUTTON_HOVER_COLOR = (100, 160, 210)
    TEXT_COLOR = (255, 255, 255)
    ACCENT_COLOR = (100, 160, 210)
    BORDER_COLOR = (60, 64, 72)

    # 可用场景列表
    AVAILABLE_SCENARIOS = [
        ("daily_life", "日常生活", "日常生活的社交互动场景"),
        ("emergency", "突发事件", "社会突发事件的应急场景"),
        ("debate", "观点辩论", "观点阐述与辩论场景"),
    ]

    # MBTI选项
    MBTI_TYPES = [
        "INTJ", "INTP", "ENTJ", "ENTP",
        "INFJ", "INFP", "ENFJ", "ENFP",
        "ISTJ", "ISFJ", "ESTJ", "ESFJ",
        "ISTP", "ISFP", "ESTP", "ESFP"
    ]

    # 性别选项
    GENDER_OPTIONS = ["男", "女"]

    def __init__(self, screen: pygame.Surface, rect: pygame.Rect,
                 interface: Optional[MainViewInterface] = None):
        """初始化主界面

        Args:
            screen: pygame屏幕对象
            rect: 主界面区域
            interface: 回调接口
        """
        self.screen = screen
        self.rect = rect
        self.interface = interface or MainViewInterface()

        # 字体
        self.title_font = get_font(28)
        self.heading_font = get_font(20)
        self.normal_font = get_font(16)
        self.small_font = get_font(14)

        # 当前选中的主选项
        self.current_selection: Optional[str] = None  # None, "scenario", "agent", "quickstart"

        # 左侧按钮区域
        button_width = 180
        button_height = 80
        button_margin = 20
        left_x = self.rect.x + 30
        top_y = self.rect.y + 80

        # 三个主按钮
        self.scenario_button = Button(
            rect=pygame.Rect(left_x, top_y, button_width, button_height),
            text="场景",
            callback=lambda: self._on_main_button_clicked("scenario"),
            color=self.BUTTON_COLOR,
            hover_color=self.BUTTON_HOVER_COLOR,
        )

        self.agent_button = Button(
            rect=pygame.Rect(left_x, top_y + button_height + button_margin,
                             button_width, button_height),
            text="智能体",
            callback=lambda: self._on_main_button_clicked("agent"),
            color=self.BUTTON_COLOR,
            hover_color=self.BUTTON_HOVER_COLOR,
        )

        self.quickstart_button = Button(
            rect=pygame.Rect(left_x, top_y + (button_height + button_margin) * 2,
                             button_width, button_height),
            text="快速开始",
            callback=lambda: self._on_main_button_clicked("quickstart"),
            color=(80, 160, 100),
            hover_color=(100, 180, 120),
        )

        # 右侧面板区域
        panel_x = self.rect.x + 250
        panel_width = self.rect.width - 280
        panel_height = self.rect.height - 100
        self.detail_panel = Panel(
            rect=pygame.Rect(panel_x, top_y, panel_width, panel_height),
            title="",
            background_color=self.PANEL_COLOR,
            border_color=self.BORDER_COLOR,
        )

        # 场景选择相关
        self._init_scenario_panel()

        # 智能体管理相关
        self._init_agent_panel()

        # 快速开始相关
        self._init_quickstart_panel()

        # 底部确认按钮
        confirm_button_width = 160
        confirm_button_height = 45
        self.confirm_button = Button(
            rect=pygame.Rect(
                self.rect.right - confirm_button_width - 30,
                self.rect.bottom - confirm_button_height - 20,
                confirm_button_width,
                confirm_button_height
            ),
            text="启动模拟",
            callback=self._on_confirm_clicked,
            color=(80, 160, 100),
            hover_color=(100, 180, 120),
        )

        # 选中状态指示
        self.selection_indicators = {
            "scenario": False,
            "agent": False,
            "quickstart": False,
        }

    def _init_scenario_panel(self):
        """初始化场景选择面板"""
        panel_x = self.detail_panel.rect.x + 20
        panel_y = self.detail_panel.rect.y + 50
        panel_width = self.detail_panel.rect.width - 40
        item_height = 60
        item_margin = 10

        # 场景选项按钮
        self.scenario_buttons: List[Button] = []
        self.selected_scenario: Optional[str] = None

        for i, (scenario_id, scenario_name, scenario_desc) in enumerate(
                self.AVAILABLE_SCENARIOS):
            btn = Button(
                rect=pygame.Rect(panel_x, panel_y + i * (item_height + item_margin),
                                panel_width, item_height),
                text=f"{scenario_name}",
                callback=lambda sid=scenario_id: self._on_scenario_selected(sid),
                color=(50, 54, 62),
                hover_color=(70, 74, 82),
            )
            self.scenario_buttons.append(btn)

        # 场景详情区域
        detail_y = panel_y + len(self.AVAILABLE_SCENARIOS) * (item_height + item_margin) + 20
        self.scenario_detail_panel = Panel(
            rect=pygame.Rect(panel_x, detail_y, panel_width, 200),
            title="场景详情",
            background_color=(50, 54, 62),
            border_color=self.BORDER_COLOR,
        )
        self.scenario_detail_text = ""

        # 场景参数配置
        config_y = detail_y + 230
        self.scenario_config_panel = Panel(
            rect=pygame.Rect(panel_x, config_y, panel_width, 150),
            title="场景配置",
            background_color=(50, 54, 62),
            border_color=self.BORDER_COLOR,
        )

        # 场景配置输入框
        config_label_width = 100
        input_width = panel_width - config_label_width - 20
        input_height = 30

        self.agent_count_input = TextBox(
            rect=pygame.Rect(panel_x + config_label_width, config_y + 50,
                            input_width, input_height),
            placeholder="智能体数量 (默认5)",
            max_length=10
        )

        self.round_count_input = TextBox(
            rect=pygame.Rect(panel_x + config_label_width, config_y + 90,
                            input_width, input_height),
            placeholder="轮次数量 (默认5)",
            max_length=10
        )

    def _init_agent_panel(self):
        """初始化智能体管理面板"""
        panel_x = self.detail_panel.rect.x + 20
        panel_y = self.detail_panel.rect.y + 50
        panel_width = self.detail_panel.rect.width - 40
        input_height = 35
        input_margin = 10

        # 标签宽度
        label_width = 80
        input_width = (panel_width - label_width - 30) // 2

        # 姓名
        y = panel_y
        self.agent_name_input = TextBox(
            rect=pygame.Rect(panel_x + label_width, y, input_width, input_height),
            placeholder="姓名",
            max_length=20
        )

        # 性别下拉框
        self.agent_gender_dropdown = Dropdown(
            rect=pygame.Rect(panel_x + label_width + input_width + 10, y,
                            input_width, input_height),
            options=self.GENDER_OPTIONS,
            title="性别"
        )

        # 年龄
        y += input_height + input_margin
        self.agent_age_input = TextBox(
            rect=pygame.Rect(panel_x + label_width, y, input_width, input_height),
            placeholder="年龄",
            max_length=3
        )

        # MBTI下拉框
        self.agent_mbti_dropdown = Dropdown(
            rect=pygame.Rect(panel_x + label_width + input_width + 10, y,
                            input_width, input_height),
            options=self.MBTI_TYPES,
            title="MBTI"
        )

        # 职业
        y += input_height + input_margin
        self.agent_occupation_input = TextBox(
            rect=pygame.Rect(panel_x + label_width, y,
                            panel_width - label_width, input_height),
            placeholder="职业",
            max_length=50
        )

        # 背景
        y += input_height + input_margin
        self.agent_background_input = TextBox(
            rect=pygame.Rect(panel_x + label_width, y,
                            panel_width - label_width, input_height * 2),
            placeholder="背景描述 (可选)",
            max_length=200
        )

        # 操作按钮
        y += input_height * 2 + 30
        button_width = 120
        button_height = 40
        button_margin = 20

        self.create_agent_button = Button(
            rect=pygame.Rect(panel_x, y, button_width, button_height),
            text="创建智能体",
            callback=self._on_create_agent,
            color=(80, 160, 100),
            hover_color=(100, 180, 120),
        )

        self.import_agent_button = Button(
            rect=pygame.Rect(panel_x + button_width + button_margin, y,
                            button_width, button_height),
            text="导入智能体",
            callback=self._on_import_agent,
            color=self.BUTTON_COLOR,
            hover_color=self.BUTTON_HOVER_COLOR,
        )

        # 已创建智能体列表
        y += button_height + 30
        self.agent_list_panel = Panel(
            rect=pygame.Rect(panel_x, y, panel_width, 180),
            title="已创建的智能体",
            background_color=(50, 54, 62),
            border_color=self.BORDER_COLOR,
        )
        self.created_agents: List[dict] = []

        # 清除按钮
        self.clear_agents_button = Button(
            rect=pygame.Rect(panel_x + panel_width - 100, y + 35, 90, 30),
            text="清空列表",
            callback=self._on_clear_agents,
            color=(160, 80, 80),
            hover_color=(180, 100, 100),
        )

    def _init_quickstart_panel(self):
        """初始化快速开始面板"""
        panel_x = self.detail_panel.rect.x + 20
        panel_y = self.detail_panel.rect.y + 50
        panel_width = self.detail_panel.rect.width - 40

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

    def _on_main_button_clicked(self, selection: str):
        """主按钮点击处理"""
        self.current_selection = selection
        # 更新面板标题
        if selection == "scenario":
            self.detail_panel.title = "场景选择"
        elif selection == "agent":
            self.detail_panel.title = "智能体管理"
        elif selection == "quickstart":
            self.detail_panel.title = "快速开始"

    def _on_scenario_selected(self, scenario_id: str):
        """场景选项点击处理"""
        self.selected_scenario = scenario_id

        # 找到场景描述
        scenario_desc = ""
        for sid, _, desc in self.AVAILABLE_SCENARIOS:
            if sid == scenario_id:
                scenario_desc = desc
                break

        # 更新场景详情文本
        scenario_name = ""
        for sid, name, _ in self.AVAILABLE_SCENARIOS:
            if sid == scenario_id:
                scenario_name = name
                break

        self.scenario_detail_text = f"当前选择: {scenario_name}\n\n{scenario_desc}"

        # 调用回调
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

        # 调用回调
        if self.interface.on_agent_created:
            self.interface.on_agent_created(agent_data)

    def _on_import_agent(self):
        """导入智能体"""
        # 这里是占位实现，实际可以通过文件选择对话框导入
        # 目前只是触发回调，具体导入逻辑由外部处理
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
            # 默认快速开始
            config["quick_start"] = True
            config["scenario_type"] = "daily_life"

        if self.interface.on_quick_start:
            self.interface.on_quick_start(config)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理事件

        Args:
            event: pygame事件

        Returns:
            bool: 是否处理了此事件
        """
        # 处理主按钮事件
        if self.scenario_button.handle_event(event):
            return True
        if self.agent_button.handle_event(event):
            return True
        if self.quickstart_button.handle_event(event):
            return True

        # 根据当前选择处理详情面板事件
        if self.current_selection == "scenario":
            for btn in self.scenario_buttons:
                if btn.handle_event(event):
                    return True
            # 输入框处理
            if self.agent_count_input.handle_event(event):
                return True
            if self.round_count_input.handle_event(event):
                return True

        elif self.current_selection == "agent":
            # 输入框处理
            if self.agent_name_input.handle_event(event):
                return True
            if self.agent_age_input.handle_event(event):
                return True
            if self.agent_occupation_input.handle_event(event):
                return True
            if self.agent_background_input.handle_event(event):
                return True

            # 下拉框处理
            if self.agent_gender_dropdown.handle_event(event):
                return True
            if self.agent_mbti_dropdown.handle_event(event):
                return True

            # 按钮处理
            if self.create_agent_button.handle_event(event):
                return True
            if self.import_agent_button.handle_event(event):
                return True
            if self.clear_agents_button.handle_event(event):
                return True

        # 处理确认按钮
        if self.confirm_button.handle_event(event):
            return True

        return False

    def draw(self, surface: pygame.Surface):
        """绘制主界面"""
        # 绘制背景
        pygame.draw.rect(surface, self.BACKGROUND_COLOR, self.rect, border_radius=10)

        # 绘制标题
        title = self.title_font.render("多智能体社会模拟", True, self.TEXT_COLOR)
        title_rect = title.get_rect(
            centerx=self.rect.centerx,
            top=self.rect.top + 20
        )
        surface.blit(title, title_rect)

        # 绘制分隔线
        divider_x = self.rect.x + 220
        pygame.draw.line(
            surface,
            self.BORDER_COLOR,
            (divider_x, self.rect.top + 20),
            (divider_x, self.rect.bottom - 20),
            2
        )

        # 绘制主按钮（带选中指示）
        self._draw_main_buttons(surface)

        # 绘制详情面板
        if self.current_selection:
            self.detail_panel.draw(surface)
            self._draw_detail_content(surface)

        # 绘制确认按钮
        if self.current_selection:
            self.confirm_button.draw(surface)

    def _draw_main_buttons(self, surface: pygame.Surface):
        """绘制主按钮"""
        buttons = [
            (self.scenario_button, "场景"),
            (self.agent_button, "智能体"),
            (self.quickstart_button, "快速开始"),
        ]

        for btn, label in buttons:
            # 绘制按钮
            btn.draw(surface)

            # 如果选中，绘制边框指示
            is_selected = (
                (label == "场景" and self.current_selection == "scenario") or
                (label == "智能体" and self.current_selection == "agent") or
                (label == "快速开始" and self.current_selection == "quickstart")
            )

            if is_selected:
                # 绘制选中边框
                border_rect = btn.rect.inflate(6, 6)
                pygame.draw.rect(
                    surface,
                    self.ACCENT_COLOR,
                    border_rect,
                    3,
                    border_radius=8
                )

    def _draw_detail_content(self, surface: pygame.Surface):
        """绘制详情内容"""
        if self.current_selection == "scenario":
            self._draw_scenario_content(surface)
        elif self.current_selection == "agent":
            self._draw_agent_content(surface)
        elif self.current_selection == "quickstart":
            self._draw_quickstart_content(surface)

    def _draw_scenario_content(self, surface: pygame.Surface):
        """绘制场景选择内容"""
        panel_x = self.detail_panel.rect.x + 20
        panel_y = self.detail_panel.rect.y + 50

        # 绘制场景选择按钮
        for i, btn in enumerate(self.scenario_buttons):
            # 标记选中状态
            scenario_id = self.AVAILABLE_SCENARIOS[i][0]
            if self.selected_scenario == scenario_id:
                original_color = btn.color
                btn.color = self.BUTTON_COLOR
                btn.draw(surface)
                btn.color = original_color
            else:
                btn.draw(surface)

            # 绘制描述
            desc = self.AVAILABLE_SCENARIOS[i][2]
            desc_surface = self.small_font.render(desc, True, (180, 180, 180))
            desc_rect = desc_surface.get_rect(
                left=btn.rect.right + 15,
                centery=btn.rect.centery
            )
            surface.blit(desc_surface, desc_rect)

        # 绘制场景详情
        if self.scenario_detail_text:
            self.scenario_detail_panel.draw(surface)
            lines = self.scenario_detail_text.split("\n")
            y_offset = self.scenario_detail_panel.rect.y + 40
            for line in lines:
                text_surface = self.normal_font.render(line, True, self.TEXT_COLOR)
                surface.blit(text_surface, (self.scenario_detail_panel.rect.x + 15, y_offset))
                y_offset += 25

        # 绘制配置输入
        self.scenario_config_panel.draw(surface)
        config_y = self.scenario_config_panel.rect.y + 40

        # 智能体数量标签
        label = self.normal_font.render("智能体数量:", True, self.TEXT_COLOR)
        surface.blit(label, (self.scenario_config_panel.rect.x + 15, config_y + 5))
        self.agent_count_input.draw(surface)

        # 轮次数量标签
        config_y += 40
        label = self.normal_font.render("模拟轮次:", True, self.TEXT_COLOR)
        surface.blit(label, (self.scenario_config_panel.rect.x + 15, config_y + 5))
        self.round_count_input.draw(surface)

    def _draw_agent_content(self, surface: pygame.Surface):
        """绘制智能体管理内容"""
        panel_x = self.detail_panel.rect.x + 20
        panel_y = self.detail_panel.rect.y + 50
        input_height = 35
        input_margin = 10
        label_width = 80

        # 绘制输入标签
        y = panel_y

        # 姓名标签
        label = self.normal_font.render("姓名:", True, self.TEXT_COLOR)
        surface.blit(label, (panel_x, y + 8))
        self.agent_name_input.draw(surface)

        # 性别标签
        label = self.normal_font.render("性别:", True, self.TEXT_COLOR)
        surface.blit(label, (panel_x + (self.detail_panel.rect.width - 40) // 2 + 10, y + 8))

        y += input_height + input_margin
        self.agent_gender_dropdown.draw(surface)

        # 年龄标签
        label = self.normal_font.render("年龄:", True, self.TEXT_COLOR)
        surface.blit(label, (panel_x, y + 8))
        self.agent_age_input.draw(surface)

        # MBTI标签
        label = self.normal_font.render("MBTI:", True, self.TEXT_COLOR)
        surface.blit(label, (panel_x + (self.detail_panel.rect.width - 40) // 2 + 10, y + 8))

        y += input_height + input_margin
        self.agent_mbti_dropdown.draw(surface)

        # 职业标签
        y += input_height + input_margin
        label = self.normal_font.render("职业:", True, self.TEXT_COLOR)
        surface.blit(label, (panel_x, y + 8))
        self.agent_occupation_input.draw(surface)

        # 背景标签
        y += input_height + input_margin
        label = self.normal_font.render("背景:", True, self.TEXT_COLOR)
        surface.blit(label, (panel_x, y + 8))
        self.agent_background_input.draw(surface)

        # 绘制操作按钮
        y += input_height * 2 + 30
        self.create_agent_button.rect.y = y
        self.import_agent_button.rect.y = y
        self.create_agent_button.draw(surface)
        self.import_agent_button.draw(surface)

        # 绘制智能体列表
        y += 50
        self.agent_list_panel.rect.y = y
        self.agent_list_panel.draw(surface)

        # 绘制列表内容
        list_y = self.agent_list_panel.rect.y + 40
        for i, agent in enumerate(self.created_agents[-6:]):  # 最多显示6个
            agent_text = f"{agent['name']} | {agent['gender']} | {agent['age']}岁 | {agent['mbti']}"
            if agent.get('occupation'):
                agent_text += f" | {agent['occupation']}"
            text_surface = self.small_font.render(agent_text, True, self.TEXT_COLOR)
            surface.blit(text_surface, (self.agent_list_panel.rect.x + 15, list_y))
            list_y += 22

        # 绘制清空按钮
        self.clear_agents_button.rect.y = self.agent_list_panel.rect.y + 35
        self.clear_agents_button.draw(surface)

        # 显示数量统计
        count_text = f"共 {len(self.created_agents)} 个智能体"
        count_surface = self.small_font.render(count_text, True, (180, 180, 180))
        count_rect = count_surface.get_rect(
            left=self.agent_list_panel.rect.x + 15,
            bottom=self.agent_list_panel.rect.bottom - 10
        )
        surface.blit(count_surface, count_rect)

    def _draw_quickstart_content(self, surface: pygame.Surface):
        """绘制快速开始内容"""
        panel_x = self.detail_panel.rect.x + 20
        panel_y = self.detail_panel.rect.y + 50

        for i, line in enumerate(self.quickstart_info):
            text_color = (180, 180, 180) if i > 0 and line else self.TEXT_COLOR
            text_surface = self.normal_font.render(line, True, text_color)
            surface.blit(text_surface, (panel_x, panel_y + i * 30))

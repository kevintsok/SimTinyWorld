"""
Agent Panel - 智能体管理面板

提供启动界面、创建/导入智能体、场景选择等功能。
"""

import pygame
import os
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from ui.components import Button, Panel, TextBox, Dropdown
from ui.fonts import get_font


@dataclass
class AgentTemplate:
    """智能体模板"""
    name: str
    mbti: str
    gender: str
    age: int
    occupation: str
    background: str


class AgentPanel:
    """智能体管理面板"""

    # MBTI 类型列表
    MBTI_TYPES = [
        "INTJ", "INTP", "ENTJ", "ENTP",
        "INFJ", "INFP", "ENFJ", "ENFP",
        "ISTJ", "ISTP", "ESTJ", "ESTP",
        "ISFJ", "ISFP", "ESFJ", "ESFP"
    ]

    # 性别选项
    GENDERS = ["男", "女", "其他"]

    # 职业选项
    OCCUPATIONS = [
        "学生", "教师", "工程师", "医生", "律师", "会计师",
        "设计师", "艺术家", "作家", "记者", "公务员", "商人",
        "运动员", "厨师", "咖啡师", "自由职业"
    ]

    def __init__(self, width: int = 1000, height: int = 700):
        """初始化面板"""
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("智能体模拟世界 - 启动界面")

        # 字体
        self.font = get_font(14)
        self.font_large = get_font(18)
        self.font_title = get_font(28)

        # 颜色
        self.bg_color = (30, 33, 40)
        self.panel_bg = (40, 44, 52)
        self.text_color = (220, 220, 220)
        self.accent_color = (70, 130, 180)

        # 状态
        self.current_view = "main"  # main, create, import, settings
        self.agents: List[Dict] = []
        self.selected_agent_id: Optional[str] = None

        # 回调函数
        self.on_start_simulation: Optional[Callable] = None
        self.on_create_agent: Optional[Callable] = None
        self.on_import_agent: Optional[Callable] = None

        # 创建智能体数据
        self.new_agent_data = {
            "name": "",
            "mbti": "ENFP",
            "gender": "男",
            "age": 25,
            "occupation": "学生",
            "background": ""
        }

        # 模拟设置
        self.simulation_settings = {
            "agents": 3,
            "rounds": 5,
            "locations": 5,
            "scenario": "daily_life",
            "fast_mode": False
        }

        # 场景选项
        self.scenarios = [
            ("daily_life", "日常生活"),
            ("emergency", "突发事件"),
            ("debate", "多人辩论"),
            ("geopolitics", "地缘政治")
        ]

        # 导入的智能体列表
        self.imported_agents: List[Dict] = []

        # 组件
        self.buttons: List[Button] = []
        self.text_boxes: Dict[str, TextBox] = {}
        self.dropdowns: Dict[str, Dropdown] = {}
        self._init_components()

    def _init_components(self):
        """初始化UI组件"""
        # 主界面按钮
        panel_width = 400
        panel_height = 320
        panel_x = (self.width - panel_width) // 2
        panel_y = (self.height - panel_height) // 2 + 30

        # 创建/导入按钮
        self.buttons.append(Button(
            rect=pygame.Rect(panel_x + 50, panel_y + 60, 130, 45),
            text="创建智能体",
            callback=self._show_create_view,
            color=(70, 130, 180)
        ))

        self.buttons.append(Button(
            rect=pygame.Rect(panel_x + 200, panel_y + 60, 130, 45),
            text="导入智能体",
            callback=self._show_import_view,
            color=(80, 100, 80)
        ))

        # 快速开始按钮
        self.buttons.append(Button(
            rect=pygame.Rect(panel_x + 100, panel_y + 150, 200, 50),
            text="快速开始",
            callback=self._quick_start,
            color=(60, 140, 80)
        ))

        # 高级设置按钮
        self.buttons.append(Button(
            rect=pygame.Rect(panel_x + 100, panel_y + 210, 200, 40),
            text="高级设置",
            callback=self._show_settings,
            color=(90, 90, 90)
        ))

        # 创建界面组件
        self._init_create_components(panel_x, panel_y)

        # 导入界面组件
        self._init_import_components()

        # 设置界面组件
        self._init_settings_components(panel_x, panel_y)

    def _init_create_components(self, base_x: int, base_y: int):
        """初始化创建界面组件"""
        # 名称输入
        self.text_boxes["name"] = TextBox(
            rect=pygame.Rect(base_x + 120, base_y + 100, 200, 30),
            placeholder="输入名称"
        )

        # MBTI 下拉选择
        self.dropdowns["mbti"] = Dropdown(
            rect=pygame.Rect(base_x + 120, base_y + 150, 200, 30),
            options=self.MBTI_TYPES,
            title="MBTI"
        )

        # 性别下拉选择
        self.dropdowns["gender"] = Dropdown(
            rect=pygame.Rect(base_x + 120, base_y + 200, 200, 30),
            options=self.GENDERS,
            title="性别"
        )

        # 职业下拉选择
        self.dropdowns["occupation"] = Dropdown(
            rect=pygame.Rect(base_x + 120, base_y + 250, 200, 30),
            options=self.OCCUPATIONS,
            title="职业"
        )

        # 年龄输入
        self.text_boxes["age"] = TextBox(
            rect=pygame.Rect(base_x + 400, base_y + 100, 80, 30),
            placeholder="年龄"
        )

        # 背景输入
        self.text_boxes["background"] = TextBox(
            rect=pygame.Rect(base_x + 400, base_y + 150, 250, 150),
            placeholder="输入背景故事..."
        )

    def _init_import_components(self):
        """初始化导入界面组件"""
        self.import_list_start_y = 120

    def _init_settings_components(self, base_x: int, base_y: int):
        """初始化设置界面组件"""
        # 智能体数量
        self.text_boxes["agent_count"] = TextBox(
            rect=pygame.Rect(base_x + 150, base_y + 80, 80, 30),
            placeholder="3"
        )

        # 轮数
        self.text_boxes["rounds"] = TextBox(
            rect=pygame.Rect(base_x + 150, base_y + 130, 80, 30),
            placeholder="5"
        )

        # 位置数量
        self.text_boxes["locations"] = TextBox(
            rect=pygame.Rect(base_x + 150, base_y + 180, 80, 30),
            placeholder="5"
        )

        # 场景选择
        scenario_names = [name for _, name in self.scenarios]
        self.dropdowns["scenario"] = Dropdown(
            rect=pygame.Rect(base_x + 150, base_y + 230, 200, 30),
            options=scenario_names,
            title="场景"
        )

        # 快速模式复选框区域
        self.fast_mode_rect = pygame.Rect(base_x + 150, base_y + 280, 30, 30)

    def _show_create_view(self):
        """显示创建视图"""
        self.current_view = "create"

    def _show_import_view(self):
        """显示导入视图"""
        self.current_view = "import"
        self._load_saved_agents()

    def _show_settings(self):
        """显示设置视图"""
        self.current_view = "settings"

    def _quick_start(self):
        """快速开始"""
        self.simulation_settings["fast_mode"] = True
        if self.on_start_simulation:
            self.on_start_simulation(self.simulation_settings)

    def _load_saved_agents(self):
        """加载保存的智能体"""
        self.imported_agents = []
        history_dir = "agent/history"

        if not os.path.exists(history_dir):
            return

        for agent_id in os.listdir(history_dir):
            identity_file = os.path.join(history_dir, agent_id, "identity.txt")
            if os.path.exists(identity_file):
                try:
                    with open(identity_file, "r", encoding="utf-8") as f:
                        identity = json.load(f)
                        self.imported_agents.append(identity)
                except Exception as e:
                    print(f"加载智能体失败: {e}")

    def _select_imported_agent(self, agent_id: str):
        """选择要导入的智能体"""
        if self.selected_agent_id == agent_id:
            self.selected_agent_id = None
        else:
            self.selected_agent_id = agent_id

    def _confirm_import(self):
        """确认导入选中的智能体"""
        if self.selected_agent_id and self.on_import_agent:
            # 找到选中的智能体数据
            for agent in self.imported_agents:
                if agent.get("id") == self.selected_agent_id:
                    self.on_import_agent(agent)
                    break

    def draw_main_view(self, surface: pygame.Surface):
        """绘制主界面"""
        # 面板（先绘制，这样上面的标题会在面板上方）
        panel_width = 400
        panel_height = 320
        panel_x = (self.width - panel_width) // 2
        panel_y = (self.height - panel_height) // 2 + 30

        pygame.draw.rect(surface, self.panel_bg, (panel_x, panel_y, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(surface, self.accent_color, (panel_x, panel_y, panel_width, panel_height), 3, border_radius=10)

        # 标题（在面板上方）
        title = self.font_title.render("智能体模拟世界", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.width // 2, 80))
        surface.blit(title, title_rect)

        # 副标题（在面板上方）
        subtitle = self.font.render("Multi-Agent Social Simulation", True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 115))
        surface.blit(subtitle, subtitle_rect)

        # 面板标题
        panel_title = self.font_large.render("开始模拟", True, (255, 255, 255))
        surface.blit(panel_title, (panel_x + 20, panel_y + 20))

        # 绘制按钮
        for btn in self.buttons:
            btn.draw(surface)

    def draw_create_view(self, surface: pygame.Surface):
        """绘制创建界面"""
        # 标题
        title = self.font_title.render("创建新智能体", True, (255, 255, 255))
        surface.blit(title, (50, 50))

        # 返回按钮
        back_btn = Button(
            rect=pygame.Rect(50, 100, 100, 35),
            text="返回",
            callback=lambda: setattr(self, 'current_view', 'main'),
            color=(80, 80, 80)
        )
        back_btn.draw(surface)

        # 表单面板
        form_x, form_y = 50, 160
        pygame.draw.rect(surface, self.panel_bg, (form_x, form_y, 650, 400), border_radius=10)

        labels = [
            ("name", "姓名:", 0),
            ("mbti", "MBTI:", 50),
            ("gender", "性别:", 100),
            ("occupation", "职业:", 150),
            ("age", "年龄:", 0),
            ("background", "背景:", 50)
        ]

        # 绘制标签和输入框
        y_offset = form_y + 30

        # 姓名
        name_label = self.font.render("姓名:", True, self.text_color)
        surface.blit(name_label, (form_x + 30, y_offset + 5))
        self.text_boxes["name"].draw(surface)

        # MBTI
        mbti_label = self.font.render("MBTI:", True, self.text_color)
        surface.blit(mbti_label, (form_x + 30, y_offset + 55))
        self.dropdowns["mbti"].draw(surface)

        # 性别
        gender_label = self.font.render("性别:", True, self.text_color)
        surface.blit(gender_label, (form_x + 350, y_offset + 5))
        self.dropdowns["gender"].draw(surface)

        # 年龄
        age_label = self.font.render("年龄:", True, self.text_color)
        surface.blit(age_label, (form_x + 350, y_offset + 55))
        self.text_boxes["age"].draw(surface)

        # 职业
        occ_label = self.font.render("职业:", True, self.text_color)
        surface.blit(occ_label, (form_x + 30, y_offset + 105))
        self.dropdowns["occupation"].draw(surface)

        # 背景
        bg_label = self.font.render("背景:", True, self.text_color)
        surface.blit(bg_label, (form_x + 350, y_offset + 105))
        self.text_boxes["background"].draw(surface)

        # 创建按钮
        create_btn = Button(
            rect=pygame.Rect(form_x + 250, form_y + 340, 150, 45),
            text="创建",
            callback=self._do_create_agent,
            color=(60, 140, 80)
        )
        create_btn.draw(surface)

        # MBTI 说明
        mbti_info_y = form_y + 400
        info = self.font.render("E=外向型(三角形) I=内向型(圆形) 不同MBTI颜色不同", True, (150, 150, 150))
        surface.blit(info, (form_x + 30, mbti_info_y))

    def draw_import_view(self, surface: pygame.Surface):
        """绘制导入界面"""
        # 标题
        title = self.font_title.render("导入智能体", True, (255, 255, 255))
        surface.blit(title, (50, 50))

        # 返回按钮
        back_btn = Button(
            rect=pygame.Rect(50, 100, 100, 35),
            text="返回",
            callback=lambda: setattr(self, 'current_view', 'main'),
            color=(80, 80, 80)
        )
        back_btn.draw(surface)

        # 列表区域
        list_x, list_y = 50, 160
        list_width, list_height = 900, 350

        pygame.draw.rect(surface, self.panel_bg, (list_x, list_y, list_width, list_height), border_radius=10)

        if not self.imported_agents:
            no_agents = self.font.render("没有找到保存的智能体", True, (150, 150, 150))
            no_agents_rect = no_agents.get_rect(center=(list_x + list_width // 2, list_y + list_height // 2))
            surface.blit(no_agents, no_agents_rect)
        else:
            # 绘制智能体列表
            item_height = 60
            for i, agent in enumerate(self.imported_agents[:5]):  # 最多显示5个
                item_y = list_y + 15 + i * (item_height + 10)

                # 条目背景
                is_selected = agent.get("id") == self.selected_agent_id
                bg_color = (60, 70, 80) if is_selected else (50, 54, 62)
                item_rect = pygame.Rect(list_x + 15, item_y, list_width - 30, item_height)
                pygame.draw.rect(surface, bg_color, item_rect, border_radius=5)

                # 智能体信息
                name = agent.get("name", "未知")
                mbti = agent.get("mbti", "?")
                gender = agent.get("gender", "?")
                age = agent.get("age", "?")
                bg = agent.get("background", {})
                occupation = bg.get("occupation", "未知") if isinstance(bg, dict) else "未知"

                name_text = self.font_large.render(name, True, (255, 255, 255))
                surface.blit(name_text, (item_rect.x + 20, item_rect.y + 10))

                info_text = self.font.render(f"{mbti} | {gender} | {age}岁 | {occupation}", True, (180, 180, 180))
                surface.blit(info_text, (item_rect.x + 20, item_rect.y + 35))

        # 导入按钮
        import_btn = Button(
            rect=pygame.Rect(400, list_y + list_height + 30, 150, 45),
            text="导入选中",
            callback=self._confirm_import,
            color=(60, 140, 80),
            enabled=self.selected_agent_id is not None
        )
        import_btn.draw(surface)

    def draw_settings_view(self, surface: pygame.Surface):
        """绘制设置界面"""
        # 标题
        title = self.font_title.render("高级设置", True, (255, 255, 255))
        surface.blit(title, (50, 50))

        # 返回按钮
        back_btn = Button(
            rect=pygame.Rect(50, 100, 100, 35),
            text="返回",
            callback=lambda: setattr(self, 'current_view', 'main'),
            color=(80, 80, 80)
        )
        back_btn.draw(surface)

        # 设置面板
        form_x, form_y = 50, 160
        pygame.draw.rect(surface, self.panel_bg, (form_x, form_y, 500, 350), border_radius=10)

        labels = [
            ("agent_count", "智能体数量:", 0),
            ("rounds", "模拟轮数:", 50),
            ("locations", "位置数量:", 100),
            ("scenario", "场景:", 150)
        ]

        y_offset = form_y + 30
        for key, label_text, offset in labels:
            label = self.font.render(label_text, True, self.text_color)
            surface.blit(label, (form_x + 30, y_offset + offset + 5))

            if key in self.text_boxes:
                self.text_boxes[key].draw(surface)
            elif key in self.dropdowns:
                self.dropdowns[key].draw(surface)

        # 快速模式复选框
        fast_label = self.font.render("快速模式 (不调用LLM):", True, self.text_color)
        surface.blit(fast_label, (form_x + 30, y_offset + 200))

        checkbox_rect = pygame.Rect(form_x + 250, y_offset + 200, 30, 30)
        pygame.draw.rect(surface, (60, 64, 72), checkbox_rect, border_radius=5)
        if self.simulation_settings["fast_mode"]:
            pygame.draw.rect(surface, self.accent_color, checkbox_rect, border_radius=5)
            check_text = self.font.render("V", True, (255, 255, 255))
            check_rect = check_text.get_rect(center=checkbox_rect.center)
            surface.blit(check_text, check_rect)

        # 确定按钮
        confirm_btn = Button(
            rect=pygame.Rect(form_x + 175, form_y + 280, 150, 45),
            text="确定",
            callback=self._apply_settings,
            color=(60, 140, 80)
        )
        confirm_btn.draw(surface)

    def _do_create_agent(self):
        """执行创建智能体"""
        name = self.text_boxes["name"].text.strip()
        if not name:
            name = f"Agent_{len(self.agents) + 1}"

        mbti = self.MBTI_TYPES[self.dropdowns["mbti"].selected_index]
        gender = self.GENDERS[self.dropdowns["gender"].selected_index]
        occupation = self.OCCUPATIONS[self.dropdowns["occupation"].selected_index]

        try:
            age = int(self.text_boxes["age"].text.strip())
        except:
            age = 25

        background = self.text_boxes["background"].text.strip()
        if not background:
            background = f"一个{occupation}，正在探索这个世界。"

        agent_data = {
            "name": name,
            "mbti": mbti,
            "gender": gender,
            "age": age,
            "occupation": occupation,
            "background": background
        }

        self.agents.append(agent_data)

        if self.on_create_agent:
            self.on_create_agent(agent_data)

        # 清空表单
        self.text_boxes["name"].text = ""
        self.text_boxes["age"].text = ""
        self.text_boxes["background"].text = ""

        # 返回主界面
        self.current_view = "main"

    def _apply_settings(self):
        """应用设置"""
        try:
            self.simulation_settings["agents"] = int(self.text_boxes["agent_count"].text.strip())
        except:
            pass

        try:
            self.simulation_settings["rounds"] = int(self.text_boxes["rounds"].text.strip())
        except:
            pass

        try:
            self.simulation_settings["locations"] = int(self.text_boxes["locations"].text.strip())
        except:
            pass

        # 场景
        scenario_names = [name for name, _ in self.scenarios]
        selected_name = self.dropdowns["scenario"].options[self.dropdowns["scenario"].selected_index]
        for i, (_, display_name) in enumerate(self.scenarios):
            if display_name == selected_name:
                self.simulation_settings["scenario"] = scenario_names[i]
                break

        self.current_view = "main"

    def draw(self):
        """绘制当前视图"""
        self.screen.fill(self.bg_color)

        if self.current_view == "main":
            self.draw_main_view(self.screen)
        elif self.current_view == "create":
            self.draw_create_view(self.screen)
        elif self.current_view == "import":
            self.draw_import_view(self.screen)
        elif self.current_view == "settings":
            self.draw_settings_view(self.screen)

        pygame.display.flip()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理事件，返回是否退出"""
        if event.type == pygame.QUIT:
            return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 主界面按钮
            for btn in self.buttons:
                btn.handle_event(event)

            # 创建界面
            if self.current_view == "create":
                for tb in self.text_boxes.values():
                    tb.handle_event(event)
                for dd in self.dropdowns.values():
                    dd.handle_event(event)

                # 返回按钮
                back_btn = Button(
                    rect=pygame.Rect(50, 100, 100, 35),
                    text="返回",
                    callback=lambda: setattr(self, 'current_view', 'main'),
                    color=(80, 80, 80)
                )
                back_btn.handle_event(event)

                # 创建按钮
                create_btn = Button(
                    rect=pygame.Rect(300, 500, 150, 45),
                    text="创建",
                    callback=self._do_create_agent,
                    color=(60, 140, 80)
                )
                create_btn.handle_event(event)

            # 导入界面
            elif self.current_view == "import":
                # 检查列表项点击
                list_x, list_y = 50, 160
                list_width, list_height = 900, 350
                item_height = 60

                for i, agent in enumerate(self.imported_agents[:5]):
                    item_rect = pygame.Rect(list_x + 15, list_y + 15 + i * (item_height + 10),
                                           list_width - 30, item_height)
                    if item_rect.collidepoint(event.pos):
                        self._select_imported_agent(agent.get("id"))

                # 返回按钮
                back_btn = Button(
                    rect=pygame.Rect(50, 100, 100, 35),
                    text="返回",
                    callback=lambda: setattr(self, 'current_view', 'main'),
                    color=(80, 80, 80)
                )
                back_btn.handle_event(event)

                # 导入按钮
                import_btn = Button(
                    rect=pygame.Rect(400, list_y + list_height + 30, 150, 45),
                    text="导入选中",
                    callback=self._confirm_import,
                    color=(60, 140, 80),
                    enabled=self.selected_agent_id is not None
                )
                import_btn.handle_event(event)

            # 设置界面
            elif self.current_view == "settings":
                for tb in self.text_boxes.values():
                    tb.handle_event(event)
                for dd in self.dropdowns.values():
                    dd.handle_event(event)

                # 快速模式复选框
                form_x, form_y = 50, 160
                y_offset = form_y + 30
                checkbox_rect = pygame.Rect(form_x + 250, y_offset + 200, 30, 30)
                if checkbox_rect.collidepoint(event.pos):
                    self.simulation_settings["fast_mode"] = not self.simulation_settings["fast_mode"]

                # 返回按钮
                back_btn = Button(
                    rect=pygame.Rect(50, 100, 100, 35),
                    text="返回",
                    callback=lambda: setattr(self, 'current_view', 'main'),
                    color=(80, 80, 80)
                )
                back_btn.handle_event(event)

                # 确定按钮
                confirm_btn = Button(
                    rect=pygame.Rect(300, 510, 150, 45),
                    text="确定",
                    callback=self._apply_settings,
                    color=(60, 140, 80)
                )
                confirm_btn.handle_event(event)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.current_view != "main":
                    self.current_view = "main"
                else:
                    return True

            # 输入框处理
            if event.key == pygame.K_TAB:
                # 切换输入焦点
                pass
            else:
                if self.current_view == "create":
                    for tb in self.text_boxes.values():
                        tb.handle_event(event)
                elif self.current_view == "settings":
                    for tb in self.text_boxes.values():
                        tb.handle_event(event)

        return False

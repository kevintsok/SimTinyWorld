"""
Session Panel - Session面板

提供Session管理界面，包括：
- Session列表显示
- 操作按钮：继续模拟、保存Session、删除、新建
- 名称输入框和创建按钮
"""

import pygame
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass

from ui.components import Button, Panel, TextBox
from ui.fonts import get_font
from session import SessionManager, SessionMetadata


@dataclass
class SessionPanelInterface:
    """Session面板回调接口"""
    on_continue_session: Callable[[str], None] = None  # 继续选中的Session
    on_save_session: Callable[[str], None] = None      # 保存当前Session
    on_delete_session: Callable[[str], None] = None    # 删除Session
    on_new_session: Callable[[str], None] = None       # 创建新Session
    on_load_session: Callable[[str], None] = None      # 加载Session（恢复）


class SessionPanel:
    """Session面板

    提供Session的列表展示和操作界面。
    """

    # 配色方案
    BACKGROUND_COLOR = (30, 33, 40)
    PANEL_COLOR = (40, 44, 52)
    BUTTON_COLOR = (70, 130, 180)
    BUTTON_HOVER_COLOR = (100, 160, 210)
    TEXT_COLOR = (255, 255, 255)
    ACCENT_COLOR = (100, 160, 210)
    BORDER_COLOR = (60, 64, 72)
    RED_BUTTON_COLOR = (160, 80, 80)
    GREEN_BUTTON_COLOR = (80, 160, 100)

    def __init__(self, screen: pygame.Surface, rect: pygame.Rect,
                 session_manager: SessionManager,
                 interface: Optional[SessionPanelInterface] = None):
        """初始化Session面板

        Args:
            screen: pygame屏幕对象
            rect: 面板区域
            session_manager: Session管理器实例
            interface: 回调接口
        """
        self.screen = screen
        self.rect = rect
        self.session_manager = session_manager
        self.interface = interface or SessionPanelInterface()

        # 字体
        self.title_font = get_font(22)
        self.heading_font = get_font(18)
        self.normal_font = get_font(14)
        self.small_font = get_font(12)

        # Session列表
        self.sessions: List[SessionMetadata] = []
        self.selected_session_id: Optional[str] = None
        self.session_buttons: List[Button] = []
        self.session_rects: List[pygame.Rect] = []

        # 新建Session输入
        self.new_session_name = ""
        self.new_session_input = TextBox(
            rect=pygame.Rect(rect.x + 20, 0, rect.width - 40, 35),
            placeholder="新Session名称",
            max_length=50
        )

        # 按钮
        button_width = 120
        button_height = 35
        button_margin = 10

        # 操作按钮
        btn_y = rect.bottom - button_height - 20

        self.continue_button = Button(
            rect=pygame.Rect(rect.x + 20, btn_y, button_width, button_height),
            text="继续模拟",
            callback=self._on_continue_clicked,
            color=self.GREEN_BUTTON_COLOR,
            hover_color=(100, 180, 120),
        )

        self.save_button = Button(
            rect=pygame.Rect(rect.x + 20 + button_width + button_margin, btn_y,
                            button_width, button_height),
            text="保存Session",
            callback=self._on_save_clicked,
            color=self.BUTTON_COLOR,
            hover_color=self.BUTTON_HOVER_COLOR,
        )

        self.delete_button = Button(
            rect=pygame.Rect(rect.x + 20 + (button_width + button_margin) * 2, btn_y,
                            button_width, button_height),
            text="删除",
            callback=self._on_delete_clicked,
            color=self.RED_BUTTON_COLOR,
            hover_color=(180, 100, 100),
        )

        # 新建按钮
        self.new_button = Button(
            rect=pygame.Rect(rect.x + rect.width - button_width - 20, btn_y,
                            button_width, button_height),
            text="新建",
            callback=self._on_new_clicked,
            color=self.GREEN_BUTTON_COLOR,
            hover_color=(100, 180, 120),
        )

        # 更新输入框位置
        self.new_session_input.rect.y = rect.y + 60

        # 加载Session列表
        self.refresh_sessions()

    def refresh_sessions(self):
        """刷新Session列表"""
        self.sessions = self.session_manager.list_sessions()

    def _on_continue_clicked(self):
        """继续模拟按钮点击"""
        if self.selected_session_id and self.interface.on_continue_session:
            self.interface.on_continue_session(self.selected_session_id)

    def _on_save_clicked(self):
        """保存Session按钮点击"""
        if self.selected_session_id and self.interface.on_save_session:
            self.interface.on_save_session(self.selected_session_id)

    def _on_delete_clicked(self):
        """删除按钮点击"""
        if self.selected_session_id and self.interface.on_delete_session:
            self.interface.on_delete_session(self.selected_session_id)

    def _on_new_clicked(self):
        """新建按钮点击"""
        name = self.new_session_input.text.strip()
        if name and self.interface.on_new_session:
            self.interface.on_new_session(name)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """处理事件

        Args:
            event: pygame事件

        Returns:
            Optional[str]: 操作类型，"close"表示关闭面板
        """
        # 处理输入框
        if self.new_session_input.handle_event(event):
            return None

        # 处理按钮点击
        if self.continue_button.handle_event(event):
            return None
        if self.save_button.handle_event(event):
            return None
        if self.delete_button.handle_event(event):
            return None
        if self.new_button.handle_event(event):
            return None

        # 处理关闭按钮点击
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # 关闭按钮
                if hasattr(self, 'close_rect') and self.close_rect.collidepoint(event.pos):
                    return "close"
                # Session列表点击
                for i, rect in enumerate(self.session_rects):
                    if rect.collidepoint(event.pos):
                        if i < len(self.sessions):
                            self.selected_session_id = self.sessions[i].session_id
                            return f"select_session:{self.selected_session_id}"

        return None

    def draw(self, surface: pygame.Surface):
        """绘制Session面板"""
        # 绘制背景
        pygame.draw.rect(surface, self.PANEL_COLOR, self.rect, border_radius=8)
        pygame.draw.rect(surface, self.BORDER_COLOR, self.rect, 2, border_radius=8)

        # 绘制关闭按钮 (右上角)
        close_btn_size = 30
        self.close_rect = pygame.Rect(
            self.rect.right - close_btn_size - 10,
            self.rect.y + 10,
            close_btn_size,
            close_btn_size
        )
        pygame.draw.rect(surface, self.RED_BUTTON_COLOR, self.close_rect, border_radius=5)
        close_text = self.small_font.render("X", True, self.TEXT_COLOR)
        close_center = close_text.get_rect(center=self.close_rect.center)
        surface.blit(close_text, close_center)

        # 绘制标题
        title = self.title_font.render("Session管理", True, self.TEXT_COLOR)
        surface.blit(title, (self.rect.x + 20, self.rect.y + 15))

        # 绘制分隔线
        pygame.draw.line(surface, self.BORDER_COLOR,
                        (self.rect.x + 20, self.rect.y + 50),
                        (self.rect.right - 20, self.rect.y + 50), 2)

        # 绘制新建区域
        self._draw_new_session_area(surface)

        # 绘制Session列表
        self._draw_session_list(surface)

        # 绘制按钮
        self.continue_button.draw(surface)
        self.save_button.draw(surface)
        self.delete_button.draw(surface)
        self.new_button.draw(surface)

    def _draw_new_session_area(self, surface: pygame.Surface):
        """绘制新建Session区域"""
        label_y = self.rect.y + 70

        label = self.normal_font.render("新建Session:", True, (180, 180, 180))
        surface.blit(label, (self.rect.x + 20, label_y + 5))

        # 更新输入框位置
        self.new_session_input.rect.y = label_y + 30
        self.new_session_input.draw(surface)

    def _draw_session_list(self, surface: pygame.Surface):
        """绘制Session列表"""
        list_top = self.rect.y + 150
        list_height = self.rect.bottom - 200 - list_top

        if not self.sessions:
            no_session_text = self.normal_font.render("暂无Session", True, (150, 150, 150))
            text_rect = no_session_text.get_rect(
                center=(self.rect.centerx, list_top + list_height // 2)
            )
            surface.blit(no_session_text, text_rect)
            self.session_rects = []
            return

        # 列配置
        col_widths = [150, 80, 60, 50]  # 名称、场景、智能体数、天数
        col_names = ["名称", "场景", "智能体", "天数"]

        # 表头
        header_rect = pygame.Rect(self.rect.x + 15, list_top,
                                 self.rect.width - 30, 25)
        pygame.draw.rect(surface, (50, 54, 62), header_rect, border_radius=3)

        x_offset = self.rect.x + 20
        for i, col_name in enumerate(col_names):
            col_text = self.small_font.render(col_name, True, (180, 180, 180))
            surface.blit(col_text, (x_offset, list_top + 6))
            x_offset += col_widths[i]

        # Session列表项
        self.session_rects = []
        row_height = 35
        y_offset = list_top + 28

        for i, session in enumerate(self.sessions[:8]):  # 最多显示8个
            is_selected = session.session_id == self.selected_session_id
            row_bg_color = (50, 60, 75) if is_selected else (45, 50, 58)

            row_rect = pygame.Rect(self.rect.x + 15, y_offset,
                                  self.rect.width - 30, row_height)
            pygame.draw.rect(surface, row_bg_color, row_rect)
            if is_selected:
                pygame.draw.rect(surface, self.ACCENT_COLOR, row_rect, 2, border_radius=2)

            # 保存点击区域
            self.session_rects.append(row_rect)

            # 格式化数据
            session_name = session.name[:12] + ".." if len(session.name) > 12 else session.name
            scenario_map = {
                "daily_life": "日常生活",
                "emergency": "突发事件",
                "debate": "辩论"
            }
            scenario_name = scenario_map.get(session.scenario_type, session.scenario_type)

            row_data = [
                session_name,
                scenario_name,
                str(session.agent_count),
                str(session.current_day) if session.current_day > 0 else "-"
            ]

            x_offset = self.rect.x + 20
            for j, cell_data in enumerate(row_data):
                cell_text = self.small_font.render(str(cell_data), True, (220, 220, 220))
                surface.blit(cell_text, (x_offset, y_offset + 10))
                x_offset += col_widths[j]

            y_offset += row_height

    def set_selected_session(self, session_id: Optional[str]):
        """设置选中的Session"""
        self.selected_session_id = session_id

"""
UI Components - 可复用的UI组件
"""

import pygame
from typing import Callable, Optional, List, Tuple, Any
from dataclasses import dataclass
from ui.fonts import get_font


@dataclass
class Button:
    """按钮组件"""
    rect: pygame.Rect
    text: str
    callback: Callable[[], None]
    color: Tuple[int, int, int] = (70, 130, 180)
    hover_color: Tuple[int, int, int] = (100, 160, 210)
    text_color: Tuple[int, int, int] = (255, 255, 255)
    border_radius: int = 5
    visible: bool = True
    enabled: bool = True

    def __post_init__(self):
        self.font = get_font(16)
        self.is_hovered = False
        self._normal_surface = None
        self._hover_surface = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理事件，返回是否处理了此事件"""
        if not self.visible or not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

    def draw(self, surface: pygame.Surface):
        """绘制按钮"""
        if not self.visible:
            return

        color = self.hover_color if self.is_hovered else self.color
        if not self.enabled:
            color = tuple(max(0, c - 50) for c in color)

        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)

        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


@dataclass
class Panel:
    """面板组件"""
    rect: pygame.Rect
    title: str = ""
    background_color: Tuple[int, int, int] = (40, 44, 52)
    border_color: Tuple[int, int, int] = (60, 64, 72)
    title_color: Tuple[int, int, int] = (255, 255, 255)
    border_width: int = 2
    title_height: int = 30
    visible: bool = True

    def __post_init__(self):
        self.font = get_font(16)
        self.scroll_offset = 0
        self.content_height = 0

    def draw(self, surface: pygame.Surface):
        """绘制面板"""
        if not self.visible:
            return

        pygame.draw.rect(surface, self.background_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, self.border_color, self.rect, self.border_width, border_radius=5)

        if self.title:
            title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.title_height)
            pygame.draw.rect(surface, (60, 64, 72), title_rect, border_radius=5)
            title_clip = pygame.Rect(self.rect.x, self.rect.y + self.title_height - 5,
                                      self.rect.width, 5)
            pygame.draw.rect(surface, (60, 64, 72), title_clip)

            title_surface = self.font.render(self.title, True, self.title_color)
            title_pos = (self.rect.x + 10, self.rect.y + 7)
            surface.blit(title_surface, title_pos)


class TextBox:
    """文本输入框组件"""
    def __init__(self, rect: pygame.Rect, placeholder: str = "", max_length: int = 100):
        self.rect = rect
        self.placeholder = placeholder
        self.max_length = max_length
        self.text = ""
        self.font = get_font(16)
        self.text_color = (255, 255, 255)
        self.placeholder_color = (128, 128, 128)
        self.background_color = (60, 64, 72)
        self.border_color = (80, 84, 92)
        self.active_color = (70, 130, 180)
        self.is_active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.is_active = True
                    return True
                else:
                    self.is_active = False
                    return False
        elif event.type == pygame.KEYDOWN and self.is_active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            elif event.key == pygame.K_RETURN:
                return True
            elif event.unicode and len(self.text) < self.max_length:
                self.text += event.unicode
                return True
        return False

    def draw(self, surface: pygame.Surface):
        """绘制文本框"""
        bg_color = self.active_color if self.is_active else self.background_color
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, self.border_color, self.rect, 2, border_radius=5)

        if self.text:
            text_surface = self.font.render(self.text, True, self.text_color)
        else:
            text_surface = self.font.render(self.placeholder, True, self.placeholder_color)

        text_rect = text_surface.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        surface.blit(text_surface, text_rect)

        if self.is_active and self.text:
            self.cursor_timer += 1
            if self.cursor_timer % 60 < 30:
                cursor_x = text_rect.right + 2
                pygame.draw.line(surface, self.text_color,
                                 (cursor_x, self.rect.y + 5),
                                 (cursor_x, self.rect.y + self.rect.height - 5), 2)


class Dropdown:
    """下拉选择框组件"""
    def __init__(self, rect: pygame.Rect, options: List[str], title: str = ""):
        self.rect = rect
        self.options = options
        self.title = title
        self.selected_index = 0
        self.is_open = False
        self.font = get_font(14)
        self.text_color = (255, 255, 255)
        self.background_color = (60, 64, 72)
        self.hover_color = (80, 84, 92)
        self.option_height = 25

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.is_open:
                    option_rects = self._get_option_rects()
                    for i, opt_rect in enumerate(option_rects):
                        if opt_rect.collidepoint(event.pos):
                            self.selected_index = i
                            self.is_open = False
                            return True
                    self.is_open = False
                else:
                    if self.rect.collidepoint(event.pos):
                        self.is_open = True
                        return True
        elif event.type == pygame.MOUSEMOTION:
            if self.is_open:
                option_rects = self._get_option_rects()
                for i, opt_rect in enumerate(option_rects):
                    if opt_rect.collidepoint(event.pos):
                        self.selected_index = i
                        return True
        return False

    def _get_option_rects(self) -> List[pygame.Rect]:
        """获取选项区域列表"""
        rects = []
        for i in range(len(self.options)):
            rect = pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height + i * self.option_height,
                self.rect.width,
                self.option_height
            )
            rects.append(rect)
        return rects

    def draw(self, surface: pygame.Surface):
        """绘制下拉框"""
        pygame.draw.rect(surface, self.background_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (80, 84, 92), self.rect, 2, border_radius=5)

        text = self.options[self.selected_index] if self.options else ""
        text_surface = self.font.render(text, True, self.text_color)
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        surface.blit(text_surface, text_rect)

        arrow_x = self.rect.right - 20
        arrow_y = self.rect.centery
        pygame.draw.polygon(surface, self.text_color,
                           [(arrow_x, arrow_y - 5), (arrow_x + 8, arrow_y - 5),
                            (arrow_x + 4, arrow_y + 5)])

        if self.is_open:
            option_rects = self._get_option_rects()
            for i, (option, opt_rect) in enumerate(zip(self.options, option_rects)):
                color = self.hover_color if opt_rect.collidepoint(pygame.mouse.get_pos()) else self.background_color
                pygame.draw.rect(surface, color, opt_rect)
                text_surface = self.font.render(option, True, self.text_color)
                text_rect = text_surface.get_rect(midleft=(opt_rect.x + 10, opt_rect.centery))
                surface.blit(text_surface, text_rect)
                pygame.draw.line(surface, (80, 84, 92), (opt_rect.x, opt_rect.bottom - 1),
                               (opt_rect.right, opt_rect.bottom - 1))


class ProgressBar:
    """进度条组件"""
    def __init__(self, rect: pygame.Rect, value: float = 0.0, max_value: float = 1.0,
                 color: Tuple[int, int, int] = (70, 130, 180),
                 background_color: Tuple[int, int, int] = (60, 64, 72)):
        self.rect = rect
        self.value = value
        self.max_value = max_value
        self.color = color
        self.background_color = background_color

    def set_value(self, value: float):
        """设置进度值"""
        self.value = max(0, min(value, self.max_value))

    def draw(self, surface: pygame.Surface):
        """绘制进度条"""
        # 绘制背景
        pygame.draw.rect(surface, self.background_color, self.rect, border_radius=3)

        # 绘制进度
        fill_width = int(self.rect.width * (self.value / self.max_value))
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(surface, self.color, fill_rect, border_radius=3)

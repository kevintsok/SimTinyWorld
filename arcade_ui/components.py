"""
UI Components - Pixel-art style arcade UI components
"""

import arcade
import sys
import os
from typing import Callable, Optional, List, Tuple, Any

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Color scheme matching pygame version
COLORS = {
    "background": (30, 33, 40),
    "panel": (40, 44, 52),
    "button": (70, 130, 180),
    "button_hover": (100, 160, 210),
    "accent": (100, 160, 210),
    "text": (255, 255, 255),
    "text_secondary": (180, 180, 180),
    "placeholder": (128, 128, 128),
    "border": (60, 64, 72),
    "input_bg": (60, 64, 72),
    "input_active": (70, 130, 180),
}


# Pygame-compatible rectangle drawing wrappers for arcade
def draw_rectangle_filled(center_x: float, center_y: float, width: float, height: float, color: Tuple[int, int, int]):
    """Draw a filled rectangle (pygame-compatible API)."""
    arcade.draw_lbwh_rectangle_filled(
        center_x - width / 2,
        center_y - height / 2,
        width, height, color
    )


def draw_rectangle_outline(center_x: float, center_y: float, width: float, height: float, color: Tuple[int, int, int], border_width: int = 1):
    """Draw a rectangle outline (pygame-compatible API)."""
    arcade.draw_lbwh_rectangle_outline(
        center_x - width / 2,
        center_y - height / 2,
        width, height, color, border_width
    )


class Button:
    """Button component with hover state"""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        callback: Callable[[], None],
        color: Tuple[int, int, int] = COLORS["button"],
        hover_color: Tuple[int, int, int] = COLORS["button_hover"],
        text_color: Tuple[int, int, int] = COLORS["text"],
        font_size: int = 16,
        visible: bool = True,
        enabled: bool = True,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font_size = font_size
        self.visible = visible
        self.enabled = enabled
        self.is_hovered = False

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within button bounds"""
        return (
            self.x <= x <= self.x + self.width
            and self.y <= y <= self.y + self.height
        )

    def handle_mouse_motion(self, x: float, y: float):
        """Handle mouse motion event"""
        if not self.visible or not self.enabled:
            return False
        self.is_hovered = self.contains_point(x, y)
        return True

    def handle_mouse_press(self, x: float, y: float, button: int = arcade.MOUSE_BUTTON_LEFT) -> bool:
        """Handle mouse press event"""
        if not self.visible or not self.enabled:
            return False
        if button == arcade.MOUSE_BUTTON_LEFT and self.contains_point(x, y):
            self.callback()
            return True
        return False

    def draw(self):
        """Draw the button"""
        if not self.visible:
            return

        color = self.hover_color if self.is_hovered else self.color
        if not self.enabled:
            color = tuple(max(0, c - 50) for c in color)

        # Draw button background
        draw_rectangle_filled(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height,
            color=color,
        )

        # Draw border
        draw_rectangle_outline(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height,
            color=COLORS["border"],
            border_width=2,
        )

        # Draw text
        arcade.draw_text(
            text=self.text,
            x=self.x + self.width / 2,
            y=self.y + self.height / 2,
            color=self.text_color,
            font_size=self.font_size,
            anchor_x="center",
            anchor_y="center",
            font_name="arial",
        )


class Panel:
    """Panel container with optional title"""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        title: str = "",
        background_color: Tuple[int, int, int] = COLORS["panel"],
        border_color: Tuple[int, int, int] = COLORS["border"],
        title_color: Tuple[int, int, int] = COLORS["text"],
        border_width: int = 2,
        title_height: int = 30,
        visible: bool = True,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        self.background_color = background_color
        self.border_color = border_color
        self.title_color = title_color
        self.border_width = border_width
        self.title_height = title_height
        self.visible = visible
        self.scroll_offset = 0
        self.content_height = 0

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within panel bounds"""
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

    def draw(self):
        """Draw the panel"""
        if not self.visible:
            return

        # Draw background
        draw_rectangle_filled(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height,
            color=self.background_color,
        )

        # Draw border
        draw_rectangle_outline(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height,
            color=self.border_color,
            border_width=self.border_width,
        )

        # Draw title bar if title exists
        if self.title:
            # Title bar background
            draw_rectangle_filled(
                center_x=self.x + self.width / 2,
                center_y=self.y + self.height - self.title_height / 2,
                width=self.width - 4,
                height=self.title_height,
                color=self.border_color,
            )

            # Title text
            arcade.draw_text(
                text=self.title,
                x=self.x + 10,
                y=self.y + self.height - self.title_height + 8,
                color=self.title_color,
                font_size=14,
                font_name="arial",
            )


class TextBox:
    """Text input box with placeholder, cursor, max length"""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        placeholder: str = "",
        max_length: int = 100,
        font_size: int = 16,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.placeholder = placeholder
        self.max_length = max_length
        self.text = ""
        self.font_size = font_size
        self.text_color = COLORS["text"]
        self.placeholder_color = COLORS["placeholder"]
        self.background_color = COLORS["input_bg"]
        self.border_color = COLORS["border"]
        self.active_color = COLORS["input_active"]
        self.is_active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within textbox bounds"""
        return (
            self.x <= x <= self.x + self.width
            and self.y <= y <= self.y + self.height
        )

    def handle_mouse_press(self, x: float, y: float, button: int = arcade.MOUSE_BUTTON_LEFT) -> bool:
        """Handle mouse press event"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.contains_point(x, y):
                self.is_active = True
                return True
            else:
                self.is_active = False
        return False

    def handle_key_press(self, key: int, modifiers: int, text: str = "") -> bool:
        """Handle key press event"""
        if not self.is_active:
            return False

        if key == arcade.key.BACKSPACE:
            self.text = self.text[:-1]
            return True
        elif key == arcade.key.RETURN:
            return True
        elif text and len(self.text) < self.max_length:
            self.text += text
            return True
        return False

    def update(self, delta_time: float = 1/60):
        """Update cursor visibility"""
        self.cursor_timer += delta_time
        if self.cursor_timer >= 0.5:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible

    def draw(self):
        """Draw the textbox"""
        bg_color = self.active_color if self.is_active else self.background_color

        # Draw background
        draw_rectangle_filled(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height,
            color=bg_color,
        )

        # Draw border
        border_color = self.active_color if self.is_active else self.border_color
        draw_rectangle_outline(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height,
            color=border_color,
            border_width=2,
        )

        # Draw text or placeholder
        display_text = self.text if self.text else self.placeholder
        text_color = self.text_color if self.text else self.placeholder_color

        arcade.draw_text(
            text=display_text,
            x=self.x + 10,
            y=self.y + self.height / 2,
            color=text_color,
            font_size=self.font_size,
            anchor_y="center",
            font_name="arial",
        )

        # Draw cursor
        if self.is_active and self.text and self.cursor_visible:
            # Calculate cursor position based on text length
            text_width = len(self.text) * (self.font_size * 0.6)
            cursor_x = self.x + 10 + text_width + 2
            arcade.draw_line(
                x=cursor_x,
                y=self.y + 5,
                end_x=cursor_x,
                end_y=self.y + self.height - 5,
                color=self.text_color,
                line_width=2,
            )


class Dropdown:
    """Dropdown selection with options"""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        options: List[str],
        title: str = "",
        font_size: int = 14,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.options = options
        self.title = title
        self.selected_index = 0
        self.is_open = False
        self.font_size = font_size
        self.text_color = COLORS["text"]
        self.background_color = COLORS["input_bg"]
        self.hover_color = (80, 84, 92)
        self.option_height = 25
        self.hovered_option = -1

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within dropdown bounds"""
        if self.is_open:
            # Check options area
            total_height = self.height + len(self.options) * self.option_height
            return (
                self.x <= x <= self.x + self.width
                and self.y <= y <= self.y + total_height
            )
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

    def handle_mouse_motion(self, x: float, y: float):
        """Handle mouse motion event"""
        if not self.is_open:
            return
        self.hovered_option = self._get_option_index_at(x, y)

    def _get_option_index_at(self, x: float, y: float) -> int:
        """Get option index at given coordinates"""
        if not self.is_open:
            return -1
        for i in range(len(self.options)):
            opt_y = self.y + self.height + i * self.option_height
            if opt_y <= y <= opt_y + self.option_height:
                return i
        return -1

    def handle_mouse_press(self, x: float, y: float, button: int = arcade.MOUSE_BUTTON_LEFT) -> bool:
        """Handle mouse press event"""
        if button != arcade.MOUSE_BUTTON_LEFT:
            return False

        if self.is_open:
            option_idx = self._get_option_index_at(x, y)
            if option_idx >= 0:
                self.selected_index = option_idx
                self.is_open = False
                return True
            self.is_open = False
        else:
            if self.contains_point(x, y):
                self.is_open = True
                return True
        return False

    def get_selected(self) -> str:
        """Get currently selected option"""
        if 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return ""

    def draw(self):
        """Draw the dropdown"""
        # Draw main box
        draw_rectangle_filled(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height,
            color=self.background_color,
        )

        draw_rectangle_outline(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height,
            color=COLORS["border"],
            border_width=2,
        )

        # Draw selected text
        text = self.options[self.selected_index] if self.options else ""
        arcade.draw_text(
            text=text,
            x=self.x + 10,
            y=self.y + self.height / 2,
            color=self.text_color,
            font_size=self.font_size,
            anchor_y="center",
            font_name="arial",
        )

        # Draw arrow
        arrow_x = self.x + self.width - 20
        arrow_y = self.y + self.height / 2
        arcade.draw_triangle_filled(
            arrow_x, arrow_y - 5,
            arrow_x + 8, arrow_y - 5,
            arrow_x + 4, arrow_y + 5,
            self.text_color,
        )

        # Draw options if open
        if self.is_open:
            for i, option in enumerate(self.options):
                opt_y = self.y + self.height + i * self.option_height
                is_hovered = i == self.hovered_option

                color = self.hover_color if is_hovered else self.background_color
                draw_rectangle_filled(
                    center_x=self.x + self.width / 2,
                    center_y=opt_y + self.option_height / 2,
                    width=self.width,
                    height=self.option_height,
                    color=color,
                )

                arcade.draw_text(
                    text=option,
                    x=self.x + 10,
                    y=opt_y + self.option_height / 2,
                    color=self.text_color,
                    font_size=self.font_size,
                    anchor_y="center",
                    font_name="arial",
                )

                # Draw separator line
                if i < len(self.options) - 1:
                    arcade.draw_line(
                        x=self.x,
                        y=opt_y,
                        end_x=self.x + self.width,
                        end_y=opt_y,
                        color=COLORS["border"],
                    )


class ProgressBar:
    """Horizontal progress indicator"""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        value: float = 0.0,
        max_value: float = 1.0,
        color: Tuple[int, int, int] = COLORS["button"],
        background_color: Tuple[int, int, int] = COLORS["input_bg"],
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.value = value
        self.max_value = max_value
        self.color = color
        self.background_color = background_color

    def set_value(self, value: float):
        """Set progress value"""
        self.value = max(0, min(value, self.max_value))

    def draw(self):
        """Draw the progress bar"""
        # Draw background
        draw_rectangle_filled(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height,
            color=self.background_color,
        )

        # Draw progress fill
        fill_width = self.width * (self.value / self.max_value) if self.max_value > 0 else 0
        if fill_width > 0:
            draw_rectangle_filled(
                center_x=self.x + fill_width / 2,
                center_y=self.y + self.height / 2,
                width=fill_width,
                height=self.height,
                color=self.color,
            )

        # Draw border
        draw_rectangle_outline(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height,
            color=COLORS["border"],
            border_width=1,
        )


class Label:
    """Simple text label"""

    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        color: Tuple[int, int, int] = COLORS["text"],
        font_size: int = 14,
        anchor_y: str = "center",
    ):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font_size = font_size
        self.anchor_y = anchor_y

    def set_text(self, text: str):
        """Update label text"""
        self.text = text

    def draw(self):
        """Draw the label"""
        arcade.draw_text(
            text=self.text,
            x=self.x,
            y=self.y,
            color=self.color,
            font_size=self.font_size,
            anchor_y=self.anchor_y,
            font_name="arial",
        )


class Checkbox:
    """Checkbox component"""

    def __init__(
        self,
        x: float,
        y: float,
        size: float = 20,
        checked: bool = False,
        label: str = "",
        callback: Callable[[bool], None] = None,
        color: Tuple[int, int, int] = COLORS["button"],
        text_color: Tuple[int, int, int] = COLORS["text"],
        font_size: int = 14,
    ):
        self.x = x
        self.y = y
        self.size = size
        self.checked = checked
        self.label = label
        self.callback = callback
        self.color = color
        self.text_color = text_color
        self.font_size = font_size

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within checkbox bounds"""
        label_width = len(self.label) * (self.font_size * 0.6) if self.label else 0
        return (
            self.x <= x <= self.x + self.size + label_width
            and self.y <= y <= self.y + self.size
        )

    def handle_mouse_press(self, x: float, y: float, button: int = arcade.MOUSE_BUTTON_LEFT) -> bool:
        """Handle mouse press event"""
        if button == arcade.MOUSE_BUTTON_LEFT and self.contains_point(x, y):
            self.checked = not self.checked
            if self.callback:
                self.callback(self.checked)
            return True
        return False

    def draw(self):
        """Draw the checkbox"""
        # Draw box
        draw_rectangle_outline(
            center_x=self.x + self.size / 2,
            center_y=self.y + self.size / 2,
            width=self.size,
            height=self.size,
            color=self.color,
            border_width=2,
        )

        # Draw checkmark if checked
        if self.checked:
            draw_rectangle_filled(
                center_x=self.x + self.size / 2,
                center_y=self.y + self.size / 2,
                width=self.size - 6,
                height=self.size - 6,
                color=self.color,
            )

        # Draw label
        if self.label:
            arcade.draw_text(
                text=self.label,
                x=self.x + self.size + 8,
                y=self.y + self.size / 2,
                color=self.text_color,
                font_size=self.font_size,
                anchor_y="center",
                font_name="arial",
            )


class Slider:
    """Slider component for value selection"""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float = 20,
        min_value: float = 0.0,
        max_value: float = 1.0,
        value: float = 0.5,
        callback: Callable[[float], None] = None,
        color: Tuple[int, int, int] = COLORS["button"],
        background_color: Tuple[int, int, int] = COLORS["input_bg"],
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self.callback = callback
        self.color = color
        self.background_color = background_color
        self.handle_radius = 8
        self.is_dragging = False

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within slider bounds"""
        return (
            self.x - self.handle_radius <= x <= self.x + self.width + self.handle_radius
            and self.y - self.handle_radius <= y <= self.y + self.height + self.handle_radius
        )

    def _get_value_at(self, x: float) -> float:
        """Get value at x position"""
        ratio = max(0, min(1, (x - self.x) / self.width))
        return self.min_value + ratio * (self.max_value - self.min_value)

    def handle_mouse_press(self, x: float, y: float, button: int = arcade.MOUSE_BUTTON_LEFT) -> bool:
        """Handle mouse press event"""
        if button == arcade.MOUSE_BUTTON_LEFT and self.contains_point(x, y):
            self.is_dragging = True
            self.value = self._get_value_at(x)
            if self.callback:
                self.callback(self.value)
            return True
        return False

    def handle_mouse_drag(self, x: float, y: float):
        """Handle mouse drag event"""
        if self.is_dragging:
            self.value = self._get_value_at(x)
            if self.callback:
                self.callback(self.value)

    def handle_mouse_release(self):
        """Handle mouse release event"""
        self.is_dragging = False

    def draw(self):
        """Draw the slider"""
        # Draw track background
        draw_rectangle_filled(
            center_x=self.x + self.width / 2,
            center_y=self.y + self.height / 2,
            width=self.width,
            height=self.height // 2,
            color=self.background_color,
        )

        # Draw filled portion
        value_range = self.max_value - self.min_value
        fill_ratio = (self.value - self.min_value) / value_range if value_range != 0 else 0
        fill_width = self.width * fill_ratio
        if fill_width > 0:
            draw_rectangle_filled(
                center_x=self.x + fill_width / 2,
                center_y=self.y + self.height / 2,
                width=fill_width,
                height=self.height // 2,
                color=self.color,
            )

        # Draw handle
        handle_x = self.x + fill_width
        handle_y = self.y + self.height / 2
        arcade.draw_circle_filled(
            center_x=handle_x,
            center_y=handle_y,
            radius=self.handle_radius,
            color=self.color,
        )
        arcade.draw_circle_outline(
            center_x=handle_x,
            center_y=handle_y,
            radius=self.handle_radius,
            color=COLORS["border"],
            line_width=2,
        )

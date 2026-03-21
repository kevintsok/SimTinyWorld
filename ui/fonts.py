"""
UI Fonts - 字体工具
"""

import pygame
import os
from typing import Tuple

# 确保pygame已初始化
try:
    pygame.init()
except Exception:
    pass


# Mac系统支持中文的字体路径
CHINESE_FONT_PATHS = [
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Libian.ttc",
]

# 备用系统字体名
CHINESE_FONT_NAMES = [
    "Arial Unicode MS",
    "PingFang SC",
    "PingFang TC",
    "Hiragino Sans GB",
    "Microsoft YaHei",
    "SimHei",
    "STHeiti",
]

# 全局字体缓存
_font_cache = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """获取支持中文的字体

    Args:
        size: 字体大小
        bold: 是否粗体

    Returns:
        pygame.font.Font: 字体对象
    """
    cache_key = (size, bold)
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    font = None

    # 首先尝试使用字体文件路径
    for font_path in CHINESE_FONT_PATHS:
        if os.path.exists(font_path):
            try:
                font = pygame.font.Font(font_path, size)
                # 测试渲染中文
                test_surf = font.render("中", True, (0, 0, 0))
                if test_surf.get_width() > 5:
                    _font_cache[cache_key] = font
                    return font
            except Exception:
                continue

    # 尝试使用系统字体名称
    for font_name in CHINESE_FONT_NAMES:
        try:
            font = pygame.font.SysFont(font_name, size, bold=bold)
            # 测试渲染中文
            test_surf = font.render("中", True, (0, 0, 0))
            if test_surf.get_width() > 5:
                _font_cache[cache_key] = font
                return font
        except Exception:
            continue

    # 使用默认字体（最后手段）
    font = pygame.font.Font(None, size)
    _font_cache[cache_key] = font
    return font


def get_text_size(text: str, font: pygame.font.Font) -> Tuple[int, int]:
    """获取文本渲染后的尺寸"""
    return font.size(text)

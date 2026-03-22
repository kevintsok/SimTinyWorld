"""
UI Module - 游戏风格可视化界面

提供2D俯视角界面用于显示模拟世界中的智能体和位置。

主要组件:
- MainView: 主界面（场景选择、智能体管理、Session管理、快速开始）
- ScenarioView: 场景视图（地图渲染、智能体详情、模拟控制）
- SessionPanel: Session面板（Session列表、保存、加载、删除、新建）
- Button/Panel/TextBox: 可复用UI组件
"""

from ui.main_view import MainView, MainViewInterface
from ui.scenario_view import ScenarioView, ScenarioViewInterface
from ui.session_panel import SessionPanel, SessionPanelInterface
from ui.game_view import GameView
from ui.agent_panel import AgentPanel
from ui.components import Button, Panel, TextBox

__all__ = [
    'MainView', 'MainViewInterface',
    'ScenarioView', 'ScenarioViewInterface',
    'SessionPanel', 'SessionPanelInterface',
    'GameView', 'AgentPanel',
    'Button', 'Panel', 'TextBox'
]

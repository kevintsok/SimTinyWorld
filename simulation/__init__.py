"""
Simulation Framework - 可扩展的多场景智能体模拟框架

提供通用的模拟基础设施，支持多种场景：
- 日常生活对话 (daily_life)
- 社会突发事件 (emergency)
- 国际博弈 (geopolitics)
- 观点辩论 (debate)
"""

from simulation.base import BaseAgent, BaseEnvironment, BaseEntity
from simulation.engine import SimulationEngine
from simulation.scenarios import get_scenario

__all__ = [
    "BaseAgent",
    "BaseEnvironment",
    "BaseEntity",
    "SimulationEngine",
    "get_scenario",
]

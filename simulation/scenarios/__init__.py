"""
Scenarios - 场景模块

提供各种模拟场景的实现：
- daily_life: 日常生活对话
- emergency: 社会突发事件
- geopolitics: 国际博弈
- debate: 观点辩论
"""

from simulation.scenarios.base import BaseScenario
from simulation.scenarios.daily_life import DailyLifeScenario


SCENARIOS = {
    "daily_life": DailyLifeScenario,
    # "emergency": EmergencyScenario,
    # "geopolitics": GeopoliticsScenario,
    # "debate": DebateScenario,
}


def get_scenario(scenario_type: str, config: dict = None):
    """获取场景实例

    Args:
        scenario_type: 场景类型
        config: 配置字典

    Returns:
        BaseScenario: 场景实例

    Raises:
        ValueError: 如果场景类型不存在
    """
    if scenario_type not in SCENARIOS:
        raise ValueError(f"Unknown scenario type: {scenario_type}. Available: {list(SCENARIOS.keys())}")

    scenario_class = SCENARIOS[scenario_type]
    return scenario_class(config or {})


__all__ = [
    "BaseScenario",
    "DailyLifeScenario",
    "get_scenario",
]

"""
Scenarios - 场景模块

提供各种模拟场景的实现：
- daily_life: 日常生活对话
- emergency: 社会突发事件
- debate: 观点辩论
- json: 从JSON文件加载的自定义场景
"""

from simulation.scenarios.base import BaseScenario
from simulation.scenarios.daily_life import DailyLifeScenario
from simulation.scenarios.emergency import EmergencyScenario
from simulation.scenarios.debate import DebateScenario


SCENARIOS = {
    "daily_life": DailyLifeScenario,
    "emergency": EmergencyScenario,
    "debate": DebateScenario,
    # "geopolitics": GeopoliticsScenario,
}


def get_scenario(scenario_type: str, config: dict = None, scenario_file: str = None):
    """获取场景实例

    Args:
        scenario_type: 场景类型
        config: 配置字典
        scenario_file: JSON场景文件路径（用于json类型）

    Returns:
        BaseScenario: 场景实例

    Raises:
        ValueError: 如果场景类型不存在
    """
    # JSON场景特殊处理
    if scenario_type == "json" or scenario_file:
        from simulation.scenarios.json_scenario import JSONScenario
        if scenario_file:
            return JSONScenario({"scenario_file": scenario_file, **(config or {})})
        raise ValueError("JSON场景需要指定 scenario_file 参数")

    if scenario_type not in SCENARIOS:
        raise ValueError(f"Unknown scenario type: {scenario_type}. Available: {list(SCENARIOS.keys())}")

    scenario_class = SCENARIOS[scenario_type]
    return scenario_class(config or {})


__all__ = [
    "BaseScenario",
    "DailyLifeScenario",
    "EmergencyScenario",
    "DebateScenario",
    "JSONScenario",
    "get_scenario",
]

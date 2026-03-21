"""
Base Scenario - 场景抽象基类

定义场景的核心接口：
- setup(): 初始化场景
- get_prompt_for_agent(): 获取智能体提示词
- evaluate_action(): 评估行动结果
- is_complete(): 判断场景是否完成
- get_summary(): 获取场景总结
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseScenario(ABC):
    """场景抽象基类

    所有具体场景实现的基类。
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化场景

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 场景状态
        self.is_initialized = False
        self.is_completed = False

        # 场景数据
        self.data: Dict[str, Any] = {}

        # 环境引用（将由引擎设置）
        self.environment = None

        # 模拟结果
        self.result: Dict[str, Any] = {
            "steps": 0,
            "events": [],
            "summary": ""
        }

    @abstractmethod
    def setup(self) -> None:
        """初始化场景

        在模拟开始前调用，用于设置场景环境、生成初始事件等。
        """
        pass

    def setup_agent(self, agent) -> None:
        """设置智能体

        在智能体添加到模拟引擎后调用，用于初始化智能体的场景相关状态。

        Args:
            agent: 智能体实例
        """
        pass

    @abstractmethod
    def get_prompt_for_agent(self, agent, context: Dict[str, Any]) -> str:
        """获取智能体的提示词

        Args:
            agent: 智能体实例
            context: 上下文信息

        Returns:
            str: 提示词
        """
        pass

    @abstractmethod
    def evaluate_action(self, agent, action: Dict[str, Any]) -> Dict[str, Any]:
        """评估智能体的行动

        Args:
            agent: 智能体实例
            action: 行动字典

        Returns:
            Dict[str, Any]: 评估结果
        """
        pass

    @abstractmethod
    def step(
        self,
        agents: Dict[str, Any],
        environment: Any,
        step: int
    ) -> Dict[str, Any]:
        """执行一步模拟

        Args:
            agents: 智能体字典
            environment: 环境实例
            step: 当前步数

        Returns:
            Dict[str, Any]: 步进结果
        """
        pass

    def is_complete(self) -> bool:
        """判断场景是否完成

        Returns:
            bool: 是否完成
        """
        return self.is_completed

    def get_summary(self) -> Dict[str, Any]:
        """获取场景总结

        Returns:
            Dict[str, Any]: 场景总结
        """
        return {
            "steps": self.result.get("steps", 0),
            "events": self.result.get("events", []),
            "summary": self.result.get("summary", ""),
            "data": self.data
        }

    def add_event(self, event: Dict[str, Any]) -> None:
        """添加事件到结果

        Args:
            event: 事件字典
        """
        self.result["events"].append(event)

    def set_completed(self, summary: str = "") -> None:
        """设置场景完成

        Args:
            summary: 总结信息
        """
        self.is_completed = True
        if summary:
            self.result["summary"] = summary
